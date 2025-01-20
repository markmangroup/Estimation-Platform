"""
Custom Context Processors for Application Access.
"""


def get_user_application_access(request) -> dict:
    """
    Determine if the authenticated user has access to both 'Rental'
    and 'Proposal' applications.

    :prams request: The HTTP request object containing user information.
    """
    # Get the authenticated user from the request
    user = request.user

    # Initialize access status
    access_granted = False

    # Check if the user is authenticated and has both application types
    if user.is_authenticated:
        has_rental_access = "Rental" in user.application_type
        has_proposal_access = "Proposal" in user.application_type

        # Grant access if both application types are present
        access_granted = has_rental_access and has_proposal_access

    # Return access status as a context dictionary
    return {"ACCESS": access_granted}
