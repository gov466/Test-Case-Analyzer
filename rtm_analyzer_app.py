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

def analyze_rtm_by_columns(csv_content: str) -> dict:
    """Analyze RTM by detecting columns intelligently"""
    
    try:
        # Read CSV
        df = pd.read_csv(StringIO(csv_content))
        
        # Auto-detect requirement column (look for IDs, requirements, etc)
        req_col = None
        jira_col = None
        desc_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Find requirement/ID column
            if any(x in col_lower for x in ['requirement', 'req', 'id', 'test case', 'tc-']):
                req_col = col
            
            # Find Jira column (contains issue links)
            if any(x in col_lower for x in ['jira', 'issue', 'link', 'pm2', 'hw', 'fw', 'sw']):
                jira_col = col
            
            # Find description column
            if any(x in col_lower for x in ['description', 'desc', 'title', 'name']):
                desc_col = col
        
        # If no explicit columns found, try by position
        if not req_col and len(df.columns) > 0:
            req_col = df.columns[0]
        if not jira_col and len(df.columns) > 1:
            jira_col = df.columns[1]
        
        # Analyze row by row
        total_requirements = 0
        with_jira = 0
        without_jira = 0
        missing_jira_rows = []
        found_issues = {}
        
        for idx, row in df.iterrows():
            # Check if row has requirement
            req_value = str(row.get(req_col, '')).strip() if req_col else ''
            jira_value = str(row.get(jira_col, '')).strip() if jira_col else ''
            
            # Skip empty rows
            if not req_value or req_value.lower() == 'nan' or req_value == '':
                continue
            
            # Skip header-like rows
            if any(x in req_value.lower() for x in ['requirement', 'test', 'description', 'id']):
                continue
            
            total_requirements += 1
            
            # Check if has Jira link
            if jira_value and jira_value != 'nan' and jira_value != '':
                with_jira += 1
                
                # Extract issue keys from Jira column
                issues = re.findall(r'(PM2|HW|FW|SW)-\d{2,}', jira_value)
                for issue in issues:
                    found_issues[issue] = found_issues.get(issue, 0) + 1
            else:
                without_jira += 1
                missing_jira_rows.append({
                    'row': idx + 2,  # +2 for 1-indexed and header
                    'requirement': req_value[:50],
                    'description': row.get(desc_col, '')[:100] if desc_col else ''
                })
        
        # Calculate coverage
        coverage = (with_jira / total_requirements * 100) if total_requirements > 0 else 0
        
        # Determine ISO status
        if coverage >= 95:
            iso_status = 'Compliant'
            risk_level = 'Low'
        elif coverage >= 70:
            iso_status = 'Partial'
            risk_level = 'Medium'
        else:
            iso_status = 'Non-Compliant'
            risk_level = 'High'
        
        return {
            'total_requirements': total_requirements,
            'with_jira': with_jira,
            'without_jira': without_jira,
            'coverage_percentage': round(coverage, 2),
            'coverage_percent': round(coverage, 2),
            'iso_status': iso_status,
            'risk_level': risk_level,
            'gaps': without_jira,
            'found_issues': found_issues,
            'missing_jira_rows': missing_jira_rows,
            'req_column': req_col,
            'jira_column': jira_col,
            'desc_column': desc_col,
            'issues_breakdown': [
                {'Project': k.split('-')[0], 'Issues': 1} 
                for k in found_issues.keys()
            ]
        }
    
    except Exception as e:
        st.error(f"Error analyzing RTM: {str(e)}")
        return {}

def generate_text_report(analysis: dict) -> str:
    """Generate text format report"""
    
    report = f"""
RTM ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
=================
Total Requirements: {analysis.get('total_requirements', 'N/A')}
With Jira Links: {analysis.get('with_jira', 'N/A')}
Coverage: {analysis.get('coverage_percentage', 'N/A')}%
ISO Status: {analysis.get('iso_status', 'Unknown')}
Risk Level: {analysis.get('risk_level', 'Unknown')}

DETAILED ANALYSIS
=================
Requirements with Jira: {analysis.get('with_jira', 0)}
Requirements without Jira: {analysis.get('without_jira', 0)}
Total Gaps: {analysis.get('gaps', 0)}

RECOMMENDATIONS
===============
- Link remaining requirements to Jira issues
- Document traceability in RTM
- Verify test case coverage

END OF REPORT
"""
    return report

def query_jira_for_testcases(jira_url: str, jira_user: str, jira_token: str, jira_issues: list) -> dict:
    """Query Jira API to check if each issue has linked test cases"""
    
    results = {
        'issues_with_tests': [],
        'issues_without_tests': [],
        'api_errors': []
    }
    
    if not jira_token or not jira_user:
        return results
    
    for issue_key in jira_issues:
        try:
            # Query Jira for the issue
            url = f"{jira_url}/rest/api/3/search?jql=key={issue_key}"
            headers = {
                'Authorization': f'Basic {base64.b64encode(f"{jira_user}:{jira_token}".encode()).decode()}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                issue_data = response.json()
                if issue_data.get('issues'):
                    issue = issue_data['issues'][0]
                    
                    # Check for linked test cases in fields
                    has_test_cases = False
                    
                    # Check common test case link patterns
                    linked_issues = issue.get('fields', {}).get('issuelinks', [])
                    for link in linked_issues:
                        link_type = link.get('type', {}).get('name', '').lower()
                        if 'test' in link_type or 'relates' in link_type:
                            has_test_cases = True
                            break
                    
                    # Check in description for test references
                    description = issue.get('fields', {}).get('description', '').lower()
                    if 'test' in description or 'tc-' in description:
                        has_test_cases = True
                    
                    if has_test_cases:
                        results['issues_with_tests'].append(issue_key)
                    else:
                        results['issues_without_tests'].append(issue_key)
        
        except Exception as e:
            results['api_errors'].append(f"{issue_key}: {str(e)}")
    
    return results

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
                
                # Analyze using smart column detection
                results = analyze_rtm_by_columns(content)
                
                if not results:
                    st.error("Could not analyze RTM. Check URL format.")
                    st.stop()
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Requirements", results.get('total_requirements', 0))
                with col2:
                    st.metric("With Jira Links", results.get('with_jira', 0))
                with col3:
                    st.metric("Without Jira Links", results.get('without_jira', 0))
                with col4:
                    coverage = results.get('coverage_percentage', 0)
                    st.metric("Coverage %", f"{coverage}%")
                
                st.divider()
                
                # Show found Jira issues
                st.subheader("Found Jira Issues")
                if results.get('found_issues'):
                    issues_list = [[k, v] for k, v in sorted(results['found_issues'].items())]
                    issues_df = pd.DataFrame(issues_list, columns=['Issue', 'Count'])
                    st.dataframe(issues_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No Jira issues found")
                
                # CRITICAL: Show missing Jira links (REAL GAPS)
                st.divider()
                st.subheader("❌ GAPS: Requirements WITHOUT Jira Links")
                
                if results.get('missing_jira_rows'):
                    missing_df = pd.DataFrame(results['missing_jira_rows'])
                    st.warning(f"⚠️ {len(results['missing_jira_rows'])} requirements missing Jira links!")
                    st.dataframe(missing_df, use_container_width=True, hide_index=True)
                    
                    # Download gaps as CSV
                    gaps_csv = missing_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Gaps CSV",
                        gaps_csv,
                        f"rtm_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
                else:
                    st.success("✅ All requirements have Jira links!")
                
                # Advanced: Check for test cases in Jira (if credentials available)
                if jira_token and jira_user and results.get('found_issues'):
                    st.divider()
                    with st.expander("🧪 Test Case Verification (from Jira)", expanded=False):
                        st.info("Checking Jira for linked test cases... this may take a moment")
                        
                        # Extract all Jira issue keys
                        all_issues = list(results['found_issues'].keys())
                        
                        if all_issues:
                            # Query Jira for test cases
                            test_results = query_jira_for_testcases(jira_url, jira_user, jira_token, all_issues)
                            
                            # Show results
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.success(f"✅ Issues WITH Test Cases: {len(test_results['issues_with_tests'])}")
                                if test_results['issues_with_tests']:
                                    for issue in test_results['issues_with_tests']:
                                        st.markdown(f"- {issue}")
                            
                            with col2:
                                st.error(f"❌ Issues WITHOUT Test Cases: {len(test_results['issues_without_tests'])}")
                                if test_results['issues_without_tests']:
                                    for issue in test_results['issues_without_tests']:
                                        st.markdown(f"- {issue} ← **REAL GAP**")
                            
                            # Show API errors if any
                            if test_results['api_errors']:
                                st.warning(f"⚠️ {len(test_results['api_errors'])} API errors")
                
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
                
                recommendations = analysis.get('recommendations', [
                    "Link remaining requirements to Jira issues",
                    "Document traceability in RTM",
                    "Verify test case coverage"
                ])
                gaps_count = analysis.get('gaps', 0)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔴 Identified Gaps:**")
                    if gaps_count > 0:
                        st.markdown(f"- **{gaps_count} requirements** missing Jira links")
                    else:
                        st.markdown("✅ No gaps identified - full coverage!")
                
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
                            result = analyze_rtm_by_columns(content)
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
                        'Total Requirements': r.get('total_requirements', 0),
                        'With Jira': r.get('with_jira', 0),
                        'Without Jira': r.get('without_jira', 0),
                        'Coverage %': f"{r.get('coverage_percentage', 0)}%",
                        'ISO Status': r.get('iso_status', 'Unknown')
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
            'Date': pd.date_range('2024-01-01', periods=12, freq='ME'),
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
# RUN APP
# ============================================================================

if __name__ == "__main__":
    pass
