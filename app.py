import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
import feedparser
import re

# --- CONFIGURATION ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("⚠️ Please put your GROQ_API_KEY in Streamlit Secrets!")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="LinkedGod Designer", layout="wide")
st.title("🎨 LinkedGod: Designer Edition")
st.markdown("Generates a **Designed PDF** + **Viral Caption**.")

# --- 1. LOGIC ---

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/", 
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness",
    "Startup Life": "https://news.ycombinator.com/rss"
}

def clean_text(text):
    """Cleans AI text for PDF generation"""
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text) # Bold
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)     # Italic
    return text

def get_latest_news(niche):
    feed = feedparser.parse(RSS_FEEDS.get(niche))
    if feed.entries:
        return feed.entries[0]
    return None

def generate_full_content(news_item, niche):
    """Generates BOTH the Caption and the Slides"""
    prompt = f"""
    You are a viral LinkedIn Ghostwriter.
    NEWS: {news_item.title}
    SUMMARY: {news_item.summary[:800]}
    
    Output TWO parts separated by "|||".
    
    PART 1: THE CAPTION
    - Write a high-engagement LinkedIn caption.
    - Start with a Hook.
    - Use short lines.
    - End with 3-5 hashtags.
    
    |||
    
    PART 2: THE CAROUSEL SLIDES (5 Slides)
    - Format strictly as:
      Slide 1: [Title] - [Subtitle/Body]
      Slide 2: [Main Point] - [Explanation]
      Slide 3: [Main Point] - [Explanation]
      Slide 4: [Main Point] - [Explanation]
      Slide 5: [Conclusion] - [Call to Action]
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return completion.choices[0].message.content

def create_designed_pdf(slide_text):
    """Creates a visually styled PDF with colored 'Cards'"""
    buffer = BytesIO()
    # Landscape mode for "Carousel" feel
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
    
    styles = getSampleStyleSheet()
    
    # 1. Header Style (Big Blue Text)
    header_style = ParagraphStyle(
        'SlideHead',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#154360'), # Navy Blue
        alignment=TA_CENTER,
        spaceAfter=15,
        leading=30
    )
    
    # 2. Body Style (Clean Grey Text)
    body_style = ParagraphStyle(
        'SlideBody',
        parent=styles['BodyText'],
        fontSize=16,
        textColor=colors.HexColor('#2E4053'), # Dark Grey
        alignment=TA_CENTER,
        leading=22
    )

    story = []
    
    # Parse Slides
    lines = slide_text.strip().split('\n')
    current_slide = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # If line starts with "Slide X:", it's a new slide
        if "Slide" in line and ":" in line:
            
            # --- SPLIT TITLE & BODY ---
            # Expecting format "Slide 1: Title - Body"
            parts = line.split(":", 1)[1].strip()
            
            if "-" in parts:
                title_txt, body_txt = parts.split("-", 1)
            else:
                title_txt = parts
                body_txt = ""
            
            # --- CREATE THE "CARD" VISUAL ---
            # We use a Table to create a colored box
            
            # Content inside the box
            content = [
                [Paragraph(clean_text(title_txt), header_style)],
                [Spacer(1, 20)],
                [Paragraph(clean_text(body_txt), body_style)]
            ]
            
            # Table Style (The "Card" Look)
            card_table = Table(content, colWidths=[600])
            card_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EBF5FB')), # Light Blue BG
                ('BOX', (0,0), (-1,-1), 2, colors.HexColor('#AED6F1')),     # Blue Border
                ('ROUNDEDCORNERS', [10, 10, 10, 10]),                       # (ReportLab 3.6+)
                ('TOPPADDING', (0,0), (-1,-1), 40),
                ('BOTTOMPADDING', (0,0), (-1,-1), 40),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            
            # Add to PDF
            story.append(Spacer(1, 20)) # Top margin
            story.append(card_table)    # The visual card
            story.append(PageBreak())   # One slide per page
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- 2. THE UI ---

col1, col2 = st.columns([1, 1])

with col1:
    niche = st.selectbox("Select Your Niche", list(RSS_FEEDS.keys()))
    
    if st.button("🚀 Auto-Design Post"):
        with st.status("Agent Working...", expanded=True):
            st.write("📡 Fetching News...")
            news = get_latest_news(niche)
            
            if news:
                st.write(f"✅ Found: {news.title}")
                st.write("🧠 Writing Caption & Slides...")
                
                # Get raw AI text
                full_response = generate_full_content(news, niche)
                
                # Split Caption vs Slides
                try:
                    caption_part, slides_part = full_response.split("|||")
                    st.session_state['caption'] = caption_part.strip()
                    st.session_state['slides'] = slides_part.strip()
                    
                    # Generate PDF
                    st.write("🎨 Painting PDF...")
                    pdf_buffer = create_designed_pdf(st.session_state['slides'])
                    st.session_state['pdf_data'] = pdf_buffer
                    
                except:
                    st.error("AI formatting error. Try again.")
            else:
                st.error("Feed unavailable.")

# --- 3. OUTPUTS ---
with col2:
    if 'caption' in st.session_state:
        st.subheader("1. LinkedIn Caption (Copy This)")
        st.text_area("Caption", st.session_state['caption'], height=350)
        
        st.subheader("2. Designed Carousel (Download This)")
        st.download_button(
            label="📥 Download Designed PDF",
            data=st.session_state['pdf_data'],
            file_name="designed_carousel.pdf",
            mime="application/pdf"
        )
