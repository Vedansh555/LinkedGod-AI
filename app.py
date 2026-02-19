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

st.set_page_config(page_title="LinkedGod: Unbreakable", layout="wide")
st.title("🩸 LinkedGod: Zero-Failure Edition")
st.markdown("Guarantees a **Real Image** on every slide. No patterns. No text placeholders.")

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/", 
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss"
}

# --- BACKUP IMAGES (Real 4K Stock Photos) ---
# If AI fails, we use one of these high-quality dark abstracts.
BACKUP_IMAGES = [
    "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?q=80&w=1000&auto=format&fit=crop", # Dark Red Abstract
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1000&auto=format&fit=crop", # Cyberpunk City
    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=1000&auto=format&fit=crop", # Tech Chip
    "https://images.unsplash.com/photo-1605810230434-7631ac76ec81?q=80&w=1000&auto=format&fit=crop", # Dark Data Center
    "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?q=80&w=1000&auto=format&fit=crop"  # Neon Fluid
]

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
      Slide 1: [Punchy Title] | [Write a 20-word subtitle] | [Visual Prompt: Dark red cinematic, photorealistic, 8k]
      Slide 2: [Main Concept] | [Write a FULL PARAGRAPH (40 words) explaining this.] | [Visual Prompt]
      Slide 3: [Main Concept] | [Write a FULL PARAGRAPH (40 words) explaining this.] | [Visual Prompt]
      Slide 4: [Main Concept] | [Write a FULL PARAGRAPH (40 words) explaining this.] | [Visual Prompt]
      Slide 5: [The Takeaway] | [Write a strong conclusion and CTA.] | [Visual Prompt]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.8
    )
    return completion.choices[0].message.content

def get_image_with_fallback(prompt):
    """
    1. Tries to generate AI Image.
    2. If that fails/times out, downloads a Real Stock Photo.
    """
    # 1. Try AI Generation (Pollinations)
    random_seed = random.randint(1, 1000000)
    enhanced_prompt = f"{prompt}, dark red lighting, cinematic, photorealistic, vertical".replace(" ", "%20")
    ai_url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=720&height=1280&nologo=true&seed={random_seed}"
    
    try:
        # Try to fetch AI image with a 6-second timeout (keep it fast)
        response = requests.get(ai_url, timeout=6)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        pass # AI Failed, moving to backup...

    # 2. Backup: Use a Real Stock Photo
    # This guarantees NO "Visual Data Stream" text ever again.
    backup_url = random.choice(BACKUP_IMAGES)
    try:
        response = requests.get(backup_url, timeout=5)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        return None # Only happens if NO internet at all

# --- DESIGN ENGINE ---
def draw_split_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    half_width = width * 0.5
    
    # --- LEFT SIDE: IMAGE (50%) ---
    c.setFillColor(colors.HexColor('#0F172A')) 
    c.rect(0, 0, width*0.5, height, fill=1, stroke=0)
    
    # FETCH IMAGE (With Backup Guarantee)
    img_data = get_image_with_fallback(visual_prompt)
    
    if img_data:
        try:
            img = ImageReader(img_data)
            c.drawImage(img, 0, 0, width=width*0.5, height=height, preserveAspectRatio=False)
        except:
            # Absolute worst case (corrupt data), just keep black
            pass

    # Gradient Overlay (To make it look "Designed")
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
    c.setFillColor(colors.HexColor('#000000')) 
    c.rect(width*0.5, 0, width*0.5, height, fill=1, stroke=0)
    
    # Slide Number
    c.setFillColor(colors.HexColor('#990000')) # Blood Red
    c.setFont("Helvetica-Bold", 80)
    c.drawRightString(width - 30, height - 80, f"{slide_num:02d}")

    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    title_lines = textwrap.wrap(title, width=20)
    y_text = height * 0.70
    for line in title_lines:
        c.drawString(width*0.55, y_text, line)
        y_text -= 35
        
    # Red Divider
    c.setStrokeColor(colors.HexColor('#FF0000'))
    c.setLineWidth(3)
    c.line(width*0.55, y_text+10, width*0.65, y_text+10)
    
    # Body Text
    c.setFillColor(colors.HexColor('#D1D5DB')) # Light Grey
    c.setFont("Helvetica", 16)
    body_lines = textwrap.wrap(body, width=35) 
    y_body = y_text - 40
    for line in body_lines:
        c.drawString(width*0.55, y_body, line)
        y_body -= 22

    # Progress Bar
    bar_width = (slide_num / 5.0) * width * 0.5
    c.setFillColor(colors.HexColor('#990000'))
    c.rect(width*0.5, 0, bar_width, 10, fill=1, stroke=0)

def create_pdf(slide_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    lines = slide_text.strip().split('\n')
    slide_count = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            parts = line.split(":", 1)[1].strip()
            segments = parts.split("|")
            
            if len(segments) >= 3:
                title, body, visual = segments[0], segments[1], segments[2]
            elif len(segments) == 2:
                title, body, visual = segments[0], segments[1], "Abstract"
            else:
                title, body, visual = segments[0], "Read caption.", "Abstract"

            draw_split_slide(c, title.strip(), body.strip(), visual.strip(), slide_count)
            c.showPage()
            slide_count += 1
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    if st.button("🩸 Generate Guaranteed Carousel"):
        st.info("Generating... (If AI is slow, we will use stock photos instantly)")
        with st.status("Working...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.write("🎨 Fetching images (AI or Backup)...")
                    st.session_state['pdf'] = create_pdf(slides.strip())
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download PDF", st.session_state['pdf'], "guaranteed_carousel.pdf")
