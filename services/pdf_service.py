from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from config import Config

def generate_interview_report(interview_data, filename="report.pdf"):
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 750, "IntelliHire AI - Interview Report")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Candidate: {interview_data.get('candidate_name', 'N/A')}")
    c.drawString(100, 680, f"Overall Rating: {interview_data.get('overall_rating', 'N/A')}/100")
    c.drawString(100, 660, f"Recommendation: {interview_data.get('recommendation', 'N/A')}")
    
    # Detailed Scores
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 620, "Detailed Scores:")
    c.setFont("Helvetica", 12)
    c.drawString(120, 600, f"- Technical: {interview_data.get('technical_score', 0)}")
    c.drawString(120, 580, f"- Communication: {interview_data.get('communication_score', 0)}")
    c.drawString(120, 560, f"- Problem Solving: {interview_data.get('problem_solving_score', 0)}")
    c.drawString(120, 540, f"- Confidence: {interview_data.get('confidence_score', 0)}")
    
    # Feedback
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 500, "Strengths:")
    c.setFont("Helvetica", 12)
    c.drawString(120, 480, str(interview_data.get('strengths', 'N/A')))
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 440, "Weaknesses:")
    c.setFont("Helvetica", 12)
    c.drawString(120, 420, str(interview_data.get('weaknesses', 'N/A')))
    
    c.save()
    return filepath
