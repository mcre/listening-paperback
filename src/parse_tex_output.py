import json

import regex as re

PATTERNS = {
    'page': re.compile(r'Completed box being shipped out.*?\|\.\\special{'),
    'text': re.compile(r'\JT2/mc/m/n/(?:14|19\.6|23\.8|35)\s(\S+?)'),
}

def main():
    with open('tex_output.txt', 'r') as f:
        output = f.read()
    output = output.replace('\n', '|')
    pages = PATTERNS['page'].findall(output)
    texts = []
    for page in pages:
        page = page.replace('|', '\n')
        text = PATTERNS['text'].findall(page)
        texts.append(''.join(PATTERNS['text'].findall(page)))
    with open('pages.json', 'w') as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
