import json
import string

import jaconv
import regex as re

N = r'[１２３４５６７８９０一二三四五六七八九〇十]+'
LATIN = r"[A-Za-zÀ-ÿ0-9#\-\;\&,. !\?'…―:\\]"

PATTERNS = {
    'about': re.compile(r'^-+$'),
    'teihon': re.compile(r'^底本[：]'),
    'midashi_l': [
        re.compile(r'(?:［＃(?:' + N + r')字下げ］)?(.*)［＃「(.*?)」は大見出し］'),
        re.compile(r'［＃大見出し］(.*?)［＃大見出し終わり］'),
    ],
    'midashi_m': [
        re.compile(r'(?:［＃(?:' + N + r')字下げ］)?(.*)［＃「.*?」は中見出し］(.*?)$'),  # ルビ付きの見出しに対応するため、\1を使用しない
        re.compile(r'［＃中見出し］(.*?)［＃中見出し終わり］(.*?)$'),
        re.compile(r'(.*)［＃「.*?」は同行大見出し］(.*?)$'),
    ],
    'midashi_m_multiline': re.compile(r'［＃(?:ここから中見出し|同行大見出し)］(.*?)［＃(?:ここで中見出し|同行大見出し)終わり］', flags=re.DOTALL),
    'rubies': [
        re.compile(r'｜(.+?)《(.+?)》'),
        re.compile(r'([\p{Han}ヶ〆]+?)《(.+?)》'),
        re.compile(r'([\p{Hiragana}]+?)《(.+?)》'),
        re.compile(r'([\p{Katakana}]+?)《(.+?)》'),
        re.compile(r'([Ａ-Ｚａ-ｚΑ-Ωα-ωА-Яа-я・]+?)《(.+?)》'),
        re.compile(r'(' + LATIN + r'+?)《(.+?)》'),
        re.compile(r'　(.{1,10}?)《(.+?)》　'),
    ],
    'remaining_ruby': re.compile(r'《.*?》'),
    'remaining_command': re.compile(r'［＃.*?］'),
    'kunoji': re.compile(r'／＼'),
    'kunoji_dakuten': re.compile(r'／″＼'),
    'big': re.compile(r'((.*?)(?:《.*》)?(.*?)(?:《.*》)?(.*?)(?:《.*》)?(.*?))［＃「\2\3\4\5」は([１２３４５６７８９０]+)段階大きな文字］'),
    'big_multiline': re.compile(r'［＃(?:ここから)?([１２３４５６７８９０]+)段階大きな文字］(.*?)［＃(?:ここで)?大きな文字終わり］', flags=re.DOTALL),
    'small_multiline': re.compile(r'［＃(?:ここから)?([１２３４５６７８９０]+)段階小さな文字］(.*?)［＃(?:ここで)?小さな文字終わり］', flags=re.DOTALL),
    'caption_multiline': re.compile(r'［＃キャプション］(.*?)［＃キャプション終わり］', flags=re.DOTALL),
    'gothic': re.compile(r'(.+?)［＃「\1」は太字］'),
    'gothic_multiline': re.compile(r'［＃ここから太字］(.*?)［＃ここで太字終わり］', flags=re.DOTALL),
    'lr_bousen': re.compile(r'(.+?)［＃.*?「\1」に傍線］［＃.*?「\1」の左に傍線］'),
    'r_bousen': re.compile(r'(.+?)［＃.*?「\1」に傍線］'),
    'l_bousen': re.compile(r'(.+?)［＃.*?「\1」の左に傍線］'),
    'bouten': re.compile(r'(.+?)［＃.*?「\1」に傍点］'),
    'marubouten': re.compile(r'(.+?)［＃.*?「\1」に丸傍点］'),
    'shiromarubouten': re.compile(r'(.+?)［＃.*?「\1」に白丸傍点］'),
    'tatechuyoko': re.compile(r'(.+?)［＃「\1」は縦中横］'),
    'warichu': re.compile(r'（［＃割り注］(.+?)［＃割り注終わり］）'),
    'bouten_long': re.compile(r'［＃傍点］(.+?)［＃傍点終わり］'),
    'subscript': re.compile(r'([Ａ-Ｚａ-ｚΑ-Ωα-ωА-Яа-яA-Za-z0-9]+)(.+?)［＃「\2」は下付き小文字］'),
    'line': re.compile(r'(^\s*?×　*?×　*?×*?$|^\s*?―{6,}\s*?$)'),
    'new_page': re.compile('［＃改(頁|ページ|段|丁)］'),
    'frame': re.compile(r'(.+?)［＃「\1」は罫囲み］'),
    'frame_multiline': re.compile(r'(?:［＃ここから' + N + r'字下げ］\s*?)?(?:\s*?［＃ここから' + N + r'字詰め］\s*?)?［＃ここから罫囲み］(.*?)［＃ここで罫囲み終わり］(?:\s*?［＃ここで字詰め終わり］)?(?:\s*?［＃ここで字下げ終わり］)?', flags=re.DOTALL),  # 罫囲みの字下げは無視
    'center_frame_multiline': re.compile(r'［＃ここから' + N + r'字下げ、横書き、中央揃え、罫囲み］(.*?)［＃ここで字下げ終わり］', flags=re.DOTALL),
    'indent': re.compile(r'［＃(?:この行|天から)?(' + N + r')字下げ］(.*)$'),
    'indent_hang_multiline': re.compile(r'［＃ここから(' + N + r')字下げ、折り返して(' + N + r')字下げ］(.*?)［＃ここで字下げ終わり］', flags=re.DOTALL),
    'indent_multiline': re.compile(r'［＃ここから(' + N + r')字下げ］(.*?)［＃ここで字下げ終わり］', flags=re.DOTALL),
    'indent_bottom': re.compile(r'［＃地から(' + N + r')字上げ］(.*)$'),
    'indent_bottom_multiline': re.compile(r'［＃ここから地から(' + N + r')字上げ］(.*?)［＃ここで字上げ終わり］', flags=re.DOTALL),
    'bottom': re.compile(r'［＃地付き］(.*)$'),
    'page_center_multiline': re.compile(r'［＃ページの左右中央］(.*?)\\clearpage', flags=re.DOTALL),
    'kunten': re.compile(r'［＃(一|二|レ)］'),
    'kunten_okuri': re.compile(r'［＃（(.*?)）］'),
    'accent': re.compile(r"〔(.*?)〕"),
    'fig': re.compile(r'［＃(.*?)（(.*?)、横([0-9]+?)×縦([0-9]+?)）入る］'),
    'frac': re.compile(r'(.*?)／(.*?)［＃「\1／\2」は分数］'),
    'latin_double_quote': re.compile(r'“(' + LATIN + r'+?)”'),
    'latin_double_quote_begin': re.compile(r'“(' + LATIN + r'+?)$'),
    'latin_double_quote_end': re.compile(r'^(' + LATIN + r'+?)”'),
    'many_spaces': re.compile(r'^　{3,}'),
    'many_symbols': re.compile(r'(…|？|！){13,}'),
    'ignores': [
        re.compile(r'［＃ここから(' + N + r')字詰め］'),
        re.compile(r'［＃ここから(' + N + r')字下げ］'),  # ２字下げ、４字下げ、字下げ終わり、みたいなのがあるので、余った真ん中を消す
        re.compile(r'［＃ここから改行天付き、折り返して(' + N + r')字下げ］'),  # ほとんど普通のレイアウトなので無視
        re.compile(r'［＃ここで字詰め終わり］'),
        re.compile(r'［＃ここで字下げ終わり］'),
        re.compile(r'［＃横組み］'),
        re.compile(r'［＃横組み終わり］'),
        re.compile(r'［＃(ルビの)?「.*?」は底本では「.*?」］'),
        re.compile(r'［＃(ルビの)?「.*?」はママ］'),
        re.compile(r'［＃地から(' + N + r')字上げ］'),
        re.compile(r'^　', flags=re.MULTILINE),
        re.compile(r'(〔|〕)'),
    ],
}

REPLACE_CHAR = str.maketrans({'&': '\\&', '　': '\\　', '懚': '隠', '滆': '溶', '㊞': '（印）'})
REPLACE_STR = {
    '※［＃感嘆符三つ、626-10］': '\\tatechuyoko{!!!}',
    '※［＃感嘆符三つ、77-3］': '\\tatechuyoko{!!!}',
    '\\3': '{Y\\llap{=}} 3',  # 痴人の愛
    '┌───┐\n\n│\\　\\　\\　│\n\n└───┘': '\\breakfbox{\\　\\　}',  # 夢野久作/ドグラ・マグラ
    '\\leftskip=1zw \n\nA     B     C     D   …………………………\n\n1111  1112  1121  1211…………………………\n\n \\leftskip=0zw': "\\begin{table}[htb]\\begin{tabular}{lllll}\nA & B & C & D & ...... \\\\\n1111 & 1112 & 1121 & 1211 & ......\n\\end{tabular}\\end{table}",  # 江戸川乱歩/二銭銅貨
}

with open('config.json', 'r') as f:
    config = json.load(f)

with open('consts.json', 'r') as f:
    consts = json.load(f)

# https://qiita.com/kichiki/items/bb65f7b57e09789a05ce
with open('jisx0213-2004-std.txt') as f:
    ms = (re.match(r'(\d-\w{4})\s+U\+(\w{4,5})', l) for l in f if l[0] != '#')
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
    m = re.search(r'(?:小書き片仮名|ローマ数字|感嘆符|アステリズム|二の字点).*\d-(\d{1,2})-(\d{1,2})', s)
    if m:
        key = f'3-{int(m[1])+32:2X}{int(m[2])+32:2X}'
        return gaiji_table.get(key, s)
    if s == '※［＃小書き平仮名ん、168-12］':
        return 'ん'
    if s == '※［＃「孛＋鳥」、105-11］':
        return '勃'  # 鵓はフォントにないので適当なのに変える
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


def accent(line):
    ret = line
    dic = {'a`': 'à', "a'": 'á', 'a^': 'â', 'a~': 'ã', 'a:': 'ä', 'a&': 'å', 'a_': 'ā', 'c,': 'ç', "c'": 'ć', 'c^': 'ĉ', 'd/': 'đ', 'e`': 'è', "e'": 'é', 'e^': 'ê', 'e:': 'ë', 'e_': 'ē', 'e~': 'ẽ', 'g^': 'ĝ', 'h^': 'ĥ', 'h/': 'ħ', 'i`': 'ì', "i'": 'í', 'i^': 'î', 'i:': 'ï', 'i_': 'ī', 'i/': 'ɨ', 'i~': 'ĩ', 'j^': 'ĵ', 'l/': 'ł', "l'": 'ĺ', "m'": 'ḿ', 'n`': 'ǹ', 'n~': 'ñ', "n'": 'ń', 'o`': 'ò', "o'": 'ó', 'o^': 'ô', 'o~': 'õ', 'o:': 'ö', 'o/': 'ø', 'o_': 'ō', "r'": 'ŕ', "s'": 'ś', 's,': 'ş', 's^': 'ŝ', 't,': 'ţ', 'u`': 'ù', "u'": 'ú', 'u^': 'û', 'u:': 'ü', 'u_': 'ū', 'u&': 'ů', 'u~': 'ũ', "y'": 'ý', 'y:': 'ÿ', "z'": 'ź', 'A`': 'À', "A'": 'Á', 'A^': 'Â', 'A~': 'Ã', 'A:': 'Ä', 'A&': 'Å', 'A_': 'Ā', 'C,': 'Ç', "C'": 'Ć', 'C^': 'Ĉ', 'D/': 'Đ', 'E`': 'È', "E'": 'É', 'E^': 'Ê', 'E:': 'Ë', 'E_': 'Ē', 'E~': 'Ẽ', 'G^': 'Ĝ', 'H^': 'Ĥ', 'I`': 'Ì', "I'": 'Í', 'I^': 'Î', 'I:': 'Ï', 'I_': 'Ī', 'I~': 'Ĩ', 'J^': 'Ĵ', 'L/': 'Ł', "L'": 'Ĺ', "M'": 'Ḿ', 'N`': 'Ǹ', 'N~': 'Ñ', "N'": 'Ń', 'O`': 'Ò', "O'": 'Ó', 'O^': 'Ô', 'O~': 'Õ', 'O:': 'Ö', 'O/': 'Ø', 'O_': 'Ō', "R'": 'Ŕ', "S'": 'Ś', 'S,': 'Ş', 'S^': 'Ŝ', 'T,': 'Ţ', 'U`': 'Ù', "U'": 'Ú', 'U^': 'Û', 'U:': 'Ü', 'U_': 'Ū', 'U&': 'Ů', 'U~': 'Ũ', "Y'": 'Ý', "Z'": 'Ź', 's&': 'ß', 'ae&': 'æ', 'AE&': 'Æ', 'oe&': 'œ', 'OE&': 'Œ'}
    for k, v in dic.items():
        ret = ret.replace(k, v)
    return ret


def big(size):
    return 14 + int(size) * 0.8


def small(size):
    return 14 - int(size) * 0.8


def image_width(w, h):
    # wが縦, hが横
    wmax, hmax = 3.6 * 0.8, 6.4 * 0.8  # 最大サイズ(インチ)
    winch, hinch = int(w) / 200, int(h) / 200  # 画像サイズをインチで補正
    wr, hr = winch / wmax , hinch / hmax  # 最大サイズに対する割合
    wscale, hscale = 1 / wr, 1 / hr  # 最大サイズになったときの倍率
    scale = min(wscale, hscale, 5.0)  # 最大サイズは5倍まで
    width = winch * scale
    return f'width={width:.2f}in'


# line: {\hfill \rightskip=1zw あああああ \par}, command: textgt のときに、下記を出力する
# {\hfill \rightskip=1zw \textgt{あああああ} \par}
def apply_only_text(line, command):
    ls = line.strip()
    if ls.startswith('{') and ls.endswith('}'):
        return re.sub(r'[\s{](?!\\)(\S*)[\s}]', r' \\' + command + r'{\1} ', ls)
    else:
        return '\\' + command + r'{' + ls + r'}'


# chapter_name / part_name からコマンドを消す
ht_ptn = re.compile(r'［＃.*］')


def ht(name):
    return ht_ptn.sub('', name)


def main():
    with open('template.tex', 'r', encoding='utf-8') as f:
        template = f.read()
    try:
        with open('novel.txt', 'r', encoding='shift_jis') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open('novel.txt', 'r', encoding='utf-8') as f:
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
                body_lines[index] = f'\\part{{{part_name}}}\n\\renewcommand{{\\headtext}}{{{ht(part_name)}}}'
        for pattern in PATTERNS['midashi_m']:
            if (obj := pattern.search(line)):
                show_part_name = ''
                if part_name != '':
                    show_part_name = part_name + '\\quad '
                chapter_name = obj.group(1)
                body_lines[index] = f'\\chapter{{{chapter_name}}}\n\\renewcommand{{\\headtext}}{{{show_part_name}{ht(chapter_name)}}}\n\n{obj.group(2)}'

    for index in range(len(body_lines)):
        body_lines[index] = PATTERNS['accent'].sub(lambda x: accent(x.group(1)), body_lines[index])
        body_lines[index] = PATTERNS['new_page'].sub(r'\\clearpage', body_lines[index])
        body_lines[index] = PATTERNS['line'].sub(r'\\hrulefill', body_lines[index])
        body_lines[index] = PATTERNS['kunoji'].sub(r'〳〵', body_lines[index])
        body_lines[index] = PATTERNS['kunoji_dakuten'].sub(r'〴〵', body_lines[index])
        body_lines[index] = PATTERNS['gothic'].sub(r'\\textgt{\1}', body_lines[index])
        body_lines[index] = PATTERNS['frame'].sub(r'\\breakfbox{\1}', body_lines[index])
        body_lines[index] = PATTERNS['lr_bousen'].sub(r'\\oline{\\uline{\1}}', body_lines[index])
        body_lines[index] = PATTERNS['r_bousen'].sub(r'\\oline{\1}', body_lines[index])
        body_lines[index] = PATTERNS['l_bousen'].sub(r'\\uline{\1}', body_lines[index])
        body_lines[index] = PATTERNS['bouten'].sub(r'\\kenten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['bouten_long'].sub(r'\\kenten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['marubouten'].sub(r'\\kentensubmarkintate{bullet}\\kenten[s]{\1}', body_lines[index])
        body_lines[index] = PATTERNS['shiromarubouten'].sub(r'\\kentensubmarkintate{Circle}\\kenten[s]{\1}', body_lines[index])
        body_lines[index] = PATTERNS['subscript'].sub(r'$\1_{\2}$', body_lines[index])
        body_lines[index] = PATTERNS['warichu'].sub(r'\\warichu{\1}', body_lines[index])
        body_lines[index] = PATTERNS['indent'].sub(r'\\leftskip=1zw\n\2\n\\leftskip=0zw', body_lines[index])  # 字下げは１字固定(普通の本より縦が短いので)以下同様
        body_lines[index] = PATTERNS['indent_bottom'].sub(r'{\\hfill \\rightskip=1zw \2 \\par}', body_lines[index])
        body_lines[index] = PATTERNS['bottom'].sub(r'{\\hfill \\rightskip=0zw \1 \\par}', body_lines[index])
        body_lines[index] = PATTERNS['kunten'].sub(r'\\kaeriten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['kunten_okuri'].sub(r'\\kokana{\1}{}', body_lines[index])
        body_lines[index] = PATTERNS['frac'].sub(r'$\\frac{\1}{\2}$', body_lines[index])
        body_lines[index] = PATTERNS['latin_double_quote'].sub(r'"\1"', body_lines[index])
        body_lines[index] = PATTERNS['latin_double_quote_begin'].sub(r'"\1', body_lines[index])
        body_lines[index] = PATTERNS['latin_double_quote_end'].sub(r'\1"', body_lines[index])
        body_lines[index] = PATTERNS['many_spaces'].sub(r'　　', body_lines[index])  # 行頭3つ以上の全角スペースは２つに減らす
        body_lines[index] = PATTERNS['many_symbols'].sub(lambda x: x.group()[:12], body_lines[index])  # 記号が並んでると改行されないので(ドグラ・マグラ用)
        body_lines[index] = PATTERNS['fig'].sub(
            lambda x: '\\clearpage\n\n（' + x.group(1) + '）\n\n\\vspace*{\\stretch{1}}\\begin{center}\\includegraphics[' + image_width(x.group(4), x.group(3)) + ']{' + x.group(2) + '}\\vspace*{\\stretch{1}}\\end{center}\n\n\\clearpage\n\n',
            body_lines[index]
        )
        body_lines[index] = PATTERNS['tatechuyoko'].sub(
            lambda x: '\\tatechuyoko{' + jaconv.z2h(x.group(1), ascii=True, digit=True) + '}',
            body_lines[index]
        )
        if '段階大きな文字］' in body_lines[index]:  # 時間がかかるのでコマンドが含まれない場合は何もしない
            body_lines[index] = PATTERNS['big'].sub(
                lambda x: '{\\fontsize{' + str(big(x.group(6))) + '}{' + str(big(x.group(6)) * 1.6) + '}\\selectfont ' + x.group(1) + '\\par}',
                body_lines[index]
            )
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
    body_text = PATTERNS['center_frame_multiline'].sub(
        r'\\begin{oframed}\n\\begin{center}\1\\end{center}\n\\end{oframed}',
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
        lambda x: '{\\fontsize{' + f'{big(x.group(1)):.2f}' + '}{' + f'{big(x.group(1)) * 1.6:.2f}' + '}\\selectfont ' + x.group(2) + '}',
        body_text
    )
    body_text = PATTERNS['small_multiline'].sub(
        lambda x: '{\\fontsize{' + f'{small(x.group(1)):.2f}' + '}{' + f'{small(x.group(1)) * 1.6:.2f}' + '}\\selectfont ' + x.group(2) + '}',
        body_text
    )
    body_text = PATTERNS['caption_multiline'].sub(
        lambda x: '{\\fontsize{' + f'{small(4):.2f}' + '}{' + f'{small(4) * 1.6:.2f}' + '}\\selectfont ' + x.group(1) + '}',
        body_text
    )
    body_text = PATTERNS['gothic_multiline'].sub(
        lambda x: '\n\n'.join([apply_only_text(l, 'textgt') for l in x.group(1).split('\n') if len(l) > 0]),
        body_text
    )

    for pattern_ignore in PATTERNS['ignores']:
        body_text = pattern_ignore.sub('', body_text)

    body_text = body_text.translate(REPLACE_CHAR)
    for k, v in REPLACE_STR.items():
        body_text = body_text.replace(k, v)

    for manual_chapter in config['manual_chapters']:
        body_text = re.sub(r'\n(' + manual_chapter + r')', r'\n\\clearpage % manual_chapter\n\n\1', body_text, 1)

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
