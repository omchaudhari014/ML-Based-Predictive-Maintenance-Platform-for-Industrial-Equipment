with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_init = False
for line in lines:
    if "async function init" in line:
        in_init = True
    if in_init:
        print(line, end='')
    if in_init and "catch(err)" in line:
        print("    }")
        print("  }")
        break
