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