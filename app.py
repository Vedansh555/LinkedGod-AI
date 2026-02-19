import streamlit as st
from groq import Groq
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
st.title("🏛️ LinkedGod: Typography Titan")
st.markdown("Generates **4:5 Portrait Carousels** (Mobile Optimized). No Images. Pure Design.")

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/", 
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss"
}

def get_random_news(niche):
    feed = feedparser.parse(RSS_FEEDS.get(niche))
    if feed.entries:
        limit = min(len(feed.entries), 10)
        return random.choice(feed.entries[:limit]) 
    return None

def generate_content(news_item, niche):
    prompt = f"""
    You are a viral LinkedIn Ghostwriter.
    NEWS: {news_item.title}
    SUMMARY: {news_item.summary[:1500]}
    
    Output TWO parts separated by "|||".
    
    PART 1: CAPTION
    - Hook + Body + 3 Hashtags.
    
    |||
    
    PART 2: CAROUSEL SLIDES (5 Slides)
    - IMPORTANT: Use the pipe symbol '|' to separate Title and Body.
    - WRITING RULES:
      - Use *asterisks* to highlight key words (e.g. "AI is *dangerous*").
      - Body must be 3-4 bullet points or short punchy sentences.
      
    - Format strictly as:
      Slide 1: [Short Title] | [Subtitle with *highlight*]
      Slide 2: [Main Point] | [Bullet 1 with *highlight* \n Bullet 2 \n Bullet 3]
      Slide 3: [Main Point] | [Bullet 1 \n Bullet 2 with *highlight* \n Bullet 3]
      Slide 4: [Main Point] | [Bullet 1 \n Bullet 2 \n Bullet 3 with *highlight*]
      Slide 5: [The Takeaway] | [Strong conclusion and CTA]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.8
    )
    return completion.choices[0].message.content

# --- THE GEOMETRIC BACKGROUND ENGINE (NO INTERNET REQUIRED) ---
def draw_background(c, width, height):
    """Draws a premium dark gradient + subtle grid"""
    
    # 1. Base Dark Navy
    c.setFillColor(colors.HexColor('#0B1120')) # Deepest Blue/Black
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # 2. Subtle Grid Pattern
    c.setStrokeColor(colors.HexColor('#1E293B'))
    c.setLineWidth(1)
    step = 100
    for x in range(0, int(width), step):
        c.line(x, 0, x, height)
    for y in range(0, int(height), step):
        c.line(0, y, width, y)
        
    # 3. Top Gradient Accent (Blue Glow)
    p = c.beginPath()
    p.moveTo(0, height)
    p.lineTo(width, height)
    p.lineTo(width, height - 200)
    p.lineTo(0, height - 50)
    p.close()
    c.setFillColor(colors.HexColor('#1D4ED8')) # Electric Blue
    c.setFillAlpha(0.2)
    c.drawPath(p, fill=1, stroke=0)
    c.setFillAlpha(1)

def draw_highlighted_text(c, text, x, y, width, font_size, align="left"):
    """Parses text for *bold* and draws it in GOLD color"""
    
    c.setFont("Helvetica", font_size)
    leading = font_size * 1.4
    words = text.split(" ")
    
    current_line = []
    current_width = 0
    
    # Simple word wrapper logic
    lines = []
    for word in words:
        # Check width
        w = c.stringWidth(word + " ", "Helvetica", font_size)
        if current_width + w > width:
            lines.append(current_line)
            current_line = [word]
            current_width = w
        else:
            current_line.append(word)
            current_width += w
    lines.append(current_line)
    
    # Draw Lines
    for line_words in lines:
        if align == "center":
            # Calculate total line width to center it
            line_str = " ".join(line_words).replace("*", "")
            total_w = c.stringWidth(line_str, "Helvetica", font_size)
            cursor_x = (1080 - total_w) / 2 # Center of 1080 canvas
        else:
            cursor_x = x
            
        for word in line_words:
            # Check for highlight
            clean_word = word.replace("\n", "")
            is_highlight = "*" in clean_word
            clean_word = clean_word.replace("*", "")
            
            if is_highlight:
                c.setFillColor(colors.HexColor('#F59E0B')) # GOLD Highlight
                c.setFont("Helvetica-Bold", font_size)
            else:
                c.setFillColor(colors.HexColor('#F8FAFC')) # White/Grey
                c.setFont("Helvetica", font_size)
                
            c.drawString(cursor_x, y, clean_word)
            cursor_x += c.stringWidth(clean_word + " ", "Helvetica", font_size) if not is_highlight else c.stringWidth(clean_word + " ", "Helvetica-Bold", font_size)
            
        y -= leading
        
    return y # Return new Y position

def create_portrait_pdf(slide_text):
    buffer = BytesIO()
    # 4:5 Aspect Ratio (1080x1350) - Standard LinkedIn Portrait
    W, H = 1080, 1350
    c = canvas.Canvas(buffer, pagesize=(W, H))
    
    lines = slide_text.strip().split('\n')
    slide_num = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            parts = line.split(":", 1)[1].strip()
            # Split Title | Body
            if "|" in parts:
                title, body = parts.split("|", 1)
            else:
                title, body = parts, "Swipe to read more"
                
            title = title.strip()
            body = body.strip().replace(r"\n", "\n") # Handle newlines
            
            # --- DRAW SLIDE ---
            draw_background(c, W, H)
            
            # 1. Slide Number (Top Right)
            c.setFillColor(colors.HexColor('#334155'))
            c.setFont("Helvetica-Bold", 60)
            c.drawRightString(W - 50, H - 80, f"{slide_num:02d}")
            
            # 2. Title (Big, Top Left)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 70) # Massive Title
            
            # Wrap Title
            title_obj = c.beginText(60, H - 250)
            title_obj.setFont("Helvetica-Bold", 70)
            title_lines = textwrap.wrap(title, width=18)
            for t_line in title_lines:
                title_obj.textLine(t_line)
            c.drawText(title_obj)
            
            # 3. Accent Line
            y_pos = H - 250 - (len(title_lines)*80)
            c.setStrokeColor(colors.HexColor('#F59E0B')) # Gold
            c.setLineWidth(6)
            c.line(60, y_pos, 260, y_pos)
            
            # 4. Body Text (The "Good Amount of Text")
            # We treat '\n' as line breaks
            body_parts = body.split('\n')
            
            text_y = y_pos - 100
            for part in body_parts:
                part = part.strip()
                if not part: continue
                # Draw bullet symbol
                c.setFillColor(colors.HexColor('#3B82F6')) # Blue bullet
                c.setFont("Helvetica-Bold", 40)
                c.drawString(60, text_y, "•")
                
                # Draw highlighted text
                # We offset X by 50px to make room for bullet
                new_y = draw_highlighted_text(c, part, 110, text_y, 850, 45, align="left")
                text_y = new_y - 30 # Extra spacing between bullets
            
            # 5. Swipe Arrow (Bottom)
            if slide_num < 5:
                c.setFillColor(colors.white)
                c.setFont("Helvetica", 30)
                c.drawCentredString(W/2, 60, "Swipe ➜")
            
            c.showPage()
            slide_num += 1
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    if st.button("🏛️ Generate Portrait Carousel"):
        with st.status("Architecting content...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.write("🎨 Rendering 1080x1350 Canvas...")
                    st.session_state['pdf'] = create_portrait_pdf(slides.strip())
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download Portrait PDF (Mobile Ready)", st.session_state['pdf'], "portrait_carousel.pdf")
