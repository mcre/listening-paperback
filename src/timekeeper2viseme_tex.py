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
    'ia': 'いあ', 'ii': 'いう', 'i@': 'いえ', 'io': 'いお',
    'Ja': 'あ', 'Ji': 'ゐ', 'J@': 'え', 'Jo': 'お',
    'ka': 'あ', 'ki': 'ゐ', 'k@': 'え', 'ko': 'お',
    'pa': 'あ', 'pi': 'ゐ', 'p@': 'え', 'po': 'お',
    'ra': 'あ', 'ri': 'い', 'r@': 'え', 'ro': 'お',
    'sa': 'あ', 'si': 'う', 's@': 'え', 'so': 'お',
    'ta': 'あ', 'ti': 'う', 't@': 'え', 'to': 'お',
    'ua': 'あ', 'ui': 'い', 'u@': 'え', 'uo': 'お',
})
dic.append({
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
                    if word['includes_kanji']:
                        obj = ptn.match(t)
                        v = word['viseme']
                        h = viseme_to_hira(v, t)
                        en = obj.group(3)
                        tex_text += f'{obj.group(1)}\\ruby{{{obj.group(2)}}}{{{h}}}{en} % {v}\n'
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
