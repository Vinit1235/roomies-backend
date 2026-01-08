"""
Supabase Authentication Service for Roomies

This module handles OAuth (Google, GitHub) authentication via Supabase.
It provides methods for:
- OAuth login initiation
- OAuth callback handling  
- User session management
- Linking OAuth users to local database
"""

import os
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://nlhhssjsbacghfrmacru.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# OAuth Redirect URL (configure this in Supabase Dashboard)
OAUTH_REDIRECT_URL = os.environ.get("OAUTH_REDIRECT_URL", "http://localhost:5000/auth/callback")

try:
    from supabase import create_client, Client
    
    def get_supabase_client() -> Optional[Client]:
        """Get Supabase client with anon key for public operations."""
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            print("⚠️ Supabase credentials not configured")
            return None
        try:
            return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        except Exception as e:
            print(f"❌ Failed to create Supabase client: {e}")
            return None
    
    def get_supabase_admin_client() -> Optional[Client]:
        """Get Supabase client with service key for admin operations."""
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("⚠️ Supabase service credentials not configured")
            return None
        try:
            return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        except Exception as e:
            print(f"❌ Failed to create Supabase admin client: {e}")
            return None
    
    SUPABASE_AVAILABLE = True
    print("✅ Supabase client initialized")

except ImportError as e:
    print(f"⚠️ Supabase not installed: {e}")
    SUPABASE_AVAILABLE = False
    
    def get_supabase_client():
        return None
    
    def get_supabase_admin_client():
        return None


class SupabaseAuthService:
    """
    Service class for Supabase OAuth authentication.
    
    Supports:
    - Google OAuth
    - GitHub OAuth
    - Email/Password (optional)
    """
    
    SUPPORTED_PROVIDERS = ['google', 'github']
    
    def __init__(self):
        self.client = get_supabase_client()
        self.admin_client = get_supabase_admin_client()
        self.redirect_url = OAUTH_REDIRECT_URL
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase auth is available."""
        return self.client is not None
    
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
            
            # Generate OAuth sign-in URL
            response = self.client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_url,
                    "scopes": "email profile" if provider == "google" else "user:email"
                }
            })
            
            if response and hasattr(response, 'url') and response.url:
                return True, response.url
            else:
                return False, "Failed to generate OAuth URL"
                
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
            user_data = None
            
            if code:
                # Exchange code for session
                response = self.client.auth.exchange_code_for_session({"auth_code": code})
                if response and response.user:
                    user_data = self._extract_user_data(response.user)
            elif access_token:
                # Get user from access token
                response = self.client.auth.get_user(access_token)
                if response and response.user:
                    user_data = self._extract_user_data(response.user)
            
            if user_data:
                return True, user_data
            else:
                return False, {"error": "Failed to retrieve user data"}
                
        except Exception as e:
            return False, {"error": f"Callback handling error: {str(e)}"}
    
    def _extract_user_data(self, user) -> Dict[str, Any]:
        """Extract relevant user data from Supabase user object."""
        user_metadata = user.user_metadata or {}
        
        return {
            "supabase_id": user.id,
            "email": user.email,
            "name": user_metadata.get("full_name") or user_metadata.get("name") or user.email.split("@")[0],
            "avatar_url": user_metadata.get("avatar_url") or user_metadata.get("picture"),
            "provider": user.app_metadata.get("provider") if user.app_metadata else "email",
            "email_verified": user.email_confirmed_at is not None,
            "raw_metadata": user_metadata
        }
    
    def get_user_by_email(self, email: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Get Supabase user by email using admin client.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success, user_data_or_none)
        """
        if not self.admin_client:
            return False, None
        
        try:
            # Use admin API to get user by email
            response = self.admin_client.auth.admin.list_users()
            
            for user in response:
                if user.email and user.email.lower() == email.lower():
                    return True, self._extract_user_data(user)
            
            return True, None  # Success but user not found
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return False, None
    
    def sign_out(self, access_token: str = None) -> bool:
        """Sign out user from Supabase."""
        if not self.is_available:
            return False
        
        try:
            self.client.auth.sign_out()
            return True
        except Exception:
            return False


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
