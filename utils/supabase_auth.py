"""
Supabase OAuth Authentication Service for Roomies

This module handles OAuth (Google, GitHub) authentication via Supabase
using direct HTTP requests - NO supabase package required.

It provides methods for:
- OAuth login initiation
- OAuth callback handling  
- User session management
- Linking OAuth users to local database
"""

import os
import requests
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nlhhssjsbacghfrmacru.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# OAuth Redirect URL (configure this in Supabase Dashboard)
OAUTH_REDIRECT_URL = os.environ.get("OAUTH_REDIRECT_URL", "http://localhost:5000/auth/callback")


class SupabaseAuthService:
    """
    Service class for Supabase OAuth authentication.
    Uses direct HTTP requests - no supabase package needed.
    
    Supports:
    - Google OAuth
    - GitHub OAuth
    """
    
    SUPPORTED_PROVIDERS = ['google', 'github']
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.anon_key = SUPABASE_ANON_KEY
        self.service_key = SUPABASE_SERVICE_KEY
        self.redirect_url = OAUTH_REDIRECT_URL
        
        if self.anon_key:
            print("✅ Supabase OAuth configured (HTTP mode)")
        else:
            print("⚠️ Supabase OAuth not configured (missing SUPABASE_ANON_KEY)")
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase auth is available."""
        return bool(self.supabase_url and self.anon_key)
    
    def _get_headers(self, use_service_key: bool = False) -> Dict[str, str]:
        """Get headers for Supabase API requests."""
        key = self.service_key if use_service_key else self.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    
    def get_oauth_url(self, provider: str, redirect_to: str = None) -> Tuple[bool, str]:
        """
        Generate OAuth URL for a provider.
        
        Args:
            provider: OAuth provider ('google' or 'github')
            redirect_to: Optional custom redirect URL after auth
            
        Returns:
            Tuple of (success, url_or_error_message)
        """
        if not self.is_available:
            return False, "Supabase authentication not configured"
        
        provider = provider.lower()
        if provider not in self.SUPPORTED_PROVIDERS:
            return False, f"Unsupported OAuth provider: {provider}. Supported: {', '.join(self.SUPPORTED_PROVIDERS)}"
        
        try:
            redirect_url = redirect_to or self.redirect_url
            
            # Build OAuth URL using Supabase Auth endpoint
            # Format: {SUPABASE_URL}/auth/v1/authorize?provider={provider}&redirect_to={redirect_url}
            params = {
                "provider": provider,
                "redirect_to": redirect_url,
            }
            
            # Add scopes based on provider
            if provider == "google":
                params["scopes"] = "email profile"
            elif provider == "github":
                params["scopes"] = "user:email"
            
            oauth_url = f"{self.supabase_url}/auth/v1/authorize?{urlencode(params)}"
            
            return True, oauth_url
                
        except Exception as e:
            return False, f"OAuth error: {str(e)}"
    
    def handle_oauth_callback(self, code: str = None, access_token: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Handle OAuth callback and extract user information.
        
        Args:
            code: Authorization code from OAuth callback
            access_token: Access token (if exchanged client-side)
            
        Returns:
            Tuple of (success, user_data_or_error)
        """
        if not self.is_available:
            return False, {"error": "Supabase authentication not configured"}
        
        try:
            if access_token:
                # Get user info using access token
                return self._get_user_from_token(access_token)
            
            if code:
                # Exchange code for session/token
                return self._exchange_code_for_session(code)
            
            return False, {"error": "No authorization code or access token provided"}
                
        except Exception as e:
            return False, {"error": f"Callback handling error: {str(e)}"}
    
    def _exchange_code_for_session(self, code: str) -> Tuple[bool, Dict[str, Any]]:
        """Exchange authorization code for a session."""
        try:
            url = f"{self.supabase_url}/auth/v1/token?grant_type=authorization_code"
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"auth_code": code}
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                
                if access_token:
                    return self._get_user_from_token(access_token)
                
                # Try to extract user from response directly
                user = data.get("user")
                if user:
                    return True, self._extract_user_data(user)
            
            return False, {"error": f"Token exchange failed: {response.text}"}
            
        except Exception as e:
            return False, {"error": f"Code exchange error: {str(e)}"}
    
    def _get_user_from_token(self, access_token: str) -> Tuple[bool, Dict[str, Any]]:
        """Get user information from access token."""
        try:
            url = f"{self.supabase_url}/auth/v1/user"
            
            headers = {
                "apikey": self.anon_key,
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                user = response.json()
                return True, self._extract_user_data(user)
            
            return False, {"error": f"Failed to get user: {response.text}"}
            
        except Exception as e:
            return False, {"error": f"Get user error: {str(e)}"}
    
    def _extract_user_data(self, user: Dict) -> Dict[str, Any]:
        """Extract relevant user data from Supabase user object."""
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})
        
        # Get name from various possible fields
        name = (
            user_metadata.get("full_name") or 
            user_metadata.get("name") or 
            user_metadata.get("preferred_username") or
            user.get("email", "User").split("@")[0]
        )
        
        return {
            "supabase_id": user.get("id"),
            "email": user.get("email"),
            "name": name,
            "avatar_url": user_metadata.get("avatar_url") or user_metadata.get("picture"),
            "provider": app_metadata.get("provider", "email"),
            "email_verified": user.get("email_confirmed_at") is not None,
            "raw_metadata": user_metadata
        }
    
    def verify_token(self, access_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Verify an access token and get user info."""
        return self._get_user_from_token(access_token)
    
    def signup_with_email(self, email: str, password: str, user_metadata: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Sign up a new user with email and password.
        Supabase will automatically send a verification email.
        
        Args:
            email: User's email address
            password: User's password
            user_metadata: Additional user data (name, role, etc.)
            
        Returns:
            Tuple of (success, user_data_or_error)
        """
        if not self.is_available:
            return False, {"error": "Supabase authentication not configured"}
        
        try:
            url = f"{self.supabase_url}/auth/v1/signup"
            
            payload = {
                "email": email,
                "password": password
            }
            
            if user_metadata:
                payload["data"] = user_metadata  # User metadata goes in 'data' field
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                user = data.get("user")
                
                if user:
                    return True, {
                        "supabase_id": user.get("id"),
                        "email": user.get("email"),
                        "email_verified": user.get("email_confirmed_at") is not None,
                        "message": "Signup successful! Please check your email to verify your account.",
                        "user": user
                    }
                
                return True, {
                    "message": "Signup successful! Please check your email to verify your account.",
                    "data": data
                }
            
            # Handle error responses
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or error_data.get("error_description") or "Signup failed"
            
            return False, {"error": error_msg}
            
        except Exception as e:
            return False, {"error": f"Signup error: {str(e)}"}
    
    def login_with_email(self, email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Log in a user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (success, session_data_or_error)
        """
        if not self.is_available:
            return False, {"error": "Supabase authentication not configured"}
        
        try:
            url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
            
            payload = {
                "email": email,
                "password": password
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                user = data.get("user")
                access_token = data.get("access_token")
                
                if user:
                    user_data = self._extract_user_data(user)
                    user_data["access_token"] = access_token
                    user_data["refresh_token"] = data.get("refresh_token")
                    return True, user_data
                
                return False, {"error": "Login successful but user data missing"}
            
            # Handle error responses  
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or error_data.get("error_description") or "Login failed"
            
            # Check if email not verified
            if "email not confirmed" in error_msg.lower():
                return False, {"error": "Please verify your email before logging in. Check your inbox for the verification link."}
            
            return False, {"error": error_msg}
            
        except Exception as e:
            return False, {"error": f"Login error: {str(e)}"}
    
    def resend_verification_email(self, email: str) -> Tuple[bool, str]:
        """
        Resend email verification link.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, message)
        """
        if not self.is_available:
            return False, "Supabase authentication not configured"
        
        try:
            url = f"{self.supabase_url}/auth/v1/resend"
            
            payload = {
                "type": "signup",
                "email": email
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code in [200, 201]:
                return True, "Verification email sent! Please check your inbox."
            
            error_data = response.json() if response.text else {}
            error_msg = error_data.get("message") or error_data.get("error_description") or "Failed to resend email"
            
            return False, error_msg
            
        except Exception as e:
            return False, f"Error: {str(e)}"


# Singleton instance
supabase_auth = SupabaseAuthService()


# Convenience functions for routes
def get_google_oauth_url(redirect_to: str = None) -> Tuple[bool, str]:
    """Get Google OAuth URL."""
    return supabase_auth.get_oauth_url("google", redirect_to)


def get_github_oauth_url(redirect_to: str = None) -> Tuple[bool, str]:
    """Get GitHub OAuth URL."""
    return supabase_auth.get_oauth_url("github", redirect_to)


def handle_oauth_callback(code: str = None, access_token: str = None) -> Tuple[bool, Dict[str, Any]]:
    """Handle OAuth callback."""
    return supabase_auth.handle_oauth_callback(code, access_token)


def is_oauth_available() -> bool:
    """Check if OAuth is available."""
    return supabase_auth.is_available


def signup_with_email(email: str, password: str, user_metadata: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
    """Sign up user with email/password - Supabase sends verification email."""
    return supabase_auth.signup_with_email(email, password, user_metadata)


def login_with_email(email: str, password: str) -> Tuple[bool, Dict[str, Any]]:
    """Login user with email/password."""
    return supabase_auth.login_with_email(email, password)


def resend_verification_email(email: str) -> Tuple[bool, str]:
    """Resend email verification link."""
    return supabase_auth.resend_verification_email(email)
