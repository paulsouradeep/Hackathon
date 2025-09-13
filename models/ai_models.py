import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TalentMatcher:
    def __init__(self):
        """Initialize the AI models for talent matching"""
        logger.info("Loading Sentence-BERT model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.jobs_data = []
        self.job_embeddings = None
        self.faiss_index = None
        self.load_jobs()
        
    def load_jobs(self):
        """Load job descriptions and create embeddings"""
        try:
            with open('data/jobs/jobs.json', 'r') as f:
                self.jobs_data = json.load(f)
            
            # Create job text for embedding
            job_texts = []
            for job in self.jobs_data:
                job_text = f"{job['title']} {job['summary']} {' '.join(job['requirements'])} {' '.join(job.get('nice_to_have', []))}"
                job_texts.append(job_text)
            
            # Generate embeddings
            logger.info("Generating job embeddings...")
            self.job_embeddings = self.model.encode(job_texts, normalize_embeddings=True)
            
            # Create FAISS index for fast similarity search
            dimension = self.job_embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors
            self.faiss_index.add(self.job_embeddings.astype('float32'))
            
            logger.info(f"Loaded {len(self.jobs_data)} jobs and created embeddings")
            
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
            raise
    
    def parse_resume_simple(self, resume_text: str) -> Dict:
        """Simple resume parser (can be enhanced with LLM later)"""
        # This is a simplified parser - in production, use LLM for better parsing
        lines = resume_text.split('\n')
        
        # Extract basic info
        name = lines[0] if lines else "Unknown"
        
        # Extract skills (look for SKILLS section)
        skills = []
        in_skills_section = False
        for line in lines:
            if 'SKILLS:' in line.upper():
                in_skills_section = True
                skills_text = line.split(':', 1)[1] if ':' in line else ""
                if skills_text:
                    skills.extend([s.strip() for s in skills_text.split(',')])
            elif in_skills_section and line.strip() and not line.startswith(' '):
                break
            elif in_skills_section and line.strip():
                skills.extend([s.strip() for s in line.split(',')])
        
        # Extract experience years (simple heuristic)
        experience_years = 0
        for line in lines:
            if '(' in line and ')' in line and '-' in line:
                # Look for date patterns like (2020-2024)
                try:
                    date_part = line[line.find('(')+1:line.find(')')]
                    if '-' in date_part:
                        start, end = date_part.split('-')
                        if len(start) == 4 and len(end) == 4:
                            experience_years = max(experience_years, int(end) - int(start))
                except:
                    pass
        
        return {
            "name": name,
            "skills": skills,
            "experience_years": experience_years,
            "resume_text": resume_text
        }
    
    def create_candidate_embedding(self, candidate_data: Dict) -> np.ndarray:
        """Create embedding for candidate"""
        # Combine relevant text for embedding
        candidate_text = f"{candidate_data.get('resume_text', '')} {' '.join(candidate_data.get('skills', []))}"
        embedding = self.model.encode([candidate_text], normalize_embeddings=True)
        return embedding[0]
    
    def match_candidate_to_jobs(self, candidate_data: Dict, top_k: int = 5) -> List[Dict]:
        """Match candidate to jobs using semantic similarity"""
        try:
            # Check if FAISS index is available
            if self.faiss_index is None or len(self.jobs_data) == 0:
                logger.error("FAISS index not initialized or no jobs data available")
                return []
            
            # Create candidate embedding
            candidate_embedding = self.create_candidate_embedding(candidate_data)
            
            # Search for similar jobs using FAISS
            k = min(top_k, len(self.jobs_data))
            distances, indices = self.faiss_index.search(
                candidate_embedding.reshape(1, -1).astype('float32'), 
                k
            )
            
            # Prepare results
            matches = []
            for i, (score, job_idx) in enumerate(zip(distances[0], indices[0])):
                job = self.jobs_data[job_idx]
                
                # Determine confidence band
                confidence_band = self.get_confidence_band(float(score))
                
                # Generate explanation
                explanation = self.generate_explanation(candidate_data, job, float(score))
                
                match = {
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "department": job["department"],
                    "similarity_score": float(score),
                    "confidence_band": confidence_band,
                    "explanation": explanation,
                    "job_details": job
                }
                matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching candidate: {e}")
            return []
    
    def get_confidence_band(self, score: float) -> str:
        """Determine confidence band based on similarity score"""
        if score >= 0.85:
            return "AUTO"
        elif score >= 0.70:
            return "REVIEW"
        else:
            return "HUMAN"
    
    def generate_explanation(self, candidate_data: Dict, job: Dict, score: float) -> str:
        """Generate explanation for the match"""
        candidate_skills = set([s.lower() for s in candidate_data.get('skills', [])])
        job_requirements = set([s.lower() for s in job.get('requirements', [])])
        
        # Find matching skills
        matching_skills = candidate_skills.intersection(job_requirements)
        missing_skills = job_requirements - candidate_skills
        
        explanation_parts = []
        
        if matching_skills:
            explanation_parts.append(f"Matching skills: {', '.join(list(matching_skills)[:3])}")
        
        if candidate_data.get('experience_years', 0) > 0:
            explanation_parts.append(f"{candidate_data['experience_years']} years experience")
        
        if missing_skills:
            explanation_parts.append(f"Gap areas: {', '.join(list(missing_skills)[:2])}")
        
        explanation_parts.append(f"Similarity: {score:.2f}")
        
        return " | ".join(explanation_parts)
    
    def analyze_skill_gaps(self, candidate_data: Dict, job: Dict) -> Dict:
        """Analyze skill gaps between candidate and job requirements"""
        candidate_skills = set([s.lower() for s in candidate_data.get('skills', [])])
        job_requirements = set([s.lower() for s in job.get('requirements', [])])
        job_nice_to_have = set([s.lower() for s in job.get('nice_to_have', [])])
        
        missing_required = job_requirements - candidate_skills
        missing_nice_to_have = job_nice_to_have - candidate_skills
        matching_skills = candidate_skills.intersection(job_requirements)
        
        # Simple training recommendations (can be enhanced with Knowledge Graph)
        training_recommendations = []
        for skill in list(missing_required)[:3]:
            training_recommendations.append({
                "skill": skill.title(),
                "priority": "High",
                "suggested_resources": [
                    f"Online course: {skill.title()} Fundamentals",
                    f"Certification: Professional {skill.title()}"
                ]
            })
        
        return {
            "missing_required_skills": list(missing_required),
            "missing_nice_to_have": list(missing_nice_to_have),
            "matching_skills": list(matching_skills),
            "training_recommendations": training_recommendations,
            "readiness_score": len(matching_skills) / len(job_requirements) if job_requirements else 0
        }

# Global instance
talent_matcher = TalentMatcher()
