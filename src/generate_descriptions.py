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
        template = f.read()

    output = string.Template(template).substitute({
        'title': config['title'],
        'author': config['author'],
        'part_text': f'第{u.number_to_kansuji(part_id + 1)}回' if len(timekeeper['parts']) > 1 else '',
        'play_list': config['play_list'],
        'music_author': config['music']['author'],
        'music_url': config['music']['url'],
        'cover_author': config['cover']['author'],
        'cover_url': config['cover']['url'],
        'version': version,
    })
    with open(f'part_movies/{part_id:0>5}/description.txt', 'w') as f:
        f.write(output)
    shutil.copy(f'cover_images/{part_id:0>5}.png', f'part_movies/{part_id:0>5}/thumbnail.png')


if __name__ == '__main__':
    main(int(sys.argv[1]), sys.argv[2])
