import pdfplumber
import PyPDF2
import fitz
import pytesseract
from PIL import Image

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber failed, falling back to PyPDF2: {e}")
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e2:
            print(f"PyPDF2 failed: {e2}")
    
    text = text.strip()
    
    # Fallback for image-based PDFs
    if not text:
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                text += pytesseract.image_to_string(img) + "\n"
            text = text.strip()
        except Exception as e3:
            print(f"OCR failed: {e3}")
            
    return text
