import re
from pathlib import Path

html = Path(
    r"c:\Users\Administrator\Downloads\Sr AI Engineer - Product @ MeridianLink.html"
).read_text(encoding="utf-8", errors="ignore")

# Split by field containers
for m in re.finditer(
    r'ashby-application-form-field-container[^>]*>(.{0,3000}?)(?=ashby-application-form-field-container|$)',
    html,
    re.DOTALL,
):
    chunk = m.group(1)
    title = re.search(r'ashby-application-form-field-title[^>]*>([^<]+)<', chunk)
    if not title:
        title = re.search(r'ashby-application-form-field-label[^>]*>([^<]+)<', chunk)
    if title:
        t = re.sub(r"\s+", " ", title.group(1)).strip()
        inputs = re.findall(r'type="(checkbox|radio|text|email|tel|file)"', chunk)
        if t and inputs:
            print(f"\n[{', '.join(inputs)}] {t[:120]}")
