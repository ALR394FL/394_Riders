import os
import json
import io
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# SET TO TRUE TO TEST PATHS WITHOUT DOWNLOADING OR DELETING FILES
DRY_RUN = False 

# 1. Authenticate using GitHub Secrets
creds_json = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json)
service = build('drive', 'v3', credentials=creds)
root_folder_id = os.environ['FOLDER_ID']

# Global tracking sets
tracked_local_paths = set()
# Tracks file assignments made STRICTLY during this specific execution to catch true same-folder collisions
current_run_assignments = set()

def get_unique_filepath(calculated_path, file_id):
    """
    Requirement 2: True Collision Safeguard using Google Drive File ID.
    Only modifies the filename if another file from Google Drive has ALREADY claimed 
    this exact path during this current script execution.
    """
    if calculated_path not in current_run_assignments:
        current_run_assignments.add(calculated_path)
        return calculated_path
    
    # If the path was already claimed during THIS run, a true collision occurred.
    # We append the unique Google Drive File ID to guarantee a permanent, stable filename.
    base, extension = os.path.splitext(calculated_path)
    new_path = f"{base}_{file_id}{extension}"
    
    current_run_assignments.add(new_path)
    return new_path

def process_folder_contents(folder_id, parent_folder_name="uncategorized", is_root_level=False):
    """
    Deep searches the connected folder ID for real files and follows shortcuts.
    Treats shortcut folders as root environments containing 'images' and 'documents'.
    """
    page_token = None
    while True:
        query = f"'{folder_id}' in parents and trashed = false and name != 'Archive'"
        try:
            results = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, shortcutDetails)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000,
                pageToken=page_token
            ).execute()
            items = results.get('files', [])
        except Exception as e:
            print(f"Skipping folder access restriction on ID {folder_id}: {e}")
            return

        for item in items:
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']

            if file_name == 'Archive':
                continue

            # Resolve shortcuts safely
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_id = shortcut.get('targetId')
                target_mime = shortcut.get('targetMimeType')

                if target_mime == 'application/vnd.google-apps.folder':
                    # CRITICAL FIX: Treat the target folder as a new root level
                    process_folder_contents(target_id, parent_folder_name=parent_folder_name, is_root_level=True)
                    continue
                else:
                    file_id = target_id
                    mime_type = target_mime

            # Handle subfolders
            if mime_type == 'application/vnd.google-apps.folder':
                # If we are at root level and see folders named 'images' or 'documents', skip nesting them
                if is_root_level and file_name.lower() in ['images', 'documents']:
                    process_folder_contents(file_id, parent_folder_name="uncategorized", is_root_level=False)
                else:
                    process_folder_contents(file_id, parent_folder_name=file_name, is_root_level=False)
                continue

            if not file_name:
                continue

            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
            is_image = file_name.lower().endswith(image_extensions)

            # Determine path based on file type and category folder name
            top_level = "images" if is_image else "documents"
            subfolder = os.path.join(top_level, parent_folder_name)

            is_exportable = False
            export_mime = ""
            extension = ""

            if mime_type == 'application/vnd.google-apps.document':
                is_exportable = True
                export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                extension = '.docx'
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                is_exportable = True
                export_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                extension = '.xlsx'
            elif mime_type in ['application/vnd.google-apps.presentation', 'application/vnd.google-apps.form']:
                continue

            if is_exportable and not file_name.lower().endswith(extension):
                calculated_path = os.path.join(subfolder, f"{file_name}{extension}")
            else:
                calculated_path = os.path.join(subfolder, file_name)

            # Route through our smart execution collision check
            local_path = get_unique_filepath(calculated_path, file_id)
            tracked_local_paths.add(local_path)

            if DRY_RUN:
                print(f"[DRY-RUN] Target Path: {local_path} (From: {file_name})")
                continue # Skip directory creation and downloading

            dir_name = os.path.dirname(local_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            try:
                # If it already exists on disk from a previous run, skip downloading to save actions time
                if os.path.exists(local_path):
                    print(f"File safely preserved without suffix updates: {local_path}")
                    continue

                if is_exportable:
                    request = service.files().export_media(fileId=file_id, mimeType=export_mime)
                else:
                    request = service.files().get_media(fileId=file_id)

                with io.FileIO(local_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                print(f"Successfully synchronized file: {file_name} into {subfolder}")
            except Exception as file_error:
                print(f"Skipping protected file resource {file_name}: {file_error}")

        page_token = results.get('nextPageToken')
        if not page_token:
            break

def cleanup_deleted_files():
    """
    Requirement 1: Deletion Safeguard.
    """
    if DRY_RUN:
        print("[DRY-RUN] Skipping deletion cleanup phase.")
        return

    print("Checking for files deleted from Google Drive to sync removal...")
    # ... (rest of your cleanup code remains exactly the same)
    for target_dir in ["images", "documents"]:
        if not os.path.exists(target_dir):
            continue
            
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                if local_file_path not in tracked_local_paths:
                    try:
                        os.remove(local_file_path)
                        print(f"Removed deleted Drive file from Git environment: {local_file_path}")
                    except Exception as e:
                        print(f"Error removing file {local_file_path}: {e}")

if __name__ == "__main__":
    try:
        root_metadata = service.files().get(fileId=root_folder_id, fields="name", supportsAllDrives=True).execute()
        root_name = root_metadata.get("name", "uncategorized")
    except Exception:
        root_name = "uncategorized"

    process_folder_contents(root_folder_id, parent_folder_name=root_name, is_root_level=True)
    cleanup_deleted_files()

# === CALENDAR CACHING ===
print("Caching Calendar entries into repository tracking sheets...")
now_iso = datetime.datetime.utcnow().isoformat() + 'Z'
calendar_secret_id = os.environ.get('CALENDAR_ID')
calendar_creds_json = os.environ.get('CALENDAR_CREDENTIALS')

try:
    if calendar_secret_id and calendar_creds_json:
        cal_creds_info = json.loads(calendar_creds_json)
        cal_creds = Credentials.from_service_account_info(cal_creds_info)
        calendar_service = build('calendar', 'v3', credentials=cal_creds)
        
        calendar_results = calendar_service.events().list(
            calendarId=calendar_secret_id,
            timeMin=now_iso,
            maxResults=12,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        with open('events.json', 'w', encoding='utf-8') as json_file:
            json_file.write(json.dumps(calendar_results, indent=2))
        print("Successfully synchronized events.json mapping file via secondary credentials.")
except Exception as cal_err:
    print(f"Skipping calendar resource pull line: {cal_err}")
