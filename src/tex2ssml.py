import os

import regex as re

prefix =  '''<?xml version="1.0"?>
<speak
    version="1.1" 
    xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
    xml:lang="ja-JP"><prosody rate="95%">
'''
postfix = '\n</prosody></speak>'
ignore_list = ['\\documentclass', '\\usepackage', '\\setminchofont', '\\setgothicfont', '\\rubysetup', '\\ModifyHeading', '\\NewPageStyle', '\\pagestyle', '\\date', '\\begin', '\\maketitle', '\\end']
PATTERNS = {
    'ruby': re.compile(r'\\ruby{(.*?)}{(.*?)}'),
    'command': re.compile(r'\\.*?{(.*?)}'),
}

def convert_line(line):
    ret = line.strip()
    if len(ret) <= 1:
        return None
    for ig in ignore_list:
        if ret.startswith(ig):
            return None
    ret = PATTERNS['ruby'].sub(r'\1', ret)
    ret = PATTERNS['command'].sub(r'\1', ret)
    return ret

def main():
    os.makedirs('ssml', exist_ok=True)
    with open('novel.tex', 'r') as fr:
        i = 0
        while line := fr.readline():
            cline = convert_line(line)
            if not cline:
                continue
            with open(f'ssml/{i:0>5}.xml', 'w') as fw:
                fw.write(prefix)
                fw.write(cline)
                fw.write(postfix)
            i += 1

if __name__ == '__main__':
    main()
