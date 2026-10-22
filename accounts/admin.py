from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "subscription_status", "subscription_expiry",
        "monthly_letter_count", "usage_period",
    )
    list_filter = ("subscription_status",)
    search_fields = ("user__username", "user__email", "full_name")
