import json
import os
import sys

import fitz

opacity = 0.20 # 既読に背景色をかぶせるときの不透明度 = 既読文字の薄さ
adj = {'x0': 3, 'y0': 2, 'x1': 0, 'y1': 3} # offsetは文字サイズ(文字幅？)に対する割合にしたほうがいいかも
ignore_width = [ # この幅に一致する場合は既読の対象にしない、小数点以下1桁の文字列で指定する
    '24.9', # 傍点
    '10.4', # ふりがな
    '10.1', # 左上の章文字
]

with open('config.json', 'r') as f:
    config = json.load(f)

def hex_to_rgb(hex):
    return tuple(int(hex[i:i+2], 16) / 255 for i in range(0, 6, 2))

def read(page, rect):
    rect = fitz.fitz.Rect(rect.x0 + adj['x0'], rect.y0 + adj['y0'], rect.x1 + adj['x1'], rect.y1 + adj['y1'])
    annot = page.addRectAnnot(rect)
    # annot.setColors({'fill': (0, 0, 0)}) # 黒表示、枠のデバッグ用
    annot.setColors({'fill': hex_to_rgb(config['background_color'])})
    annot.setBorder({'width': 100}) # こうすると何故か枠が消える
    annot.setOpacity(opacity)
    annot.update()

def cut_rects(rects): # 「す」で検索すると「すすき」の「すす」が一つの枠で出現してしまうので、連続した場合は等分する
    ret = []
    for rect in rects:
        ratio = (rect.y1 - rect.y0) / (rect.x1 - rect.x0) / 0.693 # 1文字の場合はおよそ1になる
        if   ratio < 1.5: # 1文字
            ret.append(rect)
        elif ratio < 2.5: # 2文字
            h = (rect.y1 - rect.y0) / 2
            for i in range(2):
                ret.append(fitz.fitz.Rect(rect.x0, rect.y0 + i * h, rect.x1, rect.y0 + (i + 1) * h))
        elif ratio < 3.5: # 3文字
            h = (rect.y1 - rect.y0) / 3
            for i in range(3):
                ret.append(fitz.fitz.Rect(rect.x0, rect.y0 + i * h, rect.x1, rect.y0 + (i + 1) * h))
        else:
            print('4文字以上連続した場合の処理を作る必要がある')
            sys.exit(1)
    return ret

def main():
    os.makedirs('animation_images', exist_ok=True)
    with open('pagefeeds.json', 'r') as f:
        pagefeeds = json.load(f)
    original_pdf = fitz.open('novel.pdf')

    for page_id, pagefeed in enumerate(pagefeeds):
        appear = {}
        already_read_rects = []
        for word_id, word in enumerate(pagefeed['words']):
            pdf = fitz.open()
            pdf.insertPDF(original_pdf, page_id, page_id)
            page = pdf[0]
            w = word['skipped_text'] + word['text']
            if word['skipped_start_index_in_page'] < 0: # ページ切り替えで前ページに余った文字を既読にするとずれるので、調整する
                w = w[- word['skipped_start_index_in_page']:]
            for char in w:
                rects = page.searchFor(char, hit_max=100)
                rects = cut_rects(rects)
                rects = [rect for rect in rects if f'{rect.x1 - rect.x0:.1f}' not in ignore_width]
                if char in appear.keys():
                    appear[char] += 1
                else:
                    appear[char] = 0
                already_read_rects.append(rects[appear[char]])
            for rect in already_read_rects:
                read(page, rect)
            pdf.save(f'animation_images/novel_{page_id:0>5}_{word_id:0>5}.pdf', garbage=4, deflate=True, clean=True)

if __name__ == '__main__':
    main()

