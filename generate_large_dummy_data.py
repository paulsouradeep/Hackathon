#!/usr/bin/env python3
"""
Large Dummy Data Generator for Telus Talent Intelligence Platform
Generates extensive dummy data including candidates, jobs, and assessments for testing
"""

import json
import sqlite3
import uuid
import random
from datetime import datetime, timedelta
from models.improved_ai_models import improved_talent_matcher as talent_matcher

# Expanded job data with more diverse roles
ADDITIONAL_JOBS = [
    {
        "job_id": "job_007",
        "title": "Full Stack Developer",
        "department": "Product Engineering",
        "location": "Toronto",
        "requirements": ["JavaScript", "React", "Node.js", "MongoDB", "Express"],
        "nice_to_have": ["TypeScript", "GraphQL", "AWS", "Docker", "Testing"],
        "summary": "Join our product engineering team as a Full Stack Developer. Build end-to-end web applications using modern JavaScript technologies. Work with React frontend, Node.js backend, and MongoDB database.",
        "experience_years": "3-6",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_008",
        "title": "Data Scientist",
        "department": "Analytics",
        "location": "Vancouver",
        "requirements": ["Python", "R", "Statistics", "Machine Learning", "SQL"],
        "nice_to_have": ["TensorFlow", "PyTorch", "Tableau", "AWS", "Spark"],
        "summary": "Drive data-driven insights as a Data Scientist. Analyze large datasets, build predictive models, and communicate findings to stakeholders. Strong statistical background required.",
        "experience_years": "2-5",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_009",
        "title": "Security Engineer",
        "department": "Cybersecurity",
        "location": "Montreal",
        "requirements": ["Security", "Penetration Testing", "CISSP", "Network Security", "Incident Response"],
        "nice_to_have": ["Python", "AWS Security", "SIEM", "Compliance", "Risk Assessment"],
        "summary": "Protect our infrastructure as a Security Engineer. Conduct security assessments, implement security controls, and respond to incidents. Security certifications preferred.",
        "experience_years": "4-8",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_010",
        "title": "Mobile Developer",
        "department": "Mobile Engineering",
        "location": "Calgary",
        "requirements": ["React Native", "iOS", "Android", "JavaScript", "Mobile UI/UX"],
        "nice_to_have": ["Swift", "Kotlin", "Flutter", "Firebase", "App Store"],
        "summary": "Build mobile applications for iOS and Android platforms. Work with React Native and native technologies to create engaging mobile experiences.",
        "experience_years": "2-6",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_011",
        "title": "QA Engineer",
        "department": "Quality Assurance",
        "location": "Ottawa",
        "requirements": ["Test Automation", "Selenium", "API Testing", "Quality Assurance", "Bug Tracking"],
        "nice_to_have": ["Python", "Java", "CI/CD", "Performance Testing", "Security Testing"],
        "summary": "Ensure product quality as a QA Engineer. Design and execute test plans, automate testing processes, and work closely with development teams.",
        "experience_years": "2-5",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_012",
        "title": "UX Designer",
        "department": "Design",
        "location": "Toronto",
        "requirements": ["UX Design", "User Research", "Prototyping", "Figma", "Design Thinking"],
        "nice_to_have": ["UI Design", "Usability Testing", "Analytics", "Frontend Knowledge", "Accessibility"],
        "summary": "Create exceptional user experiences as a UX Designer. Conduct user research, design wireframes and prototypes, and collaborate with product teams.",
        "experience_years": "3-7",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_013",
        "title": "Backend Developer",
        "department": "Platform Engineering",
        "location": "Bengaluru",
        "requirements": ["Java", "Spring Boot", "Microservices", "PostgreSQL", "REST APIs"],
        "nice_to_have": ["Kafka", "Redis", "Docker", "Kubernetes", "AWS"],
        "summary": "Build robust backend systems as a Backend Developer. Design APIs, implement business logic, and ensure system scalability and performance.",
        "experience_years": "3-7",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_014",
        "title": "Site Reliability Engineer",
        "department": "Infrastructure",
        "location": "Vancouver",
        "requirements": ["SRE", "Monitoring", "Incident Management", "Automation", "Linux"],
        "nice_to_have": ["Python", "Go", "Kubernetes", "Prometheus", "Grafana"],
        "summary": "Ensure system reliability as an SRE. Monitor production systems, automate operations, and improve system performance and availability.",
        "experience_years": "4-8",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_015",
        "title": "Business Analyst",
        "department": "Business Operations",
        "location": "Toronto",
        "requirements": ["Business Analysis", "Requirements Gathering", "Process Improvement", "Stakeholder Management", "Documentation"],
        "nice_to_have": ["SQL", "Analytics", "Project Management", "Agile", "Domain Knowledge"],
        "summary": "Drive business improvements as a Business Analyst. Gather requirements, analyze processes, and work with stakeholders to implement solutions.",
        "experience_years": "2-6",
        "employment_type": "Full-time"
    },
    {
        "job_id": "job_016",
        "title": "Technical Writer",
        "department": "Documentation",
        "location": "Remote",
        "requirements": ["Technical Writing", "Documentation", "API Documentation", "Content Strategy", "Communication"],
        "nice_to_have": ["Markdown", "Git", "Developer Tools", "UX Writing", "Video Creation"],
        "summary": "Create clear technical documentation as a Technical Writer. Document APIs, write user guides, and help developers and users understand our products.",
        "experience_years": "2-5",
        "employment_type": "Full-time"
    }
]

# Diverse candidate profiles with realistic data
CANDIDATE_TEMPLATES = [
    {
        "name_patterns": ["Nigga", "Priya", "Rahul", "Black", "Vikash", "Doggy", "Rohan", "Kavya", "Amit", "Divya"],
        "surnames": ["Sharma", "Patel", "Kumar", "Sigma", "Reddy", "Saur", "Agarwal", "Jain", "Shah", "Verma", "Yadav", "Mishra", "Tiwari", "Pandey", "Srivastava"],
        "domains": ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "company.com", "tech.com"]
    },
    {
        "name_patterns": ["John", "Gay", "Michael", "Emily", "David", "Jessica", "Robert", "Ashley", "James", "Amanda"],
        "surnames": ["Smith", "Johnson", "Cheeks", "Brown", "Jones", "G", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"],
        "domains": ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "company.com", "tech.com"]
    }
]

# Skill sets for different roles
SKILL_SETS = {
    "software_engineer": {
        "core": ["Python", "Java", "JavaScript", "Git", "SQL", "REST APIs"],
        "frameworks": ["React", "Spring Boot", "Django", "Flask", "Node.js", "Express"],
        "cloud": ["AWS", "GCP", "Azure", "Docker", "Kubernetes"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
        "tools": ["Jenkins", "GitLab", "JIRA", "Confluence"]
    },
    "data_engineer": {
        "core": ["Python", "SQL", "ETL", "Data Warehousing", "Big Data"],
        "frameworks": ["Apache Spark", "Kafka", "Airflow", "Pandas", "NumPy"],
        "cloud": ["AWS", "GCP", "Azure", "S3", "BigQuery", "Redshift"],
        "databases": ["PostgreSQL", "MySQL", "Cassandra", "Elasticsearch"],
        "tools": ["Tableau", "Power BI", "Jupyter", "Git"]
    },
    "devops_engineer": {
        "core": ["Linux", "CI/CD", "Infrastructure as Code", "Monitoring", "Automation"],
        "frameworks": ["Terraform", "Ansible", "Puppet", "Chef"],
        "cloud": ["AWS", "GCP", "Azure", "Docker", "Kubernetes"],
        "tools": ["Jenkins", "GitLab CI", "Prometheus", "Grafana", "ELK Stack"],
        "languages": ["Python", "Bash", "Go", "YAML"]
    },
    "ml_engineer": {
        "core": ["Python", "Machine Learning", "Statistics", "MLOps", "Data Science"],
        "frameworks": ["TensorFlow", "PyTorch", "scikit-learn", "Keras", "XGBoost"],
        "cloud": ["AWS", "GCP", "Azure", "SageMaker", "Vertex AI"],
        "tools": ["Jupyter", "MLflow", "Kubeflow", "Git", "Docker"],
        "specialties": ["NLP", "Computer Vision", "Deep Learning", "Time Series"]
    },
    "frontend_developer": {
        "core": ["JavaScript", "HTML", "CSS", "React", "TypeScript"],
        "frameworks": ["Vue.js", "Angular", "Next.js", "Svelte"],
        "tools": ["Webpack", "Vite", "Jest", "Cypress", "Figma"],
        "styling": ["Sass", "Tailwind CSS", "Bootstrap", "Material-UI"],
        "state": ["Redux", "MobX", "Context API", "Zustand"]
    },
    "backend_developer": {
        "core": ["Java", "Python", "Node.js", "REST APIs", "Microservices"],
        "frameworks": ["Spring Boot", "Django", "Flask", "Express", "FastAPI"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
        "cloud": ["AWS", "GCP", "Azure", "Docker", "Kubernetes"],
        "tools": ["Git", "Maven", "Gradle", "Postman"]
    },
    "mobile_developer": {
        "core": ["React Native", "JavaScript", "Mobile UI/UX", "iOS", "Android"],
        "frameworks": ["Flutter", "Xamarin", "Ionic"],
        "languages": ["Swift", "Kotlin", "Dart", "Objective-C"],
        "tools": ["Xcode", "Android Studio", "Firebase", "App Store Connect"],
        "testing": ["Detox", "Appium", "XCTest", "Espresso"]
    },
    "qa_engineer": {
        "core": ["Test Automation", "Quality Assurance", "Bug Tracking", "Test Planning"],
        "tools": ["Selenium", "Cypress", "Postman", "JIRA", "TestRail"],
        "languages": ["Python", "Java", "JavaScript"],
        "types": ["API Testing", "Performance Testing", "Security Testing", "Mobile Testing"],
        "frameworks": ["TestNG", "JUnit", "Pytest", "Mocha"]
    },
    "designer": {
        "core": ["UX Design", "UI Design", "User Research", "Prototyping", "Design Thinking"],
        "tools": ["Figma", "Sketch", "Adobe XD", "InVision", "Principle"],
        "skills": ["Wireframing", "User Testing", "Information Architecture", "Interaction Design"],
        "specialties": ["Accessibility", "Design Systems", "Visual Design", "Motion Design"]
    },
    "business_analyst": {
        "core": ["Business Analysis", "Requirements Gathering", "Process Improvement", "Stakeholder Management"],
        "tools": ["JIRA", "Confluence", "Visio", "Lucidchart", "Excel"],
        "methodologies": ["Agile", "Waterfall", "Lean", "Six Sigma"],
        "skills": ["Documentation", "Data Analysis", "Project Management", "Communication"]
    }
}

# Education institutions
EDUCATION_OPTIONS = [
    "B.Tech Computer Science, IIT Delhi",
    "B.Tech Information Technology, IIT Bombay", 
    "B.E. Computer Engineering, BITS Pilani",
    "B.Tech Computer Science, NIT Trichy",
    "B.Tech Information Technology, VIT Vellore",
    "M.Tech Computer Science, IISc Bangalore",
    "M.S. Computer Science, Stanford University",
    "M.S. Data Science, Carnegie Mellon University",
    "B.S. Computer Science, University of Toronto",
    "M.Eng Software Engineering, University of Waterloo",
    "B.Tech Electronics, IIT Kanpur",
    "M.Tech Data Science, IIIT Bangalore",
    "B.E. Software Engineering, PES University",
    "M.S. Machine Learning, Georgia Tech",
    "B.Tech Computer Science, Amrita University"
]

# Companies for work experience
COMPANIES = [
    "TechCorp", "DataTech Solutions", "CloudOps Ltd", "AI Innovations", "WebTech Solutions",
    "StartupHub", "Analytics Pro", "DevOps Masters", "ML Systems Inc", "Frontend Labs",
    "Backend Solutions", "Mobile First", "QA Excellence", "Design Studio", "Business Insights",
    "Infosys", "TCS", "Wipro", "Accenture", "Cognizant", "HCL", "Tech Mahindra",
    "Amazon", "Google", "Microsoft", "Meta", "Apple", "Netflix", "Uber", "Airbnb",
    "Flipkart", "Paytm", "Zomato", "Swiggy", "BYJU'S", "Ola", "PhonePe", "Razorpay"
]

def generate_phone_number():
    """Generate a realistic Indian phone number"""
    return f"+91-{random.randint(7000000000, 9999999999)}"

def generate_candidate_name():
    """Generate a realistic candidate name"""
    template = random.choice(CANDIDATE_TEMPLATES)
    first_name = random.choice(template["name_patterns"])
    last_name = random.choice(template["surnames"])
    return f"{first_name} {last_name}"

def generate_email(name):
    """Generate email from name"""
    template = random.choice(CANDIDATE_TEMPLATES)
    domain = random.choice(template["domains"])
    clean_name = name.lower().replace(" ", ".")
    return f"{clean_name}@{domain}"

def generate_skills_for_role(role_type, experience_years):
    """Generate realistic skills based on role and experience"""
    if role_type not in SKILL_SETS:
        role_type = "software_engineer"
    
    skill_set = SKILL_SETS[role_type]
    skills = []
    
    # Core skills (always include most of these)
    skills.extend(random.sample(skill_set["core"], min(len(skill_set["core"]), random.randint(4, 6))))
    
    # Add framework skills based on experience
    if experience_years >= 2:
        framework_count = min(len(skill_set.get("frameworks", [])), random.randint(2, 4))
        if framework_count > 0:
            skills.extend(random.sample(skill_set["frameworks"], framework_count))
    
    # Add cloud skills for senior developers
    if experience_years >= 3:
        cloud_count = min(len(skill_set.get("cloud", [])), random.randint(2, 3))
        if cloud_count > 0:
            skills.extend(random.sample(skill_set["cloud"], cloud_count))
    
    # Add additional skills based on role
    for category in ["databases", "tools", "languages", "specialties", "styling", "state", "testing", "types", "methodologies", "skills"]:
        if category in skill_set:
            additional_count = min(len(skill_set[category]), random.randint(1, 3))
            if additional_count > 0:
                skills.extend(random.sample(skill_set[category], additional_count))
    
    # Remove duplicates and return
    return list(set(skills))

def generate_work_experience(role_type, experience_years, name):
    """Generate realistic work experience"""
    experiences = []
    current_year = datetime.now().year
    years_covered = 0
    
    while years_covered < experience_years:
        # Generate job duration (1-4 years typically)
        job_duration = min(random.randint(1, 4), experience_years - years_covered)
        end_year = current_year - years_covered
        start_year = end_year - job_duration
        
        # Select company
        company = random.choice(COMPANIES)
        
        # Generate role title based on experience level
        if years_covered == 0:  # Current/most recent role
            if experience_years >= 7:
                title_prefix = "Senior"
            elif experience_years >= 4:
                title_prefix = "Mid-level"
            else:
                title_prefix = ""
        else:  # Previous roles
            if experience_years - years_covered >= 5:
                title_prefix = "Senior"
            elif experience_years - years_covered >= 2:
                title_prefix = "Mid-level"
            else:
                title_prefix = "Junior"
        
        # Map role types to job titles
        role_titles = {
            "software_engineer": "Software Engineer",
            "data_engineer": "Data Engineer", 
            "devops_engineer": "DevOps Engineer",
            "ml_engineer": "Machine Learning Engineer",
            "frontend_developer": "Frontend Developer",
            "backend_developer": "Backend Developer",
            "mobile_developer": "Mobile Developer",
            "qa_engineer": "QA Engineer",
            "designer": "UX Designer",
            "business_analyst": "Business Analyst"
        }
        
        base_title = role_titles.get(role_type, "Software Engineer")
        full_title = f"{title_prefix} {base_title}".strip()
        
        experience = {
            "company": company,
            "title": full_title,
            "duration": f"{start_year}-{end_year}",
            "years": job_duration
        }
        
        experiences.append(experience)
        years_covered += job_duration
    
    return experiences

def generate_resume_text(name, role_type, skills, experience_years, education, experiences):
    """Generate realistic resume text"""
    
    # Map role types to resume titles
    role_titles = {
        "software_engineer": "Software Engineer",
        "data_engineer": "Data Engineer",
        "devops_engineer": "DevOps Engineer", 
        "ml_engineer": "Machine Learning Engineer",
        "frontend_developer": "Frontend Developer",
        "backend_developer": "Backend Developer",
        "mobile_developer": "Mobile Developer",
        "qa_engineer": "QA Engineer",
        "designer": "UX Designer",
        "business_analyst": "Business Analyst"
    }
    
    resume_title = role_titles.get(role_type, "Software Engineer")
    
    resume_text = f"{name}\n{resume_title}\n\nEXPERIENCE:\n"
    
    # Add work experiences
    for exp in experiences:
        resume_text += f"{exp['title']} at {exp['company']} ({exp['duration']})\n"
        
        # Generate realistic job responsibilities based on role
        if role_type == "software_engineer":
            responsibilities = [
                "- Developed and maintained web applications using modern frameworks",
                "- Collaborated with cross-functional teams to deliver high-quality software",
                "- Implemented REST APIs and microservices architecture",
                "- Participated in code reviews and maintained coding standards",
                "- Worked with cloud platforms and containerization technologies"
            ]
        elif role_type == "data_engineer":
            responsibilities = [
                "- Built and maintained data pipelines for large-scale data processing",
                "- Designed ETL processes and data warehousing solutions",
                "- Worked with big data technologies and cloud platforms",
                "- Optimized database performance and data quality",
                "- Collaborated with data scientists and analysts"
            ]
        elif role_type == "devops_engineer":
            responsibilities = [
                "- Managed cloud infrastructure and deployment pipelines",
                "- Implemented CI/CD processes and automation tools",
                "- Monitored system performance and reliability",
                "- Worked with containerization and orchestration platforms",
                "- Ensured security and compliance standards"
            ]
        elif role_type == "ml_engineer":
            responsibilities = [
                "- Developed and deployed machine learning models",
                "- Built MLOps pipelines for model training and deployment",
                "- Worked with large datasets and feature engineering",
                "- Implemented A/B testing for model performance",
                "- Collaborated with data scientists and product teams"
            ]
        elif role_type == "frontend_developer":
            responsibilities = [
                "- Built responsive and interactive user interfaces",
                "- Worked with modern JavaScript frameworks and libraries",
                "- Collaborated with designers and backend developers",
                "- Implemented automated testing and code quality tools",
                "- Optimized application performance and accessibility"
            ]
        elif role_type == "backend_developer":
            responsibilities = [
                "- Designed and implemented backend services and APIs",
                "- Worked with databases and data modeling",
                "- Implemented security and authentication mechanisms",
                "- Optimized application performance and scalability",
                "- Collaborated with frontend and infrastructure teams"
            ]
        elif role_type == "mobile_developer":
            responsibilities = [
                "- Developed mobile applications for iOS and Android platforms",
                "- Worked with native and cross-platform technologies",
                "- Implemented mobile UI/UX best practices",
                "- Integrated with backend APIs and third-party services",
                "- Published apps to app stores and managed releases"
            ]
        elif role_type == "qa_engineer":
            responsibilities = [
                "- Designed and executed comprehensive test plans",
                "- Implemented automated testing frameworks and tools",
                "- Performed functional, performance, and security testing",
                "- Collaborated with development teams on quality processes",
                "- Managed bug tracking and test case management"
            ]
        elif role_type == "designer":
            responsibilities = [
                "- Conducted user research and usability testing",
                "- Created wireframes, prototypes, and design systems",
                "- Collaborated with product and engineering teams",
                "- Designed accessible and inclusive user experiences",
                "- Maintained design consistency across products"
            ]
        else:  # business_analyst
            responsibilities = [
                "- Gathered and analyzed business requirements",
                "- Facilitated stakeholder meetings and workshops",
                "- Created process documentation and workflows",
                "- Worked with technical teams on solution implementation",
                "- Performed data analysis and reporting"
            ]
        
        # Add 3-4 random responsibilities
        selected_responsibilities = random.sample(responsibilities, min(len(responsibilities), random.randint(3, 4)))
        for resp in selected_responsibilities:
            resume_text += f"{resp}\n"
        resume_text += "\n"
    
    # Add skills section
    resume_text += f"SKILLS:\n{', '.join(skills)}\n\n"
    
    # Add education
    resume_text += f"EDUCATION:\n{education}\n\n"
    
    # Add GitHub (sometimes)
    if random.random() < 0.7:  # 70% chance of having GitHub
        github_username = name.lower().replace(" ", "")
        resume_text += f"GITHUB: github.com/{github_username}\n"
    
    return resume_text

def generate_assessment_data(candidate_id, job_id, role_type):
    """Generate realistic assessment data"""
    assessments = []
    
    # Assessment types based on role
    assessment_types = {
        "software_engineer": ["Technical Skills Assessment", "Coding Challenge", "System Design"],
        "data_engineer": ["Data Engineering Assessment", "SQL Skills Test", "Big Data Technologies"],
        "devops_engineer": ["Infrastructure Assessment", "Cloud Platforms Test", "Automation Skills"],
        "ml_engineer": ["Machine Learning Fundamentals", "Statistics and Probability", "MLOps Assessment"],
        "frontend_developer": ["Frontend Development Test", "JavaScript Assessment", "UI/UX Principles"],
        "backend_developer": ["Backend Development Test", "Database Design", "API Development"],
        "mobile_developer": ["Mobile Development Assessment", "Platform-specific Skills", "Mobile UI/UX"],
        "qa_engineer": ["Quality Assurance Fundamentals", "Test Automation", "Testing Methodologies"],
        "designer": ["UX Design Principles", "Design Thinking", "User Research Methods"],
        "business_analyst": ["Business Analysis Fundamentals", "Requirements Gathering", "Process Improvement"]
    }
    
    available_assessments = assessment_types.get(role_type, ["Technical Skills Assessment"])
    
    # Generate 1-3 assessments per candidate
    num_assessments = random.randint(1, 3)
    
    for i in range(num_assessments):
        assessment_type = random.choice(available_assessments)
        
        # Generate realistic scores
        base_score = random.randint(60, 95)
        cutoff_score = random.randint(65, 80)
        max_score = 100
        
        # Generate assessment responses
        responses = []
        num_questions = random.randint(3, 6)
        
        for q in range(num_questions):
            if random.random() < 0.6:  # 60% text questions
                question_type = "text"
                questions = [
                    "Explain the concept of object-oriented programming",
                    "What is the difference between SQL and NoSQL databases?",
                    "Describe your experience with cloud platforms",
                    "How do you ensure code quality in your projects?",
                    "What is your approach to debugging complex issues?",
                    "Explain the importance of version control in software development"
                ]
                question = random.choice(questions)
                answer = "Detailed explanation provided by candidate demonstrating understanding of the concept."
                is_correct = random.random() < 0.8  # 80% correct answers
                
                responses.append({
                    "question": question,
                    "answer": answer,
                    "type": question_type,
                    "is_correct": is_correct
                })
            else:  # 40% multiple choice
                question_type = "multiple_choice"
                questions = [
                    "Which of the following is a NoSQL database?",
                    "What does API stand for?",
                    "Which cloud provider offers S3 storage?",
                    "What is the primary purpose of Docker?",
                    "Which programming language is known for data science?"
                ]
                question = random.choice(questions)
                options = ["Option A", "Option B", "Option C", "Option D"]
                selected_option = random.choice(options)
                is_correct = random.random() < 0.75  # 75% correct answers
                
                responses.append({
                    "question": question,
                    "selected_option": selected_option,
                    "type": question_type,
                    "is_correct": is_correct
                })
        
        assessment = {
            "assessment_id": f"assess_{str(uuid.uuid4())[:8]}",
            "candidate_id": candidate_id,
            "job_id": job_id,
            "assessment_type": assessment_type,
            "candidate_score": float(base_score),
            "cutoff_score": float(cutoff_score),
            "max_score": float(max_score),
            "status": "completed",
            "responses": json.dumps(responses),
            "duration_minutes": random.randint(30, 90)
        }
        
        assessments.append(assessment)
    
    return assessments

def generate_candidates(num_candidates=100):
    """Generate a large number of diverse candidates"""
    print(f"Generating {num_candidates} diverse candidates...")
    
    candidates = []
    role_types = list(SKILL_SETS.keys())
    
    for i in range(num_candidates):
        # Generate basic info
        name = generate_candidate_name()
        email = generate_email(name)
        phone = generate_phone_number()
        
        # Select role type and experience
        role_type = random.choice(role_types)
        experience_years = random.randint(1, 12)
        
        # Generate skills and experience
        skills = generate_skills_for_role(role_type, experience_years)
        education = random.choice(EDUCATION_OPTIONS)
        experiences = generate_work_experience(role_type, experience_years, name)
        
        # Generate resume text
        resume_text = generate_resume_text(name, role_type, skills, experience_years, education, experiences)
        
        # Select job to apply for (randomly from available jobs)
        all_jobs = talent_matcher.jobs_data + ADDITIONAL_JOBS
        applied_job = random.choice(all_jobs)
        
        candidate = {
            "candidate_id": f"cand_{str(uuid.uuid4())[:8]}",
            "name": name,
            "email": email,
            "phone": phone,
            "applied_for": applied_job["job_id"],
            "resume_text": resume_text,
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "role_type": role_type
        }
        
        candidates.append(candidate)
        
        if (i + 1) % 20 == 0:
            print(f"Generated {i + 1} candidates...")
    
    return candidates

def load_additional_jobs():
    """Add additional jobs to the system"""
    print("Adding additional job postings...")
    
    # Load existing jobs
    current_jobs = talent_matcher.jobs_data.copy()
    
    # Add new jobs
    all_jobs = current_jobs + ADDITIONAL_JOBS
    
    # Update jobs.json file
    with open('data/jobs/jobs.json', 'w') as f:
        json.dump(all_jobs, f, indent=2)
    
    # Reload the AI model with new jobs
    talent_matcher.load_jobs()
    
    print(f"Added {len(ADDITIONAL_JOBS)} new job postings!")
    return all_jobs

def load_large_candidate_dataset(num_candidates=100):
    """Load a large dataset of candidates into the database"""
    print(f"Loading {num_candidates} candidates into the database...")
    
    # Generate candidates
    candidates = generate_candidates(num_candidates)
    
    # Connect to database
    conn = sqlite3.connect('talent_platform.db')
    cursor = conn.cursor()
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("Clearing existing candidate and match data...")
    cursor.execute('DELETE FROM matches')
    cursor.execute('DELETE FROM candidates')
    cursor.execute('DELETE FROM assessments')
    cursor.execute('DELETE FROM feedback')
    
    total_matches = 0
    total_assessments = 0
    
    for i, candidate in enumerate(candidates):
        # Store candidate in database
        cursor.execute('''
            INSERT INTO candidates (candidate_id, name, email, phone, applied_for, resume_text, skills, experience_years)
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
        
        try:
            matches = talent_matcher.match_candidate_to_jobs(candidate_data, top_k=5)
            
            # Store matches in database
            for match in matches:
                match_id = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO matches (match_id, candidate_id, job_id, similarity_score, confidence_band, explanation)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    match_id,
                    candidate['candidate_id'],
                    match['job_id'],
                    match['similarity_score'],
                    match['confidence_band'],
                    match['explanation']
                ))
            
            total_matches += len(matches)
            
            # Generate assessment data for some candidates (60% chance)
            if random.random() < 0.6:
                # Generate assessments for top 2 job matches
                top_matches = matches[:2]
                for match in top_matches:
                    assessments = generate_assessment_data(
                        candidate['candidate_id'], 
                        match['job_id'], 
                        candidate['role_type']
                    )
                    
                    for assessment in assessments:
                        cursor.execute('''
                            INSERT INTO assessments (assessment_id, candidate_id, job_id, assessment_type, 
                                                   candidate_score, cutoff_score, max_score, status, responses, duration_minutes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            assessment["assessment_id"],
                            assessment["candidate_id"],
                            assessment["job_id"],
                            assessment["assessment_type"],
                            assessment["candidate_score"],
                            assessment["cutoff_score"],
                            assessment["max_score"],
                            assessment["status"],
                            assessment["responses"],
                            assessment["duration_minutes"]
                        ))
                    
                    total_assessments += len(assessments)
            
        except Exception as e:
            print(f"Error processing candidate {candidate['name']}: {e}")
            continue
        
        # Commit every 20 candidates to avoid memory issues
        if (i + 1) % 20 == 0:
            conn.commit()
            print(f"Processed {i + 1} candidates...")
    
    # Generate some feedback data (simulate recruiter actions)
    print("Generating sample feedback data...")
    
    # Get some random matches to simulate recruiter actions
    cursor.execute('SELECT match_id, candidate_id, job_id FROM matches ORDER BY RANDOM() LIMIT 50')
    sample_matches = cursor.fetchall()
    
    feedback_actions = ['accept', 'reject', 'promote', 'defer']
    reason_codes = ['skills_match', 'experience_good', 'cultural_fit', 'skills_mismatch', 'experience_low', 'overqualified']
    
    for match_id, candidate_id, job_id in sample_matches[:30]:  # Generate feedback for 30 matches
        action = random.choice(feedback_actions)
        reason_code = random.choice(reason_codes)
        comment = f"Sample feedback comment for {action} action"
        
        # Update match status if accepted
        if action == 'accept':
            cursor.execute('''
                UPDATE matches 
                SET status = 'accepted', updated_at = CURRENT_TIMESTAMP 
                WHERE match_id = ?
            ''', (match_id,))
        
        # Insert feedback
        feedback_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO feedback (feedback_id, candidate_id, job_id, recruiter_action, reason_code, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            feedback_id,
            candidate_id,
            job_id,
            action,
            reason_code,
            comment
        ))
    
    # Final commit
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully loaded {len(candidates)} candidates!")
    print(f"✅ Generated {total_matches} job matches!")
    print(f"✅ Created {total_assessments} assessments!")
    print(f"✅ Added sample feedback for 30 matches!")
    print("\nDatabase is now populated with extensive dummy data for testing!")

def generate_sample_resumes_file(num_candidates=50):
    """Generate an updated sample_resumes.json file with more candidates"""
    print(f"Generating sample_resumes.json with {num_candidates} candidates...")
    
    candidates = generate_candidates(num_candidates)
    
    # Convert to the format expected by sample_resumes.json
    sample_resumes = []
    for candidate in candidates:
        sample_resume = {
            "candidate_id": candidate["candidate_id"],
            "name": candidate["name"],
            "email": candidate["email"],
            "phone": candidate["phone"],
            "applied_for": candidate["applied_for"],
            "resume_text": candidate["resume_text"],
            "skills": candidate["skills"],
            "experience_years": candidate["experience_years"],
            "education": candidate["education"]
        }
        sample_resumes.append(sample_resume)
    
    # Save to file
    with open('data/resumes/sample_resumes.json', 'w') as f:
        json.dump(sample_resumes, f, indent=2)
    
    print(f"✅ Generated sample_resumes.json with {len(sample_resumes)} candidates!")

def main():
    """Main function to generate and load all dummy data"""
    print("🚀 Starting Large Dummy Data Generation for Telus Talent Platform")
    print("=" * 70)
    
    try:
        # Step 1: Add additional jobs
        load_additional_jobs()
        print()
        
        # Step 2: Generate and load large candidate dataset
        num_candidates = 150  # You can adjust this number
        load_large_candidate_dataset(num_candidates)
        print()
        
        # Step 3: Update sample resumes file
        generate_sample_resumes_file(50)
        print()
        
        print("🎉 All dummy data generation completed successfully!")
        print("=" * 70)
        print("You can now:")
        print("1. Run the application: python app.py")
        print("2. Access the dashboard at: http://localhost:8080")
        print("3. Test with extensive candidate and job data")
        print("4. Explore analytics with realistic data volumes")
        
    except Exception as e:
        print(f"❌ Error during data generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
