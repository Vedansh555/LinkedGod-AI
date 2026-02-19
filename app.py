import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def clean_markdown(text):
    """
    Converts AI Markdown (**, #) into ReportLab XML tags for styling.
    """
    # 1. Bold: **text** -> <b>text</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    
    # 2. Italics: *text* -> <i>text</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    
    # 3. Clean up generic bullets
    text = text.replace("- ", "• ")
    
    return text

def create_pro_pdf(ai_text, filename="professional_report.pdf", title="Viral Content Report"):
    """
    Generates a Consulting-Grade PDF using Platypus
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )
    
    # Styles Setup
    styles = getSampleStyleSheet()
    
    # Custom Title Style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2E4053') # Professional Navy Blue
    )
    
    # Custom Header Style
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#2874A6'), # Ocean Blue
        borderPadding=5,
        borderColor=colors.HexColor('#E5E8E8'),
        borderWidth=0,
        backColor=None
    )
    
    # Professional Body Text
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=15, # Good line spacing
        alignment=TA_JUSTIFY
    )

    # --- BUILD THE STORY ---
    story = []
    
    # 1. Add Title Page
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Generated on: {datetime.date.today()}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    story.append(PageBreak()) # Start content on fresh page

    # 2. Parse AI Text into Flowables
    lines = ai_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.1*inch))
            continue
            
        # Headers (###)
        if line.startswith('###') or line.startswith('##'):
            clean_line = clean_markdown(line.replace('#', '').strip())
            story.append(Paragraph(clean_line, h1_style))
        
        # Slides / Lists (Slide 1:)
        elif line.startswith('Slide') or line.startswith('-') or line.startswith('•'):
            clean_line = clean_markdown(line)
            # Make lists look nice
            story.append(Paragraph(clean_line, body_style))
            story.append(Spacer(1, 0.05*inch))
            
        # Standard Text
        else:
            clean_line = clean_markdown(line)
            story.append(Paragraph(clean_line, body_style))

    # 3. Add a "Visual" Footer or Disclaimer
    story.append(Spacer(1, 1*inch))
    footer_text = "<i>Powered by Your AI Agent • Confidential Report</i>"
    story.append(Paragraph(footer_text, styles['Normal']))

    # 4. Build PDF
    doc.build(story)
    return filename
