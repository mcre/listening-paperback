import json
import os
import sys

import fitz
import PIL.Image
import PIL.ImageDraw
import PIL.ImageOps
import PIL.ImageEnhance

read_brightness = 0.25  # 既読文字の明るさ倍率(1以上で明るく、1以下で暗くなる)
adj = {'x0': 0.3, 'y0': 0, 'x1': -0.02, 'y1': 0.1}  # 文字の幅・高さの何％を増減させるか
ignore_width = [  # この幅に一致する場合は既読の対象にしない、小数点以下1桁の文字列で指定する
    '24.9',  # 傍点
    '10.4',  # ふりがな
    '10.1',  # 左上の章文字
]

with open('config.json', 'r') as f:
    config = json.load(f)

with open('consts.json', 'r') as f:
    consts = json.load(f)


def hex_to_rgb(hex):
    return tuple(int(hex[i: i + 2], 16) for i in range(0, 6, 2))


def cut_rects(rects):  # 「す」で検索すると「すすき」の「すす」が一つの枠で出現してしまうので、連続した場合は等分する
    ret = []
    for rect in rects:
        ratio = (rect.y1 - rect.y0) / (rect.x1 - rect.x0) / 0.693  # 1文字の場合はおよそ1になる
        if ratio < 1.5:  # 1文字
            ret.append(rect)
        elif ratio < 2.5:  # 2文字
            h = (rect.y1 - rect.y0) / 2
            for i in range(2):
                ret.append(fitz.fitz.Rect(rect.x0, rect.y0 + i * h, rect.x1, rect.y0 + (i + 1) * h))
        elif ratio < 3.5:  # 3文字
            h = (rect.y1 - rect.y0) / 3
            for i in range(3):
                ret.append(fitz.fitz.Rect(rect.x0, rect.y0 + i * h, rect.x1, rect.y0 + (i + 1) * h))
        else:
            print('4文字以上連続した場合の処理を作る必要がある')
            sys.exit(1)
    return ret


def conv(x):
    if x > 240:
        return 255
    if x == 0:
        return 255
    return x


def main():
    os.makedirs('animation_images', exist_ok=True)
    with open('timekeeper.json', 'r') as f:
        timekeeper = json.load(f)
    pdf = fitz.open('novel.pdf')

    for chapter in timekeeper['chapters']:
        for page in chapter['pages']:
            page_image = PIL.Image.open(page['image_path']).convert('RGBA')
            canvas = PIL.Image.new('RGBA', page_image.size)
            draw = PIL.ImageDraw.Draw(canvas)
            appear = {}
            pdf_page = pdf[page['serial_page_id']]
            w_scale = page_image.width / pdf_page.rect.x1
            h_scale = page_image.height / pdf_page.rect.y1
            for word in page['words']:
                w = word['skipped_text'] + word['text']
                if word['skipped_start_index_in_page'] < 0:  # ページ切り替えで前ページに余った文字を既読にするとずれるので、調整する
                    w = w[- word['skipped_start_index_in_page']:]
                for char in w:
                    rects = pdf_page.searchFor(char, hit_max=100)
                    rects = cut_rects(rects)
                    rects = [rect for rect in rects if f'{rect.x1 - rect.x0:.1f}' not in ignore_width]
                    if char in appear.keys():
                        appear[char] += 1
                    else:
                        appear[char] = 0
                    rect = rects[appear[char]]
                    cw = rect.x1 - rect.x0
                    ch = rect.y1 - rect.y0
                    col = hex_to_rgb(consts['background_color'])
                    draw.rectangle((
                        (rect.x0 + cw * adj['x0']) * w_scale, (rect.y0 + ch * adj['y0']) * h_scale, 
                        (rect.x1 + cw * adj['x1']) * w_scale, (rect.y1 + ch * adj['y1']) * h_scale
                    ), fill=(col[0], col[1], col[2], 255))
                square = PIL.ImageChops.darker(page_image, canvas)  # 既読の四角の部分のみを抜き出す
                alpha = PIL.ImageOps.invert(square.convert('L').point(conv))  # 文字部分のみのアルファチャンネルを作る(背景色(薄い色)と真っ黒(もと透過部分)を白に置換し,反転)
                target = page_image.convert('RGB')
                target.putalpha(alpha)  # 文字部分以外を透過したものができる
                dark_target = PIL.ImageEnhance.Brightness(target).enhance(read_brightness)  # 明るさ調整
                dark_page_image = PIL.Image.alpha_composite(page_image, dark_target)  # 暗い文字を重ねる
                dark_page_image.save(word['animation_image_path'])


if __name__ == '__main__':
    main()
