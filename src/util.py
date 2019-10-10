ssml_prefix = '''<?xml version="1.0"?>
<speak
    version="1.1"
    xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.w3.org/2001/10/synthesis http://www.w3.org/TR/speech-synthesis11/synthesis.xsd"
    xml:lang="ja-JP"><prosody rate="95%">
'''
ssml_postfix = '\n</prosody></speak>'


def number_to_kansuji(number):
    max_ = 4
    if number >= 10 ** max_:
        raise Exception()

    dic = {0: '', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九', 10: '十', 100: '百', 1000: '千'}
    bases = {10 ** i: number // 10 ** i % 10 for i in range(max_)}
    ret = ''
    for i in reversed(range(max_)):
        b = bases[10 ** i]
        if i == 0:  # 一桁目
            ret += f'{dic[b]}'
        elif b != 0:
            if b == 1:
                ret += dic[10 ** i]
            else:
                ret += f'{dic[b]}{dic[10 ** i]}'
    return ret


viseme_dic = []
viseme_dic.append({
    'a': 'あ', 'i': 'ゐ', 'u': 'う', '@': 'え', 'o': 'お', 'k': 'ん', 'B': 'っ', 'f': 'っ', 'J': 'っ', 'p': 'っ', 'r': 'っ', 's': 'っ', 't': 'っ',
})
viseme_dic.append({
    'Ba': 'あ', 'Bi': 'ゐ', 'B@': 'え', 'Bo': 'お',
    'fa': 'あ', 'fi': 'う', 'f@': 'え', 'fo': 'お',
    'ia': 'いあ', 'ii': 'いう', 'i@': 'いえ', 'io': 'いお',
    'Ja': 'あ', 'Ji': 'ゐ', 'J@': 'え', 'Jo': 'お',
    'ka': 'あ', 'ki': 'ゐ', 'k@': 'え', 'ko': 'お',
    'pa': 'あ', 'pi': 'ゐ', 'p@': 'え', 'po': 'お',
    'ra': 'あ', 'ri': 'い', 'r@': 'え', 'ro': 'お',
    'sa': 'あ', 'si': 'う', 's@': 'え', 'so': 'お',
    'ta': 'あ', 'ti': 'う', 't@': 'え', 'to': 'お',
    'ua': 'あ', 'ui': 'い', 'u@': 'え', 'uo': 'お',
})
viseme_dic.append({
    'kya': 'あ', 'kyi': 'う', 'kyo': 'お',
    'rya': 'あ', 'ryi': 'う', 'ryo': 'お',
    'tsu': 'う',
})


def viseme_to_hira(viseme, text):
    ret = ''
    cur = 0
    while cur < len(viseme):
        for i in reversed(range(3)):
            v = viseme[cur : cur + i + 1]
            if v in viseme_dic[i]:
                h = viseme_dic[i][v]
                cur += i + 1
                break
        else:
            raise Exception(f'変換できません: {viseme} {text}')
        ret += h
    return ret
