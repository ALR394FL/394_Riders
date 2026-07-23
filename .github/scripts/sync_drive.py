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

def determine_subfolder(file_name, is_image):
    """
    Sorts files first by type (images vs documents), then checks for specific keywords in the filename.
    """
    name_lower = file_name.lower()
    
    # 🖼️ LAYER 1: IF THE FILE IS AN IMAGE
    if is_image:
        image_keywords = {
            "ride": "chapter-rides",
            "escort": "veteran-escorts",
            "fundraiser": "fundraisers",
            "leader": "leadership",
            "officer": "leadership",
            "event": "fundraisers",
            "community": "community-service",
            "road": "the-open-road"
        }
        for keyword, folder in image_keywords.items():
            if keyword in name_lower:
                return os.path.join("images", folder)
        # RESTORED: Route unmatched images back to the uncategorized path
        return os.path.join("images", "uncategorized")

    # 📄 LAYER 2: IF THE FILE IS A DOCUMENT
    else:
        document_keywords = {
            "waiver": "ride-waivers",
            "application": "membership-applications",
            "request": "event-requests",
            "invoice": "financials",
            "receipt": "financials",
            "minutes": "meeting-minutes",
            "agenda": "meeting-agendas"
        }
        for keyword, folder in document_keywords.items():
            if keyword in name_lower:
                return os.path.join("documents", folder)
        # RESTORED: Route unmatched documents back to the uncategorized path
        return os.path.join("documents", "uncategorized")

def process_folder_contents(folder_id):
    """Deep searches the connected folder ID for real files and follows shortcuts cleanly with full pagination Support"""
    page_token = None
    while True:
        # UPDATED: Explicitly tell Google Drive API to ignore any item named Archive at the query level
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

            # 🎯 SAFEGUARD: If somehow a folder named Archive slips through, ignore it completely
            if file_name == 'Archive':
                print(f"Safety: Skipping Archive folder completely.")
                continue

            # 🎯 Resolve folder or file shortcuts safely
            if mime_type == 'application/vnd.google-apps.shortcut':
                shortcut = item.get('shortcutDetails', {})
                target_id = shortcut.get('targetId')
                target_mime = shortcut.get('targetMimeType')
                
                # SAFEGUARD: If the shortcut points to an Archive folder, do not follow it
                if file_name == 'Archive':
                    print(f"Safety: Skipping shortcut pointing to Archive.")
                    continue

                if target_mime == 'application/vnd.google-apps.folder':
                    print(f"Following shortcut folder link: {file_name}")
                    process_folder_contents(target_id)
                    continue
                else:
                    file_id = target_id
                    mime_type = target_mime

            # If it's a real subfolder directory node, step inside it recursively
            if mime_type == 'application/vnd.google-apps.folder':
                print(f"Stepping inside subfolder: {file_name}")
                process_folder_contents(file_id)
                continue

            if not file_name:
                continue

            # Check if the file is an image by its extension
            image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp')
            is_image = file_name.lower().endswith(image_extensions)

            # 📂 ROUTE FILE BY TYPE AND KEYWORDS
            subfolder = determine_subfolder(file_name, is_image)
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
                local_path = os.path.join(subfolder, f"{file_name}{extension}")
            else:
                local_path = os.path.join(subfolder, file_name)

            # 3. Securely synchronize files down to repository tracks
            dir_name = os.path.dirname(local_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            try:
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

if __name__ == "__main__":
    process_folder_contents(root_folder_id)

    # === APPEND THIS TO THE BOTTOM OF YOUR PYTHON SYNC FILE ===
    import datetime
    
    print("Caching Calendar entries into repository tracking sheets...")
    now_iso = datetime.datetime.utcnow().isoformat() + 'Z'
    
    calendar_secret_id = os.environ.get('CALENDAR_ID')
    calendar_creds_json = os.environ.get('CALENDAR_CREDENTIALS') # ◄── Pull new secret
    
    try:
        if calendar_secret_id and calendar_creds_json:
            # 1. Authenticate independently using the second service account credentials
            cal_creds_info = json.loads(calendar_creds_json)
            cal_creds = Credentials.from_service_account_info(cal_creds_info)
            calendar_service = build('calendar', 'v3', credentials=cal_creds) # ◄── Dedicated API hook
            
            # 2. Pull the next 3 events using the dedicated calendar service account connection
            calendar_results = calendar_service.events().list(
                calendarId=calendar_secret_id,
                timeMin=now_iso,
                maxResults=12,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            # 3. Save the data locally
            with open('calendar.json', 'w', encoding='utf-8') as json_file:
                json.dump(calendar_results, json_file, indent=2)
            print("Successfully synchronized calendar.json mapping file via secondary credentials.")
        else:
            print("Skipping calendar run: CALENDAR_ID or CALENDAR_CREDENTIALS environmental flags missing.")
        
    except Exception as cal_err:
        print(f"Skipping calendar resource pull line: {cal_err}")
