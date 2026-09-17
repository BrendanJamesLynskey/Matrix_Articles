"""Shared ReportLab / matplotlib styling for the two Matrix articles.

Palette and layout are taken from the previous editions so the pair still reads
as a matched set: navy headings, navy table header bars, pale grey callouts,
DejaVu Sans throughout.
"""

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle

# ---------------------------------------------------------------- palette ---

NAVY = colors.HexColor("#1A3A5F")     # headings, table header bars
INK = colors.HexColor("#1B2A4A")      # dark blocks inside figures
TEAL = colors.HexColor("#2C8C8B")     # incident / forward
RED = colors.HexColor("#C0392B")      # reflected / reverse
CALLOUT_BG = colors.HexColor("#F2F4F7")
CALLOUT_EDGE = colors.HexColor("#C3CBD6")
RULE = colors.HexColor("#B9C2CE")
BODY = colors.HexColor("#111418")
MUTED = colors.HexColor("#5A6673")

HEX = dict(navy="#1A3A5F", ink="#1B2A4A", teal="#2C8C8B", red="#C0392B",
           grey="#8A97A6", pale="#F2F4F7", edge="#C3CBD6", amber="#B7791F")

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def register_fonts():
    pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))
    # No oblique face ships with this DejaVu build; map italic onto the roman so
    # that <i> tags degrade quietly rather than raising.
    pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold",
                                  italic="DejaVu", boldItalic="DejaVu-Bold")


def styles():
    ss = getSampleStyleSheet()
    s = {}
    s["title"] = ParagraphStyle("title", parent=ss["Normal"], fontName="DejaVu-Bold",
                                fontSize=21, leading=25, alignment=TA_CENTER,
                                textColor=NAVY, spaceAfter=4)
    s["deck"] = ParagraphStyle("deck", parent=ss["Normal"], fontName="DejaVu",
                               fontSize=10.5, leading=14, alignment=TA_CENTER,
                               textColor=MUTED, spaceAfter=2)
    s["byline"] = ParagraphStyle("byline", parent=s["deck"], fontSize=9.5,
                                 leading=13, spaceAfter=10)
    s["h1"] = ParagraphStyle("h1", parent=ss["Normal"], fontName="DejaVu-Bold",
                             fontSize=13.5, leading=17, textColor=NAVY,
                             spaceBefore=13, spaceAfter=5, keepWithNext=1)
    s["h2"] = ParagraphStyle("h2", parent=ss["Normal"], fontName="DejaVu-Bold",
                             fontSize=11, leading=14, textColor=NAVY,
                             spaceBefore=9, spaceAfter=3, keepWithNext=1)
    s["body"] = ParagraphStyle("body", parent=ss["Normal"], fontName="DejaVu",
                               fontSize=9.2, leading=13.4, alignment=TA_JUSTIFY,
                               textColor=BODY, spaceAfter=6,
                               allowWidows=0, allowOrphans=0)
    s["callout"] = ParagraphStyle("callout", parent=s["body"], fontSize=8.8,
                                  leading=12.8, spaceAfter=0)
    s["cell"] = ParagraphStyle("cell", parent=ss["Normal"], fontName="DejaVu",
                               fontSize=8.3, leading=11.4, textColor=BODY)
    s["cellhead"] = ParagraphStyle("cellhead", parent=s["cell"],
                                   fontName="DejaVu-Bold",
                                   textColor=colors.white)
    s["caption"] = ParagraphStyle("caption", parent=ss["Normal"], fontName="DejaVu",
                                  fontSize=7.8, leading=10.5, alignment=TA_CENTER,
                                  textColor=MUTED, spaceBefore=2, spaceAfter=9)
    s["gloss"] = ParagraphStyle("gloss", parent=s["body"], fontSize=8.6,
                                leading=12, spaceAfter=3, alignment=TA_JUSTIFY)
    s["ref"] = ParagraphStyle("ref", parent=s["gloss"], leftIndent=13,
                              firstLineIndent=-13)
    return s


# ---------------------------------------------------------------- helpers ---

def callout(text, st, width=None):
    """A pale boxed aside, one paragraph wide."""
    t = Table([[Paragraph(text, st["callout"])]], colWidths=[width or 158 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CALLOUT_BG),
        ("BOX", (0, 0), (-1, -1), 0.6, CALLOUT_EDGE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def datatable(rows, widths, st, header=True):
    body = []
    for r_i, row in enumerate(rows):
        style = st["cellhead"] if (header and r_i == 0) else st["cell"]
        body.append([Paragraph(c, style) for c in row])
    t = Table(body, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                 ("LINEBELOW", (0, 0), (-1, 0), 0.4, NAVY)]
    t.setStyle(TableStyle(cmds))
    return t


def page_furniture(footer_text):
    """Return an onPage callback drawing the running footer."""
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("DejaVu", 7.2)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(A4[0] / 2.0, 13 * mm,
                                 "%s  •  p. %d" % (footer_text, doc.page))
        canvas.restoreState()
    return draw


def mpl_setup():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 8.0,
        "axes.edgecolor": HEX["grey"],
        "axes.labelcolor": HEX["navy"],
        "axes.titlesize": 9.0,
        "axes.titleweight": "bold",
        "axes.titlecolor": HEX["navy"],
        "xtick.color": HEX["navy"],
        "ytick.color": HEX["navy"],
        "xtick.labelsize": 7.2,
        "ytick.labelsize": 7.2,
        "legend.fontsize": 7.2,
        "legend.frameon": False,
        "figure.dpi": 200,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
    })
    return plt
