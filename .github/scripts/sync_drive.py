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

def sync_all_accessible_files():
    """Bypasses nested shortcut folder visibility walls by searching for all accessible files globally"""
    # 🎯 FORCE GLOBAL SWEEP: Finds all valid files shared with this account, skipping structural folder nodes completely
    query = "mimeType != 'application/vnd.google-apps.folder' and mimeType != 'application/vnd.google-apps.shortcut' and trashed = false"
    
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
    except Exception as e:
        print(f"Global API access error: {e}")
        return

    print(f"Discovered {len(items)} total synchronization candidates across shared nodes.")

    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']

        if not file_name:
            continue

        # 📂 FILE ARCHITECTURE ROUTING
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
        
        if file_name.lower().endswith(image_extensions):
            subfolder = "images/"
        elif 'waiver' in file_name.lower():
            subfolder = "documents/ride-waivers/"
        elif 'application' in file_name.lower():
            subfolder = "documents/membership-applications/"
        else:
            subfolder = "documents/event-requests/"

        is_exportable = False
        export_mime = ""
        extension = ""

        # Map native cloud formats smoothly
        if mime_type == 'application/vnd.google-apps.document':
            is_exportable = True
            export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            extension = '.docx'
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            is_exportable = True
            export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = '.xlsx'

        if is_exportable and not file_name.lower().endswith(extension):
            local_path = os.path.join(subfolder, f"{file_name}{extension}")
        else:
            local_path = os.path.join(subfolder, file_name)

        # 3. Synchronize data payload streams into repository files
        if not os.path.exists(local_path):
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            try:
                if is_exportable:
                    request = service.files().export_media(fileId=file_id, mimeType=export_mime)
                else:
                    request = service.files().get_media(fileId=file_id)
                    
                fh = io.FileIO(local_path, 'wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                print(f"Successfully synchronized file: {file_name} into {subfolder}")
            except Exception as file_error:
                print(f"Skipping unauthorized file {file_name}: {file_error}")

# Execute the search
sync_all_accessible_files()
