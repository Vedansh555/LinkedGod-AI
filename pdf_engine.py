"""
pdf_engine.py — the "Obsidian" carousel renderer.

Turns a list of {"title": str, "body": str} slides into a polished,
LinkedIn-ready PDF carousel (1080x1350 portrait). Wrap words in the
body text with *asterisks* to highlight them in cyan.
"""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
C_BG_TOP = colors.HexColor("#0A0F1E")
C_BG_BOT = colors.HexColor("#060B14")
C_ACCENT_LINE = colors.HexColor("#2563EB")
C_TITLE = colors.HexColor("#F8FAFC")
C_BODY = colors.HexColor("#CBD5E1")
C_HIGHLIGHT = colors.HexColor("#67E8F9")
C_SLIDE_NUM = colors.HexColor("#1E3A5F")
C_RULE = colors.HexColor("#334155")
C_TAG_BG = colors.HexColor("#172554")
C_TAG_TEXT = colors.HexColor("#93C5FD")

PAGE_SIZE = (1080, 1350)  # LinkedIn carousel portrait
MARGIN_X = 72


def _draw_background(c: canvas.Canvas, w: float, h: float) -> None:
    c.setFillColor(C_BG_TOP)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    c.setFillColor(C_BG_BOT)
    c.rect(0, 0, w, h * 0.35, fill=1, stroke=0)

    glow_colors = ["#0F2A6B", "#0C2157", "#091A44", "#061330"]
    alphas = [0.22, 0.14, 0.08, 0.04]
    sizes = [600, 800, 950, 1100]
    cx, cy = w / 2, h - 80
    for col_hex, alpha, size in zip(glow_colors, alphas, sizes):
        c.setFillColor(colors.HexColor(col_hex))
        c.setFillAlpha(alpha)
        half = size / 2
        c.rect(cx - half, cy - half * 0.6, size, size * 0.6, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.4)
    c.setStrokeAlpha(0.25)
    for y in range(0, int(h), 120):
        c.line(0, y, w, y)
    c.setStrokeAlpha(1.0)

    c.setFillColor(C_ACCENT_LINE)
    c.rect(0, h - 12, w, 12, fill=1, stroke=0)
    c.rect(0, 0, w, 5, fill=1, stroke=0)

    c.setStrokeColor(C_ACCENT_LINE)
    c.setLineWidth(2.5)
    c.setStrokeAlpha(0.5)
    m, l = 48, 80
    c.line(m, h - m, m + l, h - m)
    c.line(m, h - m, m, h - m - l)
    c.line(w - m, m, w - m - l, m)
    c.line(w - m, m, w - m, m + l)
    c.setStrokeAlpha(1.0)


def _wrapped_words(c: canvas.Canvas, text: str, font: str, size: float, max_width: float):
    """Greedy word-wrap that also tags each word bold/not for *highlight* rendering."""
    words = text.split()
    lines: list[list[tuple[str, bool]]] = []
    current: list[tuple[str, bool]] = []
    current_w = 0.0
    for word in words:
        clean = word.replace("*", "")
        w = c.stringWidth(clean + " ", font, size)
        if current_w + w > max_width and current:
            lines.append(current)
            current, current_w = [(word, "*" in word)], w
        else:
            current.append((word, "*" in word))
            current_w += w
    if current:
        lines.append(current)
    return lines


def _draw_rich_text(
    c: canvas.Canvas, text: str, x: float, y: float, max_width: float, font_size: float, line_height_ratio: float = 1.55
) -> float:
    """Draws `text`, rendering *word* as bold cyan. Returns the final y position."""
    leading = font_size * line_height_ratio
    y_cursor = y
    for para in (p for p in text.split("\n") if p.strip()):
        for word_list in _wrapped_words(c, para, "Helvetica", font_size, max_width):
            cursor_x = x
            for word, is_bold in word_list:
                clean = word.replace("*", "")
                font = "Helvetica-Bold" if is_bold else "Helvetica"
                c.setFillColor(C_HIGHLIGHT if is_bold else C_BODY)
                c.setFont(font, font_size)
                c.drawString(cursor_x, y_cursor, clean)
                cursor_x += c.stringWidth(clean + " ", font, font_size)
            y_cursor -= leading
        y_cursor -= font_size * 0.4  # paragraph gap
    return y_cursor


def _draw_slide(c: canvas.Canvas, w: float, h: float, slide_num: int, total: int, title: str, body: str) -> None:
    safe_width = w - MARGIN_X * 2
    top_y = h - 60

    _draw_background(c, w, h)

    # Ghost slide number
    c.setFillColor(C_SLIDE_NUM)
    c.setFont("Helvetica-Bold", 320)
    c.setFillAlpha(0.18)
    c.drawRightString(w - 20, h * 0.08, f"{slide_num:02d}")
    c.setFillAlpha(1.0)

    # Slide counter pill
    pill_label = f"{slide_num} / {total}"
    pill_font_size = 28
    pw = c.stringWidth(pill_label, "Helvetica-Bold", pill_font_size) + 36
    ph = 48
    px = w - MARGIN_X - pw
    py = top_y - ph - 10
    c.setFillColor(C_TAG_BG)
    c.roundRect(px, py, pw, ph, 14, fill=1, stroke=0)
    c.setFillColor(C_TAG_TEXT)
    c.setFont("Helvetica-Bold", pill_font_size)
    c.drawCentredString(px + pw / 2, py + 12, pill_label)

    # Title (auto-wrapped)
    title_font_size = 82
    title_leading = title_font_size * 1.15
    title_y = top_y - 80

    c.setFillColor(C_TITLE)
    c.setFont("Helvetica-Bold", title_font_size)
    t_lines, curr, curr_w = [], [], 0.0
    for word in title.split():
        ww = c.stringWidth(word + " ", "Helvetica-Bold", title_font_size)
        if curr_w + ww > safe_width and curr:
            t_lines.append(" ".join(curr))
            curr, curr_w = [word], ww
        else:
            curr.append(word)
            curr_w += ww
    t_lines.append(" ".join(curr))

    for line in t_lines:
        c.drawString(MARGIN_X, title_y, line)
        title_y -= title_leading

    # Accent rule
    rule_y = title_y - 24
    c.setStrokeColor(C_ACCENT_LINE)
    c.setLineWidth(6)
    c.line(MARGIN_X, rule_y, MARGIN_X + 200, rule_y)
    c.setStrokeColor(C_RULE)
    c.setLineWidth(1.5)
    c.line(MARGIN_X + 210, rule_y, w - MARGIN_X, rule_y)

    # Body — pick the largest font size that still fits the remaining space
    body_top_y = rule_y - 52
    body_bottom_y = 60
    avail_height = body_top_y - body_bottom_y

    body_font_size = 26
    for size in range(46, 24, -2):
        leading = size * 1.55
        test_lines = _wrapped_words(c, body.replace("\n", " "), "Helvetica", size, safe_width)
        if len(test_lines) * leading <= avail_height:
            body_font_size = size
            break

    _draw_rich_text(c, body, MARGIN_X, body_top_y, safe_width, body_font_size)


def create_carousel_pdf(slides: list[dict]) -> bytes:
    """Render a list of {"title", "body"} slides into a PDF carousel and
    return the raw PDF bytes (safe to store/re-use across Streamlit reruns,
    unlike a BytesIO whose read cursor can be left exhausted)."""
    if not slides:
        slides = [{"title": "No Content", "body": "Nothing to render — try regenerating."}]

    buffer = BytesIO()
    w, h = PAGE_SIZE
    c = canvas.Canvas(buffer, pagesize=(w, h))
    total = len(slides)
    for idx, slide in enumerate(slides, start=1):
        _draw_slide(c, w, h, idx, total, slide["title"], slide["body"])
        c.showPage()
    c.save()
    return buffer.getvalue()
