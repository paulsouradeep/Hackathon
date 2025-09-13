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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
        )
    ''')
    
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
        
        # Get matches
        cursor.execute('''
            SELECT job_id, similarity_score, confidence_band, explanation
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
