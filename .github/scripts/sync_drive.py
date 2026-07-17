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

def sync_all_assets_deep(target_id):
    """Bypasses strict parent-folder index blocks by executing a deep structural search query"""
    # 🎯 FORCE EXPLICIT OVERRIDE: Instructs Google's API to recursively expose files buried in subfolders
    search_query = f"'{target_id}' in parents and trashed = false"
    
    try:
        results = service.files().list(
            q=search_query,
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
    except Exception as e:
        print(f"API pipeline restriction hit on folder ID {target_id}: {e}")
        return

    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']

        # If a nested subfolder (like the 'Photos' directory) is encountered, dive inside automatically
        if mime_type == 'application/vnd.google-apps.folder':
            print(f"Deep scanner diving down into subfolder path: {file_name}")
            sync_all_assets_deep(file_id)
            continue

        # 📂 FILE TYPE CLASSIFICATION & ROUTING
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
        
        if file_name.lower().endswith(image_extensions):
            # Divert all images and graphic badges straight to the web layout images root
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

        # Handle native cloud document conversions smoothly
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

        # 3. Download the real file asset to the GitHub workspace
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
                print(f"Successfully synchronized: {file_name} into {subfolder}")
            except Exception as download_err:
                print(f"Could not synchronize asset {file_name}. Error: {download_err}")

# Execute the deep sync run
sync_all_assets_deep(root_folder_id)
