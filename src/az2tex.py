import json
import string

import jaconv
import regex as re

PATTERNS = {
    'about': re.compile(r'^-+$'),
    'teihon': re.compile(r'^底本[：]'),
    'midashi_l': [
        re.compile(r'(?:［＃(?:[１２３４５６７８９０一二三四五六七八九〇十]+)字下げ］)?(.*)［＃「(.*?)」は大見出し］'),
        re.compile(r'［＃大見出し］(.*?)［＃大見出し終わり］'),
    ],
    'midashi_m': [
        re.compile(r'(?:［＃(?:[１２３４５６７８９０一二三四五六七八九〇十]+)字下げ］)?(.*)［＃「(.*?)」は中見出し］'),
        re.compile(r'［＃中見出し］(.*?)［＃中見出し終わり］'),
    ],
    'midashi_m_multiline': re.compile(r'［＃ここから中見出し］(.*?)［＃ここで中見出し終わり］', flags=re.DOTALL),
    'rubies': [
        re.compile(r'｜(.+?)《(.+?)》'),
        re.compile(r'　(.+?)《(.+?)》　'),
        re.compile(r'([\p{Han}]+?)《(.+?)》'),
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
    'gothic': re.compile(r'(.+?)［＃「\1」は太字］'),
    'bouten': re.compile(r'(.+?)［＃.*?「\1」に傍点］'),
    'tatechuyoko': re.compile(r'(.+?)［＃「\1」は縦中横］'),
    'bouten_long': re.compile(r'［＃傍点］(.+?)［＃傍点終わり］'),
    'subscript': re.compile(r'([Ａ-Ｚａ-ｚΑ-Ωα-ωА-Яа-яA-Za-z0-9]+)(.+?)［＃「\2」は下付き小文字］'),
    'line': re.compile(r'✕　*?✕　*?✕'),
    'new_page': re.compile('［＃改(頁|ページ|段)］'),
    'frame_start': re.compile('［＃ここから罫囲み］'),
    'frame_end': re.compile('［＃ここで罫囲み終わり］'),
    'indent': re.compile(r'［＃(?:この行)?([１２３４５６７８９０一二三四五六七八九〇十]+)字下げ］'),
    'indent_bottom': re.compile(r'［＃地から([１２３４５６７８９０一二三四五六七八九〇十]+)字上げ］(.{1,13})$'),  # 13文字以上だと上にはみ出るので適用しない
    'indent_bottom_multiline': re.compile(r'［＃ここから地から([１２３４５６７８９０一二三四五六七八九〇十]+)字上げ］(.*?)［＃ここで字上げ終わり］', flags=re.DOTALL),
    'ignores': [
        re.compile(r'［＃ここから([１２３４５６７８９０一二三四五六七八九〇十]+)字下げ］'),  # 字下げは \\leftskip = 1zw でできるけど、違和感激しいので無視。
        re.compile(r'［＃ここで字下げ終わり］'),
        re.compile(r'［＃ここから([１２３４５６７８９０一二三四五六七八九〇十]+)字詰め］'),
        re.compile(r'［＃ここで字詰め終わり］'),
        re.compile(r'［＃(ルビの)?「.*?」は底本では「.*?」］'),
        re.compile(r'［＃(ルビの)?「.*?」はママ］'),
        re.compile(r'［＃地から([１２３４５６７８９０一二三四五六七八九〇十]+)字上げ］'),
        re.compile(r'^　'),
    ],
}

REPLACE_CHAR = str.maketrans({'×': '✕', '&': '\\&', '　': '\\　'})
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


def main():
    with open('template.tex', 'r', encoding='utf-8') as f:
        template = f.read()
    with open('novel.txt', 'r', encoding='shift_jis') as f:
        lines = f.readlines()
        aozora_lines = [sub_gaiji(line.strip(' \n\t\r')) for line in lines]

    head = aozora_lines[:50]
    body_lines = aozora_lines[get_first_line_index(head):get_last_line_index(aozora_lines[-50:])]

    for index, line in enumerate(body_lines):
        for pattern in PATTERNS['midashi_l']:
            if (obj := pattern.search(line)):
                body_lines[index] = f'\\part{{{obj.group(1)}}}'
        for pattern in PATTERNS['midashi_m']:
            if (obj := pattern.search(line)):
                body_lines[index] = f'\\chapter{{{obj.group(1)}}}'

    for index in range(len(body_lines)):
        body_lines[index] = PATTERNS['new_page'].sub(r'\\clearpage', body_lines[index])
        body_lines[index] = PATTERNS['line'].sub(r'\\hrulefill', body_lines[index])
        body_lines[index] = PATTERNS['kunoji'].sub(r'〳〵', body_lines[index])
        body_lines[index] = PATTERNS['kunoji_dakuten'].sub(r'〴〵', body_lines[index])
        body_lines[index] = PATTERNS['gothic'].sub(r'\\textgt{\1}', body_lines[index])
        body_lines[index] = PATTERNS['bouten'].sub(r'\\kenten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['bouten_long'].sub(r'\\kenten{\1}', body_lines[index])
        body_lines[index] = PATTERNS['subscript'].sub(r'$\1_{\2}$', body_lines[index])
        body_lines[index] = PATTERNS['frame_start'].sub(r'\\begin{oframed}', body_lines[index])
        body_lines[index] = PATTERNS['frame_end'].sub(r'\\end{oframed}', body_lines[index])
        body_lines[index] = PATTERNS['indent'].sub(r'\\noindent\\　', body_lines[index])  # 字下げは１字固定(普通の本より縦が短いので)以下同様
        body_lines[index] = PATTERNS['indent_bottom'].sub(r'\\noindent\\rightline{\2\\　}', body_lines[index])
        body_lines[index] = PATTERNS['tatechuyoko'].sub(
            lambda x: '\\tatechuyoko{' + jaconv.z2h(x.group(1), ascii=True, digit=True) + '}',
            body_lines[index]
        )
        body_lines[index] = PATTERNS['big'].sub(
            lambda x: '{\\fontsize{' + str(14 + int(x.group(6))) + '}{' + str((14 + int(x.group(6))) * 1.2) + '}\\selectfont ' + x.group(1) + '}',
            body_lines[index]
        )
        for pattern_ignore in PATTERNS['ignores']:
            body_lines[index] = pattern_ignore.sub('', body_lines[index])

    for index, line in enumerate(body_lines):
        body_lines[index] = ruby(line)

    body_text = '\n\n'.join(body_lines)
    body_text = PATTERNS['midashi_m_multiline'].sub(lambda x: '\\chapter{' + re.sub(r'\s+', ' ', x.group(1).strip()) + '}', body_text)
    body_text = PATTERNS['indent_bottom_multiline'].sub(lambda x: '\\begin{flushright}\n\n' + '\n'.join([l + '\\　\n' for l in x.group(2).split('\n') if len(l) > 0]) + '\n\\end{flushright}', body_text)
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
