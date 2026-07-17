import os
import json
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Authenticate with Google API using GitHub Secrets
creds_json = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json)
service = build('drive', 'v3', credentials=creds)

folder_id = os.environ['FOLDER_ID']

# Look for files inside the shared Google Drive folder
query = f"'{folder_id}' in parents and trashed = false"
results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
items = results.get('files', [])

# Map subfolders based on document naming or drive organization
for item in items:
    file_id = item['id']
    file_name = item['name']
    mime_type = item['mimeType']
    
    # Skip Google Docs formats, only download real files (PDFs, Images, etc.)
    if 'vnd.google-apps' in mime_type:
        continue
        
    # Auto-sort sorting logic based on text keyword tags
    if 'waiver' in file_name.lower():
        local_path = f"documents/ride-waivers/{file_name}"
    elif 'application' in file_name.lower():
        local_path = f"documents/membership-applications/{file_name}"
    else:
        local_path = f"documents/event-requests/{file_name}"

    # Only download if the file doesn't already exist in GitHub
    if not os.path.exists(local_path):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        print(f"Successfully synchronized: {file_name}")
