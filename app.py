from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from pydantic import BaseModel
import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import logging
import smtplib
import os
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback for systems where email modules might not be available
    MimeText = None
    MimeMultipart = None
from models.improved_ai_models import improved_talent_matcher as talent_matcher
from models.social_media_sourcing import social_media_sourcer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Telus Talent Intelligence Platform", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('talent_platform.db')
    cursor = conn.cursor()
    
    # Create candidates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            candidate_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            applied_for TEXT,
            resume_text TEXT,
            skills TEXT,
            experience_years INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create matches table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            candidate_id TEXT,
            job_id TEXT,
            similarity_score REAL,
            confidence_band TEXT,
            explanation TEXT,
            status TEXT DEFAULT 'pending',
            email_sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        )
    ''')
    
    # Add new columns to existing matches table if they don't exist
    try:
        cursor.execute('ALTER TABLE matches ADD COLUMN status TEXT DEFAULT "pending"')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE matches ADD COLUMN email_sent BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE matches ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Update existing rows to have updated_at if they don't have it
    try:
        cursor.execute('UPDATE matches SET updated_at = created_at WHERE updated_at IS NULL')
    except sqlite3.OperationalError:
        pass  # Column might not exist yet
    
    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id TEXT PRIMARY KEY,
            candidate_id TEXT,
            job_id TEXT,
            recruiter_action TEXT,
            reason_code TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        )
    ''')
    
    # Create assessments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id TEXT PRIMARY KEY,
            candidate_id TEXT,
            job_id TEXT,
            assessment_type TEXT,
            candidate_score REAL,
            cutoff_score REAL,
            max_score REAL,
            status TEXT DEFAULT 'completed',
            assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responses TEXT,
            duration_minutes INTEGER,
            FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Add sample assessment data
def add_sample_assessments():
    """Add sample assessment data for testing"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Check if assessments already exist
        cursor.execute('SELECT COUNT(*) FROM assessments')
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Sample assessment data
            sample_assessments = [
                {
                    "assessment_id": "assess_001",
                    "candidate_id": "84bed765-a2c9-4674-b7f1-31e3a4c3ff45",
                    "job_id": "job_001",
                    "assessment_type": "Technical Skills Assessment",
                    "candidate_score": 85.0,
                    "cutoff_score": 70.0,
                    "max_score": 100.0,
                    "status": "completed",
                    "responses": json.dumps([
                        {
                            "question": "What is the difference between supervised and unsupervised learning?",
                            "answer": "Supervised learning uses labeled data to train models, while unsupervised learning finds patterns in unlabeled data.",
                            "type": "text",
                            "is_correct": True
                        },
                        {
                            "question": "Which Python library is commonly used for machine learning?",
                            "selected_option": "scikit-learn",
                            "type": "multiple_choice",
                            "is_correct": True
                        },
                        {
                            "question": "Explain the concept of overfitting in machine learning.",
                            "answer": "Overfitting occurs when a model learns the training data too well, including noise, resulting in poor generalization to new data.",
                            "type": "text",
                            "is_correct": True
                        }
                    ]),
                    "duration_minutes": 45
                },
                {
                    "assessment_id": "assess_002",
                    "candidate_id": "84bed765-a2c9-4674-b7f1-31e3a4c3ff45",
                    "job_id": "job_002",
                    "assessment_type": "Cloud Architecture Assessment",
                    "candidate_score": 72.0,
                    "cutoff_score": 75.0,
                    "max_score": 100.0,
                    "status": "completed",
                    "responses": json.dumps([
                        {
                            "question": "What are the benefits of using cloud computing?",
                            "answer": "Scalability, cost-effectiveness, flexibility, and reduced infrastructure management.",
                            "type": "text",
                            "is_correct": True
                        },
                        {
                            "question": "Which AWS service is used for object storage?",
                            "selected_option": "S3",
                            "type": "multiple_choice",
                            "is_correct": True
                        },
                        {
                            "question": "Describe the difference between IaaS, PaaS, and SaaS.",
                            "answer": "IaaS provides infrastructure, PaaS provides platform services, SaaS provides complete applications.",
                            "type": "text",
                            "is_correct": False
                        }
                    ]),
                    "duration_minutes": 60
                },
                {
                    "assessment_id": "assess_003",
                    "candidate_id": "a3ddd24d-7d8d-4482-9458-4018d83c6361",
                    "job_id": "job_004",
                    "assessment_type": "Machine Learning Fundamentals",
                    "candidate_score": 92.0,
                    "cutoff_score": 80.0,
                    "max_score": 100.0,
                    "status": "completed",
                    "responses": json.dumps([
                        {
                            "question": "What is gradient descent?",
                            "answer": "An optimization algorithm used to minimize the cost function by iteratively moving towards the steepest descent.",
                            "type": "text",
                            "is_correct": True
                        },
                        {
                            "question": "Which activation function is commonly used in hidden layers?",
                            "selected_option": "ReLU",
                            "type": "multiple_choice",
                            "is_correct": True
                        }
                    ]),
                    "duration_minutes": 30
                }
            ]
            
            # Insert sample assessments
            for assessment in sample_assessments:
                cursor.execute('''
                    INSERT INTO assessments (assessment_id, candidate_id, job_id, assessment_type, 
                                           candidate_score, cutoff_score, max_score, status, responses, duration_minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    assessment["assessment_id"],
                    assessment["candidate_id"],
                    assessment["job_id"],
                    assessment["assessment_type"],
                    assessment["candidate_score"],
                    assessment["cutoff_score"],
                    assessment["max_score"],
                    assessment["status"],
                    assessment["responses"],
                    assessment["duration_minutes"]
                ))
            
            conn.commit()
            logger.info(f"Added {len(sample_assessments)} sample assessments")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error adding sample assessments: {e}")

# Add sample assessments on startup
add_sample_assessments()

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "email_user": os.getenv("EMAIL_USER", "talent@telus.com"),
    "email_password": os.getenv("EMAIL_PASSWORD", ""),
    "from_name": "Telus Talent Acquisition Team"
}

# Email helper functions
def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    """Send email notification"""
    try:
        # For demo purposes, we'll just log the email instead of actually sending it
        # In production, you would configure actual SMTP settings
        logger.info(f"EMAIL SENT TO: {to_email}")
        logger.info(f"SUBJECT: {subject}")
        logger.info(f"BODY: {body}")
        
        # Uncomment below for actual email sending
        # msg = MimeMultipart()
        # msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email_user']}>"
        # msg['To'] = to_email
        # msg['Subject'] = subject
        # 
        # if is_html:
        #     msg.attach(MimeText(body, 'html'))
        # else:
        #     msg.attach(MimeText(body, 'plain'))
        # 
        # server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        # server.starttls()
        # server.login(EMAIL_CONFIG['email_user'], EMAIL_CONFIG['email_password'])
        # server.send_message(msg)
        # server.quit()
        
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False

def generate_acceptance_email(candidate_name: str, job_title: str, job_department: str):
    """Generate acceptance email content"""
    subject = f"Congratulations! Your Application for {job_title} at Telus"
    
    body = f"""Dear {candidate_name},

Congratulations! We are pleased to inform you that you have been selected for the {job_title} position in our {job_department} department at Telus.

Our AI-powered talent matching system identified you as an excellent fit for this role, and our recruitment team has confirmed this assessment.

Next Steps:
• Our HR team will contact you within 2 business days to discuss the offer details
• Please prepare any questions you may have about the role, compensation, or benefits
• We will schedule a final interview with the hiring manager if required

We are excited about the possibility of you joining our team and contributing to Telus's mission of connecting Canadians to what matters most.

If you have any immediate questions, please don't hesitate to reach out to us.

Best regards,
{EMAIL_CONFIG['from_name']}
Telus Corporation

---
This is an automated message from our AI-powered talent platform.
"""
    
    return subject, body

def generate_rejection_email(candidate_name: str, job_title: str, reason: str = ""):
    """Generate rejection email content"""
    subject = f"Update on Your Application for {job_title} at Telus"
    
    reason_text = ""
    if reason and reason != "other":
        reason_mapping = {
            "skills_mismatch": "While your background is impressive, we found that the specific skills required for this role don't align perfectly with your current expertise.",
            "experience_low": "We were looking for candidates with more extensive experience in the specific areas required for this position.",
            "overqualified": "Your qualifications exceed what we're looking for in this particular role, and we want to ensure you find a position that fully utilizes your talents.",
            "location_issue": "Unfortunately, the location requirements for this position don't align with your preferences or availability.",
            "missing_certifications": "This role requires specific certifications that weren't present in your application."
        }
        reason_text = f"\n{reason_mapping.get(reason, '')}\n"
    
    body = f"""Dear {candidate_name},

Thank you for your interest in the {job_title} position at Telus and for taking the time to submit your application.

After careful consideration by our AI-powered talent matching system and recruitment team, we have decided to move forward with other candidates whose backgrounds more closely align with our current requirements.{reason_text}

We encourage you to continue monitoring our career opportunities at Telus, as we frequently have new openings that might be a better match for your skills and experience. Your profile will remain in our talent database for future consideration.

We appreciate your interest in Telus and wish you the best in your career endeavors.

Best regards,
{EMAIL_CONFIG['from_name']}
Telus Corporation

---
This is an automated message from our AI-powered talent platform.
"""
    
    return subject, body

# Pydantic models
class CandidateData(BaseModel):
    name: str
    email: str
    phone: str
    applied_for: str
    resume_text: str

class FeedbackData(BaseModel):
    candidate_id: str
    job_id: str
    action: str  # accept, reject, promote, defer
    reason_code: str
    comment: Optional[str] = ""

class JobData(BaseModel):
    title: str
    department: str
    location: str
    requirements: List[str]
    nice_to_have: Optional[List[str]] = []
    summary: str
    experience_years: str
    employment_type: str

# API Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main recruiter dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Resume upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/api/upload-resume")
async def upload_resume(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    applied_for: str = Form(...),
    resume_file: UploadFile = File(...)
):
    """Upload and process resume"""
    try:
        # Read resume content
        resume_content = await resume_file.read()
        
        # Handle different file types
        file_extension = resume_file.filename.lower().split('.')[-1] if resume_file.filename else ''
        
        if file_extension == 'pdf':
            # For PDF files, extract text (simplified - in production use PyPDF2 or pdfplumber)
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(resume_content))
                resume_text = ""
                for page in pdf_reader.pages:
                    resume_text += page.extract_text() + "\n"
            except ImportError:
                # Fallback: treat as plain text and handle encoding errors
                resume_text = resume_content.decode('utf-8', errors='ignore')
        elif file_extension in ['doc', 'docx']:
            # For Word documents (simplified - in production use python-docx)
            try:
                import docx
                import io
                doc = docx.Document(io.BytesIO(resume_content))
                resume_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            except ImportError:
                # Fallback: treat as plain text and handle encoding errors
                resume_text = resume_content.decode('utf-8', errors='ignore')
        else:
            # For text files, try UTF-8 with error handling
            try:
                resume_text = resume_content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                try:
                    resume_text = resume_content.decode('latin-1')
                except UnicodeDecodeError:
                    resume_text = resume_content.decode('utf-8', errors='ignore')
        
        # Generate candidate ID
        candidate_id = str(uuid.uuid4())
        
        # Parse resume using enhanced AI
        parsed_data = talent_matcher.parse_resume_enhanced(resume_text)
        
        # Store candidate in database
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO candidates (candidate_id, name, email, phone, applied_for, resume_text, skills, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate_id,
            name,
            email, 
            phone,
            applied_for,
            resume_text,
            json.dumps(parsed_data.get('skills', [])),
            parsed_data.get('experience_years', 0)
        ))
        
        conn.commit()
        conn.close()
        
        # Get job matches
        candidate_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "applied_for": applied_for,
            "resume_text": resume_text,
            "skills": parsed_data.get('skills', []),
            "experience_years": parsed_data.get('experience_years', 0)
        }
        
        matches = talent_matcher.match_candidate_to_jobs(candidate_data, top_k=5)
        
        # Store matches in database
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        for match in matches:
            match_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO matches (match_id, candidate_id, job_id, similarity_score, confidence_band, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                match_id,
                candidate_id,
                match['job_id'],
                match['similarity_score'],
                match['confidence_band'],
                match['explanation']
            ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "candidate_id": candidate_id,
            "matches": matches,
            "message": "Resume processed successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/candidates")
async def get_candidates():
    """Get all candidates with their matches (excluding those with accepted matches)"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidates with their top match, excluding those who have accepted matches
        cursor.execute('''
            SELECT c.candidate_id, c.name, c.email, c.applied_for, c.created_at,
                   m.job_id, m.similarity_score, m.confidence_band, m.explanation
            FROM candidates c
            LEFT JOIN matches m ON c.candidate_id = m.candidate_id
            WHERE c.candidate_id NOT IN (
                SELECT DISTINCT candidate_id 
                FROM matches 
                WHERE status = 'accepted'
            )
            AND (m.similarity_score = (
                SELECT MAX(similarity_score) 
                FROM matches m2 
                WHERE m2.candidate_id = c.candidate_id
                AND m2.status != 'accepted'
            ) OR m.similarity_score IS NULL)
            ORDER BY c.created_at DESC
        ''')
        
        candidates = []
        for row in cursor.fetchall():
            candidates.append({
                "candidate_id": row[0],
                "name": row[1],
                "email": row[2],
                "applied_for": row[3],
                "created_at": row[4],
                "top_match": {
                    "job_id": row[5],
                    "similarity_score": row[6],
                    "confidence_band": row[7],
                    "explanation": row[8]
                } if row[5] else None
            })
        
        conn.close()
        return {"candidates": candidates}
        
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/candidates/accepted")
async def get_accepted_candidates():
    """Get all accepted candidates with their accepted job details"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidates with accepted matches
        cursor.execute('''
            SELECT c.candidate_id, c.name, c.email, c.phone, c.applied_for, c.created_at,
                   m.job_id, m.similarity_score, m.confidence_band, m.explanation, 
                   m.updated_at, m.email_sent
            FROM candidates c
            JOIN matches m ON c.candidate_id = m.candidate_id
            WHERE m.status = 'accepted'
            ORDER BY m.updated_at DESC
        ''')
        
        accepted_candidates = []
        for row in cursor.fetchall():
            # Get job details
            job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == row[6]), None)
            
            accepted_candidates.append({
                "candidate_id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "applied_for": row[4],
                "created_at": row[5],
                "accepted_match": {
                    "job_id": row[6],
                    "similarity_score": row[7],
                    "confidence_band": row[8],
                    "explanation": row[9],
                    "accepted_at": row[10],
                    "email_sent": bool(row[11]) if row[11] is not None else False,
                    "job_details": job_details
                }
            })
        
        conn.close()
        return {"accepted_candidates": accepted_candidates}
        
    except Exception as e:
        logger.error(f"Error fetching accepted candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/candidate/{candidate_id}/matches")
async def get_candidate_matches(candidate_id: str):
    """Get all matches for a specific candidate"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidate info
        cursor.execute('SELECT * FROM candidates WHERE candidate_id = ?', (candidate_id,))
        candidate_row = cursor.fetchone()
        
        if not candidate_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Get matches with status and email information
        cursor.execute('''
            SELECT job_id, similarity_score, confidence_band, explanation, status, email_sent
            FROM matches 
            WHERE candidate_id = ?
            ORDER BY similarity_score DESC
        ''', (candidate_id,))
        
        matches = []
        for row in cursor.fetchall():
            # Get job details
            job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == row[0]), None)
            
            matches.append({
                "job_id": row[0],
                "similarity_score": row[1],
                "confidence_band": row[2],
                "explanation": row[3],
                "status": row[4] or "pending",
                "email_sent": bool(row[5]) if row[5] is not None else False,
                "job_details": job_details
            })
        
        # Parse skills safely (column 6 is skills, column 5 is resume_text)
        try:
            skills = json.loads(candidate_row[6]) if candidate_row[6] and candidate_row[6].strip() else []
        except (json.JSONDecodeError, TypeError):
            skills = []
        
        # Get skill gap analysis for top match
        skill_gaps = None
        if matches:
            candidate_data = {
                "skills": skills,
                "experience_years": candidate_row[7] or 0
            }
            top_job = matches[0]["job_details"]
            if top_job:
                skill_gaps = talent_matcher.analyze_skill_gaps(candidate_data, top_job)
        
        conn.close()
        
        return {
            "candidate": {
                "candidate_id": candidate_row[0],
                "name": candidate_row[1],
                "email": candidate_row[2],
                "phone": candidate_row[3],
                "applied_for": candidate_row[4],
                "skills": skills,
                "experience_years": candidate_row[7] or 0
            },
            "matches": matches,
            "skill_gaps": skill_gaps
        }
        
    except Exception as e:
        logger.error(f"Error fetching candidate matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/match/accept/preview")
async def preview_acceptance_email(candidate_id: str, job_id: str):
    """Preview acceptance email before sending"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidate details
        cursor.execute('SELECT name, email FROM candidates WHERE candidate_id = ?', (candidate_id,))
        candidate_row = cursor.fetchone()
        if not candidate_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate_name, candidate_email = candidate_row
        
        # Get job details
        job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == job_id), None)
        if not job_details:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Generate email content
        subject, body = generate_acceptance_email(candidate_name, job_details['title'], job_details['department'])
        
        conn.close()
        
        return {
            "success": True,
            "email_preview": {
                "to": candidate_email,
                "subject": subject,
                "body": body,
                "candidate_name": candidate_name,
                "job_title": job_details['title'],
                "job_department": job_details['department']
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating email preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match/accept")
async def accept_match(feedback: FeedbackData):
    """Accept a job match and send confirmation email"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidate and job details
        cursor.execute('SELECT name, email FROM candidates WHERE candidate_id = ?', (feedback.candidate_id,))
        candidate_row = cursor.fetchone()
        if not candidate_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate_name, candidate_email = candidate_row
        
        # Get job details
        job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == feedback.job_id), None)
        if not job_details:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update match status
        cursor.execute('''
            UPDATE matches 
            SET status = 'accepted', updated_at = CURRENT_TIMESTAMP 
            WHERE candidate_id = ? AND job_id = ?
        ''', (feedback.candidate_id, feedback.job_id))
        
        # Store feedback
        feedback_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO feedback (feedback_id, candidate_id, job_id, recruiter_action, reason_code, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            feedback_id,
            feedback.candidate_id,
            feedback.job_id,
            'accept',
            feedback.reason_code,
            feedback.comment
        ))
        
        conn.commit()
        
        # Generate and send acceptance email
        subject, body = generate_acceptance_email(candidate_name, job_details['title'], job_details['department'])
        email_sent = send_email(candidate_email, subject, body)
        
        # Update email sent status
        if email_sent:
            cursor.execute('''
                UPDATE matches 
                SET email_sent = 1, updated_at = CURRENT_TIMESTAMP 
                WHERE candidate_id = ? AND job_id = ?
            ''', (feedback.candidate_id, feedback.job_id))
            conn.commit()
        
        conn.close()
        
        return {
            "success": True, 
            "message": "Match accepted and email sent successfully",
            "email_sent": email_sent,
            "status": "accepted"
        }
        
    except Exception as e:
        logger.error(f"Error accepting match: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/match/reject")
async def reject_match(feedback: FeedbackData):
    """Reject a job match and remove it from the system"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidate and job details before deletion
        cursor.execute('SELECT name, email FROM candidates WHERE candidate_id = ?', (feedback.candidate_id,))
        candidate_row = cursor.fetchone()
        if not candidate_row:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        candidate_name, candidate_email = candidate_row
        
        # Get job details
        job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == feedback.job_id), None)
        if not job_details:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Store feedback before deleting the match
        feedback_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO feedback (feedback_id, candidate_id, job_id, recruiter_action, reason_code, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            feedback_id,
            feedback.candidate_id,
            feedback.job_id,
            'reject',
            feedback.reason_code,
            feedback.comment
        ))
        
        # Delete the match from the database
        cursor.execute('''
            DELETE FROM matches 
            WHERE candidate_id = ? AND job_id = ?
        ''', (feedback.candidate_id, feedback.job_id))
        
        conn.commit()
        
        # Generate and send rejection email
        subject, body = generate_rejection_email(candidate_name, job_details['title'], feedback.reason_code)
        email_sent = send_email(candidate_email, subject, body)
        
        conn.close()
        
        return {
            "success": True, 
            "message": "Match rejected and removed successfully",
            "email_sent": email_sent,
            "status": "deleted"
        }
        
    except Exception as e:
        logger.error(f"Error rejecting match: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackData):
    """Submit recruiter feedback"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        feedback_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO feedback (feedback_id, candidate_id, job_id, recruiter_action, reason_code, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            feedback_id,
            feedback.candidate_id,
            feedback.job_id,
            feedback.action,
            feedback.reason_code,
            feedback.comment
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Feedback submitted successfully"}
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_analytics():
    """Get platform analytics"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Total candidates
        cursor.execute('SELECT COUNT(*) FROM candidates')
        total_candidates = cursor.fetchone()[0]
        
        # Confidence band distribution for pending matches only
        cursor.execute('''
            SELECT confidence_band, COUNT(*) 
            FROM matches 
            WHERE status = 'pending'
            GROUP BY confidence_band
        ''')
        confidence_distribution = dict(cursor.fetchall())
        
        # Total roles offered (accepted matches)
        cursor.execute('SELECT COUNT(*) FROM matches WHERE status = "accepted"')
        total_roles_offered = cursor.fetchone()[0]
        
        # Total rejections (from feedback table)
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE recruiter_action = "reject"')
        total_rejections = cursor.fetchone()[0]
        
        # Users with multiple role offers
        cursor.execute('''
            SELECT candidate_id, COUNT(*) as offer_count
            FROM matches 
            WHERE status = 'accepted'
            GROUP BY candidate_id
            HAVING COUNT(*) > 1
        ''')
        multiple_offers = cursor.fetchall()
        users_with_multiple_offers = len(multiple_offers)
        
        # Candidates needing human review (low confidence matches)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM matches 
            WHERE confidence_band = 'HUMAN' AND status = 'pending'
        ''')
        human_review_needed = cursor.fetchone()[0]
        
        # Feedback distribution
        cursor.execute('''
            SELECT recruiter_action, COUNT(*) 
            FROM feedback 
            GROUP BY recruiter_action
        ''')
        feedback_distribution = dict(cursor.fetchall())
        
        # Average similarity scores by band
        cursor.execute('''
            SELECT confidence_band, AVG(similarity_score) 
            FROM matches 
            GROUP BY confidence_band
        ''')
        avg_scores = dict(cursor.fetchall())
        
        # Recent activity (candidates added in last 7 days)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM candidates 
            WHERE created_at >= datetime('now', '-7 days')
        ''')
        recent_candidates = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_candidates": total_candidates,
            "confidence_distribution": confidence_distribution,
            "feedback_distribution": feedback_distribution,
            "average_scores": avg_scores,
            "total_roles_offered": total_roles_offered,
            "total_rejections": total_rejections,
            "users_with_multiple_offers": users_with_multiple_offers,
            "human_review_needed": human_review_needed,
            "recent_candidates": recent_candidates
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/candidate/{candidate_id}/assessments")
async def get_candidate_assessments(candidate_id: str):
    """Get all assessments for a specific candidate"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get assessments for the candidate
        cursor.execute('''
            SELECT assessment_id, job_id, assessment_type, candidate_score, cutoff_score, max_score,
                   status, assessment_date, responses, duration_minutes
            FROM assessments 
            WHERE candidate_id = ?
            ORDER BY assessment_date DESC
        ''', (candidate_id,))
        
        assessments = []
        for row in cursor.fetchall():
            # Get job details
            job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == row[1]), None)
            
            # Parse responses safely
            try:
                responses = json.loads(row[8]) if row[8] and row[8].strip() else []
            except (json.JSONDecodeError, TypeError):
                responses = []
            
            # Determine pass/fail status
            passed = row[3] >= row[4] if row[3] is not None and row[4] is not None else None
            
            assessments.append({
                "assessment_id": row[0],
                "job_id": row[1],
                "job_title": job_details['title'] if job_details else "Unknown Job",
                "job_department": job_details['department'] if job_details else "Unknown Department",
                "assessment_type": row[2],
                "candidate_score": row[3],
                "cutoff_score": row[4],
                "max_score": row[5],
                "status": row[6],
                "assessment_date": row[7],
                "responses": responses,
                "duration_minutes": row[9],
                "passed": passed,
                "score_percentage": round((row[3] / row[5]) * 100, 1) if row[3] is not None and row[5] is not None and row[5] > 0 else None
            })
        
        conn.close()
        
        return {"assessments": assessments}
        
    except Exception as e:
        logger.error(f"Error fetching candidate assessments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/assessment/{assessment_id}/responses")
async def get_assessment_responses(assessment_id: str):
    """Get detailed responses for a specific assessment"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT candidate_id, job_id, assessment_type, candidate_score, cutoff_score, max_score,
                   status, assessment_date, responses, duration_minutes
            FROM assessments 
            WHERE assessment_id = ?
        ''', (assessment_id,))
        
        assessment_row = cursor.fetchone()
        if not assessment_row:
            raise HTTPException(status_code=404, detail="Assessment not found")
        
        # Get candidate info
        cursor.execute('SELECT name, email FROM candidates WHERE candidate_id = ?', (assessment_row[0],))
        candidate_row = cursor.fetchone()
        
        # Get job details
        job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == assessment_row[1]), None)
        
        # Parse responses safely
        try:
            responses = json.loads(assessment_row[8]) if assessment_row[8] and assessment_row[8].strip() else []
        except (json.JSONDecodeError, TypeError):
            responses = []
        
        conn.close()
        
        return {
            "assessment_id": assessment_id,
            "candidate": {
                "candidate_id": assessment_row[0],
                "name": candidate_row[0] if candidate_row else "Unknown",
                "email": candidate_row[1] if candidate_row else "Unknown"
            },
            "job": {
                "job_id": assessment_row[1],
                "title": job_details['title'] if job_details else "Unknown Job",
                "department": job_details['department'] if job_details else "Unknown Department"
            },
            "assessment_type": assessment_row[2],
            "candidate_score": assessment_row[3],
            "cutoff_score": assessment_row[4],
            "max_score": assessment_row[5],
            "status": assessment_row[6],
            "assessment_date": assessment_row[7],
            "responses": responses,
            "duration_minutes": assessment_row[9],
            "passed": assessment_row[3] >= assessment_row[4] if assessment_row[3] is not None and assessment_row[4] is not None else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching assessment responses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/candidate/{candidate_id}", response_class=HTMLResponse)
async def candidate_detail(request: Request, candidate_id: str):
    """Candidate detail page"""
    return templates.TemplateResponse("candidate_detail.html", {
        "request": request, 
        "candidate_id": candidate_id
    })

# Jobs API Routes
@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """Jobs listing page"""
    return templates.TemplateResponse("jobs.html", {"request": request})

@app.get("/api/jobs")
async def get_jobs():
    """Get all jobs"""
    try:
        # Return jobs from the AI model's data
        jobs = talent_matcher.jobs_data
        return {"jobs": jobs}
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs")
async def create_job(job: JobData):
    """Create a new job"""
    try:
        # Generate job ID
        job_id = f"job_{str(uuid.uuid4())[:8]}"
        
        # Create job object
        new_job = {
            "job_id": job_id,
            "title": job.title,
            "department": job.department,
            "location": job.location,
            "requirements": job.requirements,
            "nice_to_have": job.nice_to_have,
            "summary": job.summary,
            "experience_years": job.experience_years,
            "employment_type": job.employment_type
        }
        
        # Add to jobs data
        talent_matcher.jobs_data.append(new_job)
        
        # Update the jobs.json file
        with open('data/jobs/jobs.json', 'w') as f:
            json.dump(talent_matcher.jobs_data, f, indent=2)
        
        # Reload the AI model with new jobs
        talent_matcher.load_jobs()
        
        return {"success": True, "job_id": job_id, "message": "Job created successfully"}
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get job details"""
    try:
        job = next((job for job in talent_matcher.jobs_data if job['job_id'] == job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"job": job}
        
    except Exception as e:
        logger.error(f"Error fetching job details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}/recommendations")
async def get_job_recommendations(job_id: str):
    """Get candidate recommendations for a job"""
    try:
        # Get job details
        job = next((job for job in talent_matcher.jobs_data if job['job_id'] == job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get all candidates and their matches for this job
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.candidate_id, c.name, c.email, c.phone, c.applied_for, c.skills, c.experience_years,
                   m.similarity_score, m.confidence_band, m.explanation
            FROM candidates c
            JOIN matches m ON c.candidate_id = m.candidate_id
            WHERE m.job_id = ?
            ORDER BY m.similarity_score DESC
        ''', (job_id,))
        
        recommendations = []
        for row in cursor.fetchall():
            # Parse skills safely
            try:
                skills = json.loads(row[5]) if row[5] and row[5].strip() else []
            except (json.JSONDecodeError, TypeError):
                skills = []
            
            recommendations.append({
                "candidate_id": row[0],
                "name": row[1],
                "email": row[2],
                "phone": row[3],
                "applied_for": row[4],
                "skills": skills,
                "experience_years": row[6] or 0,
                "similarity_score": row[7],
                "confidence_band": row[8],
                "explanation": row[9]
            })
        
        conn.close()
        
        return {
            "job": job,
            "recommendations": recommendations,
            "total_candidates": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error fetching job recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: str):
    """Job detail page"""
    return templates.TemplateResponse("job_detail.html", {
        "request": request, 
        "job_id": job_id
    })

# Social Media Sourcing API Routes
class SourcingCampaignData(BaseModel):
    campaign_name: str
    target_skills: List[str]
    target_companies: Optional[List[str]] = []
    job_id: Optional[str] = None

@app.get("/sourcing", response_class=HTMLResponse)
async def sourcing_dashboard(request: Request):
    """Social media sourcing dashboard"""
    return templates.TemplateResponse("sourcing_dashboard.html", {"request": request})

@app.post("/api/sourcing/campaigns")
async def create_sourcing_campaign(campaign: SourcingCampaignData):
    """Create a new sourcing campaign"""
    try:
        campaign_id = social_media_sourcer.create_sourcing_campaign(
            campaign.campaign_name,
            campaign.target_skills,
            campaign.target_companies or [],
            campaign.job_id
        )
        
        return {
            "success": True,
            "campaign_id": campaign_id,
            "message": "Sourcing campaign created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating sourcing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sourcing/campaigns/{campaign_id}/run")
async def run_sourcing_campaign(campaign_id: str):
    """Run a sourcing campaign to find candidates"""
    try:
        results = social_media_sourcer.run_sourcing_campaign(campaign_id)
        
        return {
            "success": True,
            "results": results,
            "message": f"Found {results['candidates_found']} candidates"
        }
        
    except Exception as e:
        logger.error(f"Error running sourcing campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sourcing/campaigns")
async def get_sourcing_campaigns():
    """Get all sourcing campaigns"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT campaign_id, campaign_name, target_skills, target_companies, job_id,
                   status, candidates_found, candidates_contacted, response_rate, created_at
            FROM sourcing_campaigns
            ORDER BY created_at DESC
        ''')
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                "campaign_id": row[0],
                "campaign_name": row[1],
                "target_skills": json.loads(row[2]) if row[2] else [],
                "target_companies": json.loads(row[3]) if row[3] else [],
                "job_id": row[4],
                "status": row[5],
                "candidates_found": row[6],
                "candidates_contacted": row[7],
                "response_rate": row[8],
                "created_at": row[9]
            })
        
        conn.close()
        return {"campaigns": campaigns}
        
    except Exception as e:
        logger.error(f"Error fetching sourcing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sourcing/candidates")
async def get_sourced_candidates():
    """Get all sourced candidates"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sourced_id, name, email, linkedin_url, github_url, current_company,
                   current_role, location, skills, experience_years, sourcing_score,
                   passive_indicator, contact_status, source_platform, profile_summary, created_at
            FROM sourced_candidates
            ORDER BY sourcing_score DESC, created_at DESC
        ''')
        
        candidates = []
        for row in cursor.fetchall():
            # Parse skills safely
            try:
                skills = json.loads(row[8]) if row[8] and row[8].strip() else []
            except (json.JSONDecodeError, TypeError):
                skills = []
            
            candidates.append({
                "sourced_id": row[0],
                "name": row[1],
                "email": row[2],
                "linkedin_url": row[3],
                "github_url": row[4],
                "current_company": row[5],
                "current_role": row[6],
                "location": row[7],
                "skills": skills,
                "experience_years": row[9],
                "sourcing_score": row[10],
                "passive_indicator": row[11],
                "contact_status": row[12],
                "source_platform": row[13],
                "profile_summary": row[14],
                "created_at": row[15]
            })
        
        conn.close()
        return {"sourced_candidates": candidates}
        
    except Exception as e:
        logger.error(f"Error fetching sourced candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sourcing/candidates/{sourced_id}/matches")
async def get_sourced_candidate_matches(sourced_id: str):
    """Get job matches for a sourced candidate"""
    try:
        # Get matches from database
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sm.job_id, sm.similarity_score, sm.confidence_band, sm.explanation, sm.status,
                   sc.name, sc.current_company, sc.current_role, sc.skills, sc.experience_years
            FROM sourcing_matches sm
            JOIN sourced_candidates sc ON sm.sourced_id = sc.sourced_id
            WHERE sm.sourced_id = ?
            ORDER BY sm.similarity_score DESC
        ''', (sourced_id,))
        
        matches = []
        for row in cursor.fetchall():
            # Get job details
            job_details = next((job for job in talent_matcher.jobs_data if job['job_id'] == row[0]), None)
            
            # Parse skills safely
            try:
                skills = json.loads(row[8]) if row[8] and row[8].strip() else []
            except (json.JSONDecodeError, TypeError):
                skills = []
            
            matches.append({
                "job_id": row[0],
                "similarity_score": row[1],
                "confidence_band": row[2],
                "explanation": row[3],
                "status": row[4],
                "job_details": job_details,
                "candidate_info": {
                    "name": row[5],
                    "current_company": row[6],
                    "current_role": row[7],
                    "skills": skills,
                    "experience_years": row[9]
                }
            })
        
        # If no matches in database, generate them
        if not matches:
            matches = social_media_sourcer.match_sourced_candidate_to_jobs(sourced_id, talent_matcher.jobs_data)
        
        conn.close()
        return {"matches": matches}
        
    except Exception as e:
        logger.error(f"Error fetching sourced candidate matches: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sourcing/candidates/{sourced_id}/contact")
async def contact_sourced_candidate(sourced_id: str, contact_data: dict):
    """Mark a sourced candidate as contacted"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sourced_candidates 
            SET contact_status = 'contacted', last_updated = CURRENT_TIMESTAMP
            WHERE sourced_id = ?
        ''', (sourced_id,))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Candidate marked as contacted"
        }
        
    except Exception as e:
        logger.error(f"Error updating contact status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sourcing/analytics")
async def get_sourcing_analytics():
    """Get sourcing analytics"""
    try:
        analytics = social_media_sourcer.get_sourcing_analytics()
        return {"analytics": analytics}
        
    except Exception as e:
        logger.error(f"Error fetching sourcing analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sourced-candidate/{sourced_id}", response_class=HTMLResponse)
async def sourced_candidate_detail(request: Request, sourced_id: str):
    """Sourced candidate detail page"""
    return templates.TemplateResponse("sourced_candidate_detail.html", {
        "request": request, 
        "sourced_id": sourced_id
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
