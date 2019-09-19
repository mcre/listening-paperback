import json
import string

import regex as re

dic = []
dic.append({
    'a': 'あ', 'i': 'ゐ', '@': 'え', 'o': 'お', 'k': 'ん', 'B': 'っ', 'f': 'っ', 'J': 'っ', 'p': 'っ', 'r': 'っ', 's': 'っ', 't': 'っ',
})
dic.append({
    'Ba': 'あ', 'Bi': 'ゐ', 'B@': 'え', 'Bo': 'お',
    'fa': 'あ', 'fi': 'う', 'f@': 'え', 'fo': 'お',
    'ia': 'あ', 'ii': 'う', 'i@': 'え', 'io': 'お',
    'Ja': 'あ', 'Ji': 'ゐ', 'J@': 'え', 'Jo': 'お',
    'ka': 'あ', 'ki': 'ゐ', 'k@': 'え', 'ko': 'お',
    'pa': 'あ', 'pi': 'ゐ', 'p@': 'え', 'po': 'お',
    'ra': 'あ', 'ri': 'い', 'r@': 'え', 'ro': 'お',
    'sa': 'あ', 'si': 'う', 's@': 'え', 'so': 'お',
    'ta': 'あ', 'ti': 'う', 't@': 'え', 'to': 'お',
    'ua': 'あ', 'ui': 'い', 'u@': 'え', 'uo': 'お',
})
dic.append({
    'kio': 'んお',
    'kya': 'あ', 'kyi': 'う', 'kyo': 'お',
    'rya': 'あ', 'ryi': 'う', 'ryo': 'お',
    'tsu': 'う',
})


class Template(string.Template):
    delimiter = '@'


def viseme_to_hira(viseme, text):
    ret = ''
    cur = 0
    while cur < len(viseme):
        for i in reversed(range(3)):
            v = viseme[cur : cur + i + 1]
            if v in dic[i]:
                h = dic[i][v]
                cur += i + 1
                break
        else:
            raise Exception(f'変換できません: {viseme} {text}')
        ret += h
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
    voice_id = -1
    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                for word in page['words']:
                    if voice_id != word['voice_id']:
                        voice_id = word['voice_id']
                        tex_text += f'\n\n\\tatechuyoko{{\\tiny {voice_id}}}'
                    t = word['text']
                    if ptn_kanji.search(t):
                        obj = ptn.match(t)
                        h = viseme_to_hira(word['viseme'], t)
                        en = obj.group(3)
                        tex_text += f'{obj.group(1)}\\ruby{{{obj.group(2)}}}{{{h}}}{en}\n'
                    else:
                        tex_text += t + '\n'

    out = Template(template).substitute({
        'text_color': consts['text_color'],
        'background_color': consts['background_color'],
        'body': tex_text,
    })
    with open('viseme.tex', 'w', encoding='utf-8') as f:
        f.write(out)


if __name__ == '__main__':
    main()
