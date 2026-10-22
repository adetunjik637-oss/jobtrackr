from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=150, required=False, label="Full name")

    class Meta:
        model = User
        fields = ("username", "email", "full_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Profile is created by signal; fill in the name.
            full_name = self.cleaned_data.get("full_name", "")
            if full_name:
                profile = user.profile
                profile.full_name = full_name
                profile.save(update_fields=["full_name", "updated_at"])
        return user
