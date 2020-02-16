import re
import subprocess

import japanize_kivy
import romkan

print(japanize_kivy)

TAG = re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>''')


def remove_tag(text):
    return TAG.sub('', text)


def kkc(romaji, num):
    ret = []
    hira = romkan.to_hiragana(romaji)
    kata = romkan.to_katakana(romaji)
    ret.append(hira)
    ret.append(kata)
    cmd = f'''docker run --rm lp-kkc sh -c 'echo "{hira}" {num} | kkc' '''
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = proc.stdout.split('\n')[2:-1]
    ptn = re.compile(r'(^[>\d\s]+:\s|/.*?>|<)')
    ret.extend([ptn.sub('', x) for x in result])
    return ret
