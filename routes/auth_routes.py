from flask import Blueprint, request, jsonify, make_response
import bcrypt
import jwt
import datetime
from utils.db import get_db_connection
from config import Config

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'candidate')
    
    if not name or not email or not password:
        return jsonify({"message": "Missing fields"}), 400
        
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                       (name, email, hashed_password, role))
        conn.commit()
        user_id = cursor.lastrowid
        
        if role == 'candidate':
            cursor.execute("INSERT INTO candidates (user_id) VALUES (%s)", (user_id,))
            conn.commit()
            
        return jsonify({"message": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, Config.SECRET_KEY, algorithm="HS256")
        
        response = make_response(jsonify({
            "message": "Login successful",
            "token": token,
            "role": user['role']
        }))
        response.set_cookie('token', token, httponly=True)
        return response
    
    return jsonify({"message": "Invalid email or password"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({"message": "Logged out"}))
    response.set_cookie('token', '', expires=0)
    return response

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500
        
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if user:
        # Generate a reset token valid for 15 minutes
        reset_token = jwt.encode({
            'reset_email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }, Config.SECRET_KEY, algorithm="HS256")
        
        # Simulate sending email by returning the link directly (demo mode)
        reset_link = f"/reset-password?token={reset_token}"
        return jsonify({
            "message": "Demo mode: Password reset link generated.", 
            "reset_link": reset_link
        }), 200
        
    # Security best practice: don't reveal if email exists, just say sent.
    # But since it's a demo, we can just say "Email not found" if we want.
    # Let's just return success anyway to prevent enumeration, or return 404 for clarity in demo.
    return jsonify({"message": "If that email is in our system, a reset link has been sent."}), 200

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({"message": "Missing token or new password"}), 400
        
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        email = payload.get('reset_email')
        
        if not email:
            return jsonify({"message": "Invalid token"}), 400
            
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"message": "Database connection error"}), 500
            
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        conn.commit()
        
        return jsonify({"message": "Password successfully reset!"}), 200
        
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Reset token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid reset token"}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500
