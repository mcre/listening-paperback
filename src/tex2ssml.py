import json
import os
import re
import unicodedata

import jaconv
import MeCab

prefix = '''<?xml version="1.0"?>
<speak
    version="1.1"
    xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
    xml:lang="ja-JP"><prosody rate="95%">
'''
postfix = '\n</prosody></speak>'
ignore_list = [
    '%', '\\documentclass', '\\usepackage', '\\setminchofont', '\\setgothicfont', '\\rubysetup',
    '\\ModifyHeading', '\\NewPageStyle', '\\pagestyle', '\\date', '\\begin', '\\maketitle',
    '\\end', '\\showoutput', '\\definecolor', '\\pagecolor', '\\color' ,'\\thiswatermark',
    '\\shadowoffset', '\\shadowcolor', '\\clearpage'
]
PATTERNS = {
    'ruby': re.compile(r'\\ruby{(.*?)}{(.*?)}'),
    'wakati_ruby': re.compile(r'(?:(?<=(?:\||\}))([^\|]*?)\\ruby{([^\{\}]*?)\|}{([^\{\}]*?)}|(?<=(?:\||\}))([^\|]*?)\\ruby{([^\{\}]*?[^\|])}{([^\{\}]*?)}([^\|]*?)(?=(?:\||\\)))'),
    'zspace': re.compile(r'\\　'),
    'command': re.compile(r'\\(?!ruby)\S*?{(.*?)}'),
    'command_no_params': re.compile(r'\\(?!ruby)\S*?\s'),
    'dialogue': re.compile(r'「(.*?)」'),
    'think': re.compile(r'（(.*?)）'),
    'remove_marks': re.compile(r'[「」『』（）]'),
}


def count_japanese(text):
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in 'FWA':
            count += 1
    return count


def wakati(line):
    mecab = MeCab.Tagger('-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd -Owakati')
    return mecab.parse(line).strip().split(' ')


def plain_except_ruby(line):
    ret = line.strip()
    if len(ret) <= 1:
        return None
    for ig in ignore_list:
        if ret.startswith(ig):
            return None
    ret = PATTERNS['zspace'].sub(r' ', ret)
    ret = PATTERNS['command'].sub(r' \1 ', ret)
    ret = PATTERNS['command_no_params'].sub(' ', ret)
    return ret


def plain(line):
    ret = plain_except_ruby(line)
    if ret is None:
        return None
    return PATTERNS['ruby'].sub(r'\1', ret)


def rp(x):
    return x.replace('|', '')


def list_rubies(lines):
    rubies = []
    for l in lines:
        line = l['line']
        pline = plain(line)
        if pline is None:
            continue
        ruby_line = plain_except_ruby(line)
        tmp = ['|']
        cur = 0
        for morpheme in wakati(pline):
            for char in morpheme:
                loc = ruby_line.find(char, cur)  # ふりがなの読みの中にcharがあるとダメ
                if loc >= 0:
                    tmp.append(ruby_line[cur: loc + 1])
                    cur = loc + 1
                else:
                    print('break', loc, morpheme)
                    break
            tmp.append('|')
        for r in PATTERNS['wakati_ruby'].findall(''.join(tmp)):
            if r is not None:
                if len(r[1]) > 0:  # 後方なし
                    if len(r[0]) > 0:  # 前方あり
                        alias = rp(r[2])
                    else:  # 前方なし
                        alias = jaconv.hira2kata(rp(r[2]))
                    rubies.append({
                        'kanji': f'{r[0]}{r[1]}',
                        'ruby': f'{rp(r[0])}<sub alias="{alias}">{rp(r[1])}</sub>',
                    })
                else:  # 後方あり
                    rubies.append({
                        'kanji': f'{r[3]}{r[4]}{r[6]}',
                        'ruby': f'{rp(r[3])}<sub alias="{rp(r[5])}">{rp(r[4])}</sub>{rp(r[6])}',
                    })
    return sorted(rubies, key=lambda x: len(x['kanji']), reverse=True)


def main():
    os.makedirs('ssml', exist_ok=True)

    with open('config.json', 'r') as f:
        config = json.load(f)

    with open('consts.json', 'r') as f:
        consts = json.load(f)

    with open('novel.tex', 'r') as f:
        lines = [{'filename': f'num', 'line': line} for i, line in enumerate(f.readlines())]

    # linesにタイトルなどを追加
    for i in range(0, config['estimated_max_num_of_parts']):
        lines.append({'filename': f'part{i:0>5}', 'line': f'第{i + 1}回'})
    lines.append({'filename': 'title', 'line': config['title']})
    lines.append({'filename': 'channel', 'line': '聴く、名作文庫'})
    lines.append({'filename': 'next', 'line': 'つづく'})
    lines.append({'filename': 'end', 'line': '終わり'})
    lines.append({'filename': 'please', 'line': 'チャンネル登録お願いします！'})

    rubies = config.get('special_rubies', [])
    rubies.extend(consts['avoid_polly_bugs'])
    rubies.extend(list_rubies(lines))

    with open('rubies.json', 'w') as f:
        json.dump(rubies, f, ensure_ascii=False, indent=2)

    clines = []
    for line in lines:
        pline = plain(line['line'])
        if pline is None:
            continue
        replaced = '|' + '|'.join(wakati(pline)) + '|'
        for ruby in rubies:
            replaced = replaced.replace('|' + ruby['kanji'] + '|', '|' + ruby['ruby'] + '|')
        replaced = PATTERNS['dialogue'].sub(r'<break strength="weak"/><prosody pitch="+10%">\1</prosody><break strength="weak"/>', replaced)
        replaced = PATTERNS['think'].sub(r'<break strength="weak"/>\1<break strength="weak"/>', replaced)
        replaced = PATTERNS['remove_marks'].sub('', replaced)  # pollyのバグで、「<sub alias=\"カスケ\">加助"」等でmarksで余分なものが出るので記号系を置換しておく
        clines.append({'filename': line['filename'], 'line': replaced.replace('|', '')})

    for i, cline in enumerate(clines):
        fn = f'text{i:0>5}' if cline['filename'] == 'num' else cline['filename']
        with open(f'ssml/{fn}.xml', 'w') as fw:
            fw.write(prefix)
            fw.write(cline['line'])
            fw.write(postfix)
        if count_japanese(cline['line']) == 0:
            print(f'日本語が存在しないssmlがあります: {fn}.xml')
            raise Exception()


if __name__ == '__main__':
    main()
