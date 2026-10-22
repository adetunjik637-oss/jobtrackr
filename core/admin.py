from django.contrib import admin

from .models import CoverLetter, JobApplication, Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at")
    search_fields = ("title", "user__username")


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job_title", "company_name", "user", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("job_title", "company_name", "user__username")


@admin.register(CoverLetter)
class CoverLetterAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "tone", "created_at")
    list_filter = ("tone",)
