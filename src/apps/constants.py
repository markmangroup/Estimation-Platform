"""
Global error message to be used for JSON responses in the application.
"""

import logging

ERROR_RESPONSE = {"status": "error", "message": "Something went wrong, please try again"}
LOGGER = logging.getLogger(__name__)
