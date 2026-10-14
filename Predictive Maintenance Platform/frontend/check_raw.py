with open('frontend/index.html', 'r', encoding='utf-8') as f:
    for line in f:
        if 'moreBtn =' in line:
            print(repr(line))
