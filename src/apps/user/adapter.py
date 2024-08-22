from typing import Any

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for handling social account authentication and user signup.
    """

    def is_open_for_signup(self, request: HttpRequest, sociallogin: Any):
        """
        Determines whether signup is open for the given social login.

        :request (HttpRequest): The current request object.
        :sociallogin (SocialLogin): The social login instance.

        Returns:
            bool: True if signup is open, otherwise False.
        """
        return True

    def pre_social_login(self, request, sociallogin):
        """
        Prepares for a social login by performing necessary checks and actions before the user is logged in.

        :request (HttpRequest): The current request object.
        :sociallogin (SocialLogin): The social login instance.

        Raises:
            ImmediateHttpResponse: If the user is not authorized, redirects to the login page.
        """
        user = sociallogin.user
        print(f"user : {user}")
        User = get_user_model()
        user_obj = User.objects.filter(email=user.email)

        if len(user_obj) == 0:

            messages.error(
                request,
                "You are not authorized to access application, Please contact provider !!",
            )
            raise ImmediateHttpResponse(HttpResponseRedirect(reverse("user:login")))

        elif user and not sociallogin.is_existing:
            sociallogin.connect(request, user_obj[0])

    def save_user(self, request, sociallogin, form=None):
        """
        Override this method and perform to save with user with social login and save user as account user.

        :request (HttpRequest): The current request object.
        :sociallogin (SocialLogin): The social login instance.
        :form (optional): The form instance, if any.

        Returns:
            Any: The saved user object.
        """
        user = super(CustomSocialAccountAdapter, self).save_user(request, sociallogin, form)
        return user
