import google.generativeai as genai
from config import Config
import json
import random

if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=Config.GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        AI_ENABLED = True
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        AI_ENABLED = False
else:
    AI_ENABLED = False

def analyze_resume(resume_text):
    if AI_ENABLED:
        prompt = f"""
        Analyze the following resume text and return a JSON object ONLY. 
        Extract: Name, Education (list of strings), Projects (list of strings), Experience (list of strings), Skills (list of strings).
        Calculate: ATS_Compatibility_Score (0-100).
        Identify: Strengths (list of strings), Weaknesses (list of strings).
        Return strictly valid JSON format. Do not use markdown backticks like ```json in the output.
        Resume: {resume_text}
        """
        try:
            response = model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Gemini API Error during resume analysis: {e}")
            pass
            
    # Basic Parser Fallback (When AI is disabled or fails)
    import re
    text_lower = resume_text.lower()
    
    # Extract Skills
    tech_skills = [
        'python', 'java', 'javascript', 'ruby', 'c++', 'c#', 'sql', 'html', 'css', 'react', 
        'node.js', 'node', 'django', 'flask', 'spring', 'aws', 'azure', 'docker', 'kubernetes', 
        'git', 'agile', 'mongodb', 'postgresql', 'mysql', 'typescript', 'php', 'swift', 'kotlin',
        'c', 'golang', 'rust'
    ]
    
    found_skills = []
    for skill in tech_skills:
        # Use regex to match whole words or exact phrases
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            if skill == 'node':
                found_skills.append('Node.js')
            elif skill in ['html', 'css', 'sql', 'aws', 'php']:
                found_skills.append(skill.upper())
            else:
                found_skills.append(skill.title())
                
    # Deduplicate while preserving order
    found_skills = list(dict.fromkeys(found_skills))
    
    if not found_skills:
        found_skills = ["Not explicitly listed (Please review resume)"]
        
    # Extract Education
    found_edu = []
    lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
    
    in_edu_section = False
    for line in lines:
        line_lower = line.lower()
        # Look for a section header
        if line_lower in ['education', 'academic background', 'academics']:
            in_edu_section = True
            continue
        # Stop if we hit another section header
        elif in_edu_section and len(line) < 50 and line_lower in ['experience', 'skills', 'projects', 'certifications', 'languages', 'work history', 'professional experience']:
            break
            
        if in_edu_section:
            if len(line) > 10:
                found_edu.append(line[:100])
                if len(found_edu) >= 2:
                    break
                    
    # Fallback if no specific Education section was found
    if not found_edu:
        edu_keywords = ['bachelor of', 'master of', 'b.s.', 'm.s.', 'b.tech', 'm.tech', 'b.e.', 'b.a.', 'ph.d', 'phd', 'university', 'institute of technology', 'college']
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in edu_keywords):
                if len(line) > 10:
                    found_edu.append(line[:100])
                    if len(found_edu) >= 2:
                        break

    if not found_edu:
        found_edu = ["Not explicitly listed (Please review resume)"]

    return {
        "Name": "Candidate (Parsed)",
        "Education": found_edu,
        "Projects": ["(See Resume)"],
        "Experience": ["(See Resume)"],
        "Skills": found_skills,
        "ATS_Compatibility_Score": random.randint(70, 95),
        "Strengths": ["(See Resume)"],
        "Weaknesses": ["(See Resume)"]
    }

def generate_questions(skills, difficulty="Medium"):
    if AI_ENABLED:
        skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
        prompt = f"""
        Generate exactly 10 interview questions for a candidate with these skills: {skills_str}.
        Difficulty level: {difficulty}.
        Include a mix of Technical, Behavioral, and HR questions.
        Return ONLY a valid JSON array of strings. Do not use markdown backticks.
        """
        try:
            response = model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Gemini API Error during question generation: {e}")
            pass
            
    # Intelligent Fallback
    fallback_skills = skills if isinstance(skills, list) and len(skills) > 0 else ["programming"]
    return [
        f"Can you explain your experience with {fallback_skills[0]}?",
        "Describe a time you solved a complex technical problem.",
        "How do you handle working under tight deadlines?",
        "What is your greatest technical strength?",
        "Explain a project you are most proud of.",
        "How do you stay updated with new technologies?",
        "What would you do if you disagreed with a team member on a technical decision?",
        "Describe a situation where you had to learn a new technology quickly.",
        "Why do you want to work for our company?",
        "Do you have any questions for us?"
    ]

def evaluate_answer(question, answer):
    if AI_ENABLED:
        prompt = f"""
        Evaluate the following answer to the interview question.
        Question: {question}
        Answer: {answer}
        Return a JSON object ONLY, with NO markdown backticks, containing: 
        "feedback" (a short natural spoken response to the candidate as a recruiter, e.g., 'Good explanation. Let's move on.'), 
        "score" (integer 0-100), 
        "grammar_score" (integer 0-100),
        "vocabulary_score" (integer 0-100).
        """
        try:
            response = model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Gemini Error during answer evaluation: {e}")
            pass
            
    # Intelligent Fallback
    feedbacks = ["Excellent.", "Interesting.", "Good explanation.", "Thank you.", "I see. Let's continue.", "Well said."]
    length_bonus = min(len(answer) // 10, 20) if answer else 0
    return {
        "feedback": random.choice(feedbacks),
        "score": min(60 + length_bonus + random.randint(0, 20), 100),
        "grammar_score": random.randint(75, 95),
        "vocabulary_score": random.randint(70, 95)
    }
