import logging

from django.http import HttpResponseRedirect
from django.urls import reverse

logger = logging.getLogger(__name__)


class CheckUserAppTypeMiddleware:
    """
    Middleware to check if the authenticated user has access to specific application types
    based on the URL path. Redirects users without the necessary permissions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the incoming request and check user application type.

        :prams request: The HTTP request object.
        """
        # Call the next middleware or view
        response = self.get_response(request)

        # Ensure the user is authenticated
        if request.user.is_authenticated:
            # Extract the first part of the path after the leading slash
            path_parts = request.path.split("/")

            # Check the user's application type based on the path
            if len(path_parts) > 1:
                app_type = path_parts[1].lower()  # Normalize to lowercase for consistency

                if app_type == "rental":
                    if "Rental" not in request.user.application_type:
                        logger.warning(f"User {request.user} attempted to access Rental applications.")
                        return HttpResponseRedirect(reverse("proposal_app:opportunity:opportunity-list"))

                elif app_type == "proposal":
                    if "Proposal" not in request.user.application_type:
                        logger.warning(f"User {request.user} attempted to access Proposal applications.")
                        return HttpResponseRedirect(reverse("rental:map_view"))

        return response
