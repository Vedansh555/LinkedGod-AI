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

st.set_page_config(page_title="LinkedGod: Dense", layout="wide")
st.title("📚 LinkedGod: Deep Dive Edition")
st.markdown("Generates **Text-Heavy, High-Value Carousels** that fill the page.")

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
    - IMPORTANT: You MUST write long, detailed slides. 
    - DO NOT use short bullet points. Use full sentences.
    - Each slide must have 60-80 words of body text.
    - Use *asterisks* to highlight key phrases.
    
    - Format strictly as:
      Slide 1: [Punchy Title] | [Write a 30-word powerful intro summary]
      Slide 2: [Concept Name] | [Write a detailed paragraph explaining the problem. Then add a "Key Insight" sentence. FILL THE SPACE.]
      Slide 3: [Concept Name] | [Write a detailed paragraph explaining the solution. Explain WHY it works. FILL THE SPACE.]
      Slide 4: [Concept Name] | [Write a detailed paragraph about the future implication. Be specific. FILL THE SPACE.]
      Slide 5: [The Takeaway] | [Write a strong summary paragraph and a clear Call to Action.]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.7 # Slightly lower temp for more focused writing
    )
    return completion.choices[0].message.content

# --- DESIGN ENGINE (DENSE MODE) ---

def draw_background(c, width, height):
    # Dark Navy Professional BG
    c.setFillColor(colors.HexColor('#0F172A')) 
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Grid
    c.setStrokeColor(colors.HexColor('#1E293B'))
    c.setLineWidth(1)
    for x in range(0, int(width), 100):
        c.line(x, 0, x, height)
    for y in range(0, int(height), 100):
        c.line(0, y, width, y)

def draw_text_block(c, text, x, y, width, font_size):
    """
    Draws a dense block of text with highlighting.
    Handles wrapping for long paragraphs.
    """
    c.setFont("Helvetica", font_size)
    leading = font_size * 1.5 # Space between lines
    
    # Split by logical breaks if AI sends newlines, else treat as one block
    paragraphs = text.split('\n')
    
    current_y = y
    
    for para in paragraphs:
        if not para.strip(): continue
        
        # Split paragraph into words
        words = para.split(' ')
        current_line = []
        current_w = 0
        
        for word in words:
            # Measure word (remove * for measurement)
            clean_word = word.replace('*', '')
            w = c.stringWidth(clean_word + " ", "Helvetica", font_size)
            
            if current_w + w > width:
                # DRAW THE LINE
                cursor_x = x
                for w_word in current_line:
                    is_bold = '*' in w_word
                    clean = w_word.replace('*', '')
                    
                    if is_bold:
                        c.setFillColor(colors.HexColor('#F59E0B')) # Gold
                        c.setFont("Helvetica-Bold", font_size)
                    else:
                        c.setFillColor(colors.HexColor('#CBD5E1')) # Light Grey
                        c.setFont("Helvetica", font_size)
                        
                    c.drawString(cursor_x, current_y, clean)
                    # Advance cursor
                    f_font = "Helvetica-Bold" if is_bold else "Helvetica"
                    cursor_x += c.stringWidth(clean + " ", f_font, font_size)
                
                # Reset for next line
                current_line = [word]
                current_w = w
                current_y -= leading
            else:
                current_line.append(word)
                current_w += w
        
        # Draw the last remaining line of the paragraph
        cursor_x = x
        for w_word in current_line:
            is_bold = '*' in w_word
            clean = w_word.replace('*', '')
            if is_bold:
                c.setFillColor(colors.HexColor('#F59E0B'))
                c.setFont("Helvetica-Bold", font_size)
            else:
                c.setFillColor(colors.HexColor('#CBD5E1'))
                c.setFont("Helvetica", font_size)
            c.drawString(cursor_x, current_y, clean)
            f_font = "Helvetica-Bold" if is_bold else "Helvetica"
            cursor_x += c.stringWidth(clean + " ", f_font, font_size)
            
        current_y -= (leading * 1.5) # Extra space between paragraphs

def create_dense_pdf(slide_text):
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
            c.setFont("Helvetica-Bold", 80)
            c.drawRightString(W - 60, H - 100, f"{slide_num:02d}")
            
            # 2. Title (Higher up now)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 65)
            # Wrap Title
            title_wrap = textwrap.wrap(title, width=20)
            title_y = H - 200
            for t in title_wrap:
                c.drawString(80, title_y, t)
                title_y -= 80
            
            # 3. Gold Divider
            c.setStrokeColor(colors.HexColor('#F59E0B'))
            c.setLineWidth(5)
            c.line(80, title_y - 20, 300, title_y - 20)
            
            # 4. Body Text (The Meat)
            # Starting Y position is dynamic based on title height
            body_start_y = title_y - 120 
            
            # Font size 34 (Readable but allows density)
            draw_text_block(c, body, 80, body_start_y, 920, 34)
            
            c.showPage()
            slide_num += 1
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    if st.button("📚 Generate Deep Dive"):
        with st.status("Writing long-form content...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.write("🎨 Fitting text to page...")
                    st.session_state['pdf'] = create_dense_pdf(slides.strip())
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download Dense PDF", st.session_state['pdf'], "dense_carousel.pdf")
