import json
import re
from pathlib import Path


def extract_json_after_marker(text: str, marker: str) -> dict:
    start = text.find(marker)
    if start == -1:
        raise ValueError("marker not found")
    i = start + len(marker)
    while text[i] != "{":
        i += 1
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[i : j + 1])
    raise ValueError("json not closed")


html = Path(r"c:\Users\Administrator\Downloads\Sr AI Engineer - Product @ MeridianLink.html").read_text(
    encoding="utf-8", errors="ignore"
)
data = extract_json_after_marker(html, "window.__appData = ")
print("Top keys:", list(data.keys()))

titles = []


def walk(obj, path=""):
    if isinstance(obj, dict):
        title = obj.get("title")
        if isinstance(title, str) and 2 < len(title) < 120:
            titles.append(
                {
                    "title": title,
                    "type": obj.get("type") or obj.get("fieldType"),
                    "path": obj.get("path") or obj.get("id"),
                    "required": obj.get("isRequired"),
                }
            )
        for k, v in obj.items():
            walk(v, path)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, path)


walk(data)
seen = set()
print("\n=== Ashby fields ===")
for item in titles:
    key = item["title"]
    if key in seen:
        continue
    seen.add(key)
    print(item)
