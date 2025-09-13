import json
import re
import requests
from typing import List, Dict, Optional, Tuple
import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import uuid
from urllib.parse import urlparse, urljoin
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaSourcer:
    def __init__(self):
        """Initialize the social media sourcing AI"""
        logger.info("Loading Sentence-BERT model for social media analysis...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.init_sourcing_db()
        
        # Skill keywords for different tech domains
        self.skill_domains = {
            "frontend": ["react", "vue", "angular", "javascript", "typescript", "html", "css", "sass", "webpack"],
            "backend": ["python", "java", "node.js", "express", "django", "flask", "spring", "php", "ruby"],
            "mobile": ["react native", "flutter", "swift", "kotlin", "ios", "android", "xamarin"],
            "data": ["python", "sql", "pandas", "numpy", "tensorflow", "pytorch", "machine learning", "data science"],
            "devops": ["docker", "kubernetes", "aws", "azure", "gcp", "jenkins", "terraform", "ansible"],
            "cloud": ["aws", "azure", "google cloud", "serverless", "microservices", "containers"]
        }
        
        # Company indicators for passive candidates
        self.target_companies = [
            "google", "microsoft", "amazon", "apple", "meta", "netflix", "uber", "airbnb",
            "shopify", "stripe", "slack", "zoom", "salesforce", "oracle", "ibm", "intel",
            "nvidia", "adobe", "atlassian", "github", "gitlab", "docker", "mongodb"
        ]
    
    def init_sourcing_db(self):
        """Initialize database tables for social media sourcing"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            # Create sourced_candidates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sourced_candidates (
                    sourced_id TEXT PRIMARY KEY,
                    name TEXT,
                    email TEXT,
                    linkedin_url TEXT,
                    github_url TEXT,
                    current_company TEXT,
                    current_role TEXT,
                    location TEXT,
                    skills TEXT,
                    experience_years INTEGER,
                    sourcing_score REAL,
                    passive_indicator REAL,
                    contact_status TEXT DEFAULT 'not_contacted',
                    source_platform TEXT,
                    profile_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create sourcing_campaigns table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sourcing_campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    campaign_name TEXT,
                    target_skills TEXT,
                    target_companies TEXT,
                    job_id TEXT,
                    status TEXT DEFAULT 'active',
                    candidates_found INTEGER DEFAULT 0,
                    candidates_contacted INTEGER DEFAULT 0,
                    response_rate REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create sourcing_matches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sourcing_matches (
                    match_id TEXT PRIMARY KEY,
                    sourced_id TEXT,
                    job_id TEXT,
                    similarity_score REAL,
                    confidence_band TEXT,
                    explanation TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sourced_id) REFERENCES sourced_candidates (sourced_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Social media sourcing database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing sourcing database: {e}")
    
    def simulate_linkedin_search(self, keywords: List[str], location: str = "", company: str = "") -> List[Dict]:
        """Simulate LinkedIn profile search (in production, use LinkedIn API or web scraping)"""
        # This simulates finding LinkedIn profiles based on search criteria
        # In production, you would integrate with LinkedIn API or use web scraping tools
        
        simulated_profiles = [
            {
                "name": "Sarah Chen",
                "current_role": "Senior Software Engineer",
                "current_company": "Microsoft",
                "location": "Seattle, WA",
                "linkedin_url": "https://linkedin.com/in/sarah-chen-dev",
                "profile_summary": "Full-stack developer with 6 years experience in React, Node.js, and Azure cloud services. Led multiple high-impact projects at Microsoft.",
                "skills": ["React", "Node.js", "TypeScript", "Azure", "Docker", "Kubernetes", "Python"],
                "experience_years": 6,
                "education": "MS Computer Science, University of Washington",
                "connections": 500,
                "recent_activity": "Posted about microservices architecture 2 days ago"
            },
            {
                "name": "Marcus Rodriguez",
                "current_role": "Machine Learning Engineer",
                "current_company": "Google",
                "location": "Mountain View, CA",
                "linkedin_url": "https://linkedin.com/in/marcus-rodriguez-ml",
                "profile_summary": "ML Engineer specializing in NLP and computer vision. PhD in AI from Stanford. 8 years experience building production ML systems.",
                "skills": ["Python", "TensorFlow", "PyTorch", "Kubernetes", "GCP", "SQL", "Spark"],
                "experience_years": 8,
                "education": "PhD AI, Stanford University",
                "connections": 1200,
                "recent_activity": "Shared article about transformer models 1 week ago"
            },
            {
                "name": "Emily Johnson",
                "current_role": "DevOps Engineer",
                "current_company": "Amazon",
                "location": "Austin, TX",
                "linkedin_url": "https://linkedin.com/in/emily-johnson-devops",
                "profile_summary": "DevOps specialist with expertise in AWS, Terraform, and CI/CD pipelines. 5 years experience scaling infrastructure for high-traffic applications.",
                "skills": ["AWS", "Terraform", "Docker", "Jenkins", "Python", "Bash", "Monitoring"],
                "experience_years": 5,
                "education": "BS Computer Engineering, UT Austin",
                "connections": 800,
                "recent_activity": "Commented on infrastructure automation post 3 days ago"
            },
            {
                "name": "David Kim",
                "current_role": "Frontend Architect",
                "current_company": "Netflix",
                "location": "Los Angeles, CA",
                "linkedin_url": "https://linkedin.com/in/david-kim-frontend",
                "profile_summary": "Frontend architect with deep expertise in React ecosystem. Led UI/UX initiatives for Netflix's streaming platform. 7 years experience.",
                "skills": ["React", "Redux", "TypeScript", "Webpack", "CSS", "JavaScript", "GraphQL"],
                "experience_years": 7,
                "education": "BS Computer Science, UCLA",
                "connections": 950,
                "recent_activity": "Posted about React 18 features 5 days ago"
            },
            {
                "name": "Priya Patel",
                "current_role": "Data Scientist",
                "current_company": "Uber",
                "location": "San Francisco, CA",
                "linkedin_url": "https://linkedin.com/in/priya-patel-data",
                "profile_summary": "Data scientist focused on recommendation systems and predictive analytics. 4 years experience in ride-sharing and marketplace optimization.",
                "skills": ["Python", "SQL", "Pandas", "Scikit-learn", "TensorFlow", "Spark", "Tableau"],
                "experience_years": 4,
                "education": "MS Data Science, UC Berkeley",
                "connections": 600,
                "recent_activity": "Shared insights on A/B testing 1 week ago"
            }
        ]
        
        # Filter profiles based on keywords
        filtered_profiles = []
        for profile in simulated_profiles:
            profile_text = f"{profile['profile_summary']} {' '.join(profile['skills'])} {profile['current_role']}"
            if any(keyword.lower() in profile_text.lower() for keyword in keywords):
                if not location or location.lower() in profile['location'].lower():
                    if not company or company.lower() in profile['current_company'].lower():
                        filtered_profiles.append(profile)
        
        return filtered_profiles
    
    def simulate_github_search(self, keywords: List[str], language: str = "") -> List[Dict]:
        """Simulate GitHub profile search (in production, use GitHub API)"""
        # This simulates finding GitHub profiles based on search criteria
        # In production, you would use GitHub API to search users and repositories
        
        simulated_github_profiles = [
            {
                "username": "sarahchen-dev",
                "name": "Sarah Chen",
                "github_url": "https://github.com/sarahchen-dev",
                "bio": "Full-stack developer passionate about clean code and scalable architecture",
                "location": "Seattle, WA",
                "company": "Microsoft",
                "public_repos": 45,
                "followers": 234,
                "following": 89,
                "languages": ["JavaScript", "TypeScript", "Python", "Go"],
                "top_repositories": [
                    {"name": "react-microservices", "stars": 156, "language": "JavaScript", "description": "Microservices architecture with React frontend"},
                    {"name": "azure-deployment-tools", "stars": 89, "language": "Python", "description": "Automated deployment tools for Azure"},
                    {"name": "typescript-utils", "stars": 67, "language": "TypeScript", "description": "Utility library for TypeScript projects"}
                ],
                "contribution_activity": "Very active - 1,234 contributions last year",
                "recent_activity": "Pushed to react-microservices 2 days ago"
            },
            {
                "username": "marcus-ml",
                "name": "Marcus Rodriguez",
                "github_url": "https://github.com/marcus-ml",
                "bio": "ML Engineer | NLP & Computer Vision | PhD AI",
                "location": "Mountain View, CA",
                "company": "Google",
                "public_repos": 32,
                "followers": 567,
                "following": 123,
                "languages": ["Python", "Jupyter Notebook", "C++", "R"],
                "top_repositories": [
                    {"name": "nlp-transformers", "stars": 445, "language": "Python", "description": "Advanced NLP models using transformers"},
                    {"name": "computer-vision-toolkit", "stars": 289, "language": "Python", "description": "CV toolkit for production ML systems"},
                    {"name": "ml-deployment", "stars": 178, "language": "Python", "description": "MLOps tools for model deployment"}
                ],
                "contribution_activity": "Active - 892 contributions last year",
                "recent_activity": "Created new repository nlp-research 1 week ago"
            },
            {
                "username": "emily-devops",
                "name": "Emily Johnson",
                "github_url": "https://github.com/emily-devops",
                "bio": "DevOps Engineer | Infrastructure as Code | AWS Certified",
                "location": "Austin, TX",
                "company": "Amazon",
                "public_repos": 28,
                "followers": 189,
                "following": 67,
                "languages": ["Python", "Shell", "HCL", "YAML"],
                "top_repositories": [
                    {"name": "terraform-aws-modules", "stars": 234, "language": "HCL", "description": "Reusable Terraform modules for AWS"},
                    {"name": "ci-cd-pipeline", "stars": 145, "language": "YAML", "description": "Complete CI/CD pipeline templates"},
                    {"name": "monitoring-stack", "stars": 98, "language": "Python", "description": "Comprehensive monitoring solution"}
                ],
                "contribution_activity": "Consistent - 756 contributions last year",
                "recent_activity": "Updated terraform-aws-modules 3 days ago"
            }
        ]
        
        # Filter profiles based on keywords and language
        filtered_profiles = []
        for profile in simulated_github_profiles:
            profile_text = f"{profile['bio']} {' '.join(profile['languages'])} {' '.join([repo['description'] for repo in profile['top_repositories']])}"
            if any(keyword.lower() in profile_text.lower() for keyword in keywords):
                if not language or language.lower() in [lang.lower() for lang in profile['languages']]:
                    filtered_profiles.append(profile)
        
        return filtered_profiles
    
    def analyze_linkedin_profile(self, profile: Dict) -> Dict:
        """Analyze LinkedIn profile and extract insights"""
        # Calculate passive candidate score
        passive_indicators = {
            "high_connections": profile.get('connections', 0) > 500,
            "recent_activity": 'days ago' in profile.get('recent_activity', ''),
            "senior_role": any(title in profile.get('current_role', '').lower() 
                             for title in ['senior', 'lead', 'principal', 'architect', 'manager']),
            "target_company": profile.get('current_company', '').lower() in [c.lower() for c in self.target_companies],
            "advanced_education": any(degree in profile.get('education', '').lower() 
                                    for degree in ['ms', 'phd', 'master', 'doctorate'])
        }
        
        passive_score = sum(passive_indicators.values()) / len(passive_indicators)
        
        # Extract skills and calculate experience relevance
        skills = profile.get('skills', [])
        experience_years = profile.get('experience_years', 0)
        
        # Calculate overall sourcing score
        sourcing_score = self.calculate_sourcing_score(profile, passive_score)
        
        return {
            "passive_score": passive_score,
            "sourcing_score": sourcing_score,
            "skills": skills,
            "experience_years": experience_years,
            "passive_indicators": passive_indicators,
            "profile_strength": self.assess_profile_strength(profile)
        }
    
    def analyze_github_profile(self, profile: Dict) -> Dict:
        """Analyze GitHub profile and extract technical insights"""
        # Calculate technical activity score
        activity_indicators = {
            "high_repos": profile.get('public_repos', 0) > 20,
            "good_followers": profile.get('followers', 0) > 100,
            "active_contributor": 'active' in profile.get('contribution_activity', '').lower(),
            "recent_commits": 'days ago' in profile.get('recent_activity', ''),
            "popular_repos": any(repo.get('stars', 0) > 50 for repo in profile.get('top_repositories', []))
        }
        
        technical_score = sum(activity_indicators.values()) / len(activity_indicators)
        
        # Extract programming languages and skills
        languages = profile.get('languages', [])
        top_repos = profile.get('top_repositories', [])
        
        # Calculate code quality indicators
        code_quality = self.assess_code_quality(profile)
        
        return {
            "technical_score": technical_score,
            "languages": languages,
            "top_repositories": top_repos,
            "activity_indicators": activity_indicators,
            "code_quality": code_quality
        }
    
    def calculate_sourcing_score(self, profile: Dict, passive_score: float) -> float:
        """Calculate overall sourcing score for a candidate"""
        factors = {
            "experience": min(profile.get('experience_years', 0) / 10, 1.0),  # Normalize to 0-1
            "passive_score": passive_score,
            "skill_relevance": len(profile.get('skills', [])) / 10,  # Normalize based on skill count
            "company_prestige": 1.0 if profile.get('current_company', '').lower() in [c.lower() for c in self.target_companies] else 0.5,
            "role_seniority": 1.0 if any(title in profile.get('current_role', '').lower() 
                                       for title in ['senior', 'lead', 'principal', 'architect', 'manager']) else 0.7
        }
        
        # Weighted average
        weights = {"experience": 0.25, "passive_score": 0.3, "skill_relevance": 0.2, "company_prestige": 0.15, "role_seniority": 0.1}
        score = sum(factors[key] * weights[key] for key in factors)
        
        return min(score, 1.0)
    
    def assess_profile_strength(self, profile: Dict) -> str:
        """Assess the overall strength of a LinkedIn profile"""
        strength_indicators = [
            profile.get('connections', 0) > 300,
            len(profile.get('skills', [])) > 5,
            profile.get('experience_years', 0) > 3,
            'recent_activity' in profile and 'days ago' in profile['recent_activity'],
            any(degree in profile.get('education', '').lower() for degree in ['ms', 'phd', 'master', 'bachelor'])
        ]
        
        strength_score = sum(strength_indicators) / len(strength_indicators)
        
        if strength_score >= 0.8:
            return "Strong"
        elif strength_score >= 0.6:
            return "Good"
        elif strength_score >= 0.4:
            return "Average"
        else:
            return "Weak"
    
    def assess_code_quality(self, profile: Dict) -> Dict:
        """Assess code quality based on GitHub profile indicators"""
        repos = profile.get('top_repositories', [])
        
        quality_indicators = {
            "has_documentation": any('readme' in repo.get('description', '').lower() for repo in repos),
            "popular_projects": any(repo.get('stars', 0) > 100 for repo in repos),
            "diverse_languages": len(profile.get('languages', [])) > 3,
            "recent_activity": 'days ago' in profile.get('recent_activity', ''),
            "good_naming": any(len(repo.get('name', '').split('-')) > 1 for repo in repos)
        }
        
        quality_score = sum(quality_indicators.values()) / len(quality_indicators)
        
        return {
            "quality_score": quality_score,
            "indicators": quality_indicators,
            "assessment": "High" if quality_score >= 0.7 else "Medium" if quality_score >= 0.4 else "Low"
        }
    
    def create_sourcing_campaign(self, campaign_name: str, target_skills: List[str], 
                                target_companies: List[str] = None, job_id: str = None) -> str:
        """Create a new sourcing campaign"""
        try:
            campaign_id = str(uuid.uuid4())
            
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sourcing_campaigns (campaign_id, campaign_name, target_skills, target_companies, job_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                campaign_name,
                json.dumps(target_skills),
                json.dumps(target_companies or []),
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created sourcing campaign: {campaign_name}")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error creating sourcing campaign: {e}")
            raise
    
    def run_sourcing_campaign(self, campaign_id: str) -> Dict:
        """Run a sourcing campaign to find candidates"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            # Get campaign details
            cursor.execute('SELECT * FROM sourcing_campaigns WHERE campaign_id = ?', (campaign_id,))
            campaign_row = cursor.fetchone()
            
            if not campaign_row:
                raise ValueError("Campaign not found")
            
            campaign_name = campaign_row[1]
            target_skills = json.loads(campaign_row[2])
            target_companies = json.loads(campaign_row[3])
            job_id = campaign_row[4]
            
            # Search LinkedIn profiles
            linkedin_profiles = self.simulate_linkedin_search(target_skills)
            
            # Search GitHub profiles
            github_profiles = self.simulate_github_search(target_skills)
            
            # Process and store candidates
            sourced_candidates = []
            
            # Process LinkedIn profiles
            for profile in linkedin_profiles:
                analysis = self.analyze_linkedin_profile(profile)
                
                sourced_id = str(uuid.uuid4())
                candidate_data = {
                    "sourced_id": sourced_id,
                    "name": profile['name'],
                    "linkedin_url": profile['linkedin_url'],
                    "current_company": profile['current_company'],
                    "current_role": profile['current_role'],
                    "location": profile['location'],
                    "skills": json.dumps(profile['skills']),
                    "experience_years": profile['experience_years'],
                    "sourcing_score": analysis['sourcing_score'],
                    "passive_indicator": analysis['passive_score'],
                    "source_platform": "LinkedIn",
                    "profile_summary": profile['profile_summary']
                }
                
                # Store in database
                cursor.execute('''
                    INSERT INTO sourced_candidates 
                    (sourced_id, name, linkedin_url, current_company, current_role, location, 
                     skills, experience_years, sourcing_score, passive_indicator, source_platform, profile_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate_data["sourced_id"], candidate_data["name"], candidate_data["linkedin_url"],
                    candidate_data["current_company"], candidate_data["current_role"], candidate_data["location"],
                    candidate_data["skills"], candidate_data["experience_years"], candidate_data["sourcing_score"],
                    candidate_data["passive_indicator"], candidate_data["source_platform"], candidate_data["profile_summary"]
                ))
                
                sourced_candidates.append(candidate_data)
            
            # Process GitHub profiles
            for profile in github_profiles:
                analysis = self.analyze_github_profile(profile)
                
                sourced_id = str(uuid.uuid4())
                candidate_data = {
                    "sourced_id": sourced_id,
                    "name": profile['name'],
                    "github_url": profile['github_url'],
                    "current_company": profile.get('company', ''),
                    "location": profile['location'],
                    "skills": json.dumps(profile['languages']),
                    "sourcing_score": analysis['technical_score'],
                    "passive_indicator": 0.7,  # GitHub users are generally more passive
                    "source_platform": "GitHub",
                    "profile_summary": profile['bio']
                }
                
                # Store in database
                cursor.execute('''
                    INSERT INTO sourced_candidates 
                    (sourced_id, name, github_url, current_company, location, 
                     skills, sourcing_score, passive_indicator, source_platform, profile_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    candidate_data["sourced_id"], candidate_data["name"], candidate_data["github_url"],
                    candidate_data["current_company"], candidate_data["location"],
                    candidate_data["skills"], candidate_data["sourcing_score"],
                    candidate_data["passive_indicator"], candidate_data["source_platform"], candidate_data["profile_summary"]
                ))
                
                sourced_candidates.append(candidate_data)
            
            # Update campaign statistics
            cursor.execute('''
                UPDATE sourcing_campaigns 
                SET candidates_found = ? 
                WHERE campaign_id = ?
            ''', (len(sourced_candidates), campaign_id))
            
            conn.commit()
            conn.close()
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign_name,
                "candidates_found": len(sourced_candidates),
                "linkedin_profiles": len(linkedin_profiles),
                "github_profiles": len(github_profiles),
                "sourced_candidates": sourced_candidates
            }
            
        except Exception as e:
            logger.error(f"Error running sourcing campaign: {e}")
            raise
    
    def match_sourced_candidate_to_jobs(self, sourced_id: str, jobs_data: List[Dict]) -> List[Dict]:
        """Match a sourced candidate to available jobs"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            # Get candidate data
            cursor.execute('SELECT * FROM sourced_candidates WHERE sourced_id = ?', (sourced_id,))
            candidate_row = cursor.fetchone()
            
            if not candidate_row:
                raise ValueError("Sourced candidate not found")
            
            # Parse candidate skills
            skills = json.loads(candidate_row[8]) if candidate_row[8] else []
            
            # Create candidate text for embedding
            candidate_text = f"{candidate_row[14]} {' '.join(skills)} {candidate_row[6]} {candidate_row[7]}"
            candidate_embedding = self.model.encode([candidate_text], normalize_embeddings=True)[0]
            
            # Calculate similarity with jobs
            matches = []
            for job in jobs_data:
                job_text = f"{job['title']} {job['summary']} {' '.join(job['requirements'])} {' '.join(job.get('nice_to_have', []))}"
                job_embedding = self.model.encode([job_text], normalize_embeddings=True)[0]
                
                # Calculate cosine similarity
                similarity = np.dot(candidate_embedding, job_embedding)
                
                # Determine confidence band
                confidence_band = self.get_confidence_band(float(similarity))
                
                # Generate explanation
                explanation = self.generate_sourcing_explanation(candidate_row, job, float(similarity))
                
                match = {
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "department": job["department"],
                    "similarity_score": float(similarity),
                    "confidence_band": confidence_band,
                    "explanation": explanation,
                    "job_details": job
                }
                matches.append(match)
            
            # Sort by similarity score
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Store top matches in database
            for match in matches[:5]:  # Store top 5 matches
                match_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO sourcing_matches (match_id, sourced_id, job_id, similarity_score, confidence_band, explanation)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    match_id, sourced_id, match['job_id'], match['similarity_score'], 
                    match['confidence_band'], match['explanation']
                ))
            
            conn.commit()
            conn.close()
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching sourced candidate: {e}")
            raise
    
    def get_confidence_band(self, score: float) -> str:
        """Determine confidence band based on similarity score"""
        if score >= 0.85:
            return "AUTO"
        elif score >= 0.70:
            return "REVIEW"
        else:
            return "HUMAN"
    
    def generate_sourcing_explanation(self, candidate_row: tuple, job: Dict, score: float) -> str:
        """Generate explanation for sourced candidate match"""
        skills = json.loads(candidate_row[8]) if candidate_row[8] else []
        candidate_skills = set([s.lower() for s in skills])
        job_requirements = set([s.lower() for s in job.get('requirements', [])])
        
        # Find matching skills
        matching_skills = candidate_skills.intersection(job_requirements)
        missing_skills = job_requirements - candidate_skills
        
        explanation_parts = []
        
        if matching_skills:
            explanation_parts.append(f"Skills match: {', '.join(list(matching_skills)[:3])}")
        
        if candidate_row[9]:  # experience_years
            explanation_parts.append(f"{candidate_row[9]} years experience")
        
        if candidate_row[4]:  # current_company
            explanation_parts.append(f"Currently at {candidate_row[4]}")
        
        if missing_skills:
            explanation_parts.append(f"Gap: {', '.join(list(missing_skills)[:2])}")
        
        explanation_parts.append(f"Score: {score:.2f}")
        
        return " | ".join(explanation_parts)
    
    def get_sourcing_analytics(self) -> Dict:
        """Get analytics for sourcing campaigns"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            # Total sourced candidates
            cursor.execute('SELECT COUNT(*) FROM sourced_candidates')
            total_sourced = cursor.fetchone()[0]
            
            # Platform distribution
            cursor.execute('SELECT source_platform, COUNT(*) FROM sourced_candidates GROUP BY source_platform')
            platform_distribution = dict(cursor.fetchall())
            
            # Average sourcing scores
            cursor.execute('SELECT AVG(sourcing_score) FROM sourced_candidates')
            avg_sourcing_score = cursor.fetchone()[0] or 0
            
            # Passive candidate percentage
            cursor.execute('SELECT AVG(passive_indicator) FROM sourced_candidates')
            avg_passive_score = cursor.fetchone()[0] or 0
            
            # Contact status distribution
            cursor.execute('SELECT contact_status, COUNT(*) FROM sourced_candidates GROUP BY contact_status')
            contact_distribution = dict(cursor.fetchall())
            
            # Active campaigns
            cursor.execute('SELECT COUNT(*) FROM sourcing_campaigns WHERE status = "active"')
            active_campaigns = cursor.fetchone()[0]
            
            # Top companies
            cursor.execute('''
                SELECT current_company, COUNT(*) as count 
                FROM sourced_candidates 
                WHERE current_company IS NOT NULL AND current_company != ""
                GROUP BY current_company 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_companies = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_sourced": total_sourced,
                "platform_distribution": platform_distribution,
                "avg_sourcing_score": round(avg_sourcing_score, 2),
                "avg_passive_score": round(avg_passive_score, 2),
                "contact_distribution": contact_distribution,
                "active_campaigns": active_campaigns,
                "top_companies": top_companies
            }
            
        except Exception as e:
            logger.error(f"Error getting sourcing analytics: {e}")
            return {
                "total_sourced": 0,
                "platform_distribution": {},
                "avg_sourcing_score": 0,
                "avg_passive_score": 0,
                "contact_distribution": {},
                "active_campaigns": 0,
                "top_companies": []
            }

# Global instance
social_media_sourcer = SocialMediaSourcer()
