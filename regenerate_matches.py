#!/usr/bin/env python3
"""
Regenerate job matches for fixed candidates
"""

import sqlite3
import json
import sys
import os

# Add the current directory to Python path to import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.improved_ai_models import improved_talent_matcher

def regenerate_matches_for_candidates():
    """Regenerate job matches for candidates that were just fixed"""
    conn = sqlite3.connect('talent_platform.db')
    cursor = conn.cursor()
    
    # Get all candidates that don't have the 'cand_' prefix (original uploaded resumes)
    cursor.execute("""
        SELECT candidate_id, name, skills, experience_years, resume_text, applied_for
        FROM candidates 
        WHERE candidate_id NOT LIKE 'cand_%'
    """)
    
    candidates = cursor.fetchall()
    print(f"Found {len(candidates)} candidates to regenerate matches for")
    
    # Delete existing matches for these candidates
    candidate_ids = [c[0] for c in candidates]
    placeholders = ','.join(['?' for _ in candidate_ids])
    cursor.execute(f"DELETE FROM matches WHERE candidate_id IN ({placeholders})", candidate_ids)
    print(f"Deleted existing matches for {len(candidate_ids)} candidates")
    
    regenerated_count = 0
    for candidate_id, name, skills_json, experience_years, resume_text, applied_for in candidates:
        try:
            # Parse skills from JSON
            skills = json.loads(skills_json) if skills_json else []
            
            # Create candidate data structure
            candidate_data = {
                'candidate_id': candidate_id,
                'name': name,
                'skills': skills,
                'experience_years': experience_years,
                'resume_text': resume_text,
                'applied_for': applied_for
            }
            
            # Generate matches using the improved AI model
            matches = improved_talent_matcher.match_candidate_to_jobs(candidate_data, top_k=5)
            
            # Insert new matches into database
            for match in matches:
                cursor.execute("""
                    INSERT INTO matches (
                        candidate_id, job_id, similarity_score, confidence_band, 
                        explanation, created_at
                    ) VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (
                    candidate_id,
                    match['job_id'],
                    match['similarity_score'],
                    match['confidence_band'],
                    match['explanation']
                ))
            
            print(f"Generated {len(matches)} matches for {name} ({candidate_id})")
            if matches:
                best_match = matches[0]
                print(f"  Best match: {best_match['title']} ({best_match['similarity_score']:.1f}%)")
            
            regenerated_count += 1
            
        except Exception as e:
            print(f"Error processing candidate {candidate_id}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\nSuccessfully regenerated matches for {regenerated_count} candidates")
    return regenerated_count

if __name__ == "__main__":
    regenerate_matches_for_candidates()
