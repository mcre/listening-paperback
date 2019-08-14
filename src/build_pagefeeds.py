import glob
import json

import mutagen.mp3
import regex as re

PATTERNS = {
    'tag': re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>'''),
}

with open('consts.json', 'r') as f:
    consts = json.load(f)

def main():
    voice_num = len(glob.glob('voices/*.mp3'))
    voice_durations = []
    words_list = []
    for i in range(voice_num):
        voice_durations.append(mutagen.mp3.MP3(f'voices/{i:0>5}.mp3').info.length)
        with open(f'marks/{i:0>5}.json', 'r') as f:
            marks = json.load(f)
            words_list.append([mark for mark in marks if mark['type'] == 'word'])

    words_tmp = [{
        'voice_id': voice_id,
        'voice_sec': voice_durations[voice_id],
        'word_num_in_voice': len(words_in_voice),
        'word_id_in_voice': word_id_in_voice,
        'start_in_voice': word['time'] / 1000,
        'text': word['value'],
    } for voice_id, words_in_voice in enumerate(words_list) for word_id_in_voice, word in enumerate(words_in_voice)]

    words = []
    for word_id, word in enumerate(words_tmp):
        if word['word_id_in_voice'] == 0:
            start_this_voice = words[word_id - 1]['end'] + consts['voice_interval'] if word_id > 0 else consts['start_voice_interval']
        start = start_this_voice + word['start_in_voice']
        if word['word_id_in_voice'] + 1 == word['word_num_in_voice']:
            end = start_this_voice + word['voice_sec']
        else:
            end = start_this_voice + words_tmp[word_id + 1]['start_in_voice']
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
        index_in_page = - len(remain)
        remain = f'{remain}{page}'
        while len(remain) > 0 and cur < len(words):
            w = PATTERNS['tag'].sub('', words[cur]['text'])
            if (loc := remain.find(w)) >= 0:
                l = loc + len(w)
                words[cur]['skipped_text'] = remain[:loc]
                words[cur]['start_index_in_page'] = index_in_page + loc
                words[cur]['end_index_in_page'] = index_in_page + l
                words[cur]['skipped_start_index_in_page'] = index_in_page
                page_words.append(words[cur])
                remain = remain[l:]
                cur += 1
                index_in_page += l
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

    for page_id, pagefeed in enumerate(pagefeeds):
        pagefeed['next_page_start'] = pagefeeds[page_id + 1]['start'] if page_id + 1 < len(pagefeeds) else pagefeed['end']
        pagefeed['duration_to_next_page_start'] = round(pagefeed['next_page_start'] - pagefeed['start'], 3)
        pagefeeds[page_id] = pagefeed

    for pagefeed in pagefeeds:
        for word_id, word in enumerate(pagefeed['words']):
            word['next_word_start'] = pagefeed['words'][word_id + 1]['start'] if word_id + 1 < len(pagefeed['words']) else pagefeed['next_page_start']
            word['duration_to_next_word_start'] = round(word['next_word_start'] - word['start'], 3)
            word['next_word_duration'] = pagefeed['words'][word_id + 1]['duration'] if word_id + 1 < len(pagefeed['words']) else 0
            pagefeed['words'][word_id] = word

    with open(f'pagefeeds.json', 'w') as f:
        json.dump(pagefeeds, f, ensure_ascii=False, indent=2)
    with open(f'voice_durations.json', 'w') as f:
        json.dump(voice_durations, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
