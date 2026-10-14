with open('backend/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_mode = '''        # Observed mode logic
        observed_mode = None
        for mode in MODE_COLS:
            if mode in row and pd.notna(row[mode]) and float(row[mode]) == 1:
                observed_mode = mode
                break'''

new_mode = '''        # Observed mode logic
        observed_mode = None
        for mode in MODE_COLS:
            if mode in row and pd.notna(row[mode]):
                val = row[mode]
                try:
                    if float(val) == 1.0:
                        observed_mode = mode
                        break
                except:
                    if isinstance(val, str) and val.lower() not in ['none', '0', 'false', '']:
                        observed_mode = val
                        break'''

content = content.replace(old_mode, new_mode)

with open('backend/server.py', 'w', encoding='utf-8') as f:
    f.write(content)
