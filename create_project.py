import json
import os
import sys

import requests


def create_project(book_id):
    response = requests.get(f'http://pubserver2.herokuapp.com/api/v0.1/books/{book_id}')
    if response.status_code != 200:
        print(f'作品が見つかりません: book_id = {book_id}')
        sys.exit(1)
    book = json.loads(response.text)
    print(json.dumps(book, ensure_ascii=False, indent=2))
    print()

    if book['copyright']:
        print('著作権存続作品のため使用できません')
        sys.exit(1)

    if book['font_kana_type'] != '新字新仮名' or book['text_encoding'] != 'ShiftJIS':
        print('対応していない形式です')
        sys.exit(1)

    response = requests.get(f'http://pubserver2.herokuapp.com/api/v0.1/books/{book_id}/content?format=txt')
    if response.status_code != 200:
        print(f'テキストが見つかりません')
        sys.exit(1)

    response.encoding = 'sjis'
    text = response.text
    author = book['authors'][0]['last_name'] + book['authors'][0]['first_name']
    title = book['title']
    path = f'projects/{author}/{title}'

    config = {
        'title': title,
        'author': author,
        'font': 'aokin-mincho.ttf',
        'cover': {
            'file': 'framedesign_book02_black.png',
            'author': 'Frame Design',
            'url': 'http://frames-design.com/'
        },
        'music': {
            'file': 'bgm_maoudamashii_piano35.mp3',
            'author': '魔王魂',
            'url': 'https://maoudamashii.jokersounds.com/'
        },
        'part_duration': 600,
        'min_part_duration': 240,
        'tex_replaces': {},
        'manual_chapters': [],
        'special_rubies': [],
        'book_info': {k: v for k, v in book.items() if v != ''},
    }
    os.makedirs(path, exist_ok=True)
    with open(path + '/config.json', 'w') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
        print(f.name)
    with open(path + '/novel.txt', 'w') as f:
        f.write(text)
        print(f.name)


if __name__ == '__main__':
    create_project(sys.argv[1])
