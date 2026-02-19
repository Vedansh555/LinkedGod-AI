import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
import feedparser
import requests
import textwrap
import re

# --- CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("⚠️ GROQ_API_KEY missing in Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="LinkedGod: Magazine", layout="wide")
st.title("🩸 LinkedGod: Magazine Edition")
st.markdown("Generates **Full-Screen Visual Carousels** (Magazine Style).")

# --- 1. LOGIC ---

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/", 
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss"
}

def get_latest_news(niche):
    feed = feedparser.parse(RSS_FEEDS.get(niche))
    if feed.entries:
        return feed.entries[0]
    return None

def generate_content(news_item, niche):
    prompt = f"""
    You are a viral LinkedIn Ghostwriter.
    NEWS: {news_item.title}
    SUMMARY: {news_item.summary[:1500]} 
    
    Output TWO parts separated by "|||".
    
    PART 1: CAPTION
    - Write a "Storytelling" style post (approx 150 words).
    - Start with a controversial hook.
    - Use short lines.
    - 3 hashtags.
    
    |||
    
    PART 2: CAROUSEL SLIDES (5 Slides)
    - Format strictly as:
      Slide 1: [Short Title] - [Subtitle] - [Visual Prompt: Describe a dark, red/black cinematic background image, e.g. 'Cyberpunk city with red neon, dark atmosphere']
      Slide 2: [Concept Name] - [2-3 detailed sentences explaining it] - [Visual Prompt]
      Slide 3: [Concept Name] - [2-3 detailed sentences explaining it] - [Visual Prompt]
      Slide 4: [Concept Name] - [2-3 detailed sentences explaining it] - [Visual Prompt]
      Slide 5: [The Takeaway] - [Call to Action] - [Visual Prompt]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return completion.choices[0].message.content

# --- THE IMAGE GENERATOR (ROBUST) ---
def get_ai_image(prompt):
    """Fetches a real AI image. Includes a fallback if it fails."""
    # Force 'dark red cinematic' style
    enhanced_prompt = f"{prompt}, dark red lighting, cinematic, 8k, photorealistic, high contrast".replace(" ", "%20")
    # We add a random seed to ensure uniqueness
    url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=1280&height=720&nologo=true&seed=123"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        pass
        
    # FALLBACK IMAGE (If AI fails, use a reliable dark background)
    # This ensures you NEVER get a white blank slide.
    try:
        fallback_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
        response = requests.get(fallback_url, timeout=5)
        return BytesIO(response.content)
    except:
        return None

# --- THE DESIGN ENGINE (MAGAZINE STYLE) ---

def draw_magazine_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    
    # 1. DRAW BACKGROUND IMAGE (Full Screen)
    img_data = get_ai_image(visual_prompt)
    if img_data:
        try:
            img = ImageReader(img_data)
            c.drawImage(img, 0, 0, width=width, height=height, preserveAspectRatio=False)
        except:
            # Absolute Fail-Safe: Black Background
            c.setFillColor(colors.black)
            c.rect(0, 0, width, height, fill=1)
            
    # 2. DRAW "GLASS" OVERLAY (Darkens the image so text pops)
    # We draw a semi-transparent black box over the WHOLE image
    c.setFillColor(colors.black)
    c.setFillAlpha(0.85) # 85% Dark - Very readable
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillAlpha(1) # Reset alpha

    # 3. TYPOGRAPHY
    
    # Slide Number (Huge Watermark Style)
    c.setFillColor(colors.HexColor('#990000')) # Blood Red
    c.setFont("Helvetica-Bold", 180)
    c.setFillAlpha(0.2) # Subtle watermark
    c.drawRightString(width - 20, 20, f"{slide_num:02d}")
    c.setFillAlpha(1)

    # Title (White, Big)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 36)
    
    title_lines = textwrap.wrap(title, width=30)
    y_text = height * 0.75
    for line in title_lines:
        c.drawCentredString(width/2, y_text, line)
        y_text -= 45
        
    # Red Accent Line
    c.setStrokeColor(colors.HexColor('#FF0000')) # Bright Red
    c.setLineWidth(4)
    c.line(width*0.4, y_text+10, width*0.6, y_text+10)
    
    # Body Text (Centered, Readable)
    c.setFillColor(colors.HexColor('#E5E5E5')) # Off-White
    c.setFont("Helvetica", 20)
    
    body_lines = textwrap.wrap(body, width=50) # Wider text area
    y_body = y_text - 40
    for line in body_lines:
        c.drawCentredString(width/2, y_body, line)
        y_body -= 30

def create_visual_pdf(slide_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    
    lines = slide_text.strip().split('\n')
    slide_count = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            parts = line.split(":", 1)[1].strip()
            segments = parts.split("-")
            
            if len(segments) >= 3:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = segments[2].strip()
            elif len(segments) == 2:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = "Dark red abstract background"
            else:
                title = segments[0].strip()
                body = ""
                visual = "Dark void"

            draw_magazine_slide(c, title, body, visual, slide_count)
            c.showPage()
            slide_count += 1
        
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---

col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    
    if st.button("🩸 Generate Magazine Post"):
        with st.status("Agent Working...", expanded=True):
            st.write("📡 Fetching News...")
            news = get_latest_news(niche)
            
            if news:
                st.write(f"✅ Found: {news.title}")
                st.write("🧠 Dreaming of Visuals...")
                full_res = generate_content(news, niche)
                
                try:
                    caption, slides = full_res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.session_state['slides'] = slides.strip()
                    
                    st.write("🎨 Rendering Magazine PDF...")
                    pdf_data = create_visual_pdf(st.session_state['slides'])
                    st.session_state['pdf_data'] = pdf_data
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("No news.")

with col2:
    if 'pdf_data' in st.session_state:
        st.subheader("Viral Caption")
        st.text_area("Copy:", st.session_state['caption'], height=350)
        st.download_button("📥 Download Magazine PDF", st.session_state['pdf_data'], "magazine_carousel.pdf")
