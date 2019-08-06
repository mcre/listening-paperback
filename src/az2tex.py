import json
import string

import regex as re

PATTERNS = {
    'about': re.compile(r'^-+$'),
    'teihon': re.compile(r'^底本[：]'),
    'chapters': [
        re.compile(r'(.*)［＃「(.*?)」は中見出し］'),
        re.compile(r'［＃中見出し］(.*?)［＃中見出し終わり］'),
    ],
    'ignores': [
        re.compile(r'［＃(?:この行)?.*?([１２３４５６７８９０一二三四五六七八九〇十]*)字下げ］'),
    ],
    'rubies': [
	    re.compile(r'｜(.+?)《(.+?)》'),
        re.compile(r'([\p{Han}]+?)《(.+?)》'),
	    re.compile(r'([\p{Hiragana}]+?)《(.+?)》'),
	    re.compile(r'([\p{Katakana}]+?)《(.+?)》'),
	    re.compile(r'([Ａ-Ｚａ-ｚΑ-Ωα-ωА-Яа-я・]+?)《(.+?)》'),
	    re.compile(r'([A-Za-z0-9#\-\;\&. ]+?)《(.+?)》'),
    ],
    'remaining_ruby': re.compile(r'《.*?》'),
    'bouten': re.compile(r'(.+?)［＃.*?「\1」に傍点］'),
}

with open('config.json', 'r') as f:
    config = json.load(f)

class Template(string.Template):
    delimiter = '@'

def read(filename, encoding=None):
    with open(filename, 'r', encoding=encoding) as f:
        return f.read()

def get_meta_data(lines):
    metas = []
    for line in lines:
        if PATTERNS['about'].fullmatch(line):
            break
        if line:
            metas.append(line)
    l = len(metas)
    ret = {}
    if l == 0:
        return ret
    ret['title'] = {'size': config.get('title_size', ''), 'data': metas[0]}
    if l == 2:
        ret['author'] = {'data': metas[1]}
    if l >= 3:
        ret['subtitle'] = {'data': metas[1]}
        ret['author'] = {'data': metas[2]}
    if l >= 4:
        ret['subauthor'] = {'data': metas[3]}
    return ret

def get_first_line_index(lines):
    count = 0
    for index, line in enumerate(lines):
        if count >= 2 and len(line.strip()) > 0:
            return index
        if PATTERNS['about'].fullmatch(line):
            count += 1
    return 0

def get_last_line_index(lines):
    matched = False
    for index, line in enumerate(reversed(lines)):
        if matched and len(line.strip()) > 0:
            return -index
        if PATTERNS['teihon'].match(line):
            matched = True
    return None

def ruby(line):
    ret = line
    for p in PATTERNS['rubies']:
        ret = p.sub(r'\\ruby{\1}{\2}', ret)
    if (obj := PATTERNS['remaining_ruby'].search(ret)):
        print(f'処理できていないルビあり: {obj.group()}')
    return ret

def bouten(line):
    return PATTERNS['bouten'].sub(r'\\kenten{\1}', line)

def main():
    with open('template.tex', 'r', encoding='utf-8') as f:
        template = f.read()
    with open('novel.txt', 'r', encoding='shift_jis') as f:
        aozora_lines = [line.strip() for line in f.readlines()]

    head = aozora_lines[:50]
    meta_data = get_meta_data(head)
    body_lines = aozora_lines[get_first_line_index(head):get_last_line_index(aozora_lines[-50:])]

    for index, line in enumerate(body_lines):
        for pattern_ignore in PATTERNS['ignores']:
            body_lines[index] = pattern_ignore.sub('', line)

    for index, line in enumerate(body_lines):
        for pattern_chapter in PATTERNS['chapters']:
            if (obj := pattern_chapter.search(line)):
                body_lines[index] = f'\\chapter{{{obj.group(1)}}}'

    for index, line in enumerate(body_lines):
        body_lines[index] = ruby(line)
    
    for index, line in enumerate(body_lines):
        body_lines[index] = bouten(line)

    bs = '\\'
    tex = Template(template).substitute({
        'meta_data': '\n'.join([f'\\{k}{{{bs + v["size"] + " " if v.get("size", False) else ""}{v["data"]}}}' for k, v in meta_data.items()]),
        'text_color': config['text_color'],
        'text_shadow_color': config['text_shadow_color'],
        'background_color': config['background_color'],
        'body': '\n\n'.join(body_lines),
    })
    with open('novel.tex', 'w', encoding='utf-8') as f:
        f.write(tex)

if __name__ == '__main__':
    main()
