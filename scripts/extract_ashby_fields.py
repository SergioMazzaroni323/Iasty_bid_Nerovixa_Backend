import re
from pathlib import Path

html = Path(
    r"c:\Users\Administrator\Downloads\Sr AI Engineer - Product @ MeridianLink.html"
).read_text(encoding="utf-8", errors="ignore")

for m in re.finditer(r"ashby-application-form-field-label[^>]*>([^<]+)<", html):
    print("LABEL:", m.group(1).strip())

for m in re.finditer(r'name="(_systemfield[^"]+)"', html):
    print("SYSTEM:", m.group(1))

for m in re.finditer(r"<textarea[^>]+name=\"([^\"]+)\"", html):
    print("TEXTAREA:", m.group(1))

for m in re.finditer(r"<input[^>]+>", html):
    tag = m.group(0)
    if 'type="hidden"' in tag:
        continue
    typ = re.search(r'type="([^"]+)"', tag)
    name = re.search(r'name="([^"]+)"', tag)
    if name:
        print("INPUT", typ.group(1) if typ else "?", name.group(1))
