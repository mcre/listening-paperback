import json
import os

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

import util as u

with open('config.json', 'r') as f:
    config = json.load(f)

with open('consts.json', 'r') as f:
    consts = json.load(f)

with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def hex_to_rgb(hex):
    return tuple(int(hex[i: i + 2], 16) for i in range(0, 6, 2))


def draw_text(im, text, loc=None, shadow=False):
    im_draw = PIL.ImageDraw.Draw(im)
    if loc is None or 'type' not in loc:
        return

    if 'size' in loc:
        font = PIL.ImageFont.truetype('./font.ttf', loc['size'])
        w, h = im_draw.textsize(text, font=font)

    if loc['type'] == 'x_center':  # {'type': 'x_center', 'y': 123, 'size': 10}
        x, y = (im.width - w) / 2, loc['y']
    elif loc['type'] == 'right_bottom':  # {'type': 'right_bottom', 'right': 123, 'bottom': 123, 'size': 10}
        x, y = loc['right'] - w, loc['bottom'] - h
    elif loc['type'] == 'in_rect':  # {'type': 'in_rect', 'rect': (x0, y0, x1, y1)}
        rw, rh = loc['rect'][2] - loc['rect'][0], loc['rect'][3] - loc['rect'][1]
        for size in range(300, 0, -5):
            font = PIL.ImageFont.truetype('./font.ttf', size)
            w, h = im_draw.textsize(text, font=font)
            if w <= rw and h <= rh:
                x, y = loc['rect'][0] + (rw - w) / 2, loc['rect'][1] + (rh - h) / 2
                break

    if shadow:
        n = 4
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                im_draw.text((x + i, y + j), text, align='center', font=font, fill=(64, 64, 64))
        n = 2
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                im_draw.text((x + i, y + j), text, align='center', font=font, fill=(255, 255, 255))
    im_draw.text((x, y), text, align='center', font=font, fill=hex_to_rgb(consts['text_color']))


def main():
    os.makedirs('cover_images', exist_ok=True)
    size = (1280, 720)
    for part in timekeeper['parts']:
        back = PIL.Image.open('cover.png')
        draw_text(back, '「聴く」名作文庫', loc={'type': 'x_center', 'y': 80, 'size': 100})
        draw_text(back, config['title'], loc={'type': 'in_rect', 'rect': (180, 220, size[0] - 180, 450)}, shadow=True)
        draw_text(back, f'第{u.number_to_kansuji(part["part_id"] + 1)}回', loc={'type': 'x_center', 'y': 480, 'size': 50})
        draw_text(back, config['author'], loc={'type': 'right_bottom', 'right': 1100, 'bottom': 600, 'size': 50})
        back.save(f'cover_images/{part["part_id"]:0>5}.png')

    loc = {'type': 'right_bottom', 'right': size[0] - 50, 'bottom': size[1] - 50, 'size': 100}
    bc = hex_to_rgb(consts['background_color'])
    back = PIL.Image.new('RGB', size, color=bc)
    draw_text(back, 'つづく', loc=loc)
    back.save(f'cover_images/next.png')
    back = PIL.Image.new('RGB', size, color=bc)
    draw_text(back, '終わり', loc=loc)
    back.save(f'cover_images/end.png')


if __name__ == '__main__':
    main()
