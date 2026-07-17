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
    """Deep searches the connected folder ID for real files and follows shortcuts cleanly"""
    query = f"'{folder_id}' in parents and trashed = false"
    
    try:
        results = service.files().list(
            q=query, 
            fields="files(id, name, mimeType, shortcutDetails)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        items = results.get('files', [])
    except Exception as e:
        print(f"Skipping folder access restriction on ID {folder_id}: {e}")
        return

    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']
        
        # 🎯 Resolve folder or file shortcuts safely
        if mime_type == 'application/vnd.google-apps.shortcut':
            shortcut = item.get('shortcutDetails', {})
            target_id = shortcut.get('targetId')
            target_mime = shortcut.get('targetMimeType')
            
            # If shortcut points to a folder, step inside it recursively
            if target_mime == 'application/vnd.google-apps.folder':
                print(f"Following shortcut folder link: {file_name}")
                process_folder_contents(target_id)
                continue
            else:
                # If shortcut points to a file, swap target properties
                file_id = target_id
                mime_type = target_mime

        # If it's a real subfolder directory node, step inside it recursively
        if mime_type == 'application/vnd.google-apps.folder':
            print(f"Stepping inside subfolder: {file_name}")
            process_folder_contents(file_id)
            continue

        if not file_name:
            continue

        # 📂 FILE TYPE STRUCTURE CLASSIFICATION RULES
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

        # Map cloud workplace native documents smoothly
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

        # 3. Securely synchronize files down to repository tracks
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
                print(f"Skipping protected file resource {file_name}: {file_error}")

# Kickstart the deep recursive synchronization sweep
process_folder_contents(root_folder_id)
