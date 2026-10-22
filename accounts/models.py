from django.conf import settings
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    """Per-user profile holding subscription state and the free-tier counter."""

    FREE = "free"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (FREE, "Free"),
        (ACTIVE, "Active"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=60, blank=True)

    subscription_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=FREE
    )
    subscription_expiry = models.DateField(null=True, blank=True)
    paystack_customer_code = models.CharField(max_length=100, blank=True)
    paystack_subscription_code = models.CharField(max_length=100, blank=True)

    # Free-tier usage tracking
    monthly_letter_count = models.PositiveIntegerField(default=0)
    usage_period = models.CharField(max_length=7, blank=True)  # "YYYY-MM"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"

    # --- Subscription helpers ------------------------------------------------

    @property
    def is_subscribed(self):
        """True when the user has an active, unexpired subscription."""
        if self.subscription_status != self.ACTIVE:
            return False
        if self.subscription_expiry and self.subscription_expiry < timezone.now().date():
            return False
        return True

    def activate_subscription(self, expiry_date, subscription_code="", customer_code=""):
        self.subscription_status = self.ACTIVE
        self.subscription_expiry = expiry_date
        if subscription_code:
            self.paystack_subscription_code = subscription_code
        if customer_code:
            self.paystack_customer_code = customer_code
        self.save(update_fields=[
            "subscription_status", "subscription_expiry",
            "paystack_subscription_code", "paystack_customer_code", "updated_at",
        ])

    def cancel_subscription(self):
        self.subscription_status = self.CANCELLED
        self.save(update_fields=["subscription_status", "updated_at"])

    # --- Free-tier usage -----------------------------------------------------

    def _current_period(self):
        return timezone.now().strftime("%Y-%m")

    def _reset_if_new_period(self):
        period = self._current_period()
        if self.usage_period != period:
            self.usage_period = period
            self.monthly_letter_count = 0

    def letters_remaining(self):
        """How many free letters are left this month (None = unlimited)."""
        if self.is_subscribed:
            return None
        self._reset_if_new_period()
        remaining = settings.FREE_MONTHLY_LETTERS - self.monthly_letter_count
        return max(remaining, 0)

    def can_generate_letter(self):
        return self.is_subscribed or self.letters_remaining() > 0

    def record_letter_generated(self):
        """Increment the monthly counter (no-op accounting for subscribers)."""
        self._reset_if_new_period()
        self.monthly_letter_count += 1
        self.save(update_fields=[
            "monthly_letter_count", "usage_period", "updated_at",
        ])
