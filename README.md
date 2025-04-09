# yt-autobot
This python tool automates the upload of mutiple video files from a local folder to a YouTube channel. 
## Features
- **Batch Video Uploads:**  
 Upload every video file (e.g., `.mp4`, `.mov`, `.avi`, `.mkv`) found in the `videos` folder.
- **CSV Metadata Support:**  
 If `video_details.csv` file is populated properly, metadata (title, description, tags, thumbnail, upload date/time) is applied to matching video files. Otherwise, default metadata is generated from the video filename.
- **Scheduling:**  
 Supports scheduled uploads using the `upload_date` and `upload_time` fields from the CSV. If scheduling data exists, the video is scheduled via YouTube’s API.
- **Thumbnail Upload:**
 Supports scheduled uploads using the `upload_date` and `upload_time` fields from the CSV. If scheduling data exists, the video is scheduled via YouTube’s API.
- **Local & Google Sheets Logging:**  
  Upload details are logged to a local text file. When enabled with the `--use-sheets` flag, the tool logs details to a Google Sheets spreadsheet. The spreadsheet ID is taken from the `SPREADSHEET_ID` environment variable if set; otherwise, a new spreadsheet is created automatically.
- **Dynamic SEO Optimization:**  
  When enabled with the `--ai-seo` flag, the tool uses OpenAI's API to completely generate new SEO-optimized metadata (title, description, and tags) for each video. An OpenAPI key environment variable is required to use this feature.
## Prerequisites

- **Python 3.7+**
- **pip** (Python package installer)
- **Google Cloud Project:**
  - Since the script is in the testing stage, a project should be initialized.
  - Add yourself as a test user.
  - Enable the [YouTube Data API v3](https://console.developers.google.com/apis/library/youtube.googleapis.com)
  - Enable the [Google Sheets API](https://console.developers.google.com/apis/library/sheets.googleapis.com)
  - Download the OAuth 2.0 client credentials as `client_secret.json` and place it in the project root.
- **OpenAI API Key:**  
  For AI-powered SEO optimization, set your API key in an environment variable (`OPENAI_API_KEY`).
- **Directory Structure:**  
  - A folder called `videos` containing your video files.
  - Optionally, a folder called `thumbnails` containing thumbnail images.
  - Optionally, a CSV file named `video_details.csv` with the following headers:  
    `filename,title,description,tags,thumbnail,upload_date,upload_time`
## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/MustAWPa/yt-autobot.git
   cd yt-autobot
   
   pip install -r requirements.txt

2. **Run the Script:**
   ```bash
   python script.py

## Bonus features

3. **Log to Google Sheets**
   To log video details to Google sheets, set your spreadsheet ID in the environment file otherwise a sheet will be created for you.
   ```bash
   python script.py --use-sheets

5. **Dynamic Title and Description Renaming using OpenAI**
   To enable AI-powered SEO optimization (requires an OpenAI API key set in your environment)
   ```bash
   python script.py --ai-seo
  
