import os
import re
import sys

import jaconv
import MeCab

prefix =  '''<?xml version="1.0"?>
<speak
    version="1.1" 
    xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
    xml:lang="ja-JP"><prosody rate="95%">
'''
postfix = '\n</prosody></speak>'
ignore_list = ['\\documentclass', '\\usepackage', '\\setminchofont', '\\setgothicfont', '\\rubysetup', '\\ModifyHeading', '\\NewPageStyle', '\\pagestyle', '\\date', '\\begin', '\\maketitle', '\\end', '\\showoutput']
PATTERNS = {
    'ruby': re.compile(r'\\ruby{(.*?)}{(.*?)}'),
    'wakati_ruby': re.compile(r'(?:(?<=(?:\||\}))([^\|]*?)\\ruby{([^\{\}]*?)\|}{([^\{\}]*?)}|(?<=(?:\||\}))([^\|]*?)\\ruby{([^\{\}]*?[^\|])}{([^\{\}]*?)}([^\|]*?)(?=(?:\||\\)))'),
    'command': re.compile(r'\\(?!ruby).*?{(.*?)}'),
    'remove_marks': re.compile(r'[「」『』]'),
}

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
    return PATTERNS['command'].sub(r'\1', ret)

def plain(line):
    ret = plain_except_ruby(line)
    if ret is None:
        return None
    return PATTERNS['ruby'].sub(r'\1', ret)

def list_rubies(lines):
    rubies = {}
    for line in lines:
        pline = plain(line)
        if pline is None:
            continue
        ruby_line = plain_except_ruby(line)
        tmp = ['|']
        cur = 0
        for morpheme in wakati(pline):
            for char in morpheme:
                loc = ruby_line.find(char, cur) #ふりがなの読みの中にcharがあるとダメ
                if loc >= 0:
                    tmp.append(ruby_line[cur: loc + 1])
                    cur = loc + 1
                else:
                    print('break', loc, morpheme)
                    break
            tmp.append('|')
        for r in PATTERNS['wakati_ruby'].findall(''.join(tmp)):
            if r is not None:
                rp = lambda x: x.replace('|', '')
                if len(r[1]) > 0: # 後方なし
                    rubies[f'{r[0]}{r[1]}'] = f'{rp(r[0])}<sub alias="{jaconv.hira2kata(rp(r[2]))}">{rp(r[1])}</sub>'
                else: # 後方あり
                    rubies[f'{r[3]}{r[4]}{r[6]}'] = f'{rp(r[3])}<sub alias="{jaconv.hira2kata(rp(r[5]))}">{rp(r[4])}</sub>{rp(r[6])}'
    return rubies

def main():
    os.makedirs('ssml', exist_ok=True)

    with open('novel.tex', 'r') as fr:
        lines = fr.readlines()

    rubies = list_rubies(lines)

    clines = []
    for line in lines:
        pline = plain(line)
        if pline is None:
            continue
        replaced = '|' + '|'.join(wakati(pline)) + '|'
        for ruby in rubies.keys():
            replaced = replaced.replace('|' + ruby + '|', '|' + rubies[ruby] + '|')
        clines.append(replaced.replace('|', ''))

    for i, cline in enumerate(clines):
        with open(f'ssml/{i:0>5}.xml', 'w') as fw:
            cline = PATTERNS['remove_marks'].sub('', cline) # pollyのバグで、「<sub alias=\"カスケ\">加助"」等でmarksで余分なものが出るので記号系を置換しておく
            fw.write(prefix)
            fw.write(cline)
            fw.write(postfix)

if __name__ == '__main__':
    main()
