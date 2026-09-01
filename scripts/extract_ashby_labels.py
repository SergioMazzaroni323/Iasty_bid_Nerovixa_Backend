import re
from pathlib import Path

html = Path(
    r"c:\Users\Administrator\Downloads\Sr AI Engineer - Product @ MeridianLink.html"
).read_text(encoding="utf-8", errors="ignore")

# Find labels near checkboxes
for uid in [
    "e21915ce-9b4a-4c97-b4a9-10877142d2f7",
    "6d05512b-1e81-4533-8482-03a6adf698b8",
    "ea3bf90c-ffa9-423a-86a2-28c6b5a9cfb6",
    "17336b92-908b-400e-b87b-133b077cf7a9",
    "30543182-ef16-4a0d-a497-8a8fcddbc971",
]:
    idx = html.find(uid)
    if idx == -1:
        print(uid, "NOT FOUND")
        continue
    snippet = html[max(0, idx - 500) : idx + 500]
    labels = re.findall(r">([^<>]{3,80})<", snippet)
    print(f"\n=== {uid} ===")
    for l in labels[-8:]:
        print(" ", l.strip())

# All ashby labels
print("\n=== ALL ASHBY LABELS ===")
for m in re.finditer(r'class="[^"]*ashby-application-form-field-label[^"]*"[^>]*>([^<]+)<', html):
    print(m.group(1).strip())

# file input
for m in re.finditer(r'type="file"[^>]+>', html):
    print("FILE:", m.group(0)[:200])
