# Google Drive to GitHub Sync & Catalog Pipeline

An automated data pipeline that pulls photos and documents from Google Drive, maps them into structured folders, dynamically rebuilds JSON indices, and commits the updates directly back to GitHub Pages.

## 🚀 System Architecture

[Google Drive Folder] ──(GitHub Actions)──► [Local Repo Storage]
                                                   │
                                     ┌─────────────┴─────────────┐
                                     ▼                           ▼
                            [Generate JSON Data]       [Auto Commit & Push]
                                     │                           │
                                     ▼                           ▼
                             `photos.json`               Live Site Updates
                             `documents.json`

1. Syncing Engine: A Python routine authenticates with Google Drive and downloads modified or new files.
2. Indexing Machine: Native shell commands scan the newly updated file repositories, format human-readable layout names, and compile structured array sheets (`photos.json` and `documents.json`).
3. Static Delivery: GitHub Pages references these fresh JSON catalogs directly to build visual web albums and catalog lists on the frontend.

---

## 🛠️ Step-by-Step Setup Guide

Follow these instructions to connect your Google Drive and securely configure the GitHub repository actions.

### Step 1: Generate Google Cloud Credentials
1. Go to the Google Cloud Console (https://google.com).
2. Create a new project and enable the Google Drive API.
3. Navigate to APIs & Services > Credentials.
4. Click Create Credentials and select Service Account.
5. Open your new Service Account details, navigate to the Keys tab, click Add Key > Create New Key, and choose JSON.
6. Save the downloaded JSON file securely. *Never commit this file directly to GitHub.*

### Step 2: Configure Your Google Drive Folder
1. Open the Google Drive folder you wish to target.
2. Share Viewer access permissions with the unique email address of your generated Google Service Account.
3. Copy the unique Folder ID from your browser's URL window line (the string of characters located at the very end of the URL).
4. *Built-in Exclusion Safeguard:* Any directory or shortcut link explicitly named `Archive` will be passed over entirely by the sync application.

### Step 3: Configure Protected GitHub Repository Secrets
To allow the workflow container to authenticate without hardcoding private tokens, save your credentials securely within GitHub:

1. In your GitHub repository, go to Settings.
2. In the left panel, expand Secrets and variables and click Actions.
3. Select New repository secret to add these two requirements:

| Secret Name | Intended Vault Content |
| :--- | :--- |
| DRIVE_CREDENTIALS | Copy and paste the entire raw text string from your downloaded JSON credential file. |
| FOLDER_ID | Paste the unique Google Drive folder ID string you copied from the browser link. |

---

## 📂 File Routing & Index Matrix

The Python script scans item titles (case-insensitive) and evaluates their file extension types to distribute them into categorical production directories:

### 📸 Images File Pipeline
Applies to targets matching: .png, .jpg, .jpeg, .gif, .svg, .webp.

| Filename Keyword Match | Target Directory Destination | JSON Album Map Identifier |
| :--- | :--- | :--- |
| ride | images/chapter-rides/ | Chapter Rides |
| escort | images/veteran-escorts/ | Veteran Escorts |
| fundraiser \| event | images/fundraisers/ | Fundraisers |
| leader \| officer | images/leadership/ | Leadership |
| community | images/community-service/ | Community Service |
| road | images/the-open-road/ | The Open Road |
| *No Rule Match* | images/uncategorized/ | Uncategorized Media |

### 📄 Documents File Pipeline
Applies to textual layouts and native office packages.

| Filename Keyword Match | Target Directory Destination | JSON Archive Label Output |
| :--- | :--- | :--- |
| waiver | documents/ride-waivers/ | Ride Liability Waiver |
| application | documents/membership-applications/ | Membership Form |
| request | documents/event-requests/ | Community Support Request |
| invoice \| receipt | documents/financials/ | Finance |
| minutes | documents/meeting-minutes/ | Meeting Minutes |
| agenda | documents/meeting-agendas/ | Meeting Agendas |
| *No Rule Match* | documents/uncategorized/ | General / Uncategorized |

### ⚙️ Workspace Conversions
The synchronization process safely parses enterprise workspace native nodes and auto-converts files to static offline documents:
* Google Docs translate directly into standalone .docx packages.
* Google Sheets translate directly into standalone .xlsx spreadsheets.

---

## 🤖 Automated Actions Deployment

The background workflow file is located inside your repository under .github/workflows/sync.yml. 

### Automated Trigger Timing
The pipeline triggers automatically at 23 minutes past every 6th hour (`23 */6 * * *`) daily. Manual runs can be initiated using the Run workflow button inside the GitHub Actions panel.

### Generated JSON Layout Examples
The script automatically builds runtime structural objects so your JavaScript frontend can query active records dynamically.

#### Example photos.json Schema
{
  "categoryOrder": ["chapter-rides"],
  "albums": {
    "chapter-rides": [
      {
        "path": "images/chapter-rides/annual-ride.jpg",
        "title": "Chapter Rides",
        "caption": "Annual Ride"
      }
    ]
  }
}

#### Example documents.json Schema
{
  "documentOrder": ["ride-waivers"],
  "archives": {
    "ride-waivers": [
      {
        "path": "documents/ride-waivers/2026-signup-form.pdf",
        "title": "2026 Signup Form",
        "type": "PDF",
        "label": "Ride Liability Waiver"
      }
    ]
  }
}
