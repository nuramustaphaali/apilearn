# courses/utils.py
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from django.conf import settings

def generate_certificate_pdf(certificate):
    """
    Generates a premium-style PDF certificate.
    """
    filename = f"cert_{certificate.id}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, 'certificates', filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Setup Canvas (Landscape)
    c = canvas.Canvas(file_path, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # --- COLORS ---
    navy_blue = HexColor('#003366')
    gold_color = HexColor('#C5B358')

    # --- BORDERS ---
    # Outer Border (Navy)
    c.setStrokeColor(navy_blue)
    c.setLineWidth(10)
    c.rect(20, 20, width-40, height-40)

    # Inner Border (Gold)
    c.setStrokeColor(gold_color)
    c.setLineWidth(3)
    c.rect(35, 35, width-70, height-70)

    # --- HEADER ---
    c.setFillColor(navy_blue)
    c.setFont("Times-Bold", 40)
    c.drawCentredString(width / 2, height - 120, "CERTIFICATE OF COMPLETION")

    c.setFillColor(gold_color)
    c.setFont("Times-Roman", 16)
    c.drawCentredString(width / 2, height - 150, "THIS CERTIFIES THAT")

    # --- STUDENT NAME (Big & Fancy) ---
    student_name = certificate.student.full_name or certificate.student.username
    c.setFillColor(HexColor('#000000')) 
    c.setFont("Times-BoldItalic", 45)
    c.drawCentredString(width / 2, height - 230, student_name)

    # --- SEPARATOR LINE ---
    c.setStrokeColor(navy_blue)
    c.setLineWidth(1)
    c.line(width/2 - 150, height - 245, width/2 + 150, height - 245)

    # --- COURSE DETAILS ---
    c.setFont("Times-Roman", 18)
    c.drawCentredString(width / 2, height - 280, "Has successfully demonstrated proficiency in")
    
    c.setFillColor(navy_blue)
    c.setFont("Times-Bold", 30)
    c.drawCentredString(width / 2, height - 330, certificate.course.title)

    # --- FOOTER / VERIFICATION ---
    c.setFillColor(HexColor('#555555'))
    c.setFont("Courier", 12) # Courier for the code (looks techy)
    
    # Left Side: Date
    date_str = certificate.issued_at.strftime("%B %d, %Y")
    c.drawString(60, 80, f"Date Issued: {date_str}")
    c.line(60, 95, 200, 95) # Signature Line

    # Right Side: Verification Code
    c.drawRightString(width - 60, 80, f"ID: {str(certificate.id)}")
    c.setFont("Times-Italic", 10)
    c.drawRightString(width - 60, 65, "Verify at: app.apilearn.com/courses/certificate/verify")

    # --- FAKE DIGITAL SEAL (Bottom Center) ---
    c.setStrokeColor(gold_color)
    c.setLineWidth(3)
    c.circle(width/2, 85, 40)
    c.setFillColor(gold_color)
    c.setFont("Times-Bold", 10)
    c.drawCentredString(width/2, 90, "OFFICIAL")
    c.drawCentredString(width/2, 78, "SEAL")

    c.save()
    return f"certificates/{filename}"