from django import forms
from django.conf import settings

from .models import JobApplication, Resume


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ("title", "file")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Software CV"}),
        }

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            raise forms.ValidationError("Please choose a file.")
        if f.size > settings.MAX_RESUME_SIZE:
            raise forms.ValidationError("File is too large (max 5 MB).")
        name = f.name.lower()
        if not name.endswith((".pdf", ".docx", ".txt")):
            raise forms.ValidationError("Please upload a PDF, DOCX, or TXT file.")
        return f


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = (
            "company_name", "job_title", "job_link",
            "job_description", "status", "follow_up_date",
        )
        widgets = {
            "job_description": forms.Textarea(attrs={"rows": 6}),
            "follow_up_date": forms.DateInput(attrs={"type": "date"}),
            "job_link": forms.URLInput(attrs={"placeholder": "https://..."}),
        }


class GenerateLetterForm(forms.Form):
    """Form on the 'generate cover letter' screen."""

    resume = forms.ModelChoiceField(
        queryset=Resume.objects.none(), required=True, label="Resume",
    )
    company_name = forms.CharField(max_length=150)
    job_title = forms.CharField(max_length=150)
    job_link = forms.URLField(required=False, label="Job link (optional)")
    job_description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text="Paste the job description here for a tailored letter.",
    )
    tone = forms.ChoiceField(
        choices=[
            ("formal", "Formal"),
            ("enthusiastic", "Enthusiastic"),
            ("concise", "Concise"),
        ],
        initial="formal",
    )
    save_application = forms.BooleanField(
        required=False, initial=True,
        label="Also save this to my application tracker",
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["resume"].queryset = Resume.objects.filter(user=user)
