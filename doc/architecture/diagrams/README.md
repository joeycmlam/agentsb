# Architecture Diagrams

This directory contains Mermaid diagram files for system architecture designs.

## Diagram Types

### C4 Diagrams
- **Context Diagrams** (`*-context.mmd`): Show system boundary and external dependencies
- **Container Diagrams** (`*-container.mmd`): Show high-level technical building blocks
- **Component Diagrams** (`*-component.mmd`): Show components within containers
- **Dynamic Diagrams** (`*-dynamic.mmd`): Show runtime behavior

### Sequence Diagrams
- Files ending with `-sequence.mmd`
- Show interaction between components over time

### Entity Relationship Diagrams (ERD)
- Files ending with `-erd.mmd`
- Show database schema and relationships

### Flowcharts
- Files ending with `-flow.mmd`
- Show business logic or process flows

### Class Diagrams
- Files ending with `-class.mmd`
- Show object-oriented design

## Naming Convention

Format: `TICKET-ID-diagram-type.mmd`

Examples:
- `SCRUM-123-context.mmd`
- `SCRUM-123-container.mmd`
- `SCRUM-123-sequence.mmd`
- `SCRUM-123-erd.mmd`

## Viewing Diagrams

### In VS Code
Install the Mermaid Preview extension:
```
code --install-extension bierner.markdown-mermaid
```

### Online
Paste diagram code into [Mermaid Live Editor](https://mermaid.live/)

### In Documentation
Embed in Markdown files:
````markdown
```mermaid
[diagram code here]
```
````

## References
- [Mermaid Documentation](https://mermaid.js.org/)
- [C4 Model](https://c4model.com/)
- [Mermaid C4 Diagrams](https://mermaid.js.org/syntax/c4.html)
