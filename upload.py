import datetime as dt
import json
import os
import subprocess
import sys


def main(project, version, start_publish_at, start_part_id, end_part_id):
    os.makedirs('tmp', exist_ok=True)
    path = f'./projects/{project}/output/{version}'

    with open(f'./projects/{project}/config.json', 'r') as f:
        config = json.load(f)
    publish_at = dt.datetime.fromisoformat(f'{start_publish_at}+09:00')

    for part_id in range(start_part_id, end_part_id + 1):
        part_path = f'{path}/{part_id:0>5}'
        with open(f'{part_path}/description.txt', 'r') as f:
            description_all = f.read()
        descriptions = description_all.split('\n###############################################\n')
        with open('tmp/description.txt', 'w') as f:
            f.write(descriptions[1])
        print('---------------------------')
        print('part_id:', part_id)
        print(descriptions[0])
        print(descriptions[1].split('\n')[-1])
        print(f'公開日:', publish_at.strftime('%Y年%m月%d日 %H時%M分(JST)'))
        print('この動画をアップします。よろしいですか？')
        y = input('y/n : ')
        if y != 'y':
            print('中断します')
            break

        response = subprocess.check_output(
            f'''youtube-upload \
                --title="{descriptions[0]}" --description-file="tmp/description.txt" \
                --category="Entertainment" --tags="{descriptions[2]}" \
                --default-language="ja" --default-audio-language="ja" --client-secrets="./certs/youtube_client_secrets.json" \
                --playlist="{config['author']}『{config['title']}』" --embeddable=True --privacy="public" \
                --publish-at="{publish_at.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.0Z')}" \
                --thumbnail="{part_path}/thumbnail.png" \
                {part_path}/movie.mp4
        ''', shell=True)
        print(response)
        publish_at += dt.timedelta(days=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
