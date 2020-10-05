import difflib
import json
import os
import unicodedata

import jaconv
import MeCab
import regex as re
import util as u

MASU = '〼'
PATTERNS = {
    'ruby': re.compile(r'\\ruby{(.+?)}{(.+?)}'),
    'zspace': re.compile(r'\\　'),
    'masu': re.compile(MASU),
    'masu_sub': re.compile(MASU + r'</sub>'),
    'newline': re.compile(r'\\\\'),
    # \hoge{aaa} でaaaを読まないようなコマンド
    'ignore_command': re.compile(r'(?:\\fontsize{[0-9\.]+?}{[0-9\.]+?}\s*?\\selectfont|\\kentensubmarkintate{.+?}|\\stretch{.+?})|\\kaeriten{.+?}'),
    # aaaを読むコマンド
    'command': re.compile(r'\\(?!ruby)\S*?(?<rec>{((?:[^{}]+|(?&rec))*)})'),
    'command_no_params': re.compile(r'\\(?!ruby)\S*?(?=[\s}]|$)'),
    'chu_kakko_space': re.compile(r'{\s+(.*?)}'),
    'dialogue_1': re.compile(r'^「(.*?)」'),  # 文頭の発言の場合は高くする
    'dialogue_2': re.compile(r'(?!^)「(.{20,}?)」'),  # 文中の発言が連続すると音声がどんどん高くなるバグがあるっぽいので、長い文字の場合のみ高くする
    'dialogue_s': re.compile(r'(?!^)「(.{,19}?)」'),  # 短い文字は間隔だけ入れる、そもそもこういうのは発言じゃない場合も多いし。
    'think': re.compile(r'(?<!<sub alias=.*?>)(?:（(.*?)）|『(.*?)』)'),
    'remove_marks': re.compile(r'[「」〔〕{}$_&]'),
    'break_marks': re.compile(r'[『』（）]'),  # subを回避したthinkが詰まるのを回避する
    'double_odoriji': re.compile(r'([\p{Han}]{2})々々(?!</sub>)'),  # ルビ付きは一旦除外
    'time_break': re.compile(r'(?<![一ニ三四五六七八九])([―…])(?![一ニ三四五六七八九])'),  # 江戸川乱歩/怪人二十面相 の ニ―三人を変換するのを回避
    'tag': re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>'''),
}
gomi_list = ['{', '}']
ignore_list = [
    '%', '\\documentclass', '\\usepackage', '\\setminchofont', '\\setgothicfont', '\\rubysetup',
    '\\ModifyHeading', '\\NewPageStyle', '\\pagestyle', '\\date', '\\begin', '\\maketitle',
    '\\end', '\\showoutput', '\\definecolor', '\\pagecolor', '\\color' ,'\\thiswatermark',
    '\\shadowoffset', '\\shadowcolor', '\\clearpage', '\\hrulefill', '\\cjkcategory',
    '\\newcommand', '\\renewcommand', '\\leftskip',
    '\\vspace*{\\stretch{1}}\\begin{center}\\includegraphics',
]

config = u.load_config()
consts = u.load_consts()


def plain_except_ruby(line):
    ret = line.strip()
    if len(ret) < 1:
        return None
    for ig in ignore_list:
        if ret.startswith(ig):
            return None
    ret = PATTERNS['zspace'].sub(MASU, ret)
    ret = PATTERNS['newline'].sub(r'', ret)
    ret = PATTERNS['ignore_command'].sub(r'', ret)
    for i in range(3):  # 入れ子コマンドのために複数回実施しておく
        ret = PATTERNS['command'].sub(r'\2', ret)
    ret = PATTERNS['command_no_params'].sub('', ret)
    ret = PATTERNS['chu_kakko_space'].sub(r'{\1}', ret)  # { あいうえお} みたいなのが残ると変になるので{あいうえお}になおしとく
    ret = ret.strip()
    for gomi in gomi_list:  # コマンド置換した結果gomiだけ残るような場合は空にする
        if gomi == ret:
            return None
    if len(ret) < 1:
        return None
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
            'morphemes': [], 'first_in_morpheme': False, 'last_in_morpheme': False,
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
        if ruby['first_in_morpheme'] and (ruby['last_in_morpheme'] or ruby['ruby'][0] in consts['force_katakana_ruby_starts_with']):  # 独立した読み、あるいは、ひらがなだと読み間違うやつをカタカナにする
            ruby['ruby'] = jaconv.hira2kata(ruby['ruby'])
        # ルビの発生箇所の文字列表現
        ruby['pos'] = f'{ruby["ssml_filename"]}-{ruby["start"] - ruby["offset_from_first_morpheme"]:0>5}'
        # 1文字ルビは誤爆しやすいのでその箇所専用とする
        ruby['only_here'] = len(ruby['kanji']) == 1 and len(ruby['morphemes']) == 1 and len(ruby['morphemes'][0]['el'][0]) == 1 and ruby['morphemes'][0]['el'][3] != ''  # Mecabの読みがない場合は特殊な漢字なので拡散できるようにする
        # 同一漢字別読み用のキー
        ruby['ambiguous_key'] = f"{ruby['kanji']}|{str([m['el'] for m in ruby['morphemes']])}"
        # 重複削除用のキー
        ruby['dup_key'] = ruby['ambiguous_key'] + f"|{ruby['ruby']}"
        if ruby['only_here']:
            ruby['dup_key'] += '|' + ruby['pos']
    return plain_line, rubies, mecab_results


def count_japanese(text):
    count = 0
    for c in text:
        if unicodedata.east_asian_width(c) in 'FWA' or c in ('⁂'):
            count += 1
    return count


def load_special_ruby(special_ruby):
    return {
        'ssml_filename': '_sperial_rubies',
        'kanji': special_ruby['kanji'],
        'ruby': special_ruby['ruby'],
        'morphemes': [{'el': tuple(m.split('|'))} for m in special_ruby['morphemes']],
        'offset_from_first_morpheme': special_ruby['offset_from_first_morpheme'],
        'only_here': special_ruby.get('only_here', False),
        'pos': special_ruby.get('pos', '_sperial_rubies-00000'),
    }


def main():
    os.makedirs('ssml', exist_ok=True)
    with open('novel.tex', 'r') as f:
        tex_ruby_lines = [plain_except_ruby(line) for line in f.readlines()]
    tex_ruby_lines = [line for line in tex_ruby_lines if line is not None]

    tex_ruby_lines = [{'id': i, 'fn': f'text{i:0>5}', 'line': line} for i, line in enumerate(tex_ruby_lines)]

    text_rubies = []
    lines = []
    for line in tex_ruby_lines:
        p, r, m = split_ruby(line['fn'], line['line'])
        lines.append({'id': line['id'], 'ssml_filename': line['fn'], 'plain_text': p, 'tex_ruby_text': line['line'], 'morphemes': m, 'ssml_rubies': []})
        text_rubies.extend(r)

    # 同じ漢字で読みが違うものがある場合すべてonly_hereにする
    a_rubies = {}
    for ruby in text_rubies:
        a_key = ruby['ambiguous_key']
        if a_key not in a_rubies:
            a_rubies[a_key] = set()
        a_rubies[a_key].add(ruby['ruby'])
    ambiguous_keys = [key for key in a_rubies if len(a_rubies[key]) >= 2]

    for ruby in text_rubies:
        for ambiguous_key in ambiguous_keys:
            if ruby['ambiguous_key'] == ambiguous_key:
                ruby['only_here'] = True
                ruby['dup_key'] += '|' + ruby['pos']  # 重複削除で消えないようにする
                # print(f"読みが複数あるため only_here に設定: {ruby['kanji']} {ruby['ruby']}")
        for foh_ruby in config.get('force_only_here_rubies', []):
            if foh_ruby['kanji'] == ruby['kanji'] and foh_ruby['ruby'] == ruby['ruby']:
                ruby['only_here'] = True
                ruby['dup_key'] += '|' + ruby['pos']  # 重複削除で消えないようにする
                print(f"config の force_only_here_rubies 設定により only_here に設定: {ruby['kanji']} {ruby['ruby']}")

    # 重複削除 本の頭からの順にtext_rubiesに入っているはずなので、最初に登場したほうが残るはず
    dic = {}
    for ruby in text_rubies:
        if ruby['dup_key'] not in dic:
            dic[ruby['dup_key']] = ruby
    text_rubies = dic.values()

    # 無視ルビ除外(普通の感じにふりがなしてあることにより発音が変になる場合にそのふりがなを無視できる)
    ig_rubies = consts.get('ignore_rubies', [])
    if len(ig_rubies) > 0:
        new_text_rubies = []
        for ruby in text_rubies:
            ig = False
            for ig_ruby in ig_rubies:
                if ruby['kanji'] == ig_ruby['kanji'] and ruby['ruby'] == ig_ruby['ruby']:
                    ig = True
            if not ig:
                new_text_rubies.append(ruby)
        text_rubies = new_text_rubies

    rubies = []
    rubies.extend([load_special_ruby(x) for x in config.get('primary_special_rubies', []) + consts['primary_special_rubies']])  # 本文のルビより優先する
    rubies.extend(sorted(text_rubies, key=lambda x: len(x['morphemes']), reverse=True))  # 形態素数が長いルビから適用
    rubies.extend([load_special_ruby(x) for x in config.get('special_rubies', []) + consts['special_rubies']])

    # consts['use_mecab_yomi_rubies']の処理(これに該当するものはmecabの読みを有効にする(pollyが間違えやすい漢字を入れる: "方|名詞|方|ホウ" とか)
    for use_mecabu_yomi_ruby in consts['use_mecab_yomi_rubies']:
        el = tuple(use_mecabu_yomi_ruby.split('|'))
        rubies.append({
            'ssml_filename': '_sperial_rubies',
            'kanji': el[0],
            'ruby': el[3],
            'morphemes': [{'el': el}],
            'offset_from_first_morpheme': 0,
            'only_here': False,
            'pos': '_sperial_rubies-00000',
        })

    with open('rubies.json', 'w') as f:
        json.dump(rubies, f, ensure_ascii=False, indent=2)

    # 高速化のためにhash mapをつくる
    rubies_map = {}
    for ruby in rubies:
        key = ruby['morphemes'][0]['el'][0]
        if key not in rubies_map:
            rubies_map[key] = []
        rubies_map[key].append(ruby)

    for line_id, line in enumerate(lines):
        offset = 0  # lineのうちのこの文字まで処理済み(なので再処理しない)
        for morpheme_id, morpheme in enumerate(line['morphemes']):
            line_pos = f'{line["ssml_filename"]}-{morpheme["start"]:0>5}'
            key = morpheme['el'][0]
            for ruby in rubies_map.get(key, []):
                if ruby['only_here'] and ruby['pos'] != line_pos:
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
        t = PATTERNS['masu_sub'].sub(r'</sub>〼', t)  # 〼</sub> を </sub>〼 に置換(breakを外に出さないとエラーになるので)

        t = PATTERNS['dialogue_s'].sub(r'<break strength="weak"/>\1<break strength="weak"/>', t)
        ds = r'<break strength="weak"/><prosody pitch="+10%">\1</prosody><break strength="weak"/>'
        t = PATTERNS['dialogue_1'].sub(ds, t)
        t = PATTERNS['dialogue_2'].sub(ds, t)
        t = PATTERNS['think'].sub(r'<break strength="weak"/>\1\2<break strength="weak"/>', t)
        t = PATTERNS['remove_marks'].sub('', t)  # pollyのバグで、「<sub alias=\"カスケ\">加助"」等でmarksで余分なものが出るので記号系を置換しておく
        t = PATTERNS['break_marks'].sub('<break strength="weak"/>', t)
        t = PATTERNS['double_odoriji'].sub(r'\1<sub alias="\1">々々</sub>', t)
        t = PATTERNS['time_break'].sub(r'<break time="0.5s"/>\1', t)
        t = PATTERNS['masu'].sub(r'<break time="800ms"/>', t)
        line['ssml_ruby_text'] = t

    for line in lines:
        fn = line['ssml_filename']
        t = line['ssml_ruby_text']
        with open(f'ssml/{fn}.xml', 'w') as fw:
            fw.write(u.ssml_prefix)
            fw.write(t)
            fw.write(u.ssml_postfix)
        if count_japanese(t) == 0 and len(t) <= 1:
            print(f'日本語が存在しないか、英字含めて1文字以下のssmlがあります: {fn}.xml')
            raise Exception()

    # タイトルのssmlを出力(fast_checkに含めるためcreate_cover_images_and_ssmlではなくここで生成)
    with open(f'ssml/title.xml', 'w') as fw:
        fw.write(u.ssml_prefix)
        fw.write(config.get('title_yomi', config['title']))
        fw.write(u.ssml_postfix)

    # corrector用にテキストデータを整形
    def get_diff(line):
        bpath = f'ssml_before/{line["ssml_filename"]}.xml'
        if not os.path.exists(bpath):
            return '(履歴なし)'
        with open(bpath, 'r') as f:
            a = f.readlines()[7].strip()
        ret = ''
        b = line['ssml_ruby_text']
        for op in difflib.SequenceMatcher(None, a, b).get_opcodes():
            o = op[0]
            p = f'{op[3] / len(b) * 100:.0f}%'
            x = a[op[1]:op[2]].replace('</sub>', '').replace('<sub alias="', '').replace('">', '')
            y = b[op[3]:op[4]].replace('</sub>', '').replace('<sub alias="', '').replace('">', '')
            if o == 'replace':
                ret += f'置換({p}): {x} => {y}\n'
            if o == 'insert':
                if y:
                    ret += f'挿入({p}): {y}\n'
            if o == 'delete':
                if x:
                    ret += f'消去({p}): {x}\n'
        return ret

    with open('sentences.json', 'w') as f:
        json.dump([{
            'id': line['id'],
            'filename': line['ssml_filename'],
            'plain': line['plain_text'],
            'ssml': line['ssml_ruby_text'],
            'ssml_diff': get_diff(line),
            'morphemes': [{'start': m['start'], 'end': m['end'], 'el': '|'.join(m['el'])} for m in line['morphemes']],
        } for line in lines], f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    main()
