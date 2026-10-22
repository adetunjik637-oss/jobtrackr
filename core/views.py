from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GenerateLetterForm, JobApplicationForm, ResumeForm
from .models import CoverLetter, JobApplication, Resume
from .services.openai_service import CoverLetterError, generate_cover_letter
from .services.resume_parser import ResumeParseError, extract_text


def landing(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/landing.html")


@login_required
def dashboard(request):
    apps_qs = JobApplication.objects.filter(user=request.user)
    status_counts = {row["status"]: row["n"] for row in
                     apps_qs.values("status").annotate(n=Count("id"))}
    ordered_statuses = [
        (value, label, status_counts.get(value, 0))
        for value, label in JobApplication.STATUS_CHOICES
    ]
    context = {
        "profile": request.user.profile,
        "total_apps": apps_qs.count(),
        "recent_apps": apps_qs[:5],
        "letters_remaining": request.user.profile.letters_remaining(),
        "status_summary": ordered_statuses,
        "resume_count": Resume.objects.filter(user=request.user).count(),
    }
    return render(request, "core/dashboard.html", context)


# --- Resumes ----------------------------------------------------------------

@login_required
def resume_list(request):
    resumes = Resume.objects.filter(user=request.user)
    return render(request, "core/resume_list.html", {"resumes": resumes})


@login_required
def resume_upload(request):
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            try:
                resume.extracted_text = extract_text(form.cleaned_data["file"])
            except ResumeParseError as exc:
                messages.error(request, str(exc))
                return render(request, "core/resume_upload.html", {"form": form})
            resume.save()
            messages.success(request, "Resume uploaded and read successfully.")
            return redirect("resume_list")
    else:
        form = ResumeForm()
    return render(request, "core/resume_upload.html", {"form": form})


@login_required
def resume_delete(request, pk):
    resume = get_object_or_404(Resume, pk=pk, user=request.user)
    if request.method == "POST":
        resume.delete()
        messages.success(request, "Resume deleted.")
        return redirect("resume_list")
    return render(request, "core/confirm_delete.html",
                  {"object": resume, "kind": "resume"})


# --- Cover letter generation ------------------------------------------------

@login_required
def generate_letter(request):
    profile = request.user.profile

    if not Resume.objects.filter(user=request.user).exists():
        messages.info(request, "Upload a resume first, then generate a cover letter.")
        return redirect("resume_upload")

    if not profile.can_generate_letter():
        messages.warning(
            request,
            "You've used all your free cover letters this month. "
            "Upgrade for unlimited letters.",
        )
        return redirect("pricing")

    if request.method == "POST":
        form = GenerateLetterForm(request.POST, user=request.user)
        if form.is_valid():
            data = form.cleaned_data
            resume = data["resume"]
            try:
                content = generate_cover_letter(
                    resume_text=resume.extracted_text,
                    job_title=data["job_title"],
                    company_name=data["company_name"],
                    job_description=data["job_description"],
                    tone=data["tone"],
                )
            except CoverLetterError as exc:
                messages.error(request, str(exc))
                return render(request, "core/generate.html", {"form": form})

            application = None
            if data.get("save_application"):
                application = JobApplication.objects.create(
                    user=request.user,
                    company_name=data["company_name"],
                    job_title=data["job_title"],
                    job_link=data.get("job_link", ""),
                    job_description=data["job_description"],
                    status=JobApplication.APPLIED,
                )

            letter = CoverLetter.objects.create(
                user=request.user,
                job_application=application,
                resume=resume,
                content=content,
                tone=data["tone"],
            )
            # Only count against the free tier for non-subscribers.
            if not profile.is_subscribed:
                profile.record_letter_generated()

            messages.success(request, "Your cover letter is ready.")
            return redirect("letter_detail", pk=letter.pk)
    else:
        form = GenerateLetterForm(user=request.user)

    return render(request, "core/generate.html", {
        "form": form,
        "letters_remaining": profile.letters_remaining(),
    })


@login_required
def letter_detail(request, pk):
    letter = get_object_or_404(CoverLetter, pk=pk, user=request.user)
    if request.method == "POST":
        # Allow inline edit of the content.
        letter.content = request.POST.get("content", letter.content)
        letter.save(update_fields=["content"])
        messages.success(request, "Changes saved.")
        return redirect("letter_detail", pk=letter.pk)
    return render(request, "core/letter_detail.html", {"letter": letter})


@login_required
def letter_list(request):
    letters = CoverLetter.objects.filter(user=request.user)
    return render(request, "core/letter_list.html", {"letters": letters})


@login_required
def letter_download(request, pk):
    letter = get_object_or_404(CoverLetter, pk=pk, user=request.user)
    filename = f"cover-letter-{letter.pk}.txt"
    response = HttpResponse(letter.content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# --- Application tracker -----------------------------------------------------

@login_required
def application_list(request):
    applications = JobApplication.objects.filter(user=request.user)
    status_filter = request.GET.get("status")
    if status_filter:
        applications = applications.filter(status=status_filter)
    return render(request, "core/application_list.html", {
        "applications": applications,
        "status_choices": JobApplication.STATUS_CHOICES,
        "active_status": status_filter or "",
    })


@login_required
def application_create(request):
    if request.method == "POST":
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.user = request.user
            app.save()
            messages.success(request, "Application added.")
            return redirect("application_list")
    else:
        form = JobApplicationForm(initial={"status": JobApplication.SAVED})
    return render(request, "core/application_form.html",
                  {"form": form, "mode": "create"})


@login_required
def application_detail(request, pk):
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    return render(request, "core/application_detail.html", {"application": app})


@login_required
def application_edit(request, pk):
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == "POST":
        form = JobApplicationForm(request.POST, instance=app)
        if form.is_valid():
            form.save()
            messages.success(request, "Application updated.")
            return redirect("application_detail", pk=app.pk)
    else:
        form = JobApplicationForm(instance=app)
    return render(request, "core/application_form.html",
                  {"form": form, "mode": "edit", "application": app})


@login_required
def application_delete(request, pk):
    app = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == "POST":
        app.delete()
        messages.success(request, "Application deleted.")
        return redirect("application_list")
    return render(request, "core/confirm_delete.html",
                  {"object": app, "kind": "application"})
