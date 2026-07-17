import os
import json
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 1. Authenticate using GitHub Secrets
creds_json = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json)
service = build('drive', 'v3', credentials=creds)

folder_id = os.environ['FOLDER_ID']

# 2. Fetch everything inside the target folder
query = f"'{folder_id}' in parents and trashed = false"
results = service.files().list(q=query, fields="files(id, name, mimeType, shortcutDetails)").execute()
items = results.get('files', [])

for item in items:
    file_id = item['id']
    file_name = item['name']
    mime_type = item['mimeType']
    
    # Handle Shortcuts gracefully
    if mime_type == 'application/vnd.google-apps.shortcut':
        shortcut_details = item.get('shortcutDetails', {})
        file_id = shortcut_details.get('targetId')
        try:
            target_meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
            mime_type = target_meta.get('mimeType')
            if not file_name:
                file_name = target_meta.get('name')
        except Exception as e:
            print(f"Skipping broken shortcut reference: {file_name}. Error: {e}")
            continue

    # 📂 3. Group files logically into website folders based on filename keywords
    if 'waiver' in file_name.lower():
        subfolder = "documents/ride-waivers/"
    elif 'application' in file_name.lower():
        subfolder = "documents/membership-applications/"
    else:
        subfolder = "documents/event-requests/"

    # Define standard conversion parameters for cloud docs vs binary uploads
    is_exportable = False
    export_mime = ""
    extension = ""

    # Check for core native Google Workplace formats
    if mime_type == 'application/vnd.google-apps.document':  # Google Doc
        is_exportable = True
        export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        extension = '.docx'
    elif mime_type == 'application/vnd.google-apps.spreadsheet':  # Google Sheet
        is_exportable = True
        export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        extension = '.xlsx'
    elif mime_type == 'application/vnd.google-apps.presentation':  # Google Slides
        is_exportable = True
        export_mime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        extension = '.pptx'

    # Append clean desktop extensions to Google templates if they are missing
    if is_exportable and not file_name.lower().endswith(extension):
        local_path = os.path.join(subfolder, f"{file_name}{extension}")
    else:
        local_path = os.path.join(subfolder, file_name)

    # 4. Process secure local data transfer
    if not os.path.exists(local_path):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        try:
            if is_exportable:
                # 🎯 Fix: Safely utilize Export for live cloud editor content
                request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            else:
                # Safely utilize direct Get for standard binaries (PDFs, ZIPs, JPGs)
                request = service.files().get_media(fileId=file_id)
                
            fh = io.FileIO(local_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
            print(f"Successfully synchronized: {file_name}")
            
        except Exception as io_error:
            print(f"Failed to synchronize asset {file_name}: {io_error}")
