# Design Documents

This directory contains solution architecture and design documents for features and enhancements.

## Document Structure

Each design document should follow the template provided in the Solution Architect Agent and include:

1. **Overview** - Problem statement and solution approach
2. **System Architecture** - C4 diagrams showing system context, containers, and components
3. **Component Design** - Detailed component specifications
4. **Data Model** - ERD and database schema
5. **Implementation Notes** - Backend, frontend, database, and performance considerations
6. **Architecture Decisions** - Key decisions and trade-offs
7. **Risk Assessment** - Potential risks and mitigation strategies
8. **Implementation Plan** - Phased approach to implementation
9. **Testing Strategy** - Testing approach and coverage
10. **JIRA Comments Summary** - Key discussions and decisions from JIRA

## Naming Convention

Format: `TICKET-ID-design.md`

Examples:
- `SCRUM-123-design.md`
- `FEAT-456-design.md`
- `EPIC-789-design.md`

## Workflow

1. Solution Architect Agent reads JIRA ticket and comments
2. Creates design branch: `design/TICKET-ID` or `arch/TICKET-ID`
3. Generates design document with Mermaid diagrams
4. Saves diagram files to `doc/architecture/diagrams/`
5. Commits and pushes to branch
6. Posts architecture summary and diagrams to JIRA ticket
7. Creates implementation tasks

## Related Directories

- `doc/architecture/diagrams/` - Mermaid diagram source files
- `doc/architecture/` - High-level architecture documentation

## Review Process

Design documents should be reviewed by:
- Technical leads
- Development team members
- Product owners (for requirements alignment)
- DevOps/Infrastructure team (for deployment considerations)

## Tools

- **Mermaid** - For creating diagrams as code
- **JIRA** - For requirements and task tracking
- **GitHub** - For version control and review

## References

- [Solution Architect Agent Documentation](../../.github/agents/architect.agent.md)
- [C4 Model](https://c4model.com/)
- [Mermaid Diagrams](https://mermaid.js.org/)
