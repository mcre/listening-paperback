def number_to_kansuji(number):
    max_ = 4
    if number >= 10 ** max_:
        raise Exception()

    dic = {0: '', 1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九', 10: '十', 100: '百', 1000: '千'}
    bases = {10 ** i: number // 10 ** i % 10 for i in range(max_)}
    ret = ''
    for i in reversed(range(max_)):
        b = bases[10 ** i]
        if i == 0:  # 一桁目
            ret += f'{dic[b]}'
        elif b != 0:
            if b == 1:
                ret += dic[10 ** i]
            else:
                ret += f'{dic[b]}{dic[10 ** i]}'
    return ret
