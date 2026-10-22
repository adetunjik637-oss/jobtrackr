from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # Resumes
    path("resumes/", views.resume_list, name="resume_list"),
    path("resumes/upload/", views.resume_upload, name="resume_upload"),
    path("resumes/<int:pk>/delete/", views.resume_delete, name="resume_delete"),

    # Cover letters
    path("generate/", views.generate_letter, name="generate_letter"),
    path("letters/", views.letter_list, name="letter_list"),
    path("letters/<int:pk>/", views.letter_detail, name="letter_detail"),
    path("letters/<int:pk>/download/", views.letter_download, name="letter_download"),

    # Applications
    path("applications/", views.application_list, name="application_list"),
    path("applications/new/", views.application_create, name="application_create"),
    path("applications/<int:pk>/", views.application_detail, name="application_detail"),
    path("applications/<int:pk>/edit/", views.application_edit, name="application_edit"),
    path("applications/<int:pk>/delete/", views.application_delete, name="application_delete"),
]
