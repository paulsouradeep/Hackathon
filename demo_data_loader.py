#!/usr/bin/env python3
"""
Demo Data Loader for Telus Talent Intelligence Platform
Loads sample candidates from JSON data into the system for demonstration
"""

import json
import sqlite3
import uuid
from models.ai_models import talent_matcher

def load_sample_candidates():
    """Load sample candidates into the database"""
    print("Loading sample candidates into the database...")
    
    # Load sample resumes
    with open('data/resumes/sample_resumes.json', 'r') as f:
        candidates = json.load(f)
    
    # Connect to database
    conn = sqlite3.connect('talent_platform.db')
    cursor = conn.cursor()
    
    for candidate in candidates:
        print(f"Processing candidate: {candidate['name']}")
        
        # Store candidate in database
        cursor.execute('''
            INSERT OR REPLACE INTO candidates (candidate_id, name, email, phone, applied_for, resume_text, skills, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            candidate['candidate_id'],
            candidate['name'],
            candidate['email'],
            candidate['phone'],
            candidate['applied_for'],
            candidate['resume_text'],
            json.dumps(candidate['skills']),
            candidate['experience_years']
        ))
        
        # Generate matches using AI
        candidate_data = {
            "name": candidate['name'],
            "email": candidate['email'],
            "phone": candidate['phone'],
            "applied_for": candidate['applied_for'],
            "resume_text": candidate['resume_text'],
            "skills": candidate['skills'],
            "experience_years": candidate['experience_years']
        }
        
        matches = talent_matcher.match_candidate_to_jobs(candidate_data, top_k=5)
        
        # Store matches in database
        for match in matches:
            match_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT OR REPLACE INTO matches (match_id, candidate_id, job_id, similarity_score, confidence_band, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                match_id,
                candidate['candidate_id'],
                match['job_id'],
                match['similarity_score'],
                match['confidence_band'],
                match['explanation']
            ))
        
        print(f"  - Generated {len(matches)} matches")
    
    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully loaded {len(candidates)} sample candidates!")
    print("You can now run the demo with: python app.py")

if __name__ == "__main__":
    load_sample_candidates()
