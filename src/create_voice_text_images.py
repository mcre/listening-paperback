import json
import os
import subprocess


def main():
    os.makedirs('voice_text_images', exist_ok=True)
    with open(f'timekeeper.json', 'r') as f:
        timekeeper = json.load(f)

    for part in timekeeper['parts']:
        for chapter in part['chapters']:
            for page in chapter['pages']:
                for word in page['words']:
                    text = word['original_text']
                    if word['includes_kanji'] and len(text) >= 2:  # 1文字を読み上げられてもなんだかわからないので2文字以上
                        path = word['animation_image_path'].replace('animation_images', 'voice_text_images')
                        subprocess.call(f"convert -pointsize 144 -background none -font font.ttf label:'{text}' {path}", shell=True)


if __name__ == '__main__':
    main()
