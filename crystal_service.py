import requests
from typing import Dict, Any, Optional
import os
from requests.exceptions import RequestException

class CrystalService:
    def __init__(self):
        self.base_url = "https://api.crystalknows.com/v1"
        self.api_token = os.getenv('CRYSTAL_KNOWS_TOKEN')
        
        # Validate configuration
        if not self.api_token:
            raise ValueError("Missing CRYSTAL_KNOWS_TOKEN. Please check your .env file.")
        
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token.strip()}"
        }

    def test_connection(self) -> bool:
        """Test the Crystal API connection and credentials."""
        try:
            # Test authentication with profiles endpoint
            response = requests.get(
                f"{self.base_url}/profiles",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except RequestException as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 401:
                    raise ConnectionError("Invalid Bearer token. Please check your CRYSTAL_KNOWS_TOKEN.")
                elif e.response.status_code == 403:
                    raise ConnectionError("Access forbidden. Please check your API permissions.")
                elif e.response.status_code == 429:
                    raise ConnectionError("Rate limit exceeded. Please try again later.")
            raise ConnectionError(f"Failed to connect to Crystal API: {str(e)}")

    def get_profile_by_email(self, email: str) -> Dict[str, Any]:
        """Fetch a personality profile using email address."""
        try:
            # Using Profiles endpoint as mentioned in docs
            response = requests.get(
                f"{self.base_url}/profiles",
                params={"email": email},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 404:
                    raise ValueError(f"No profile found for email: {email}")
                elif e.response.status_code == 401:
                    raise ConnectionError("Authentication failed. Please check your Crystal API token.")
                elif e.response.status_code == 402:
                    raise ConnectionError("Payment required. Please check your subscription status.")
            raise Exception(f"Failed to fetch Crystal profile: {str(e)}")

    def get_profile_by_linkedin(self, linkedin_url: str) -> Dict[str, Any]:
        """Fetch a personality profile using LinkedIn URL."""
        try:
            # Using correct URL format with linkedin_url parameter
            response = requests.get(
                f"{self.base_url}/profiles",
                params={"linkedin_url": linkedin_url},  # Changed back to linkedin_url
                headers=self.headers,
                timeout=10  # Added timeout for consistency
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if hasattr(e, 'response'):
                if e.response.status_code == 404:
                    raise ValueError(f"No profile found for LinkedIn URL: {linkedin_url}")
                elif e.response.status_code == 401:
                    raise ConnectionError("Invalid Bearer token. Please check your CRYSTAL_KNOWS_TOKEN.")
                elif e.response.status_code == 403:
                    raise ConnectionError("Access forbidden. Please check your API permissions.")
                elif e.response.status_code == 429:
                    raise ConnectionError("Rate limit exceeded. Please try again later.")
            raise Exception(f"Failed to fetch Crystal profile: {str(e)}")

    def analyze_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze text to generate a personality profile."""
        try:
            payload = {
                "text": text,
                "metadata": metadata or {}
            }
            
            # Using Analysis endpoint as mentioned in docs
            response = requests.post(
                f"{self.base_url}/analysis",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise Exception(f"Failed to analyze text with Crystal: {str(e)}") 