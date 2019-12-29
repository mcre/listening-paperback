import glob
import json
import os
import sys

import mutagen.mp3
import regex as re

import util as u

PATTERNS = {
    'tag': re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>'''),
    'kanji': re.compile(r'[\p{Han}ヶ]')
}

with open('consts.json', 'r') as f:
    consts = json.load(f)

with open('config.json', 'r') as f:
    config = json.load(f)


def main():
    # chapter と pages の対応を作成()
    with open(f'chapters_and_pages.json', 'r') as f:
        chapters_and_pages = json.load(f)
    chapters = [{
        'chapter_id': chapter_id,
        'movie_path': f'chapter_movies/{chapter_id:0>5}.avi',
        'pages': [{
            'page_id': page_id,
            'text': page,
            'movie_path': f'page_movies/{chapter_id:0>5}_{page_id:0>5}.avi',
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
        'marks_path': f'marks/{u.basename(voice_path)}.json',
        'duration': mutagen.mp3.MP3(voice_path).info.length,
    } for voice_id, voice_path in enumerate(sorted(glob.glob('voices/text*.mp3')))]

    # all_words を作成(これをpageごとに分解してぶら下げる)
    words_in_voices = []
    for voice in all_voices:
        with open(voice['marks_path'], 'r') as f:
            marks = json.load(f)
            word_marks = []
            for mark in marks:
                if mark['type'] == 'word':
                    word_marks.append(mark)
                    word_marks[-1]['viseme'] = ''
                if mark['type'] == 'viseme' and mark['value'] != 'sil':
                    word_marks[-1]['viseme'] += mark['value']
            words_in_voices.append([mark for mark in word_marks])

    all_words = [{
        'voice_id': voice_id,
        'voice_duration': all_voices[voice_id]['duration'],
        'word_num_in_voice': len(words_in_voice),
        'word_id_in_voice': word_id_in_voice,
        'start_in_voice': word['time'] / 1000,
        'text': PATTERNS['tag'].sub('', word['value']),
        'viseme': word['viseme'],
        'includes_kanji': True if PATTERNS['kanji'].search(word['value']) else False,
    } for voice_id, words_in_voice in enumerate(words_in_voices) for word_id_in_voice, word in enumerate(words_in_voice)]

    # all_words を分解しながら page に words としてぶら下げる
    cur = 0
    remain = ''
    for chapter in chapters:
        for page in chapter['pages']:
            word_id = 0
            index_in_page = - len(remain)
            if len(remain) > 100:
                print(f'marks と chapters_and_pages の対応が乱れています。remainが{len(remain)}文字存在します。『{remain[:50]}・・・』から『{all_words[cur]["text"]}』(voice_id: {all_words[cur]["voice_id"]})が見つからないようです。')
                sys.exit(1)
            remain = f'{remain}{page["text"]}'.replace('-', '')  # PDF上で勝手に英単語が分割されるハイフンはどうにもならないので無理やり消す
            while len(remain) > 0 and cur < len(all_words):
                word = all_words[cur]
                w = word['text'].replace(' ', '').replace('-', '')
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
    chapters[-1]['pages'][-1]['words'][-1]['text'] += remain  # 最後の word に残りの文字を追加

    # skipped_textを前後に振り分ける
    before_word_pointer = None
    for chapter in chapters:
        for page in chapter['pages']:
            for word_id, word in enumerate(page['words']):
                word['original_text'] = word['text']
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

    # この次でエラーになることが多いのでこの時点を出力しておく。
    with open(f'tmp_timekeeper.json', 'w') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)

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
        for page_id, page in enumerate(chapter['pages']):
            if len(page['words']) == 0 and page['text'] == '':  # 空ページの場合
                if page_id == 0:
                    tm = chapters[chapter['chapter_id'] - 1]['pages'][-1]['end']
                else:
                    tm = chapter['pages'][page_id - 1]['end']
                page['start'] = tm
                page['end'] = tm + consts['blank_page_duration']
            else:  # 空ページじゃない場合
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
                page[key] = round(page[key], 3)
            for word in page['words']:
                del word['voice_duration'], word['word_num_in_voice'], word['skipped_text'], word['voice_start']
                for key in ['start', 'end', 'duration', 'duration_to_next_word_start', 'next_word_duration']:
                    word[key] = round(word[key], 3)
        for voice in chapter['voices'].values():
            for key in ['start', 'duration']:
                voice[key] = round(voice[key], 3)

    # chapters から parts を構成
    chapters_in_parts = []
    part, duration = [], 0

    print('\n== chapters ==')
    for chapter in chapters:
        print(f"chapter_id: {chapter['chapter_id']}, duration: {u.seconds_to_str(chapter['duration'])}")
        part.append(chapter)
        duration += chapter['duration']
        if duration > config['part_duration']:
            chapters_in_parts.append(part)
            part, duration = [], 0
    if len(part) > 0:
        chapters_in_parts.append(part)
    if len(chapters_in_parts) > 1:  # 2個以上のときの処理
        # 最後のパートが min_part_durationにも達していない場合はその前に足し込む
        last_part_duration = sum(x['duration'] for x in chapters_in_parts[-1])
        if last_part_duration < config['min_part_duration']:
            chapters_in_parts[-2].extend(chapters_in_parts[-1])
            del chapters_in_parts[-1]
    parts = [{'chapters': chapters} for chapters in chapters_in_parts]

    print('\n== parts ==')
    for part_id, part in enumerate(parts):
        part['part_id'] = part_id
        part['duration'] = sum([chapter['duration'] for chapter in part['chapters']])
        chapter_ids = ', '.join([str(chapter['chapter_id']) for chapter in part['chapters']])
        print(f'part_id:{part_id:>3}, duration: {u.seconds_to_str(part["duration"])}, chapter_ids: [{chapter_ids}]')

    # 書き込み
    with open(f'timekeeper.json', 'w') as f:
        json.dump({'parts': parts}, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
