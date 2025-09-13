# 🤖 AI Agent Instructions - Telus AI Talent Platform

## For AI Agents: How to Run This Project

When asked to "run this project" on any laptop, follow these simple steps:

### 🚀 Quick Commands (Choose One)

**Option 1: Automatic Setup & Run (Recommended)**
```bash
# On macOS/Linux:
./install_and_run.sh

# On Windows:
install_and_run.bat
```

**Option 2: Manual Steps**
```bash
# Step 1: Setup (one-time only)
python3 setup.py

# Step 2: Run the application
python3 run_project.py
```

**Option 3: Direct Run (if already set up)**
```bash
python3 app.py
```

### 📋 What These Commands Do

1. **Check Python version** (requires 3.8+)
2. **Install all dependencies** from `requirements.txt`
3. **Create necessary directories**
4. **Initialize the database**
5. **Download AI models** (sentence-transformers)
6. **Start the web application**
7. **Open browser** to `http://localhost:8081`

### 🎯 Expected Output

When successful, you should see:
```
✅ Python version X.X.X is compatible
✅ Installing Python packages completed successfully
✅ Database initialized successfully
🎉 Setup completed successfully!
🚀 Starting Telus AI Talent Intelligence Platform...
📍 Server will be available at: http://localhost:8081
```

### 🔧 Troubleshooting

**If Python is not found:**
- Install Python 3.8+ from [python.org](https://python.org)
- Make sure it's added to PATH

**If dependencies fail to install:**
- Check internet connection
- Try: `python3 -m pip install --user -r requirements.txt`

**If port 8081 is busy:**
- Kill existing processes or change port in `app.py`

### 📁 Required Files

Make sure these files exist in the project directory:
- `app.py` (main application)
- `requirements.txt` (dependencies)
- `setup.py` (setup script)
- `run_project.py` (run script)
- `models/ai_models.py` (AI logic)
- `data/jobs/jobs.json` (job data)
- `templates/` folder (HTML templates)

### 🎉 Success Indicators

The project is working when:
1. ✅ No error messages in console
2. ✅ Browser opens automatically
3. ✅ Beautiful dashboard loads at `http://localhost:8081`
4. ✅ Can upload resumes and see AI matches

---

## 📝 Summary for AI Agents

**Single command to run everything:**
```bash
python3 setup.py && python3 run_project.py
```

This will handle all setup and start the application automatically!
