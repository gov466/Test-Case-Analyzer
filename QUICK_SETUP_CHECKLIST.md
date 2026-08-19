# ⚡ RTM Analyzer - 30-Minute Setup Checklist

**Goal:** Get RTM Analyzer running and deployed in 30 minutes!

---

## ⏱️ Timeline Estimate

```
Step 1: Gather API Keys        (5 min)
Step 2: GitHub Setup           (5 min)
Step 3: Local Testing          (5 min)
Step 4: Deploy to Cloud        (10 min)
Step 5: Share with Team        (2 min)
────────────────────────────────────
TOTAL:                          27 min! 🎉
```

---

## 📋 STEP 1: Gather API Keys (5 minutes)

### Jira Token

- [ ] Go to: https://id.atlassian.com/manage-profile/security/api-tokens
- [ ] Click "Create API token"
- [ ] Name it: `RTM Analyzer`
- [ ] Copy the token
- [ ] Save somewhere (you'll need it in Step 2)

**Format:**
```
jira_token = "ATATT3xFfGF0OdkSkBsx_..."
jira_user = "govind.raj@exacttechnology.com"
jira_url = "https://etcengineering.atlassian.net"
```

### Anthropic (Claude) API Key

- [ ] Go to: https://console.anthropic.com/account/api-keys
- [ ] Click "Create Key"
- [ ] Name it: `RTM Analyzer`
- [ ] Copy the key
- [ ] Save it

**Format:**
```
anthropic_key = "sk-ant-api03-..."
```

### Google API Key (Optional, but recommended)

- [ ] Go to: https://console.cloud.google.com
- [ ] Create new project: `RTM Analyzer`
- [ ] Enable: Google Sheets API, Google Docs API
- [ ] Create API Key (Credentials)
- [ ] Copy the key
- [ ] Save it

**Format:**
```
google_key = "AIzaSy..."
```

---

## 📂 STEP 2: GitHub Setup (5 minutes)

### Create Repository

- [ ] Go to: https://github.com/new
- [ ] Repository name: `rtm-analyzer`
- [ ] Description: `Comprehensive Requirements Traceability Matrix Analyzer`
- [ ] Public (recommended for Streamlit Cloud)
- [ ] Click "Create repository"

### Clone & Add Files

```bash
# Clone the empty repo
git clone https://github.com/yourusername/rtm-analyzer.git
cd rtm-analyzer

# Copy app files
cp rtm_analyzer_app.py app.py
cp requirements.txt .
cp README_RTM_ANALYZER.md README.md
```

### Create Secrets File

```bash
# Create directories
mkdir -p .streamlit

# Create secrets file
cat > .streamlit/secrets.toml << EOF
# Jira Configuration
jira_token = "PASTE_YOUR_JIRA_TOKEN_HERE"
jira_user = "govind.raj@exacttechnology.com"
jira_url = "https://etcengineering.atlassian.net"

# Anthropic Configuration
anthropic_key = "PASTE_YOUR_ANTHROPIC_KEY_HERE"

# Google Configuration
google_key = "PASTE_YOUR_GOOGLE_KEY_HERE"
EOF
```

### Create .gitignore

```bash
cat > .gitignore << EOF
# Secrets (NEVER commit!)
.streamlit/secrets.toml
.env
.env.local

# Python
__pycache__/
*.py[cod]
venv/
env/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF
```

### Push to GitHub

```bash
git add .
git commit -m "Initial RTM Analyzer"
git branch -M main
git push -u origin main
```

---

## 🧪 STEP 3: Local Testing (5 minutes)

### Install & Run

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

### Test Features

- [ ] App opens at `http://localhost:8501`
- [ ] Enter settings (API keys)
- [ ] Try "Quick Analysis" tab with test URL
- [ ] Try "Detailed Report" tab
- [ ] Try downloading CSV
- [ ] If all ✅ → Ready to deploy!

**Test URL (if you have access):**
```
https://docs.google.com/spreadsheets/d/1tzRTNtq3N-QPabBSowhmzYXuxHR9bimvYTn1z0wjuQs/edit
```

---

## 🚀 STEP 4: Deploy to Cloud (10 minutes)

### Streamlit Cloud Deployment

1. **Go to:** https://share.streamlit.io
2. **Sign in** with GitHub (if not already)
3. **Click:** "New app"
4. **Select Repository:**
   - [ ] username: `yourusername`
   - [ ] repository: `rtm-analyzer`
   - [ ] branch: `main`
5. **Main file path:** `app.py`
6. **Click:** "Deploy"

**Wait 2-3 minutes for deployment...**

### Add Secrets to Cloud

1. **Go to:** Your app in Streamlit Cloud dashboard
2. **Click:** ⋮ (menu) → Settings
3. **Click:** "Secrets" tab
4. **Paste your secrets:**

```toml
jira_token = "ATATT3xFfGF0OdkSkBsx_..."
jira_user = "govind.raj@exacttechnology.com"
jira_url = "https://etcengineering.atlassian.net"
anthropic_key = "sk-ant-api03-..."
google_key = "AIzaSy..."
```

5. **Click:** "Save"
6. **Wait:** App auto-redeploys (1-2 min)

### Verify Deployment

- [ ] App is running (green status in dashboard)
- [ ] URL looks like: `https://yourusername-rtm-analyzer.streamlit.app`
- [ ] Click the URL to open app
- [ ] Test quick analysis works
- [ ] Settings show API keys loaded ✅

---

## 👥 STEP 5: Share with Team (2 minutes)

### Send to Team

```
Send this message to Tyler, Shahin, and team:

---

Hey! Check out the new RTM Analyzer! 🚀

https://yourusername-rtm-analyzer.streamlit.app

Features:
✅ Quick analysis of any RTM
✅ ISO 9001 compliance reports
✅ Test coverage analysis
✅ Batch document comparison

No installation needed - just click the link!

Questions? See the README in the repo.

---
```

### Slack Integration

```
Post to #engineering or team channel:

@channel 📊 New tool available!

RTM Analyzer - https://yourusername-rtm-analyzer.streamlit.app

Analyze any requirements document instantly!
- Google Sheets/Docs
- Confluence pages
- Jira filters
- GitHub files

Try it: https://yourusername-rtm-analyzer.streamlit.app ✨
```

---

## ✅ COMPLETE CHECKLIST

### API Keys
- [ ] Jira token obtained
- [ ] Anthropic key obtained
- [ ] Google key obtained

### GitHub
- [ ] Repository created
- [ ] Files added
- [ ] .gitignore configured
- [ ] Pushed to GitHub

### Local Testing
- [ ] App runs locally
- [ ] Quick analysis works
- [ ] Reports download correctly
- [ ] No error messages

### Cloud Deployment
- [ ] Deployed to Streamlit Cloud
- [ ] Secrets added to cloud
- [ ] App is running (green status)
- [ ] Live URL verified

### Team Sharing
- [ ] Shared URL with team
- [ ] Posted to Slack/chat
- [ ] Team can access
- [ ] Ready for use!

---

## 🎉 SUCCESS! You're Done!

Your RTM Analyzer is now:
- ✅ Running in the cloud
- ✅ Accessible to team
- ✅ Fully functional
- ✅ Easy to update

---

## 📊 What's Next?

### Now That It's Live

1. **Team Testing**
   - Have team try it
   - Gather feedback
   - Report any issues

2. **Customize** (Optional)
   - Add team logo
   - Adjust colors
   - Add more features

3. **Integrate** (Advanced)
   - Add Slack bot
   - Set up email reports
   - Create dashboards

4. **Scale**
   - Add more team members
   - Integrate with more tools
   - Track usage metrics

---

## 🆘 Quick Troubleshooting

### "Deployment Failed"
```
→ Check GitHub push was successful
→ Verify all files committed
→ Check Streamlit Cloud logs
→ Redeploy manually
```

### "API Keys Not Working"
```
→ Verify keys in .streamlit/secrets.toml
→ Verify keys added to Streamlit Cloud
→ Restart app
→ Check key validity in original service
```

### "Can't Access Google Sheets"
```
→ Make sheets public (share link)
→ Check Google key is valid
→ Try different document
```

### "Jira Connection Error"
```
→ Verify Jira token is valid
→ Check Jira URL is correct
→ Verify email/username match
```

---

## 📞 Help Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Deployment Guide:** See RTM_ANALYZER_DEPLOYMENT_GUIDE.md
- **API Help:** Check settings panel in app

---

## 🎯 Estimated Costs

```
Streamlit Cloud (FREE tier):
├─ 1 app
├─ Up to 3GB storage
└─ Unlimited bandwidth = $0/month

GitHub (FREE):
├─ Unlimited repos
└─ = $0/month

API Costs (depends on usage):
├─ Jira: $0 (you're already paying)
├─ Anthropic: $0.50-1.00/month typical
└─ Google: $0 (free tier generous)

TOTAL: ~$0-1/month 💰
```

---

## 📈 Keep It Updated

Auto-updates from GitHub:
```
1. Make changes locally
2. Test locally: streamlit run app.py
3. Push to GitHub: git push
4. Streamlit Cloud auto-redeploys! (1 min)
5. Everyone gets new version instantly
```

---

## 🚀 Go Live Now!

You've got everything you need. Let's go! 

**Start at Step 1 and you'll be done in 30 minutes!** ⏱️

Questions? Check the Deployment Guide or troubleshooting above.

---

**Happy analyzing!** 📊✨
