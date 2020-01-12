import json

import regex as re

PATTERNS = {
    'page': re.compile(r'Completed box being shipped out.*?\|\.\\special{'),
    'discretionaries': re.compile(r'\n([\.]*?)\\discretionary\n\1[\.]\\.*?\n|\n([\.]*?)\\discretionary\sreplacing\s2\n\2[\.]\\.*?\n\2[\.]\\.*?\n'),
    'accent': re.compile(r'\n.*?\\kern.*?\(for\saccent\)\n(.*?)\^\n.*?\\kern.*?\(for\saccent\)\n'),
    'char': re.compile(r'(?:\\J[TY]2/(?:mc|gt)/m/n/|\\OT1/lmr/m/n/|\\OML/lmm/m/it/)(?:7\.1|8\.40009|9\.79996|10\.8|13\.2|14|14\.8|15\.6|16\.4|17\.2|18|18\.8|19\.6|23\.8|35)\s(\S+?)(?:\s\(.*?\))?\n'),
    'ruby': re.compile(r'\\ruby{(.*?)}{(.*?)}'),
    'command': re.compile(r'\\(?!(part|chapter|textgt)).*?{(.*?)}({.*?})?'),
    'command_no_params': re.compile(r'\\(?!(part|chapter|textgt))\S*?\s'),
    'chapter': re.compile(r'(?:\\part{(.+?)}|\\chapter{(.+?)}\s*([^\\\n]{0,10})|%\smanual_chapter\s*([^\\\n]{0,10})|%\sblank_line\s*([^\\\n]{0,10}))'),
    'paragraphs': re.compile(r'^[^\\\n,%「]{20}', flags=re.MULTILINE),  # `「` は切れ目として不自然になりやすいから除く
}

COMBINATIONS_BEFORE = ['^^X']
COMBINATIONS_AFTER = ['^^a', '^^R', '^^S', '^^?']

REPLACES = {
    '^^L': 'fi', '^^M': 'fl', '^^Z': 'æ',
    '^^ae': 'ê',  # '^^aは独自'
    '^^Re': 'è',
    '^^Se': 'é', '^^SE': 'É', '^^Sn': 'ń', '^^Sr': 'ŕ', '^^Sy': 'ý',
    '^^?o': 'ö', '^^?u': 'ü',
    's^^X': 'ş', 't^^X': 'ţ',
}

# chapter分割の重み指定
SPLIT_PRIORITIES = {
    'first_page': 0,
    'part': 0,
    'chapter': 0,
    'manual_chapter': 0,
    'blank_line': 1,
    'coincidentally_newpage': 2,
}


def plain(text):
    ret = text
    ret = PATTERNS['ruby'].sub(r'\1', ret)
    ret = PATTERNS['command'].sub(r'\1', ret)
    ret = PATTERNS['command_no_params'].sub('', ret)
    return ret


def create_new_chapter(chapter_type):
    return {'chapter_type': chapter_type, 'split_priority': SPLIT_PRIORITIES[chapter_type], 'pages': []}


def main():
    with open('tex_output.txt', 'r') as f:
        output = f.read()

    output = output.replace('\n', '|')
    pages = PATTERNS['page'].findall(output)
    texts = []
    for page in pages:
        page = page.replace('|', '\n')
        page = PATTERNS['discretionaries'].sub('\n', page)
        page = PATTERNS['accent'].sub(r'\n\1^^a\n', page)
        chars = PATTERNS['char'].findall(page)
        for i, c in enumerate(chars):
            if c in COMBINATIONS_BEFORE:
                chars[i - 1] = chars[i - 1] + chars[i]
                chars[i] = ''
            if c in COMBINATIONS_AFTER:
                chars[i + 1] = chars[i] + chars[i + 1]
                chars[i] = ''

        for i, c in enumerate(chars):
            if c in REPLACES.keys():
                chars[i] = REPLACES[c]
            if len(chars[i]) >= 3:
                print(f'\n注意, 3文字以上のcharあり。REPLACESに追加すること: {chars[i]}\n{chars[:i + 2]}\n')
        texts.append(''.join(chars))

    with open('novel.tex', 'r') as f:
        tex = f.read()

    chapter_start_texts = []
    plain_tex = plain(tex)
    for s in PATTERNS['chapter'].findall(plain_tex):
        if len(s[0]) > 0:
            text = {'chapter_type': 'part', 'text': s[0]}
        elif len(s[1]) > 0:
            text = {'chapter_type': 'chapter', 'text': f'{s[1]}{s[2]}'}
        elif len(s[3]) > 0:
            text = {'chapter_type': 'manual_chapter', 'text': s[3]}
        elif len(s[4]) > 0:
            text = {'chapter_type': 'blank_line', 'text': s[4]}
        text['text'] = text['text'].replace('　', '')
        chapter_start_texts.append(text)

    print('chapter_start_texts:', chapter_start_texts)

    paragraphs = PATTERNS['paragraphs'].findall(plain_tex)
    # print('len(paragraphs):', len(paragraphs))
    # print('head(paragraphs):', paragraphs[:5])

    chapters = []
    new_chapter = create_new_chapter(chapter_type='first_page')
    for text in texts:
        next_chapter = chapter_start_texts[0] if len(chapter_start_texts) > 0 else None

        if next_chapter and text.startswith(next_chapter['text']):  # textと次のchapterが一致した場合はそこから新しいチャプター
            if len(new_chapter['pages']) > 0:  # 前のチャプターにページがあれば前のチャプターを確定させる
                chapters.append(new_chapter)
                # print('before_chapter_added > chapter_type', new_chapter['chapter_type'], ', pages0:', new_chapter['pages'][0][:20])
            new_chapter = create_new_chapter(chapter_type=next_chapter['chapter_type'])  # 新しいチャプターを作り始める
            chapter_start_texts = chapter_start_texts[1:]  # next_chapterを切り替える
            # print('new_chapter:', new_chapter['chapter_type'], text[:20])
            # print('next_chapter:', chapter_start_texts[0] if len(chapter_start_texts) > 0 else None, '\n')
        elif text[:20] in paragraphs:  # たまたまページ区切りと段落の区切りが一致したらそこから新しいチャプター
            if len(new_chapter['pages']) > 0:
                chapters.append(new_chapter)
                # print('before_chapter_added > chapter_type:', new_chapter['chapter_type'], ', pages0:', new_chapter['pages'][0][:20])
            new_chapter = create_new_chapter(chapter_type='coincidentally_newpage')
            used_index = paragraphs.index(text[:20])
            paragraphs = paragraphs[used_index + 1:]  # 使ったところまでの段落を消す
            # print('new_chapter:', new_chapter['chapter_type'], text[:20])
            # print('next_paragraph:', paragraphs[0] if len(paragraphs) > 0 else None, '\n')
        new_chapter['pages'].append(text)
    chapters.append(new_chapter)  # 文末まで行ったらchaptersに足す

    # 1ページしか無いchapterは、後ろのpriorityより高いか同じならつなぐ
    new_chapters = []
    next_of_part = False
    for chapter_id, chapter in enumerate(chapters):
        if next_of_part:
            next_of_part = False
        elif len(chapter['pages']) == 1 and chapter_id < len(chapters) - 1 and chapter['split_priority'] <= chapters[chapter_id + 1]['split_priority']:
            new_chapters.append({
                'chapter_type': chapter['chapter_type'],
                'split_priority': chapter['split_priority'],
                'pages': chapter['pages'] + chapters[chapter_id + 1]['pages']
            })
            next_of_part = True
        else:
            new_chapters.append(chapter)
    chapters = new_chapters

    # 整形
    chapters = [{
        'chapter_id': chapter_id,
        'chapter_type': chapter['chapter_type'],
        'split_priority': chapter['split_priority'],
        'movie_path': f'chapter_movies/{chapter_id:0>5}.avi',
        'pages': [{
            'page_id': page_id,
            'text': page,
            'movie_path': f'page_movies/{chapter_id:0>5}_{page_id:0>5}.avi',
        } for page_id, page in enumerate(chapter['pages'])],
    } for chapter_id, chapter in enumerate(chapters)]

    with open('chapters.json', 'w') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)

    print('\n== chapters ==')
    for chapter in chapters:
        print(f"chapter_id: {chapter['chapter_id']:>3}, split_priority: {chapter['split_priority']}, chapter_type: {chapter['chapter_type']}, {chapter['pages'][0]['text'][:10]}")


if __name__ == '__main__':
    main()
