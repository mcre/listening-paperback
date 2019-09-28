import json

import regex as re

PATTERNS = {
    'page': re.compile(r'Completed box being shipped out.*?\|\.\\special{'),
    'char': re.compile(r'(?<!\\discretionary[\.\n]*?)(?:\\J[TY]2/mc/m/n/|\\OT1/lmr/m/n/|\\OML/lmm/m/it/)(?:9\.79996|14|19\.6|23\.8|35)\s(\S+?)\n'),
    'ruby': re.compile(r'\\ruby{(.*?)}{(.*?)}'),
    'command': re.compile(r'\\(?!(part|chapter)).*?{(.*?)}({.*?})?'),
    'command_no_params': re.compile(r'\\(?!(part|chapter))\S*?\s'),
    'chapter': re.compile(r'(?:\\part{(.+?)}|\\chapter{(.+?)}\s*([^\\\n]{0,10})|(%\smanual_chapter)\s*([^\\\n]{0,10}))'),
}

COMBINATIONS_BEFORE = ['^^X']
COMBINATIONS_AFTER = ['^^R', '^^S', '^^?']

REPLACES = {
    '^^Z': 'æ',
    '^^Re': 'è',
    '^^Se': 'é', '^^SE': 'É', '^^Sn': 'ń', '^^Sr': 'ŕ', '^^Sy': 'ý',
    '^^?o': 'ö', '^^?u': 'ü',
    's^^X': 'ş', 't^^X': 'ţ',
}


def plain(text):
    ret = text
    ret = PATTERNS['ruby'].sub(r'\1', ret)
    ret = PATTERNS['command'].sub(r'\1', ret)
    ret = PATTERNS['command_no_params'].sub('', ret)
    return ret


def main():
    with open('tex_output.txt', 'r') as f:
        output = f.read()

    output = output.replace('\n', '|')
    pages = PATTERNS['page'].findall(output)
    texts = []
    for page in pages:
        page = page.replace('|', '\n')
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
            if len(chars[i]) >= 2:
                print(f'\n注意, 2文字以上のcharあり。REPLACESに追加すること: {chars[i]}\n{chars[:i + 2]}\n')
        texts.append(''.join(chars))

    # きたない
    with open('novel.tex', 'r') as f:
        tex = f.read()
    chapter_start_strings = PATTERNS['chapter'].findall(plain(tex))
    print(chapter_start_strings)

    if len(chapter_start_strings) <= 0:  # chapterがない場合
        with open('chapters_and_pages.json', 'w') as f:
            json.dump([texts], f, ensure_ascii=False, indent=2)
        return

    cursor = 0
    chapters = []
    texts_in_chapter = None
    before_chapter_text_id = None
    for text_id, text in enumerate(texts):
        if cursor < len(chapter_start_strings):
            s = [st.replace('　', '') for st in chapter_start_strings[cursor]]
            # 最初のテキストか、chapter文字列にあるもの。
            if text_id == 0 or text == s[0] or (len(s[1]) > 0 and text.startswith(f'{s[1]}{s[2]}')) or (len(s[3]) > 0 and text.startswith(s[4])):
                if text_id - 1 != before_chapter_text_id:  # partとchapterが連続している場合はこの処理をしない(同じchapter扱いにする)
                    if texts_in_chapter:
                        chapters.append(texts_in_chapter)
                    texts_in_chapter = []
                before_chapter_text_id = text_id
                cursor += 1
        texts_in_chapter.append(text)
    chapters.append(texts_in_chapter)

    with open('chapters_and_pages.json', 'w') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
