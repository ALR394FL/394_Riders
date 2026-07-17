import os
import json
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 1. Authenticate with the Google API using GitHub Secrets
creds_json = json.loads(os.environ['DRIVE_CREDENTIALS'])
creds = Credentials.from_service_account_info(creds_json)
service = build('drive', 'v3', credentials=creds)

folder_id = os.environ['FOLDER_ID']

# 2. Query all items in the folder, specifically telling Google to expose shortcut metadata details
query = f"'{folder_id}' in parents and trashed = false"
results = service.files().list(q=query, fields="files(id, name, mimeType, shortcutDetails)").execute()
items = results.get('files', [])

for item in items:
    file_id = item['id']
    file_name = item['name']
    mime_type = item['mimeType']
    
    # 🎯 FIX 1: If the item is a Shortcut, dynamically hop to its true target file ID
    if mime_type == 'application/vnd.google-apps.shortcut':
        shortcut_details = item.get('shortcutDetails', {})
        file_id = shortcut_details.get('targetId')
        
        # Pull the target's internal structural properties so we know how to download it
        target_meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        mime_type = target_meta.get('mimeType')
        if not file_name:
            file_name = target_meta.get('name')

    # 📂 3. Assign sorting directories based on file name keywords
    if 'waiver' in file_name.lower():
        subfolder = "documents/ride-waivers/"
    elif 'application' in file_name.lower():
        subfolder = "documents/membership-applications/"
    else:
        subfolder = "documents/event-requests/"

    # 🎯 FIX 2: Check if it's a live cloud Google Doc and handle file format conversion
    is_google_doc = (mime_type == 'application/vnd.google-apps.document')
    
    # Ensure the final output file has a clean desktop extension
    if is_google_doc and not file_name.endswith('.docx'):
        local_path = os.path.join(subfolder, f"{file_name}.docx")
    else:
        local_path = os.path.join(subfolder, file_name)

    # 4. Perform the file download if it hasn't been synced to GitHub yet
    if not os.path.exists(local_path):
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        if is_google_doc:
            # Tell Google's servers to convert the Google Doc into an editable Word document file
            request = service.files().export_media(fileId=file_id, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        else:
            # Grab standard files directly (PDFs, Images, Text Files)
            request = service.files().get_media(fileId=file_id)
            
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            
        print(f"Successfully synchronized: {file_name}")
