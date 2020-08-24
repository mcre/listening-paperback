import json
import shutil
import string
import sys

import util as u

config = u.load_config()
timekeeper = u.load_timekeeper()


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
        'title': config['title'],
        'author': config['author'],
        'playlist': f"\n{config['title']}：https://www.youtube.com/playlist?list=${{playlist_id}}" if len(timekeeper['parts']) > 1 else '',
        'special_description': config['special_description'] + '\n\n' if 'special_description' in config and len(config['special_description']) > 0 else '',
        'music': f"・音楽：{config['music']['author']} {config['music']['url']}\n" if 'music' in config else '',
        'cover': f"・表紙：{config['cover']['author']} {config['cover']['url']}\n" if 'cover' in config else '',
        'version': version,
    })
    with open(f'{path}/description.txt', 'w') as f:
        f.write(description)

    shutil.copy(f'cover_images/{part_id:0>5}.png', f'{path}/thumbnail.png')


if __name__ == '__main__':
    main(int(sys.argv[1]), sys.argv[2])
