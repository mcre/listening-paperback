import json
import shutil
import string
import sys

import util as u


with open('config.json', 'r') as f:
    config = json.load(f)
with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def main(part_id, version):
    with open('template_description.txt', 'r') as f:
        t_description = f.read()
    with open('template_upload_settings.json', 'r') as f:
        t_settings = f.read()

    path = f'part_movies/{part_id:0>5}'

    settings = string.Template(t_settings).substitute({
        'title': config['title'],
        'author': config['author'],
        'part_text': f'第{u.number_to_kansuji(part_id + 1)}回' if len(timekeeper['parts']) > 1 else '',
        'version': version,
    })

    settings_json = json.loads(settings)
    with open(f'{path}/upload_settings.json', 'w') as f:
        json.dump(settings_json, f, ensure_ascii=False, indent=4)

    description = string.Template(t_description).substitute({
        'playlist': f"\n{config['title']}：https://www.youtube.com/playlist?list=${{playlist_id}}" if len(timekeeper['parts']) > 1 else '',
        'music_author': config['music']['author'],
        'music_url': config['music']['url'],
        'cover_author': config['cover']['author'],
        'cover_url': config['cover']['url'],
        'version': version,
    })
    with open(f'{path}/description.txt', 'w') as f:
        f.write(description)

    shutil.copy(f'cover_images/{part_id:0>5}.png', f'{path}/thumbnail.png')


if __name__ == '__main__':
    main(int(sys.argv[1]), sys.argv[2])