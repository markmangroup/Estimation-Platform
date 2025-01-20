"""
Google Map Service
"""

import traceback
from typing import Dict, Optional

import requests
from django.conf import settings


class GoogleMap:
    """Google Map API service for geocoding addresses."""

    def __init__(self):
        """
        Initialize constructor with API key.

        :prams :Google Maps API key for authentication.
        """
        self.URL = "https://maps.googleapis.com/maps/api/geocode/json"
        self.API_KEY = settings.GOOGLE_API_KEY

    def get_geo_code_from_address(
        self, address1: str, city: str, state: str, country: str
    ) -> Optional[Dict[str, float]]:
        """Return Geo code for provided address."""
        address = f"{address1},{city},{state},{country}".strip()
        if not address:
            print("Error: Address cannot be empty.")
            return None

        try:
            params = {
                "address": address,
                "key": self.API_KEY,
            }
            response = requests.get(self.URL, params=params)

            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code}")
                return None

            data = response.json()
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                print("Location:", location)
                return location
            else:
                print(f"Error: Geocoding API error: {data['status']}")
                return None

        except Exception as e:
            print("Exception:", e)
            print(traceback.format_exc())
            return None
