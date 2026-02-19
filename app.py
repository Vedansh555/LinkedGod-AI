import streamlit as st
from groq import Groq
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
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

st.set_page_config(page_title="LinkedGod AI", layout="wide")
st.title("🏭 Content Factory (Pro Edition)")

# --- 1. LOGIC ---

RSS_FEEDS = {
    "Product Management": "https://techcrunch.com/category/startups/feed/",
    "AI Agents": "https://www.artificialintelligence-news.com/feed/", 
    "Consulting": "http://feeds.harvardbusiness.org/harvardbusiness"
}

def clean_text(text):
    """Cleans AI text for PDF generation"""
    # Convert **bold** to <b>bold</b> (ReportLab format)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Convert *italic* to <i>italic</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Remove hashtags for clean PDF
    text = re.sub(r'#\w+', '', text)
    return text

def get_latest_news(niche):
    feed = feedparser.parse(RSS_FEEDS.get(niche))
    if feed.entries:
        return feed.entries[0]
    return None

def generate_content(news_item, niche):
    prompt = f"""
    You are a generic LinkedIn expert.
    NEWS: {news_item.title}
    SUMMARY: {news_item.summary[:500]}
    
    TASK: Write a 5-slide educational carousel about this news.
    Format strictly as:
    Slide 1: [Title]
    Slide 2: [Point 1]
    Slide 3: [Point 2]
    Slide 4: [Point 3]
    Slide 5: [Conclusion]
    
    Do NOT use '###' or markdown headers. Just plain text.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return completion.choices[0].message.content

def create_memory_pdf(ai_text):
    """Writes PDF to RAM (BytesIO) instead of Disk"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Slide Title Style
    title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2E86C1'), # Blue
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    # Body Text Style
    body_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        fontSize=18,
        leading=24,
        alignment=TA_CENTER
    )

    story = []
    
    # Process text
    lines = ai_text.split('\n')
    current_slide_text = []
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # If new slide detected
        if "Slide" in line and ":" in line:
            # If we have previous content, add page break
            if current_slide_text:
                story.append(Spacer(1, 100))
                story.append(PageBreak())
            
            # Add Slide Title (e.g., "Slide 1: The News")
            clean_line = clean_text(line)
            story.append(Spacer(1, 50))
            story.append(Paragraph(clean_line, title_style))
            current_slide_text = [line]
            
        else:
            # Body text
            clean_line = clean_text(line)
            story.append(Paragraph(clean_line, body_style))
            current_slide_text.append(line)

    # If story is empty (AI failed), add error message to PDF
    if not story:
        story.append(Paragraph("Error: AI returned empty text.", styles['Normal']))

    # Build PDF
    doc.build(story)
    buffer.seek(0) # Rewind buffer to start
    return buffer

# --- 2. UI ---

niche = st.selectbox("Select Niche", list(RSS_FEEDS.keys()))

if st.button("Generate Pro PDF"):
    with st.spinner("Fetching & Writing..."):
        news = get_latest_news(niche)
        if news:
            st.success(f"Found: {news.title}")
            
            # Generate Text
            ai_text = generate_content(news, niche)
            st.text_area("AI Output (Debug)", ai_text, height=200) # DEBUG VIEW
            
            # Generate PDF in Memory
            pdf_buffer = create_memory_pdf(ai_text)
            
            st.download_button(
                label="📥 Download PDF (Guaranteed Work)",
                data=pdf_buffer,
                file_name="linkedin_carousel.pdf",
                mime="application/pdf"
            )
        else:
            st.error("No news found.")
