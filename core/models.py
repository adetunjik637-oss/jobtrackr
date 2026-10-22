from django.conf import settings
from django.db import models
from django.urls import reverse


class Resume(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resumes"
    )
    title = models.CharField(max_length=120, default="My Resume")
    file = models.FileField(upload_to="resumes/", blank=True, null=True)
    extracted_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class JobApplication(models.Model):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    STATUS_CHOICES = [
        (SAVED, "Saved"),
        (APPLIED, "Applied"),
        (INTERVIEWING, "Interviewing"),
        (OFFER, "Offer"),
        (REJECTED, "Rejected"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    company_name = models.CharField(max_length=150)
    job_title = models.CharField(max_length=150)
    job_link = models.URLField(blank=True)
    job_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SAVED)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.job_title} @ {self.company_name}"

    def get_absolute_url(self):
        return reverse("application_detail", args=[self.pk])

    @property
    def status_color(self):
        return {
            self.SAVED: "slate",
            self.APPLIED: "blue",
            self.INTERVIEWING: "amber",
            self.OFFER: "green",
            self.REJECTED: "red",
        }.get(self.status, "slate")


class CoverLetter(models.Model):
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"
    CONCISE = "concise"
    TONE_CHOICES = [
        (FORMAL, "Formal"),
        (ENTHUSIASTIC, "Enthusiastic"),
        (CONCISE, "Concise"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cover_letters"
    )
    job_application = models.ForeignKey(
        JobApplication, on_delete=models.CASCADE,
        related_name="cover_letters", null=True, blank=True,
    )
    resume = models.ForeignKey(
        Resume, on_delete=models.SET_NULL, null=True, blank=True
    )
    content = models.TextField()
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default=FORMAL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Cover letter #{self.pk} ({self.user.username})"
