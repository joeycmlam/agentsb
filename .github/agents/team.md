# Agent Team Directory

This directory contains specialized agents organized into functional teams.

## 📋 Quick Navigation

- **[Testing Agents](README_TESTING.md)** ⭐ Comprehensive testing architecture (START HERE for testing)
- **Business Analysis Team** - Requirements, scenarios, validation
- **Development Team** - Frontend, backend, architecture
- **Documentation Team** - API docs, architecture docs, workflows
- **DevOps Team** - CI/CD, deployment, infrastructure

---

## 🧪 Testing Agents (Hierarchical Architecture)

**Main Entry Point:** [@test-lead](test-lead.agent.md) - Orchestrates all testing activities

**New Specialist:** [@e2e-test-engineer](e2e-test-engineer.agent.md) - Testability review & refactoring

**Quick Command:**
```
@test-lead: [Describe your testing need]
```

**Documentation:**
- [README_TESTING.md](README_TESTING.md) - Complete testing index
- [QUICK_START_TESTING.md](QUICK_START_TESTING.md) - Getting started guide
- [TESTING_ARCHITECTURE.md](TESTING_ARCHITECTURE.md) - Architecture reference
- [VISUAL_WORKFLOWS.md](VISUAL_WORKFLOWS.md) - Workflow diagrams

**Agent Roster:**
- [@test-lead](test-lead.agent.md) - Main orchestrator
- [@e2e-test-engineer](e2e-test-engineer.agent.md) - Testability & refactoring (NEW)
- [@testing-architect](testing-architect.agent.md) - Strategy advisor
- [@bdd-lead-engineer](bdd-lead-engineer.agent.md) - BDD implementation
- [@bdd-automation-engineer](bdd-automation-engineer.agent.md) - Step definitions
- [@e2e-test-generator](e2e-test-generator.agent.md) - Automated E2E
- [@test-review](test-review.agent.md) - Quality assurance

---

## 📊 Business Analysis Team

- [@ba-lead](ba-lead.agent.md) - Business requirements analysis
- [@ba-scenario](ba-scenario.agent.md) - Gherkin scenario creation
- [@ba-requirements-validator](ba-requirements-validator.agent.md) - Acceptance criteria validation
- [@ba-financial-domain-expert](ba-financial-domain-expert.agent.md) - Financial domain knowledge

---

## 💻 Development Team

### Architecture & Strategy
- [@engineering-lead](engineering-lead.agent.md) - Project orchestration, KISS/YAGNI enforcement
- [@architecture-advisor](architecture-advisor.agent.md) - SOLID principles, design patterns
- [@tech-stack-advisor](tech-stack-advisor.agent.md) - Technology selection

### Implementation
- [@frontend-dev](frontend-dev.agent.md) - React/Next.js development
- [@backend-dev](backend-dev.agent.md) - FastAPI/Python development
- [@dba](dba.agent.md) - Database design and optimization

### Quality & Security
- [@bug-investigator](bug-investigator.agent.md) - Debug and root cause analysis
- [@security-reporter](security-reporter.agent.md) - Security audit and reporting

---

## 📚 Documentation Team

- [@doc-architect](doc-architect.agent.md) - Documentation strategy
- [@doc-api-specialist](doc-api-specialist.agent.md) - API documentation
- [@doc-architecture-specialist](doc-architecture-specialist.agent.md) - Architecture docs
- [@doc-database-specialist](doc-database-specialist.agent.md) - Database documentation
- [@doc-workflow-specialist](doc-workflow-specialist.agent.md) - Workflow diagrams

---

## 🚀 DevOps Team

- [@cicd-pipeline-engineer](cicd-pipeline-engineer.agent.md) - CI/CD pipeline design
- [@lead-ai-engineer](lead-ai-engineer.agent.md) - AI/ML operations

---

## 🎯 How to Use This Directory

### For Testing Needs
**Always start with:**
```
@test-lead: [Your testing request]
```

Examples:
- `@test-lead: Test the new authentication feature`
- `@test-lead: Review PaymentService.py for testability`
- `@test-lead: Optimize test suite performance`

See [QUICK_START_TESTING.md](QUICK_START_TESTING.md) for more examples.

---

### For Development Needs
**Start with:**
```
@engineering-lead: [Your development request]
```

The engineering lead will coordinate architects and developers.

---

### For Documentation Needs
**Start with:**
```
@doc-architect: [Your documentation request]
```

The doc architect will delegate to specialists.

---

## 🆕 Recent Updates

**2026-02-22**: Testing agent architecture redesigned
- ✅ Created hierarchical testing agent structure (12 agents)
- ✅ Added @test-lead as main orchestrator
- ✅ Added @e2e-test-engineer for testability reviews
- ✅ Comprehensive documentation and guides
- ✅ Visual workflows and diagrams
- ✅ Removed 2 redundant agents (14 → 12 agents)
- ✅ Simplified structure with clear single responsibilities

**See:** [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md) for cleanup details

---

## 📞 Support

**Testing questions:** → [@test-lead](test-lead.agent.md)  
**Development questions:** → [@engineering-lead](engineering-lead.agent.md)  
**Documentation questions:** → [@doc-architect](doc-architect.agent.md)

---

**Note:** This is a living directory. Agents are continuously improved based on project needs.