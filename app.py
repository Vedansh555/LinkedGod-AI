import streamlit as st
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
import feedparser
import random
import textwrap
import re

# --- CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("⚠️ GROQ_API_KEY missing. Please add it to Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="LinkedGod: Titan", layout="wide")
st.title("🏛️ LinkedGod: Titan Edition")
st.markdown("Generates **Massive Text** slides that actually fill the screen.")

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/",
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss"
}

# --- TONE PROFILES (only addition) ---
TONE_PROFILES = {
    "Professional": {
        "caption_style": "authoritative, data-driven, expert tone. No hype. Clean insight-led paragraphs.",
        "slide_style": "clear, formal, evidence-based language",
        "temperature": 0.65,
    },
    "Controversial": {
        "caption_style": "provocative and contrarian. Challenge the mainstream view. Open with a statement most people will disagree with. Make them uncomfortable enough to comment.",
        "slide_style": "bold claims, challenging conventional wisdom, sparking debate",
        "temperature": 0.85,
    },
    "Scary / Urgent": {
        "caption_style": "alarming and urgent. Use real risk and fear of missing out. Make the reader feel they NEED to act now or fall behind permanently.",
        "slide_style": "high-stakes warnings, alarming statistics, urgent calls to action",
        "temperature": 0.80,
    },
    "Motivational": {
        "caption_style": "inspiring and energetic. Stories of real transformation. Make the reader believe they can do the same. Grounded, not fluffy.",
        "slide_style": "empowering language, transformative insights, action-oriented",
        "temperature": 0.75,
    },
    "Contrarian": {
        "caption_style": "deeply contrarian. Every paragraph challenges something the reader assumes is true. Use angles like 'everyone is wrong about this' and 'here is what they are not telling you'.",
        "slide_style": "myth-busting framing, unpopular truth hooks, counterintuitive insights",
        "temperature": 0.90,
    },
}


def get_random_news(niche):
    feed = feedparser.parse(RSS_FEEDS.get(niche))
    if feed.entries:
        limit = min(len(feed.entries), 10)
        return random.choice(feed.entries[:limit])
    return None


def generate_content(news_item, niche, tone):
    profile = TONE_PROFILES[tone]
    prompt = f"""
You are an elite LinkedIn Ghostwriter. Tone for this post: {tone.upper()}.

NEWS: {news_item.title}
SUMMARY: {news_item.summary[:2000]}

Output TWO parts separated by "|||".

PART 1: CAPTION
Write a hook-first, SEO-optimised LinkedIn caption (280-320 words) in {profile['caption_style']} style, built for maximum organic reach.

Structure:
- LINE 1 — THE HOOK: One sentence, MAX 12 words. Must create curiosity, tension, or shock. End with a colon or ellipsis to force "see more" clicks. This is the most critical line.
- [blank line]
- THE STORY: 3 short paragraphs (2-3 sentences each), blank line between each. Include a real stat or number. Surprising angle.
- [blank line]
- "Here is what nobody is talking about:" — sharpest counterintuitive take in 2 sentences.
- [blank line]
- One direct debate-sparking question to the reader.
- [blank line]
- HASHTAGS: Exactly 8 hashtags on one line. Mix: 2 mega tags (1M+ like #leadership #innovation), 3 mid-tier niche tags (100K-500K), 3 hyper-specific topic tags for SEO discovery.

STRICT RULES FOR CAPTION:
- ZERO asterisks (*) anywhere in the caption.
- Hook line must be under 12 words. Non-negotiable.
- ZERO fluff (no "pushing boundaries", "making waves", "game changer", "poised for success").
- Plain text only. No markdown, no bullet points, no symbols except hashtags.

|||

PART 2: CAROUSEL SLIDES (5 Slides)
- Write LONG, DETAILED paragraphs. Each slide body must be at least 50-60 words.
- Use *asterisks* only inside slide body text to highlight key phrases (this is for PDF rendering).
- Write slides in {profile['slide_style']} style matching the {tone} tone.
- Format strictly as:

Slide 1: [Punchy Title] | [Write a 30-word powerful intro summary]
Slide 2: [Concept Name] | [Write a detailed paragraph explaining the problem. Use strong language. FILL THE SPACE.]
Slide 3: [Concept Name] | [Write a detailed paragraph explaining the solution. Explain WHY it works. FILL THE SPACE.]
Slide 4: [Concept Name] | [Write a detailed paragraph about the future implication. Be specific. FILL THE SPACE.]
Slide 5: [The Takeaway] | [Write a strong summary paragraph and a clear Call to Action.]
"""
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=profile["temperature"]
    )
    return completion.choices[0].message.content


# ============================================================
# DESIGN ENGINE — PREMIUM "OBSIDIAN" THEME
# ============================================================

# Palette
C_BG_TOP        = colors.HexColor('#0A0F1E')   # Deep navy-black (top)
C_BG_BOT        = colors.HexColor('#060B14')   # Almost pure black (bottom)
C_ACCENT_LINE   = colors.HexColor('#2563EB')   # Electric blue accent bar
C_ACCENT_GLOW   = colors.HexColor('#1D4ED8')   # Darker blue for glow rect
C_TITLE         = colors.HexColor('#F8FAFC')   # Near-white title
C_BODY          = colors.HexColor('#CBD5E1')   # Soft slate body text
C_HIGHLIGHT     = colors.HexColor('#67E8F9')   # Light cyan for *bold* words
C_SLIDE_NUM     = colors.HexColor('#1E3A5F')   # Dark-blue ghost number
C_RULE          = colors.HexColor('#334155')   # Subtle divider
C_TAG_BG        = colors.HexColor('#172554')   # Tag / pill background
C_TAG_TEXT      = colors.HexColor('#93C5FD')   # Tag text (light blue)


def draw_background(c, W, H):
    """Gradient-like background using 3 rects + subtle corner geometry."""
    # Base fill
    c.setFillColor(C_BG_TOP)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Subtle bottom darkening panel
    c.setFillColor(C_BG_BOT)
    c.rect(0, 0, W, H * 0.35, fill=1, stroke=0)

    # Very subtle blue radial glow near top-center (layered large rects with alpha)
    glow_colors = ['#0F2A6B', '#0C2157', '#091A44', '#061330']
    alphas      = [0.22, 0.14, 0.08, 0.04]
    sizes       = [600, 800, 950, 1100]
    cx, cy = W / 2, H - 80
    for col_hex, alpha, size in zip(glow_colors, alphas, sizes):
        c.setFillColor(colors.HexColor(col_hex))
        c.setFillAlpha(alpha)
        half = size / 2
        c.rect(cx - half, cy - half * 0.6, size, size * 0.6, fill=1, stroke=0)
    c.setFillAlpha(1.0)

    # Thin grid lines (very subtle)
    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.4)
    c.setStrokeAlpha(0.25)
    for y in range(0, H, 120):
        c.line(0, y, W, y)
    c.setStrokeAlpha(1.0)

    # Top accent bar (electric blue, full width)
    c.setFillColor(C_ACCENT_LINE)
    c.rect(0, H - 12, W, 12, fill=1, stroke=0)

    # Bottom accent bar (thinner)
    c.setFillColor(C_ACCENT_LINE)
    c.rect(0, 0, W, 5, fill=1, stroke=0)

    # Corner bracket — top-left only (decorative)
    c.setStrokeColor(C_ACCENT_LINE)
    c.setLineWidth(2.5)
    c.setStrokeAlpha(0.5)
    m, l = 48, 80
    c.line(m, H - m, m + l, H - m)
    c.line(m, H - m, m, H - m - l)
    # Bottom-right
    c.line(W - m, m, W - m - l, m)
    c.line(W - m, m, W - m, m + l)
    c.setStrokeAlpha(1.0)


def wrapped_lines(c, text, font, size, max_width):
    """Return a list of (line_str, [(word, is_bold), ...]) tuples."""
    words = text.split()
    lines = []
    current_words = []
    current_w = 0.0

    for word in words:
        clean = word.replace('*', '')
        w = c.stringWidth(clean + ' ', font, size)
        if current_w + w > max_width and current_words:
            lines.append(current_words)
            current_words = [(word, '*' in word)]
            current_w = w
        else:
            current_words.append((word, '*' in word))
            current_w += w
    if current_words:
        lines.append(current_words)
    return lines


def draw_rich_text(c, text, x, y, max_width, font_size, line_height_ratio=1.5):
    """
    Renders text with *bold-cyan* highlights.
    Returns the final Y position after all text is drawn.
    """
    leading = font_size * line_height_ratio
    paragraphs = [p for p in text.split('\n') if p.strip()]

    current_y = y
    for para in paragraphs:
        lines = wrapped_lines(c, para, 'Helvetica', font_size, max_width)
        for word_list in lines:
            cursor_x = x
            for word, is_bold in word_list:
                clean = word.replace('*', '')
                if is_bold:
                    c.setFillColor(C_HIGHLIGHT)
                    c.setFont('Helvetica-Bold', font_size)
                else:
                    c.setFillColor(C_BODY)
                    c.setFont('Helvetica', font_size)
                c.drawString(cursor_x, current_y, clean)
                f = 'Helvetica-Bold' if is_bold else 'Helvetica'
                cursor_x += c.stringWidth(clean + ' ', f, font_size)
            current_y -= leading
        current_y -= font_size * 0.4   # paragraph gap
    return current_y


def draw_slide(c, W, H, slide_num, total_slides, title, body):
    """Render a single slide page."""
    MARGIN_X   = 72
    SAFE_WIDTH = W - MARGIN_X * 2
    TOP_Y      = H - 60   # just below top accent bar

    draw_background(c, W, H)

    # ── Ghost slide number (background) ──────────────────────────
    c.setFillColor(C_SLIDE_NUM)
    c.setFont('Helvetica-Bold', 320)
    c.setFillAlpha(0.18)
    c.drawRightString(W - 20, H * 0.08, f'{slide_num:02d}')
    c.setFillAlpha(1.0)

    # ── Slide counter pill (top-right) ──────────────────────────
    pill_label = f'{slide_num} / {total_slides}'
    pill_font_size = 28
    pw = c.stringWidth(pill_label, 'Helvetica-Bold', pill_font_size) + 36
    ph = 48
    px = W - MARGIN_X - pw
    py = TOP_Y - ph - 10
    c.setFillColor(C_TAG_BG)
    c.roundRect(px, py, pw, ph, 14, fill=1, stroke=0)
    c.setFillColor(C_TAG_TEXT)
    c.setFont('Helvetica-Bold', pill_font_size)
    c.drawCentredString(px + pw / 2, py + 12, pill_label)

    # ── Title ────────────────────────────────────────────────────
    TITLE_FONT_SIZE = 82
    title_leading   = TITLE_FONT_SIZE * 1.15
    title_y_start   = TOP_Y - 80

    c.setFillColor(C_TITLE)
    c.setFont('Helvetica-Bold', TITLE_FONT_SIZE)

    # Wrap title
    t_lines = []
    t_words = title.split()
    curr = []
    curr_w = 0.0
    for w in t_words:
        ww = c.stringWidth(w + ' ', 'Helvetica-Bold', TITLE_FONT_SIZE)
        if curr_w + ww > SAFE_WIDTH and curr:
            t_lines.append(' '.join(curr))
            curr = [w]; curr_w = ww
        else:
            curr.append(w); curr_w += ww
    t_lines.append(' '.join(curr))

    title_y = title_y_start
    for tl in t_lines:
        c.drawString(MARGIN_X, title_y, tl)
        title_y -= title_leading

    # ── Accent rule ───────────────────────────────────────────────
    rule_y = title_y - 24
    c.setStrokeColor(C_ACCENT_LINE)
    c.setLineWidth(6)
    c.line(MARGIN_X, rule_y, MARGIN_X + 200, rule_y)
    c.setStrokeColor(C_RULE)
    c.setLineWidth(1.5)
    c.line(MARGIN_X + 210, rule_y, W - MARGIN_X, rule_y)

    # ── Body text ─────────────────────────────────────────────────
    # Dynamically choose font size to fill available vertical space
    body_top_y    = rule_y - 52
    body_bottom_y = 60   # keep above bottom accent bar
    avail_height  = body_top_y - body_bottom_y

    # Try sizes from large down until text fits
    for body_font_size in range(46, 24, -2):
        leading       = body_font_size * 1.55
        # Estimate number of lines
        test_lines    = wrapped_lines(c, body.replace('\n', ' '), 'Helvetica', body_font_size, SAFE_WIDTH)
        total_height  = len(test_lines) * leading
        if total_height <= avail_height:
            break

    draw_rich_text(c, body, MARGIN_X, body_top_y, SAFE_WIDTH, body_font_size, line_height_ratio=1.55)


def create_titan_pdf(slide_text):
    buffer = BytesIO()
    W, H   = 1080, 1350  # LinkedIn carousel portrait

    lines       = slide_text.strip().split('\n')
    slide_data  = []

    for line in lines:
        if 'Slide' in line and ':' in line:
            parts = line.split(':', 1)[1].strip()
            if '|' in parts:
                title, body = parts.split('|', 1)
            else:
                title, body = parts, 'Content loading...'
            slide_data.append((title.strip(), body.strip()))

    if not slide_data:
        slide_data = [("No Content", "Could not parse slides. Try regenerating.")]

    total = len(slide_data)
    c = canvas.Canvas(buffer, pagesize=(W, H))

    for idx, (title, body) in enumerate(slide_data, start=1):
        draw_slide(c, W, H, idx, total, title, body)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))

    # Tone selector (only new UI element)
    tone = st.selectbox("🎭 Select Tone", list(TONE_PROFILES.keys()))
    tone_descriptions = {
        "Professional":   "📊 Data-driven, executive voice",
        "Controversial":  "🔥 Challenges mainstream views, sparks debate",
        "Scary / Urgent": "⚠️ High-stakes warnings, fear of missing out",
        "Motivational":   "🚀 Inspiring stories, action-oriented energy",
        "Contrarian":     "🧠 Myth-busting, 'what they're not telling you'",
    }
    st.caption(tone_descriptions.get(tone, ""))

    if st.button("🏛️ Generate Titan Post"):
        with st.status("Forging content...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche, tone)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.write("🎨 Painting Obsidian Canvas...")
                    st.session_state['pdf'] = create_titan_pdf(slides.strip())
                    st.write("✅ Done!")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button(
            "📥 Download Titan PDF",
            st.session_state['pdf'],
            "titan_carousel.pdf",
            mime="application/pdf"
        )
