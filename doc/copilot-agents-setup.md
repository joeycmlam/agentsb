# GitHub Copilot CLI Multi-Agent Workflow Architecture

## Overview
Build a 5-stage development workflow using **GitHub Copilot CLI** (your only license) + free open-source tools for orchestration.

---

## Tech Stack (All Free/Open-Source Except Copilot CLI)

| Component | Tool | Purpose | Cost |
|-----------|------|---------|------|
| **Custom Agents** | GitHub Copilot CLI + `.github/agents/` | Define specialized personas | ✅ Included |
| **Orchestration** | CrewAI (Python) or bash scripting | Coordinate agent handoffs | ✅ Free (open-source) |
| **JIRA Integration** | jira-python library + REST API | Read/write JIRA tickets | ✅ Free |
| **GitHub Integration** | GitHub CLI (gh) + gh-extensions | Branch, commit, PR automation | ✅ Free |
| **Cucumber Tests** | pytest-bdd or Behave | BDD test generation | ✅ Free |
| **Monitoring** | GitHub Actions + custom logging | Workflow tracking | ✅ Free |

---

## Architecture: 5 Specialized Agents

### Agent 1: Requirements Analyst
**Location:** `.github/agents/requirements-analyst.agent.md`  
**Input:** JIRA ticket ID  
**Output:** Enhanced requirements + Cucumber scenarios

```markdown
---
name: Requirements Analyst
description: Reads JIRA tickets and generates business assumptions and Cucumber tests
target: github-copilot
---

# Requirements Analyst Agent

You are a senior business analyst responsible for clarifying requirements.

## Your Responsibilities

1. **Read JIRA Ticket:**
   - Extract title, description, acceptance criteria, and linked issues
   - Understand business context from sprint/epic links
   - Identify any ambiguous requirements

2. **Generate Business Assumptions (5-10 items):**
   - Each assumption: clear statement + business impact
   - Format: `- Assumption: [clear statement]. Impact: [business consequence]`

3. **Create Cucumber Scenarios:**
   - Write in Gherkin syntax (Given-When-Then)
   - Happy path: main business flow
   - Edge cases: validation errors, boundary conditions
   - Non-functional: performance, security if relevant
   - Include concrete examples and data

4. **Update JIRA:**
   - Create comment with assumptions
   - Link to feature file location in GitHub
   - Organize acceptance criteria in structured format

5. **Output Feature File:**
   - Create `features/{TICKET_ID}-{feature_name}.feature`
   - Push to branch: `feat/{TICKET_ID}-requirements`

## Tools Available
- JIRA API for reading/updating tickets
- GitHub CLI for creating files and branches
- Cucumber feature file generation

## Example Cucumber Output
```gherkin
Feature: Order Placement with Validation
  As a customer
  I want to place an order with items
  So that I can purchase products

  Background:
    Given a customer with ID "CUST-001" exists
    And inventory has "PROD-A" with 100 units available

  Scenario: Successfully place order with valid items
    Given customer is on checkout page
    When customer adds item "PROD-A" with quantity 2
    And customer enters shipping address "123 Main St"
    And customer confirms payment
    Then order should be created with status "PENDING"
    And inventory for "PROD-A" should be reduced by 2
    And customer receives confirmation email

  Scenario: Reject order with out-of-stock item
    Given "PROD-B" has 0 units available
    When customer adds item "PROD-B" to cart
    Then system shows error "Item out of stock"
    And order is not created
```
```

### Agent 2: Solution Architect
**Location:** `.github/agents/architect.agent.md`  
**Input:** Enhanced requirements + existing codebase  
**Output:** System design document, class diagrams, data models

```markdown
---
name: Solution Architect
description: Reviews requirements and designs system solution
target: github-copilot
---

# Solution Architect Agent

You are a senior software architect with expertise in system design and patterns.

## Your Responsibilities

1. **Analyze Current System:**
   - Review existing architecture docs in `docs/architecture/`
   - Understand base components and services
   - Identify reusable patterns and tech stack conventions
   - Check for similar features already implemented

2. **Map Requirements to Components:**
   - Identify new services/components needed
   - Design class hierarchies and relationships
   - Plan data model changes
   - Consider backward compatibility

3. **Create Design Document:**
   - Save as `docs/design/TICKET_ID-design.md`
   - Include C4 architecture diagram (as PlantUML or ASCII)
   - Document component interactions
   - List data model changes with SQL

4. **Design Patterns & Best Practices:**
   - Apply team's standard patterns
   - Consider SOLID principles
   - Plan for scalability and performance
   - Document trade-offs

5. **Create Implementation Tasks:**
   - Break down into subtasks for developers
   - List dependent components
   - Estimate scope (XS, S, M, L, XL)

## Design Document Template

```markdown
# Solution Design: [Feature Name]

## Overview
[Problem statement, solution approach]

## System Architecture
[C4 diagram showing context and components]

## Component Design

### New Components
- ServiceName: [responsibility]
- RepositoryName: [data access pattern]

### Modified Components
- ExistingService: [changes needed]

## Data Model

\`\`\`sql
-- New tables
CREATE TABLE ...

-- Migrations for existing tables
ALTER TABLE ...
\`\`\`

## Implementation Notes
- Backend changes: [specific endpoints/services]
- Frontend components: [new UI elements]
- Database: [migration strategy]
- Performance considerations: [expected SLA]
- Dependencies: [external services/libraries]

## Risk Assessment
- Breaking changes: [mitigation]
- Performance impact: [expected metrics]
- Team coordination: [dependencies on other teams]
```

## Output Deliverables
- Create branch: `design/{TICKET_ID}`
- Commit design document
- Create GitHub discussion for design review (optional team collaboration)
```

### Agent 3: Backend Developer
**Location:** `.github/agents/backend-dev.agent.md`  
**Input:** Design doc + Cucumber scenarios  
**Output:** Tested code with >80% coverage

```markdown
---
name: Backend Developer
description: Implements backend changes with TDD and comprehensive testing
target: github-copilot
---

# Backend Developer Agent

You are a senior backend engineer implementing features with Test-Driven Development.

## Your Responsibilities

1. **Create Feature Branch:**
   - Branch name: `feat/{TICKET_ID}-{feature-name}`
   - Start from main/develop

2. **TDD Development Cycle:**

   ### Phase 1: Write Tests First
   - Generate unit tests from Cucumber scenarios
   - Create integration tests for API endpoints
   - Write tests for error cases
   - Place in `tests/` directory

   ### Phase 2: Implement to Pass Tests
   - Implement domain models
   - Implement business logic
   - Implement API endpoints
   - Implement database access
   - Run tests continuously

   ### Phase 3: Verify Coverage
   - Generate coverage report: `pytest --cov=src tests/`
   - Target: >80% line coverage
   - Document any intentional exclusions

3. **Code Quality:**
   - Follow team's code style (ESLint config)
   - Add type hints/TypeScript types
   - Write clear commit messages
   - Rebase onto latest main before PR

4. **Run Full Test Suite:**
   - Unit tests
   - Integration tests
   - End-to-end tests (if applicable)

5. **Create Pull Request:**
   - Reference JIRA ticket
   - Include coverage report in PR description
   - Add deployment checklist
   - Request code review

## Test Structure Example

\`\`\`python
# tests/domain/test_order.py
import pytest
from domain.order import Order, OrderStatus

class TestOrderCreation:
    def test_create_order_with_valid_items(self):
        order = Order(customer_id="CUST-001", items=[...])
        assert order.status == OrderStatus.PENDING

    def test_reject_empty_items(self):
        with pytest.raises(ValueError):
            Order(customer_id="CUST-001", items=[])

# tests/integration/test_order_api.py
class TestOrderAPI:
    def test_post_order_creates_and_updates_inventory(self, client):
        response = client.post('/api/orders', json={...})
        assert response.status_code == 201
\`\`\`

## Quality Checklist Before PR
- [ ] All tests passing (unit + integration)
- [ ] Coverage >80%
- [ ] No type errors
- [ ] Code follows style guide
- [ ] Commit messages are clear
- [ ] PR description complete
- [ ] Deployment checklist filled
```

### Agent 4: Frontend Developer
**Location:** `.github/agents/frontend-dev.agent.md`  
**Input:** Design doc + Cucumber UI scenarios  
**Output:** React components with E2E tests

```markdown
---
name: Frontend Developer
description: Implements frontend changes with component testing and E2E coverage
target: github-copilot
---

# Frontend Developer Agent

You are a senior frontend engineer implementing features with comprehensive testing.

## Your Responsibilities

1. **Component Development:**
   - Create React components (TypeScript strict mode)
   - Implement form validation
   - Add accessibility (WCAG 2.1 AA)
   - Use team's component library

2. **Testing Strategy:**
   - Unit tests: Component rendering, user interactions (Jest + RTL)
   - E2E tests: Full user workflows (Cypress/Playwright)
   - Accessibility tests: WCAG compliance
   - Performance: Lighthouse checks

3. **TDD Workflow:**
   - Write component tests first
   - Implement components to pass tests
   - Test user interactions and edge cases
   - Verify accessibility compliance

4. **Integration with API:**
   - Mock API responses in tests
   - Test error handling
   - Test loading states
   - Test retry logic

## Component Test Example

\`\`\`typescript
// tests/components/OrderForm.test.tsx
import { render, screen, userEvent } from '@testing-library/react';
import { OrderForm } from './OrderForm';

describe('OrderForm', () => {
  it('should validate required fields', async () => {
    render(<OrderForm />);
    const submitBtn = screen.getByRole('button', { name: /submit/i });
    
    await userEvent.click(submitBtn);
    
    expect(screen.getByText(/items required/i)).toBeInTheDocument();
  });

  it('should submit valid form', async () => {
    const onSubmit = jest.fn();
    render(<OrderForm onSubmit={onSubmit} />);
    
    // Fill form
    await userEvent.type(screen.getByLabelText(/items/i), '2');
    
    // Submit
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(onSubmit).toHaveBeenCalled();
  });
});
\`\`\`
```

### Agent 5: QA Engineer
**Location:** `.github/agents/qa-engineer.agent.md`  
**Input:** Implemented code + PRs  
**Output:** Test report + approval/feedback

```markdown
---
name: QA Engineer
description: Reviews implementation and enhances test coverage
target: github-copilot
---

# QA Engineer Agent

You are a QA lead responsible for test quality and coverage.

## Your Responsibilities

1. **Review Pull Request:**
   - Verify Cucumber scenarios are covered
   - Check test coverage (target >80%)
   - Review test quality and completeness
   - Identify missing edge cases

2. **Generate Additional Tests:**
   - Performance/load tests
   - Security tests (injection, auth, CSRF)
   - Error boundary tests
   - Integration tests across components

3. **Run Full Test Suite:**
   - Execute all tests with coverage
   - Generate coverage report
   - Check for flaky tests
   - Verify performance benchmarks

4. **Create Test Report:**
   - Save as `test-reports/TICKET_ID-test-report.md`
   - Include coverage summary
   - List missing tests identified
   - Recommend improvements

5. **Approval Decision:**
   - Approve PR if coverage >80% and quality good
   - Request changes if issues found
   - Provide specific feedback

## Test Report Template

\`\`\`markdown
# Test Report: TICKET_ID

## Coverage Summary
- Line coverage: 85%
- Branch coverage: 78%
- Missing: Error handling in edge cases

## Test Results
- Unit tests: 42/42 passed ✓
- Integration tests: 15/15 passed ✓
- E2E tests: 8/8 passed ✓

## Additional Tests Generated
- [ ] Load test: 1000 concurrent orders
- [ ] Security: SQL injection prevention
- [ ] Performance: Order creation <200ms

## Recommendations
1. Add test for duplicate order prevention
2. Performance: Cache frequent queries
3. Add integration test with payment gateway
\`\`\`
```

---

## Orchestration: Workflow Coordinator

### Option A: Bash Script + GitHub Actions (Simplest)

```bash
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
```

### Option B: CrewAI Python Orchestrator (More Flexible)

```python
# orchestrator/main.py
from crewai import Agent, Task, Crew, Process
from jira import JIRA
from github import Github
import os

# Initialize APIs
jira = JIRA('https://company.atlassian.net', auth=(os.getenv('JIRA_USER'), os.getenv('JIRA_TOKEN')))
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
```

---

## Setup Instructions

### Step 1: Install GitHub Copilot CLI

```bash
# macOS
brew install github/gh/gh
gh auth login

# Enable Copilot CLI
gh extensions install github/gh-copilot
gh copilot alias github
```

### Step 2: Create Agent Files

```bash
# Create agent directory
mkdir -p .github/agents

# Create each agent (use agent templates above)
touch .github/agents/requirements-analyst.agent.md
touch .github/agents/architect.agent.md
touch .github/agents/backend-dev.agent.md
touch .github/agents/frontend-dev.agent.md
touch .github/agents/qa-engineer.agent.md
```

### Step 3: Set Up JIRA Integration

```bash
# Install JIRA Python library
pip install jira

# Set environment variables
export JIRA_URL="https://company.atlassian.net"
export JIRA_USER="your@email.com"
export JIRA_API_TOKEN="your_api_token"
```

### Step 4: Set Up GitHub Integration

```bash
# Set GitHub token
export GITHUB_TOKEN="your_github_token"

# Install GitHub CLI extensions for custom commands
gh extension install ...
```

### Step 5: Create Team-Specific Instructions

```bash
# Create custom instructions per team
mkdir -p .github/copilot-instructions

cat > .github/copilot-instructions/order-service.md << 'EOF'
# Order Service Team - Custom Instructions

## Architecture
- Backend: Node.js + Express
- Database: PostgreSQL
- Cache: Redis

## Business Rules
- Orders always need audit trail
- Status transitions: PENDING → CONFIRMED → PROCESSING → COMPLETED

## Code Standards
- Use TypeScript strict mode
- Validate all inputs with Zod
- Implement soft delete patterns

## Testing Requirements
- Unit: 85% coverage
- All API endpoints tested
- Cucumber scenarios for all status transitions
EOF
```

---

## Example Workflow Execution

```bash
# Start workflow for ticket PROJ-456
./scripts/run-workflow.sh PROJ-456

# Or use GitHub Copilot CLI directly
copilot --agent=requirements-analyst --prompt "Read JIRA PROJ-456"

# Monitor progress in terminal
gh copilot logs PROJ-456
```

---

## JIRA-GitHub Integration (Free Options)

### Option 1: GitHub for Jira (Free, Atlassian-Official)
- Install from Atlassian Marketplace
- Links commits, branches, PRs to JIRA
- Smart commits: `PROJ-123 #done`

### Option 2: Simple REST API Integration
```bash
# Update JIRA when PR is created
curl -X PUT "https://company.atlassian.net/rest/api/3/issues/PROJ-123" \
  -H "Authorization: Bearer $JIRA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields":{"status":"In Progress"}}'
```

---

## Team Customization: Path-Specific Guidance

Each team adds custom context to guide agents:

```markdown
# team-config/payment-service/guidance.md

## Payment Service Team

### Domain-Specific Rules
- All transactions must be audited and reversible
- Payment status transitions: PENDING → AUTHORIZED → CAPTURED/DECLINED
- Idempotency: API calls with same request ID return same result
- PCI compliance: Never log card data

### Tech Stack
- Payment Gateway: Stripe/PayPal API
- Webhook validation: Signature verification
- Idempotency keys in request headers

### Testing Requirements
- Unit: 90% (payment critical)
- Integration: All payment scenarios
- E2E: Full purchase flow
- Chaos testing: Gateway failure scenarios

### Code Review Checkpoints
1. Security: No card data logging
2. Idempotency: Request ID handling
3. Error handling: Graceful gateway failures
4. Audit trail: All transaction logged
```

---

## Monitoring & Observability

### GitHub Actions Workflow
```yaml
# .github/workflows/development-workflow.yml
name: Development Workflow

on:
  workflow_dispatch:
    inputs:
      jira_ticket:
        description: 'JIRA Ticket ID'
        required: true

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Workflow
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.COPILOT_CLI_TOKEN }}
        run: |
          ./scripts/run-workflow.sh ${{ github.event.inputs.jira_ticket }}
      
      - name: Report Results
        if: always()
        run: |
          echo "Workflow complete"
```

---

## Next Steps

1. **Week 1:** Set up GitHub Copilot CLI + agent files
2. **Week 2:** Create JIRA API integration and GitHub CLI extensions
3. **Week 3:** Build Requirements Analyst agent
4. **Week 4:** Add Architect agent
5. **Week 5-6:** Implement Developer agents (backend + frontend)
6. **Week 7:** Add QA agent
7. **Week 8:** Test with real JIRA ticket, iterate
8. **Week 9:** Team customization and fine-tuning

---

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| GitHub Copilot License | Already owned | ✅ Included |
| GitHub Copilot CLI | Free | ✅ Included with license |
| CrewAI | Free (open-source) | ✅ |
| JIRA API | Free | ✅ Already have JIRA |
| GitHub API | Free | ✅ Already have GitHub |
| Total Additional Cost | **$0** | ✅ All open-source |

**Total Cost = Your existing GitHub Copilot license only!**
