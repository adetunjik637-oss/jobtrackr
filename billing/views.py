import hashlib
import hmac
import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Payment
from .paystack import PaystackError, initialize_transaction, verify_transaction


def pricing(request):
    return render(request, "billing/pricing.html")


def _plan_for_currency(currency):
    if currency == Payment.USD:
        return settings.PAYSTACK_PLAN_CODE_USD, settings.PRICE_USD
    return settings.PAYSTACK_PLAN_CODE_NGN, settings.PRICE_NGN


@login_required
def subscribe(request):
    """Kick off a Paystack subscription checkout."""
    if request.method != "POST":
        return redirect("pricing")

    currency = request.POST.get("currency", Payment.NGN)
    if currency not in (Payment.NGN, Payment.USD):
        currency = Payment.NGN

    plan_code, price = _plan_for_currency(currency)
    # Smallest unit: kobo for NGN, cents for USD.
    amount_minor = int(float(price) * 100)
    reference = f"jt_{uuid.uuid4().hex[:20]}"
    callback_url = request.build_absolute_uri(reverse("billing_callback"))

    Payment.objects.create(
        user=request.user,
        reference=reference,
        amount=price,
        currency=currency,
        status=Payment.PENDING,
    )

    try:
        data = initialize_transaction(
            email=request.user.email or f"{request.user.username}@example.com",
            amount_kobo=amount_minor,
            reference=reference,
            callback_url=callback_url,
            plan_code=plan_code,
            currency=currency,
        )
    except PaystackError as exc:
        messages.error(request, str(exc))
        return redirect("pricing")

    return redirect(data["authorization_url"])


@login_required
def callback(request):
    """Paystack redirects the user back here after payment."""
    reference = request.GET.get("reference") or request.GET.get("trxref")
    if not reference:
        messages.error(request, "No payment reference returned.")
        return redirect("pricing")

    try:
        data = verify_transaction(reference)
    except PaystackError as exc:
        messages.error(request, f"Could not verify payment: {exc}")
        return redirect("pricing")

    if data.get("status") == "success":
        _activate_from_verification(request.user, reference, data)
        messages.success(request, "Payment successful — your subscription is active!")
        return redirect("dashboard")

    messages.error(request, "Payment was not completed. Please try again.")
    return redirect("pricing")


def _activate_from_verification(user, reference, data):
    """Mark the payment successful and extend the user's subscription."""
    payment = Payment.objects.filter(reference=reference).first()
    customer_code = (data.get("customer") or {}).get("customer_code", "")
    # Subscription code may arrive via webhook; capture if present.
    sub_code = ""
    if payment:
        payment.status = Payment.SUCCESS
        payment.paid_at = timezone.now()
        payment.paystack_customer_code = customer_code
        payment.save(update_fields=[
            "status", "paid_at", "paystack_customer_code",
        ])

    expiry = timezone.now().date() + timedelta(days=31)
    profile = user.profile
    # Keep the later of current expiry and new expiry.
    if profile.subscription_expiry and profile.subscription_expiry > expiry:
        expiry = profile.subscription_expiry
    profile.activate_subscription(
        expiry_date=expiry,
        subscription_code=sub_code,
        customer_code=customer_code,
    )


@csrf_exempt
def webhook(request):
    """Handle Paystack webhook events (source of truth for recurring charges)."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    signature = request.headers.get("x-paystack-signature", "")
    secret = settings.PAYSTACK_SECRET_KEY.encode("utf-8")
    computed = hmac.new(secret, request.body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(computed, signature):
        return HttpResponseBadRequest("Invalid signature")

    try:
        event = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid payload")

    event_type = event.get("event", "")
    data = event.get("data", {})

    if event_type in ("charge.success", "subscription.create", "invoice.payment_succeeded"):
        _handle_successful_charge(data)
    elif event_type in ("subscription.disable", "invoice.payment_failed"):
        _handle_subscription_ended(data)

    # Always 200 so Paystack stops retrying.
    return HttpResponse("ok")


def _find_user_from_event(data):
    customer = data.get("customer") or {}
    email = customer.get("email")
    if email:
        from django.contrib.auth.models import User
        return User.objects.filter(email=email).first()
    return None


def _handle_successful_charge(data):
    user = _find_user_from_event(data)
    if not user:
        return
    reference = data.get("reference", "")
    expiry = timezone.now().date() + timedelta(days=31)
    profile = user.profile
    if profile.subscription_expiry and profile.subscription_expiry > expiry:
        expiry = profile.subscription_expiry
    sub_code = data.get("subscription_code", "") or (
        data.get("subscription", {}) or {}).get("subscription_code", "")
    customer_code = (data.get("customer") or {}).get("customer_code", "")
    profile.activate_subscription(
        expiry_date=expiry,
        subscription_code=sub_code,
        customer_code=customer_code,
    )
    if reference:
        Payment.objects.update_or_create(
            reference=reference,
            defaults={
                "user": user,
                "status": Payment.SUCCESS,
                "paid_at": timezone.now(),
                "amount": (data.get("amount", 0) or 0) / 100,
                "currency": data.get("currency", Payment.NGN),
                "paystack_customer_code": customer_code,
                "paystack_subscription_code": sub_code,
            },
        )


def _handle_subscription_ended(data):
    user = _find_user_from_event(data)
    if user:
        user.profile.cancel_subscription()
