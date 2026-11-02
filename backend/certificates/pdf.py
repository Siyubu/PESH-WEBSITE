from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

LOGO = Path(__file__).parent / "assets" / "logo.jpg"
NAVY = colors.HexColor("#012d60")
GOLD = colors.HexColor("#b8860b")


def _header(c, w, h):
    if LOGO.exists():
        c.drawImage(str(LOGO), w / 2 - 70, h - 140, width=140, height=70, preserveAspectRatio=True, mask="auto")
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 40)
    c.drawCentredString(w / 2, h - 210, "Certificate of Completion")


def _footer_strip(c, w, note):
    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, 52, note)
    c.showPage()
    c.save()


def certificate_pdf(cert):
    buf = BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle(f"PESH certificate {cert.code}")

    c.setStrokeColor(GOLD)
    c.setLineWidth(6)
    c.rect(24, 24, w - 48, h - 48)
    c.setLineWidth(1.5)
    c.rect(38, 38, w - 76, h - 76)

    _header(c, w, h)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Times-Italic", 16)
    c.drawCentredString(w / 2, h - 250, "This certifies that")
    c.setFillColor(colors.black)
    c.setFont("Times-Bold", 34)
    c.drawCentredString(w / 2, h - 300, cert.learner_name)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(w / 2 - 190, h - 310, w / 2 + 190, h - 310)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Times-Italic", 16)
    c.drawCentredString(w / 2, h - 345, "has successfully completed PESH's module of")
    c.setFillColor(NAVY)
    c.setFont("Times-Bold", 26)
    c.drawCentredString(w / 2, h - 385, cert.course.title)

    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 10)
    y = 90
    for x, label, value in (
        (w * 0.22, "Date", cert.issued_at.strftime("%d %B %Y")),
        (w * 0.5, "Certificate ID", cert.code),
        (w * 0.78, "Issued by", "PESH, Rwanda"),
    ):
        c.setStrokeColor(colors.HexColor("#666666"))
        c.line(x - 90, y + 16, x + 90, y + 16)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x, y, value)
        c.setFont("Helvetica", 9)
        c.drawCentredString(x, y - 14, label)
    _footer_strip(c, w, "Verify this certificate at the PESH website using the Certificate ID.")
    return buf.getvalue()


def combined_certificate_pdf(cert):
    """A single certificate covering every course, for a learner who took the program in person."""
    buf = BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=(w, h))
    c.setTitle(f"PESH certificate {cert.code}")

    c.setStrokeColor(GOLD)
    c.setLineWidth(6)
    c.rect(24, 24, w - 48, h - 48)
    c.setLineWidth(1.5)
    c.rect(38, 38, w - 76, h - 76)

    _header(c, w, h)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Times-Italic", 16)
    c.drawCentredString(w / 2, h - 250, "This certifies that")
    c.setFillColor(colors.black)
    c.setFont("Times-Bold", 34)
    c.drawCentredString(w / 2, h - 300, cert.learner.full_name())
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(w / 2 - 190, h - 310, w / 2 + 190, h - 310)
    c.setFillColor(colors.HexColor("#555555"))
    c.setFont("Times-Italic", 16)
    c.drawCentredString(w / 2, h - 345, "has successfully completed PESH's modules of")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, h - 385, "   •   ".join(cert.course_titles))

    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica", 10)
    y = 90
    for x, label, value in (
        (w * 0.22, "Date", cert.issued_at.strftime("%d %B %Y")),
        (w * 0.5, "Certificate ID", cert.code),
        (w * 0.78, "Issued by", "PESH, Rwanda"),
    ):
        c.setStrokeColor(colors.HexColor("#666666"))
        c.line(x - 90, y + 16, x + 90, y + 16)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x, y, value)
        c.setFont("Helvetica", 9)
        c.drawCentredString(x, y - 14, label)
    _footer_strip(c, w, "Verify this certificate at the PESH website using the Certificate ID.")
    return buf.getvalue()
