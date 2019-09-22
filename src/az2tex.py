import json
import string

import jaconv
import regex as re

N = r'[１２３４５６７８９０一二三四五六七八九〇十]+'

PATTERNS = {
    'about': re.compile(r'^-+$'),
    'teihon': re.compile(r'^底本[：]'),
    'midashi_l': [
        re.compile(r'(?:［＃(?:' + N + r')字下げ］)?(.*)［＃「(.*?)」は大見出し］'),
        re.compile(r'［＃大見出し］(.*?)［＃大見出し終わり］'),
    ],
    'midashi_m': [
        re.compile(r'(?:［＃(?:' + N + r')字下げ］)?(.*)［＃「(.*?)」は中見出し］'),
        re.compile(r'［＃中見出し］(.*?)［＃中見出し終わり］'),
    ],
    'midashi_m_multiline': re.compile(r'［＃ここから中見出し］(.*?)［＃ここで中見出し終わり］', flags=re.DOTALL),
    'rubies': [
        re.compile(r'｜(.+?)《(.+?)》'),
        re.compile(r'　(.+?)《(.+?)》　'),
        re.compile(r'([\p{Han}ヶ]+?)《(.+?)》'),
        re.compile(r'([\p{Hiragana}]+?)《(.+?)》'),
        re.compile(r'([\p{Katakana}]+?)《(.+?)》'),
        re.compile(r'([Ａ-Ｚａ-ｚΑ-Ωα-ωА-Яа-я・]+?)《(.+?)》'),
        re.compile(r'([A-Za-z0-9#\-\;\&. ]+?)《(.+?)》'),
    ],
    'remaining_ruby': re.compile(r'《.*?》'),
    'remaining_command': re.compile(r'［＃.*?］'),
    'kunoji': re.compile(r'／＼'),
    'kunoji_dakuten': re.compile(r'／″＼'),
    'big': re.compile(r'((.*?)(?:《.*》)?(.*?)(?:《.*》)?(.*?)(?:《.*》)?(.*?))［＃「\2\3\4\5」は([１２３４５６７８９０]+)段階大きな文字］'),
    'big_multiline': re.compile(r'［＃([１２３４５６７８９０]+)段階大きな文字］(.*?)［＃大きな文字終わり］', flags=re.DOTALL),
    'gothic': re.compile(r'(.+?)［＃「\1」は太字］'),
    'bouten': re.compile(r'(.+?)［＃.*?「\1」に傍点］'),
    'tatechuyoko': re.compile(r'(.+?)［＃「\1」は縦中横］'),
    'warichu': re.compile(r'（［＃割り注］(.+?)［＃割り注終わり］）'),
    'bouten_long': re.compile(r'［＃傍点］(.+?)［＃傍点終わり］'),
    'subscript': re.compile(r'([Ａ-Ｚａ-ｚΑ-Ωα-ωА-Яа-яA-Za-z0-9]+)(.+?)［＃「\2」は下付き小文字］'),
    'line': re.compile(r'(^\s*?×　*?×　*?×*?$|^\s*?―{6,}\s*?$)'),
    'new_page': re.compile('［＃改(頁|ページ|段)］'),
    'frame_multiline': re.compile(r'(?:［＃ここから' + N + r'字下げ］\s*?)?［＃ここから罫囲み］(.*?)［＃ここで罫囲み終わり］(?:\s*?［＃ここで字下げ終わり］)?', flags=re.DOTALL),  # 罫囲みの字下げは無視
    'indent': re.compile(r'［＃(?:この行)?(' + N + r')字下げ］(.*)$'),
    'indent_hang_multiline': re.compile(r'［＃ここから(' + N + r')字下げ、折り返して(' + N + r')字下げ］(.*?)［＃ここで字下げ終わり］', flags=re.DOTALL),
    'indent_multiline': re.compile(r'［＃ここから(' + N + r')字下げ］(.*?)［＃ここで字下げ終わり］', flags=re.DOTALL),
    'indent_bottom': re.compile(r'［＃地から(' + N + r')字上げ］(.*)$'),
    'indent_bottom_multiline': re.compile(r'［＃ここから地から(' + N + r')字上げ］(.*?)［＃ここで字上げ終わり］', flags=re.DOTALL),
    'page_center_multiline': re.compile(r'［＃ページの左右中央］(.*?)\\clearpage', flags=re.DOTALL),
    'kunten': re.compile(r'［＃(一|二|レ)］'),
    'accent': re.compile(r"([A-Za-z][`'\^\~:&,/_]|ae&|AE&|oe&|OE&)"),  # 本来は〔〕に囲んだ部分だけが適用されるはずだがめんどくさいので手抜き
    'many_spaces': re.compile(r'^　{3,}'),
    'many_symbols': re.compile(r'(…|？|！){13,}'),
    'ignores': [
        re.compile(r'［＃ここから(' + N + r')字詰め］'),
        re.compile(r'［＃ここで字詰め終わり］'),
        re.compile(r'［＃(ルビの)?「.*?」は底本では「.*?」］'),
        re.compile(r'［＃(ルビの)?「.*?」はママ］'),
        re.compile(r'［＃地から(' + N + r')字上げ］'),
        re.compile(r'^　'),
        re.compile(r'(〔|〕)'),
    ],
}

REPLACE_CHAR = str.maketrans({'&': '\\&', '　': '\\　', '懚': '隠'})
REPLACE_STR = {'※［＃感嘆符三つ、626-10］': '\\tatechuyoko{!!!}'}

with open('config.json', 'r') as f:
    config = json.load(f)

with open('consts.json', 'r') as f:
    consts = json.load(f)

# https://qiita.com/kichiki/items/bb65f7b57e09789a05ce
with open('jisx0213-2004-std.txt') as f:
    ms = (re.match(r'(\d-\w{4})\s+U\+(\w{4})', l) for l in f if l[0] != '#')
    gaiji_table = {m[1]: chr(int(m[2], 16)) for m in ms if m}


def get_gaiji(s):
    # ※［＃「弓＋椁のつくり」、第3水準1-84-22］
    m = re.search(r'第(\d)水準\d-(\d{1,2})-(\d{1,2})', s)
    if m:
        key = f'{m[1]}-{int(m[2])+32:2X}{int(m[3])+32:2X}'
        return gaiji_table.get(key, s)
    # ※［＃「身＋單」、U+8EC3、56-1］
    m = re.search(r'U\+(\w{4})', s)
    if m:
        return chr(int(m[1], 16))
    # ※［＃小書き片仮名ヒ、1-6-84］［＃ローマ数字1、1-13-21］
    m = re.search(r'(?:小書き片仮名|ローマ数字|感嘆符).*\d-(\d{1,2})-(\d{1,2})', s)
    if m:
        key = f'3-{int(m[1])+32:2X}{int(m[2])+32:2X}'
        return gaiji_table.get(key, s)
    if s == '※［＃小書き平仮名ん、168-12］':
        return 'ん'
    # unknown format
    return s


def sub_gaiji(text):
    return re.sub(r'※［＃.+?］', lambda m: get_gaiji(m[0]), text)


class Template(string.Template):
    delimiter = '@'


def get_first_line_index(lines):
    count = 0
    for index, line in enumerate(lines):
        if count >= 2 and len(line.strip()) > 0:
            return index
        if PATTERNS['about'].fullmatch(line):
            count += 1
    return 0


def get_last_line_index(lines):
    matched = False
    for index, line in enumerate(reversed(lines)):
        if matched and len(line.strip()) > 0:
            return -index
        if PATTERNS['teihon'].match(line):
            matched = True
    return None


def ruby(line):
    ret = line
    for p in PATTERNS['rubies']:
        ret = p.sub(r'\\ruby{\1}{\2}', ret)
    if (obj := PATTERNS['remaining_ruby'].search(ret)):
        print(f'処理できていないルビあり: {obj.group()}')
    return ret


def accent(char):
    dic = {'a`': 'à', "a'": 'á', 'a^': 'â', 'a~': 'ã', 'a:': 'ä', 'a&': 'å', 'a_': 'ā', 'c,': 'ç', "c'": 'ć', 'c^': 'ĉ', 'd/': 'đ', 'e`': 'è', "e'": 'é', 'e^': 'ê', 'e:': 'ë', 'e_': 'ē', 'e~': 'ẽ', 'g^': 'ĝ', 'h^': 'ĥ', 'h/': 'ħ', 'i`': 'ì', "i'": 'í', 'i^': 'î', 'i:': 'ï', 'i_': 'ī', 'i/': 'ɨ', 'i~': 'ĩ', 'j^': 'ĵ', 'l/': 'ł', "l'": 'ĺ', "m'": 'ḿ', 'n`': 'ǹ', 'n~': 'ñ', "n'": 'ń', 'o`': 'ò', "o'": 'ó', 'o^': 'ô', 'o~': 'õ', 'o:': 'ö', 'o/': 'ø', 'o_': 'ō', "r'": 'ŕ', "s'": 'ś', 's,': 'ş', 's^': 'ŝ', 't,': 'ţ', 'u`': 'ù', "u'": 'ú', 'u^': 'û', 'u:': 'ü', 'u_': 'ū', 'u&': 'ů', 'u~': 'ũ', "y'": 'ý', 'y:': 'ÿ', "z'": 'ź', 'A`': 'À', "A'": 'Á', 'A^': 'Â', 'A~': 'Ã', 'A:': 'Ä', 'A&': 'Å', 'A_': 'Ā', 'C,': 'Ç', "C'": 'Ć', 'C^': 'Ĉ', 'D/': 'Đ', 'E`': 'È', "E'": 'É', 'E^': 'Ê', 'E:': 'Ë', 'E_': 'Ē', 'E~': 'Ẽ', 'G^': 'Ĝ', 'H^': 'Ĥ', 'I`': 'Ì', "I'": 'Í', 'I^': 'Î', 'I:': 'Ï', 'I_': 'Ī', 'I~': 'Ĩ', 'J^': 'Ĵ', 'L/': 'Ł', "L'": 'Ĺ', "M'": 'Ḿ', 'N`': 'Ǹ', 'N~': 'Ñ', "N'": 'Ń', 'O`': 'Ò', "O'": 'Ó', 'O^': 'Ô', 'O~': 'Õ', 'O:': 'Ö', 'O/': 'Ø', 'O_': 'Ō', "R'": 'Ŕ', "S'": 'Ś', 'S,': 'Ş', 'S^': 'Ŝ', 'T,': 'Ţ', 'U`': 'Ù', "U'": 'Ú', 'U^': 'Û', 'U:': 'Ü', 'U_': 'Ū', 'U&': 'Ů', 'U~': 'Ũ', "Y'": 'Ý', "Z'": 'Ź', 's&': 'ß', 'ae&': 'æ', 'AE&': 'Æ', 'oe&': 'œ', 'OE&': 'Œ'}
    if char in dic.keys():
        return dic[char]
    return char


def big(size):
    return 14 + int(size) * 0.8


def main():
    with open('template.tex', 'r', encoding='utf-8') as f:
        template = f.read()
    with open('novel.txt', 'r', encoding='shift_jis') as f:
        lines = f.readlines()
        aozora_lines = [sub_gaiji(line.strip(' \n\t\r')) for line in lines]

    head = aozora_lines[:50]
    body_lines = aozora_lines[get_first_line_index(head):get_last_line_index(aozora_lines[-50:])]

    part_name = ''
    chapter_name = ''
    for index, line in enumerate(body_lines):
        for pattern in PATTERNS['midashi_l']:
            if (obj := pattern.search(line)):
                part_name = obj.group(1)
                chapter_name = ''
                body_lines[index] = f'\\part{{{part_name}}}\n\\renewcommand{{\\headtext}}{{{part_name}}}'
        for pattern in PATTERNS['midashi_m']:
            if (obj := pattern.search(line)):
                show_part_name = ''
                if part_name != '':
                    show_part_name = part_name + '\\quad '
                chapter_name = obj.group(1)
                body_lines[index] = f'\\chapter{{{chapter_name}}}\n\\renewcommand{{\\headtext}}{{{show_part_name}{chapter_name}}}'

    for index in range(len(body_lines)):
        body_lines[index] = PATTERNS['accent'].sub(lambda x: accent(x.group()), body_lines[index])
        body_lines[index] = PATTERNS['new_page'].sub(r'\\clearpage', body_lines[index])
        body_lines[index] = PATTERNS['line'].sub(r'\\hrulefill', body_lines[index])
        body_lines[index] = PATTERNS['kunoji'].sub(r'〳〵', body_lines[index])
        body_lines[index] = PATTERNS['kunoji_dakuten'].sub(r'〴〵', body_lines[index])
        body_lines[index] = PATTERNS['gothic'].sub(r'\\textgt{\1}', body_lines[index])
        body_lines[index] = PATTERNS['bouten'].sub(r'\\kenten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['bouten_long'].sub(r'\\kenten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['subscript'].sub(r'$\1_{\2}$', body_lines[index])
        body_lines[index] = PATTERNS['warichu'].sub(r'\\warichu{\1}', body_lines[index])
        body_lines[index] = PATTERNS['indent'].sub(r'\\leftskip=1zw\n\2\n\\leftskip=0zw', body_lines[index])  # 字下げは１字固定(普通の本より縦が短いので)以下同様
        body_lines[index] = PATTERNS['indent_bottom'].sub(r'{\\hfill \\rightskip=1zw \2 \\par}', body_lines[index])
        body_lines[index] = PATTERNS['kunten'].sub(r'\\kaeriten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['many_spaces'].sub(r'　　', body_lines[index])  # 行頭3つ以上の全角スペースは２つに減らす
        body_lines[index] = PATTERNS['many_symbols'].sub(lambda x: x.group()[:12], body_lines[index])  # 記号が並んでると改行されないので(ドグラ・マグラ用)
        body_lines[index] = PATTERNS['tatechuyoko'].sub(
            lambda x: '\\tatechuyoko{' + jaconv.z2h(x.group(1), ascii=True, digit=True) + '}',
            body_lines[index]
        )
        if '段階大きな文字］' in body_lines[index]:  # 時間がかかるのでコマンドが含まれない場合は何もしない
            body_lines[index] = PATTERNS['big'].sub(
                lambda x: '{\\fontsize{' + str(big(x.group(6))) + '}{' + str(big(x.group(6)) * 1.6) + '}\\selectfont ' + x.group(1) + '\\par}',
                body_lines[index]
            )
        for pattern_ignore in PATTERNS['ignores']:
            body_lines[index] = pattern_ignore.sub('', body_lines[index])

    for index, line in enumerate(body_lines):
        body_lines[index] = ruby(line)

    body_text = '\n\n'.join(body_lines)
    body_text = PATTERNS['midashi_m_multiline'].sub(
        lambda x: '\\chapter{' + re.sub(r'\s+', ' ', x.group(1).strip()) + '}',
        body_text
    )
    body_text = PATTERNS['frame_multiline'].sub(  # 複数行字下げより前に置く
        r'\\begin{oframed}\n\1\n\\end{oframed}',
        body_text
    )
    body_text = PATTERNS['indent_hang_multiline'].sub(
        lambda x: '\\leftskip=1zw\n\n' + '\n\n'.join([f'\\hangindent={int(x.group(2)) - 1}zw ' + l for l in x.group(3).split('\n') if len(l) > 0]) + '\n\n\\leftskip=0zw',
        body_text
    )
    body_text = PATTERNS['indent_multiline'].sub(
        r'\\leftskip=1zw \2 \\leftskip=0zw',
        body_text
    )
    body_text = PATTERNS['indent_bottom_multiline'].sub(
        lambda x: '{\\raggedleft \\rightskip=1zw\n' + '\\\\\n'.join([l for l in x.group(2).split('\n') if len(l) > 0]) + '\\\\\n}',
        body_text
    )
    body_text = PATTERNS['page_center_multiline'].sub(
        r'\n\\vspace*{\\stretch{1}}\n\1\n\\vspace{\stretch{1}}\\clearpage\n',
        body_text
    )
    body_text = PATTERNS['big_multiline'].sub(
        lambda x: '{\\fontsize{' + str(big(x.group(1))) + '}{' + str(big(x.group(1)) * 1.6) + '}\\selectfont ' + x.group(2) + '}',
        body_text
    )

    body_text = body_text.translate(REPLACE_CHAR)
    for k, v in REPLACE_STR.items():
        body_text = body_text.replace(k, v)

    tex = Template(template).substitute({
        'text_color': consts['text_color'],
        'background_color': consts['background_color'],
        'body': body_text,
    })
    with open('novel.tex', 'w', encoding='utf-8') as f:
        f.write(tex)

    for cmd in PATTERNS['remaining_command'].findall(tex):
        print('処理できていないコマンドあり: ' + cmd)


if __name__ == '__main__':
    main()
