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

root_folder_id = os.environ['FOLDER_ID']

def process_folder_contents(folder_id):
    """Scans a folder ID and downloads all valid binary or cloud editor documents"""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType, shortcutDetails)").execute()
    items = results.get('files', [])

    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']
        
        # 🎯 Check if item is a Shortcut
        if mime_type == 'application/vnd.google-apps.shortcut':
            shortcut_details = item.get('shortcutDetails', {})
            target_id = shortcut_details.get('targetId')
            target_mime = shortcut_details.get('targetMimeType')
            
            # If shortcut points to a folder, dive inside it recursively
            if target_mime == 'application/vnd.google-apps.folder':
                print(f"Opening folder shortcut path: {file_name}")
                process_folder_contents(target_id)
                continue
            else:
                # If shortcut points to a file, swap targets
                file_id = target_id
                mime_type = target_mime

        # Skip folders completely (they are traversed recursively instead)
        if mime_type == 'application/vnd.google-apps.folder':
            process_folder_contents(file_id)
            continue

        # 📂 2. Assign sorting folders based on filename keywords
        if 'waiver' in file_name.lower():
            subfolder = "documents/ride-waivers/"
        elif 'application' in file_name.lower():
            subfolder = "documents/membership-applications/"
        else:
            subfolder = "documents/event-requests/"

        is_exportable = False
        export_mime = ""
        extension = ""

        # Map native Google cloud application formats
        if mime_type == 'application/vnd.google-apps.document':
            is_exportable = True
            export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            extension = '.docx'
        elif mime_type == 'application/vnd.google-apps.spreadsheet':
            is_exportable = True
            export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            extension = '.xlsx'
        elif mime_type == 'application/vnd.google-apps.presentation':
            is_exportable = True
            export_mime = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            extension = '.pptx'

        if is_exportable and not file_name.lower().endswith(extension):
            local_path = os.path.join(subfolder, f"{file_name}{extension}")
        else:
            local_path = os.path.join(subfolder, file_name)

        # 3. Securely download the actual file asset
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
                print(f"Successfully synchronized: {file_name}")
            except Exception as e:
                print(f"Error downloading {file_name}: {e}")

# Start scanning from your main connected Drive folder
process_folder_contents(root_folder_id)
