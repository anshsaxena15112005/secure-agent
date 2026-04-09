# SecureAgent Interview Q&A

## Basic Questions

### Q1: What is SecureAgent?
SecureAgent is a runtime security platform for AI agents that monitors prompts, tool usage, and outputs to detect and prevent unsafe behavior in real time.

---

### Q2: Why did you build this project?
AI systems are becoming more powerful and autonomous, which introduces risks like prompt injection, data leakage, and unsafe tool usage. I wanted to build a system that actively monitors and controls these risks.

---

### Q3: What problem does it solve?
It solves:
- prompt injection attacks
- secret leakage
- unsafe tool execution
- policy bypass attempts

---

## Technical Questions

### Q4: How does your system work internally?
1. User sends prompt
2. Planner creates execution plan
3. Executor checks:
   - prompt safety
   - tool permissions
   - output safety
4. Risk score is calculated
5. Event is logged
6. Incident is created if needed
7. Dashboard updates via WebSocket

---

### Q5: What is the role of the executor?
The executor is the core component that enforces security. It evaluates prompts, tools, and outputs and decides whether to allow, block, or redact actions.

---

### Q6: Why did you use FastAPI?
- lightweight and fast
- easy API building
- supports async and WebSockets
- suitable for backend systems

---

### Q7: Why SQLite?
- simple setup
- no external dependency
- suitable for demo and prototype

---

### Q8: Why SQLAlchemy?
- ORM abstraction
- cleaner code
- easier database handling

---

### Q9: How do you detect prompt injection?
By analyzing user prompts for patterns like:
- "ignore previous instructions"
- attempts to reveal system prompt
- instruction override patterns

---

### Q10: How are incidents created?
If a security event has high or critical severity, an incident is automatically created and stored for review.

---

### Q11: How does real-time update work?
Using WebSockets. When an event or incident is created, it is broadcasted to the frontend dashboard.

---

## Design Questions

### Q12: Why separate planner and executor?
To separate logic:
- planner → decides what to do
- executor → decides if it is safe

---

### Q13: How is policy enforced?
Through a YAML-based policy system that defines:
- allowed tools per role
- risk thresholds
- blocking conditions

---

### Q14: Can your system scale?
Yes, by:
- replacing SQLite with PostgreSQL
- adding async workers
- deploying with Docker and cloud infrastructure

---

## Scenario Questions

### Q15: What happens if a user tries to extract API keys?
- prompt is flagged
- output is blocked
- event is logged
- incident is created

---

### Q16: What happens if an unauthorized tool is used?
- tool is blocked
- high-risk event is generated
- incident may be created

---

### Q17: What if policy changes?
- policy is updated via editor
- reloaded
- new executions follow updated rules

---

## Advanced Questions

### Q18: How is this different from a firewall?
Traditional firewalls protect network traffic.
SecureAgent protects AI runtime behavior.

---

### Q19: How can this integrate with real systems?
It can act as:
- middleware for AI APIs
- wrapper around LLM calls
- plugin for agent frameworks

---

### Q20: What are future improvements?
- multi-tenant system
- external alerts (email/slack)
- better analytics
- SIEM integration
- production deployment

---

## Your Pitch (IMPORTANT)

SecureAgent is not just monitoring AI behavior, it actively controls and prevents unsafe actions at runtime using policy-based enforcement, making AI systems safer and more reliable.