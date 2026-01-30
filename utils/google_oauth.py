"""
Google OAuth 2.0 Authentication for Roomies
Direct integration without external libraries (uses requests only)
"""

import os
import secrets
import requests
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

# Google OAuth Endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthService:
    """
    Service class for Google OAuth 2.0 authentication.
    Uses direct HTTP requests - no google-auth library needed.
    """
    
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        
        if self.client_id and self.client_secret:
            print("✅ Google OAuth configured")
        else:
            print("⚠️ Google OAuth not configured (missing credentials)")
    
    @property
    def is_available(self) -> bool:
        """Check if Google OAuth is available."""
        return bool(self.client_id and self.client_secret)
    
    def get_authorization_url(self, role: str = "student") -> Tuple[bool, str]:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            role: User role ('student' or 'owner')
            
        Returns:
            Tuple of (success, url_or_error_message)
        """
        if not self.is_available:
            return False, "Google OAuth not configured"
        
        try:
            # Generate state token for CSRF protection
            # Format: role:random_token
            state = f"{role}:{secrets.token_urlsafe(32)}"
            
            # Build authorization URL
            params = {
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "online",  # Don't need refresh token
                "prompt": "select_account",  # Always show account selector
            }
            
            auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
            return True, auth_url
            
        except Exception as e:
            return False, f"OAuth error: {str(e)}"
    
    def exchange_code_for_token(self, code: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Tuple of (success, token_data_or_error)
        """
        if not self.is_available:
            return False, {"error": "Google OAuth not configured"}
        
        try:
            # Exchange code for token
            data = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            }
            
            response = requests.post(GOOGLE_TOKEN_URL, data=data)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error_description") or error_data.get("error") or "Token exchange failed"
                return False, {"error": error_msg}
                
        except Exception as e:
            return False, {"error": f"Token exchange error: {str(e)}"}
    
    def get_user_info(self, access_token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            Tuple of (success, user_data_or_error)
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            response = requests.get(GOOGLE_USERINFO_URL, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Extract relevant fields
                return True, {
                    "google_id": user_data.get("id"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "given_name": user_data.get("given_name"),
                    "family_name": user_data.get("family_name"),
                    "picture": user_data.get("picture"),
                    "email_verified": user_data.get("verified_email", False),
                    "locale": user_data.get("locale"),
                }
            else:
                return False, {"error": "Failed to get user info"}
                
        except Exception as e:
            return False, {"error": f"Get user info error: {str(e)}"}
    
    def authenticate(self, code: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Complete OAuth flow: exchange code for token and get user info.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Tuple of (success, user_data_or_error)
        """
        # Exchange code for token
        success, token_data = self.exchange_code_for_token(code)
        if not success:
            return False, token_data
        
        access_token = token_data.get("access_token")
        if not access_token:
            return False, {"error": "No access token received"}
        
        # Get user info
        return self.get_user_info(access_token)


# Singleton instance
google_oauth = GoogleOAuthService()


# Convenience functions for routes
def get_google_auth_url(role: str = "student") -> Tuple[bool, str]:
    """Get Google OAuth authorization URL."""
    return google_oauth.get_authorization_url(role)


def authenticate_google_user(code: str) -> Tuple[bool, Dict[str, Any]]:
    """Authenticate user with Google OAuth code."""
    return google_oauth.authenticate(code)


def is_google_oauth_available() -> bool:
    """Check if Google OAuth is available."""
    return google_oauth.is_available
