"""Помощники для веб-уроков: страница-заготовка и слияние урока в pack.json."""
import json

from mk import *

PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Задание</title>
</head>
<body>
{body}
</body>
</html>
"""


def page(body, head=""):
    p = PAGE.replace("{body}", body)
    return p.replace("</head>", head + "</head>") if head else p


def style(css):
    return "  <style>\n" + "".join("    " + ln + "\n" if ln else "\n" for ln in css.strip("\n").split("\n")) + "  </style>\n"


def measure(code, expr):
    """Значение выражения на настоящей странице (тем же раннером, что в приложении)."""
    return str(page_text(code, expr))


def merge_pack(pack_id, lesson_id, skills, description=None):
    f = ROOT / "content/packs" / pack_id / "pack.json"
    data = json.loads(f.read_text("utf-8"))
    if lesson_id not in data["lessons"]:
        data["lessons"].append(lesson_id)
    data["skills"].update(skills)
    if description:
        data["description"] = description
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8")


def computed(selector, prop):
    return f"getComputedStyle(document.querySelector('{selector}')).{prop}"


def merge_js_lesson(lesson_id, skills, pack_id="javascript"):
    merge_pack(pack_id, lesson_id, skills)
