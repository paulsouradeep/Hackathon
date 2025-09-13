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
from models.ai_models import talent_matcher

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
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

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
        
        # Parse resume using AI
        parsed_data = talent_matcher.parse_resume_simple(resume_text)
        
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
    """Get all candidates with their matches"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get candidates with their top match
        cursor.execute('''
            SELECT c.candidate_id, c.name, c.email, c.applied_for, c.created_at,
                   m.job_id, m.similarity_score, m.confidence_band, m.explanation
            FROM candidates c
            LEFT JOIN matches m ON c.candidate_id = m.candidate_id
            WHERE m.similarity_score = (
                SELECT MAX(similarity_score) 
                FROM matches m2 
                WHERE m2.candidate_id = c.candidate_id
            ) OR m.similarity_score IS NULL
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
        
        # Parse skills safely
        try:
            skills = json.loads(candidate_row[5]) if candidate_row[5] and candidate_row[5].strip() else []
        except (json.JSONDecodeError, TypeError):
            skills = []
        
        # Get skill gap analysis for top match
        skill_gaps = None
        if matches:
            candidate_data = {
                "skills": skills,
                "experience_years": candidate_row[6] or 0
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
                "experience_years": candidate_row[6] or 0
            },
            "matches": matches,
            "skill_gaps": skill_gaps
        }
        
    except Exception as e:
        logger.error(f"Error fetching candidate matches: {e}")
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
        
        # Confidence band distribution
        cursor.execute('''
            SELECT confidence_band, COUNT(*) 
            FROM matches 
            GROUP BY confidence_band
        ''')
        confidence_distribution = dict(cursor.fetchall())
        
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
        
        conn.close()
        
        return {
            "total_candidates": total_candidates,
            "confidence_distribution": confidence_distribution,
            "feedback_distribution": feedback_distribution,
            "average_scores": avg_scores
        }
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
