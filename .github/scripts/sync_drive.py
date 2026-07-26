import os
import json
import io
import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 1. Authenticate using GitHub Secrets
creds_json = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json)
service = build('drive', 'v3', credentials=creds)
root_folder_id = os.environ['FOLDER_ID']

# Global set to track all local paths that exist on Google Drive during this run
tracked_local_paths = set()

def get_unique_filepath(target_path):
    """
    Requirement 2: Collision Safeguard.
    If a file name collision occurs, appends an incrementing counter 
    (e.g., file_1.jpg, file_2.jpg) to prevent overwriting existing files.
    """
    if not os.path.exists(target_path):
        return target_path
    
    base, extension = os.path.splitext(target_path)
    counter = 1
    while True:
        new_path = f"{base}_{counter}{extension}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1

def process_folder_contents(folder_id, parent_folder_name="uncategorized"):
    """
    Deep searches the connected folder ID for real files and follows shortcuts.
    Pivoted: Uses parent_folder_name to determine the local download directory.
    """
    page_token = None
    while True:
        # Explicitly tell Google Drive API to ignore any item named Archive at the query level
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

            # Safeguard: Skip Archive folders
            if file_name == 'Archive':
                print("Safety: Skipping Archive folder completely.")
                continue

            # Resolve folder or file shortcuts safely
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_id = shortcut.get('targetId')
                target_mime = shortcut.get('targetMimeType')

                if file_name == 'Archive':
                    print("Safety: Skipping shortcut pointing to Archive.")
                    continue

                if target_mime == 'application/vnd.google-apps.folder':
                    print(f"Following shortcut folder link: {file_name}")
                    # The folder name remains the shortcut's name or the destination name. 
                    # We pass file_name here to use this directory name for sorting.
                    process_folder_contents(target_id, parent_folder_name=file_name)
                    continue
                else:
                    file_id = target_id
                    mime_type = target_mime

            # If it's a real subfolder directory node, step inside it recursively
            if mime_type == 'application/vnd.google-apps.folder':
                print(f"Stepping inside subfolder: {file_name}")
                process_folder_contents(file_id, parent_folder_name=file_name)
                continue

            if not file_name:
                continue

            # Check if the file is an image by its extension
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
            is_image = file_name.lower().endswith(image_extensions)

            # Pivot: Route file based on whether it is an image/document, sorted by the parent folder name
            top_level = "images" if is_image else "documents"
            subfolder = os.path.join(top_level, parent_folder_name)

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
            elif mime_type in ['application/vnd.google-apps.presentation', 'application/vnd.google-apps.form']:
                print(f"Skipping native unsupported export file format: {file_name}")
                continue

            if is_exportable and not file_name.lower().endswith(extension):
                calculated_path = os.path.join(subfolder, f"{file_name}{extension}")
            else:
                calculated_path = os.path.join(subfolder, file_name)

            # Apply collision protection mechanism
            local_path = get_unique_filepath(calculated_path)
            
            # Track this local path as active on Google Drive
            tracked_local_paths.add(local_path)

            # Securely synchronize files down to repository tracks
            dir_name = os.path.dirname(local_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            try:
                # If the file already exists (and has tracking identity match), skip re-downloading to save bandwidth
                if os.path.exists(local_path):
                    print(f"File already exists and is safe: {local_path}")
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

        # Break the loop if no more token blocks exist
        page_token = results.get('nextPageToken')
        if not page_token:
            break

def cleanup_deleted_files():
    """
    Requirement 1: Deletion Safeguard.
    Walks through local 'images' and 'documents' folders and deletes 
    local files that no longer exist in the tracked Google Drive set.
    """
    print("Checking for files deleted from Google Drive to sync removal...")
    for target_dir in ["images", "documents"]:
        if not os.path.exists(target_dir):
            continue
            
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                # If the local file wasn't registered during our Google Drive crawl, delete it
                if local_file_path not in tracked_local_paths:
                    try:
                        os.remove(local_file_path)
                        print(f"Removed deleted Drive file from Git environment: {local_file_path}")
                    except Exception as e:
                        print(f"Error removing file {local_file_path}: {e}")

if __name__ == "__main__":
    # Fetch root folder details to use its native name if needed, default to 'uncategorized'
    try:
        root_metadata = service.files().get(fileId=root_folder_id, fields="name", supportsAllDrives=True).execute()
        root_name = root_metadata.get("name", "uncategorized")
    except Exception:
        root_name = "uncategorized"

    # Start crawling and downloading
    process_folder_contents(root_folder_id, parent_folder_name=root_name)
    
    # Run the cleanup logic to drop files missing from Drive
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
            json.dump(calendar_results, json_file, indent=2)
        print("Successfully synchronized events.json mapping file via secondary credentials.")
    else:
        print("Skipping calendar run: CALENDAR_ID or CALENDAR_CREDENTIALS environmental flags missing.")
except Exception as cal_err:
    print(f"Skipping calendar resource pull line: {cal_err}")
