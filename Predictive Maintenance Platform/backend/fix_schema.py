import json
import os

CATALOG_FILE = 'backend/catalog/machines.json'
with open(CATALOG_FILE, 'r') as f:
    catalog = json.load(f)

for m in catalog['machines']:
    for s in m['sensor_schema']:
        # if warning_min is greater than normal_max, it was swapped with warning_max!
        if s.get('warning_min') is not None and s.get('normal_max') is not None:
            if s['warning_min'] >= s['normal_max']:
                # it's an upper bound mistakenly placed in min
                if s.get('warning_max') is not None and s['warning_max'] > s['warning_min']:
                    # if warning_max is already there and higher, maybe warning_min was meant to be None
                    s['warning_min'] = None
                else:
                    # just clear it
                    s['warning_min'] = None
                    
        # same for critical_min
        if s.get('critical_min') is not None and s.get('normal_max') is not None:
            if s['critical_min'] >= s['normal_max']:
                if s.get('critical_max') is None:
                    s['critical_max'] = s['critical_min']
                s['critical_min'] = None

        # also for speed where critical_max is 1400 but normal_min is 1440
        if s.get('critical_max') is not None and s.get('normal_min') is not None:
            if s['critical_max'] <= s['normal_min']:
                if s.get('critical_min') is None:
                    s['critical_min'] = s['critical_max']
                s['critical_max'] = None

with open(CATALOG_FILE, 'w') as f:
    json.dump(catalog, f, indent=2)

print("Fixed threshold schema bounds in catalog.")
