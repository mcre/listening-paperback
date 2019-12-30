import string

import regex as re
import util as u


class Template(string.Template):
    delimiter = '@'


def main():
    consts = u.load_consts()
    timekeeper = u.load_timekeeper()

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
                        h = u.viseme_to_hira(v, t)
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
