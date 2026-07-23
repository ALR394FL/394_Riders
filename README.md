# Google Drive & Calendar Sync Pipeline

An automated data pipeline that pulls photos and documents from Google Drive, maps them into structured folders, dynamically rebuilds JSON indices via GitHub Actions, and displays upcoming schedules dynamically via a live Google Calendar frontend stream.

## 🚀 System Architecture

```text
[Google Drive Folder] ──► [GitHub Actions Container] ──► [Local Repository Storage]
                                                                 │
                                           ┌─────────────────────┴─────────────────────┐
                                           ▼                                           ▼
                                 [Generate JSON Data]                        [Auto Commit & Push]
                                           │                                           │
                                           ▼                                           ▼
                                   `photos.json` &                            Fresh Media Assets On
                                  `documents.json`                              GitHub Pages Site
```

1. **Syncing Engine:** A Python routine authenticates with Google Drive to download modified or new files.
2. **Indexing Machine:** Native shell commands scan updated repositories, format human-readable layout names, and compile structured array sheets (`photos.json` and `documents.json`).
3. **Live Calendar Streaming:** A client-side JavaScript routine connects directly to the Google Calendar API to render the next 3 upcoming events dynamically on the live site using existing CSS layouts.

---

## 📅 Integrated Google Calendar Frontend

The events section is completely dynamic and reads your public Google Calendar feed automatically. Because this process runs natively inside the visitor's web browser, it does not require background execution resources from your GitHub Actions workflow routines.

### ⚙️ JavaScript Credentials Properties
The frontend configuration variables must be stored inside **quotation marks** at the top of your webpage's script file:

```javascript
const API_KEY = 'YOUR_GOOGLE_API_KEY_HERE'; 
const CALENDAR_ID = 'your-chapter-email@gmail.com'; // Your exact primary calendar email address
```

### 🛡️ Security Best Practices
Because your frontend JavaScript is exposed to the public on GitHub Pages, you must secure your API key via your Google Cloud dashboard:
1. Navigate to the **Credentials** page in Google Cloud Console.
2. Edit your active API Key and select **Websites (HTTP referrers)** under application restrictions.
3. Whitelist your repository layout by adding your public web link: `https://github.io*`. This completely stops third-party sites from stealing your key.

---

## 🛠️ Step-by-Step Backend Setup Guide

Follow these instructions to connect your Google Drive and securely configure the GitHub repository actions.

### Step 1: Generate Google Cloud Credentials
1. Go to the Google Cloud Console (https://google.com).
2. Create a new project and enable the **Google Drive API** and **Google Calendar API**.
3. Navigate to APIs & Services > Credentials.
4. Click Create Credentials and select Service Account.
5. Open your new Service Account details, navigate to the Keys tab, click Add Key > Create New Key, and choose JSON.
6. Save the downloaded JSON file securely. *Never commit this file directly to GitHub.*

### Step 2: Configure Your Google Drive Folder
1. Open the Google Drive folder you wish to target.
2. Share **Viewer** access permissions with the unique email address of your generated Google Service Account.
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
