import json
import openai
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
import re
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    GREETING = "greeting"
    BASIC_INFO = "basic_info"
    EXPERIENCE_REVIEW = "experience_review"
    TECHNICAL_SCREENING = "technical_screening"
    AVAILABILITY = "availability"
    SALARY_EXPECTATIONS = "salary_expectations"
    QUESTIONS_FROM_CANDIDATE = "questions_from_candidate"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"

@dataclass
class ConversationContext:
    candidate_id: str
    job_id: str
    stage: ConversationStage
    collected_info: Dict
    conversation_history: List[Dict]
    screening_score: float
    red_flags: List[str]
    positive_indicators: List[str]
    next_questions: List[str]

class ConversationalAIRecruiter:
    def __init__(self):
        """Initialize the Conversational AI Recruiter"""
        self.init_conversation_db()
        
        # Question templates for different job categories
        self.question_templates = {
            "software_engineer": {
                "technical": [
                    "Can you walk me through your experience with {primary_language}?",
                    "Tell me about a challenging technical problem you solved recently.",
                    "How do you approach debugging complex issues?",
                    "What's your experience with {framework} framework?",
                    "How do you ensure code quality in your projects?"
                ],
                "experience": [
                    "What type of projects have you worked on in your current role?",
                    "How do you handle working in a team environment?",
                    "Tell me about a time you had to learn a new technology quickly.",
                    "What's your experience with agile development methodologies?"
                ],
                "problem_solving": [
                    "How would you design a system to handle 1 million users?",
                    "What would you do if a production system went down?",
                    "How do you prioritize features when you have limited time?"
                ]
            },
            "data_scientist": {
                "technical": [
                    "What's your experience with machine learning algorithms?",
                    "How do you approach data cleaning and preprocessing?",
                    "Tell me about a data science project you're proud of.",
                    "What tools do you use for data visualization?",
                    "How do you validate your machine learning models?"
                ],
                "experience": [
                    "How do you communicate technical findings to non-technical stakeholders?",
                    "What's your experience with big data technologies?",
                    "How do you handle missing or incomplete data?"
                ]
            },
            "product_manager": {
                "strategic": [
                    "How do you prioritize product features?",
                    "Tell me about a product you helped launch.",
                    "How do you gather and analyze user feedback?",
                    "What's your approach to competitive analysis?"
                ],
                "leadership": [
                    "How do you work with engineering teams?",
                    "Tell me about a time you had to make a difficult product decision.",
                    "How do you handle conflicting stakeholder requirements?"
                ]
            }
        }
        
        # Scoring criteria
        self.scoring_criteria = {
            "technical_competency": 0.3,
            "communication_skills": 0.25,
            "problem_solving": 0.2,
            "cultural_fit": 0.15,
            "enthusiasm": 0.1
        }
        
        # Red flag indicators
        self.red_flag_patterns = [
            r"i don't know",
            r"never worked with",
            r"not interested in",
            r"just for money",
            r"hate my current job",
            r"can't work with",
            r"impossible to",
            r"always late",
            r"don't like"
        ]
        
        # Positive indicators
        self.positive_patterns = [
            r"passionate about",
            r"love working with",
            r"excited to learn",
            r"challenging project",
            r"team collaboration",
            r"continuous learning",
            r"problem solving",
            r"innovative solution",
            r"user experience"
        ]
    
    def init_conversation_db(self):
        """Initialize database for conversation tracking"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            # Create conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    conversation_id TEXT PRIMARY KEY,
                    candidate_id TEXT,
                    job_id TEXT,
                    stage TEXT,
                    collected_info TEXT,
                    conversation_history TEXT,
                    screening_score REAL,
                    red_flags TEXT,
                    positive_indicators TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (candidate_id) REFERENCES candidates (candidate_id)
                )
            ''')
            
            # Create conversation messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    sender TEXT,
                    message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_type TEXT DEFAULT 'text',
                    metadata TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES ai_conversations (conversation_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Conversation database initialized")
            
        except Exception as e:
            logger.error(f"Error initializing conversation database: {e}")
    
    def start_conversation(self, candidate_id: str, job_id: str, candidate_info: Dict) -> str:
        """Start a new AI conversation with a candidate"""
        try:
            logger.info(f"ConversationalAIRecruiter.start_conversation called with candidate_id={candidate_id}, job_id={job_id}")
            logger.info(f"Candidate info: {candidate_info}")
            
            conversation_id = str(uuid.uuid4())
            logger.info(f"Generated conversation_id: {conversation_id}")
            
            # Get job details
            logger.info("Getting job details...")
            job_details = self.get_job_details(job_id)
            logger.info(f"Job details: {job_details}")
            
            # Initialize conversation context
            logger.info("Initializing conversation context...")
            context = ConversationContext(
                candidate_id=candidate_id,
                job_id=job_id,
                stage=ConversationStage.GREETING,
                collected_info={
                    "name": candidate_info.get("name", ""),
                    "email": candidate_info.get("email", ""),
                    "applied_for": candidate_info.get("applied_for", "")
                },
                conversation_history=[],
                screening_score=0.0,
                red_flags=[],
                positive_indicators=[],
                next_questions=[]
            )
            logger.info("Context initialized successfully")
            
            # Generate opening message
            logger.info("Generating opening message...")
            opening_message = self.generate_opening_message(candidate_info, job_details)
            logger.info(f"Opening message: {opening_message}")
            
            # Store conversation in database
            logger.info("Saving conversation to database...")
            self.save_conversation(conversation_id, context)
            logger.info("Conversation saved successfully")
            
            # Add opening message
            logger.info("Adding opening message...")
            self.add_message(conversation_id, "ai", opening_message, "greeting")
            logger.info("Opening message added successfully")
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def generate_opening_message(self, candidate_info: Dict, job_details: Dict) -> str:
        """Generate personalized opening message"""
        name = candidate_info.get("name", "there")
        job_title = job_details.get("title", "position")
        company = "Telus"
        
        opening_message = f"""Hi {name}! 👋

Thank you for your interest in the {job_title} position at {company}. I'm Alex, your AI recruiting assistant, and I'm here to help you through the initial screening process.

This conversation will take about 10-15 minutes, and I'll be asking you some questions about your experience, technical background, and interest in the role. Feel free to ask me any questions about the position or company as well!

To get started, could you briefly tell me what excites you most about this {job_title} opportunity?"""

        return opening_message
    
    def process_candidate_response(self, conversation_id: str, candidate_message: str) -> str:
        """Process candidate response and generate AI reply"""
        try:
            # Load conversation context
            context = self.load_conversation(conversation_id)
            
            # Add candidate message to history
            self.add_message(conversation_id, "candidate", candidate_message, "response")
            context.conversation_history.append({
                "sender": "candidate",
                "message": candidate_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Analyze candidate response
            analysis = self.analyze_response(candidate_message, context)
            
            # Update context with analysis
            context.screening_score = analysis["updated_score"]
            context.red_flags.extend(analysis["red_flags"])
            context.positive_indicators.extend(analysis["positive_indicators"])
            
            # Generate next question/response
            ai_response = self.generate_ai_response(context, analysis)
            
            # Update conversation stage if needed
            context.stage = self.determine_next_stage(context)
            
            # Save updated context
            self.save_conversation(conversation_id, context)
            
            # Add AI response to history
            self.add_message(conversation_id, "ai", ai_response, context.stage.value)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error processing candidate response: {e}")
            return "I apologize, but I'm experiencing some technical difficulties. Let me connect you with a human recruiter who can assist you further."
    
    def analyze_response(self, message: str, context: ConversationContext) -> Dict:
        """Analyze candidate response for scoring and insights"""
        message_lower = message.lower()
        
        # Check for red flags
        red_flags = []
        for pattern in self.red_flag_patterns:
            if re.search(pattern, message_lower):
                red_flags.append(f"Potential concern: {pattern}")
        
        # Check for positive indicators
        positive_indicators = []
        for pattern in self.positive_patterns:
            if re.search(pattern, message_lower):
                positive_indicators.append(f"Positive signal: {pattern}")
        
        # Score different aspects
        scores = {
            "technical_competency": self.score_technical_competency(message, context),
            "communication_skills": self.score_communication_skills(message),
            "problem_solving": self.score_problem_solving(message, context),
            "cultural_fit": self.score_cultural_fit(message),
            "enthusiasm": self.score_enthusiasm(message)
        }
        
        # Calculate weighted score
        weighted_score = sum(
            scores[criterion] * weight 
            for criterion, weight in self.scoring_criteria.items()
        )
        
        # Update overall score (running average)
        current_score = context.screening_score
        response_count = len(context.conversation_history) // 2  # Approximate number of responses
        updated_score = (current_score * response_count + weighted_score) / (response_count + 1)
        
        return {
            "scores": scores,
            "weighted_score": weighted_score,
            "updated_score": updated_score,
            "red_flags": red_flags,
            "positive_indicators": positive_indicators,
            "message_length": len(message),
            "response_quality": self.assess_response_quality(message)
        }
    
    def score_technical_competency(self, message: str, context: ConversationContext) -> float:
        """Score technical competency based on response"""
        if context.stage not in [ConversationStage.TECHNICAL_SCREENING, ConversationStage.EXPERIENCE_REVIEW]:
            return 0.5  # Neutral score for non-technical questions
        
        technical_keywords = [
            "algorithm", "database", "api", "framework", "architecture",
            "scalability", "performance", "testing", "deployment", "security",
            "optimization", "debugging", "version control", "agile", "ci/cd"
        ]
        
        message_lower = message.lower()
        keyword_count = sum(1 for keyword in technical_keywords if keyword in message_lower)
        
        # Score based on technical depth and keyword usage
        if keyword_count >= 3 and len(message) > 100:
            return 0.9
        elif keyword_count >= 2 and len(message) > 50:
            return 0.7
        elif keyword_count >= 1:
            return 0.6
        else:
            return 0.3
    
    def score_communication_skills(self, message: str) -> float:
        """Score communication skills based on response quality"""
        # Check for clear structure, proper grammar, and completeness
        sentences = message.split('.')
        
        factors = {
            "length": min(len(message) / 200, 1.0),  # Optimal length around 200 chars
            "structure": min(len(sentences) / 3, 1.0),  # Multiple sentences show structure
            "clarity": 1.0 if not re.search(r'um|uh|like|you know', message.lower()) else 0.7,
            "completeness": 1.0 if len(message) > 30 else 0.5
        }
        
        return sum(factors.values()) / len(factors)
    
    def score_problem_solving(self, message: str, context: ConversationContext) -> float:
        """Score problem-solving approach"""
        problem_solving_indicators = [
            "approach", "solution", "analyze", "break down", "step by step",
            "consider", "evaluate", "alternative", "pros and cons", "trade-off"
        ]
        
        message_lower = message.lower()
        indicator_count = sum(1 for indicator in problem_solving_indicators if indicator in message_lower)
        
        return min(indicator_count / 3, 1.0)
    
    def score_cultural_fit(self, message: str) -> float:
        """Score cultural fit based on values and attitude"""
        positive_culture_indicators = [
            "team", "collaborate", "learn", "grow", "challenge", "innovation",
            "customer", "quality", "improvement", "feedback", "mentor", "help"
        ]
        
        negative_culture_indicators = [
            "alone", "individual", "don't like", "hate", "boring", "easy money"
        ]
        
        message_lower = message.lower()
        positive_count = sum(1 for indicator in positive_culture_indicators if indicator in message_lower)
        negative_count = sum(1 for indicator in negative_culture_indicators if indicator in message_lower)
        
        base_score = min(positive_count / 3, 1.0)
        penalty = negative_count * 0.2
        
        return max(0.0, base_score - penalty)
    
    def score_enthusiasm(self, message: str) -> float:
        """Score enthusiasm and motivation"""
        enthusiasm_indicators = [
            "excited", "passionate", "love", "enjoy", "interested", "motivated",
            "eager", "looking forward", "can't wait", "amazing", "awesome"
        ]
        
        message_lower = message.lower()
        enthusiasm_count = sum(1 for indicator in enthusiasm_indicators if indicator in message_lower)
        
        # Also consider exclamation marks and positive tone
        exclamation_bonus = min(message.count('!') * 0.1, 0.3)
        
        return min((enthusiasm_count / 2) + exclamation_bonus, 1.0)
    
    def assess_response_quality(self, message: str) -> str:
        """Assess overall response quality"""
        length = len(message)
        
        if length < 20:
            return "too_short"
        elif length > 500:
            return "too_long"
        elif length > 100:
            return "detailed"
        else:
            return "adequate"
    
    def get_job_details(self, job_id: str) -> Dict:
        """Get job details from the database or jobs data"""
        try:
            # Import here to avoid circular imports
            from models.improved_ai_models import improved_talent_matcher
            
            # Check if jobs_data is available and not None
            if hasattr(improved_talent_matcher, 'jobs_data') and improved_talent_matcher.jobs_data:
                job_details = next((job for job in improved_talent_matcher.jobs_data if job['job_id'] == job_id), None)
                if job_details:
                    return job_details
            
            # Fallback to default job details
            return {
                "job_id": job_id,
                "title": "Software Engineer",
                "department": "Engineering",
                "requirements": ["Python", "JavaScript", "SQL"],
                "nice_to_have": ["React", "AWS"],
                "summary": "Join our engineering team to build innovative solutions."
            }
        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            return {
                "job_id": job_id, 
                "title": "Position", 
                "department": "Technology",
                "requirements": ["Programming"],
                "nice_to_have": [],
                "summary": "Join our team to work on exciting projects."
            }
    
    def save_conversation(self, conversation_id: str, context: ConversationContext):
        """Save conversation context to database"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO ai_conversations 
                (conversation_id, candidate_id, job_id, stage, collected_info, 
                 conversation_history, screening_score, red_flags, positive_indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                conversation_id,
                context.candidate_id,
                context.job_id,
                context.stage.value,
                json.dumps(context.collected_info),
                json.dumps(context.conversation_history),
                context.screening_score,
                json.dumps(context.red_flags),
                json.dumps(context.positive_indicators)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
    
    def load_conversation(self, conversation_id: str) -> ConversationContext:
        """Load conversation context from database"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM ai_conversations WHERE conversation_id = ?', (conversation_id,))
            row = cursor.fetchone()
            
            if not row:
                raise ValueError("Conversation not found")
            
            context = ConversationContext(
                candidate_id=row[1],
                job_id=row[2],
                stage=ConversationStage(row[3]),
                collected_info=json.loads(row[4]) if row[4] else {},
                conversation_history=json.loads(row[5]) if row[5] else [],
                screening_score=row[6] or 0.0,
                red_flags=json.loads(row[7]) if row[7] else [],
                positive_indicators=json.loads(row[8]) if row[8] else [],
                next_questions=[]
            )
            
            conn.close()
            return context
            
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
            raise
    
    def add_message(self, conversation_id: str, sender: str, message: str, message_type: str = "text"):
        """Add a message to the conversation"""
        try:
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            message_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO conversation_messages 
                (message_id, conversation_id, sender, message, message_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (message_id, conversation_id, sender, message, message_type))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
    
    def generate_ai_response(self, context: ConversationContext, analysis: Dict) -> str:
        """Generate AI response based on context and analysis"""
        try:
            # Get job details for context
            job_details = self.get_job_details(context.job_id)
            
            # Determine response based on current stage
            if context.stage == ConversationStage.GREETING:
                return self.generate_experience_question(context, job_details)
            elif context.stage == ConversationStage.EXPERIENCE_REVIEW:
                return self.generate_technical_question(context, job_details)
            elif context.stage == ConversationStage.TECHNICAL_SCREENING:
                return self.generate_availability_question(context)
            elif context.stage == ConversationStage.AVAILABILITY:
                return self.generate_salary_question(context)
            elif context.stage == ConversationStage.SALARY_EXPECTATIONS:
                return self.generate_candidate_questions_prompt(context)
            elif context.stage == ConversationStage.QUESTIONS_FROM_CANDIDATE:
                return self.generate_wrap_up(context)
            else:
                return self.generate_completion_message(context)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Thank you for your response. Let me connect you with a human recruiter to continue the process."
    
    def generate_experience_question(self, context: ConversationContext, job_details: Dict) -> str:
        """Generate experience-related question"""
        job_title = job_details.get("title", "position")
        
        questions = [
            f"Great! Now, could you tell me about your most relevant experience for this {job_title} role?",
            f"I'd love to hear about a project you've worked on that you think demonstrates your fit for this {job_title} position.",
            f"What experience do you have that makes you excited about this {job_title} opportunity?"
        ]
        
        return questions[len(context.conversation_history) % len(questions)]
    
    def generate_technical_question(self, context: ConversationContext, job_details: Dict) -> str:
        """Generate technical screening question"""
        requirements = job_details.get("requirements", [])
        
        if requirements:
            primary_skill = requirements[0]
            return f"That sounds great! I'd like to dive a bit deeper into your technical background. Can you tell me about your experience with {primary_skill} and how you've used it in your projects?"
        else:
            return "Excellent! Now I'd like to ask about your technical approach. Can you walk me through how you typically approach solving complex technical problems?"
    
    def generate_availability_question(self, context: ConversationContext) -> str:
        """Generate availability question"""
        return """Perfect! I'm getting a good sense of your technical background. 

Now, let's talk about logistics. What's your current availability? Are you actively looking to make a move, or are you exploring opportunities?"""
    
    def generate_salary_question(self, context: ConversationContext) -> str:
        """Generate salary expectations question"""
        return """Thanks for that information! 

To make sure we're aligned, could you share your salary expectations for this role? This helps us ensure we can make a competitive offer if we move forward."""
    
    def generate_candidate_questions_prompt(self, context: ConversationContext) -> str:
        """Prompt candidate to ask questions"""
        return """Great! I think I have a good understanding of your background and interests.

Now it's your turn - do you have any questions about the role, the team, the company culture, or anything else about Telus? I'm here to help!"""
    
    def generate_wrap_up(self, context: ConversationContext) -> str:
        """Generate conversation wrap-up"""
        score = context.screening_score
        
        if score >= 0.7:
            next_steps = "I'll be recommending you for the next round of interviews with our hiring manager."
        elif score >= 0.5:
            next_steps = "I'll be sharing your profile with our hiring team for review."
        else:
            next_steps = "I'll be sharing your information with our team, and we'll be in touch about next steps."
        
        return f"""Thank you so much for taking the time to chat with me today! I really enjoyed learning about your background and experience.

{next_steps} You can expect to hear back from us within 2-3 business days.

Is there anything else you'd like to add before we wrap up?"""
    
    def generate_completion_message(self, context: ConversationContext) -> str:
        """Generate final completion message"""
        return """Perfect! Thank you again for your time and interest in Telus. 

We'll be in touch soon with next steps. Have a great day! 🚀"""
    
    def determine_next_stage(self, context: ConversationContext) -> ConversationStage:
        """Determine the next conversation stage"""
        current_stage = context.stage
        response_count = len(context.conversation_history)
        
        # Simple stage progression logic
        stage_progression = [
            ConversationStage.GREETING,
            ConversationStage.EXPERIENCE_REVIEW,
            ConversationStage.TECHNICAL_SCREENING,
            ConversationStage.AVAILABILITY,
            ConversationStage.SALARY_EXPECTATIONS,
            ConversationStage.QUESTIONS_FROM_CANDIDATE,
            ConversationStage.WRAP_UP,
            ConversationStage.COMPLETED
        ]
        
        try:
            current_index = stage_progression.index(current_stage)
            if current_index < len(stage_progression) - 1:
                return stage_progression[current_index + 1]
            else:
                return ConversationStage.COMPLETED
        except ValueError:
            return ConversationStage.COMPLETED
    
    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of the conversation for recruiters"""
        try:
            context = self.load_conversation(conversation_id)
            
            # Get all messages
            conn = sqlite3.connect('talent_platform.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT sender, message, timestamp 
                FROM conversation_messages 
                WHERE conversation_id = ? 
                ORDER BY timestamp
            ''', (conversation_id,))
            
            messages = cursor.fetchall()
            conn.close()
            
            # Generate summary
            summary = {
                "conversation_id": conversation_id,
                "candidate_id": context.candidate_id,
                "job_id": context.job_id,
                "final_score": context.screening_score,
                "stage_reached": context.stage.value,
                "red_flags": context.red_flags,
                "positive_indicators": context.positive_indicators,
                "collected_info": context.collected_info,
                "message_count": len(messages),
                "recommendation": self.generate_recommendation(context),
                "key_insights": self.extract_key_insights(context, messages)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}")
            return {}
    
    def generate_recommendation(self, context: ConversationContext) -> str:
        """Generate hiring recommendation based on conversation"""
        score = context.screening_score
        
        if score >= 0.8:
            return "STRONG_RECOMMEND"
        elif score >= 0.6:
            return "RECOMMEND"
        elif score >= 0.4:
            return "CONSIDER"
        else:
            return "NOT_RECOMMEND"
    
    def extract_key_insights(self, context: ConversationContext, messages: List) -> List[str]:
        """Extract key insights from the conversation"""
        insights = []
        
        # Add insights based on scoring
        if context.screening_score >= 0.7:
            insights.append("Strong technical background demonstrated")
        
        if len(context.positive_indicators) > 3:
            insights.append("High enthusiasm and cultural fit")
        
        if len(context.red_flags) > 0:
            insights.append(f"Some concerns noted: {', '.join(context.red_flags[:2])}")
        
        # Add insights based on conversation length
        candidate_messages = [msg for msg in messages if msg[0] == "candidate"]
        avg_response_length = sum(len(msg[1]) for msg in candidate_messages) / len(candidate_messages) if candidate_messages else 0
        
        if avg_response_length > 150:
            insights.append("Detailed and thoughtful responses")
        elif avg_response_length < 50:
            insights.append("Brief responses - may need follow-up")
        
        return insights

# Global instance
conversational_ai_recruiter = ConversationalAIRecruiter()
