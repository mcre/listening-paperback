import glob
import json
import os

import mutagen.mp3
import regex as re

PATTERNS = {
    'tag': re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>'''),
}

with open('consts.json', 'r') as f:
    consts = json.load(f)


def basename(path):
    return os.path.splitext(os.path.basename(path))[0]


def main():
    # chapter と pages の対応を作成()
    with open(f'chapters_and_pages.json', 'r') as f:
        chapters_and_pages = json.load(f)
    chapters = [{
        'chapter_id': chapter_id,
        'movie_path': f'chapter_movies/{chapter_id:0>5}.mp4',
        'pages': [{
            'page_id': page_id,
            'text': page,
            'movie_path': f'page_movies/{chapter_id:0>5}_{page_id:0>5}.mp4',
            'words': [],
        } for page_id, page in enumerate(pages)],
    } for chapter_id, pages in enumerate(chapters_and_pages)]

    # page に image_path, serial_page_id(chapterによらないページ通し番号)を設定
    cursor = 0
    page_image_paths = sorted(glob.glob('page_images/novel*.png'))
    for chapter in chapters:
        for page in chapter['pages']:
            page['image_path'] = page_image_paths[cursor]
            page['serial_page_id'] = cursor
            cursor += 1

    # all_voices を作成(これをchapterごとに分解してぶら下げる)
    all_voices = [{
        'voice_id': voice_id,
        'voice_path': voice_path,
        'marks_path': f'marks/{basename(voice_path)}.json',
        'duration': mutagen.mp3.MP3(voice_path).info.length,
    } for voice_id, voice_path in enumerate(sorted(glob.glob('voices/text*.mp3')))]

    # all_words を作成(これをpageごとに分解してぶら下げる)
    words_in_voices = []
    for voice in all_voices:
        with open(voice['marks_path'], 'r') as f:
            marks = json.load(f)
            words_in_voices.append([mark for mark in marks if mark['type'] == 'word'])
    all_words = [{
        'voice_id': voice_id,
        'voice_duration': all_voices[voice_id]['duration'],
        'word_num_in_voice': len(words_in_voice),
        'word_id_in_voice': word_id_in_voice,
        'start_in_voice': word['time'] / 1000,
        'text': word['value'],
    } for voice_id, words_in_voice in enumerate(words_in_voices) for word_id_in_voice, word in enumerate(words_in_voice)]

    # all_words を分解しながら page に words としてぶら下げる
    cur = 0
    remain = ''
    for chapter in chapters:
        for page in chapter['pages']:
            word_id = 0
            index_in_page = - len(remain)
            remain = f'{remain}{page["text"]}'
            while len(remain) > 0 and cur < len(all_words):
                word = all_words[cur]
                w = PATTERNS['tag'].sub('', word['text'])
                if (loc := remain.find(w)) >= 0:
                    ll = loc + len(w)
                    word['word_id'] = word_id
                    word['animation_image_path'] = f'animation_images/{chapter["chapter_id"]:0>5}_{page["page_id"]:0>5}_{word_id:0>5}.png'
                    word['skipped_text'] = remain[:loc]
                    word['start_index_in_page'] = index_in_page + loc
                    page['words'].append(word)
                    remain = remain[ll:]
                    cur += 1
                    index_in_page += ll
                    word_id += 1
                else:
                    break
    try:
        chapters[-1]['pages'][-1]['words'][-1]['text'] += remain  # 最後の word に残りの文字を追加
    except Exception as e:
        pass

    # skipped_textを前後に振り分ける
    for chapter in chapters:
        for page in chapter['pages']:
            for word_id, word in enumerate(page['words']):
                if len(word['skipped_text']) > 0:
                    cnt = 0
                    for char in word['skipped_text']:
                        if char in ('、', '。', '」', '？', '！', '』', '）'):
                            cnt += 1
                        else:
                            break
                    bef = word['skipped_text'][:cnt]
                    aft = word['skipped_text'][cnt:]
                    if before_word_pointer is not None:
                        before_word_pointer['text'] = f"{before_word_pointer['text']}{bef}"
                    if word_id + 1 < len(page['words']):
                        word['text'] = f"{aft}{word['text']}"
                        word['start_index_in_page'] -= len(aft)
                before_word_pointer = word

    # all_voices を分解しながら chapter に voices としてぶら下げる。start(chapter内の音声再生開始時刻)も計算
    for chapter in chapters:
        voice_ids = [word['voice_id'] for page in chapter['pages'] for word in page['words']]
        if len(voice_ids) < 1:
            continue
        voices = {voice_id: all_voices[voice_id] for voice_id in range(min(voice_ids), max(voice_ids) + 1)}
        s = 0
        for voice in voices.values():
            voice['start'] = s
            s += voice['duration'] + consts['voice_interval']
        chapter['voices'] = voices

    # 各 word の start(chapter内の開始時刻)等を計算
    for chapter in chapters:
        for page in chapter['pages']:
            for word in page['words']:
                word['voice_start'] = chapter['voices'][word['voice_id']]['start']
                word['start'] = word['voice_start'] + word['start_in_voice']

    # 各 word の 他の時刻を計算(次のstartを使うので↑と一緒にはまわせない)
    for chapter in chapters:
        all_words_in_chapter = []
        for page in chapter['pages']:
            all_words_in_chapter.extend(page['words'])
        for i, word in enumerate(all_words_in_chapter):
            if word['word_id_in_voice'] + 1 != word['word_num_in_voice']:  # 通常
                word['end'] = word['voice_start'] + all_words_in_chapter[i + 1]['start_in_voice']  # 次のwordの開始時刻
            else:  # voice の中の最後の word の場合
                word['end'] = word['voice_start'] + word['voice_duration']  # voice の開始 + voice の長さを end とする
            word['duration'] = word['end'] - word['start']

            if i + 1 < len(all_words_in_chapter):  # ページの最後の word じゃない場合
                next_word_start = all_words_in_chapter[i + 1]['start']
                word['duration_to_next_word_start'] = next_word_start - word['start']
            elif word['word_id_in_voice'] + 1 == word['word_num_in_voice']:  # ページの最後の word だけど voice の最後の word のとき
                word['duration_to_next_word_start'] = word['duration']
            else:  # ページの最後の word のとき
                word['duration_to_next_word_start'] = 0

    # 各 word のさらに↑を使うのを計算
    for chapter in chapters:
        all_words_in_chapter = []
        for page in chapter['pages']:
            all_words_in_chapter.extend(page['words'])
        for i, word in enumerate(all_words_in_chapter):
            word['next_word_duration'] = 0
            if i + 1 < len(all_words_in_chapter):  # 最後のwordじゃない場合
                word['next_word_duration'] = all_words_in_chapter[i + 1]['duration']

    # 各 page に時刻を追加
    for chapter in chapters:
        for page in chapter['pages']:
            if len(page['words']) < 1:
                page['start'], page['end'], page['duration'] = 0, 0, 0
                continue
            page['start'] = page['words'][0]['start']
            page['end'] = page['words'][len(page['words']) - 1]['end']
            page['duration'] = page['end'] - page['start']

    # 各chapter に duration を追加
    for chapter in chapters:
        start = chapter['pages'][0]['start'] if 'start' in chapter['pages'][0] else 0
        end = chapter['pages'][-1]['end'] if 'end' in chapter['pages'][-1] else 0
        chapter['duration'] = end - start

    # 不要な変数を削除、整形
    for chapter in chapters:
        for key in ['duration']:
            chapter[key] = round(chapter[key], 3)
        for page in chapter['pages']:
            for key in ['start', 'end', 'duration']:
                if key in page:
                    page[key] = round(page[key], 3)
            for word in page['words']:
                del word['voice_duration'], word['word_num_in_voice'], word['start_in_voice'], word['skipped_text'], word['voice_start']
                for key in ['start', 'end', 'duration', 'duration_to_next_word_start', 'next_word_duration']:
                    if key in word:
                        word[key] = round(word[key], 3)
        for voice in chapter.get('voices', {}).values():
            for key in ['start', 'duration']:
                voice[key] = round(voice[key], 3)

    # 書き込み
    with open(f'timekeeper.json', 'w') as f:
        json.dump({'chapters': chapters}, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
