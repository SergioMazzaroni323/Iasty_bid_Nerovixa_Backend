import json
import re
import sys
from pathlib import Path


def extract_ashby_fields(path: str) -> None:
    html = Path(path).read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"window\.__appData = (\{.*?\});", html, re.DOTALL)
    if not match:
        print("No __appData found")
        return

    data = json.loads(match.group(1))
    posting = data.get("posting", {})
    form = posting.get("applicationForm", {}) or posting.get("applicationFormDefinition", {})
    sections = form.get("sections", []) or form.get("fieldSets", [])

    print("=== Ashby application fields ===")
    print("Title:", posting.get("title"))

    def walk(fields, prefix=""):
        for field in fields:
            title = field.get("title") or field.get("label") or field.get("path")
            field_type = field.get("type") or field.get("fieldType")
            path_key = field.get("path") or field.get("id")
            required = field.get("isRequired")
            if title:
                print(f"- [{field_type}] {title} (path={path_key}, required={required})")
            for sub in field.get("fields", []) or field.get("children", []):
                walk([sub], prefix + "  ")

    if sections:
        for section in sections:
            section_title = section.get("title") or section.get("name")
            if section_title:
                print(f"\n## {section_title}")
            walk(section.get("fields", []) or section.get("fieldSets", []))

    # fallback: search applicationForm in full json keys
    if not sections:
        form_str = json.dumps(form)[:5000]
        print("Form snippet:", form_str[:2000])


if __name__ == "__main__":
    extract_ashby_fields(sys.argv[1])
