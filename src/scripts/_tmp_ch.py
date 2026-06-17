from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
token_path = Path('token.json')
creds = Credentials.from_authorized_user_file(str(token_path), None)
print('valid=', creds.valid, 'expired=', creds.expired, 'has_refresh=', creds.refresh_token is not None)
service = build('youtube', 'v3', credentials=creds)
ch = service.channels().list(part='id,snippet', mine=True).execute()
print(json.dumps(ch, indent=2))
