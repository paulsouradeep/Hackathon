# Telus Talent Intelligence Platform - MVP

## Overview
An AI-powered talent matching system that automatically matches candidates to multiple roles, provides confidence-based routing, and includes human-in-the-loop workflows.

## Core Features
- Resume parsing using LLM
- Semantic job matching with Sentence-BERT
- Confidence-based routing (Auto/Review/Human)
- Recruiter dashboard for overrides
- Alternative role suggestions
- Basic skill gap analysis

## Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
python app.py

# Open browser to http://localhost:8080
```

## Architecture
- **Backend**: FastAPI + Python
- **AI Models**: Sentence Transformers + OpenAI GPT
- **Vector Search**: FAISS
- **Frontend**: HTML/CSS/JavaScript
- **Database**: SQLite (for demo)

## Demo Flow
1. Upload resume
2. View AI-generated matches with confidence scores
3. See alternative role suggestions
4. Recruiter can accept/reject with feedback
5. System learns from feedback

## Files Structure
```
/
├── app.py              # Main FastAPI application
├── models/             # AI models and utilities
├── data/               # Sample resumes and job descriptions
├── static/             # Frontend files
├── templates/          # HTML templates
└── requirements.txt    # Python dependencies
# Hackathon
