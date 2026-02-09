#!/usr/bin/env python3
"""
Google Drive Setup Wizard for Wafermap Analysis Tool
Run this script to set up Google Drive integration.
"""

import os
import sys
import webbrowser
import json

print("=" * 60)
print("  Google Drive Setup Wizard")
print("  For Wafermap Analysis Tool")
print("=" * 60)
print()

# Check if required packages are installed
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    print("✅ Google API libraries installed")
except ImportError as e:
    print("❌ Google API libraries not installed")
    print("   Installing now...")
    os.system(f"{sys.executable} -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    print("   Please run this script again after installation.")
    sys.exit(1)

SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/presentations',
]

script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_file = os.path.join(script_dir, 'credentials.json')
token_file = os.path.join(script_dir, 'google_token.pickle')

def create_credentials_file():
    """Guide user to create credentials.json"""
    print("\n📋 Step 1: Create Google Cloud Project Credentials")
    print("-" * 50)
    print("""
To use Google Drive with this app, you need OAuth credentials.

Follow these steps:

1. Go to Google Cloud Console:
   https://console.cloud.google.com/

2. Sign in with your Meta Google account (szenklarz@meta.com)

3. Create a new project (or select existing):
   - Click "Select a project" → "New Project"
   - Name it "Wafermap Analysis" → Create

4. Enable APIs:
   - Go to "APIs & Services" → "Library"
   - Search and enable "Google Drive API"
   - Search and enable "Google Slides API"

5. Create OAuth Credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "+ CREATE CREDENTIALS" → "OAuth client ID"
   - If prompted, configure OAuth consent screen:
     * User Type: Internal (for Meta) or External
     * App name: "Wafermap Analysis"
     * User support email: your email
     * Save and continue (skip scopes)
   - Application type: "Desktop app"
   - Name: "Wafermap Desktop"
   - Click "Create"

6. Download the credentials:
   - Click the download button (⬇) next to your OAuth client
   - Save the file as 'credentials.json' in:
     {0}

Press Enter when you've completed these steps...
""".format(script_dir))

    input()

    # Open Google Cloud Console
    print("Opening Google Cloud Console...")
    webbrowser.open("https://console.cloud.google.com/apis/credentials")

def authenticate():
    """Run OAuth authentication flow"""
    print("\n🔐 Step 2: Authenticate with Google")
    print("-" * 50)

    if not os.path.exists(credentials_file):
        print(f"❌ credentials.json not found at: {credentials_file}")
        print("   Please complete Step 1 first.")
        return False

    print("Starting authentication flow...")
    print("A browser window will open. Sign in with your Meta Google account.")
    print()

    try:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the credentials
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)

        print("✅ Authentication successful!")
        print(f"   Token saved to: {token_file}")
        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def test_connection():
    """Test Google Drive connection"""
    print("\n🧪 Step 3: Test Connection")
    print("-" * 50)

    if not os.path.exists(token_file):
        print("❌ No authentication token found. Please authenticate first.")
        return False

    try:
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        # Test Drive API
        service = build('drive', 'v3', credentials=creds)
        results = service.files().list(pageSize=1, fields="files(name)").execute()

        print("✅ Google Drive connection successful!")

        # Test Slides API
        slides_service = build('slides', 'v1', credentials=creds)
        print("✅ Google Slides connection successful!")

        # Get user info
        about = service.about().get(fields="user").execute()
        user = about.get('user', {})
        print(f"\n👤 Connected as: {user.get('displayName', 'Unknown')}")
        print(f"   Email: {user.get('emailAddress', 'Unknown')}")

        return True

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    print("\nChecking current setup...\n")

    # Check for existing token
    if os.path.exists(token_file):
        print("🔑 Found existing authentication token")
        if test_connection():
            print("\n" + "=" * 60)
            print("✅ Setup complete! You can now use Google Drive in the app.")
            print("=" * 60)
            return
        else:
            print("\nToken may be expired. Re-authenticating...")
            os.remove(token_file)

    # Check for credentials file
    if not os.path.exists(credentials_file):
        print("📄 credentials.json not found")
        print("\nWould you like to set up Google Drive integration? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("Setup cancelled.")
            return
        create_credentials_file()

    # Wait for credentials file
    print("\nLooking for credentials.json...")
    if not os.path.exists(credentials_file):
        print("Waiting for you to save credentials.json...")
        print("Press Enter when the file is saved...")
        input()

    if os.path.exists(credentials_file):
        print("✅ Found credentials.json")

        # Authenticate
        if authenticate():
            # Test connection
            test_connection()

            print("\n" + "=" * 60)
            print("✅ Setup complete! You can now use Google Drive in the app.")
            print("   - Go to 'Create Presentation' tab")
            print("   - Select 'Google Slides (Convert)' option")
            print("   - Click 'Create Presentation'")
            print("=" * 60)
    else:
        print("❌ credentials.json still not found. Please try again.")

if __name__ == "__main__":
    main()
    print("\nPress Enter to exit...")
    input()
