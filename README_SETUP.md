# 🚀 Telus AI Talent Intelligence Platform - Setup Guide

## Quick Start (For AI Agents)

**To run this project on any laptop, simply execute:**

```bash
# 1. Setup the project (one-time only)
python3 setup.py

# 2. Run the application
python3 run_project.py
```

That's it! The application will automatically open in your browser at `http://localhost:8081`

---

## 📋 Prerequisites

- **Python 3.8+** (Required)
- **Internet connection** (for downloading AI models)
- **4GB+ RAM** (for AI model loading)

---

## 🔧 Manual Installation Steps

### 1. Clone/Download the Project
```bash
# If using git
git clone <repository-url>
cd telus-ai-talent-platform

# Or download and extract the ZIP file
```

### 2. Run Setup Script
```bash
python3 setup.py
```

This will:
- ✅ Check Python version compatibility
- ✅ Create necessary directories
- ✅ Install all dependencies from `requirements.txt`
- ✅ Initialize the SQLite database
- ✅ Download AI models (sentence-transformers)

### 3. Start the Application
```bash
python3 run_project.py
```

Or manually:
```bash
python3 app.py
```

---

## 📦 What Gets Installed

The setup script installs these key dependencies:

### Core Framework
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine

### AI/ML Libraries
- `sentence-transformers` - For semantic text analysis
- `faiss-cpu` - For fast similarity search
- `scikit-learn` - For machine learning utilities
- `numpy` - For numerical computations

### File Processing
- `PyPDF2` - For PDF resume parsing
- `python-multipart` - For file uploads

### Additional Tools
- `pydantic` - Data validation
- `aiofiles` - Async file operations
- `python-dotenv` - Environment variables

---

## 🗂️ Project Structure

```
telus-ai-talent-platform/
├── 📄 app.py                 # Main FastAPI application
├── 📄 setup.py              # Setup script
├── 📄 run_project.py         # Quick run script
├── 📄 requirements.txt       # Python dependencies
├── 📄 README_SETUP.md        # This file
├── 📁 models/
│   └── ai_models.py          # AI matching logic
├── 📁 templates/             # HTML templates
│   ├── dashboard.html        # Main dashboard
│   ├── upload.html          # Resume upload page
│   └── candidate_detail.html # Candidate details
├── 📁 data/
│   ├── jobs/
│   │   └── jobs.json        # Job descriptions
│   └── resumes/             # Sample resumes
├── 📁 static/               # Static files (CSS, JS)
└── 📁 config/               # Configuration files
```

---

## 🌐 Application Features

### 🎯 Dashboard (`http://localhost:8081`)
- Real-time analytics
- Candidate management
- Job matching overview

### 📤 Upload Page (`http://localhost:8081/upload`)
- Drag & drop resume upload
- Support for PDF, DOC, DOCX, TXT
- AI-powered processing

### 👤 Candidate Details
- Detailed candidate profiles
- Job match analysis
- Skill gap recommendations

---

## 🔍 Troubleshooting

### Common Issues

**1. Python Version Error**
```
❌ Python 3.8 or higher is required
```
**Solution:** Install Python 3.8+ from [python.org](https://python.org)

**2. Permission Denied**
```
❌ Permission denied during installation
```
**Solution:** Use virtual environment or add `--user` flag:
```bash
python3 -m pip install --user -r requirements.txt
```

**3. Port Already in Use**
```
❌ Port 8081 is already in use
```
**Solution:** Kill existing process or change port in `app.py`

**4. AI Model Download Fails**
```
❌ Error downloading sentence-transformers model
```
**Solution:** Check internet connection and try again

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Run setup
python3 setup.py

# Run application
python3 run_project.py
```

---

## 🚀 For AI Agents

When an AI agent needs to run this project:

1. **Copy all project files** to the target laptop
2. **Run setup once**: `python3 setup.py`
3. **Start application**: `python3 run_project.py`
4. **Access at**: `http://localhost:8081`

The setup script handles everything automatically!

---

## 📞 Support

If you encounter issues:

1. Check the console output for error messages
2. Ensure Python 3.8+ is installed
3. Verify internet connection for AI model downloads
4. Try running in a virtual environment

---

## 🎉 Success Indicators

When everything is working correctly, you should see:

```
✅ Python version X.X.X is compatible
✅ Created directory: static
✅ Created directory: data/jobs
✅ Upgrading pip completed successfully
✅ Installing Python packages completed successfully
✅ Database initialized successfully
🎉 Setup completed successfully!

🚀 Starting Telus AI Talent Intelligence Platform...
📍 Server will be available at: http://localhost:8081
⏳ Loading AI models (this may take a moment)...
✅ Application starting...
🌐 Opening browser in 3 seconds...
```

The browser should automatically open to the beautiful Tailwind CSS dashboard!
