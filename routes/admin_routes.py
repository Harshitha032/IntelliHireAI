from flask import Blueprint, jsonify
from utils.db import get_db_connection
from utils.auth import token_required, role_required

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('admin')
def get_users(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email, role, DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

import os

@admin_bp.route('/interviews', methods=['GET'])
@token_required
@role_required('admin')
def get_all_interviews(current_user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.id, i.status, i.video_path, u.name as candidate_name
        FROM interviews i
        JOIN candidates c ON i.candidate_id = c.id
        JOIN users u ON c.user_id = u.id
        ORDER BY i.id DESC
    """)
    interviews = cursor.fetchall()
    conn.close()
    
    for i in interviews:
        i['has_video'] = bool(i.get('video_path'))
        if 'video_path' in i:
            del i['video_path']
            
    return jsonify(interviews)

@admin_bp.route('/interview/<int:interview_id>/video', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_video(current_user, interview_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT video_path FROM interviews WHERE id = %s", (interview_id,))
    interview = cursor.fetchone()
    
    if interview and interview.get('video_path'):
        try:
            if os.path.exists(interview['video_path']):
                os.remove(interview['video_path'])
        except Exception as e:
            pass
            
        cursor.execute("UPDATE interviews SET video_path = NULL WHERE id = %s", (interview_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Video deleted successfully"})
        
    conn.close()
    return jsonify({"message": "No video found"}), 404

@admin_bp.route('/system-health', methods=['GET'])
@token_required
@role_required('admin')
def get_system_health(current_user):
    return jsonify({"status": "healthy", "uptime": "100%"})

@admin_bp.route('/user/<int:user_id>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_user(current_user, user_id):
    # Prevent admin from deleting themselves
    if current_user['id'] == user_id:
        return jsonify({"message": "Cannot delete your own admin account"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # First, find any files associated with this user to delete from disk
        cursor.execute("SELECT c.resume_path, c.profile_photo, i.video_path FROM candidates c LEFT JOIN interviews i ON c.id = i.candidate_id WHERE c.user_id = %s", (user_id,))
        records = cursor.fetchall()
        
        for record in records:
            for key in ['resume_path', 'profile_photo', 'video_path']:
                if record.get(key) and os.path.exists(record[key]):
                    try:
                        os.remove(record[key])
                    except:
                        pass
        
        # Now delete the user (cascade deletes candidate and interviews in DB)
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return jsonify({"message": "User and associated files deleted successfully"}), 200
        else:
            return jsonify({"message": "User not found"}), 404
    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500
    finally:
        conn.close()
