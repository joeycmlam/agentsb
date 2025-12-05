#!/usr/bin/env python3
"""Test JIRA connection and list available projects"""

import os
from jira import JIRA

# Get credentials from environment
jira_url = os.getenv('JIRA_URL', 'https://joeycmlam-1762529818344.atlassian.net')
jira_user = os.getenv('JIRA_USER')
jira_token = os.getenv('JIRA_API_TOKEN')

print(f"Testing connection to: {jira_url}")
print(f"User: {jira_user}")
print("-" * 60)

try:
    # Connect to JIRA
    jira = JIRA(server=jira_url, basic_auth=(jira_user, jira_token))
    print("✅ Successfully connected to JIRA!")
    print()
    
    # List available projects
    projects = jira.projects()
    print(f"📁 Available Projects ({len(projects)}):")
    print()
    
    for project in projects:
        print(f"  - {project.key}: {project.name}")
        
        # Get issue count for each project
        try:
            issue_count = jira.search_issues(f'project={project.key}', maxResults=0).total
            print(f"    Issues: {issue_count}")
        except:
            pass
    
    print()
    print("🎯 Ready to analyze! Use any project key above.")
    print("Example: python3 src/jira_analyst.py <PROJECT_KEY>")
    
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
    print()
    print("Please check:")
    print("1. JIRA_URL is correct")
    print("2. JIRA_USER (email) is correct")
    print("3. JIRA_API_TOKEN is valid")
    print()
    print("Set them with:")
    print('  export JIRA_USER="your@email.com"')
    print('  export JIRA_API_TOKEN="your_token"')
