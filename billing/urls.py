from django.urls import path

from . import views

urlpatterns = [
    path("pricing/", views.pricing, name="pricing"),
    path("subscribe/", views.subscribe, name="billing_subscribe"),
    path("callback/", views.callback, name="billing_callback"),
    path("webhook/", views.webhook, name="billing_webhook"),
]
