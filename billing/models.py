from django.conf import settings
from django.db import models


class Payment(models.Model):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    STATUS_CHOICES = [
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (PENDING, "Pending"),
    ]

    NGN = "NGN"
    USD = "USD"
    CURRENCY_CHOICES = [(NGN, "NGN"), (USD, "USD")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default=NGN)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    paystack_subscription_code = models.CharField(max_length=100, blank=True)
    paystack_customer_code = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} ({self.status})"
