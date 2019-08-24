import datetime as dt
import json
import subprocess
import sys


def main(project, version, start_publish_at, start_part_id, end_part_id):
    path = f'./projects/{project}/output/{version}'
    with open(f'{path}/input/config.json', 'r') as f:
        config = json.load(f)
    publish_at = dt.datetime.fromisoformat(f'{start_publish_at}+09:00')

    for part_id in range(start_part_id, end_part_id + 1):
        print(f'\n==========\npart_id: {part_id}')
        part_path = f'{path}/{part_id:0>5}'
        with open(f'{part_path}/description.txt', 'r') as f:
            description_all = f.read()
        descriptions = description_all.split('\n###############################################\n')
        description = descriptions[1].replace('\n', r'\\n')
        response = subprocess.check_output(
            f'''youtube-upload \
                --title="{descriptions[0]}" --description="{description}" \
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
