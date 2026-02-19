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
import random # <--- THE FIX

# --- CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("⚠️ GROQ_API_KEY missing in Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="LinkedGod: Fresh", layout="wide")
st.title("🎲 LinkedGod: Chaos Edition")
st.markdown("Generates **Unique Content** every single time.")

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/", 
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss"
}

def get_random_news(niche):
    """Picks a RANDOM article from the top 10 to ensure variety"""
    feed = feedparser.parse(RSS_FEEDS.get(niche))
    if feed.entries:
        # Pick random from top 10 (or fewer if feed is small)
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
    - Storytelling style (approx 150 words).
    - Controversial hook.
    
    |||
    
    PART 2: CAROUSEL SLIDES (5 Slides)
    - Format strictly as:
      Slide 1: [Short Title] - [Subtitle] - [Visual Prompt: Describe a dark, red/black cinematic background image]
      Slide 2: [Concept] - [Detail] - [Visual Prompt]
      Slide 3: [Concept] - [Detail] - [Visual Prompt]
      Slide 4: [Concept] - [Detail] - [Visual Prompt]
      Slide 5: [Takeaway] - [CTA] - [Visual Prompt]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.9 # <--- HIGH CREATIVITY (Less repetitive)
    )
    return completion.choices[0].message.content

def get_ai_image(prompt):
    """Fetches a unique AI image every time using a random seed"""
    random_seed = random.randint(1, 1000000) # <--- THE FIX
    enhanced_prompt = f"{prompt}, dark red lighting, cinematic, 8k".replace(" ", "%20")
    
    # We inject the random seed into the URL
    url = f"https://image.pollinations.ai/prompt/{enhanced_prompt}?width=1280&height=720&nologo=true&seed={random_seed}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        return None

# --- DESIGN ENGINE (Magazine Style) ---
def draw_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    
    # 1. Background Image
    img_data = get_ai_image(visual_prompt)
    if img_data:
        try:
            img = ImageReader(img_data)
            c.drawImage(img, 0, 0, width=width, height=height, preserveAspectRatio=False)
        except:
            c.setFillColor(colors.black)
            c.rect(0, 0, width, height, fill=1)
            
    # 2. Dark Overlay
    c.setFillColor(colors.black)
    c.setFillAlpha(0.85)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillAlpha(1)

    # 3. Typography
    # Number
    c.setFillColor(colors.HexColor('#990000'))
    c.setFont("Helvetica-Bold", 180)
    c.setFillAlpha(0.2)
    c.drawRightString(width - 20, 20, f"{slide_num:02d}")
    c.setFillAlpha(1)

    # Title
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 36)
    title_lines = textwrap.wrap(title, width=30)
    y = height * 0.75
    for line in title_lines:
        c.drawCentredString(width/2, y, line)
        y -= 45
        
    # Accent
    c.setStrokeColor(colors.HexColor('#FF0000'))
    c.setLineWidth(4)
    c.line(width*0.4, y+10, width*0.6, y+10)
    
    # Body
    c.setFillColor(colors.HexColor('#E5E5E5'))
    c.setFont("Helvetica", 20)
    body_lines = textwrap.wrap(body, width=50)
    y -= 40
    for line in body_lines:
        c.drawCentredString(width/2, y, line)
        y -= 30

def create_pdf(slide_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    lines = slide_text.strip().split('\n')
    slide_count = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            parts = line.split(":", 1)[1].strip()
            segments = parts.split("-")
            
            if len(segments) >= 3:
                title, body, visual = segments[0], segments[1], segments[2]
            elif len(segments) == 2:
                title, body, visual = segments[0], segments[1], "Dark abstract"
            else:
                title, body, visual = segments[0], "", "Dark void"

            draw_slide(c, title.strip(), body.strip(), visual.strip(), slide_count)
            c.showPage()
            slide_count += 1
            
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---
col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    if st.button("🎲 Generate Fresh Content"):
        with st.status("Rolling the dice...", expanded=True):
            news = get_random_news(niche) # <--- RANDOM NEWS
            if news:
                st.write(f"✅ Selected: {news.title}")
                res = generate_content(news, niche)
                try:
                    caption, slides = res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.session_state['slides'] = slides.strip()
                    st.session_state['pdf'] = create_pdf(slides.strip())
                except:
                    st.error("Error parsing content.")
            else:
                st.error("Feed error.")

with col2:
    if 'pdf' in st.session_state:
        st.subheader("Caption")
        st.text_area("Copy:", st.session_state['caption'], height=200)
        st.download_button("📥 Download PDF", st.session_state['pdf'], "chaos_carousel.pdf")
