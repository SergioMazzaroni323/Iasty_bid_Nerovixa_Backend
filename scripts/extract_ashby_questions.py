import re
from pathlib import Path

html = Path(
    r"c:\Users\Administrator\Downloads\Sr AI Engineer - Product @ MeridianLink.html"
).read_text(encoding="utf-8", errors="ignore")

# Extract visible question strings from rendered HTML
patterns = [
    r'ashby-application-form-field-title[^>]*>([^<]+)<',
    r'ashby-application-form-field-label[^>]*>([^<]+)<',
    r'class="_heading[^"]*"[^>]*>([^<]+)<',
    r'<label[^>]*for="[^"]*"[^>]*>([^<]{4,120})</label>',
]

all_labels = set()
for pat in patterns:
    for m in re.finditer(pat, html):
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        if t and t != "*":
            all_labels.add(t)

for t in sorted(all_labels, key=len):
    print(t)

print("\n--- CHECKBOX LABELS ---")
for m in re.finditer(r'labeled-checkbox-\d+"[^>]*>([^<]+)<', html):
    print(m.group(1).strip())

print("\n--- RADIO LABELS (first 30 unique) ---")
seen = set()
for m in re.finditer(r'labeled-radio-\d+"[^>]*>([^<]+)<', html):
    t = m.group(1).strip()
    if t not in seen:
        seen.add(t)
        print(t)
