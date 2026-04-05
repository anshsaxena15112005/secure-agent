# SecureAgent

**SecureAgent** is a backend-first AI runtime security platform designed to monitor, analyze, and control risky AI-agent behavior in real time.

It is built as a security layer for agentic systems and AI-powered platforms. Instead of acting like a chatbot, SecureAgent works like a **runtime security and governance engine** that can detect unsafe prompts, block malicious tool usage, redact unsafe outputs, generate incidents, and provide live security visibility through a dashboard.

---

## Overview

Modern AI agents can interact with tools, system prompts, APIs, internal data, and external environments. This creates security risks such as:

- Prompt injection
- Secret exfiltration
- Unsafe tool execution
- Policy bypass attempts
- Sensitive output leakage
- Unauthorized role escalation

SecureAgent helps reduce these risks by enforcing runtime security checks across the full execution pipeline.

---

## Core Features

### Runtime Security Enforcement
- Prompt inspection before execution
- Tool usage validation based on role
- Output inspection and redaction
- Risk scoring and severity classification

### Incident Management
- Automatic incident creation for risky events
- Open / acknowledged / resolved incident lifecycle
- Incident review through dedicated incident center

### Live Dashboard
- Security event statistics
- Blocked vs allowed event visibility
- High-risk alert tracking
- Live alert feed via WebSocket updates

### Testing Lab
- Manual agent test execution
- Prebuilt malicious and benign scenarios
- Automated red-team simulation suite
- Recent test history view

### Policy Editor
- YAML-based policy editing
- Policy reload and reset support
- Policy version history and restore
- Admin-only access controls

### Reports and Exports
- Security summary reporting
- Breakdown by severity, role, and application
- JSON and CSV export for events and incidents

### Demo Mode
- One-click demo data seeding
- One-click demo data clearing
- Useful for interviews, presentations, and project demos

---

## Architecture

SecureAgent follows a backend-first architecture:

```text
Frontend Pages
 ├── Dashboard
 ├── Testing Lab
 ├── Incidents
 ├── Reports
 └── Policy Editor

FastAPI Backend
 ├── Auth APIs
 ├── Agent Execution APIs
 ├── Events APIs
 ├── Incidents APIs
 ├── Reports APIs
 ├── Policy APIs
 ├── Demo Seeder APIs
 └── WebSocket Alerts

Runtime Security Layer
 ├── Prompt Analysis
 ├── Tool Validation
 ├── Output Inspection
 └── Policy-Based Risk Decisions

Database (SQLite + SQLAlchemy)
 ├── SecurityEvent
 ├── Incident
 └── PlatformUser
```

---

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

### Frontend
- HTML
- CSS
- Vanilla JavaScript

### Security / Platform Logic
- Policy-based YAML configuration
- Role-based access control
- WebSocket live event broadcasting

---

## Project Structure

```
secureagent/
│
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── planner.py
│   │   │   └── executor.py
│   │   ├── db.py
│   │   ├── security.py
│   │   ├── policy_loader.py
│   │   └── ws_manager.py
│   │
│   └── security/
│       └── auth.py
│
├── main.py
├── login.html
├── dashboard.html
├── testing.html
├── incidents.html
├── reports.html
├── policy_editor.html
└── README.md
```

---

## Security Workflow

When a user submits a task:

1. The task is sent to the planner
2. The executor evaluates the prompt
3. Tool permissions are checked against the user role
4. Output is inspected for unsafe leakage
5. A risk score and severity are assigned
6. A SecurityEvent is logged
7. An Incident is created if the risk is above threshold
8. Dashboard and alert feeds update in real time

---

## Main Modules

### `planner.py`
Builds the execution plan for a goal or task.

### `executor.py`
Runs the plan through the security pipeline and logs events/incidents.

### `security.py`
Contains prompt analysis, tool evaluation, and output inspection logic.

### `policy_loader.py`
Loads, updates, resets, reloads, and restores YAML security policy data.

### `db.py`
Defines database models:
- SecurityEvent
- Incident
- PlatformUser

### `ws_manager.py`
Handles real-time WebSocket broadcasting for new events and incidents.

### `main.py`
Exposes all backend routes:
- auth
- dashboard data
- testing APIs
- incidents
- reports
- policy management
- demo seed/clear

---

## Database Models

### SecurityEvent
Stores runtime security activity such as:
- prompt blocks
- tool blocks
- output redaction
- successful safe execution

### Incident
Stores escalated risky events for review and response.

### PlatformUser
Stores local user credentials and platform roles.

---

## Roles

SecureAgent supports platform roles such as:
- `admin`
- `analyst`
- `auditor`
- `user`

Role-based permissions control access to:
- policy editing
- incident actions
- sensitive APIs
- demo controls

---

## Available Pages

### Login
Authenticates users and stores access tokens.

### Dashboard
Shows:
- total events
- blocked events
- allowed events
- high-risk events
- recent events
- active alerts
- live alert feed

### Testing Lab
Used to:
- run manual test prompts
- launch quick red-team simulations
- inspect backend responses
- seed and clear demo data
- review recent test history

### Incidents
Used to:
- review incidents
- filter by status
- acknowledge incidents
- resolve incidents

### Reports
Used to:
- view security summaries
- analyze severity and role breakdowns
- export data as JSON/CSV

### Policy Editor
Used to:
- load policy
- edit YAML
- save and reload policy
- reset to default
- restore older versions

---

## Demo Flow

A strong demo flow for SecureAgent is:

**Step 1: Login**
Login as admin or analyst.

**Step 2: Seed Demo Data**
Use the demo control to populate:
- security events
- incidents
- alerts
- reports

**Step 3: Open Dashboard**
Show:
- total event visibility
- high-risk alerts
- live feed behavior

**Step 4: Open Testing Lab**
Run:
- benign prompt
- malicious prompt
- red-team suite

**Step 5: Show Incident Center**
Explain:
- automatic incident generation
- acknowledgement and resolution flow

**Step 6: Open Reports**
Export JSON/CSV evidence.

**Step 7: Open Policy Editor**
Change a rule or threshold, reload policy, and rerun the same prompt to show different enforcement behavior.

---

## Example Threat Cases Covered

- Prompt injection attempts
- System prompt extraction attempts
- API key / secret exposure attempts
- Restricted tool usage
- Unauthorized shell execution
- Sensitive output leakage
- Unsafe developer-message bypass attempts

---

## Example API Routes

### Auth
```
POST /auth/login
GET  /auth/me
```

### Events
```
GET /events
GET /alerts
GET /security/stats
```

### Testing
```
POST /agent/run
POST /security/red-team-test
```

### Incidents
```
GET   /api/incidents
PATCH /api/incidents/{incident_id}
POST  /api/incidents/{incident_id}/ack
POST  /api/incidents/{incident_id}/resolve
```

### Reports
```
GET /reports/security-summary
GET /export/events/json
GET /export/events/csv
GET /export/incidents/json
GET /export/incidents/csv
```

### Policy
```
GET  /security/policy/raw
POST /security/policy/update
POST /security/policy/reload
POST /security/policy/reset
GET  /security/policy/history
POST /security/policy/restore
```

### Demo
```
POST /demo/seed
POST /demo/clear
```

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the server
```bash
uvicorn main:app --reload
```

### 3. Open in browser
```
http://127.0.0.1:8000/login
```

---

## Why This Project Matters

AI systems are becoming more autonomous and tool-capable. That creates a growing need for runtime security, policy enforcement, and observable governance. SecureAgent demonstrates how a platform can:

- monitor AI activity
- block unsafe behavior
- generate audit records
- escalate incidents
- provide admin visibility
- support secure deployment practices

---

## Author

Developed as a security-focused AI systems project demonstrating:

- runtime AI governance
- backend engineering
- web platform integration
- security event handling
- incident response workflows

---

## License

This project is for educational, demonstration, and portfolio purposes.
