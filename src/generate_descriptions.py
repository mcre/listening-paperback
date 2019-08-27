import json
import shutil
import string
import sys


with open('config.json', 'r') as f:
    config = json.load(f)


def num_to_kanji(num):
    table = str.maketrans({'0': '〇', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'})
    return str(num).translate(table)


def main(part_id, version):
    with open('template_description.txt', 'r') as f:
        template = f.read()

    output = string.Template(template).substitute({
        'title': config['title'],
        'author': config['author'],
        'part_text': f'第{num_to_kanji(part_id + 1)}回',
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
