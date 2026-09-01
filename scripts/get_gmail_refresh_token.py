"""One-time script to obtain a Gmail API refresh token.

Usage:
  1. Copy .env.example to .env and set GMAIL_CLIENT_ID + GMAIL_CLIENT_SECRET
  2. Run: python scripts/get_gmail_refresh_token.py
  3. Complete the browser OAuth flow
  4. Copy the refresh token into GMAIL_REFRESH_TOKEN in .env
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"
ENV_EXAMPLE = BACKEND_DIR / ".env.example"

load_dotenv(ENV_FILE)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    client_id = os.getenv("GMAIL_CLIENT_ID", "")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET", "")

    if not client_id or not client_secret or client_id.startswith("your-"):
        print("Error: Gmail credentials not found.\n")
        if not ENV_FILE.exists():
            print(f"  • You edited .env.example, but the app reads {ENV_FILE.name}")
            print(f"  • Run:  copy .env.example .env   (PowerShell)")
            print(f"         Then put your real Client ID and Secret in .env\n")
            if ENV_EXAMPLE.exists():
                print(f"  • Or copy your values from .env.example into a new .env file.")
        else:
            print(f"  • Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in {ENV_FILE.name}")
        return

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\n--- Add these to backend/.env ---\n")
    print(f"GMAIL_REFRESH_TOKEN={credentials.refresh_token}")
    print("GMAIL_SENDER_EMAIL=your-gmail@gmail.com")
    print("\nUse the Gmail account you authorized as GMAIL_SENDER_EMAIL.")


if __name__ == "__main__":
    main()
