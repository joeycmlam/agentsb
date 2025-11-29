# orchestrator/main.py
from crewai import Agent, Task, Crew, Process
from jira import JIRA
from github import Github
import os

# Initialize APIs
jira = JIRA('https://joeycmlam-1762529818344.atlassian.net/', auth=(os.getenv('JIRA_USER'), os.getenv('JIRA_TOKEN')))
github = Github(os.getenv('GITHUB_TOKEN'))

# Define CrewAI Agents (each uses GitHub Copilot CLI internally)
requirements_analyst = Agent(
    role="Requirements Analyst",
    goal="Analyze JIRA tickets and generate requirements",
    backstory="Senior BA with expertise in clarifying requirements",
    llm="claude-3.5-sonnet",  # Uses your Copilot license
)

architect = Agent(
    role="Solution Architect",
    goal="Design scalable solutions",
    backstory="Experienced system architect",
    llm="claude-3.5-sonnet",
)

backend_dev = Agent(
    role="Backend Developer",
    goal="Implement with TDD",
    backstory="Senior backend engineer",
    llm="claude-3.5-sonnet",
)

qa_engineer = Agent(
    role="QA Engineer",
    goal="Ensure test coverage",
    backstory="QA lead",
    llm="claude-3.5-sonnet",
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
        llm="claude-3.5-sonnet",
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