"""Convert the PESH curriculum .docx files in ../courses into backend/courses/data/*.json."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from docx_blocks import read_blocks

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "courses"
OUT = ROOT / "backend" / "courses" / "data"

LEVELS = {  # docx heading style -> output heading level, per course
    "excel": {"Heading2": 3, "Heading3": 3, "Heading4": 4, "Heading5": 4},
    "word": {"Heading1": 3, "Heading2": 3, "Heading3": 4, "Heading4": 4},
    "scratch": {"Heading1": 3, "Heading2": 4, "Heading3": 5},
    "internet": {"Heading1": 3, "Heading2": 3, "Heading3": 4},
}


def clean(text):
    return re.sub(r"[ \t]+", " ", text).strip()


def convert(blocks, course):
    out = []
    levels = LEVELS[course]
    for b in blocks:
        if b["type"] == "table":
            rows = [[clean(c) for c in r] for r in b["rows"]]
            rows = [r for r in rows if any(r)]
            if rows:
                out.append({"t": "table", "rows": rows})
            continue
        text = clean(b["text"])
        if not text or "PAGEREF" in text or text.startswith("TOC \\"):
            continue
        style = b["style"]
        if b["list"] is not None:
            out.append({"t": "li", "text": text, "ordered": b["ordered"]})
        elif style == "HTMLPreformatted":
            out.append({"t": "code", "text": b["text"].strip("\n")})
        elif style in levels and len(text) <= 110:
            out.append({"t": "h", "level": levels[style], "text": text})
        elif b["bold"] and len(text) <= 60 and text.endswith(":"):
            out.append({"t": "h", "level": 4, "text": text.rstrip(":")})
        elif b["bold"] and len(text) <= 60 and course == "word":
            out.append({"t": "h", "level": 4, "text": text.rstrip(":")})
        elif b["bold"] and len(text) <= 80 and course == "internet":
            out.append({"t": "h", "level": 4 if text.endswith(":") else 3, "text": text.rstrip(":")})
        else:
            out.append({"t": "p", "text": text})
    return out


def split_goals(blocks):
    """Pull a leading 'Goal(s)' section out of a lesson's blocks."""
    goals, rest, i = [], list(blocks), 0
    while i < len(rest) and not (rest[i]["t"] == "h" and re.match(r"goals?:?$", rest[i]["text"], re.I)):
        i += 1
        if i > 6:
            return [], blocks
    if i >= len(rest):
        return [], blocks
    j = i + 1
    while j < len(rest) and rest[j]["t"] in ("p", "li"):
        for line in rest[j]["text"].replace("⮚", "\n").split("\n"):
            line = clean(line)
            if line and not line.lower().startswith(("by the end", "students will")):
                goals.append(line.lstrip("•-➢ "))
        j += 1
    return goals, rest[:i] + rest[j:]


def find(blocks, pred, start=0):
    for k in range(start, len(blocks)):
        if blocks[k]["type"] == "p" and pred(blocks[k]["text"]):
            return k
    raise ValueError("anchor not found")


def lesson(id_, title, blocks, course, summary=""):
    body = convert(blocks, course)
    goals, body = split_goals(body)
    return {"id": id_, "title": title, "summary": summary, "goals": goals, "blocks": body}


FORMULAS = {  # inferred from the cells and results stated in the lesson text
    "Activity 1": ["=A1+A2"],
    "Activity 2": ["=B1-B2"],
    "Activity 3": ["=C1*C2"],
    "Activity 4": ["=D1/D2"],
    "Activity 6": ["=SUM(A1:A5)"],
    "Activity 7": ["=AVERAGE(B1:B4)"],
    "Activity 8": ["=MIN(C1:C5)", "=MAX(C1:C5)"],
    "Activity 9": ["=COUNT(D1:D5)"],
}


def patch_formulas(lesson_blocks):
    pending, act = [], None
    for blk in lesson_blocks:
        if blk["t"] == "h" and blk["level"] == 3:
            m = re.match(r"(Activity \d+):", blk["text"])
            act = m.group(1) if m else None
            pending = list(FORMULAS.get(act, []))
        elif blk["t"] in ("li", "p") and pending and re.search(r"type:?$", blk["text"], re.I):
            blk["text"] = f'{blk["text"].rstrip(":")}: {pending.pop(0)}'


def build_excel():
    b = read_blocks(SRC / "PESH CURRICULUM-Excel.docx")
    marks = []
    for n in range(1, 8):
        marks.append(find(b, lambda t, n=n: re.match(rf"lesson\s*{n}\s*:\s*", t, re.I) is not None and len(t) < 60 and "\t" not in t, marks[-1] + 1 if marks else 0))
    more = find(b, lambda t: t.strip().upper() == "MORE EXERCISES")
    final = find(b, lambda t: "Final Project" in t and len(t) < 60, more)
    titles = ["Introduction to Microsoft Excel", "Home Tab", "Insert Tab", "Draw Tab", "Formulas", "More Formulas", "Data Tab"]
    # per-lesson extra practice lives under MORE EXERCISES
    extra_marks = []
    for n in range(1, 8):
        extra_marks.append(find(b, lambda t, n=n: re.match(rf"lesson\s*{n}\s*:", t, re.I) is not None, (extra_marks[-1] + 1) if extra_marks else more + 1))
    lessons = []
    for i, (m, t) in enumerate(zip(marks, titles)):
        end = marks[i + 1] if i + 1 < len(marks) else more
        core = b[m + 1:end]
        ex_end = extra_marks[i + 1] if i + 1 < len(extra_marks) else final
        extra = convert(b[extra_marks[i] + 1:ex_end], "excel")
        les = lesson(f"l{i+1}", t, core, "excel")
        if t == "Formulas":
            patch_formulas(les["blocks"])
        if extra:
            les["blocks"].append({"t": "h", "level": 3, "text": "More Practice Exercises"})
            les["blocks"].extend(extra)
        lessons.append(les)
    fin = lesson("l8", "Final Project: My School Workbook", b[final + 1:], "excel", "Put every skill together in one workbook.")
    lessons.append(fin)
    return {
        "id": "excel", "title": "Microsoft Excel", "icon": "\U0001F4CA", "level": "Beginner",
        "description": "Learn spreadsheets from the first cell to formulas, charts, sorting and filtering, with hands-on activities and projects.",
        "lessons": lessons,
    }


def build_word():
    b = read_blocks(SRC / "PESH curriculum level1 word.docx")
    def h(txt):
        return find(b, lambda t: t.strip().upper() == txt, 44)
    plan = [
        ("Introduction to the Computer", h("INTRODUCTION TO THE COMPUTER"), h("HOME TAB")),
        ("Home Tab: Moving, Selecting and Fonts", h("HOME TAB"), find(b, lambda t: t.strip() == "Lesson 3")),
        ("Home Tab: Bold, Underline, Copy and Paste", find(b, lambda t: t.strip() == "Lesson 3"), find(b, lambda t: t.strip().startswith("Lesson4"))),
        ("Home Tab: Colors, Highlight and Effects", find(b, lambda t: t.strip().startswith("Lesson4")), find(b, lambda t: t.strip().startswith("Lesson5"))),
        ("Home Tab: Lists and Alignment", find(b, lambda t: t.strip().startswith("Lesson5")), find(b, lambda t: t.strip().startswith("Lesson 6"))),
        ("Home Tab: Spacing, Folders and Files", find(b, lambda t: t.strip().startswith("Lesson 6")), h("COMMON SHORTCUTS")),
        ("Common Keyboard Shortcuts", h("COMMON SHORTCUTS"), h("INSERT TAB")),
        ("Insert Tab", h("INSERT TAB"), h("DRAW TAB")),
        ("Draw Tab", h("DRAW TAB"), find(b, lambda t: t.startswith("Writing and Creativity Competition"))),
    ]
    lessons = []
    for i, (title, s, e) in enumerate(plan):
        core = b[s + 1:e]
        # drop the "Lesson N" label line so the lesson title is not repeated
        core = [x for x in core if not (x["type"] == "p" and re.fullmatch(r"lesson\s*\d+\s*:?", x["text"].strip(), re.I))]
        lessons.append(lesson(f"l{i+1}", title, core, "word"))
    return {
        "id": "word", "title": "Microsoft Word", "icon": "\U0001F4DD", "level": "Beginner",
        "description": "Start with the computer itself, then learn to write, format, decorate and save documents in Microsoft Word.",
        "lessons": lessons,
    }


def build_scratch():
    b = read_blocks(SRC / "Scratch Student Guiding Manual draft.docx")
    marks = [k for k, x in enumerate(b) if x["type"] == "p" and re.match(r"LESSON\s+\d+\s*:", x["text"]) and x["style"] == "Heading1"]
    lessons = []
    for i, m in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(b)
        raw = re.sub(r"^LESSON\s+\d+\s*:\s*", "", b[m]["text"])
        raw = re.sub(r"[^\w\s—&'-]", "", raw).strip()
        head, _, tail = raw.partition("—")
        title = head.strip().title().replace("X And Y", "X and Y")
        summary = tail.strip().capitalize()
        lessons.append(lesson(f"l{i+1}", title, b[m + 1:end], "scratch", summary))
    return {
        "id": "scratch", "title": "Scratch Programming", "icon": "\U0001F431", "level": "Beginner",
        "description": "Learn to code by snapping blocks together: make sprites move, talk, play sounds, react to events and build your own games.",
        "lessons": lessons,
    }


def build_internet():
    import glob

    path = [p for p in glob.glob(str(SRC / "*.docx")) if "INTERNET" in p.upper()][0]
    b = read_blocks(path)
    marks = [k for k, x in enumerate(b) if x["type"] == "p" and re.match(r"LESSON\s+\d+\s*:", x["text"].strip())]
    lessons = []
    for i, m in enumerate(marks):
        end = marks[i + 1] if i + 1 < len(marks) else len(b)
        title = re.sub(r"^LESSON\s+\d+\s*:\s*", "", b[m]["text"].strip())
        small = {"a", "an", "the", "to", "and", "of", "in", "for", "on", "or"}
        words = " ".join(title.split()).lower().split(" ")
        title = " ".join(w if (n and w in small) else w.capitalize() for n, w in enumerate(words)).replace("Gmail", "Gmail")
        lessons.append(lesson(f"l{i+1}", title, b[m + 1:end], "internet"))
    return {
        "id": "internet", "title": "Internet and AI", "icon": "\U0001F310", "level": "Beginner",
        "description": "Understand the internet, browse and search safely, use email, protect your privacy, and learn how to use AI wisely.",
        "lessons": lessons,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (("excel", build_excel), ("word", build_word), ("scratch", build_scratch), ("internet", build_internet)):
        data = fn()
        (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(name, len(data["lessons"]), "lessons", sum(len(l["blocks"]) for l in data["lessons"]), "blocks")


if __name__ == "__main__":
    main()
