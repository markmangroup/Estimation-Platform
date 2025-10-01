"""
Custom Context Processors for Application Access.
"""
from django.conf import settings

def get_user_application_access(request) -> dict:
    """
    Determine if the authenticated user has access to the Proposal/Estimation application.

    :prams request: The HTTP request object containing user information.
    """
    # All authenticated users have access to estimation platform
    access_granted = request.user.is_authenticated

    # Return access status as a context dictionary
    return {"ACCESS": access_granted}

def get_google_api_key(request) -> dict:
    return {"GOOGLE_API_KEY" : settings.GOOGLE_API_KEY}