import os
import subprocess

import util as u


def main():
    os.makedirs('voice_text_images', exist_ok=True)
    timekeeper = u.load_timekeeper()

    already = set()
    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                for word in page['words']:
                    text = word['original_text']
                    viseme = u.viseme_to_hira(word['viseme'], text)
                    tv = f"{text}{word['viseme']}"
                    if tv in already:  # textもvisemeも一致したものは再度作らない
                        continue
                    already.add(tv)
                    if word['includes_kanji'] and len(text) >= 2:  # 1文字を読み上げられてもなんだかわからないので2文字以上
                        fname = f"{chapter['chapter_id']:0>5}_{page['page_id']:0>5}_{word['word_id']:0>5}.png"
                        subprocess.call(f"convert -pointsize 144 -background none -font font.ttf label:'{text}'   voice_text_images/text_{fname}", shell=True)
                        subprocess.call(f"convert -pointsize 42  -background none -font font.ttf label:'{viseme}' voice_text_images/viseme_{fname}", shell=True)

    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for voice in chapter['voices'].values():
                subprocess.call(f"convert -pointsize 24 -background none -font font_gothic.ttf label:'voice_id: {voice['voice_id']:0>5}' voice_text_images/voice_{voice['voice_id']:0>5}.png", shell=True)


if __name__ == '__main__':
    main()
