# SecureAgent Architecture

SecureAgent is a backend-first AI runtime security platform that monitors, evaluates, and controls risky AI-agent behavior.

## High-Level Flow

1. User sends a task or prompt
2. Planner creates an execution plan
3. Executor evaluates:
   - prompt safety
   - tool permissions
   - output safety
4. A security event is logged
5. If risk exceeds threshold, an incident is created
6. WebSocket broadcasts live updates
7. Dashboard, incidents, and reports reflect the new state

## Main Components

### Frontend
- Login
- Dashboard
- Testing Lab
- Incidents
- Reports
- Policy Editor

### Backend
- FastAPI routes
- Auth handling
- Policy APIs
- Event APIs
- Incident APIs
- Report APIs
- Demo seed APIs

### Runtime Security Layer
- Prompt analysis
- Tool validation
- Output inspection
- Risk scoring
- Incident triggering

### Database
- SecurityEvent
- Incident
- PlatformUser

## Security Pipeline

### Prompt Stage
Checks for:
- prompt injection
- instruction override attempts
- system prompt extraction attempts

### Tool Stage
Checks:
- whether requested tool is allowed for current role
- whether tool usage is risky or restricted

### Output Stage
Checks:
- sensitive output leakage
- redaction requirements
- block conditions

## Live Update Flow

When an event is logged:
- event is stored in database
- WebSocket broadcasts `security_event`

When an incident is created:
- incident is stored in database
- WebSocket broadcasts `incident_created`

## Benefits of This Architecture

- easy to extend
- clear separation of concerns
- supports monitoring and prevention
- suitable for demos and future deployment