import os

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import util as u

config = u.load_config()
consts = u.load_consts()
timekeeper = u.load_timekeeper()


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
    im_draw.text((x, y), text, align='center', font=font, fill=u.hex_to_rgb(consts['text_color']))


def main():
    os.makedirs('cover_images', exist_ok=True)
    size = (1280, 720)

    for part in timekeeper['parts']:
        back = PIL.Image.open('cover.png')
        draw_text(back, '「聴く」名作文庫', loc={'type': 'x_center', 'y': 80, 'size': 100})
        draw_text(back, config['title'], loc={'type': 'in_rect', 'rect': (180, 220, size[0] - 180, 450)}, shadow=True)
        if len(timekeeper['parts']) > 1:  # 1パートしかない場合は第1回と言わない
            draw_text(back, f'第{u.number_to_kansuji(part["part_id"] + 1)}回', loc={'type': 'x_center', 'y': 450, 'size': 95})
        draw_text(back, config['author'], loc={'type': 'right_bottom', 'right': 1100, 'bottom': 600, 'size': 50})
        back.save(f'cover_images/{part["part_id"]:0>5}.png')

    loc = {'type': 'right_bottom', 'right': size[0] - 50, 'bottom': size[1] - 50, 'size': 100}
    bc = u.hex_to_rgb(consts['background_color'])
    back = PIL.Image.new('RGB', size, color=bc)
    draw_text(back, 'つづく', loc=loc)
    back.save(f'cover_images/next.png')
    back = PIL.Image.new('RGB', size, color=bc)
    draw_text(back, '終わり', loc=loc)
    back.save(f'cover_images/end.png')

    ssml_texts = []
    for part in timekeeper['parts']:
        ssml_texts.append({'fn': f'part{part["part_id"]:0>5}', 'text': f'第{part["part_id"] + 1}回'})
    ssml_texts.append({'fn': 'title', 'text': config.get('title_yomi', config['title'])})
    ssml_texts.append({'fn': 'channel', 'text': '聴く、名作文庫'})
    ssml_texts.append({'fn': 'next', 'text': 'つづく'})
    ssml_texts.append({'fn': 'end', 'text': '終わり'})
    ssml_texts.append({'fn': 'please', 'text': 'チャンネル登録お願いします！'})
    for text in ssml_texts:
        with open(f'ssml/{text["fn"]}.xml', 'w') as fw:
            fw.write(u.ssml_prefix)
            fw.write(text['text'])
            fw.write(u.ssml_postfix)


if __name__ == '__main__':
    main()
