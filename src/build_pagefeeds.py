import glob
import json

import mutagen.mp3

with open('consts.json', 'r') as f:
    consts = json.load(f)

def main():
    voice_num = len(glob.glob('voices/*.mp3'))
    voices = []
    words_list = []
    for i in range(voice_num):
        voices.append(mutagen.mp3.MP3(f'voices/{i:0>5}.mp3').info.length)
        with open(f'marks/{i:0>5}.json', 'r') as f:
            marks = json.load(f)
            words_list.append([mark for mark in marks if mark['type'] == 'word'])

    words_tmp = [{
        'voice_id': voice_id,
        'voice_sec': voices[voice_id],
        'word_num_in_voice': len(words_in_voice),
        'word_id_in_voice': word_id_in_voice,
        'start_in_voice': word['time'] / 1000,
        'text': word['value'],
    } for voice_id, words_in_voice in enumerate(words_list) for word_id_in_voice, word in enumerate(words_in_voice)]

    words = []
    for i, word in enumerate(words_tmp):
        if word['word_id_in_voice'] == 0:
            start_this_voice = words[i - 1]['end'] + consts['voice_interval'] if i > 0 else consts['start_voice_interval']
        start = start_this_voice + word['start_in_voice']
        if word['word_id_in_voice'] + 1 == word['word_num_in_voice']:
            end = start_this_voice + word['voice_sec']
        else:
            end = start_this_voice + words_tmp[i + 1]['start_in_voice']
        words.append({
            'text': word['text'],
            'start': round(start, 3),
            'end': round(end, 3),
            'duration': round(end - start, 3),
        })

    with open(f'pages.json', 'r') as f:
        pages = json.load(f)

    pagefeeds = []
    cur = 0
    remain = ''
    for page in pages:
        page_words = []
        remain = f'{remain}{page}'
        while len(remain) > 0 and cur < len(words):
            w = words[cur]['text']
            if (loc := remain.find(w)) >= 0:
                remain = remain[loc + len(w):]
                page_words.append(words[cur])
                cur += 1
            else:
                break
        st = page_words[0]['start']
        en = page_words[len(page_words) - 1]['end']
        pagefeeds.append({
            'text': page,
            'start': st,
            'end': en,
            'words': page_words,
        })

    for i, pagefeed in enumerate(pagefeeds):
        pagefeed['next_start'] = pagefeeds[i + 1]['start'] if i + 1 < len(pagefeeds) else pagefeed['end']
        pagefeed['duration'] = pagefeed['next_start'] - pagefeed['start']
        pagefeeds[i] = pagefeed

    with open(f'pagefeeds.json', 'w') as f:
        json.dump(pagefeeds, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
