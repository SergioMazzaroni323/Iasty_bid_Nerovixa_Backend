import json
import re
from pathlib import Path


def extract_app_data(html: str) -> dict:
    start = html.find("window.__appData = ") + len("window.__appData = ")
    i = start
    while html[i] != "{":
        i += 1
    depth = 0
    for j in range(i, len(html)):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[i : j + 1])
    raise ValueError("json not closed")


html = Path(
    r"c:\Users\Administrator\Downloads\Sr AI Engineer - Product @ MeridianLink.html"
).read_text(encoding="utf-8", errors="ignore")
data = extract_app_data(html)

fields = []


def walk(obj, path=""):
    if isinstance(obj, dict):
        if "title" in obj and ("field" in str(obj.get("type", "")).lower() or "path" in obj):
            fields.append(obj)
        if obj.get("type") == "ApplicationFormField":
            fields.append(obj)
        for v in obj.values():
            walk(v, path)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, path)


walk(data)

seen = set()
for f in fields:
    title = f.get("title") or f.get("label")
    if not title or title in seen:
        continue
    seen.add(title)
    print(
        {
            "title": title,
            "type": f.get("type") or f.get("fieldType"),
            "path": f.get("path") or f.get("id"),
            "required": f.get("isRequired"),
        }
    )

# Also dump raw strings that look like questions
for m in re.finditer(r'"title"\s*:\s*"([^"]{5,120})"', html):
    t = m.group(1)
    if any(k in t.lower() for k in ("?", "name", "email", "phone", "resume", "linkedin", "cover", "salary", "hear")):
        print("Q:", t)
