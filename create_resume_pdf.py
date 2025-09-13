#!/usr/bin/env python3
"""
Script to convert the text resume to PDF format
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import os

def create_resume_pdf():
    # Create PDF document
    doc = SimpleDocTemplate("john_smith_resume.pdf", pagesize=A4,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=black
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=black
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=3,
        spaceBefore=6,
        textColor=black
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=3,
        alignment=TA_JUSTIFY
    )
    
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    # Story list to hold all content
    story = []
    
    # Header
    story.append(Paragraph("JOHN SMITH", title_style))
    story.append(Paragraph("Senior Software Engineer", subheading_style))
    story.append(Paragraph("Email: john.smith@email.com | Phone: +91-9876543210<br/>LinkedIn: linkedin.com/in/johnsmith | GitHub: github.com/johnsmith<br/>Location: Bengaluru, Karnataka, India", contact_style))
    story.append(Spacer(1, 12))
    
    # Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", heading_style))
    story.append(Paragraph("Experienced Senior Software Engineer with 6+ years of expertise in building scalable microservices and cloud infrastructure. Proven track record in Python development, AWS cloud services, containerization with Docker and Kubernetes, and implementing DevOps practices. Strong background in mentoring junior developers and leading technical initiatives in fast-paced environments.", normal_style))
    story.append(Spacer(1, 12))
    
    # Technical Skills
    story.append(Paragraph("TECHNICAL SKILLS", heading_style))
    skills_text = """
    <b>Programming Languages:</b> Python, Java, JavaScript, Go<br/>
    <b>Cloud Platforms:</b> AWS (EC2, S3, Lambda, RDS, EKS), Azure<br/>
    <b>Containerization:</b> Docker, Kubernetes, Docker Compose<br/>
    <b>Microservices:</b> REST APIs, GraphQL, Service Mesh, API Gateway<br/>
    <b>DevOps Tools:</b> Jenkins, GitLab CI/CD, Terraform, Ansible<br/>
    <b>Databases:</b> PostgreSQL, MySQL, MongoDB, Redis<br/>
    <b>Frameworks:</b> Django, Flask, FastAPI, React, Node.js<br/>
    <b>Monitoring:</b> Prometheus, Grafana, ELK Stack, CloudWatch<br/>
    <b>Version Control:</b> Git, GitHub, GitLab
    """
    story.append(Paragraph(skills_text, normal_style))
    story.append(Spacer(1, 12))
    
    # Professional Experience
    story.append(Paragraph("PROFESSIONAL EXPERIENCE", heading_style))
    
    # Job 1
    story.append(Paragraph("<b>Senior Software Engineer | TechCorp Solutions | Bengaluru | Jan 2020 - Present</b>", subheading_style))
    job1_bullets = [
        "Designed and developed 15+ microservices using Python and FastAPI, serving 1M+ daily active users",
        "Implemented containerization strategy using Docker and Kubernetes, reducing deployment time by 70%",
        "Architected AWS cloud infrastructure using EC2, EKS, RDS, and S3, achieving 99.9% uptime",
        "Led migration from monolithic architecture to microservices, improving system scalability by 300%",
        "Mentored 5 junior developers and conducted code reviews, improving team productivity by 40%",
        "Implemented CI/CD pipelines using Jenkins and GitLab, reducing release cycle from weeks to days",
        "Optimized database queries and implemented caching strategies, improving API response time by 60%"
    ]
    for bullet in job1_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 6))
    
    # Job 2
    story.append(Paragraph("<b>Software Engineer | DataFlow Systems | Bengaluru | Jun 2018 - Dec 2019</b>", subheading_style))
    job2_bullets = [
        "Developed Python-based data processing applications handling 10TB+ daily data volume",
        "Built RESTful APIs using Django and Flask frameworks for internal and external clients",
        "Implemented Docker containerization for development and production environments",
        "Collaborated with DevOps team to deploy applications on AWS using Kubernetes",
        "Participated in Agile development process and sprint planning sessions",
        "Wrote comprehensive unit tests achieving 90%+ code coverage"
    ]
    for bullet in job2_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 6))
    
    # Job 3
    story.append(Paragraph("<b>Junior Software Developer | StartupTech | Bengaluru | Jul 2017 - May 2018</b>", subheading_style))
    job3_bullets = [
        "Developed web applications using Python, Django, and React",
        "Worked with PostgreSQL and MongoDB databases for data storage and retrieval",
        "Participated in code reviews and followed best practices for software development",
        "Gained experience with AWS services including EC2, S3, and RDS"
    ]
    for bullet in job3_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 12))
    
    # Projects
    story.append(Paragraph("PROJECTS", heading_style))
    
    story.append(Paragraph("<b>E-commerce Microservices Platform (2022)</b>", subheading_style))
    project1_bullets = [
        "Built scalable e-commerce platform using Python microservices architecture",
        "Implemented using Docker, Kubernetes, AWS EKS, and PostgreSQL",
        "Integrated payment gateways and implemented real-time inventory management",
        "Technologies: Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis"
    ]
    for bullet in project1_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("<b>Real-time Analytics Dashboard (2021)</b>", subheading_style))
    project2_bullets = [
        "Developed real-time analytics platform processing 1M+ events per hour",
        "Used Python, Apache Kafka, and React for data streaming and visualization",
        "Deployed on AWS using EKS and implemented auto-scaling policies",
        "Technologies: Python, Kafka, React, AWS, Kubernetes, InfluxDB"
    ]
    for bullet in project2_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 12))
    
    # Education
    story.append(Paragraph("EDUCATION", heading_style))
    story.append(Paragraph("<b>Bachelor of Technology in Computer Science Engineering</b><br/>Indian Institute of Technology (IIT) Bengaluru | 2013 - 2017<br/>CGPA: 8.5/10", normal_style))
    story.append(Spacer(1, 12))
    
    # Certifications
    story.append(Paragraph("CERTIFICATIONS", heading_style))
    cert_bullets = [
        "AWS Certified Solutions Architect - Associate (2021)",
        "Certified Kubernetes Administrator (CKA) (2020)",
        "Docker Certified Associate (2019)"
    ]
    for bullet in cert_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 12))
    
    # Achievements
    story.append(Paragraph("ACHIEVEMENTS", heading_style))
    achievement_bullets = [
        "Led team that won \"Best Innovation Award\" for microservices migration project (2022)",
        "Reduced infrastructure costs by 35% through optimization and right-sizing initiatives",
        "Published technical blog posts on microservices and Kubernetes with 10K+ views",
        "Speaker at Bengaluru Python Meetup on \"Building Scalable APIs with FastAPI\""
    ]
    for bullet in achievement_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    story.append(Spacer(1, 12))
    
    # Languages
    story.append(Paragraph("LANGUAGES", heading_style))
    lang_bullets = [
        "English (Fluent)",
        "Hindi (Native)",
        "Kannada (Conversational)"
    ]
    for bullet in lang_bullets:
        story.append(Paragraph(f"• {bullet}", normal_style))
    
    # Build PDF
    doc.build(story)
    print("Resume PDF created successfully: john_smith_resume.pdf")

if __name__ == "__main__":
    create_resume_pdf()
