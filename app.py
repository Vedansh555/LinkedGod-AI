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

st.set_page_config(page_title="LinkedGod: Blood Theme", layout="wide")
st.title("🩸 LinkedGod: Blood & Visuals Edition")
st.markdown("Generates **Dark, Visual, Blood-Themed Carousels** with Real AI Images.")

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
    SUMMARY: {news_item.summary[:800]}
    
    Output TWO parts separated by "|||".
    
    PART 1: CAPTION
    - Hook + Body + 3 Hashtags.
    
    |||
    
    PART 2: CAROUSEL SLIDES (5 Slides)
    - Format strictly as:
      Slide 1: [Short Title] - [Subtitle] - [Visual Prompt: Describe a dark, cinematic, red and black image representing this, e.g. 'Cyberpunk robot with red eyes, dark atmosphere']
      Slide 2: [Concept] - [Explanation] - [Visual Prompt]
      Slide 3: [Concept] - [Explanation] - [Visual Prompt]
      Slide 4: [Concept] - [Explanation] - [Visual Prompt]
      Slide 5: [Takeaway] - [Call to Action] - [Visual Prompt]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return completion.choices[0].message.content

# --- THE IMAGE GENERATOR (FIXED) ---
def get_ai_image(prompt):
    """Fetches a real AI image from Pollinations.ai"""
    # Force the style to be "Dark" and "Photorealistic" via prompt injection
    enhanced_prompt = f"{prompt}, dark theme, red lighting, cinematic, 8k, photorealistic".replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=1024&height=1024&nologo=true&seed=42"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return BytesIO(response.content)
    except Exception as e:
        print(f"Image Error: {e}")
        return None
    return None

# --- THE DESIGN ENGINE (BLOOD THEME) ---

def draw_blood_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    
    # --- 1. LAYOUT: SPLIT SCREEN (50/50) ---
    
    # RIGHT SIDE: CONTENT (Black Background)
    c.setFillColor(colors.HexColor('#000000')) # Pure Black
    c.rect(width*0.5, 0, width*0.5, height, fill=1, stroke=0)
    
    # LEFT SIDE: IMAGE PLACEHOLDER (Dark Grey default)
    c.setFillColor(colors.HexColor('#0A0A0A')) 
    c.rect(0, 0, width*0.5, height, fill=1, stroke=0)

    # --- 2. DRAW THE AI IMAGE (Left Side) ---
    img_data = get_ai_image(visual_prompt)
    if img_data:
        try:
            img = ImageReader(img_data)
            # Draw image filling the left half completely
            c.drawImage(img, 0, 0, width=width*0.5, height=height, preserveAspectRatio=False)
        except:
            # Fallback if image fails to load: Draw a Red X
            c.setStrokeColor(colors.white)
            c.line(0,0, width*0.5, height)
            c.line(0, height, width*0.5, 0)
            
    # Add a "Vignette" overlay to the image (Darkens edges)
    # This makes the white text pop if we ever put text on it, but looks cool anyway
    p = c.beginPath()
    p.moveTo(width*0.5, 0)
    p.lineTo(width*0.5, height)
    p.lineTo(width*0.4, height)
    p.lineTo(width*0.4, 0)
    p.close()
    c.setFillColor(colors.black)
    c.setFillAlpha(0.3)
    c.drawPath(p, fill=1, stroke=0)
    c.setFillAlpha(1) # Reset alpha

    # --- 3. TYPOGRAPHY (Right Side) ---
    
    # BLOOD RED ACCENT LINE
    c.setStrokeColor(colors.HexColor('#990000')) # Blood Red
    c.setLineWidth(8)
    c.line(width*0.5, height-40, width*0.5, 40) # Vertical divider line

    # Slide Number (Huge, Blood Red)
    c.setFillColor(colors.HexColor('#990000')) 
    c.setFont("Helvetica-Bold", 120)
    # Positioned slightly off-screen for that magazine look
    c.drawRightString(width - 20, height - 100, f"{slide_num:02d}")

    # Title (White, Bold)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 32)
    
    title_lines = textwrap.wrap(title, width=20)
    y_text = height * 0.65
    for line in title_lines:
        c.drawString(width*0.55, y_text, line)
        y_text -= 40
        
    # Horizontal Red Accent under Title
    c.setStrokeColor(colors.HexColor('#FF0000')) # Bright Red
    c.setLineWidth(3)
    c.line(width*0.55, y_text+10, width*0.65, y_text+10)
    
    # Body Text (Light Grey)
    c.setFillColor(colors.HexColor('#E0E0E0')) 
    c.setFont("Helvetica", 18)
    
    body_lines = textwrap.wrap(body, width=35)
    y_body = y_text - 40
    for line in body_lines:
        c.drawString(width*0.55, y_body, line)
        y_body -= 28
        
    # Footer (Branding)
    c.setFillColor(colors.HexColor('#555555'))
    c.setFont("Helvetica", 10)
    c.drawString(width*0.55, 30, "GENERATED BY LINKEDGOD AI")

def create_visual_pdf(slide_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    
    lines = slide_text.strip().split('\n')
    slide_count = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            # Expected format: Slide 1: Title - Body - VisualPrompt
            parts = line.split(":", 1)[1].strip()
            segments = parts.split("-")
            
            if len(segments) >= 3:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = segments[2].strip()
            elif len(segments) == 2:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = "Abstract dark red and black technology background" 
            else:
                title = segments[0].strip()
                body = ""
                visual = "Dark void"

            draw_blood_slide(c, title, body, visual, slide_count)
            c.showPage()
            slide_count += 1
        
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---

col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    
    if st.button("🩸 Generate Blood Theme"):
        with st.status("Summoning Content...", expanded=True):
            st.write("📡 Fetching News...")
            news = get_latest_news(niche)
            
            if news:
                st.write(f"✅ Found: {news.title}")
                st.write("🧠 Writing & Dreaming Images...")
                full_res = generate_content(news, niche)
                
                try:
                    caption, slides = full_res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.session_state['slides'] = slides.strip()
                    
                    st.write("🎨 Painting Images & PDF...")
                    pdf_data = create_visual_pdf(st.session_state['slides'])
                    st.session_state['pdf_data'] = pdf_data
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("No news.")

with col2:
    if 'pdf_data' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download Blood PDF", st.session_state['pdf_data'], "blood_carousel.pdf")
