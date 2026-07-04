from flask import Blueprint, request, jsonify
from utils.db import get_db_connection
from utils.auth import token_required, role_required
from services.ai_service import generate_questions, evaluate_answer
import datetime
import json
import os
from werkzeug.utils import secure_filename
from config import Config

interview_bp = Blueprint('interview_bp', __name__)

@interview_bp.route('/start', methods=['POST'])
@token_required
@role_required('candidate')
def start_interview(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM candidates WHERE user_id = %s", (current_user['id'],))
    candidate = cursor.fetchone()
    
    if not candidate:
        conn.close()
        return jsonify({"message": "Candidate profile not found."}), 404
        
    skills = candidate['skills'].split(',') if candidate['skills'] else ["General Programming"]
    
    questions = generate_questions(skills)
    
    cursor.execute("INSERT INTO interviews (candidate_id, status, scheduled_at) VALUES (%s, %s, %s)",
                   (candidate['id'], 'pending', datetime.datetime.now()))
    interview_id = cursor.lastrowid
    
    for q in questions:
        cursor.execute("INSERT INTO questions (interview_id, question_text) VALUES (%s, %s)",
                       (interview_id, q))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Interview ready", "interview_id": interview_id})

@interview_bp.route('/<int:interview_id>/next_question', methods=['GET'])
@token_required
@role_required('candidate')
def get_next_question(current_user, interview_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM questions 
        WHERE interview_id = %s AND candidate_answer IS NULL 
        ORDER BY id LIMIT 1
    """, (interview_id,))
    
    question = cursor.fetchone()
    conn.close()
    
    if question:
        return jsonify({"question_id": question['id'], "text": question['question_text']})
    else:
        return jsonify({"message": "Interview completed"}), 200

@interview_bp.route('/<int:interview_id>/submit_answer', methods=['POST'])
@token_required
@role_required('candidate')
def submit_answer(current_user, interview_id):
    data = request.json
    question_id = data.get('question_id')
    answer = data.get('answer')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
    q = cursor.fetchone()
    
    if not q:
        conn.close()
        return jsonify({"message": "Question not found"}), 404
        
    evaluation = evaluate_answer(q['question_text'], answer)
    
    cursor.execute("""
        UPDATE questions 
        SET candidate_answer = %s, ai_feedback = %s 
        WHERE id = %s
    """, (answer, json.dumps(evaluation), question_id))
    
    conn.commit()
    conn.close()
    
    return jsonify(evaluation)

@interview_bp.route('/<int:interview_id>/finish', methods=['POST'])
@token_required
@role_required('candidate')
def finish_interview(current_user, interview_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE interviews 
        SET status = 'completed', completed_at = %s, overall_rating = 85
        WHERE id = %s
    """, (datetime.datetime.now(), interview_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Interview finalized"})

@interview_bp.route('/<int:interview_id>/upload_video', methods=['POST'])
@token_required
@role_required('candidate')
def upload_video(current_user, interview_id):
    if 'video' not in request.files:
        return jsonify({"message": "No video part"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"message": "No selected video"}), 400
        
    filename = secure_filename(f"interview_{interview_id}.webm")
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE interviews SET video_path = %s WHERE id = %s", (filepath, interview_id))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Video uploaded successfully"})
