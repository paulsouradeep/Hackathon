import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
import re
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedTalentMatcher:
    def __init__(self):
        """Initialize the improved AI models for talent matching"""
        logger.info("Loading Sentence-BERT model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.jobs_data = []
        self.job_embeddings = None
        self.faiss_index = None
        self.tfidf_vectorizer = None
        self.job_tfidf_vectors = None
        
        # Skill categories for better matching
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala'],
            'cloud': ['aws', 'gcp', 'azure', 'cloud', 'ec2', 's3', 'lambda', 'bigquery'],
            'data': ['sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch'],
            'ml_ai': ['tensorflow', 'pytorch', 'scikit-learn', 'machine learning', 'deep learning', 'nlp', 'computer vision'],
            'devops': ['docker', 'kubernetes', 'terraform', 'jenkins', 'ci/cd', 'ansible', 'prometheus'],
            'frontend': ['react', 'angular', 'vue', 'html', 'css', 'javascript', 'typescript'],
            'backend': ['microservices', 'api', 'rest', 'graphql', 'flask', 'django', 'spring'],
            'data_engineering': ['spark', 'kafka', 'airflow', 'etl', 'data pipeline', 'hadoop']
        }
        
        self.load_jobs()
        
    def load_jobs(self):
        """Load job descriptions and create embeddings"""
        try:
            with open('data/jobs/jobs.json', 'r') as f:
                self.jobs_data = json.load(f)
            
            # Create job text for embedding
            job_texts = []
            job_skill_texts = []
            
            for job in self.jobs_data:
                # Enhanced job text with weighted components
                job_text = f"{job['title']} {job['title']} {job['summary']} {' '.join(job['requirements'])} {' '.join(job.get('nice_to_have', []))}"
                job_texts.append(job_text)
                
                # Create skill-focused text for TF-IDF
                skill_text = f"{' '.join(job['requirements'])} {' '.join(job.get('nice_to_have', []))}"
                job_skill_texts.append(skill_text.lower())
            
            # Generate semantic embeddings
            logger.info("Generating job embeddings...")
            self.job_embeddings = self.model.encode(job_texts, normalize_embeddings=True)
            
            # Create TF-IDF vectors for skill matching
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            self.job_tfidf_vectors = self.tfidf_vectorizer.fit_transform(job_skill_texts)
            
            # Create FAISS index for fast similarity search (using cosine similarity)
            dimension = self.job_embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for normalized vectors = cosine similarity
            self.faiss_index.add(self.job_embeddings.astype('float32'))
            
            logger.info(f"Loaded {len(self.jobs_data)} jobs and created embeddings")
            
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
            raise
    
    def normalize_skill_name(self, skill: str) -> str:
        """Normalize skill names for better matching"""
        skill = skill.lower().strip()
        
        # Common skill normalizations
        normalizations = {
            'js': 'javascript',
            'ts': 'typescript',
            'k8s': 'kubernetes',
            'tf': 'tensorflow',
            'ml': 'machine learning',
            'ai': 'artificial intelligence',
            'dl': 'deep learning',
            'cv': 'computer vision',
            'nlp': 'natural language processing',
            'aws ec2': 'aws',
            'aws s3': 'aws',
            'gcp bigquery': 'gcp',
            'react.js': 'react',
            'node.js': 'nodejs',
            'vue.js': 'vue'
        }
        
        return normalizations.get(skill, skill)
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from text using pattern matching and known skill lists"""
        text_lower = text.lower()
        extracted_skills = set()
        
        # Extract from all skill categories
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill in text_lower:
                    extracted_skills.add(skill)
        
        # Extract programming languages
        prog_languages = ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala', 'php', 'ruby']
        for lang in prog_languages:
            if lang in text_lower:
                extracted_skills.add(lang)
        
        # Extract frameworks and tools
        frameworks = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'fastapi']
        for framework in frameworks:
            if framework in text_lower:
                extracted_skills.add(framework)
        
        return list(extracted_skills)
    
    def clean_resume_text(self, text: str) -> str:
        """Clean malformed resume text where words are separated by newlines"""
        # Replace multiple newlines with single spaces
        cleaned = re.sub(r'\n+', ' ', text)
        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Clean up common PDF extraction artifacts
        cleaned = cleaned.replace('|', ' ')
        return cleaned.strip()
    
    def extract_name_robust(self, text: str) -> str:
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
    
    def parse_resume_enhanced(self, resume_text: str) -> Dict:
        """Enhanced resume parser with better skill extraction and malformed text handling"""
        # Clean malformed PDF text first
        cleaned_text = self.clean_resume_text(resume_text)
        lines = cleaned_text.split('\n')
        
        # Extract name more robustly
        name = self.extract_name_robust(cleaned_text)
        
        # Extract skills from multiple sources
        skills = set()
        
        # Look for explicit skills section
        in_skills_section = False
        for line in lines:
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in ['SKILLS:', 'TECHNICAL SKILLS:', 'TECHNOLOGIES:']):
                in_skills_section = True
                # Extract skills from the same line
                if ':' in line:
                    skills_text = line.split(':', 1)[1]
                    skills.update([self.normalize_skill_name(s.strip()) for s in re.split('[,;]', skills_text) if s.strip()])
            elif in_skills_section and line.strip():
                if line.startswith(' ') or ',' in line or ';' in line:
                    # Continue skills section
                    skills.update([self.normalize_skill_name(s.strip()) for s in re.split('[,;]', line) if s.strip()])
                else:
                    # End of skills section
                    in_skills_section = False
        
        # Extract skills from entire resume text
        extracted_skills = self.extract_skills_from_text(resume_text)
        skills.update(extracted_skills)
        
        # Extract experience years using multiple patterns
        experience_years = 0
        
        # Pattern 1: (YYYY-YYYY) format
        date_pattern = r'\((\d{4})-(\d{4})\)'
        matches = re.findall(date_pattern, resume_text)
        for start, end in matches:
            years = int(end) - int(start)
            experience_years = max(experience_years, years)
        
        # Pattern 2: "X years" format
        years_pattern = r'(\d+)\s*years?\s*(of\s*)?(experience|exp)'
        matches = re.findall(years_pattern, resume_text.lower())
        for match in matches:
            years = int(match[0])
            experience_years = max(experience_years, years)
        
        # Pattern 3: Calculate from job durations
        job_durations = []
        for line in lines:
            if re.search(r'\d{4}.*\d{4}', line):
                years = re.findall(r'\d{4}', line)
                if len(years) >= 2:
                    try:
                        duration = int(years[-1]) - int(years[0])
                        if 0 < duration <= 20:  # Reasonable duration
                            job_durations.append(duration)
                    except:
                        pass
        
        if job_durations:
            experience_years = max(experience_years, sum(job_durations))
        
        return {
            "name": name,
            "skills": list(skills),
            "experience_years": experience_years,
            "resume_text": resume_text
        }
    
    def create_candidate_embedding(self, candidate_data: Dict) -> np.ndarray:
        """Create embedding for candidate with enhanced text processing"""
        # Create enhanced candidate text
        skills_text = ' '.join(candidate_data.get('skills', []))
        resume_text = candidate_data.get('resume_text', '')
        
        # Weight skills more heavily
        candidate_text = f"{skills_text} {skills_text} {resume_text}"
        
        embedding = self.model.encode([candidate_text], normalize_embeddings=True)
        return embedding[0]
    
    def calculate_skill_match_score(self, candidate_skills: List[str], job_requirements: List[str], job_nice_to_have: List[str] = None) -> float:
        """Calculate skill-based matching score"""
        if not job_requirements:
            return 0.0
        
        candidate_skills_norm = set([self.normalize_skill_name(skill) for skill in candidate_skills])
        job_req_norm = set([self.normalize_skill_name(skill) for skill in job_requirements])
        job_nice_norm = set([self.normalize_skill_name(skill) for skill in (job_nice_to_have or [])])
        
        # Direct skill matches
        required_matches = len(candidate_skills_norm.intersection(job_req_norm))
        nice_matches = len(candidate_skills_norm.intersection(job_nice_norm))
        
        # Category-based matches (partial credit for related skills)
        category_score = 0.0
        for category, category_skills in self.skill_categories.items():
            candidate_in_category = candidate_skills_norm.intersection(set(category_skills))
            job_in_category = job_req_norm.intersection(set(category_skills))
            
            if candidate_in_category and job_in_category:
                # Partial credit for having skills in the same category
                category_score += 0.3 * min(len(candidate_in_category), len(job_in_category)) / len(job_in_category)
        
        # Calculate final score
        required_score = required_matches / len(job_req_norm) if job_req_norm else 0
        nice_score = nice_matches / len(job_nice_norm) if job_nice_norm else 0
        
        # Weighted combination
        final_score = (required_score * 0.7) + (nice_score * 0.2) + (category_score * 0.1)
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def calculate_experience_match_score(self, candidate_years: int, job_experience_req: str) -> float:
        """Calculate experience matching score"""
        if not job_experience_req:
            return 0.8  # Default score if no requirement specified
        
        # Parse job experience requirement
        numbers = re.findall(r'\d+', job_experience_req)
        if not numbers:
            return 0.8
        
        if len(numbers) == 1:
            # Single number (e.g., "5+ years")
            required_years = int(numbers[0])
            if candidate_years >= required_years:
                return 1.0
            elif candidate_years >= required_years * 0.8:
                return 0.8
            else:
                return max(0.3, candidate_years / required_years)
        else:
            # Range (e.g., "3-5 years")
            min_years, max_years = int(numbers[0]), int(numbers[1])
            if min_years <= candidate_years <= max_years:
                return 1.0
            elif candidate_years >= min_years * 0.8:
                return 0.9
            elif candidate_years <= max_years * 1.2:
                return 0.8
            else:
                return max(0.3, min(candidate_years / min_years, max_years / candidate_years))
    
    def match_candidate_to_jobs(self, candidate_data: Dict, top_k: int = 5) -> List[Dict]:
        """Enhanced matching algorithm with multiple scoring methods"""
        try:
            if self.faiss_index is None or len(self.jobs_data) == 0:
                logger.error("FAISS index not initialized or no jobs data available")
                return []
            
            # Create candidate embedding for semantic similarity
            candidate_embedding = self.create_candidate_embedding(candidate_data)
            
            # Get semantic similarity scores
            k = min(top_k * 2, len(self.jobs_data))  # Get more candidates for reranking
            semantic_scores, indices = self.faiss_index.search(
                candidate_embedding.reshape(1, -1).astype('float32'), 
                k
            )
            
            # Create candidate TF-IDF vector for skill matching
            candidate_skills_text = ' '.join(candidate_data.get('skills', [])).lower()
            candidate_tfidf = self.tfidf_vectorizer.transform([candidate_skills_text])
            
            # Calculate comprehensive scores for each job
            matches = []
            for i, (semantic_score, job_idx) in enumerate(zip(semantic_scores[0], indices[0])):
                job = self.jobs_data[job_idx]
                
                # Ensure semantic score is positive (cosine similarity should be 0-1)
                semantic_score = max(0.0, float(semantic_score))
                
                # Calculate skill-based score
                skill_score = self.calculate_skill_match_score(
                    candidate_data.get('skills', []),
                    job.get('requirements', []),
                    job.get('nice_to_have', [])
                )
                
                # Calculate experience score
                experience_score = self.calculate_experience_match_score(
                    candidate_data.get('experience_years', 0),
                    job.get('experience_years', '')
                )
                
                # Calculate TF-IDF similarity for skills
                job_tfidf = self.job_tfidf_vectors[job_idx]
                tfidf_score = cosine_similarity(candidate_tfidf, job_tfidf)[0][0]
                tfidf_score = max(0.0, tfidf_score)  # Ensure positive
                
                # Combine scores with weights
                final_score = (
                    semantic_score * 0.3 +      # Semantic similarity
                    skill_score * 0.4 +         # Skill matching (most important)
                    experience_score * 0.2 +    # Experience matching
                    tfidf_score * 0.1           # TF-IDF skill similarity
                )
                
                # Ensure final score is between 0 and 1
                final_score = max(0.0, min(1.0, final_score))
                
                # Convert to percentage (0-100)
                similarity_percentage = final_score * 100
                
                # Determine confidence band based on final score
                confidence_band = self.get_confidence_band(final_score)
                
                # Generate explanation
                explanation = self.generate_enhanced_explanation(
                    candidate_data, job, final_score, skill_score, experience_score
                )
                
                match = {
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "department": job["department"],
                    "similarity_score": similarity_percentage,  # Now always 0-100
                    "confidence_band": confidence_band,
                    "explanation": explanation,
                    "job_details": job,
                    "score_breakdown": {
                        "semantic_score": semantic_score,
                        "skill_score": skill_score,
                        "experience_score": experience_score,
                        "tfidf_score": tfidf_score,
                        "final_score": final_score
                    }
                }
                matches.append(match)
            
            # Sort by final score and return top_k
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            return matches[:top_k]
            
        except Exception as e:
            logger.error(f"Error matching candidate: {e}")
            return []
    
    def get_confidence_band(self, score: float) -> str:
        """Determine confidence band based on similarity score"""
        if score >= 0.80:
            return "AUTO"
        elif score >= 0.60:
            return "REVIEW"
        else:
            return "HUMAN"
    
    def generate_enhanced_explanation(self, candidate_data: Dict, job: Dict, final_score: float, skill_score: float, experience_score: float) -> str:
        """Generate enhanced explanation for the match"""
        candidate_skills = set([self.normalize_skill_name(skill) for skill in candidate_data.get('skills', [])])
        job_requirements = set([self.normalize_skill_name(skill) for skill in job.get('requirements', [])])
        job_nice_to_have = set([self.normalize_skill_name(skill) for skill in job.get('nice_to_have', [])])
        
        # Find matching and missing skills
        matching_required = candidate_skills.intersection(job_requirements)
        matching_nice = candidate_skills.intersection(job_nice_to_have)
        missing_required = job_requirements - candidate_skills
        
        explanation_parts = []
        
        # Skill match summary
        if matching_required:
            explanation_parts.append(f"✓ Key skills: {', '.join(list(matching_required)[:3])}")
        
        if matching_nice:
            explanation_parts.append(f"✓ Bonus skills: {', '.join(list(matching_nice)[:2])}")
        
        # Experience assessment
        candidate_years = candidate_data.get('experience_years', 0)
        job_exp_req = job.get('experience_years', '')
        if candidate_years > 0:
            if experience_score >= 0.9:
                explanation_parts.append(f"✓ Experience: {candidate_years} years (excellent fit)")
            elif experience_score >= 0.7:
                explanation_parts.append(f"✓ Experience: {candidate_years} years (good fit)")
            else:
                explanation_parts.append(f"⚠ Experience: {candidate_years} years (needs review)")
        
        # Skill gaps
        if missing_required:
            explanation_parts.append(f"⚠ Missing: {', '.join(list(missing_required)[:2])}")
        
        # Overall assessment
        if final_score >= 0.8:
            explanation_parts.append("🎯 Strong match")
        elif final_score >= 0.6:
            explanation_parts.append("👍 Good potential")
        else:
            explanation_parts.append("🤔 Requires review")
        
        return " | ".join(explanation_parts)
    
    def analyze_skill_gaps(self, candidate_data: Dict, job: Dict) -> Dict:
        """Analyze skill gaps between candidate and job requirements"""
        candidate_skills = set([self.normalize_skill_name(skill) for skill in candidate_data.get('skills', [])])
        job_requirements = set([self.normalize_skill_name(skill) for skill in job.get('requirements', [])])
        job_nice_to_have = set([self.normalize_skill_name(skill) for skill in job.get('nice_to_have', [])])
        
        missing_required = job_requirements - candidate_skills
        missing_nice_to_have = job_nice_to_have - candidate_skills
        matching_skills = candidate_skills.intersection(job_requirements)
        
        # Enhanced training recommendations
        training_recommendations = []
        for skill in list(missing_required)[:3]:
            priority = "High" if skill in job_requirements else "Medium"
            
            # Skill-specific recommendations
            resources = []
            if skill in ['python', 'java', 'javascript']:
                resources = [
                    f"Codecademy {skill.title()} Course",
                    f"LeetCode {skill.title()} Practice",
                    f"{skill.title()} Official Documentation"
                ]
            elif skill in ['aws', 'gcp', 'azure']:
                resources = [
                    f"{skill.upper()} Cloud Practitioner Certification",
                    f"{skill.upper()} Free Tier Hands-on Practice",
                    f"A Cloud Guru {skill.upper()} Course"
                ]
            elif skill in ['docker', 'kubernetes']:
                resources = [
                    f"Docker/Kubernetes Official Tutorial",
                    f"Hands-on {skill.title()} Labs",
                    f"CNCF {skill.title()} Certification"
                ]
            else:
                resources = [
                    f"Online course: {skill.title()} Fundamentals",
                    f"Certification: Professional {skill.title()}",
                    f"Hands-on projects with {skill.title()}"
                ]
            
            training_recommendations.append({
                "skill": skill.title(),
                "priority": priority,
                "suggested_resources": resources,
                "estimated_time": "2-3 months" if priority == "High" else "1-2 months"
            })
        
        # Calculate readiness score
        readiness_score = len(matching_skills) / len(job_requirements) if job_requirements else 0
        
        return {
            "missing_required_skills": list(missing_required),
            "missing_nice_to_have": list(missing_nice_to_have),
            "matching_skills": list(matching_skills),
            "training_recommendations": training_recommendations,
            "readiness_score": readiness_score,
            "skill_match_percentage": readiness_score * 100
        }

# Global instance
improved_talent_matcher = ImprovedTalentMatcher()
