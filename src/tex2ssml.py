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

PATTERNS = {
    'ruby': re.compile(r'\\ruby{(.+?)}{(.+?)}'),
    'zspace': re.compile(r'\\　'),
    'command': re.compile(r'\\(?!ruby)\S*?{(.*?)}'),
    'command_no_params': re.compile(r'\\(?!ruby)\S*?(?=[\s}])'),
    'dialogue': re.compile(r'「(.*?)」'),
    'think': re.compile(r'（(.*?)）'),
    'remove_marks': re.compile(r'[「」『』（）〔〕{}$_]'),
}
ignore_list = [
    '%', '\\documentclass', '\\usepackage', '\\setminchofont', '\\setgothicfont', '\\rubysetup',
    '\\ModifyHeading', '\\NewPageStyle', '\\pagestyle', '\\date', '\\begin', '\\maketitle',
    '\\end', '\\showoutput', '\\definecolor', '\\pagecolor', '\\color' ,'\\thiswatermark',
    '\\shadowoffset', '\\shadowcolor', '\\clearpage', '\\hrulefill', '\\cjkcategory',
    '\\newcommand', '\\renewcommand', '\\leftskip',
]

with open('config.json', 'r') as f:
    config = json.load(f)
with open('consts.json', 'r') as f:
    consts = json.load(f)


def plain_except_ruby(line):
    ret = line.strip()
    if len(ret) <= 1:
        return None
    for ig in ignore_list:
        if ret.startswith(ig):
            return None
    ret = PATTERNS['zspace'].sub(r'', ret)
    ret = PATTERNS['command'].sub(r'\1', ret)
    ret = PATTERNS['command_no_params'].sub('', ret)
    return ret


def mecab(line):
    mt = MeCab.Tagger('-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd')
    columns = ['表層形', '品詞', '品詞細分類1', '品詞細分類2', '品詞細分類3', '活用型' ,'活用形', '原形', '読み', '発音']
    mecab_results = [dict(zip(columns, [result if result != '*' else None for result in re.split(',|\t', results + ',*,*,*,*,*')])) for results in mt.parse(line).splitlines() if results != 'EOS']

    s = 0
    ret = []
    for result in mecab_results:
        len_ = len(result['表層形'])
        ret.append({
            'el': (result['表層形'], result['品詞'], result['原形'], result['読み']),
            'start': s,
            'end': s + len_
        })
        s += len_
    return ret


def split_ruby(filename, line):
    rubies = []
    for obj in PATTERNS['ruby'].finditer(line):
        offset = sum([len(ruby['command']) - len(ruby['kanji']) for ruby in rubies])  # rubyコマンドを消すと位置がずれるので
        rubies.append({
            'command': obj.group(0),
            'ssml_filename': filename,
            'kanji': obj.group(1),
            'ruby': obj.group(2),
            'start': obj.start(0) - offset,
            'end': obj.start(0) + len(obj.group(1)) - offset,
            'morphemes': [],
            'first_in_morpheme': False,
            'last_in_morpheme': False,
        })
    plain_line = PATTERNS['ruby'].sub(r'\1', line)
    mecab_results = mecab(plain_line)
    for ruby in rubies:
        for result in mecab_results:
            if len(set(range(ruby['start'], ruby['end'])) & set(range(result['start'], result['end']))) > 0:  # 出現箇所が重なる場所
                ruby['morphemes'].append(result)
        ruby['offset_from_first_morpheme'] = ruby['start'] - ruby['morphemes'][0]['start']

    for ruby in rubies:
        for result in mecab_results:
            if ruby['start'] == result['start']:
                ruby['first_in_morpheme'] = True
            if ruby['end'] == result['end']:
                ruby['last_in_morpheme'] = True
        if ruby['first_in_morpheme'] and ruby['last_in_morpheme']:
            ruby['ruby'] = jaconv.hira2kata(ruby['ruby'])
    return plain_line, rubies, mecab_results


def count_japanese(text):
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in 'FWA':
            count += 1
    return count


def main():
    os.makedirs('ssml', exist_ok=True)
    with open('novel.tex', 'r') as f:
        tex_ruby_lines = [plain_except_ruby(line) for line in f.readlines()]
    tex_ruby_lines = [line for line in tex_ruby_lines if line is not None]

    tex_ruby_lines = [{'fn': f'text{i:0>5}', 'line': line} for i, line in enumerate(tex_ruby_lines)]
    for i in range(0, config['estimated_max_num_of_parts']):
        tex_ruby_lines.append({'fn': f'part{i:0>5}', 'line': f'第{i + 1}回'})
    tex_ruby_lines.append({'fn': 'title', 'line': config['title']})
    tex_ruby_lines.append({'fn': 'channel', 'line': '聴く、名作文庫'})
    tex_ruby_lines.append({'fn': 'next', 'line': 'つづく'})
    tex_ruby_lines.append({'fn': 'end', 'line': '終わり'})
    tex_ruby_lines.append({'fn': 'please', 'line': 'チャンネル登録お願いします！'})

    rubies = []
    for sruby in config.get('special_rubies', []) + consts['avoid_polly_bugs']:
        rubies.append({
            'ssml_filename': '_sperial_rubies',
            'kanji': sruby['kanji'],
            'ruby': sruby['ruby'],
            'start': 0,
            'morphemes': [{'el': tuple(m)} for m in sruby['morphemes']],
            'offset_from_first_morpheme': sruby['offset_from_first_morpheme']
        })

    lines = []
    normal_rubies = []
    for line in tex_ruby_lines:
        p, r, m = split_ruby(line['fn'], line['line'])
        lines.append({'ssml_filename': line['fn'], 'plain_text': p, 'tex_ruby_text': line['line'], 'morphemes': m, 'ssml_rubies': []})
        normal_rubies.extend(r)
    normal_rubies = sorted(normal_rubies, key=lambda x: len(x['morphemes']), reverse=True)  # 形態素数が長いルビから適用する
    rubies.extend(normal_rubies)

    with open('rubies.json', 'w') as f:
        json.dump(rubies, f, ensure_ascii=False, indent=2)

    for line in lines:
        for morpheme_id, morpheme in enumerate(line['morphemes']):
            offset = 0
            ls = f'{line["ssml_filename"]}-{morpheme["start"]:0>5}'
            for ruby in rubies:
                rm = tuple([m['el'] for m in ruby['morphemes']])
                lm = tuple([m['el'] for m in line['morphemes'][morpheme_id: morpheme_id + len(rm)]])
                if rm == lm:
                    rs = f'{ruby["ssml_filename"]}-{ruby["start"] - ruby["offset_from_first_morpheme"]:0>5}'
                    if rs > ls:  # ルビ出現以前のものはスルー
                        continue
                    if offset > ruby['offset_from_first_morpheme']:
                        continue
                    st = morpheme['start'] + ruby['offset_from_first_morpheme']
                    en = st + len(ruby['kanji'])
                    line['ssml_rubies'].append({'ruby': ruby['ruby'], 'start': st, 'end': en})
                    offset = en  # breakしてもいいけど、同じ文節の後ろの方にふりがながある場合に対応したい。(ただしテスト不足)
        t = line['plain_text']
        for ruby in reversed(line['ssml_rubies']):
            st, en = ruby['start'], ruby['end']
            t = f'{t[:st]}<sub alias="{ruby["ruby"]}">{t[st:en]}</sub>{t[en:]}'
        t = PATTERNS['dialogue'].sub(r'<break strength="weak"/><prosody pitch="+10%">\1</prosody><break strength="weak"/>', t)
        t = PATTERNS['think'].sub(r'<break strength="weak"/>\1<break strength="weak"/>', t)
        t = PATTERNS['remove_marks'].sub('', t)  # pollyのバグで、「<sub alias=\"カスケ\">加助"」等でmarksで余分なものが出るので記号系を置換しておく

        line['ssml_ruby_text'] = t

    for line in lines:
        fn = line['ssml_filename']
        t = line['ssml_ruby_text']
        with open(f'ssml/{fn}.xml', 'w') as fw:
            fw.write(prefix)
            fw.write(t)
            fw.write(postfix)
        if count_japanese(t) == 0 and len(t) <= 10:
            print(f'日本語が存在しないか、英字含めて10文字以下のssmlがあります: {fn}.xml')
            raise Exception()


if __name__ == '__main__':
    main()
