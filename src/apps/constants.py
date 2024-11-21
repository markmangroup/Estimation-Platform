"""
Global error message to be used for JSON responses in the application.
"""

import logging

from django.http import JsonResponse

# Base Error Response
ERROR_RESPONSE = {"status": "error", "message": "Something went wrong :("}

# Base Logger
LOGGER = logging.getLogger(__name__)

# Base Response
RESPONSE_CODE_0: JsonResponse = JsonResponse(
    {
        "code": 0,
        "message": "success",
    }
)
