import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import litellm with fallback
try:
    import litellm
    LITELLM_AVAILABLE = True
    logging.info("LiteLLM is available")
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available - using fallback methods")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTalentMatcher:
    def __init__(self):
        """Initialize the AI models for talent matching with LiteLLM support"""
        logger.info("Loading Sentence-BERT model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.jobs_data = []
        self.job_embeddings = None
        self.faiss_index = None
        
        # LiteLLM configuration with fallback models
        self.llm_config = {
            "model": "claude-3-5-sonnet",
            "max_tokens": 4000,
            "temperature": 0.3,
            "fallback_models": [
                "gpt-4o-mini",
                "claude-3-haiku",
                "gpt-3.5-turbo"
            ]
        }
        
        # Maximum prompt length to avoid "prompt too long" errors
        self.max_prompt_length = 100000  # Conservative limit
        
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
    
    def truncate_text(self, text: str, max_length: int = None) -> str:
        """Truncate text to avoid prompt length issues"""
        if max_length is None:
            max_length = self.max_prompt_length
        
        if len(text) <= max_length:
            return text
        
        # Truncate and add indicator
        truncated = text[:max_length-50]
        return truncated + "\n\n[Text truncated due to length...]"
    
    def call_llm_with_fallback(self, prompt: str, **kwargs) -> Optional[str]:
        """Call LiteLLM with fallback handling and prompt length management"""
        if not LITELLM_AVAILABLE:
            logger.warning("LiteLLM not available, using fallback method")
            return self._fallback_response(prompt)
        
        # Truncate prompt if too long
        truncated_prompt = self.truncate_text(prompt)
        
        # Try primary model first
        models_to_try = [self.llm_config["model"]] + self.llm_config["fallback_models"]
        
        for model in models_to_try:
            try:
                logger.info(f"Attempting to call {model}")
                
                response = litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": truncated_prompt}],
                    max_tokens=self.llm_config["max_tokens"],
                    temperature=self.llm_config["temperature"],
                    **kwargs
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.warning(f"Error with model {model}: {str(e)}")
                
                # Check if it's a prompt length error
                if "prompt is too long" in str(e).lower() or "prompt too long" in str(e).lower():
                    # Try with even shorter prompt
                    shorter_prompt = self.truncate_text(prompt, max_length=50000)
                    try:
                        response = litellm.completion(
                            model=model,
                            messages=[{"role": "user", "content": shorter_prompt}],
                            max_tokens=self.llm_config["max_tokens"],
                            temperature=self.llm_config["temperature"],
                            **kwargs
                        )
                        return response.choices[0].message.content
                    except Exception as e2:
                        logger.warning(f"Even shorter prompt failed for {model}: {str(e2)}")
                        continue
                
                continue
        
        logger.error("All LLM models failed, using fallback")
        return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback response when LLM is not available"""
        if "parse" in prompt.lower() and "resume" in prompt.lower():
            return "Unable to parse resume with AI - using basic extraction"
        elif "explain" in prompt.lower() or "analysis" in prompt.lower():
            return "AI analysis temporarily unavailable - using similarity-based matching"
        else:
            return "AI response temporarily unavailable"
    
    def parse_resume_with_llm(self, resume_text: str) -> Dict:
        """Enhanced resume parser using LLM with fallback"""
        prompt = f"""
        Parse the following resume and extract structured information. Return a JSON object with:
        - name: Full name of the candidate
        - skills: Array of technical skills
        - experience_years: Total years of experience (integer)
        - education: Highest education level
        - certifications: Array of certifications
        - summary: Brief professional summary
        
        Resume text:
        {resume_text}
        
        Return only valid JSON, no additional text.
        """
        
        try:
            response = self.call_llm_with_fallback(prompt)
            if response and response != "Unable to parse resume with AI - using basic extraction":
                # Try to parse JSON response
                parsed_data = json.loads(response)
                return parsed_data
        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}")
        
        # Fallback to simple parsing
        return self.parse_resume_simple(resume_text)
    
    def parse_resume_simple(self, resume_text: str) -> Dict:
        """Simple resume parser (fallback method)"""
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
            "education": "Not specified",
            "certifications": [],
            "summary": "Extracted using basic parsing",
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
            # Create candidate embedding
            candidate_embedding = self.create_candidate_embedding(candidate_data)
            
            # Search for similar jobs using FAISS
            scores, indices = self.faiss_index.search(
                candidate_embedding.reshape(1, -1).astype('float32'), 
                min(top_k, len(self.jobs_data))
            )
            
            # Prepare results
            matches = []
            for i, (score, job_idx) in enumerate(zip(scores[0], indices[0])):
                job = self.jobs_data[job_idx]
                
                # Determine confidence band
                confidence_band = self.get_confidence_band(float(score))
                
                # Generate explanation (try LLM first, fallback to simple)
                explanation = self.generate_explanation_with_llm(candidate_data, job, float(score))
                
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
    
    def generate_explanation_with_llm(self, candidate_data: Dict, job: Dict, score: float) -> str:
        """Generate explanation using LLM with fallback"""
        prompt = f"""
        Analyze the match between this candidate and job position. Provide a concise explanation (max 100 words) covering:
        1. Key matching skills/experience
        2. Potential gaps or concerns
        3. Overall fit assessment
        
        Candidate Skills: {', '.join(candidate_data.get('skills', []))}
        Experience: {candidate_data.get('experience_years', 0)} years
        
        Job Title: {job['title']}
        Required Skills: {', '.join(job.get('requirements', []))}
        
        Similarity Score: {score:.2f}
        
        Keep the explanation professional and actionable for recruiters.
        """
        
        try:
            llm_explanation = self.call_llm_with_fallback(prompt)
            if llm_explanation and "temporarily unavailable" not in llm_explanation:
                return llm_explanation
        except Exception as e:
            logger.warning(f"LLM explanation failed: {e}")
        
        # Fallback to simple explanation
        return self.generate_explanation(candidate_data, job, score)
    
    def generate_explanation(self, candidate_data: Dict, job: Dict, score: float) -> str:
        """Generate simple explanation for the match (fallback)"""
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
        
        # Enhanced training recommendations using LLM
        training_recommendations = self.generate_training_recommendations(
            list(missing_required)[:3], candidate_data, job
        )
        
        return {
            "missing_required_skills": list(missing_required),
            "missing_nice_to_have": list(missing_nice_to_have),
            "matching_skills": list(matching_skills),
            "training_recommendations": training_recommendations,
            "readiness_score": len(matching_skills) / len(job_requirements) if job_requirements else 0
        }
    
    def generate_training_recommendations(self, missing_skills: List[str], candidate_data: Dict, job: Dict) -> List[Dict]:
        """Generate training recommendations using LLM with fallback"""
        if not missing_skills:
            return []
        
        prompt = f"""
        Generate specific training recommendations for a candidate to acquire these missing skills:
        {', '.join(missing_skills)}
        
        Context:
        - Job Role: {job['title']}
        - Current Experience: {candidate_data.get('experience_years', 0)} years
        
        For each skill, provide:
        1. Priority level (High/Medium/Low)
        2. Suggested learning resources
        3. Estimated time to acquire
        
        Return as JSON array with objects containing: skill, priority, resources, time_estimate
        """
        
        try:
            llm_response = self.call_llm_with_fallback(prompt)
            if llm_response and "temporarily unavailable" not in llm_response:
                recommendations = json.loads(llm_response)
                return recommendations
        except Exception as e:
            logger.warning(f"LLM training recommendations failed: {e}")
        
        # Fallback to simple recommendations
        recommendations = []
        for skill in missing_skills:
            recommendations.append({
                "skill": skill.title(),
                "priority": "High",
                "resources": [
                    f"Online course: {skill.title()} Fundamentals",
                    f"Certification: Professional {skill.title()}"
                ],
                "time_estimate": "2-3 months"
            })
        
        return recommendations

# Global instance
enhanced_talent_matcher = EnhancedTalentMatcher()
