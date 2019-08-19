import json

import regex as re

PATTERNS = {
    'page': re.compile(r'Completed box being shipped out.*?\|\.\\special{'),
    'text': re.compile(r'\JT2/mc/m/n/(?:14|19\.6|23\.8|35)\s(\S+?)'),
    'ruby': re.compile(r'\\ruby{(.*?)}{(.*?)}'),
    'command': re.compile(r'\\(?!chapter).*?{(.*?)}'),
    'command_no_params': re.compile(r'\\(?!chapter)\S*?\s'),
    'chapter': re.compile(r'\\chapter{(.+?)}\s*?(\S{1,10})'),
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
        text = PATTERNS['text'].findall(page)
        texts.append(''.join(PATTERNS['text'].findall(page)))

    # きたない
    with open('novel.tex', 'r') as f:
        tex = f.read()
    chapter_start_strings = PATTERNS['chapter'].findall(plain(tex))

    cursor = 0
    chapters = []
    texts_in_chapter = None
    for text in texts:
        if cursor < len(chapter_start_strings):
            s = chapter_start_strings[cursor]
            if text.startswith(f'{s[0]}{s[1]}'):
                if texts_in_chapter:
                    chapters.append(texts_in_chapter)
                texts_in_chapter = []
                cursor += 1
        texts_in_chapter.append(text)
    chapters.append(texts_in_chapter)

    with open('chapters_and_pages.json', 'w') as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
