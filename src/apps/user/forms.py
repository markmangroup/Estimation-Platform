from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import Permissions, User


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

    def clean_email(self):
        """
        Validate that the email is not already in use
        by a different user with the same name.
        """
        first_name = self.cleaned_data.get("first_name")
        last_name = self.cleaned_data.get("last_name")
        email = self.cleaned_data.get("email")

        # Check if an existing user has the same email, first name, and last name
        user_with_same_details = User.objects.filter(email=email, first_name=first_name, last_name=last_name).exists()

        # Check if the email is already used by any user
        email_exists = User.objects.filter(email=email).exists()

        # Raise a validation error if the email exists and the user does not match
        if email_exists and not user_with_same_details:
            raise ValidationError("Email address already exists; please try different email addresses.")

        return email

    def clean(self):
        """
        Check for existing users with the same name and email.
        """
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        email = cleaned_data.get("email")

        # Check if a user with the same first name, last name, and email exists
        user_with_same_info = User.objects.filter(
            first_name=first_name, last_name=last_name, email=email, application_type__contains=User.PROPOSAL
        ).exists()

        # Raise a validation error if a user exists with the same email
        if user_with_same_info:
            raise ValidationError("User already exists; please try different details.")

        return cleaned_data


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "is_superuser", "is_active"]

        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
        }

        labels = {
            "is_superuser": "Admin",
            "is_active": "Enabled/Disabled",
        }


class RentalUserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "mobile",
            "is_superuser",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        labels = {
            "is_superuser": "Admin",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_email(self):
        """
        Validate that the email is not already in use
        by a different user with the same name.
        """
        first_name = self.cleaned_data.get("first_name")
        last_name = self.cleaned_data.get("last_name")
        email = self.cleaned_data.get("email")

        # Check if an existing user has the same email, first name, and last name
        user_with_same_details = User.objects.filter(email=email, first_name=first_name, last_name=last_name).exists()

        # Check if the email is already used by any user
        email_exists = User.objects.filter(email=email).exists()

        # Raise a validation error if the email exists and the user does not match
        if email_exists and not user_with_same_details:
            raise ValidationError("Email address already exists; please try different email addresses.")

        return email

    def clean(self):
        """
        Check for existing users with the same name and email.
        """
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")
        email = cleaned_data.get("email")

        # Check if a user with the same first name, last name, and email exists
        user_with_same_info = User.objects.filter(
            first_name=first_name, last_name=last_name, email=email, application_type__contains=User.RENTAL
        ).exists()

        # Raise a validation error if a user exists with the same email
        if user_with_same_info:
            raise ValidationError("User already exists; please try different details.")

        return cleaned_data


class RentalUserUpdateForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permissions.objects.all(),  # Ensure this queryset returns permissions from the DB
        widget=forms.SelectMultiple(attrs={"class": "select2"}),
        required=False,
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "mobile", "permissions", "is_superuser", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "is_superuser": "Admin",
            "is_active": "Enabled/Disabled",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.permissions.exists():
            self.initial["permissions"] = self.instance.permissions.all()

    def clean_permissions(self):
        permissions = self.cleaned_data.get("permissions")

        if permissions:
            valid_permissions = Permissions.objects.filter(id__in=[p.id for p in permissions])
            if valid_permissions.count() != len(permissions):
                raise ValidationError("Some permissions are invalid.")

        return permissions
