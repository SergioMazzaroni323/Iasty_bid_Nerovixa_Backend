import re
import sys
from pathlib import Path


def extract_fields(path: str) -> None:
    html = Path(path).read_text(encoding="utf-8", errors="ignore")
    print("===", Path(path).name, "===")

    for match in re.finditer(
        r'<label[^>]*(?:for="([^"]+)"|id="([^"]+-label)")[^>]*class="[^"]*label[^"]*"[^>]*>([^<]+)</label>',
        html,
    ):
        field_id = match.group(1) or match.group(2)
        print(f"LABEL: {match.group(3).strip()} -> {field_id}")

    for match in re.finditer(r'<label[^>]*for="question_(\d+)"[^>]*>([^<]+)</label>', html):
        print(f"QUESTION {match.group(1)}: {match.group(2).strip()}")

    for inp in re.finditer(r"<input[^>]+>", html):
        tag = inp.group(0)
        if 'type="hidden"' in tag:
            continue
        id_ = re.search(r'id="([^"]+)"', tag)
        name = re.search(r'name="([^"]+)"', tag)
        typ = re.search(r'type="([^"]+)"', tag)
        aria = re.search(r'aria-label="([^"]+)"', tag)
        print(
            "INPUT",
            typ.group(1) if typ else "?",
            id_.group(1) if id_ else "",
            name.group(1) if name else "",
            aria.group(1) if aria else "",
        )

    for ta in re.finditer(r"<textarea[^>]+>", html):
        tag = ta.group(0)
        id_ = re.search(r'id="([^"]+)"', tag)
        name = re.search(r'name="([^"]+)"', tag)
        print("TEXTAREA", id_.group(1) if id_ else "", name.group(1) if name else "")

    for match in re.finditer(r'class="label[^"]*"[^>]*>([^<]+)<', html):
        text = match.group(1).strip()
        if text and text != "*":
            print(f"LABEL_TEXT: {text}")

    for match in re.finditer(
        r">(Why do you[^<]+|Are you authorized[^<]+|Have you ever worked[^<]+|How many years[^<]+|"
        r"Have you worked as[^<]+|From where do you[^<]+|Have you built[^<]+|Which of the following[^<]+|"
        r"Which programming languages[^<]+)<",
        html,
    ):
        print(f"QUESTION_TEXT: {match.group(1).strip()}")

    for match in re.finditer(r"ashby-application-form-field-label[^>]*>([^<]+)<", html):
        print(f"ASHBY_LABEL: {match.group(1).strip()}")

    for match in re.finditer(r'placeholder="([^"]+)"', html):
        print(f"PLACEHOLDER: {match.group(1)}")

    print()


if __name__ == "__main__":
    for p in sys.argv[1:]:
        extract_fields(p)
