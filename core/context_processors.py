from django.conf import settings


def pricing(request):
    """Expose pricing and free-tier info to all templates."""
    return {
        "PRICE_NGN": settings.PRICE_NGN,
        "PRICE_USD": settings.PRICE_USD,
        "FREE_MONTHLY_LETTERS": settings.FREE_MONTHLY_LETTERS,
    }
