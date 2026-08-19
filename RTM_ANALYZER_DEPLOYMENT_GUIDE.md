# 🚀 RTM Analyzer - Deployment & Setup Guide

## Overview

**RTM Analyzer** is a web-based Requirements Traceability Matrix analyzer that supports multiple document sources (Google Sheets, Docs, Confluence, Jira) and provides comprehensive analysis with ISO 9001 compliance reporting.

---

## 📋 Quick Start (5 minutes)

### Step 1: Get the Code

```bash
# Clone or create GitHub repo
git clone https://github.com/yourusername/rtm-analyzer.git
cd rtm-analyzer

# Copy the app file
cp rtm_analyzer_app.py app.py
```

### Step 2: Set Up Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure API Keys

Create `.streamlit/secrets.toml`:

```toml
# Jira Configuration
jira_token = "ATATT3xFfGF0OdkSkBsx_..."
jira_user = "govind.raj@exacttechnology.com"
jira_url = "https://etcengineering.atlassian.net"

# Anthropic Configuration
anthropic_key = "sk-ant-api03-..."

# Google Configuration
google_key = "AIzaSy..."
```

**⚠️ IMPORTANT:** Add to `.gitignore`:
```
.streamlit/secrets.toml
.env
*.env
```

### Step 4: Run Locally

```bash
streamlit run app.py
```

Visit: `http://localhost:8501`

---

## 🌐 Deploy to Streamlit Cloud (FREE)

### Step 1: Push to GitHub

```bash
# Initialize git
git init
git add .
git commit -m "Initial RTM Analyzer commit"

# Create GitHub repo (via web browser)
# Then push:
git remote add origin https://github.com/yourusername/rtm-analyzer.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Click **"New app"**
3. Connect GitHub account
4. Select repo: `rtm-analyzer`
5. Select branch: `main`
6. Select file: `app.py`
7. Click **Deploy**

### Step 3: Add Secrets (CRITICAL!)

1. In Streamlit Cloud app settings
2. **Settings** → **Secrets**
3. Add the same keys from `.streamlit/secrets.toml`:

```toml
jira_token = "ATATT3xFfGF0OdkSkBsx_..."
jira_user = "govind.raj@exacttechnology.com"
jira_url = "https://etcengineering.atlassian.net"
anthropic_key = "sk-ant-api03-..."
google_key = "AIzaSy..."
```

4. Click **Save**

✅ Your app is now LIVE!

---

## 📂 Project Structure

```
rtm-analyzer/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── .gitignore                      # Exclude secrets
├── .streamlit/
│   └── config.toml                 # Streamlit config
│   └── secrets.toml                # API keys (NEVER commit!)
├── README.md                       # Project documentation
└── utils/                          # Helper modules (optional)
    ├── __init__.py
    ├── jira_client.py              # Jira integration
    ├── google_client.py            # Google API integration
    └── analyzer.py                 # Analysis logic
```

---

## 🔑 API Keys Setup

### 1. Jira API Token

```
1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it: "RTM Analyzer"
4. Copy token
5. Paste into secrets.toml
```

**Format:**
```
jira_token = "ATATT3xFfGF0OdkSkBsx_..."
jira_user = "your.email@exacttechnology.com"
jira_url = "https://etcengineering.atlassian.net"
```

---

### 2. Anthropic (Claude) API Key

```
1. Go to: https://console.anthropic.com/account/api-keys
2. Click "Create Key"
3. Name it: "RTM Analyzer"
4. Copy key
5. Paste into secrets.toml
```

**Format:**
```
anthropic_key = "sk-ant-api03-..."
```

---

### 3. Google API Key

For accessing Google Sheets/Docs:

```
1. Go to: https://console.cloud.google.com
2. Create new project "RTM Analyzer"
3. Enable APIs:
   - Google Sheets API
   - Google Docs API
   - Google Drive API
4. Create credentials (API Key)
5. Paste into secrets.toml
```

**Format:**
```
google_key = "AIzaSy..."
```

---

### 4. Service Account (Advanced - Optional)

For better security with Google APIs:

```
1. In Google Cloud console
2. Create Service Account
3. Generate JSON key
4. Download and save to secrets

In app code:
from google.oauth2 import service_account
import json

sa_key = st.secrets["google_sa_json"]
```

---

## 🛡️ Security Best Practices

### ✅ DO:

```python
# Store secrets in Streamlit secrets
api_key = st.secrets["api_key"]

# Use environment variables in .env
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("API_KEY")

# Never hardcode credentials
# Use conditional logic for different environments
if st.secrets.get("environment") == "production":
    api_key = st.secrets["prod_key"]
else:
    api_key = st.secrets["dev_key"]
```

### ❌ DON'T:

```python
# Never hardcode API keys
api_key = "ATATT3xFfGF0OdkSkBsx_..."  # ❌ BAD!

# Never commit secrets.toml
git add .streamlit/secrets.toml  # ❌ BAD!

# Never log sensitive data
st.write(f"Using key: {api_key}")  # ❌ BAD!

# Never share on public channels
"Here's our API key: ATATT3xFfGF0..."  # ❌ BAD!
```

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] Code tested locally
- [ ] All dependencies in requirements.txt
- [ ] Secrets in .streamlit/secrets.toml
- [ ] .gitignore includes secrets files
- [ ] README.md updated
- [ ] GitHub repo created and ready

### Deployment

- [ ] Code pushed to GitHub (main branch)
- [ ] Streamlit Cloud connected
- [ ] App deployed successfully
- [ ] Secrets added to Streamlit Cloud
- [ ] App tested in production
- [ ] URL shared with team

### Post-Deployment

- [ ] Monitor for errors (Streamlit Cloud dashboard)
- [ ] Test all features work
- [ ] Verify API integrations
- [ ] Document any issues
- [ ] Set up auto-redeploy on GitHub push

---

## 📋 GitHub Setup

### Initialize Repository

```bash
# Navigate to project folder
cd rtm-analyzer

# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial RTM Analyzer release"

# Create main branch
git branch -M main

# Add remote
git remote add origin https://github.com/yourusername/rtm-analyzer.git

# Push to GitHub
git push -u origin main
```

### .gitignore (Critical!)

Create `.gitignore`:

```
# Secrets
.streamlit/secrets.toml
.env
.env.local
*.key
*.pem

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

---

## 🧪 Testing

### Local Testing

```bash
# Run app
streamlit run app.py

# Test URL input
https://docs.google.com/spreadsheets/d/1tzRTNtq3N-QPabBSowhmzYXuxHR9bimvYTn1z0wjuQs/edit

# Test each feature
- Tab 1: Quick Analysis
- Tab 2: Detailed Report
- Tab 3: Test Case Analysis
- Tab 4: Batch Analysis
- Tab 5: Dashboard
```

### Production Testing

```
1. Visit deployed URL
2. Test same URLs as local
3. Verify results match
4. Check report download
5. Test email feature (if enabled)
```

---

## 🔄 Updates & Maintenance

### Auto-Redeploy from GitHub

```
Streamlit Cloud automatically redeploys when:
✅ You push to main branch
✅ Requirements.txt is updated
✅ App code is changed

Timeline: Usually within 1 minute
```

### Manual Redeploy

In Streamlit Cloud dashboard:
1. Click app
2. Click menu (⋮)
3. Select "Reboot app"
4. App restarts

### Update Process

```bash
# Make changes locally
# Test locally: streamlit run app.py

# Push to GitHub
git add .
git commit -m "Feature: Add X"
git push

# Streamlit Cloud auto-redeploys!
# Check deployment in dashboard
```

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError"

```
Solution:
1. pip install -r requirements.txt
2. Streamlit Cloud > App settings > Python version 3.11
3. Redeploy
```

### Issue: "API Key Error"

```
Solution:
1. Verify secrets in .streamlit/secrets.toml
2. Don't commit secrets (check .gitignore)
3. Add secrets to Streamlit Cloud Settings
4. Restart app
```

### Issue: "Cannot Access Google Sheets"

```
Solution:
1. Make sheets public (Share link) OR
2. Use service account with permission
3. Verify Google API key is valid
4. Check quotas in Google Cloud Console
```

### Issue: "Jira Connection Failed"

```
Solution:
1. Verify Jira token is valid
2. Check Jira URL is correct
3. Verify email/username is correct
4. Test token: curl -u email:token https://jira-url/rest/api/3/myself
```

### Issue: "App Too Slow"

```
Solution:
1. Add @st.cache_data for expensive operations
2. Reduce document size (first 5000 chars)
3. Use Streamlit Cloud Pro for more resources
4. Profile code with: streamlit run app.py --logger.level=debug
```

---

## 📊 Monitoring

### Streamlit Cloud Dashboard

```
https://share.streamlit.io → Select your app

Check:
- Deployment status (green = good)
- Runtime logs
- CPU/Memory usage
- Recent app activity
```

### Error Logs

```
Click "Logs" tab to see:
- App errors
- API failures
- Performance issues
```

---

## 📧 Email Feature (Optional)

To enable email reports, integrate SendGrid:

```python
# Install: pip install sendgrid

import sendgrid
from sendgrid.helpers.mail import Mail

def send_email(to_email, subject, content):
    message = Mail(
        from_email='noreply@exacttechnology.com',
        to_emails=to_email,
        subject=subject,
        plain_text_content=content
    )
    
    sg = sendgrid.SendGridAPIClient(st.secrets["sendgrid_key"])
    response = sg.send(message)
    return response.status_code
```

Add to secrets.toml:
```
sendgrid_key = "SG.xxxxx..."
```

---

## 🎯 Next Steps

1. **Set up GitHub repository**
   - Clone or create repo
   - Add files
   - Commit and push

2. **Configure API keys**
   - Get Jira token
   - Get Anthropic key
   - Get Google key
   - Add to secrets.toml

3. **Deploy to Streamlit Cloud**
   - Connect GitHub
   - Deploy app
   - Add secrets in cloud
   - Test live

4. **Share with team**
   - Send URL: https://your-app.streamlit.app
   - They can start using immediately!
   - No installation needed

---

## 📚 Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Streamlit Cloud:** https://share.streamlit.io
- **Jira API:** https://developer.atlassian.com/cloud/jira/rest
- **Anthropic Docs:** https://docs.anthropic.com
- **GitHub:** https://github.com

---

## 💬 Support

For issues:
1. Check troubleshooting section above
2. Review Streamlit Cloud logs
3. Test locally: `streamlit run app.py`
4. Check API key validity
5. Verify URL formats

---

**RTM Analyzer v1.0.0 | Exact Technology**

Happy analyzing! 🚀
