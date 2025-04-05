import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload
# defining upload scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authentication():
    client_secret = "client_secret.json"
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secret, SCOPES)
    
    return googleapiclient.discovery.build("youtube", "v3", credentials=flow.run_local_server(
        port=8080, prompt='consent'))

def upload_video (youtube, file_path, title, description, tags, categoryId="22", privacyStatus="private"):
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

def main():
    youtube = authentication()
    os.chdir("videos")
    directory_vids = os.listdir()
    for video in directory_vids:
        num = 1
        title = f"Test vid {num}"
        description = "Test video upload for the number {num}"
        tags = ["test", "automation"]
        num+=1
        upload_video(youtube, video, title, description, tags)
    return

if __name__ == "__main__":
    main()