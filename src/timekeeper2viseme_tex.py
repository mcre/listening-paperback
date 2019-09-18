import json
import string

import regex as re

dict2 = {
    'Ba': 'ゔぁ', 'Bi': 'ゔぃ', 'B@': 'ゔぇ', 'Bo': 'ゔぉ',
    'fa': 'ふぁ', 'fi': 'ふ', 'f@': 'ふぇ', 'fo': 'ふぉ',
    'ia': 'や', 'ii': 'ゆ', 'i@': 'いぇ', 'io': 'よ',
    'Ja': 'な', 'Ji': 'に', 'J@': 'ね', 'Jo': 'の',
    'ka': 'か', 'ki': 'き', 'k@': 'け', 'ko': 'こ',
    'pa': 'ま', 'pi': 'み', 'p@': 'め', 'po': 'も',
    'ra': 'ら', 'ri': 'り', 'r@': 'れ', 'ro': 'ろ',
    'sa': 'さ', 'si': 'し', 's@': 'せ', 'so': 'そ',
    'ta': 'ら', 'ti': 'り', 't@': 'れ', 'to': 'ろ',
    'ua': 'わ', 'ui': 'うぃ', 'u@': 'うぇ', 'uo': 'うぉ',
}

dict1 = {
    'a': 'あ', 'i': 'い', '@': 'え', 'o': 'お', 'k': 'ん', 'B': 'っ', 'f': 'っ', 'J': 'っ', 'p': 'っ', 'r': 'っ', 's': 'っ', 't': 'っ',
}


class Template(string.Template):
    delimiter = '@'


def viseme_to_hira(viseme):
    ret = ''
    cur = 0
    while cur < len(viseme):
        t1 = viseme[cur]
        t2 = viseme[cur : cur + 2]
        if t2 in dict2:
            ret += dict2[t2]
            cur += 2
        elif t1 in dict1:
            ret += dict1[t1]
            cur += 1
        else:
            raise Exception(f'変換できません: {viseme}', )
    return ret


def main():
    with open(f'timekeeper.json', 'r') as f:
        timekeeper = json.load(f)

    with open('consts.json', 'r') as f:
        consts = json.load(f)

    with open('template.tex', 'r', encoding='utf-8') as f:
        template = f.read()

    syms = '「」（）『』…―、。！？'
    ptn = re.compile(r'^([' + syms + r']*)(.*?)([' + syms + r']*)$')
    ptn_kanji = re.compile(r'[\p{Han}ヶ]')
    tex_text = ''
    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                for word in page['words']:
                    t = word['text']
                    if ptn_kanji.search(t):
                        obj = ptn.match(t)
                        h = viseme_to_hira(word['viseme'])
                        en = obj.group(3)
                        tex_text += f'{obj.group(1)}\\ruby{{{obj.group(2)}}}{{{h}}}{en}\n'
                    else:
                        tex_text += t + '\n'
                    if tex_text.endswith('。\n'):
                        tex_text += '\n\n'

    out = Template(template).substitute({
        'text_color': consts['text_color'],
        'background_color': consts['background_color'],
        'body': tex_text,
    })
    with open('viseme.tex', 'w', encoding='utf-8') as f:
        f.write(out)


if __name__ == '__main__':
    main()
