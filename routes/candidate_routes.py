from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename
from utils.db import get_db_connection
from utils.auth import token_required, role_required
from services.resume_service import extract_text_from_pdf
from services.ai_service import analyze_resume
from config import Config

candidate_bp = Blueprint('candidate_bp', __name__)

@candidate_bp.route('/profile', methods=['GET'])
@token_required
@role_required('candidate')
def get_profile(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.name, u.email, c.* 
        FROM users u 
        JOIN candidates c ON u.id = c.user_id 
        WHERE u.id = %s
    """, (current_user['id'],))
    profile = cursor.fetchone()
    conn.close()
    return jsonify(profile)

@candidate_bp.route('/upload_resume', methods=['POST'])
@token_required
@role_required('candidate')
def upload_resume(current_user):
    file = request.files.get('resume')
    photo = request.files.get('photo')
    
    if not file or file.filename == '':
        return jsonify({"message": "No file selected"}), 400
        
    if not file.filename.endswith('.pdf'):
        return jsonify({"message": "Only PDF resumes are supported."}), 400
        
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
        
    filename = secure_filename(f"resume_{current_user['id']}.pdf")
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Save photo if provided
    if photo and photo.filename != '':
        photo_filename = secure_filename(f"photo_{current_user['id']}_{photo.filename}")
        photo_path = os.path.join(Config.UPLOAD_FOLDER, photo_filename)
        photo.save(photo_path)
    else:
        photo_path = None
    
    # AI parsing
    resume_text = extract_text_from_pdf(filepath)
    ai_analysis = analyze_resume(resume_text)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    skills_raw = ai_analysis.get('Skills', [])
    skills = ", ".join(skills_raw) if isinstance(skills_raw, list) else str(skills_raw)
    
    education_raw = ai_analysis.get('Education', [])
    education = ", ".join(education_raw) if isinstance(education_raw, list) else str(education_raw)
    
    experience_raw = ai_analysis.get('Experience', [])
    experience = ", ".join(experience_raw) if isinstance(experience_raw, list) else str(experience_raw)
    
    # Build dynamic query to only update photo_path if it was provided
    if photo_path:
        cursor.execute("""
            UPDATE candidates 
            SET resume_path = %s, photo_path = %s, skills = %s, education = %s, experience = %s 
            WHERE user_id = %s
        """, (filepath, photo_path, skills, education, experience, current_user['id']))
    else:
        cursor.execute("""
            UPDATE candidates 
            SET resume_path = %s, skills = %s, education = %s, experience = %s 
            WHERE user_id = %s
        """, (filepath, skills, education, experience, current_user['id']))
        
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": "Resume processed successfully",
        "analysis": ai_analysis
    })

@candidate_bp.route('/interviews', methods=['GET'])
@token_required
@role_required('candidate')
def get_interviews(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.* FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        WHERE c.user_id = %s
    """, (current_user['id'],))
    interviews = cursor.fetchall()
    conn.close()
    return jsonify(interviews)
