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
    r = romaji.replace(',', '、').replace('.', '。')
    hira = romkan.to_hiragana(r)
    kata = romkan.to_katakana(r)
    ret.append(hira)
    ret.append(kata)
    cmd = f'''docker run --rm lp-kkc sh -c 'echo "{hira}" {num} | kkc' '''
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = proc.stdout.split('\n')[2:-1]
    ptn = re.compile(r'(^[>\d\s]+:\s|/.*?>|<)')
    ret.extend([ptn.sub('', x) for x in result])
    return ret


class Batch:
    def __init__(self, command):
        self.command = command
        self.process = None

    def start(self):
        self.process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = self.process.stdout.readline()
            if line:
                yield line.decode('utf-8')
            if not line and self.process.poll() is not None:
                break

    def terminate(self):
        if self.process:
            print('<terminate call>')
            self.process.terminate()
