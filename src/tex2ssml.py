import datetime as dt
import json
import os
import re
import unicodedata

import jaconv
import MeCab

import util as u

PATTERNS = {
    'ruby': re.compile(r'\\ruby{(.+?)}{(.+?)}'),
    'zspace': re.compile(r'\\　'),
    'command': re.compile(r'\\(?!ruby)\S*?{(.*?)}'),
    'command_no_params': re.compile(r'\\(?!ruby)\S*?(?=[\s}])'),
    'dialogue': re.compile(r'「(.*?)」'),
    'think': re.compile(r'（(.*?)）'),
    'remove_marks': re.compile(r'[「」『』（）〔〕{}$_]'),
    'double_odoriji': re.compile(r'([^>]{2})々々'),  # ルビ付きは一旦除外
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
    mt = MeCab.Tagger('-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd --node-format=%m,%M,%H\\n')
    columns = ['表層形', '空白付表層形', '品詞', '品詞細分類1', '品詞細分類2', '品詞細分類3', '活用型' ,'活用形', '原形', '読み', '発音']
    mecab_results = [dict(zip(columns, [result if result != '*' else '' for result in (results + ',*,*,*,*,*').split(',')])) for results in mt.parse(line).splitlines() if results != 'EOS']

    s = 0
    ret = []
    for result in mecab_results:
        len_ = len(result['空白付表層形'])
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
        # ルビの発生箇所の文字列表現
        ruby['pos'] = f'{ruby["ssml_filename"]}-{ruby["start"] - ruby["offset_from_first_morpheme"]:0>5}'
        # 1文字ルビは誤爆しやすいのでその箇所専用とする
        ruby['one_char'] = len(ruby['kanji']) == 1 and len(ruby['morphemes']) == 1 and len(ruby['morphemes'][0]['el'][0]) == 1
        # 重複削除用のキー
        ruby['dupkey'] = f"{ruby['kanji']}|{ruby['ruby']}|{str([m['el'] for m in ruby['morphemes']])}"
        if ruby['one_char']:
            ruby['dupkey'] += '|' + ruby['pos']
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

    rubies = []
    for sruby in config.get('special_rubies', []) + consts['special_rubies']:
        rubies.append({
            'ssml_filename': '_sperial_rubies',
            'kanji': sruby['kanji'],
            'ruby': sruby['ruby'],
            'start': 0,
            'morphemes': [{'el': tuple(m)} for m in sruby['morphemes']],
            'offset_from_first_morpheme': sruby['offset_from_first_morpheme'],
            'one_char': False,
            'pos': '_sperial_rubies-00000',
        })

    lines = []
    normal_rubies = []
    for line in tex_ruby_lines:
        p, r, m = split_ruby(line['fn'], line['line'])
        lines.append({'ssml_filename': line['fn'], 'plain_text': p, 'tex_ruby_text': line['line'], 'morphemes': m, 'ssml_rubies': []})
        normal_rubies.extend(r)
    # 重複削除 本の頭からの順にnormal_rubiesに入っているはずなので、最初に登場したほうが残るはず
    dic = {}
    for ruby in normal_rubies:
        if ruby['dupkey'] not in dic:
            dic[ruby['dupkey']] = ruby
    normal_rubies = dic.values()
    # 形態素数が長いルビから適用したい
    normal_rubies = sorted(normal_rubies, key=lambda x: len(x['morphemes']), reverse=True)
    rubies.extend(normal_rubies)

    with open('rubies.json', 'w') as f:
        json.dump(rubies, f, ensure_ascii=False, indent=2)

    for line_id, line in enumerate(lines):
        if line_id % 100 == 0:
            print(f'{dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} : {line_id} / {len(lines)}')
        offset = 0  # lineのうちのこの文字まで処理済み(なので再処理しない)
        for morpheme_id, morpheme in enumerate(line['morphemes']):
            line_pos = f'{line["ssml_filename"]}-{morpheme["start"]:0>5}'
            for ruby in rubies:
                if ruby['one_char'] and ruby['pos'] != line_pos:  # 1文字で形態素が1個の場合は誤爆しやすいので同一箇所のみ処理
                    continue
                if ruby['pos'] > line_pos:  # ルビ出現以前のものはスルー
                    continue
                rm = tuple([m['el'] for m in ruby['morphemes']])
                lm = tuple([m['el'] for m in line['morphemes'][morpheme_id: morpheme_id + len(rm)]])
                if rm == lm:
                    st = morpheme['start'] + ruby['offset_from_first_morpheme']
                    en = st + len(ruby['kanji'])
                    if st >= offset:
                        line['ssml_rubies'].append({'ruby': ruby['ruby'], 'start': st, 'end': en})
                        offset = en
        t = line['plain_text']
        for ruby in reversed(line['ssml_rubies']):
            st, en = ruby['start'], ruby['end']
            t = f'{t[:st]}<sub alias="{ruby["ruby"]}">{t[st:en]}</sub>{t[en:]}'
        t = PATTERNS['dialogue'].sub(r'<break strength="weak"/><prosody pitch="+10%">\1</prosody><break strength="weak"/>', t)
        t = PATTERNS['think'].sub(r'<break strength="weak"/>\1<break strength="weak"/>', t)
        t = PATTERNS['remove_marks'].sub('', t)  # pollyのバグで、「<sub alias=\"カスケ\">加助"」等でmarksで余分なものが出るので記号系を置換しておく
        t = PATTERNS['double_odoriji'].sub(r'\1<sub alias="\1">々々</sub>', t)
        line['ssml_ruby_text'] = t

    for line in lines:
        fn = line['ssml_filename']
        t = line['ssml_ruby_text']
        with open(f'ssml/{fn}.xml', 'w') as fw:
            fw.write(u.ssml_prefix)
            fw.write(t)
            fw.write(u.ssml_postfix)
        if count_japanese(t) == 0 and len(t) <= 10:
            print(f'日本語が存在しないか、英字含めて10文字以下のssmlがあります: {fn}.xml')
            raise Exception()


if __name__ == '__main__':
    main()
