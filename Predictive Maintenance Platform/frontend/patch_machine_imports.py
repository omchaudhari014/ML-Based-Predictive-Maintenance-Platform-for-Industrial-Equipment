with open('frontend/machine.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re
import_pattern = re.compile(r"import \{ getMachineById.*?\} from '\./js/api\.js';", re.MULTILINE)
new_import = "import { getMachineById, getRecord, getMachineProfile, getExplanation, getMachines } from './js/api.js';"

content = import_pattern.sub(new_import, content)

with open('frontend/machine.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched imports!")
