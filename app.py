import streamlit as st
import os
from groq import Groq
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import textwrap

# --- 1. CONFIGURATION (Groq) ---
# Paste your key here directly for now to test
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

client = Groq(
    api_key=GROQ_API_KEY,
)

st.set_page_config(page_title="LinkedGod AI (Groq)", layout="wide")
st.title("🚀 LinkedGod: Viral Post Generator (Powered by Llama 3)")

# --- 2. INPUTS ---
col1, col2 = st.columns([1, 1])

with col1:
    topic = st.text_input("What is your post about?", "How AI will replace junior developers")
    tone = st.selectbox("Tone", ["Controversial", "Storytelling", "Educational", "Funny"])
    
    if st.button("Generate Content"):
        with st.spinner("Llama 3 is writing..."):
            try:
                # A. GENERATE LINKEDIN TEXT
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a LinkedIn Top Voice. Write a viral post."
                        },
                        {
                            "role": "user",
                            "content": f"Topic: {topic}. Tone: {tone}. Rules: Short sentences. One line hook. No hashtags at start."
                        }
                    ],
                    model="llama3-8b-8192", # Free & Fast model
                )
                post_text = chat_completion.choices[0].message.content
                
                # B. GENERATE CAROUSEL TEXT
                slide_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Create a 5-slide carousel outline. Format strictly as: Slide 1: [Text]..."
                        },
                        {
                            "role": "user",
                            "content": f"Turn this topic '{topic}' into 5 educational slides."
                        }
                    ],
                    model="llama3-8b-8192",
                )
                slides_text = slide_completion.choices[0].message.content
                
                # Save to session
                st.session_state['post'] = post_text
                st.session_state['slides'] = slides_text
                st.success("Generated successfully!")
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- 3. OUTPUTS ---
with col2:
    if 'post' in st.session_state:
        st.subheader("📝 Your Viral Post")
        st.text_area("Copy for LinkedIn:", st.session_state['post'], height=300)
        
        st.subheader("🖼️ Your PDF Carousel")
        
        # --- PDF GENERATION ---
        pdf_file = "linkedin_carousel.pdf"
        c = canvas.Canvas(pdf_file, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Simple Logic to split slides
        lines = st.session_state['slides'].split('\n')
        slide_content = [line for line in lines if "Slide" in line]
        
        if not slide_content: 
            slide_content = ["Could not parse slides automatically. Check text above."]

        for content in slide_content:
            # Black Background
            c.setFillColor(colors.black)
            c.rect(0, 0, width, height, fill=1)
            
            # White Text
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 24)
            
            # Wrap text
            text_lines = textwrap.wrap(content, width=50)
            y_text = height / 2 + (len(text_lines)*10)
            
            for line in text_lines:
                c.drawCentredString(width / 2, y_text, line)
                y_text -= 40
            
            c.showPage()
            
        c.save()
        
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="Download PDF Carousel",
                data=f,
                file_name="carousel.pdf",
                mime="application/pdf"
            )
