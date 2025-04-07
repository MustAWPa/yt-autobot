import os
import csv
import datetime
import argparse
import json
import ast
from openai import OpenAI
from dotenv import load_dotenv
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

# defining upload scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/spreadsheets"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch upload videos with optional Google Sheets logging."
    )
    parser.add_argument(
        "--use-sheets",
        action="store_true",
        help="Enable logging to Google Sheets."
    )
    parser.add_argument(
        "--spreadsheet-id",
        type=str,
        default="",
        help="Google Sheets spreadsheet ID. If omitted and --use-sheets is set, a new sheet will be created."
    )
    parser.add_argument(
        "--ai-seo",
        action="store_true",
        help="Enable AI-powered SEO optimization for title, description, and tags."
    )
    return parser.parse_args()

def authentication():
    client_secret = "client_secret.json"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secret, SCOPES)
    creds = flow.run_local_server(port=8080, prompt='consent')
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    sheets = googleapiclient.discovery.build("sheets", "v4", credentials=creds)
    return youtube, sheets

def upload_video (youtube, file_path, title, description, tags, categoryId="22", privacyStatus="private",
                  scheduled_datetime=None, thumbnail=None):
    request_body = {
        "snippet": {
            "title" : title,
            "description": description,
            "tags": tags,
            "categoryId": categoryId
        },
        "status": {
            "privacyStatus": privacyStatus
        }
    }

    if scheduled_datetime:
        request_body["status"]["privacyStatus"] = "private"
        publish_at = scheduled_datetime.astimezone(datetime.timezone.utc).isoformat()
        request_body["status"]["publishAt"] = publish_at

    video = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=video
    )

    print(f"Starting upload for: {title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress for '{title}': {int(status.progress() * 100)}%")
    print(f"Upload complete for '{title}'. Video ID: {response.get('id')}\n")
    video_id = response.get("id")
    
    if thumbnail:
        thumbnail = f"thumbnails/{thumbnail}"
        if os.path.exists(thumbnail):
            thumb_media = MediaFileUpload(thumbnail)
            thumb_request = youtube.thumbnails().set(videoId=video_id, media_body=thumb_media)
            thumb_request.execute()
            print(f"Thumbnail set for video '{title}'.")
        else:
            print(f"Thumbnail file '{thumbnail}' not found. Skipping thumbnail.")
    
    return video_id

def create_spreadsheet(sheets, title="Video Upload Log"):
    body = {
        "properties": {
            "title": title
        }
    }
    spreadsheet = sheets.spreadsheets().create(body=body, fields="spreadsheetId").execute()
    new_id = spreadsheet.get("spreadsheetId")
    print(f"Created new spreadsheet with ID: {new_id}")
    return new_id

def initialize_sheet_headers(sheets, spreadsheet_id):

    header_range = "Sheet1!A1:H1"
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=header_range
    ).execute()
    values = result.get("values", [])
    if not values or not values[0]:
        headers = [["Filename", "Title", "Description", "Video ID", "URL", "Actual Upload Time", "Scheduled Publish", "Tags"]]
        body = {"values": headers}
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=header_range,
            valueInputOption="RAW",
            body=body
        ).execute()
        print("Sheet headers set.")
    else:
        print("Sheet headers already exist.")

def generate_ai_seo_metadata(original_title, original_description, original_tags):
    try:
        client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        )   

        response = client.responses.create(
            model="gpt-4o",
            instructions="You are an SEO expert. Generate completely new SEO-optimized metadata for a YouTube video",
            input=f"""Generate a new title, a new description, and additional tags to boost SEO. Title: {original_title}. 
            Description: {original_description}. Tags: {original_tags}. Generate a new title, a new description, and additional tags to boost SEO.
            Return the result as a JSON object with keys title, description, and tags (tags as a list)."""
        )
               
        clean_response = response.output_text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_response)
        print("running")
        new_title = result.get("title", original_title)
        new_description = result.get("description", original_description)
        new_tags = result.get("tags", original_tags)
    
    except Exception as e:
        print(f"Error in AI SEO generation: {e}")
        return original_title, original_description, original_tags
    
    return new_title, new_description, new_tags

def log_upload(video_data):
    if os.path.isfile("upload_log.txt"):
        with open("upload_log.txt", "a") as f:
            line = f"{video_data['filename']}, {video_data['title']}, {video_data['video_id']}, {video_data['url']}, {video_data['actual_upload_time']}, {video_data.get('scheduled_publish', 'Not Scheduled')}\n"
            f.write(line)
    else:
        with open("upload_log.txt", "w") as f:
            header = "Filename, Title, Video ID, URL, Upload Time, Scheduled Publish\n"
            f.write(header)
            line = f"{video_data['filename']}, {video_data['title']}, {video_data['video_id']}, {video_data['url']}, {video_data['actual_upload_time']}, {video_data.get('scheduled_publish', 'Not Scheduled')}\n"
            f.write(line)

def update_google_sheet(sheets, video_data, spreadsheet_id):
    row = [
        video_data.get("filename"),
        video_data.get("title"),
        video_data.get("description"),
        video_data.get("video_id"),
        video_data.get("url"),
        video_data.get("actual_upload_time"),
        video_data.get("scheduled_publish", "Not Scheduled"),
        ", ".join(video_data.get("tags", []))
    ]
    body = {"values": [row]}
    sheets.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A:H",
        valueInputOption="RAW",
        body=body
    ).execute()
    print("Updated Google Sheet with video data.")

def video_details(csv_file):
    '''
    Reads video details from the csv file
    Expected headers: filename, title, description, tags, thumbnail, upload_date, upload_time
    '''
    details = []
    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if "tags" in row and row["tags"]:
                row["tags"] = [tag.strip() for tag in row["tags"].split(',')]
            else:
                row["tags"] = []
            details.append(row)
    return details

def main():
    load_dotenv()
    args = parse_args()
    youtube, sheets = authentication()
    csv_file = "video_details.csv"
    video_names = video_details(csv_file)

    spreadsheet_id = None
    if args.use_sheets:
        if args.spreadsheet_id:
            spreadsheet_id = args.spreadsheet_id
        else:
            spreadsheet_id = create_spreadsheet(sheets)
        initialize_sheet_headers(sheets, spreadsheet_id)

    incoming_videos = os.listdir("videos")

    if incoming_videos==[]:
        print("No videos to upload")
        return
    
    for video in video_names:
        try:
            filename = video.get("filename", incoming_videos.pop())
            num = 1
            title = video.get("title", f"Untitled video {num}")
            description = video.get("description", f"Uploaded video number {num}")
            tags = video.get("tags", [])
            thumbnail = video.get("thumbnail", None)
            upload_date = video.get("upload_date")
            upload_time = video.get("upload_time")

            scheduled_datetime = None

            if upload_date or upload_time:
                if not upload_date:
                    upload_date = datetime.datetime.today().strftime("%Y-%m-%d")
                if not upload_time:
                    upload_time = "00:00"
            
                scheduled_datetime = datetime.datetime.strptime(f"{upload_date} {upload_time}", "%Y-%m-%d %H:%M")
            
            if args.ai_seo:
                    title, description, tags = generate_ai_seo_metadata(title, description, tags)

            
            video_id = upload_video(youtube, f"videos/{filename}", title, description, tags,
                                    scheduled_datetime=scheduled_datetime, thumbnail=thumbnail)
            video_url = f"https://youtu.be/{video_id}"

            actual_upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            scheduled_publish = (scheduled_datetime.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                                if scheduled_datetime else "Not Scheduled")

            video_data = {
                "filename": filename,
                "title": title,
                "description": description,
                "video_id": video_id,
                "url": video_url,
                "actual_upload_time": actual_upload_time,
                "scheduled_publish": scheduled_publish,
                "tags": tags
            }

            log_upload(video_data)
            if args.use_sheets and spreadsheet_id:
                update_google_sheet(sheets, video_data, spreadsheet_id)
        
        except Exception as e:
            print(f"Error processing video '{video.get('filename', 'Unknown')}': {e}. Skipping and continuing.")
            continue

    return

if __name__ == "__main__":
    main()
