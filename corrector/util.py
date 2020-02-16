import _ctypes
import copy
import json
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


class LPJsonEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))

    class NoIndent(object):
        def __init__(self, value):
            self.value = value

        def __repr__(self):
            if not isinstance(self.value, list):
                return repr(self.value)
            else:
                reps = ('{{{}}}'.format(', '.join(('{!r}:{}'.format(k, v) for k, v in sorted(v.items())))) if isinstance(v, dict) else repr(v) for v in self.value)
                return '[' + ', '.join(reps) + ']'

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, LPJsonEncoder.NoIndent)
                else super().default(obj))

    @staticmethod
    def check_objs(obj):
        if len(str(obj)) < 40:
            return LPJsonEncoder.NoIndent(obj)
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = LPJsonEncoder.check_objs(v)
        elif isinstance(obj, list):
            for i,l in enumerate(obj):
                obj[i] = LPJsonEncoder.check_objs(l)
        return obj

    @staticmethod
    def di(obj_id):
        return _ctypes.PyObj_FromPtr(obj_id)

    def encode(self, obj):
        obj = LPJsonEncoder.check_objs(obj)
        format_spec = self.FORMAT_SPEC
        json_repr = super().encode(obj)
        for match in self.regex.finditer(json_repr):
            id = int(match.group(1))
            json_repr = json_repr.replace('"{}"'.format(format_spec.format(id)), repr(LPJsonEncoder.di(id)))
        json_repr = json_repr.replace("'", '"')
        return json_repr


def to_json(json_obj):
    return json.dumps(copy.deepcopy(json_obj), indent=4, cls=LPJsonEncoder)
