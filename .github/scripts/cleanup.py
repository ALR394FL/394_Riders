import os
import json
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 1. Configuration & Authentication
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO = os.environ.get('GITHUB_REPOSITORY')  # Format: "username/repo-name" provided automatically by GitHub Actions
DRIVE_CREDENTIALS = json.loads(os.environ['DRIVE_CREDENTIALS'])

creds = Credentials.from_service_account_info(DRIVE_CREDENTIALS)
service = build('drive', 'v3', credentials=creds)
root_folder_id = os.environ['FOLDER_ID']

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
    """
    Recursively builds a map of active file paths, resolving shortcuts 
    and scanning their targets just like your primary sync script.
    """
    page_token = None
    while True:
        # Step 1: Get contents of the current folder context
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

            # 🎯 SAFEGUARD: Completely skip the Archive folder node
            if file_name == 'Archive':
                print("Safety: Skipping Archive directory mapping.")
                continue

            if not file_name:
                continue

            # 🎯 RESOLVE SHORTCUTS: 
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_id = shortcut.get('targetId')
                target_mime = shortcut.get('targetMimeType')
    
                # NEW SAFEGUARD: If the shortcut target ID is missing, skip it completely
                if not target_id:
                    print(f"Warning: Shortcut '{file_name}' has an unresolvable or broken target ID. Skipping.")
                    continue

                if file_name == 'Archive':
                    continue

                if target_mime == 'application/vnd.google-apps.folder':
                    print(f"Following shortcut folder link: {file_name} (ID: {target_id})")
                    map_active_drive_files(target_id)
                    continue 
                else:
                    file_id = target_id
                    mime_type = target_mime

            # 🎯 RECURSE SUBFOLDERS: If it's a real subfolder directory node, step inside it recursively
            if mime_type == 'application/vnd.google-apps.folder':
                print(f"Stepping inside subfolder: {file_name}")
                map_active_drive_files(file_id)
						

							 
                continue

            # 🎯 ROUTE VALID FILES: This mirrors your exact file extension routing logic
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
            is_image = file_name.lower().endswith(image_extensions)
            subfolder = determine_subfolder(file_name, is_image)

            # Map cloud workplace native documents smoothly
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

            # Standardize path structure for the GitHub API comparison checks
            clean_path = local_path.replace("\\", "/")
            active_drive_paths.add(clean_path)
            print(f"Mapped active file path: {clean_path}")

        # Handle Pagination tracking
        page_token = results.get('nextPageToken')
        if not page_token:
            break

def purge_orphaned_github_files(github_folder_path):
    """Scans a repository subfolder on GitHub and deletes files missing from Drive map"""
    url = f"https://github.com{REPO}/contents/{github_folder_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return # Folder might not exist yet if no files are routed there

    items = response.json()
    if not isinstance(items, list):
        return

    for item in items:
        # If it's a subfolder directory, recursively look inside it
        if item['type'] == 'dir':
            purge_orphaned_github_files(item['path'])
            continue

        github_file_path = item['path'] # Matches format: "images/chapter-rides/flyer.png"

        # 🎯 THE PURGE COMPARE: If it is on GitHub but missing from active Drive tracking, destroy it
        if github_file_path not in active_drive_paths:
            print(f"File missing from active Drive (likely archived). Deleting from GitHub: {github_file_path}")
            
            delete_url = f"https://github.com{REPO}/contents/{github_file_path}"
            delete_payload = {
                "message": f"chore: manual cleanup removing expired asset ({item['name']})",
                "sha": item['sha'] # REQUIRED BY GITHUB
            }
            
            del_response = requests.delete(delete_url, headers=headers, json=delete_payload)
            if del_response.status_code == 200:
                print(f"Successfully deleted {item['name']} from GitHub.")
            else:
                print(f"Failed to delete {item['name']}: {del_response.text}")

if __name__ == "__main__":
    print("Building fresh layout map from active Google Drive directories...")
    map_active_drive_files(root_folder_id)
    
    # SAFEGUARD: Panic button. If drive returns completely empty, stop entirely.
    if len(active_drive_paths) == 0:
        print("Safety Abort: Google Drive scanner returned 0 files. Script stopped to prevent wiping repository.")
        exit(1)
        
    print(f"Tracking {len(active_drive_paths)} valid assets. Cross-referencing GitHub repository targets...")
    
    # Audit your target root pipeline directories
    purge_orphaned_github_files("images")
    purge_orphaned_github_files("documents")
    print("Manual cleanup cycle complete.")
