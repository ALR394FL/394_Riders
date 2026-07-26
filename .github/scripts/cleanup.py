import os
import json
import io
import requests
import re
import base64
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 1. Authenticate using GitHub Secrets (Your proven method)
creds_json = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json)
service = build('drive', 'v3', credentials=creds)
root_folder_id = os.environ['FOLDER_ID']

REPO = os.environ.get('GITHUB_REPOSITORY')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

active_paths = set()

def clean_slug(folder_name):
    """Converts folder names into url-safe slugs (e.g., 'Chapter Rides' -> 'chapter-rides')"""
    slug = folder_name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug
def sync_google_drive_folder(drive_folder_id, current_github_base=""):
    """Crawls directories recursively and sorts assets based strictly on folder paths"""
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
            print(f"Skipping directory tracking bounds: {e}")
            return

        for item in items:
            file_id = item.get('id')
            file_name = item.get('name')
            mime_type = item.get('mimeType')
            md5_checksum = item.get('md5Checksum')
            
            if not file_name or file_name == 'Archive':
                continue

            is_folder = (mime_type == 'application/vnd.google-apps.folder')
            
            # Shortcut Resolution Check
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_mime = shortcut.get('targetMimeType')
                target_id = shortcut.get('targetId')
                if target_id:
                    if target_mime == 'application/vnd.google-apps.folder':
                        file_id = target_id
                        is_folder = True
                    else:
                        file_id = target_id
                        mime_type = target_mime

            # TASK 1: Folder-Based Sorting Logic Routing
            if is_folder:
                if current_github_base == "":
                    if file_name.lower() in ['images', 'photos']:
                        sync_google_drive_folder(file_id, "images")
                    elif file_name.lower() in ['documents', 'forms', 'files']:
                        sync_google_drive_folder(file_id, "documents")
                else:
                    category_slug = clean_slug(file_name)
                    next_github_path = f"{current_github_base}/{category_slug}"
                    sync_google_drive_folder(file_id, next_github_path)
                continue

            if not current_github_base or '/' not in current_github_base:
                continue

                  # ==========================================================================
            # STRIPPED BASELINE LOOP: SCANS, ADDS, AND MARKS ACTIVE FOR DELETION PASSES
            # ==========================================================================
            filename_base, file_extension = os.path.splitext(file_name)
            
            # Map standard cloud office files to regular extensions
            if mime_type == 'application/vnd.google-apps.document':
                file_extension = '.docx'
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                file_extension = '.xlsx'
            elif 'vnd.google-apps' in mime_type:
                continue # Skip unexportable forms or presentations

            # Assemble direct path based strictly on the current folder slug
            target_github_path = f"{current_github_base}/{filename_base}{file_extension}".replace("\\", "/")

            # Track this path so the cleanup function at the end knows it is still active
            active_paths.add(target_github_path)
            
            # Send the file straight to the download and upload handler
            print(f"Syncing asset target: {target_github_path}")
            process_and_upload_file(file_id, target_github_path, mime_type)

        page_token = results.get('nextPageToken')
        if not page_token:
            break
def process_and_upload_file(file_id, github_path, mime_type, md5_checksum=None):
    """Downloads files using MediaIoBaseDownload and pushes commits cleanly to GitHub"""
    url = f"https://github.com/repos/{REPO}/contents/{github_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    try:
        if 'vnd.google-apps' in mime_type:
            export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if '.docx' in github_path else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            request = service.files().export(fileId=file_id, mimeType=export_mime)
        else:
            request = service.files().get_media(fileId=file_id)
            
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        file_bytes = fh.getvalue()
    except Exception as e:
        print(f"Download failure for {github_path}: {e}")
        return

    sha = None
    get_response = requests.get(url, headers=headers)
    if get_response.status_code == 200:
        sha = get_response.json().get('sha')
        
    encoded_content = base64.b64encode(file_bytes).decode('utf-8')
    drive_fingerprint = md5_checksum if md5_checksum else file_id
    
    payload = {
        "message": f"automated sync: updating asset ({github_path.split('/')[-1]}) [{drive_fingerprint}]",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    put_response = requests.put(url, headers=headers, json=payload)
    if put_response.status_code in [200, 201]:
        print(f"Successfully sync'd -> {github_path}")

def purge_orphaned_github_files(github_folder_path):
    """Scans repository tracks recursively and purges assets missing from Drive"""
    url = f"https://github.com/repos/{REPO}/contents/{github_folder_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
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
            
        if github_file_path not in active_paths:
            if item['name'].startswith('.') or item['name'] == 'default-doc-icon.png':
                continue
                
            print(f"Purging orphaned asset: {github_file_path}")
            delete_url = f"https://github.com/repos/{REPO}/contents/{github_file_path}"
            delete_payload = {
                "message": f"chore: cleaning up expired resource file ({item['name']})",
                "sha": item['sha']
            }
            requests.delete(delete_url, headers=headers, json=delete_payload)

def compile_frontend_json_databases():
    """
    Scans the processed active path list, builds frontend JSON structures,
    and automatically uploads them to your GitHub repository.
    """
    document_order = set()
    archives = {}
    category_order = set()
    albums = {}

    # 1. PARSE PATHS IN MEMORY CORES
    for path in sorted(active_paths):
        parts = path.split('/')
        if len(parts) < 3:
            continue
            
        top_folder = parts[0]
        category_slug = parts[1]
        full_filename = parts[2]
        
        filename_base, file_extension = os.path.splitext(full_filename)
        clean_extension = file_extension.lower().replace('.', '')
        
        human_title = filename_base.replace('_', ' ').replace('-', ' ').title()
        group_label = category_slug.replace('-', ' ').title()

        if top_folder == "documents":
            document_order.add(category_slug)
            if category_slug not in archives:
                archives[category_slug] = []
            archives[category_slug].append({
                "path": path,
                "title": human_title,
                "type": clean_extension.upper(),
                "label": group_label
            })

        elif top_folder == "images":
            category_order.add(category_slug)
            if category_slug not in albums:
                albums[category_slug] = []
            albums[category_slug].append({
                "path": path,
                "caption": human_title,
                "title": group_label
            })

    # 2. SAVE & COMMIT DOCUMENTS DATABASE
    doc_payload = {
        "documentOrder": sorted(list(document_order)),
        "archives": archives
    }
    doc_text = json.dumps(doc_payload, indent=2)
    upload_json_to_github("documents.json", doc_text)

    # 3. SAVE & COMMIT PHOTOS DATABASE
    photo_payload = {
        "categoryOrder": sorted(list(category_order)),
        "albums": albums
    }
    photo_text = json.dumps(photo_payload, indent=2)
    upload_json_to_github("photos.json", photo_text)


def upload_json_to_github(filename, json_string_data):
    """Checks for existing files and pushes structural database commits straight to GitHub"""
    url = f"https://github.com/repos/{REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    sha = None
    get_response = requests.get(url, headers=headers)
    if get_response.status_code == 200:
        sha = get_response.json().get('sha')
        
    encoded_content = base64.b64encode(json_string_data.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"automated tracking database index update: sync {filename}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    requests.put(url, headers=headers, json=payload)
    print(f"📢 Live website database compiled and uploaded successfully: {filename}")


# ==========================================================================
# 5. ENTRY COMMAND DRIVER RUN LINES
# ==========================================================================
if __name__ == "__main__":
    print(f"Syncing folder tree from root ID: '{root_folder_id}'")
    sync_google_drive_folder(root_folder_id)
    
    if len(active_paths) == 0:
        print("Safety Abort Check: 0 active paths returned. Workflow cancelled.")
        exit(1)
        
    # Compile and upload your web layout mapping arrays
    compile_frontend_json_databases()
        
    print(f"Tracking {len(active_paths)} assets. Beginning purge passes...")
    purge_orphaned_github_files("images")
    purge_orphaned_github_files("documents")
    print("Folder synchronization cycle completed successfully.")
