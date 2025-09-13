# 🚀 Telus AI Talent Intelligence Platform

## Overview
An AI-powered talent matching system that automatically matches candidates to multiple roles, provides confidence-based routing, and includes human-in-the-loop workflows.

## ⚡ Quick Start

**To run this project on any laptop, simply execute:**

```bash
# 1. Setup the project (one-time only)
python3 setup.py

# 2. Run the application
python3 run_project.py
```

That's it! The application will automatically open in your browser at `http://localhost:8081`

## 🎯 Core Features

- **AI Resume Parsing** - Intelligent extraction of skills and experience
- **Semantic Job Matching** - Using Sentence-BERT for deep understanding
- **Confidence-Based Routing** - Auto/Review/Human confidence bands
- **Recruiter Dashboard** - Override decisions and provide feedback
- **Alternative Role Suggestions** - Multi-role candidate redirection
- **Skill Gap Analysis** - Training recommendations for candidates
- **Human-in-the-Loop** - Continuous learning from recruiter feedback

## 🏗️ Architecture

- **Backend**: FastAPI + Python
- **AI Models**: Sentence Transformers + Enhanced Matching Algorithms
- **Vector Search**: FAISS for fast similarity search
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS
- **Database**: SQLite (for demo)

## 📦 Project Structure

```
telus-ai-talent-platform/
├── 📄 app.py                     # Main FastAPI application
├── 📄 setup.py                   # Setup script
├── 📄 run_project.py              # Quick run script
├── 📄 requirements.txt            # Python dependencies
├── 📁 models/
│   └── improved_ai_models.py      # Advanced AI matching logic
├── 📁 templates/                  # HTML templates
│   ├── dashboard.html             # Main dashboard
│   ├── upload.html               # Resume upload page
│   └── candidate_detail.html     # Candidate details
├── 📁 data/
│   ├── jobs/jobs.json            # Job descriptions
│   └── resumes/                  # Sample resumes
├── 📁 static/                    # CSS, JS, images
└── 📁 config/                    # Configuration files
```

## 🎯 Demo Flow

1. **Upload Resume** - Drag & drop PDF, DOC, DOCX, or TXT files
2. **AI Processing** - Automatic parsing and skill extraction
3. **Smart Matching** - Multi-algorithm job matching with confidence scores
4. **Review Results** - See top matches with detailed explanations
5. **Alternative Roles** - Discover other suitable positions
6. **Recruiter Feedback** - Accept/reject with learning feedback
7. **Skill Analysis** - Gap analysis and training recommendations

## 📋 Prerequisites

- **Python 3.8+** (Required)
- **Internet connection** (for downloading AI models)
- **4GB+ RAM** (for AI model loading)

## 🔧 Manual Installation

```bash
# Clone the repository
git clone <repository-url>
cd telus-ai-talent-platform

# Setup (one-time only)
python3 setup.py

# Run the application
python3 run_project.py
```

## 🌐 Application URLs

- **Dashboard**: `http://localhost:8081` - Main recruiter interface
- **Upload**: `http://localhost:8081/upload` - Resume upload page
- **API Docs**: `http://localhost:8081/docs` - Interactive API documentation

## 🔍 Troubleshooting

### Common Issues

**Python Version Error**
```bash
# Install Python 3.8+ from python.org
python3 --version  # Should be 3.8+
```

**Port Already in Use**
```bash
# Kill existing process or change port in app.py
lsof -ti:8081 | xargs kill -9
```

**Virtual Environment (Recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
python3 setup.py
python3 run_project.py
```

## 🎉 Success Indicators

When working correctly, you should see:
```
✅ Python version compatible
✅ Dependencies installed
✅ Database initialized
✅ AI models loaded
🚀 Server running at http://localhost:8081
🌐 Browser opening automatically
```

## 🤖 For AI Agents

This project is optimized for AI agent deployment:
1. Copy all files to target laptop
2. Run `python3 setup.py` once
3. Run `python3 run_project.py` to start
4. Access dashboard at `http://localhost:8081`

The setup script handles everything automatically!