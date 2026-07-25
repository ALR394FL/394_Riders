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

## 📁 Content Management Instructions

This repository automatically syncs files from our shared Google Drive folder using a recursive directory tree. You no longer need to rename files or use keyword prefixes to categorize them. The directory folder structure itself handles 100% of the sorting on the website.

### 1. Main Directory Layout Map
To ensure your files appear on the correct pages, they must be uploaded into one of the two primary parent folders on Google Drive:

📂 Shared Google Drive Root
├── 📁 Documents  <-- Files uploaded here populate the "Forms & Resources" page
└── 📁 Images     <-- Files uploaded here populate the "Photo Galleries" page

---

### 2. Photo Gallery Album Uploads (`/Images`)
To create a new photo album or add images to an existing gallery grid, place your images inside a subfolder under the main `Images` directory. 
* **Folder Name = Website Album Title**: The exact name you give the folder on Google Drive will be cleaned into a web-safe URL slug and displayed as the headline title for that album on the live site.

**Example Folder Paths:**
* `Images/Chapter Rides/` -> Creates a "Chapter Rides" gallery category card.
* `Images/Veteran Escorts/` -> Creates a "Veteran Escorts" gallery category card.

*Note: Any image files dropped loosely into the root or directly inside the top-level `Images/` folder without being tucked inside a subfolder category will be automatically skipped and ignored.*

---

### 3. Resource Documents Uploads (`/Documents`)
To group PDFs, Word documents, or spreadsheets into structured download categories on our Forms page, organize them into named subfolders inside the main `Documents` directory.

**Example Folder Paths:**
* `Documents/Meeting Minutes/` -> Groups downloads under a "Meeting Minutes" webpage header.
* `Documents/Ride Waivers/` -> Groups downloads under a "Ride Waivers" webpage header.
* `Documents/Financial Records/` -> Groups downloads under a "Financial Records" webpage header.

---

### 4. Automatic Conflict Resolution & Built-In Safeguards
* **Duplicate Protection Layer:** If separate folders contain files sharing the exact same name (e.g., `flyer.pdf`), our synchronization script detects the collision and appends a short unique identifier code to the end of the filename on GitHub. This prevents file overwrite conflicts.
* **Content Hash Skipping:** The synchronization system checks the cryptographic MD5 hash of your files. If an asset has not changed, the script fast-bypasses downloading or uploading it, reducing site build times to under 10 seconds.
* **Instructional Safeguard:** Loose documentation files named `README.md` or `instructions.txt` placed within repository directories to guide editors are whitelisted and will never be removed by the automated cleanup purge engine.

---

## 📅 Frontend Events UI Architecture

The events engine handles calendar data locally to deliver a rapid, interactive user experience:

* **File Tracking:** `events.html` fetches raw event payloads directly from `events.json` using the logic inside `events.js`. 
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
