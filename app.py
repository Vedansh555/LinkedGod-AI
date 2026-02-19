import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from io import BytesIO
import feedparser
import requests  # New library to fetch images
import textwrap

# --- CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("⚠️ GROQ_API_KEY missing in Secrets.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="LinkedGod: Visuals", layout="wide")
st.title("📸 LinkedGod: AI Visuals Edition")
st.markdown("Generates **Real AI Images** + Viral Text automatically.")

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
      Slide 1: [Short Title] - [Subtitle] - [Visual Prompt: Describe an image for this slide, e.g., 'A futuristic robot shaking hands with a human, cinematic lighting']
      Slide 2: [Concept] - [Explanation] - [Visual Prompt: e.g., 'Minimalist vector icon of a brain, blue background']
      Slide 3: [Concept] - [Explanation] - [Visual Prompt]
      Slide 4: [Concept] - [Explanation] - [Visual Prompt]
      Slide 5: [Takeaway] - [Call to Action] - [Visual Prompt]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return completion.choices[0].message.content

# --- THE IMAGE GENERATOR (FREE) ---
def get_ai_image(prompt):
    """Fetches a real AI image from Pollinations.ai"""
    # Clean the prompt for URL
    clean_prompt = prompt.replace(" ", "%20")
    url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=800&height=1000&nologo=true"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return BytesIO(response.content)
    except:
        return None
    return None

# --- THE DESIGN ENGINE ---

def draw_visual_slide(c, title, body, visual_prompt, slide_num):
    width, height = landscape(letter)
    
    # --- 1. LEFT SIDE: THE AI IMAGE (40% Width) ---
    c.setFillColor(colors.HexColor('#0F172A'))
    c.rect(0, 0, width*0.4, height, fill=1, stroke=0)
    
    # Fetch and Draw Image
    img_data = get_ai_image(visual_prompt)
    if img_data:
        try:
            img = ImageReader(img_data)
            # Draw image filling the left panel
            c.drawImage(img, 0, 0, width=width*0.4, height=height, preserveAspectRatio=False)
        except:
            pass # If image fails, keep black background
            
    # Add a Dark Overlay so white text pops (Gradient effect hack)
    c.setFillColor(colors.black)
    c.setFillAlpha(0.3)
    c.rect(0, 0, width*0.4, height, fill=1, stroke=0)
    c.setFillAlpha(1)

    # --- 2. RIGHT SIDE: CONTENT (60% Width) ---
    c.setFillColor(colors.HexColor('#F8FAFC')) # Off-White Background
    c.rect(width*0.4, 0, width*0.6, height, fill=1, stroke=0)
    
    # Slide Number (Big & Stylish)
    c.setFillColor(colors.HexColor('#E2E8F0')) # Light Grey Number
    c.setFont("Helvetica-Bold", 100)
    c.drawRightString(width - 20, height - 80, f"{slide_num:02d}")

    # Title
    c.setFillColor(colors.HexColor('#0F172A')) # Dark Navy
    c.setFont("Helvetica-Bold", 30)
    
    title_lines = textwrap.wrap(title, width=25)
    y_text = height * 0.65
    for line in title_lines:
        c.drawString(width*0.45, y_text, line)
        y_text -= 35
        
    # Accent Line
    c.setStrokeColor(colors.HexColor('#F59E0B')) # Gold
    c.setLineWidth(4)
    c.line(width*0.45, y_text, width*0.55, y_text)
    
    # Body Text
    c.setFillColor(colors.HexColor('#334155')) # Slate Grey
    c.setFont("Helvetica", 18)
    
    body_lines = textwrap.wrap(body, width=40)
    y_body = y_text - 40
    for line in body_lines:
        c.drawString(width*0.45, y_body, line)
        y_body -= 25

def create_visual_pdf(slide_text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    
    lines = slide_text.strip().split('\n')
    
    slide_count = 1
    
    for line in lines:
        if "Slide" in line and ":" in line:
            # Expected format: Slide 1: Title - Body - VisualPrompt
            parts = line.split(":", 1)[1].strip()
            
            # Split by dashes
            segments = parts.split("-")
            
            if len(segments) >= 3:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = segments[2].strip()
            elif len(segments) == 2:
                title = segments[0].strip()
                body = segments[1].strip()
                visual = "Minimalist abstract technology background, blue and white, 4k" # Default
            else:
                title = segments[0].strip()
                body = ""
                visual = "Professional business background"

            draw_visual_slide(c, title, body, visual, slide_count)
            c.showPage()
            slide_count += 1
        
    c.save()
    buffer.seek(0)
    return buffer

# --- UI ---

col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))
    
    if st.button("📸 Generate Visual Carousel"):
        with st.status("Agent Working...", expanded=True):
            st.write("📡 Fetching News...")
            news = get_latest_news(niche)
            
            if news:
                st.write(f"Found: {news.title}")
                st.write("🧠 Thinking of visual concepts...")
                full_res = generate_content(news, niche)
                
                try:
                    caption, slides = full_res.split("|||")
                    st.session_state['caption'] = caption.strip()
                    st.session_state['slides'] = slides.strip()
                    
                    st.write("🎨 Generating AI Images & PDF...")
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
        st.download_button("📥 Download PDF (With Images)", st.session_state['pdf_data'], "visual_carousel.pdf")
