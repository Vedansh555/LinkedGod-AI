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
import random
import re

# --- CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("⚠️ GROQ_API_KEY missing in Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="LinkedGod: Pro", layout="wide")
st.title("🩸 LinkedGod: Pro Magazine Edition")
st.markdown("Generates **Detailed Content** (Not just 3 words) + **Split-Screen Design**.")

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
    You are a viral LinkedIn Expert.
    NEWS: {news_item.title}
    SUMMARY: {news_item.summary[:1500]}
    
    Output TWO parts separated by "|||".
    
    PART 1: CAPTION
    - Storytelling style (150 words).
    - Controversial hook.
    
    |||
    
    PART 2: CAROUSEL SLIDES (5 Slides)
    - IMPORTANT: Use the pipe symbol '|' to separate parts.
    - Format strictly as:
      Slide 1: [Punchy Title] | [Write a 20-word subtitle summary] | [Visual Prompt: Dark red cinematic cyberpunk]
      Slide 2: [Main Concept] | [Write a FULL PARAGRAPH (40 words) explaining this concept in detail. Do not be brief.] | [Visual Prompt]
      Slide 3: [Main Concept] | [Write a FULL PARAGRAPH (40 words) explaining this concept in detail.] | [Visual Prompt]
      Slide 4: [Main Concept] | [Write a FULL PARAGRAPH (40 words) explaining this concept in detail.] | [Visual Prompt]
      Slide 5: [The Takeaway] | [Write a strong conclusion paragraph and Call to Action.] | [Visual Prompt]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.8
    )
    return completion.choices[0].message.content

def get_ai_image(prompt):
    """Fetches a unique AI image with retry logic"""
    random_seed = random.randint(1, 1000000)
    # Force vertical aspect ratio for split screen
    enhanced_prompt = f"{prompt}, dark red lighting, cinematic, photorealistic, vertical aspect ratio".replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=720&height=1280&nologo=true&seed={random_seed}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        return None

# --- DESIGN ENGINE (SPLIT SCREEN) ---
def draw_split_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    
    # --- LEFT SIDE: IMAGE (50%) ---
    c.setFillColor(colors.HexColor('#0F172A')) # Dark placeholder
    c.rect(0, 0, width*0.5, height, fill=1, stroke=0)
    
    img_data = get_ai_image(visual_prompt)
    if img_data:
        try:
            img = ImageReader(img_data)
            c.drawImage(img, 0, 0, width=width*0.5, height=height, preserveAspectRatio=False)
        except:
            pass # Keep dark background if fails

    # Add Gradient Overlay on Image (Stylish)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.lineTo(width*0.5, 0)
    p.lineTo(width*0.5, height)
    p.lineTo(0, height)
    p.close()
    c.setFillColor(colors.black)
    c.setFillAlpha(0.2)
    c.drawPath(p, fill=1, stroke=0)
    c.setFillAlpha(1)

    # --- RIGHT SIDE: CONTENT (50%) ---
    c.setFillColor(colors.HexColor('#000000')) # Pure Black BG
    c.rect(width*0.5, 0, width*0.5, height, fill=1, stroke=0)
    
    # 1. Slide Number (Top Right)
    c.setFillColor(colors.HexColor('#990000')) # Blood Red
    c.setFont("Helvetica-Bold", 80)
    c.drawRightString(width - 30, height - 80, f"{slide_num:02d}")

    # 2. Title (Bold White)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    
    # Wrap Title tightly
    title_lines = textwrap.wrap(title, width=20)
    y_text = height * 0.70
    for line in title_lines:
        c.drawString(width*0.55, y_text, line)
        y_text -= 35
        
    # Red Divider Line
    c.setStrokeColor(colors.HexColor('#FF0000'))
    c.setLineWidth(3)
    c.line(width*0.55, y_text+10, width*0.65, y_text+10)
    
    # 3. Body Text (Long Paragraph)
    c.setFillColor(colors.HexColor('#D1D5DB')) # Light Grey
    c.setFont("Helvetica", 16) # Smaller font to fit more text
    
    # Wrap to fit the right column
    body_lines = textwrap.wrap(body, width=35) 
    y_body = y_text - 40
    
    for line in body_lines:
        c.drawString(width*0.55, y_body, line)
        y_body -= 22 # Tight leading for paragraph feel

    # 4. Progress Bar (Bottom)
    bar_width = (slide_num / 5.0) * (width * 0.5)
    c.setFillColor(colors.HexColor('#990000'))
    c.rect(width*0.5, 0, bar_width, 10, fill=1, stroke=0)

def create_pdf(slide_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    lines = slide_text.strip().split('\n')
    slide_count = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            # New Parser using PIPE '|' to handle long sentences
            parts = line.split(":", 1)[1].strip()
            segments = parts.split("|")
            
            if len(segments) >= 3:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = segments[2].strip()
            elif len(segments) == 2:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = "Dark abstract red"
            else:
                title = segments[0].strip()
                body = "Read the caption for details."
                visual = "Dark void"

            draw_split_slide(c, title, body, visual, slide_count)
            c.showPage()
            slide_count += 1
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    if st.button("🩸 Generate Pro Carousel"):
        with st.status("Writing detailed content...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.session_state['slides'] = slides.strip()
                    st.write("🎨 Designing Split-Screen Layout...")
                    st.session_state['pdf'] = create_pdf(slides.strip())
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download Pro PDF", st.session_state['pdf'], "pro_carousel.pdf")
