# SecureAgent API Reference

## Auth
- `POST /auth/login`
- `GET /auth/me`

## Pages
- `GET /login`
- `GET /dashboard`
- `GET /testing`
- `GET /incidents`
- `GET /reports`
- `GET /policy-editor`

## Agent
- `POST /agent/run`

## Events
- `GET /events`
- `GET /api/events`
- `GET /alerts`
- `GET /security/stats`

## Incidents
- `GET /api/incidents`
- `GET /api/incidents/stats`
- `POST /api/incidents/{incident_id}/ack`
- `POST /api/incidents/{incident_id}/resolve`
- `PATCH /api/incidents/{incident_id}`
- `PUT /api/incidents/{incident_id}`
- `POST /incidents/update/{incident_id}`

## Policy
- `GET /security/policy`
- `GET /security/policy/raw`
- `POST /security/policy/update`
- `POST /security/policy/reload`
- `POST /security/policy/reset`
- `GET /security/policy/history`
- `POST /security/policy/restore`

## Reports
- `GET /reports/security-summary`
- `GET /export/events/json`
- `GET /export/events/csv`
- `GET /export/incidents/json`
- `GET /export/incidents/csv`

## Demo
- `POST /demo/seed`
- `POST /demo/clear`

## WebSocket
- `WS /ws/alerts`