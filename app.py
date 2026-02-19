import streamlit as st
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
import feedparser
import random
import requests
import urllib.parse

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

TONE_PROFILES = {
    "Professional": {
        "caption_style": "authoritative, data-driven, expert tone. No hype. Clean insight-led paragraphs.",
        "slide_style": "clear, formal, evidence-based language",
        "temperature": 0.65,
    },
    "Controversial": {
        "caption_style": "provocative and contrarian. Challenge the mainstream view. Open with a statement most people will disagree with. Make them uncomfortable.",
        "slide_style": "bold claims, challenging conventional wisdom, sparking debate",
        "temperature": 0.85,
    },
    "Scary / Urgent": {
        "caption_style": "alarming and urgent. Use fear-of-missing-out, real risk, and urgency. Make the reader feel like they NEED to act now or fall behind.",
        "slide_style": "high-stakes warnings, alarming statistics, urgent calls to action",
        "temperature": 0.80,
    },
    "Motivational": {
        "caption_style": "inspiring and energetic. Stories of transformation. Make the reader believe they can do the same. Real, grounded, not fluffy.",
        "slide_style": "empowering language, transformative insights, action-oriented",
        "temperature": 0.75,
    },
    "Contrarian": {
        "caption_style": "deeply contrarian. Every paragraph should challenge something the reader assumes is true. Use phrases like 'everyone is wrong about this' and 'here is what they are not telling you'.",
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
You are an elite LinkedIn Ghostwriter. Your tone for this post is: {tone.upper()}.

NEWS: {news_item.title}
SUMMARY: {news_item.summary[:2000]}

Output TWO parts separated by "|||".

PART 1: CAPTION
Write a long-form LinkedIn caption (250-300 words) in {profile['caption_style']} style.

Structure:
- Open with a single punchy sentence that grabs attention (tone: {tone}).
- 2-3 short paragraphs with real context, specific insights, and data points.
- A "Here is what most people miss:" section with a sharp take.
- A reflective discussion question.
- 4-5 relevant hashtags on their own line.

STRICT RULES:
- ZERO asterisks (*) in the caption.
- ZERO buzzword fluff (no "pushing boundaries", "making waves", etc.).
- Plain text only. No markdown, no symbols.

|||

PART 2: CAROUSEL SLIDES (5 Slides)
Write in {profile['slide_style']} style.
Each slide body: minimum 55 words. Use *asterisks* to highlight key phrases (PDF rendering only).

Format strictly as:
Slide 1: [Punchy Title matching {tone} tone] | [30-word powerful intro summary]
Slide 2: [Concept Name] | [Detailed paragraph on the problem/challenge. {tone} framing. FILL THE SPACE.]
Slide 3: [Concept Name] | [Detailed paragraph on the solution/insight. WHY it works. FILL THE SPACE.]
Slide 4: [Concept Name] | [Detailed paragraph on future implication. Specific. FILL THE SPACE.]
Slide 5: [The Takeaway] | [Strong summary + Call to Action matching {tone} energy.]
"""
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=profile["temperature"]
    )
    return completion.choices[0].message.content


# ── Image Generation via Pollinations.ai (free, no key needed) ──────────────
def generate_cartoon_image(topic, tone):
    """Fetch a cartoon-style image from Pollinations.ai. Returns BytesIO or None."""
    style_map = {
        "Professional":   "flat vector illustration, corporate infographic, clean minimal style",
        "Controversial":  "bold editorial cartoon, striking graphic novel style, high contrast",
        "Scary / Urgent": "dark dramatic illustration, glowing red warnings, cinematic urgency",
        "Motivational":   "vibrant motivational poster art, sunrise colors, dynamic composition",
        "Contrarian":     "satirical cartoon, thought-provoking infographic, newspaper editorial style",
    }
    style = style_map.get(tone, "flat vector illustration")
    prompt = f"{style}, about: {topic[:120]}, no text, no words, professional digital art"
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=936&height=520&nologo=true&model=flux"
    try:
        resp = requests.get(url, timeout=40)
        if resp.status_code == 200 and "image" in resp.headers.get("content-type", ""):
            return BytesIO(resp.content)
    except Exception:
        pass
    return None


# ============================================================
# DESIGN ENGINE — PREMIUM "OBSIDIAN" THEME
# ============================================================

C_BG_TOP      = colors.HexColor('#0A0F1E')
C_BG_BOT      = colors.HexColor('#060B14')
C_TITLE       = colors.HexColor('#F8FAFC')
C_BODY        = colors.HexColor('#CBD5E1')
C_HIGHLIGHT   = colors.HexColor('#67E8F9')
C_SLIDE_NUM   = colors.HexColor('#1E3A5F')
C_RULE        = colors.HexColor('#334155')
C_TAG_BG      = colors.HexColor('#172554')
C_TAG_TEXT    = colors.HexColor('#93C5FD')

TONE_ACCENTS = {
    "Professional":   colors.HexColor('#2563EB'),
    "Controversial":  colors.HexColor('#DC2626'),
    "Scary / Urgent": colors.HexColor('#B91C1C'),
    "Motivational":   colors.HexColor('#D97706'),
    "Contrarian":     colors.HexColor('#7C3AED'),
}


def draw_background(c, W, H, accent):
    c.setFillColor(C_BG_TOP)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(C_BG_BOT)
    c.rect(0, 0, W, H * 0.35, fill=1, stroke=0)

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

    c.setStrokeColor(C_RULE)
    c.setLineWidth(0.4)
    c.setStrokeAlpha(0.18)
    for y in range(0, H, 120):
        c.line(0, y, W, y)
    c.setStrokeAlpha(1.0)

    c.setFillColor(accent)
    c.rect(0, H - 12, W, 12, fill=1, stroke=0)
    c.rect(0, 0, W, 5, fill=1, stroke=0)

    c.setStrokeColor(accent)
    c.setLineWidth(2.5)
    c.setStrokeAlpha(0.5)
    m, l = 48, 80
    c.line(m, H - m, m + l, H - m)
    c.line(m, H - m, m, H - m - l)
    c.line(W - m, m, W - m - l, m)
    c.line(W - m, m, W - m, m + l)
    c.setStrokeAlpha(1.0)


def wrapped_lines(c, text, font, size, max_width):
    words = text.split()
    lines, current_words, current_w = [], [], 0.0
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


def draw_rich_text(c, text, x, y, max_width, font_size, line_height_ratio=1.55):
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
        current_y -= font_size * 0.4
    return current_y


def draw_slide(c, W, H, slide_num, total_slides, title, body, accent, image_data=None):
    MARGIN_X   = 72
    SAFE_WIDTH = W - MARGIN_X * 2
    TOP_Y      = H - 60

    draw_background(c, W, H, accent)

    # Ghost slide number
    c.setFillColor(C_SLIDE_NUM)
    c.setFont('Helvetica-Bold', 320)
    c.setFillAlpha(0.18)
    c.drawRightString(W - 20, H * 0.08, f'{slide_num:02d}')
    c.setFillAlpha(1.0)

    # Slide counter pill
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

    # ── Slide 1: image in upper section, push title+body below ───
    if slide_num == 1 and image_data is not None:
        img_h = 500
        img_y = TOP_Y - 90 - img_h
        try:
            image_data.seek(0)
            img_reader = ImageReader(image_data)
            c.drawImage(img_reader, MARGIN_X, img_y, width=SAFE_WIDTH, height=img_h,
                        preserveAspectRatio=True, mask='auto')
            c.setStrokeColor(accent)
            c.setLineWidth(3)
            c.line(MARGIN_X, img_y - 10, W - MARGIN_X, img_y - 10)
            title_y_start = img_y - 75
        except Exception:
            title_y_start = TOP_Y - 80
    else:
        title_y_start = TOP_Y - 80

    # Title
    TITLE_FONT_SIZE = 82
    title_leading   = TITLE_FONT_SIZE * 1.15
    c.setFillColor(C_TITLE)
    c.setFont('Helvetica-Bold', TITLE_FONT_SIZE)
    t_lines, curr, curr_w = [], [], 0.0
    for w in title.split():
        ww = c.stringWidth(w + ' ', 'Helvetica-Bold', TITLE_FONT_SIZE)
        if curr_w + ww > SAFE_WIDTH and curr:
            t_lines.append(' '.join(curr)); curr = [w]; curr_w = ww
        else:
            curr.append(w); curr_w += ww
    t_lines.append(' '.join(curr))
    title_y = title_y_start
    for tl in t_lines:
        c.drawString(MARGIN_X, title_y, tl)
        title_y -= title_leading

    # Accent rule
    rule_y = title_y - 24
    c.setStrokeColor(accent)
    c.setLineWidth(6)
    c.line(MARGIN_X, rule_y, MARGIN_X + 200, rule_y)
    c.setStrokeColor(C_RULE)
    c.setLineWidth(1.5)
    c.line(MARGIN_X + 210, rule_y, W - MARGIN_X, rule_y)

    # Body — auto-size to fill remaining space
    body_top_y    = rule_y - 52
    body_bottom_y = 60
    avail_height  = body_top_y - body_bottom_y

    for body_font_size in range(46, 22, -2):
        leading    = body_font_size * 1.55
        test_lines = wrapped_lines(c, body.replace('\n', ' '), 'Helvetica', body_font_size, SAFE_WIDTH)
        if len(test_lines) * leading <= avail_height:
            break

    draw_rich_text(c, body, MARGIN_X, body_top_y, SAFE_WIDTH, body_font_size)


def create_titan_pdf(slide_text, tone, image_data=None):
    buffer = BytesIO()
    W, H   = 1080, 1350
    accent = TONE_ACCENTS.get(tone, colors.HexColor('#2563EB'))

    lines      = slide_text.strip().split('\n')
    slide_data = []
    for line in lines:
        if 'Slide' in line and ':' in line:
            parts = line.split(':', 1)[1].strip()
            title, body = parts.split('|', 1) if '|' in parts else (parts, 'Content loading...')
            slide_data.append((title.strip(), body.strip()))

    if not slide_data:
        slide_data = [("No Content", "Could not parse slides. Try regenerating.")]

    total = len(slide_data)
    c = canvas.Canvas(buffer, pagesize=(W, H))

    for idx, (title, body) in enumerate(slide_data, start=1):
        img = image_data if idx == 1 else None
        draw_slide(c, W, H, idx, total, title, body, accent, image_data=img)
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("📌 Select Niche", list(RSS_FEEDS.keys()))
    tone  = st.selectbox("🎭 Select Tone", list(TONE_PROFILES.keys()))

    tone_descriptions = {
        "Professional":   "📊 Clean, data-driven, executive voice",
        "Controversial":  "🔥 Challenges mainstream views, sparks debate",
        "Scary / Urgent": "⚠️ High-stakes warnings, fear of missing out",
        "Motivational":   "🚀 Inspiring stories, action-oriented energy",
        "Contrarian":     "🧠 Myth-busting, 'what they're not telling you'",
    }
    st.caption(tone_descriptions.get(tone, ""))

    use_image = st.toggle("🎨 Add AI cartoon image to Slide 1", value=True)

    if st.button("🏛️ Generate Titan Post"):
        with st.status("Forging content...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: **{news.title}**")

                image_data = None
                if use_image:
                    st.write("🎨 Generating cartoon image via Pollinations AI...")
                    image_data = generate_cartoon_image(news.title, tone)
                    if image_data:
                        st.write("✅ Image ready")
                    else:
                        st.write("⚠️ Image unavailable — continuing without it")

                st.write("✍️ Writing content...")
                res = generate_content(news, niche, tone)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.session_state['tone']    = tone
                    st.write("🖨️ Painting Obsidian Canvas...")
                    st.session_state['pdf'] = create_titan_pdf(
                        slides.strip(), tone, image_data
                    )
                    st.write("✅ Done!")
                except Exception as e:
                    st.error(f"Parsing error: {e}")
            else:
                st.error("Could not fetch news feed.")

with col2:
    if 'pdf' in st.session_state:
        tone_badge = st.session_state.get('tone', '')
        st.subheader(f"Caption  ·  {tone_badge} tone")
        st.text_area("Copy this caption:", st.session_state['caption'], height=260)
        st.download_button(
            "📥 Download Titan PDF",
            st.session_state['pdf'],
            "titan_carousel.pdf",
            mime="application/pdf"
        )
