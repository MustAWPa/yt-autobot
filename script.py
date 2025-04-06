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
    
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=flow.run_local_server(
        port=8080, prompt='consent'))
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
        publish_at = scheduled_datetime.astimezone(datetime.timezone.etc).isoformat()
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

def update_google_sheet(sheets, video_data):
    

def video_details(csv_file):
    '''
    Reads video details from the csv file
    Headers: filename, title, description, tags, thumbnail, upload_date, upload_time
    '''
    details = []
    with open (csv_file, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["tags"] = row["tags"].split(',')
            details.append(row)
    return details

def main():
    youtube, sheets = authentication()
    csv_file = "video_details.csv"
    
    directory_vids = os.listdir()

    video_names = video_details(csv_file)

    os.chdir("videos")
    for video in video_names:
        num = 1
        title = video.get("title", "Untitled video {num}")
        description = video.get("description", "Uploaded video number {num}")
        tags = video.get("tags", [])

        upload_date = video.get("upload_date")
        upload_time = video.get("upload_time")

        if upload_date and upload_time:
            try:
                scheduled_datetime = datetime.datetime.strptime(
                    f"{upload_date} {upload_time}", "%Y-%m-%d %H:%M"
                )
            except Exception as e:
                print(f"Error parsing scheduled date/time for {title}: {e}")


        video_id = upload_video(youtube, video, title, description, tags)
        video_url = f"https://youtu.be/{video_id}"

        video_data = {
            "filename": video.get("filename"),
            "title": title,
            "description": description,
            "video_id": video_id,
            "url": video_url,
            "upload_time": scheduled_datetime,
            "tags": tags
        }

    return

if __name__ == "__main__":
    main()