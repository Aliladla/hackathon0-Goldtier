"""
Gmail OAuth2 authentication utilities for Personal AI Employee.

Handles OAuth2 flow, token refresh, and credential validation.
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']


class GmailAuthManager:
    """Manages Gmail OAuth2 authentication."""

    def __init__(self, credentials_path: str, token_path: str):
        """
        Initialize Gmail auth manager.

        Args:
            credentials_path: Path to OAuth2 credentials JSON
            token_path: Path to store/load OAuth2 token
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.creds = None

    def authenticate(self) -> Credentials:
        """
        Authenticate with Gmail API using OAuth2.

        Returns:
            Credentials object

        Raises:
            FileNotFoundError: If credentials file not found
            Exception: If authentication fails
        """
        # Check if token exists and is valid
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired token
                self.creds.refresh(Request())
            else:
                # Run OAuth2 flow
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found at {self.credentials_path}\n"
                        f"Please download OAuth2 credentials from Google Cloud Console:\n"
                        f"1. Go to https://console.cloud.google.com/\n"
                        f"2. Create a project and enable Gmail API\n"
                        f"3. Create OAuth2 credentials (Desktop app)\n"
                        f"4. Download JSON and save to {self.credentials_path}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save token for future use
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        return self.creds

    def get_gmail_service(self):
        """
        Get authenticated Gmail API service.

        Returns:
            Gmail API service object
        """
        if not self.creds:
            self.authenticate()

        return build('gmail', 'v1', credentials=self.creds)

    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated with valid credentials.

        Returns:
            True if authenticated, False otherwise
        """
        if not self.token_path.exists():
            return False

        try:
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
                return creds and creds.valid
        except Exception:
            return False

    def revoke_authentication(self):
        """Revoke authentication and delete token."""
        if self.token_path.exists():
            self.token_path.unlink()
        self.creds = None


def setup_gmail_auth(credentials_path: str, token_path: str) -> bool:
    """
    Setup Gmail authentication (interactive).

    Args:
        credentials_path: Path to OAuth2 credentials JSON
        token_path: Path to store OAuth2 token

    Returns:
        True if successful, False otherwise
    """
    try:
        auth_manager = GmailAuthManager(credentials_path, token_path)
        auth_manager.authenticate()
        print("✅ Gmail authentication successful!")
        return True
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False


if __name__ == "__main__":
    # Interactive setup when run directly
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'config/gmail_credentials.json')
    token_path = os.getenv('GMAIL_TOKEN_PATH', 'config/gmail_token.json')

    print("Gmail OAuth2 Setup")
    print("=" * 50)
    print(f"Credentials path: {credentials_path}")
    print(f"Token path: {token_path}")
    print()

    if setup_gmail_auth(credentials_path, token_path):
        print("\nYou can now use Gmail watcher in your AI Employee!")
        sys.exit(0)
    else:
        print("\nSetup failed. Please check the error messages above.")
        sys.exit(1)
