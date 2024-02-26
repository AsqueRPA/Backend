import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Scopes for Sheets and Drive APIs
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# File to store the credentials
CREDENTIALS_FILE = {
    "installed": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": ["http://localhost"],
    }
}
TOKEN_FILE = "token.json"


def main():
    creds = None
    # Load credentials from the file if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    # Use the credentials in your application
    # Create a new Google Sheet
    sheet_service = build("sheets", "v4", credentials=creds)
    sheet = (
        sheet_service.spreadsheets()
        .create(body={"properties": {"title": "hello world"}})
        .execute()
    )

    # Get the newly created Sheet ID
    sheet_id = sheet["spreadsheetId"]

    # Make the Google Sheet public (using Drive API)
    drive_service = build("drive", "v3", credentials=creds)
    drive_service.permissions().create(
        fileId=sheet_id, body={"type": "anyone", "role": "reader"}, fields="id"
    ).execute()

    print(f"Created sheet with ID: {sheet_id}")


if __name__ == "__main__":
    main()
