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

def get_all_files_deep(folder_id):
    """Recursively crawls directories, resolving shortcuts and collecting ONLY physical file items"""
    all_files = []
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
        return []

    for item in items:
        mime_type = item['mimeType']
        
        # Resolve folder or file shortcuts safely
        if mime_type == 'application/vnd.google-apps.shortcut':
            shortcut = item.get('shortcutDetails', {})
            item['id'] = shortcut.get('targetId')
            item['mimeType'] = shortcut.get('targetMimeType')
            mime_type = item['mimeType']

        # 🎯 CRITICAL FIX: If it's a real folder, crawl INSIDE it, never add it to the download queue
        if mime_type == 'application/vnd.google-apps.folder':
            all_files.extend(get_all_files_deep(item['id']))
        else:
            all_files.append(item)
            
    return all_files

# Run the deep discovery sweep across your layout
synchronized_assets = get_all_files_deep(root_folder_id)

for asset in synchronized_assets:
    file_id = asset['id']
    file_name = asset['name']
    mime_type = asset['mimeType']

    # Double check to prevent raw empty strings or corrupted types from breaking directory builds
    if not file_name:
        continue

    # 📂 FILE TYPE STRUCTURE ARCHITECTURE
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

    # Map native document types smoothly
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

    # 3. Synchronize data payloads to repo branches
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
            print(f"Skipping file {file_name}: {file_error}")
