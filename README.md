# Google Drive & Calendar Sync Pipeline

An automated data pipeline that pulls photos, documents, and calendar schedules from Google Workspace, maps them into structured folders, dynamically rebuilds JSON indices via GitHub Actions, and displays assets natively in responsive layouts.

## 🚀 System Architecture

```text
[Single Google Account]
├── [Drive Folder] ───► (GitHub Actions Container) ───► [Local Repo Storage]
└── [Calendar Feed] ──► (Using Python Automation)    │
                        │                              └─────────────────────┐
                        ▼                                                    ▼
              [Generate JSON Data]                                  [Auto Commit & Push]
              `photos.json`, `documents.json` &                     Fresh Media Assets &
              `events.json`                                       Updated UI Components
                        │
                        ▼
             [Webpage UI Integration]
             ├── `events.html`  ◄── Powered by `events.js` (3-Column Grid + Details Modal Reads from `events.json`)
             └── `documents.html` ◄── Powered by `forms.js`
```

1. **Syncing Engine:** A Python routine authenticates with your Google Service Account to download modified or new files from your Drive folder and queries upcoming timeline events from your Calendar.
2. **Indexing Machine:** Native shell commands scan updated repositories, format human-readable layout names, and compile structured data sheets (`photos.json` and `documents.json`).
3. **Local Cache Streaming:** The Python script automatically saves the next **9 to 12 upcoming events** into a local data file (`calendar.json`), completely bypassing frontend browser CORS errors and removing any need to expose public API Keys in your client-side JavaScript.

---

## 🛠️ Step-by-Step Configuration Guide

Follow these instructions to link your Google account parameters and securely configure your protected GitHub Repository Secrets.

### Step 1: Generate Google Cloud Credentials
1. Go to the Google Cloud Console (https://console.cloud.google.com).
2. Create a new project and enable both the **Google Drive API** and the **Google Calendar API**.
3. Navigate to **APIs & Services > Credentials**.
4. Click **Create Credentials** and select **Service Account**.
5. Open your new Service Account details, navigate to the **Keys** tab, click **Add Key > Create New Key**, and choose **JSON**.
6. Save the downloaded JSON file securely. *Never commit this file directly to GitHub.*
7. Open the JSON text file and copy the `"client_email"` address listed inside it.

### Step 2: Configure Shared Assets Access
Because you are using a unified access token, you only need to grant access to this single Service Account email address across your assets:
1. **Google Drive:** Open your target media folder, click **Share**, paste your Service Account email, and give it **Viewer** rights. Copy the unique folder string out of the browser's URL path.
2. **Google Calendar:** Open your main dashboard calendar settings, toggle **Make available to public**, scroll to *Share with specific people*, add your Service Account email, and grant it **See all event details** permissions. Copy your primary calendar ID email address.

### Step 3: Configure Protected GitHub Repository Secrets
To allow your workflow container to execute without exposing private tokens, create these **four** entries inside your GitHub repository settings under **Settings > Secrets and variables > Actions**:

| Secret Name | Intended Vault Content |
| :--- | :--- |
| `DRIVE_CREDENTIALS` | Copy and paste the entire raw text content from your downloaded JSON credential key file for Drive scanning. |
| `CALENDAR_CREDENTIALS` | Copy and paste the same raw text content from your downloaded JSON credential key file for the calendar sync. |
| `FOLDER_ID` | Paste the unique Google Drive folder ID string you copied from the folder's URL path. |
| `CALENDAR_ID` | Paste your primary calendar email address or organizational calendar hash string. |

---

## 📂 File Routing & Index Matrix

The Python script scans item titles (case-insensitive) and evaluates their file extension types to distribute them into categorical production directories:

### 📸 Images File Pipeline
Applies to targets matching: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`.

| Filename Keyword Match | Target Directory Destination | JSON Album Map Identifier |
| :--- | :--- | :--- |
| `ride` | images/chapter-rides/ | Chapter Rides |
| `escort` | images/veteran-escorts/ | Veteran Escorts |
| `fundraiser \| event` | images/fundraisers/ | Fundraisers |
| `leader \| officer` | images/leadership/ | Leadership |
| `community` | images/community-service/ | Community Service |
| `road` | images/the-open-road/ | The Open Road |
| *No Rule Match* | images/uncategorized/ | Uncategorized Media |

### 📄 Documents File Pipeline
Applies to textual layouts and native office packages. Powered on the frontend by `forms.js` within `documents.html`.

| Filename Keyword Match | Target Directory Destination | JSON Archive Label Output |
| :--- | :--- | :--- |
| `waiver` | documents/ride-waivers/ | Ride Liability Waiver |
| `application` | documents/membership-applications/ | Membership Form |
| `request` | documents/event-requests/ | Community Support Request |
| `invoice \| receipt` | documents/financials/ | Finance |
| `minutes` | documents/meeting-minutes/ | Meeting Minutes |
| `agenda` | documents/meeting-agendas/ | Meeting Agendas |
| *No Rule Match* | documents/uncategorized/ | General / Uncategorized |

---

## 📅 Frontend Events UI Architecture

The events engine handles calendar data locally to deliver a rapid, interactive user experience:

* **File Tracking:** `events.html` fetches raw event payloads directly from `calendar.json` using the logic inside `events.js`. 
* **The 3-Column Layout Grid:** Upcoming entries are formatted dynamically into a clear, card-based column grid layout that automatically collapses safely to 2 columns on tablets and a single column list on mobile screens.
* **The Detail Pop-out Module:** Clicking an individual event card isolates data elements to render an animated lightbox modal window displaying complete locations, 24h formatted timetables, custom text descriptions, and a deep direct link out button to add the item directly to a user's Google Calendar.

---

## 🤖 Automated Actions Deployment

The background workflow file is located inside your repository under `.github/workflows/sync.yml`.

### Automated Trigger Timing
The pipeline triggers automatically at 23 minutes past every 6th hour (`23 */6 * * *`) daily. Manual runs can be initiated using the **Run workflow** button inside the GitHub Actions panel.

### Staging Layout Requirements
To prevent build runtime drops, ensure that your final unified Git step explicitly stages the generated structural configuration files:

```bash
git add documents/ images/ photos.json documents.json events.json
```
