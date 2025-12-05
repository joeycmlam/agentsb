#!/bin/bash
# scripts/run-workflow.sh

JIRA_ID=$1

echo "🚀 Starting Development Workflow for $JIRA_ID"

# Stage 1: Requirements
echo "📋 Stage 1: Requirements Analysis"
gh copilot --agent=requirements-analyst \
  --prompt "Read JIRA ticket $JIRA_ID and generate requirements with Cucumber scenarios"

# Wait for manual review
read -p "Press Enter after requirements are approved..."

# Stage 2: Architecture
echo "🏗️  Stage 2: Solution Design"
gh copilot --agent=architect \
  --prompt "Design solution for $JIRA_ID based on requirements"

# Wait for manual review
read -p "Press Enter after design is approved..."

# Stage 3: Implementation (parallel)
echo "💻 Stage 3: Implementation"
gh copilot --agent=backend-dev \
  --prompt "Implement backend for $JIRA_ID with TDD"

gh copilot --agent=frontend-dev \
  --prompt "Implement frontend for $JIRA_ID with component testing"

# Stage 4: QA Review
echo "✅ Stage 4: QA Review"
gh copilot --agent=qa-engineer \
  --prompt "Review tests and generate test report for $JIRA_ID"

echo "🎉 Workflow Complete!"