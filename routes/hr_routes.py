from flask import Blueprint, jsonify
from utils.db import get_db_connection
from utils.auth import token_required, role_required
import os

hr_bp = Blueprint('hr_bp', __name__)

@hr_bp.route('/dashboard-stats', methods=['GET'])
@token_required
@role_required('hr')
def dashboard_stats(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM interviews")
    total_interviews = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as pending FROM interviews WHERE status='pending'")
    pending = cursor.fetchone()['pending']
    
    cursor.execute("SELECT AVG(overall_rating) as avg_score FROM interviews WHERE status='completed'")
    avg_score = cursor.fetchone()['avg_score']
    
    conn.close()
    
    return jsonify({
        "total_interviews": total_interviews,
        "pending_interviews": pending,
        "avg_score": float(avg_score) if avg_score else 0
    })

@hr_bp.route('/interviews', methods=['GET'])
@token_required
@role_required('hr')
def get_all_interviews(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.id as interview_id, i.status, i.overall_rating, c.id as candidate_id, u.name as candidate_name
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN users u ON c.user_id = u.id
        ORDER BY i.id DESC
    """)
    interviews = cursor.fetchall()
    conn.close()
    return jsonify(interviews)

@hr_bp.route('/candidate/<int:candidate_id>/interview/<int:interview_id>', methods=['GET'])
@token_required
@role_required('hr')
def get_candidate_details(current_user, candidate_id, interview_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT c.*, u.name, u.email 
        FROM candidates c 
        JOIN users u ON c.user_id = u.id 
        WHERE c.id = %s
    """, (candidate_id,))
    candidate = cursor.fetchone()
    
    cursor.execute("SELECT * FROM interviews WHERE id = %s", (interview_id,))
    interview = cursor.fetchone()
    conn.close()
    
    if candidate and candidate.get('resume_path'):
        candidate['resume_url'] = '/uploads/' + os.path.basename(candidate['resume_path'])
    else:
        candidate['resume_url'] = None

    if candidate and candidate.get('photo_path'):
        candidate['photo_url'] = '/uploads/' + os.path.basename(candidate['photo_path'])
    else:
        candidate['photo_url'] = None
        
    if interview and interview.get('video_path'):
        interview['video_url'] = '/uploads/' + os.path.basename(interview['video_path'])
    else:
        interview['video_url'] = None
        
    return jsonify({
        "candidate": candidate,
        "interview": interview
    })
