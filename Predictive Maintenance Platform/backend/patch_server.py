import sys

with open('backend/server.py', 'r') as f:
    content = f.read()

import re

# Patch get_machines
old_get = '''def get_machines():
    summary = []
    for m in MACHINES.values():
        summary.append({
            "id": m["id"],
            "name": m["name"],
            "type": m["type"],
            "type_label": m["type_label"],
            "manufacturer": m["manufacturer"],
            "model": m["model"],
            "description": m["description"],
            "image": m["image"],
            "assessment_method": m["assessment_method"]
        })
    return jsonify({"machines": summary})'''

new_get = '''def get_machines():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    
    summary = []
    for m in MACHINES.values():
        summary.append({
            "id": m["id"],
            "name": m["name"],
            "type": m["type"],
            "type_label": m["type_label"],
            "manufacturer": m["manufacturer"],
            "model": m["model"],
            "description": m.get("description", ""),
            "image": m["image"],
            "assessment_method": m["assessment_method"]
        })
    
    total = len(summary)
    summary = summary[start:start+limit]
    return jsonify({"machines": summary, "total": total, "page": page, "limit": limit})'''

content = content.replace(old_get, new_get)

# Patch search_machines
old_search = '''def search_machines():
    query = request.args.get('q', '').lower()
    results = []
    for m in MACHINES.values():
        searchable_text = f"{m['name']} {m['type']} {m['manufacturer']} {m['model']} {m['id']}".lower()
        if query in searchable_text:
            results.append({
                "id": m["id"],
                "name": m["name"],
                "type": m["type"],
                "type_label": m["type_label"],
                "manufacturer": m["manufacturer"],
                "model": m["model"],
                "description": m["description"],
                "image": m["image"],
                "assessment_method": m["assessment_method"]
            })
    return jsonify({"machines": results})'''

new_search = '''def search_machines():
    query = request.args.get('q', '').lower()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    start = (page - 1) * limit
    
    results = []
    for m in MACHINES.values():
        searchable_text = f"{m['name']} {m.get('family', '')} {m['type']} {m['manufacturer']} {m['model']} {m['id']} {' '.join(m.get('application', []))}".lower()
        if not query or query in searchable_text:
            results.append({
                "id": m["id"],
                "name": m["name"],
                "type": m["type"],
                "type_label": m["type_label"],
                "manufacturer": m["manufacturer"],
                "model": m["model"],
                "description": m.get("description", ""),
                "image": m["image"],
                "assessment_method": m["assessment_method"]
            })
            
    total = len(results)
    results = results[start:start+limit]
    return jsonify({"machines": results, "total": total, "page": page, "limit": limit})'''

content = content.replace(old_search, new_search)

with open('backend/server.py', 'w') as f:
    f.write(content)

print("Patched server.py successfully")
