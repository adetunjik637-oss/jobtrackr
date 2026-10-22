from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "currency", "status", "paid_at")
    list_filter = ("status", "currency")
    search_fields = ("reference", "user__username", "user__email")
