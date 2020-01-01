# docker run --rm -it -v $PWD:/work lp-python-mecab /bin/sh -c "python -u ruby.py"

import json
import re

import MeCab


def mecab(line):
    mt = MeCab.Tagger('-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd')
    columns = ['表層形', '品詞', '品詞細分類1', '品詞細分類2', '品詞細分類3', '活用型' ,'活用形', '原形', '読み', '発音']
    mecab_results = [dict(zip(columns, [result if result != '*' else None for result in re.split(',|\t', results + ',*,*,*,*,*')])) for results in mt.parse(line).splitlines() if results != 'EOS']

    s = 0
    ret = []
    for result in mecab_results:
        len_ = len(result['表層形'])
        ret.append({
            'el': (result['表層形'], result['品詞'], result['原形'] or '', result['読み'] or ''),
            'start': s,
            'end': s + len_
        })
        s += len_
    return ret


def main():
    text = input('読み替えをしたい文字列を含む文章を入力してください。\n対象の漢字部分は【】でくくってください。\n > ')
    ruby = input('その読みがなを入力してください。\n > ')
    # text = '【二、三日】雨が降り続いた'
    # ruby = 'にさん日、'

    ptn = re.compile(r'【(.+?)】')
    plain_text = ptn.sub(r'\1', text)
    mecab_results = mecab(plain_text)

    obj = ptn.search(text)
    kanji = obj.group(1)
    st = obj.start(0)
    en = st + len(kanji)

    morphemes = []
    for result in mecab_results:
        if len(set(range(st, en)) & set(range(result['start'], result['end']))) > 0:
            morphemes.append(result)
    offset_from_first_morpheme = st - morphemes[0]['start']

    js = json.dumps({
        'kanji': kanji,
        'ruby': ruby,
        'offset_from_first_morpheme': offset_from_first_morpheme,
        'morphemes': [m['el'] for m in morphemes],
    }, ensure_ascii=False, indent=4)
    js = re.sub(r'\[\n\s{12}"(.*)?"', r'["\1"', js)
    js = re.sub(r',\n\s{12}"(.*)?"', r', "\1"', js)
    js = re.sub(r'\n\s{8}]', ']', js)
    print('\n----------------------------')
    print(js)
    print('----------------------------')


if __name__ == '__main__':
    main()
