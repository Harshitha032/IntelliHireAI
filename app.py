from flask import Flask, render_template, send_from_directory
from config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Blueprints will be registered here
    from routes.auth_routes import auth_bp
    from routes.candidate_routes import candidate_bp
    from routes.hr_routes import hr_bp
    from routes.admin_routes import admin_bp
    from routes.interview_routes import interview_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(candidate_bp, url_prefix='/api/candidate')
    app.register_blueprint(hr_bp, url_prefix='/api/hr')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')
    
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/uploads/<path:filename>')
    def download_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/login')
    def login_page():
        return render_template('auth.html', is_login=True)
        
    @app.route('/register')
    def register_page():
        return render_template('auth.html', is_login=False)
        
    @app.route('/forgot-password')
    def forgot_password_page():
        return render_template('forgot_password.html')

    @app.route('/reset-password')
    def reset_password_page():
        return render_template('reset_password.html')
        
    @app.route('/dashboard')
    def dashboard():
        # Ideally, we verify JWT from cookies here and redirect based on role
        # For now, it will be handled by JS on the client side checking tokens
        return render_template('candidate_dashboard.html')

    @app.route('/hr/dashboard')
    def hr_dashboard():
        return render_template('hr_dashboard.html')

    @app.route('/admin/dashboard')
    def admin_dashboard():
        return render_template('admin_dashboard.html')

    @app.route('/interview/<int:interview_id>')
    def interview_room(interview_id):
        return render_template('interview.html', interview_id=interview_id)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
