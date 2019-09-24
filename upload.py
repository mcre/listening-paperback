import datetime as dt
import json
import os
import string
import subprocess
import sys

import youtube_util as yu


def create_playlist(playlist_title):
    item = yu.youtube().playlists().insert(part='id, snippet, status', body={
        'snippet': {
            'title': playlist_title,
            'description': '著作権が切れた日本の名作を「聴きやすく」動画にまとめます。\n通勤中、運転中、就寝前などにご活用ください。',
        },
        'status': {
            'privacyStatus': 'public',
        }
    }).execute()
    return item['id']


def get_playlist_id(playlist_title):
    playlists = yu.youtube().playlists()
    request = playlists.list(mine=True, part='id, snippet')
    while request:
        results = request.execute()
        for item in results['items']:
            if item.get('snippet', {}).get('title') == playlist_title:
                return item.get('id')
        request = playlists.list_next(request, results)
    return create_playlist(playlist_title)


def insert_to_playlist(playlist_id, video_id):
    return yu.youtube().playlistitems().insert(part='snippet, contentDetails, status', body={
        'snippet': {
            'playlistId': playlist_id,
            'resourceId': video_id,
        }
    }).execute()


def main(project, version, start_publish_at, start_part_id, end_part_id):
    os.makedirs('tmp', exist_ok=True)
    path = f'./projects/{project}/output/{version}'
    publish_at = dt.datetime.fromisoformat(f'{start_publish_at}+09:00')
    for part_id in range(start_part_id, end_part_id + 1):
        part_path = f'{path}/{part_id:0>5}'

        with open(f'{part_path}/description.txt', 'r') as f:
            description = f.read()
        with open(f'{part_path}/upload_settings.json', 'r') as f:
            settings = json.load(f)

        with open('tmp/description.txt', 'w') as f:
            f.write(string.Template(description).substitute({'playlist_id': get_playlist_id(settings['playlist_title'])}))
        print('---------------------------')
        print('part_id:', part_id)
        print(settings['title'])
        print(settings['version'])
        print(f'公開日:', publish_at.strftime('%Y年%m月%d日 %H時%M分(JST)'))
        print('この動画をアップします。よろしいですか？')
        y = input('y/n : ')
        if y != 'y':
            print('中断します')
            break

        response = subprocess.check_output(
            f'''youtube-upload \
                --title="{settings['title']}" --description-file="tmp/description.txt" \
                --category="Entertainment" --tags="{','.join(settings['tags'])}" \
                --default-language="ja" --default-audio-language="ja" --client-secrets="./certs/youtube_client_secrets.json" \
                --playlist="{settings['playlist_name']}" --embeddable=True --privacy="public" \
                --publish-at="{publish_at.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.0Z')}" \
                --thumbnail="{part_path}/thumbnail.png" \
                {part_path}/movie.mp4
        ''', shell=True)
        print(response)
        if part_id == 0:  # 第一回は『「第一回」集』にも追加
            video_id = response.decode().strip()
            print(insert_to_playlist('PLaSpnMH0vy2FcAUNkaaXRd4P9uV1YBCqf', video_id))
            print('プレイリスト『「第一回」集』に追加しました。')
        publish_at += dt.timedelta(days=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
