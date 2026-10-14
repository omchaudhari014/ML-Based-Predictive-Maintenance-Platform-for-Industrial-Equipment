with open('frontend/js/api.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_exp = '''export async function getExplanation(id) {
  const activeRecord = store.getRecordById(id);
  if (activeRecord) return activeRecord;
  throw new Error("Explanation requires the record to be in the active session.");
}'''

new_exp = '''export async function getExplanation(id) {
  const activeRecord = store.getRecordById(id);
  if (!activeRecord) throw new Error("Explanation requires the record to be in the active session.");
  
  // Make a real POST to /api/explain
  const res = await fetch('/api/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ values: activeRecord.features })
  });
  
  if (!res.ok) throw new Error("Explanation failed");
  const data = await res.json();
  
  // Merge explanation into record
  activeRecord.explanation = data.explanation;
  activeRecord.expected_value = data.expected_value;
  return activeRecord;
}'''

content = content.replace(old_exp, new_exp)

with open('frontend/js/api.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched api.js getExplanation")
