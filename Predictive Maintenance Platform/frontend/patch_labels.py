import sys

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_labels = '''  const labels = {
    'all': 'All Equipment',
    'motor': 'Motors',
    'pump': 'Pumps',
    'compressor': 'Compressors',
    'gearbox': 'Gearboxes',
    'cnc': 'CNC Machines'
  };'''

new_labels = '''  const labels = {
    'all': 'All Equipment',
    'induction_motor': 'Motors',
    'centrifugal_pump': 'Pumps',
    'screw_compressor': 'Compressors',
    'industrial_gearbox': 'Gearboxes',
    'cnc_milling': 'CNC Machines',
    'steam_turbine': 'Steam Turbines',
    'industrial_boiler': 'Boilers',
    'generator': 'Generators'
  };'''

content = content.replace(old_labels, new_labels)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched frontend labels")
