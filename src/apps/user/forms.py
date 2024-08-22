from django import forms
from django.contrib.auth import authenticate

from .models import User


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"placeholder": "Enter email"}))
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({"class": "form-control"})
        self.fields["password"].widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError("Invalid email or password. Please try again.")
        return cleaned_data

    def get_user(self):
        return self.user if hasattr(self, "user") else None


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "is_superuser",
        ]

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

        labels = {
            "is_superuser": "Admin",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_active"]

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
        }

        labels = {"is_active": "Enabled/Disabled"}
