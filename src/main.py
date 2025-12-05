# orchestrator/main.py
from crewai import Agent, Task, Crew, Process, LLM
from jira import JIRA
from github import Github, Auth
import os

# Initialize APIs
jira_user = os.getenv('JIRA_USER')
jira_token = os.getenv('JIRA_API_TOKEN')

# For Atlassian Cloud, use basic_auth instead of auth
jira = JIRA(
    server='https://joeycmlam-1762529818344.atlassian.net',
    basic_auth=(jira_user, jira_token)
) if jira_user and jira_token else None

github_token = os.getenv('GITHUB_TOKEN')
if github_token:
    auth = Auth.Token(github_token)
    github = Github(auth=auth)
else:
    github = None

# Check for required API key
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required. Please set it before running.")

# Configure Claude LLM
llm = LLM(
    model="claude-3-5-sonnet-20241022",
    provider="anthropic"
)

# Define CrewAI Agents (each uses Claude via Anthropic)
requirements_analyst = Agent(
    role="Requirements Analyst",
    goal="Analyze JIRA tickets and generate requirements",
    backstory="Senior BA with expertise in clarifying requirements",
    llm=llm,
)

architect = Agent(
    role="Solution Architect",
    goal="Design scalable solutions",
    backstory="Experienced system architect",
    llm=llm,
)

backend_dev = Agent(
    role="Backend Developer",
    goal="Implement with TDD",
    backstory="Senior backend engineer",
    llm=llm,
)

qa_engineer = Agent(
    role="QA Engineer",
    goal="Ensure test coverage",
    backstory="QA lead",
    llm=llm,
)

# Define Tasks
analyze_req = Task(
    description="Read JIRA and generate requirements",
    agent=requirements_analyst,
    expected_output="Cucumber scenarios and assumptions",
)

design = Task(
    description="Create system design",
    agent=architect,
    expected_output="Design document with diagrams",
)

implement = Task(
    description="Implement with TDD",
    agent=backend_dev,
    expected_output="Code with >80% coverage",
)

qa_review = Task(
    description="Review and enhance tests",
    agent=qa_engineer,
    expected_output="Test report with approval",
)

# Orchestrate
crew = Crew(
    agents=[requirements_analyst, architect, backend_dev, qa_engineer],
    tasks=[analyze_req, design, implement, qa_review],
    process=Process.sequential,  # Or hierarchical
    manager_agent=Agent(
        role="Workflow Manager",
        goal="Coordinate development workflow",
        backstory="Experienced workflow manager",
        llm=llm,
    ),
)

def run_workflow(jira_ticket_id):
    result = crew.kickoff(
        inputs={"jira_ticket": jira_ticket_id}
    )
    return result

if __name__ == "__main__":
    import sys
    ticket = sys.argv[1]
    run_workflow(ticket)