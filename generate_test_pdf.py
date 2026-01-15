from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_form_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica", 12)
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "Patient Registration Form")
    
    # Fields
    c.setFont("Helvetica", 12)
    
    # Name
    c.drawString(50, 700, "Full Name:")
    c.line(120, 700, 300, 700) # Line for name
    
    # Date of Birth
    c.drawString(320, 700, "DOB (MM/DD/YYYY):")
    c.rect(450, 685, 100, 20) # Box for DOB
    
    # Address
    c.drawString(50, 650, "Address:")
    c.line(120, 650, 550, 650)
    
    # Email
    c.drawString(50, 600, "Email:")
    c.rect(100, 585, 200, 20)
    
    # Signature
    c.drawString(50, 500, "Signature:")
    c.line(120, 500, 300, 500)
    
    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_form_pdf("test_form.pdf")
