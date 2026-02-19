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
    SUMMARY: {news_item.summary[:2000]}
    
    Output TWO parts separated by "|||".
    
    PART 1: CAPTION
    - Detailed Storytelling style (200 words).
    
    |||
    
    PART 2: CAROUSEL SLIDES (5 Slides)
    - IMPORTANT: Write LONG, DETAILED paragraphs. 
    - Each slide must have at least 50-60 words.
    - Use *asterisks* to highlight key phrases.
    
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
        temperature=0.7 
    )
    return completion.choices[0].message.content

# --- DESIGN ENGINE (SPOTLIGHT MODE) ---

def draw_background(c, width, height):
    """Draws a premium 'Spotlight' Radial Gradient"""
    # 1. Base Dark Background
    c.setFillColor(colors.HexColor('#020617')) # Almost Black
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # 2. "Spotlight" Circle (Simulated Gradient)
    # We draw massive concentric circles with decreasing opacity
    center_x, center_y = width/2, height/2
    max_radius = width * 1.2
    
    # Dark Blue Glow
    c.setFillColor(colors.HexColor('#1E3A8A')) # Dark Blue
    c.setFillAlpha(0.03) # Very subtle
    
    for r in range(int(max_radius), 0, -20):
        c.circle(center_x, center_y, r, fill=1, stroke=0)
        
    c.setFillAlpha(1) # Reset

    # 3. Geometric Accents (The "Tech" Look)
    c.setStrokeColor(colors.HexColor('#334155'))
    c.setLineWidth(2)
    
    # Corner brackets
    m = 60 # Margin
    l = 100 # Length
    # Top Left
    c.line(m, height-m, m+l, height-m)
    c.line(m, height-m, m, height-m-l)
    # Bottom Right
    c.line(width-m, m, width-m-l, m)
    c.line(width-m, m, width-m, m+l)

def draw_text_block(c, text, x, y, width, font_size):
    """
    Draws text with Gold Highlights
    """
    c.setFont("Helvetica", font_size)
    leading = font_size * 1.4 # Space between lines
    
    paragraphs = text.split('\n')
    current_y = y
    
    for para in paragraphs:
        if not para.strip(): continue
        
        words = para.split(' ')
        current_line = []
        current_w = 0
        
        for word in words:
            clean_word = word.replace('*', '')
            w = c.stringWidth(clean_word + " ", "Helvetica", font_size)
            
            if current_w + w > width:
                # DRAW LINE
                cursor_x = x
                for w_word in current_line:
                    is_bold = '*' in w_word
                    clean = w_word.replace('*', '')
                    
                    if is_bold:
                        c.setFillColor(colors.HexColor('#FBBF24')) # Bright Gold
                        c.setFont("Helvetica-Bold", font_size)
                    else:
                        c.setFillColor(colors.HexColor('#E2E8F0')) # Bright White/Grey
                        c.setFont("Helvetica", font_size)
                        
                    c.drawString(cursor_x, current_y, clean)
                    f_font = "Helvetica-Bold" if is_bold else "Helvetica"
                    cursor_x += c.stringWidth(clean + " ", f_font, font_size)
                
                current_line = [word]
                current_w = w
                current_y -= leading
            else:
                current_line.append(word)
                current_w += w
        
        # Draw last line
        cursor_x = x
        for w_word in current_line:
            is_bold = '*' in w_word
            clean = w_word.replace('*', '')
            if is_bold:
                c.setFillColor(colors.HexColor('#FBBF24'))
                c.setFont("Helvetica-Bold", font_size)
            else:
                c.setFillColor(colors.HexColor('#E2E8F0'))
                c.setFont("Helvetica", font_size)
            c.drawString(cursor_x, current_y, clean)
            f_font = "Helvetica-Bold" if is_bold else "Helvetica"
            cursor_x += c.stringWidth(clean + " ", f_font, font_size)
            
        current_y -= (leading * 1.2)

def create_titan_pdf(slide_text):
    buffer = BytesIO()
    W, H = 1080, 1350 # Portrait
    c = canvas.Canvas(buffer, pagesize=(W, H))
    
    lines = slide_text.strip().split('\n')
    slide_num = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            parts = line.split(":", 1)[1].strip()
            if "|" in parts:
                title, body = parts.split("|", 1)
            else:
                title, body = parts, "Content loading..."
                
            title = title.strip()
            body = body.strip()
            
            draw_background(c, W, H)
            
            # 1. Slide Number
            c.setFillColor(colors.HexColor('#334155'))
            c.setFont("Helvetica-Bold", 100)
            c.drawRightString(W - 60, H - 120, f"{slide_num:02d}")
            
            # 2. Title (Massive)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 85)
            
            # Simple Title Wrap
            title_words = title.split()
            title_lines = []
            curr_line = []
            curr_w = 0
            for word in title_words:
                w = c.stringWidth(word + " ", "Helvetica-Bold", 85)
                if curr_w + w > 900:
                    title_lines.append(" ".join(curr_line))
                    curr_line = [word]
                    curr_w = w
                else:
                    curr_line.append(word)
                    curr_w += w
            title_lines.append(" ".join(curr_line))
            
            title_y = H - 220
            for t in title_lines:
                c.drawString(80, title_y, t)
                title_y -= 95
            
            # 3. Gold Bar
            c.setStrokeColor(colors.HexColor('#F59E0B'))
            c.setLineWidth(8)
            c.line(80, title_y - 20, 350, title_y - 20)
            
            # 4. Body Text (The Fix: HUGE Font)
            # Font size 48 is very large. It will fill the page.
            draw_text_block(c, body, 80, title_y - 120, 920, 48)
            
            c.showPage()
            slide_num += 1
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    if st.button("🏛️ Generate Titan Post"):
        with st.status("Forging content...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.write("🎨 Painting Huge Canvas...")
                    st.session_state['pdf'] = create_titan_pdf(slides.strip())
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download Titan PDF", st.session_state['pdf'], "titan_carousel.pdf")
