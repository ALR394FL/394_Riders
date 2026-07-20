import os
import json
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 1. Configuration & Authentication Validation
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO = os.environ.get('GITHUB_REPOSITORY')  

# Clean up raw environment variables to remove any trailing hidden spaces or quotes
raw_folder_id = os.environ.get('FOLDER_ID', '')
root_folder_id = raw_folder_id.strip().strip("'").strip('"')

if not root_folder_id:
    print("FATAL ERROR: The FOLDER_ID environment secret is completely blank or missing!")
    exit(1)

print(f"DEBUG: Successfully read FOLDER_ID from environment. Value length is {len(root_folder_id)} chars.")

DRIVE_CREDENTIALS = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(DRIVE_CREDENTIALS)
service = build('drive', 'v3', credentials=creds)

# Track all active paths that SHOULD exist on GitHub
active_drive_paths = set()

def determine_subfolder(file_name, is_image):
    """Mirroring your exact keyword sorting logic"""
    name_lower = file_name.lower()
    if is_image:
        image_keywords = {
            "ride": "chapter-rides", "escort": "veteran-escorts", 
            "fundraiser": "fundraisers", "leader": "leadership", 
            "officer": "leadership", "event": "fundraisers", 
            "community": "community-service", "road": "the-open-road"
        }
        for keyword, folder in image_keywords.items():
            if keyword in name_lower:
                return os.path.join("images", folder)
        return os.path.join("images", "uncategorized")
    else:
        document_keywords = {
            "waiver": "ride-waivers", "application": "membership-applications", 
            "request": "event-requests", "invoice": "financials", 
            "receipt": "financials", "minutes": "meeting-minutes", 
            "agenda": "meeting-agendas"
        }
        for keyword, folder in document_keywords.items():
            if keyword in name_lower:
                return os.path.join("documents", folder)
        return os.path.join("documents", "uncategorized")

def map_active_drive_files(folder_id):
    """Recursively builds a map of active file paths, ignoring 'Archive'"""
    # HARD SAFEGUARD: If something tries to pass an empty string, intercept it immediately
    if not folder_id or not str(folder_id).strip():
        print("Warning: Intercepted an attempted call with an empty Folder ID. Aborting this folder branch execution.")
        return

    page_token = None
    while True:
        query = f"'{folder_id}' in parents and trashed = false"
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
            file_id = item.get('id')
            file_name = item.get('name')
            mime_type = item.get('mimeType')

            if file_name == 'Archive':
                print("Safety: Skipping Archive directory mapping.")
                continue

            if not file_name:
                continue

            # 🎯 RESOLVE SHORTCUTS Safely
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_id = shortcut.get('targetId')
                target_mime = shortcut.get('targetMimeType')
                
                # Check for empty string target pointers
                if not target_id or not str(target_id).strip():
                    print(f"Warning: Shortcut '{file_name}' has an unresolvable target ID. Skipping.")
                    continue

                if target_mime == 'application/vnd.google-apps.folder':
                    print(f"Following shortcut folder link: {file_name} (Target ID: {target_id})")
                    map_active_drive_files(target_id)
                    continue 
                else:
                    file_id = target_id
                    mime_type = target_mime

            # Deep step into normal Subfolders
            if mime_type == 'application/vnd.google-apps.folder':
                if not file_id or not str(file_id).strip():
                    continue
                print(f"Stepping inside subfolder: {file_name} (ID: {file_id})")
                map_active_drive_files(file_id)
                continue

            # Route file paths exactly how they drop into GitHub
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
            is_image = file_name.lower().endswith(image_extensions)
            subfolder = determine_subfolder(file_name, is_image)

            # Match extensions for workspace files
            extension = ""
            if mime_type == 'application/vnd.google-apps.document':
                extension = '.docx'
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                extension = '.xlsx'
            elif mime_type in ['application/vnd.google-apps.presentation', 'application/vnd.google-apps.form']:
                continue

            if extension and not file_name.lower().endswith(extension):
                local_path = os.path.join(subfolder, f"{file_name}{extension}")
            else:
                local_path = os.path.join(subfolder, file_name)

            clean_path = local_path.replace("\\", "/")
            active_drive_paths.add(clean_path)
            print(f"Mapped active file path: {clean_path}")

        page_token = results.get('nextPageToken')
        if not page_token:
            break

def purge_orphaned_github_files(github_folder_path):
    """Scans a repository subfolder on GitHub and deletes files missing from Drive map"""
    url = f"https://github.com/{REPO}/{github_folder_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return 

    items = response.json()
    if not isinstance(items, list):
        return

    for item in items:
        if item['type'] == 'dir':
            purge_orphaned_github_files(item['path'])
            continue

        github_file_path = item['path']

        if github_file_path not in active_drive_paths:
            print(f"File missing from active Drive (archived). Deleting from GitHub: {github_file_path}")
            
            delete_url = f"https://api.github.com/{REPO}/contents/{github_file_path}"
            delete_payload = {
                "message": f"chore: manual cleanup removing expired asset ({item['name']})",
                "sha": item['sha']
            }
            
            del_response = requests.delete(delete_url, headers=headers, json=delete_payload)
            if del_response.status_code == 200:
                print(f"Successfully deleted {item['name']} from GitHub.")
            else:
                print(f"Failed to delete {item['name']}: {del_response.text}")

if __name__ == "__main__":
    print(f"Booting file mapping scanner using Root Folder ID: '{root_folder_id}'")
    map_active_drive_files(root_folder_id)
    
    if len(active_drive_paths) == 0:
        print("Safety Abort: Google Drive scanner returned 0 files. Script stopped to prevent wiping repository.")
        exit(1)
        
    print(f"Tracking {len(active_drive_paths)} valid assets. Cross-referencing GitHub repository targets...")
    purge_orphaned_github_files("images")
    purge_orphaned_github_files("documents")
    print("Manual cleanup cycle complete.")
