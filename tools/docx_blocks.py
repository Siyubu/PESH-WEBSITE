"""Read a .docx into an ordered list of blocks (paragraphs and tables) using only the stdlib."""
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _run_text(r):
    out = []
    for c in r:
        if c.tag == W + "t":
            out.append(c.text or "")
        elif c.tag == W + "tab":
            out.append("\t")
        elif c.tag == W + "br":
            out.append("\n")
    return "".join(out)


def _para(p, numfmt=None):
    style = p.find(W + "pPr/" + W + "pStyle")
    style = style.get(W + "val") if style is not None else None
    numpr = p.find(W + "pPr/" + W + "numPr")
    ilvl = None
    ordered = False
    if numpr is not None:
        lv = numpr.find(W + "ilvl")
        ilvl = int(lv.get(W + "val")) if lv is not None else 0
        nid = numpr.find(W + "numId")
        nid = nid.get(W + "val") if nid is not None else None
        fmt = (numfmt or {}).get((nid, ilvl), "bullet")
        ordered = fmt not in ("bullet", "none")
    text_parts, bold_chars, total_chars = [], 0, 0
    for r in p.iter(W + "r"):
        t = _run_text(r)
        if not t.strip():
            text_parts.append(t)
            continue
        rpr = r.find(W + "rPr")
        b = rpr is not None and rpr.find(W + "b") is not None and rpr.find(W + "b").get(W + "val") not in ("0", "false")
        text_parts.append(t)
        total_chars += len(t.strip())
        if b:
            bold_chars += len(t.strip())
    text = "".join(text_parts).replace(" ", " ").strip()
    return {
        "type": "p",
        "style": style,
        "list": ilvl,
        "ordered": ordered,
        "bold": total_chars > 0 and bold_chars / total_chars > 0.8,
        "text": text,
    }


def _numbering(z):
    """Map (numId, ilvl) -> numFmt using numbering.xml."""
    try:
        root = ET.fromstring(z.read("word/numbering.xml"))
    except KeyError:
        return {}
    abstract = {}
    for a in root.findall(W + "abstractNum"):
        aid = a.get(W + "abstractNumId")
        for lvl in a.findall(W + "lvl"):
            f = lvl.find(W + "numFmt")
            abstract[(aid, int(lvl.get(W + "ilvl")))] = f.get(W + "val") if f is not None else "bullet"
    out = {}
    for n in root.findall(W + "num"):
        aid = n.find(W + "abstractNumId").get(W + "val")
        for (a, lv), fmt in abstract.items():
            if a == aid:
                out[(n.get(W + "numId"), lv)] = fmt
    return out


def _table(t):
    rows = []
    for tr in t.findall(W + "tr"):
        row = []
        for tc in tr.findall(W + "tc"):
            cell = " ".join(_para(p, None)["text"] for p in tc.findall(W + "p")).strip()
            row.append(cell)
        rows.append(row)
    return {"type": "table", "rows": rows}


def read_blocks(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        numfmt = _numbering(z)
    blocks = []
    for el in root.find(W + "body"):
        if el.tag == W + "p":
            blocks.append(_para(el, numfmt))
        elif el.tag == W + "tbl":
            blocks.append(_table(el))
    return blocks
