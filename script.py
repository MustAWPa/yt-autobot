import os
import csv
import datetime
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
# defining upload scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = "1UNVITNb0_3uFqs-hd-HXthkkWGiBobImgtOcsaU2ATQ"

def authentication():
    client_secret = "client_secret.json"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secret, SCOPES)
    creds = flow.run_local_server(port=8080, prompt='consent')
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    sheets = googleapiclient.discovery.build("sheets", "v4", credentials=creds)
    return youtube, sheets

def upload_video (youtube, file_path, title, description, tags, categoryId="22", privacyStatus="private",
                  scheduled_datetime=None):
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
    return response.get("id")

def log_upload(video_data):
    if os.path.isfile("upload.txt"):
        with open("upload_log.txt", "a") as f:
            line = f"{video_data['filename']}, {video_data['title']}, {video_data['video_id']}, {video_data['url']}, {video_data['actual_upload_time']}, {video_data.get('scheduled_publish', 'Not Scheduled')}\n"
            f.write(line)
    else:
        with open("upload_log.txt", "w") as f:
            header = "Filename, Title, Video ID, URL, Upload Time, Scheduled Publish\n"
            f.write(header)
            line = f"{video_data['filename']}, {video_data['title']}, {video_data['video_id']}, {video_data['url']}, {video_data['actual_upload_time']}, {video_data.get('scheduled_publish', 'Not Scheduled')}\n"
            f.write(line)

def update_google_sheet(sheets, video_data):
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
        spreadsheetId=SPREADSHEET_ID,
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
    youtube, sheets = authentication()
    csv_file = "video_details.csv"

    video_names = video_details(csv_file)

    incoming_videos = os.listdir("videos")
    for video in video_names:
        filename = video.get("filename", incoming_videos.pop())
        num = 1
        title = video.get("title", f"Untitled video {num}")
        description = video.get("description", f"Uploaded video number {num}")
        tags = video.get("tags", [])

        upload_date = video.get("upload_date")
        upload_time = video.get("upload_time")

        scheduled_datetime = None

        if upload_date or upload_time:
            if not upload_date:
                upload_date = datetime.datetime.today().strftime("%Y-%m-%d")
            if not upload_time:
                upload_time = "00:00"
            
            scheduled_datetime = datetime.datetime.strptime(f"{upload_date} {upload_time}", "%Y-%m-%d %H:%M")
            


        video_id = upload_video(youtube, f"videos/{filename}", title, description, tags,
                                scheduled_datetime=scheduled_datetime)
        video_url = f"https://youtu.be/{video_id}"

        actual_upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scheduled_publish = (scheduled_datetime.astimezone(datetime.timezone.utc).isoformat()
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
        update_google_sheet(sheets,video_data)

    return

if __name__ == "__main__":
    main()