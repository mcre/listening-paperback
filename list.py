import datetime as dt
import os

import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
import pytz


def dateformat(date_str):
    return dt.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M')


def main():
    flow = flow_from_clientsecrets('./certs/youtube_client_secrets.json', scope='https://www.googleapis.com/auth/youtube.readonly')

    storage = Storage(f'{os.environ["HOME"]}/.youtube-upload-credentials.json')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        flags = argparser.parse_args()
        credentials = run_flow(flow, storage, flags)
    youtube = build('youtube', 'v3', http=credentials.authorize(httplib2.Http()))

    videos = {}
    channels_res = youtube.channels().list(mine=True, part='contentDetails').execute()
    for channel in channels_res['items']:
        uploads_id = channel['contentDetails']['relatedPlaylists']['uploads']
        playlist_req = youtube.playlistItems().list(playlistId=uploads_id, part='snippet, status', maxResults=50)
        while playlist_req:
            playlist_res = playlist_req.execute()
            for item in playlist_res['items']:
                videos[item['snippet']['resourceId']['videoId']] = {
                    'id': item['snippet']['resourceId']['videoId'],
                    'url': f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
                    'title': item['snippet']['title'],
                    'version': item['snippet']['description'][-16:],
                    'status': item['status']['privacyStatus'],
                    'publish_at': dateformat(item['snippet']['publishedAt']) if item['status']['privacyStatus'] == 'public' else None,
                }
            playlist_req = youtube.playlistItems().list_next(playlist_req, playlist_res)

    private_video_ids = [video_id for video_id, video in videos.items() if video['status'] == 'private']
    videos_req = youtube.videos().list(part='status', id=', '.join(private_video_ids))
    while videos_req:
        videos_res = videos_req.execute()
        for item in videos_res['items']:
            videos[item['id']]['publish_at'] = dateformat(item['status']['publishAt']) if 'publishAt' in item['status'] else '9999-99-99 99:99'
        videos_req = youtube.videos().list_next(videos_req, videos_res)

    videos = sorted([video for video in videos.values()], key=lambda x: x['publish_at'])

    print('id, 公開状態, 公開日時, version, タイトル')
    for v in videos:
        print(f"{v['id']}, {v['status']:>7}, {v['publish_at']}, {v['version']}, {v['title']}")


if __name__ == '__main__':
    main()
