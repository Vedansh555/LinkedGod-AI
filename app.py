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

st.set_page_config(page_title="LinkedGod: Final", layout="wide")
st.title("🩸 LinkedGod: Never-Empty Edition")
st.markdown("Features a **Fail-Safe Design Engine** so slides are never blank.")

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
      Slide 1: [Punchy Title] | [Write a 20-word subtitle summary] | [Visual Prompt: Describe a photographic, cinematic scene. Do not use abstract concepts.]
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

def get_ai_image(prompt):
    """Fetches AI image with increased timeout"""
    random_seed = random.randint(1, 1000000)
    # Add 'photographic' to ensure it's not just abstract fuzz
    enhanced_prompt = f"{prompt}, cinematic lighting, photorealistic, 8k, vertical orientation".replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=720&height=1280&nologo=true&seed={random_seed}"
    
    try:
        # Increased timeout to 15 seconds to give it more of a chance
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        return None

# --- NEW: FALLBACK DESIGN ENGINE ---
def draw_fallback_pattern(c, w, h):
    """Draws a cool geometric pattern if AI images fail load"""
    # Base dark color
    c.setFillColor(colors.HexColor('#0F172A')) 
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Subtle Tech Lines
    c.setStrokeColor(colors.HexColor('#1E293B'))
    c.setLineWidth(3)
    c.line(0, 0, w, h)
    c.line(w, 0, 0, h)
    
    # Subtle Tech Circles
    c.setStrokeColor(colors.HexColor('#334155'))
    c.setLineWidth(2)
    c.circle(w/2, h/2, w/3, fill=0, stroke=1)
    c.circle(w/2, h/2, w/1.5, fill=0, stroke=1)
    
    # Add a label so it looks intentional
    c.setFillColor(colors.HexColor('#64748B'))
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h/2, "VISUAL DATA STREAM")

# --- MAIN DESIGN ENGINE ---
def draw_split_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    half_width = width * 0.5
    
    # --- LEFT SIDE: IMAGE OR PATTERN (50%) ---
    
    # 1. Try to get the AI Image
    img_data = get_ai_image(visual_prompt)
    image_loaded = False
    
    if img_data:
        try:
            img = ImageReader(img_data)
            c.drawImage(img, 0, 0, width=half_width, height=height, preserveAspectRatio=False)
            image_loaded = True
        except:
            # Image data existed but was corrupted
            image_loaded = False

    # 2. If Image failed, draw the fallback pattern
    if not image_loaded:
        draw_fallback_pattern(c, half_width, height)

    # Add subtle overlay on left side to unify it
    c.setFillColor(colors.black)
    c.setFillAlpha(0.3)
    c.rect(0, 0, half_width, height, fill=1, stroke=0)
    c.setFillAlpha(1)


    # --- RIGHT SIDE: CONTENT (50%) ---
    c.setFillColor(colors.HexColor('#000000')) # Pure Black BG
    c.rect(half_width, 0, half_width, height, fill=1, stroke=0)
    
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
    bar_width = (slide_num / 5.0) * half_width
    c.setFillColor(colors.HexColor('#990000'))
    c.rect(half_width, 0, bar_width, 10, fill=1, stroke=0)

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
                title = segments[0].strip()
                body = segments[1].strip()
                visual = segments[2].strip()
            elif len(segments) == 2:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = "Tech concept"
            else:
                title = segments[0].strip()
                body = "See caption."
                visual = "Abstract"

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
    if st.button("🩸 Generate Fail-Safe Carousel"):
        st.info("Please wait 30-60 seconds for images to generate...")
        with st.status("Working...", expanded=True):
            news = get_random_news(niche)
            if news:
                st.write(f"✅ Topic: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.write("🎨 Generating visuals (Attempting AI images, falling back to patterns if busy)...")
                    st.session_state['pdf'] = create_pdf(slides.strip())
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download Fail-Safe PDF", st.session_state['pdf'], "failsafe_carousel.pdf")
