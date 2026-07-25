import os
import json
import requests
import re
import base64
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ==========================================================================
# 1. INITIALIZATION & CREDENTIALS CHECK
# ==========================================================================
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO = os.environ.get('GITHUB_REPOSITORY')

raw_folder_id = os.environ.get('FOLDER_ID', '')
root_folder_id = raw_folder_id.strip().strip("'").strip('"')

if not root_folder_id:
    print("FATAL ERROR: The FOLDER_ID environment secret is completely missing!")
    exit(1)

DRIVE_CREDENTIALS = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(DRIVE_CREDENTIALS)
service = build('drive', 'v3', credentials=creds)

# Global tracker to catch active paths and prevent unwanted purges
active_paths = set()

def clean_slug(folder_name):
    """Converts 'Chapter Rides' into url-safe 'chapter-rides' layout keys"""
    slug = folder_name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug

# ==========================================================================
# 2. RECURSIVE FOLDER SYNCHRONIZATION ENGINE (SHORTCUT AWARE)
# ==========================================================================
def sync_google_drive_folder(drive_folder_id, current_github_base=""):
    """
    Recursively crawls Google Drive structures. Resolves shortcuts pointing to
    external/auxiliary drives on-the-fly while maintaining local naming trees.
    """
    page_token = None
    while True:
        query = f"'{drive_folder_id}' in parents and trashed = false"
        try:
            results = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, shortcutDetails, md5Checksum)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1000,
                pageToken=page_token
            ).execute()
            items = results.get('files', [])
        except Exception as e:
            print(f"Skipping directory traversal bounds lock on ID {drive_folder_id}: {e}")
            return

        for item in items:
            file_id = item.get('id')
            file_name = item.get('name')
            mime_type = item.get('mimeType')
            md5_checksum = item.get('md5Checksum')
            
            if not file_name or file_name == 'Archive':
                continue

            # 🛠️ AUTOMATED SHORTCUT RESOLUTION CORRECTION
            is_folder = (mime_type == 'application/vnd.google-apps.folder')
            
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_mime = shortcut.get('targetMimeType')
                target_id = shortcut.get('targetId')
                
                if not target_id:
                    continue
                
                # If shortcut targets a folder, toggle mapping flag and jump IDs
                if target_mime == 'application/vnd.google-apps.folder':
                    file_id = target_id
                    is_folder = True
                else:
                    # Shortcut targets a standard file asset, update target context metadata
                    file_id = target_id
                    mime_type = target_mime

            # 📁 SUBFOLDER TRAVERSAL PATHWAY
            if is_folder:
                if current_github_base == "":
                    # At root base folder, enforce rigid images vs documents top branches mapping
                    if file_name.lower() in ['images', 'photos']:
                        sync_google_drive_folder(file_id, "images")
                    elif file_name.lower() in ['documents', 'forms', 'files']:
                        sync_google_drive_folder(file_id, "documents")
                else:
                    # Deep inside a category branch, clean subfolder name into a matching slug path
                    category_slug = clean_slug(file_name)
                    next_github_path = f"{current_github_base}/{category_slug}"
                    print(f"Traversing folder structure node: {next_github_path} (ID: {file_id})")
                    sync_google_drive_folder(file_id, next_github_path)
                continue

            # 📄 FILE PROCESSING: HYBRID ENGINE (HASH-SKIPPING + DUPLICATE PROTECTION)
            if not current_github_base or '/' not in current_github_base:
                print(f"Skipping loosely unassigned asset file at root boundary context: {file_name}")
                continue

            filename_base, file_extension = os.path.splitext(file_name)
            
            # Auto-assign extensions for Google workspace files
            if mime_type == 'application/vnd.google-apps.document':
                file_extension = '.docx'
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                file_extension = '.xlsx'
            elif mime_type in ['application/vnd.google-apps.presentation', 'application/vnd.google-apps.form']:
                continue 

            # Establish primary target path
            target_github_path = f"{current_github_base}/{filename_base}{file_extension}".replace("\\", "/")

            # 🚨 STRATEGY 2: DUPLICATE NAME COLLISION SAFETY NET
            # If a separate file with the exact same name was already processed in this group:
            if target_github_path in active_paths:
                # Grab a 6-character unique fingerprint slice from the Drive ID to split them
                short_id = file_id[-6:]
                target_github_path = f"{current_github_base}/{filename_base}_{short_id}{file_extension}".replace("\\", "/")
                print(f"⚠️ Duplicate filename resolved. Remapped path to: {target_github_path}")

            # Lock the path down in the active scan registry memory array
            active_paths.add(target_github_path)
            
            # 🚀 STRATEGY 3: HASH-CHECK (FAST ACCELERATOR BYPASS)
            # Check if this exact file exists on GitHub with the exact same content hash fingerprint
            url = f"https://github.com{REPO}/contents/{target_github_path}"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            get_response = requests.get(url, headers=headers)
            if get_response.status_code == 200:
                github_item_data = get_response.json()
                github_sha = github_item_data.get('sha')
                
                # Binary files use native MD5; fallback to file ID token string for cloud apps
                drive_fingerprint = md5_checksum if md5_checksum else file_id
                
                # Check if the existing online commit tracking note carries our matching hash tag
                # If content hash tags match completely, fast-skip downloading or processing
                if github_item_data.get('message', '').endswith(f"[{drive_fingerprint}]"):
                    print(f"⚡ Fast-Bypass: {target_github_path} is completely identical. Skipping sync.")
                    continue

            # EXECUTE ACTION: Only executes if the asset resource is new or updated
            process_and_upload_file(file_id, target_github_path, mime_type, md5_checksum)

        page_token = results.get('nextPageToken')
        if not page_token:
            break

# ==========================================================================
# 3. GITHUB COMMIT & UPDATE CONTEXT PIPELINE
# ==========================================================================
def process_and_upload_file(file_id, github_path, mime_type, md5_checksum=None):
    """Checks if file exists on GitHub, and uploads/overwrites if needed"""
    url = f"https://github.com{REPO}/contents/{github_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Download content streams raw bytes from Google Drive API
    try:
        if 'vnd.google-apps' in mime_type:
            export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if '.docx' in github_path else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            drive_download_url = f"https://googleapis.com{file_id}/export?mimeType={export_mime}"
        else:
            drive_download_url = f"https://googleapis.com{file_id}?alt=media"
            
        drive_response = requests.get(drive_download_url, headers={"Authorization": f"Bearer {creds.token}"})
        if drive_response.status_code != 200:
            return
        file_bytes = drive_response.content
    except Exception as e:
        print(f"Failed asset extraction downloading execution tracking for {github_path}: {e}")
        return

    # Check for existing item on GitHub to recover reference SHA token pointer hashes
    sha = None
    get_response = requests.get(url, headers=headers)
    if get_response.status_code == 200:
        sha = get_response.json().get('sha')
        
    encoded_content = base64.b64encode(file_bytes).decode('utf-8')
    
    # Securely lock the MD5 checksum context token directly onto the trailing tail message boundary
    drive_fingerprint = md5_checksum if md5_checksum else file_id
    payload = {
        "message": f"automated sync: uploading asset resource update ({github_path.split('/')[-1]}) [{drive_fingerprint}]",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    put_response = requests.put(url, headers=headers, json=payload)
    if put_response.status_code in [200, 201]:
        action_type = "Updated" if sha else "Created fresh"
        print(f"Successfully sync'd: [{action_type}] -> {github_path}")
    else:
        print(f"❌ GitHub upload failure for {github_path}: {put_response.status_code}")


# ==========================================================================
# 4. RECURSIVE PURGE SYSTEM MECHANICS
# ==========================================================================
def purge_orphaned_github_files(github_folder_path):
    """Crawls repo folders cleanly and removes items missing from the Drive scan"""
    url = f"https://github.com{REPO}/contents/{github_folder_path}"
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
        github_file_path = item['path']
        
        if item['type'] == 'dir':
            purge_orphaned_github_files(github_file_path)
            continue
            
        # If item sits on GitHub but wasn't indexed on Google Drive, clear it
        if github_file_path not in active_paths:
            # Skip clearing out system configuration dot-files or structural assets
            if item['name'].startswith('.') or item['name'] == 'default-doc-icon.png':
                continue
                
            print(f"Orphaned asset found. Purging item from repository tree: {github_file_path}")
            
            delete_url = f"https://github.com{REPO}/contents/{github_file_path}"
            delete_payload = {
                "message": f"chore: automated asset cleanup purging expired resource file ({item['name']})",
                "sha": item['sha']
            }
            
            requests.delete(delete_url, headers=headers, json=delete_payload)

# ==========================================================================
# 5. ENTRY COMMAND DRIVER RUN LINES
# ==========================================================================
if __name__ == "__main__":
    # Ensure fresh token runtime validation checks pull through securely
    if not creds.valid:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        
    print(f"Initializing dynamic hierarchy sync map using base ID token: '{root_folder_id}'")
    sync_google_drive_folder(root_folder_id)
    
    if len(active_paths) == 0:
        print("Safety Abort Check: 0 active paths returned from Drive. Core cancel invoked.")
        exit(1)
        
    print(f"Scan complete. Tracking {len(active_paths)} verified active assets. Starting cleanup passes...")
    purge_orphaned_github_files("images")
    purge_orphaned_github_files("documents")
    print("Automated folder synchronizations cycle completed successfully.")
