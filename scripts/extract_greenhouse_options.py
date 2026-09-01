import re
from pathlib import Path

html = Path(
    r"c:\Users\Administrator\Downloads\Job Application for Software Engineer - Full Stack at Figma.html"
).read_text(encoding="utf-8", errors="ignore")

options = set()
for m in re.finditer(r'role="option"[^>]*>([^<]+)<', html):
    options.add(m.group(1).strip())

for o in sorted(options):
    print(o)
