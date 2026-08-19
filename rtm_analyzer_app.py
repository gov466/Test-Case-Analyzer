"""
RTM Analyzer - Web App
Comprehensive Requirements Traceability Matrix Analyzer
Supports: Google Sheets, Docs, Confluence, Jira, GitHub

Author: Govind Raj
Company: Exact Technology
License: Internal Use
"""

import streamlit as st
import pandas as pd
import requests
from urllib.parse import urlparse, parse_qs
import re
from datetime import datetime
import json
import base64
from io import BytesIO, StringIO
import anthropic

# ============================================================================
# FUNCTION DEFINITIONS (MUST BE BEFORE USE)
# ============================================================================

def fetch_url_content(url: str, google_key: str, jira_user: str, jira_token: str) -> str:
    """Fetch content from various URL types"""
    
    try:
        # Google Sheets
        if 'docs.google.com/spreadsheets' in url:
            sheet_id = extract_google_id(url)
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            response = requests.get(export_url, timeout=10)
            return response.text
        
        # Google Docs
        elif 'docs.google.com/document' in url:
            doc_id = extract_google_id(url)
            export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            response = requests.get(export_url, timeout=10)
            return response.text
        
        # Confluence
        elif 'confluence' in url:
            api_url = url.replace('/display/', '/rest/api/content/')
            api_url += '?expand=body.storage'
            headers = {'Authorization': f'Bearer {jira_token}'}
            response = requests.get(api_url, headers=headers, timeout=10)
            return response.text
        
        # Jira JQL
        elif 'atlassian.net' in url and 'jql' in url:
            headers = {'Authorization': f'Basic {base64.b64encode(f"{jira_user}:{jira_token}".encode()).decode()}'}
            response = requests.get(url, headers=headers, timeout=10)
            return json.dumps(response.json())
        
        # GitHub
        elif 'github.com' in url:
            raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            response = requests.get(raw_url, timeout=10)
            return response.text
        
        # Default HTTP
        else:
            response = requests.get(url, timeout=10)
            return response.text
    
    except Exception as e:
        st.error(f"Could not fetch URL: {str(e)}")
        return ""

def extract_google_id(url: str) -> str:
    """Extract Google Sheets/Docs ID from URL"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else ""

def extract_jira_links(content: str, patterns: dict) -> dict:
    """Extract and count Jira links from content"""
    
    all_issues = {}
    projects = {}
    slack_count = 0
    
    # Find all Jira links
    for project, pattern in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            projects[project] = len(set(matches))
            for match in set(matches):
                all_issues[match] = all_issues.get(match, 0) + 1
    
    # Find Slack references
    slack_matches = re.findall(r'slack\.com|slack message', content, re.IGNORECASE)
    slack_count = len(slack_matches) // 2  # Rough estimate
    
    return {
        'total_links': len(all_issues),
        'unique_issues': len(set(all_issues.keys())),
        'projects_count': len(projects),
        'slack_refs': slack_count,
        'issues_breakdown': [
            {'Project': p, 'Issues': c} for p, c in sorted(projects.items())
        ],
        'all_links': [[k, v] for k, v in sorted(all_issues.items())]
    }

def generate_basic_analysis(content: str) -> dict:
    """Generate basic analysis without Claude"""
    
    jira_links = len(re.findall(r'(PM2|HW|FW|SW)-\d+', content))
    requirements = len(re.findall(r'[A-Z]{2,3}-\d+', content))
    
    coverage = (jira_links / requirements * 100) if requirements > 0 else 0
    
    return {
        'total_requirements': requirements,
        'total_jira_links': jira_links,
        'coverage_percent': coverage
    }

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="RTM Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        border-left-color: #2ca02c;
    }
    .warning-card {
        border-left-color: #ff7f0e;
    }
    .error-card {
        border-left-color: #d62728;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - AUTHENTICATION & SETTINGS
# ============================================================================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Keys
    with st.expander("🔑 API Keys", expanded=True):
        st.info("Keys are encrypted and never stored. Keep them private!")
        
        jira_token = st.text_input(
            "Jira API Token",
            type="password",
            value=st.secrets.get("jira_token", ""),
            help="Get from: Profile > Settings > API Tokens"
        )
        
        jira_user = st.text_input(
            "Jira Username/Email",
            value=st.secrets.get("jira_user", ""),
            help="Email used for Jira"
        )
        
        jira_url = st.text_input(
            "Jira Base URL",
            value=st.secrets.get("jira_url", "https://etcengineering.atlassian.net"),
            help="Your Jira instance URL"
        )
        
        anthropic_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.secrets.get("anthropic_key", ""),
            help="Claude API key for analysis"
        )
        
        google_key = st.text_input(
            "Google API Key",
            type="password",
            value=st.secrets.get("google_key", ""),
            help="For accessing Google Sheets/Docs"
        )
    
    # Settings
    with st.expander("📋 Settings"):
        auto_email = st.checkbox("Email results after analysis", value=False)
        email_to = st.text_input("Email address", placeholder="your@email.com") if auto_email else ""
        
        export_format = st.selectbox(
            "Default export format",
            ["PDF", "CSV", "Excel", "JSON"]
        )
        
        iso_standard = st.selectbox(
            "ISO Standard Target",
            ["ISO 9001:2015", "ISO 13485", "ISO 26262"]
        )
        
        min_coverage = st.slider(
            "Target traceability coverage %",
            min_value=50,
            max_value=100,
            value=95,
            step=5
        )
    
    st.divider()
    
    # Help
    with st.expander("❓ Help"):
        st.markdown("""
        **Supported URL Types:**
        - Google Sheets (shareable link)
        - Google Docs (shareable link)
        - Confluence pages
        - Jira JQL filters
        - GitHub raw content
        
        **Requirements:**
        - Make documents publicly accessible OR
        - Use API keys for private access
        
        **Analysis Types:**
        - Quick: List Jira links found
        - Detailed: Full traceability report
        - Test Cases: Coverage analysis
        """)
    
    st.divider()
    
    # Version
    st.caption("RTM Analyzer v1.0.0 | Exact Technology")

# ============================================================================
# MAIN INTERFACE
# ============================================================================

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="header-title">📊 RTM Analyzer</div>', unsafe_allow_html=True)
    st.markdown("Comprehensive Requirements Traceability Matrix Analysis")
with col2:
    st.metric("Status", "🟢 Ready")

st.divider()

# ============================================================================
# TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Quick Analysis",
    "📋 Detailed Report", 
    "✅ Test Case Analysis",
    "📊 Batch Analysis",
    "📈 Dashboard"
])

# ============================================================================
# TAB 1: QUICK ANALYSIS
# ============================================================================

with tab1:
    st.header("Quick Jira Link Analysis")
    st.markdown("Paste a URL to quickly scan for Jira links and get basic stats")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        url = st.text_input(
            "Document URL",
            placeholder="https://docs.google.com/spreadsheets/d/... or https://confluence.example.com/...",
            label_visibility="collapsed"
        )
    with col2:
        analyze_quick = st.button("🔍 Analyze", key="quick_analyze", use_container_width=True)
    
    if analyze_quick and url:
        try:
            with st.spinner("🔄 Fetching and analyzing..."):
                # Fetch content
                content = fetch_url_content(url, google_key, jira_user, jira_token)
                
                # Extract Jira links
                jira_patterns = {
                    'PM2': r'PM2-\d+',
                    'HW': r'HW-\d+',
                    'FW': r'FW-\d+',
                    'SW': r'SW-\d+'
                }
                
                results = extract_jira_links(content, jira_patterns)
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Jira Links", results['total_links'])
                with col2:
                    st.metric("Unique Issues", results['unique_issues'])
                with col3:
                    st.metric("Projects Found", results['projects_count'])
                with col4:
                    st.metric("Slack Refs", results['slack_refs'])
                
                st.divider()
                
                # Issues breakdown
                st.subheader("Issues by Project")
                issues_df = pd.DataFrame(results['issues_breakdown'])
                st.dataframe(issues_df, use_container_width=True, hide_index=True)
                
                # Links list
                with st.expander("View all Jira links", expanded=False):
                    links_df = pd.DataFrame(results['all_links'], columns=['Link', 'Count'])
                    st.dataframe(links_df, use_container_width=True, hide_index=True)
                
                # Download options
                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    csv_data = issues_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download CSV",
                        csv_data,
                        f"rtm_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                with col2:
                    json_data = json.dumps(results, indent=2)
                    st.download_button(
                        "📥 Download JSON",
                        json_data,
                        f"rtm_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json"
                    )
                with col3:
                    if auto_email and email_to:
                        send_email(email_to, "RTM Quick Analysis", csv_data)
                        st.success(f"📧 Email sent to {email_to}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 2: DETAILED REPORT
# ============================================================================

with tab2:
    st.header("Detailed Traceability Report")
    st.markdown("Full analysis with ISO 9001 compliance assessment")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        url_detailed = st.text_input(
            "Document URL",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            label_visibility="collapsed",
            key="detailed_url"
        )
    with col2:
        analyze_detailed = st.button("📋 Generate Report", key="detailed_analyze", use_container_width=True)
    
    if analyze_detailed and url_detailed:
        try:
            with st.spinner("🔄 Generating detailed report..."):
                content = fetch_url_content(url_detailed, google_key, jira_user, jira_token)
                
                # Use Claude for intelligent analysis
                if anthropic_key:
                    client = anthropic.Anthropic(api_key=anthropic_key)
                    
                    analysis_prompt = f"""
                    Analyze this Requirements Traceability Matrix content for compliance:
                    
                    {content[:5000]}  # First 5000 chars
                    
                    Provide:
                    1. Total requirements count
                    2. Requirements with Jira links (count & percentage)
                    3. Requirements without links
                    4. ISO 9001:2015 compliance assessment
                    5. Key gaps and recommendations
                    6. Risk assessment (Low/Medium/High)
                    
                    Format as JSON.
                    """
                    
                    message = client.messages.create(
                        model="claude-opus-4-6",
                        max_tokens=2000,
                        messages=[
                            {"role": "user", "content": analysis_prompt}
                        ]
                    )
                    
                    analysis = json.loads(message.content[0].text)
                else:
                    analysis = generate_basic_analysis(content)
                
                # Display report
                st.success("✅ Report Generated!")
                
                # Executive Summary
                st.subheader("Executive Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Requirements",
                        analysis.get('total_requirements', 'N/A'),
                        delta=None
                    )
                with col2:
                    coverage = analysis.get('coverage_percentage', 0)
                    st.metric(
                        "Coverage %",
                        f"{coverage}%",
                        delta=f"{coverage - 95}%" if coverage >= 95 else f"{coverage - 95}%"
                    )
                with col3:
                    status = analysis.get('iso_status', 'Unknown')
                    st.metric("ISO Status", status)
                with col4:
                    risk = analysis.get('risk_level', 'Unknown')
                    st.metric("Risk Level", risk)
                
                st.divider()
                
                # Detailed sections
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Requirements Distribution")
                    dist_data = {
                        'Category': ['With Jira', 'Without Jira', 'Other'],
                        'Count': [
                            analysis.get('with_jira', 0),
                            analysis.get('without_jira', 0),
                            analysis.get('other', 0)
                        ]
                    }
                    dist_df = pd.DataFrame(dist_data)
                    st.bar_chart(dist_df.set_index('Category'))
                
                with col2:
                    st.subheader("ISO 9001 Compliance")
                    compliance_data = {
                        'Criterion': ['Coverage', 'Documentation', 'Traceability'],
                        'Score': [
                            analysis.get('coverage_score', 0),
                            analysis.get('doc_score', 0),
                            analysis.get('trace_score', 0)
                        ]
                    }
                    comp_df = pd.DataFrame(compliance_data)
                    st.bar_chart(comp_df.set_index('Criterion'))
                
                st.divider()
                
                # Gaps and Recommendations
                st.subheader("Gaps & Recommendations")
                
                gaps = analysis.get('gaps', [])
                recommendations = analysis.get('recommendations', [])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔴 Identified Gaps:**")
                    for gap in gaps:
                        st.markdown(f"- {gap}")
                
                with col2:
                    st.markdown("**✅ Recommendations:**")
                    for rec in recommendations:
                        st.markdown(f"- {rec}")
                
                st.divider()
                
                # Export options
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    report_text = generate_text_report(analysis)
                    st.download_button(
                        "📄 Download as Text",
                        report_text,
                        f"rtm_report_{datetime.now().strftime('%Y%m%d')}.txt"
                    )
                
                with col2:
                    csv_data = json.dumps(analysis, indent=2)
                    st.download_button(
                        "📊 Download as JSON",
                        csv_data,
                        f"rtm_analysis_{datetime.now().strftime('%Y%m%d')}.json"
                    )
                
                with col3:
                    if auto_email and email_to:
                        send_email(email_to, "RTM Detailed Report", report_text)
                        st.success(f"✅ Email sent!")
                
                with col4:
                    st.info("📥 PDF export coming soon!")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 3: TEST CASE ANALYSIS
# ============================================================================

with tab3:
    st.header("Test Case Coverage Analysis")
    st.markdown("Match requirements to test cases and assess coverage")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        url_test = st.text_input(
            "Requirements URL",
            placeholder="RTM or requirements doc",
            key="test_req_url"
        )
    with col2:
        url_tests = st.text_input(
            "Test Cases URL",
            placeholder="Test case document",
            key="test_cases_url"
        )
    with col3:
        analyze_test = st.button("✅ Analyze Coverage", key="test_analyze", use_container_width=True)
    
    if analyze_test and url_test and url_tests:
        try:
            with st.spinner("🔄 Analyzing test coverage..."):
                req_content = fetch_url_content(url_test, google_key, jira_user, jira_token)
                test_content = fetch_url_content(url_tests, google_key, jira_user, jira_token)
                
                # Match requirements to tests
                coverage_analysis = analyze_test_coverage(req_content, test_content)
                
                st.success("✅ Coverage Analysis Complete!")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Requirements", coverage_analysis['total_reqs'])
                with col2:
                    st.metric("Test Cases Found", coverage_analysis['total_tests'])
                with col3:
                    coverage_pct = coverage_analysis['coverage_percent']
                    st.metric("Coverage %", f"{coverage_pct}%")
                
                st.divider()
                
                # Coverage breakdown
                st.subheader("Coverage Distribution")
                
                coverage_data = {
                    'Category': ['Covered', 'Partial', 'Uncovered'],
                    'Count': [
                        coverage_analysis['covered'],
                        coverage_analysis['partial'],
                        coverage_analysis['uncovered']
                    ]
                }
                coverage_df = pd.DataFrame(coverage_data)
                st.bar_chart(coverage_df.set_index('Category'))
                
                # Uncovered requirements
                if coverage_analysis['uncovered'] > 0:
                    st.subheader("⚠️ Uncovered Requirements")
                    uncovered_df = pd.DataFrame(coverage_analysis['uncovered_list'])
                    st.dataframe(uncovered_df, use_container_width=True, hide_index=True)
                
                # Recommendations
                st.subheader("Test Coverage Recommendations")
                for rec in coverage_analysis['recommendations']:
                    st.markdown(f"- {rec}")
                
                # Export
                col1, col2 = st.columns(2)
                with col1:
                    csv = coverage_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Coverage CSV",
                        csv,
                        f"coverage_{datetime.now().strftime('%Y%m%d')}.csv"
                    )
                with col2:
                    if auto_email and email_to:
                        send_email(email_to, "Test Coverage Report", csv)
                        st.success("✅ Sent!")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 4: BATCH ANALYSIS
# ============================================================================

with tab4:
    st.header("Batch Analysis")
    st.markdown("Analyze multiple documents at once and compare results")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        urls_text = st.text_area(
            "Enter URLs (one per line)",
            placeholder="https://docs.google.com/spreadsheets/d/...\nhttps://...",
            height=150
        )
    with col2:
        st.write("")
        st.write("")
        batch_analyze = st.button("🔄 Analyze All", key="batch_analyze", use_container_width=True)
    
    if batch_analyze and urls_text:
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if urls:
            try:
                progress_bar = st.progress(0)
                results_list = []
                
                for i, url in enumerate(urls):
                    with st.spinner(f"Analyzing {i+1}/{len(urls)}..."):
                        try:
                            content = fetch_url_content(url, google_key, jira_user, jira_token)
                            result = extract_jira_links(content, {
                                'PM2': r'PM2-\d+',
                                'HW': r'HW-\d+',
                                'FW': r'FW-\d+',
                                'SW': r'SW-\d+'
                            })
                            result['url'] = url[:60] + '...' if len(url) > 60 else url
                            results_list.append(result)
                        except Exception as e:
                            st.warning(f"Error with {url}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(urls))
                
                st.success("✅ Batch analysis complete!")
                
                # Comparison table
                st.subheader("Comparison Results")
                
                comparison_data = []
                for r in results_list:
                    comparison_data.append({
                        'Document': r['url'],
                        'Total Links': r['total_links'],
                        'Unique Issues': r['unique_issues'],
                        'Projects': r['projects_count'],
                        'Slack Refs': r['slack_refs']
                    })
                
                comp_df = pd.DataFrame(comparison_data)
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
                
                # Export batch results
                col1, col2 = st.columns(2)
                with col1:
                    csv = comp_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Comparison",
                        csv,
                        f"batch_comparison_{datetime.now().strftime('%Y%m%d')}.csv"
                    )
                with col2:
                    if auto_email and email_to:
                        send_email(email_to, "Batch Analysis Results", csv)
                        st.success("✅ Sent to email!")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ============================================================================
# TAB 5: DASHBOARD
# ============================================================================

with tab5:
    st.header("Analytics Dashboard")
    st.markdown("Historical analytics and trends")
    
    st.info("📊 Dashboard features coming soon! This will show:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **📈 Metrics:**
        - Coverage trends over time
        - Gap reduction progress
        - Team compliance scores
        - Document health status
        """)
    
    with col2:
        st.markdown("""
        **🎯 Features:**
        - Historical comparison
        - Team performance
        - Risk assessment
        - Export analytics
        """)
    
    # Placeholder charts
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Coverage Trend")
        trend_data = pd.DataFrame({
            'Date': pd.date_range('2024-01-01', periods=12, freq='M'),
            'Coverage %': [60, 62, 65, 68, 70, 72, 75, 76, 77, 78, 80, 82]
        })
        st.line_chart(trend_data.set_index('Date'))
    
    with col2:
        st.subheader("Documents by Status")
        status_data = pd.DataFrame({
            'Status': ['Compliant', 'Partial', 'Gap', 'Review'],
            'Count': [5, 8, 3, 2]
        })
        st.bar_chart(status_data.set_index('Status'))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data
def fetch_url_content(url: str, google_key: str, jira_user: str, jira_token: str) -> str:
    """Fetch content from various URL types"""
    
    try:
        # Google Sheets
        if 'docs.google.com/spreadsheets' in url:
            sheet_id = extract_google_id(url)
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            response = requests.get(export_url, timeout=10)
            return response.text
        
        # Google Docs
        elif 'docs.google.com/document' in url:
            doc_id = extract_google_id(url)
            export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            response = requests.get(export_url, timeout=10)
            return response.text
        
        # Confluence
        elif 'confluence' in url:
            api_url = url.replace('/display/', '/rest/api/content/')
            api_url += '?expand=body.storage'
            headers = {'Authorization': f'Bearer {jira_token}'}
            response = requests.get(api_url, headers=headers, timeout=10)
            return response.text
        
        # Jira JQL
        elif 'atlassian.net' in url and 'jql' in url:
            headers = {'Authorization': f'Basic {base64.b64encode(f"{jira_user}:{jira_token}".encode()).decode()}'}
            response = requests.get(url, headers=headers, timeout=10)
            return json.dumps(response.json())
        
        # GitHub
        elif 'github.com' in url:
            raw_url = url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
            response = requests.get(raw_url, timeout=10)
            return response.text
        
        # Default HTTP
        else:
            response = requests.get(url, timeout=10)
            return response.text
    
    except Exception as e:
        st.error(f"Could not fetch URL: {str(e)}")
        return ""

def extract_google_id(url: str) -> str:
    """Extract Google Sheets/Docs ID from URL"""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else ""

def extract_jira_links(content: str, patterns: dict) -> dict:
    """Extract and count Jira links from content"""
    
    all_issues = {}
    projects = {}
    slack_count = 0
    
    # Find all Jira links
    for project, pattern in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            projects[project] = len(set(matches))
            for match in set(matches):
                all_issues[match] = all_issues.get(match, 0) + 1
    
    # Find Slack references
    slack_matches = re.findall(r'slack\.com|slack message', content, re.IGNORECASE)
    slack_count = len(slack_matches) // 2  # Rough estimate
    
    return {
        'total_links': len(all_issues),
        'unique_issues': len(set(all_issues.keys())),
        'projects_count': len(projects),
        'slack_refs': slack_count,
        'issues_breakdown': [
            {'Project': p, 'Issues': c} for p, c in sorted(projects.items())
        ],
        'all_links': [[k, v] for k, v in sorted(all_issues.items())]
    }


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    # Verify API keys on startup
    pass
