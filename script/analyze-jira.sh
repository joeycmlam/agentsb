#!/bin/bash
# JIRA Project Analysis Script
# Usage: ./script/analyze-jira.sh <PROJECT_KEY> [output_file]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 JIRA Project Analyzer${NC}"
echo "================================"

# Check if project key is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Project key required${NC}"
    echo "Usage: $0 <PROJECT_KEY> [output_file]"
    echo "Example: $0 PROJ analysis-report.md"
    exit 1
fi

PROJECT_KEY=$1
OUTPUT_FILE=${2:-"jira-analysis-${PROJECT_KEY}-$(date +%Y%m%d).md"}

# Check for required environment variables
if [ -z "$JIRA_USER" ] || [ -z "$JIRA_API_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Warning: JIRA credentials not found in environment${NC}"
    echo "Please set JIRA_USER and JIRA_API_TOKEN environment variables"
    echo ""
    echo "Example:"
    echo "  export JIRA_USER='your@email.com'"
    echo "  export JIRA_API_TOKEN='your_api_token'"
    exit 1
fi

echo -e "Project: ${GREEN}${PROJECT_KEY}${NC}"
echo -e "Output: ${GREEN}${OUTPUT_FILE}${NC}"
echo ""

# Check if Python script exists
if [ ! -f "src/jira_analyst.py" ]; then
    echo -e "${RED}Error: src/jira_analyst.py not found${NC}"
    exit 1
fi

# Check if jira package is installed
python3 -c "import jira" 2>/dev/null || {
    echo -e "${YELLOW}Installing required Python package: jira${NC}"
    pip3 install jira
}

# Run the analysis
echo -e "${GREEN}Running analysis...${NC}"
echo ""

python3 src/jira_analyst.py "$PROJECT_KEY" "$OUTPUT_FILE"

# Check if analysis was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Analysis complete!${NC}"
    echo -e "Report saved to: ${GREEN}${OUTPUT_FILE}${NC}"
    
    # Optionally open the report
    if command -v open &> /dev/null; then
        read -p "Open report? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open "$OUTPUT_FILE"
        fi
    fi
else
    echo -e "${RED}❌ Analysis failed${NC}"
    exit 1
fi
