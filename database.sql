CREATE DATABASE IF NOT EXISTS intellihire;
USE intellihire;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('candidate', 'hr', 'admin') DEFAULT 'candidate',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phone VARCHAR(20),
    education TEXT,
    skills TEXT,
    experience TEXT,
    resume_path VARCHAR(255),
    profile_photo VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    hr_id INT,
    status ENUM('pending', 'completed') DEFAULT 'pending',
    scheduled_at DATETIME,
    completed_at DATETIME,
    resume_score FLOAT,
    interview_score FLOAT,
    communication_score FLOAT,
    confidence_score FLOAT,
    technical_score FLOAT,
    problem_solving_score FLOAT,
    overall_rating FLOAT,
    strengths TEXT,
    weaknesses TEXT,
    recommendation VARCHAR(100),
    video_path VARCHAR(255),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (hr_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    interview_id INT NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50),
    difficulty VARCHAR(20),
    candidate_answer TEXT,
    ai_feedback TEXT,
    FOREIGN KEY (interview_id) REFERENCES interviews(id) ON DELETE CASCADE
);

-- Insert an admin user (password is 'admin123' hashed with bcrypt)
-- Wait, bcrypt hashing varies by salt. I will create a script or route to insert a default admin.
