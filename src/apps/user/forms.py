from django import forms
from django.contrib.auth import authenticate


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(
        attrs={'placeholder': 'Enter email'}))
    password = forms.CharField(label="Password", widget=forms.PasswordInput(
        attrs={'placeholder': 'Enter password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError(
                    "Invalid email or password. Please try again."
                )
        return cleaned_data

    def get_user(self):
        return self.user if hasattr(self, "user") else None
