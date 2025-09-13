#!/usr/bin/env python3
"""
Fix resume parsing for malformed PDF text extraction
"""

import sqlite3
import json
import re
from typing import Dict, List

def clean_resume_text(text: str) -> str:
    """Clean malformed resume text where words are separated by newlines"""
    # Replace multiple newlines with single spaces
    cleaned = re.sub(r'\n+', ' ', text)
    # Remove extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Clean up common PDF extraction artifacts
    cleaned = cleaned.replace('|', ' ')
    return cleaned.strip()

def extract_name_robust(text: str) -> str:
    """Extract name from resume text more robustly"""
    lines = text.split('\n')
    
    # Look for name patterns
    for line in lines[:10]:  # Check first 10 lines
        line = line.strip()
        if not line:
            continue
            
        # Skip common headers
        if any(skip in line.lower() for skip in ['resume', 'cv', 'curriculum', 'contact', 'phone', 'email', '@']):
            continue
            
        # Look for name patterns (2-4 words, mostly alphabetic)
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check if it looks like a name (mostly alphabetic)
            if all(word.replace('.', '').replace(',', '').isalpha() for word in words):
                return line
    
    # Fallback: look for capitalized words
    words = text.split()[:20]  # First 20 words
    name_words = []
    for word in words:
        if word.istitle() and word.isalpha() and len(word) > 1:
            name_words.append(word)
            if len(name_words) >= 2:
                break
    
    if len(name_words) >= 2:
        return ' '.join(name_words)
    
    return "Unknown Candidate"

def extract_skills_robust(text: str) -> List[str]:
    """Extract skills from resume text more robustly"""
    text_lower = text.lower()
    
    # Comprehensive skill lists
    skills_database = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala', 'php', 'ruby', 'swift', 'kotlin',
        'c', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell',
        
        # Web Technologies
        'html', 'css', 'react', 'angular', 'vue', 'nodejs', 'express', 'django', 'flask', 'spring', 'laravel',
        'jquery', 'bootstrap', 'sass', 'less', 'webpack', 'babel',
        
        # Databases
        'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb', 'oracle',
        'sqlite', 'mariadb', 'nosql',
        
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab', 'github',
        'ci/cd', 'devops', 'microservices', 'serverless', 'lambda', 'ec2', 's3', 'rds',
        
        # Data & Analytics
        'spark', 'hadoop', 'kafka', 'airflow', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
        'machine learning', 'deep learning', 'data science', 'analytics', 'tableau', 'power bi', 'excel',
        
        # Mobile
        'ios', 'android', 'react native', 'flutter', 'xamarin', 'cordova',
        
        # Other Technologies
        'git', 'linux', 'unix', 'windows', 'api', 'rest', 'graphql', 'json', 'xml', 'agile', 'scrum',
        'jira', 'confluence', 'slack', 'teams'
    }
    
    found_skills = set()
    
    # Direct skill matching
    for skill in skills_database:
        if skill in text_lower:
            found_skills.add(skill)
    
    # Look for skills in common sections
    skill_sections = []
    lines = text.split('\n')
    in_skills_section = False
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check for skills section headers
        if any(header in line.lower() for header in ['skill', 'technolog', 'competenc', 'proficienc', 'expertise']):
            in_skills_section = True
            # Extract skills from the same line if it contains a colon
            if ':' in line:
                skills_text = line.split(':', 1)[1]
                skill_sections.append(skills_text)
        elif in_skills_section:
            # Continue collecting skills until we hit a new section
            if line_clean.isupper() or any(section in line.lower() for section in ['experience', 'education', 'project', 'work']):
                in_skills_section = False
            else:
                skill_sections.append(line_clean)
    
    # Parse skills from collected sections
    for section in skill_sections:
        # Split by common delimiters
        potential_skills = re.split(r'[,;|•\-\n\t]', section)
        for skill in potential_skills:
            skill = skill.strip().lower()
            if skill in skills_database:
                found_skills.add(skill)
    
    return list(found_skills)

def extract_experience_robust(text: str) -> int:
    """Extract years of experience more robustly"""
    text_lower = text.lower()
    max_years = 0
    
    # Pattern 1: "X years of experience"
    patterns = [
        r'(\d+)\s*years?\s*of\s*experience',
        r'(\d+)\s*years?\s*experience',
        r'(\d+)\+?\s*years?\s*in',
        r'over\s*(\d+)\s*years?',
        r'more than\s*(\d+)\s*years?'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            years = int(match)
            if 0 < years <= 50:  # Reasonable range
                max_years = max(max_years, years)
    
    # Pattern 2: Date ranges (YYYY-YYYY)
    date_ranges = re.findall(r'(\d{4})\s*[-–—]\s*(\d{4})', text)
    for start, end in date_ranges:
        start_year, end_year = int(start), int(end)
        if 1990 <= start_year <= 2024 and start_year < end_year <= 2024:
            duration = end_year - start_year
            max_years = max(max_years, duration)
    
    # Pattern 3: Date ranges with "present" or "current"
    present_ranges = re.findall(r'(\d{4})\s*[-–—]\s*(present|current|now)', text_lower)
    current_year = 2024
    for start_year, _ in present_ranges:
        start_year = int(start_year)
        if 1990 <= start_year <= current_year:
            duration = current_year - start_year
            max_years = max(max_years, duration)
    
    return max_years

def parse_resume_improved(resume_text: str) -> Dict:
    """Improved resume parser that handles malformed PDF text"""
    # Clean the text first
    cleaned_text = clean_resume_text(resume_text)
    
    # Extract information
    name = extract_name_robust(cleaned_text)
    skills = extract_skills_robust(cleaned_text)
    experience_years = extract_experience_robust(cleaned_text)
    
    return {
        "name": name,
        "skills": skills,
        "experience_years": experience_years,
        "resume_text": cleaned_text  # Store cleaned version
    }

def fix_existing_resumes():
    """Fix all existing resumes in the database"""
    conn = sqlite3.connect('talent_platform.db')
    cursor = conn.cursor()
    
    # Get all candidates with empty skills or zero experience
    cursor.execute("""
        SELECT candidate_id, resume_text 
        FROM candidates 
        WHERE candidate_id NOT LIKE 'cand_%' 
        AND (skills = '[]' OR experience_years = 0)
    """)
    
    candidates_to_fix = cursor.fetchall()
    print(f"Found {len(candidates_to_fix)} candidates to fix")
    
    fixed_count = 0
    for candidate_id, resume_text in candidates_to_fix:
        if not resume_text:
            continue
            
        # Parse the resume with improved parser
        parsed_data = parse_resume_improved(resume_text)
        
        # Update the candidate record
        cursor.execute("""
            UPDATE candidates 
            SET name = ?, skills = ?, experience_years = ?, resume_text = ?
            WHERE candidate_id = ?
        """, (
            parsed_data['name'],
            json.dumps(parsed_data['skills']),
            parsed_data['experience_years'],
            parsed_data['resume_text'],
            candidate_id
        ))
        
        print(f"Fixed candidate {candidate_id}:")
        print(f"  Name: {parsed_data['name']}")
        print(f"  Skills: {parsed_data['skills'][:5]}{'...' if len(parsed_data['skills']) > 5 else ''}")
        print(f"  Experience: {parsed_data['experience_years']} years")
        print()
        
        fixed_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Successfully fixed {fixed_count} candidates")
    return fixed_count

if __name__ == "__main__":
    fix_existing_resumes()
