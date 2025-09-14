#!/usr/bin/env python3
"""
Demo Data Population Script for Social Media Sourcing
This script populates the sourcing database with realistic demo data for presentation purposes.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
import random
import logging
from models.social_media_sourcing import social_media_sourcer
from models.improved_ai_models import improved_talent_matcher as talent_matcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_existing_sourcing_data():
    """Clear existing sourcing data to start fresh"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Clear existing sourcing data
        cursor.execute('DELETE FROM sourcing_matches')
        cursor.execute('DELETE FROM sourced_candidates')
        cursor.execute('DELETE FROM sourcing_campaigns')
        
        conn.commit()
        conn.close()
        logger.info("Cleared existing sourcing data")
        
    except Exception as e:
        logger.error(f"Error clearing sourcing data: {e}")

def create_sample_campaigns():
    """Create sample sourcing campaigns"""
    campaigns = [
        {
            "campaign_name": "Senior React Developers",
            "target_skills": ["React", "JavaScript", "TypeScript", "Node.js"],
            "target_companies": ["Google", "Microsoft", "Netflix", "Meta"],
            "job_id": "job_001"
        },
        {
            "campaign_name": "ML Engineers - AI Team",
            "target_skills": ["Python", "Machine Learning", "TensorFlow", "PyTorch"],
            "target_companies": ["Google", "OpenAI", "Uber", "Amazon"],
            "job_id": "job_002"
        },
        {
            "campaign_name": "DevOps Specialists",
            "target_skills": ["AWS", "Docker", "Kubernetes", "Terraform"],
            "target_companies": ["Amazon", "Microsoft", "Netflix"],
            "job_id": "job_003"
        },
        {
            "campaign_name": "Full-Stack Engineers",
            "target_skills": ["React", "Python", "Node.js", "PostgreSQL"],
            "target_companies": ["Shopify", "Stripe", "Airbnb"],
            "job_id": "job_004"
        },
        {
            "campaign_name": "Data Scientists - Analytics",
            "target_skills": ["Python", "SQL", "Pandas", "Scikit-learn"],
            "target_companies": ["Uber", "Netflix", "Spotify"],
            "job_id": "job_005"
        }
    ]
    
    campaign_ids = []
    for campaign in campaigns:
        try:
            campaign_id = social_media_sourcer.create_sourcing_campaign(
                campaign["campaign_name"],
                campaign["target_skills"],
                campaign["target_companies"],
                campaign["job_id"]
            )
            campaign_ids.append(campaign_id)
            logger.info(f"Created campaign: {campaign['campaign_name']}")
        except Exception as e:
            logger.error(f"Error creating campaign {campaign['campaign_name']}: {e}")
    
    return campaign_ids

def get_enhanced_linkedin_profiles():
    """Get enhanced LinkedIn profiles with more diversity"""
    return [
        {
            "name": "Sarah Chen",
            "email": "sarah.chen@email.com",
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
            "email": "marcus.rodriguez@email.com",
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
            "email": "emily.johnson@email.com",
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
            "email": "david.kim@email.com",
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
            "email": "priya.patel@email.com",
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
        },
        {
            "name": "Alex Thompson",
            "email": "alex.thompson@email.com",
            "current_role": "Principal Engineer",
            "current_company": "Stripe",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/alex-thompson-eng",
            "profile_summary": "Principal engineer with 10+ years building scalable payment systems. Expert in distributed systems and microservices architecture.",
            "skills": ["Java", "Scala", "Kafka", "Redis", "PostgreSQL", "Kubernetes", "Go"],
            "experience_years": 12,
            "education": "MS Computer Science, Stanford",
            "connections": 1500,
            "recent_activity": "Published article on payment system design 1 week ago"
        },
        {
            "name": "Lisa Wang",
            "email": "lisa.wang@email.com",
            "current_role": "Senior Data Engineer",
            "current_company": "Airbnb",
            "location": "San Francisco, CA",
            "linkedin_url": "https://linkedin.com/in/lisa-wang-data",
            "profile_summary": "Data engineer specializing in real-time analytics and data pipelines. 6 years experience with big data technologies.",
            "skills": ["Python", "Spark", "Kafka", "Airflow", "AWS", "Snowflake", "dbt"],
            "experience_years": 6,
            "education": "BS Data Science, UC Berkeley",
            "connections": 750,
            "recent_activity": "Spoke at data engineering conference 2 weeks ago"
        },
        {
            "name": "James Wilson",
            "email": "james.wilson@email.com",
            "current_role": "Cloud Architect",
            "current_company": "Salesforce",
            "location": "Seattle, WA",
            "linkedin_url": "https://linkedin.com/in/james-wilson-cloud",
            "profile_summary": "Cloud architect with expertise in multi-cloud strategies. 9 years experience designing enterprise cloud solutions.",
            "skills": ["AWS", "Azure", "GCP", "Terraform", "Kubernetes", "Istio", "Helm"],
            "experience_years": 9,
            "education": "MS Cloud Computing, University of Washington",
            "connections": 1100,
            "recent_activity": "Presented at AWS re:Invent 3 weeks ago"
        }
    ]

def get_enhanced_github_profiles():
    """Get enhanced GitHub profiles with more diversity"""
    return [
        {
            "name": "Sarah Chen",
            "email": "sarah.chen@email.com",
            "username": "sarahchen-dev",
            "github_url": "https://github.com/sarahchen-dev",
            "bio": "Full-stack developer passionate about clean code and scalable architecture",
            "location": "Seattle, WA",
            "company": "Microsoft",
            "public_repos": 45,
            "followers": 234,
            "following": 89,
            "languages": ["JavaScript", "TypeScript", "Python", "Go"],
            "top_repositories": [
                {"name": "react-microservices", "stars": 156, "language": "JavaScript"},
                {"name": "azure-deployment-tools", "stars": 89, "language": "Python"},
                {"name": "typescript-utils", "stars": 67, "language": "TypeScript"}
            ],
            "contribution_activity": "Very active - 1,234 contributions last year",
            "recent_activity": "Pushed to react-microservices 2 days ago"
        },
        {
            "name": "Marcus Rodriguez",
            "email": "marcus.rodriguez@email.com",
            "username": "marcus-ml",
            "github_url": "https://github.com/marcus-ml",
            "bio": "ML Engineer | NLP & Computer Vision | PhD AI",
            "location": "Mountain View, CA",
            "company": "Google",
            "public_repos": 32,
            "followers": 567,
            "following": 123,
            "languages": ["Python", "Jupyter Notebook", "C++", "R"],
            "top_repositories": [
                {"name": "nlp-transformers", "stars": 445, "language": "Python"},
                {"name": "computer-vision-toolkit", "stars": 289, "language": "Python"},
                {"name": "ml-deployment", "stars": 178, "language": "Python"}
            ],
            "contribution_activity": "Active - 892 contributions last year",
            "recent_activity": "Created new repository nlp-research 1 week ago"
        },
        {
            "name": "Emily Johnson",
            "email": "emily.johnson@email.com",
            "username": "emily-devops",
            "github_url": "https://github.com/emily-devops",
            "bio": "DevOps Engineer | Infrastructure as Code | AWS Certified",
            "location": "Austin, TX",
            "company": "Amazon",
            "public_repos": 28,
            "followers": 189,
            "following": 67,
            "languages": ["Python", "Shell", "HCL", "YAML"],
            "top_repositories": [
                {"name": "terraform-aws-modules", "stars": 234, "language": "HCL"},
                {"name": "ci-cd-pipeline", "stars": 145, "language": "YAML"},
                {"name": "monitoring-stack", "stars": 98, "language": "Python"}
            ],
            "contribution_activity": "Consistent - 756 contributions last year",
            "recent_activity": "Updated terraform-aws-modules 3 days ago"
        },
        {
            "name": "Alex Thompson",
            "email": "alex.thompson@email.com",
            "username": "alex-backend",
            "github_url": "https://github.com/alex-backend",
            "bio": "Backend Engineer | Distributed Systems | Payment Infrastructure",
            "location": "San Francisco, CA",
            "company": "Stripe",
            "public_repos": 38,
            "followers": 423,
            "following": 156,
            "languages": ["Java", "Scala", "Go", "Python"],
            "top_repositories": [
                {"name": "payment-gateway", "stars": 312, "language": "Java"},
                {"name": "distributed-cache", "stars": 198, "language": "Go"},
                {"name": "microservices-framework", "stars": 156, "language": "Scala"}
            ],
            "contribution_activity": "Very active - 1,456 contributions last year",
            "recent_activity": "Released payment-gateway v2.0 1 week ago"
        },
        {
            "name": "Lisa Wang",
            "email": "lisa.wang@email.com",
            "username": "lisa-data",
            "github_url": "https://github.com/lisa-data",
            "bio": "Data Engineer | Real-time Analytics | Big Data",
            "location": "San Francisco, CA",
            "company": "Airbnb",
            "public_repos": 25,
            "followers": 298,
            "following": 89,
            "languages": ["Python", "Scala", "SQL", "Shell"],
            "top_repositories": [
                {"name": "realtime-analytics", "stars": 267, "language": "Python"},
                {"name": "data-pipeline-framework", "stars": 189, "language": "Scala"},
                {"name": "streaming-etl", "stars": 134, "language": "Python"}
            ],
            "contribution_activity": "Active - 987 contributions last year",
            "recent_activity": "Updated data-pipeline-framework 4 days ago"
        }
    ]

def populate_sourced_candidates():
    """Populate sourced candidates from LinkedIn and GitHub profiles"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        sourced_candidates = []
        
        # Process LinkedIn profiles
        linkedin_profiles = get_enhanced_linkedin_profiles()
        for profile in linkedin_profiles:
            analysis = social_media_sourcer.analyze_linkedin_profile(profile)
            
            sourced_id = str(uuid.uuid4())
            
            # Vary contact status for demo
            contact_statuses = ['not_contacted', 'contacted', 'responded', 'interviewed']
            contact_status = random.choice(contact_statuses)
            
            candidate_data = {
                "sourced_id": sourced_id,
                "name": profile['name'],
                "email": profile['email'],
                "linkedin_url": profile['linkedin_url'],
                "current_company": profile['current_company'],
                "current_role": profile['current_role'],
                "location": profile['location'],
                "skills": json.dumps(profile['skills']),
                "experience_years": profile['experience_years'],
                "sourcing_score": analysis['sourcing_score'],
                "passive_indicator": analysis['passive_score'],
                "source_platform": "LinkedIn",
                "profile_summary": profile['profile_summary'],
                "contact_status": contact_status
            }
            
            # Store in database
            cursor.execute('''
                INSERT INTO sourced_candidates 
                (sourced_id, name, email, linkedin_url, current_company, current_role, location, 
                 skills, experience_years, sourcing_score, passive_indicator, source_platform, 
                 profile_summary, contact_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                candidate_data["sourced_id"], candidate_data["name"], candidate_data["email"],
                candidate_data["linkedin_url"], candidate_data["current_company"], 
                candidate_data["current_role"], candidate_data["location"],
                candidate_data["skills"], candidate_data["experience_years"], 
                candidate_data["sourcing_score"], candidate_data["passive_indicator"], 
                candidate_data["source_platform"], candidate_data["profile_summary"],
                candidate_data["contact_status"]
            ))
            
            sourced_candidates.append(candidate_data)
            logger.info(f"Added LinkedIn candidate: {profile['name']}")
        
        # Process GitHub profiles
        github_profiles = get_enhanced_github_profiles()
        for profile in github_profiles:
            analysis = social_media_sourcer.analyze_github_profile(profile)
            
            sourced_id = str(uuid.uuid4())
            
            # Vary contact status for demo
            contact_status = random.choice(contact_statuses)
            
            candidate_data = {
                "sourced_id": sourced_id,
                "name": profile['name'],
                "email": profile['email'],
                "github_url": profile['github_url'],
                "current_company": profile.get('company', ''),
                "location": profile['location'],
                "skills": json.dumps(profile['languages']),
                "sourcing_score": analysis['technical_score'],
                "passive_indicator": 0.7,  # GitHub users are generally more passive
                "source_platform": "GitHub",
                "profile_summary": profile['bio'],
                "contact_status": contact_status
            }
            
            # Store in database
            cursor.execute('''
                INSERT INTO sourced_candidates 
                (sourced_id, name, email, github_url, current_company, location, 
                 skills, sourcing_score, passive_indicator, source_platform, 
                 profile_summary, contact_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                candidate_data["sourced_id"], candidate_data["name"], candidate_data["email"],
                candidate_data["github_url"], candidate_data["current_company"], 
                candidate_data["location"], candidate_data["skills"], 
                candidate_data["sourcing_score"], candidate_data["passive_indicator"], 
                candidate_data["source_platform"], candidate_data["profile_summary"],
                candidate_data["contact_status"]
            ))
            
            sourced_candidates.append(candidate_data)
            logger.info(f"Added GitHub candidate: {profile['name']}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Populated {len(sourced_candidates)} sourced candidates")
        return sourced_candidates
        
    except Exception as e:
        logger.error(f"Error populating sourced candidates: {e}")
        return []

def generate_job_matches(sourced_candidates):
    """Generate job matches for sourced candidates"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        total_matches = 0
        
        for candidate in sourced_candidates:
            # Get candidate skills
            try:
                skills = json.loads(candidate['skills']) if candidate['skills'] else []
            except (json.JSONDecodeError, TypeError):
                skills = []
            
            # Create candidate text for matching
            candidate_text = f"{candidate['profile_summary']} {' '.join(skills)} {candidate.get('current_role', '')} {candidate.get('current_company', '')}"
            
            # Generate matches with jobs
            matches = social_media_sourcer.match_sourced_candidate_to_jobs(
                candidate['sourced_id'], 
                talent_matcher.jobs_data
            )
            
            # Store top 3 matches for each candidate
            for match in matches[:3]:
                match_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO sourcing_matches (match_id, sourced_id, job_id, similarity_score, confidence_band, explanation)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    match_id, candidate['sourced_id'], match['job_id'], 
                    match['similarity_score'], match['confidence_band'], match['explanation']
                ))
                total_matches += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Generated {total_matches} job matches")
        return total_matches
        
    except Exception as e:
        logger.error(f"Error generating job matches: {e}")
        return 0

def update_campaign_statistics(campaign_ids):
    """Update campaign statistics with realistic numbers"""
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        # Get total sourced candidates
        cursor.execute('SELECT COUNT(*) FROM sourced_candidates')
        total_sourced = cursor.fetchone()[0]
        
        # Distribute candidates among campaigns
        candidates_per_campaign = total_sourced // len(campaign_ids) if campaign_ids else 0
        
        for i, campaign_id in enumerate(campaign_ids):
            # Vary the numbers for realism
            found = candidates_per_campaign + random.randint(-2, 3)
            contacted = max(0, found - random.randint(1, 4))
            response_rate = round(random.uniform(0.15, 0.35), 2) if contacted > 0 else 0.0
            
            cursor.execute('''
                UPDATE sourcing_campaigns 
                SET candidates_found = ?, candidates_contacted = ?, response_rate = ?
                WHERE campaign_id = ?
            ''', (found, contacted, response_rate, campaign_id))
        
        conn.commit()
        conn.close()
        
        logger.info("Updated campaign statistics")
        
    except Exception as e:
        logger.error(f"Error updating campaign statistics: {e}")

def add_historical_campaigns():
    """Add some historical campaigns to show progression"""
    historical_campaigns = [
        {
            "campaign_name": "Backend Engineers - Q3",
            "target_skills": ["Java", "Spring", "PostgreSQL", "Redis"],
            "target_companies": ["Netflix", "Uber", "Spotify"],
            "status": "completed",
            "candidates_found": 12,
            "candidates_contacted": 8,
            "response_rate": 0.25,
            "created_days_ago": 45
        },
        {
            "campaign_name": "Frontend Specialists - Mobile",
            "target_skills": ["React Native", "Flutter", "iOS", "Android"],
            "target_companies": ["Meta", "Airbnb", "Shopify"],
            "status": "completed", 
            "candidates_found": 15,
            "candidates_contacted": 12,
            "response_rate": 0.33,
            "created_days_ago": 30
        },
        {
            "campaign_name": "Security Engineers",
            "target_skills": ["Cybersecurity", "Penetration Testing", "CISSP"],
            "target_companies": ["Google", "Microsoft", "Amazon"],
            "status": "paused",
            "candidates_found": 6,
            "candidates_contacted": 3,
            "response_rate": 0.17,
            "created_days_ago": 15
        }
    ]
    
    try:
        conn = sqlite3.connect('talent_platform.db')
        cursor = conn.cursor()
        
        for campaign in historical_campaigns:
            campaign_id = str(uuid.uuid4())
            created_at = (datetime.now() - timedelta(days=campaign['created_days_ago'])).isoformat()
            
            cursor.execute('''
                INSERT INTO sourcing_campaigns 
                (campaign_id, campaign_name, target_skills, target_companies, status,
                 candidates_found, candidates_contacted, response_rate, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                campaign_id,
                campaign['campaign_name'],
                json.dumps(campaign['target_skills']),
                json.dumps(campaign['target_companies']),
                campaign['status'],
                campaign['candidates_found'],
                campaign['candidates_contacted'],
                campaign['response_rate'],
                created_at
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added {len(historical_campaigns)} historical campaigns")
        
    except Exception as e:
        logger.error(f"Error adding historical campaigns: {e}")

def main():
    """Main function to populate all demo data"""
    logger.info("Starting social media sourcing demo data population...")
    
    # Clear existing data
    clear_existing_sourcing_data()
    
    # Create sample campaigns
    campaign_ids = create_sample_campaigns()
    
    # Add historical campaigns
    add_historical_campaigns()
    
    # Populate sourced candidates
    sourced_candidates = populate_sourced_candidates()
    
    # Generate job matches
    if sourced_candidates:
        generate_job_matches(sourced_candidates)
    
    # Update campaign statistics
    if campaign_ids:
        update_campaign_statistics(campaign_ids)
    
    logger.info("Demo data population completed successfully!")
    logger.info("You can now view the sourcing dashboard with populated data.")

if __name__ == "__main__":
    main()
