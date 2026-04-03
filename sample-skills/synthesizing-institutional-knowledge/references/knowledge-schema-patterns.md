# Knowledge Schema Patterns

## Extended Event Schema by Knowledge Type

### Architectural Decision Record (ADR) as Institutional Event

```json
{
  "id": "adr_042_service_mesh",
  "type": "decision",
  "category": "architecture",
  "timestamp": "2023-11-08T10:00:00Z",
  "title": "Adopt Istio as service mesh for inter-service communication",
  "status": "accepted",
  "context": "We have 34 microservices with no standardized service discovery, mTLS, or traffic management. Debugging inter-service failures takes days.",
  "decision": "Adopt Istio 1.19. Begin with observability features, then roll out mTLS over 2 quarters.",
  "rationale": "Istio was selected over Linkerd due to existing team familiarity and richer policy controls required for PCI compliance.",
  "alternatives_considered": [
    {"option": "Linkerd", "rejected_because": "Smaller policy API; less familiar to team"},
    {"option": "Custom mTLS with Envoy", "rejected_because": "Too high operational burden"}
  ],
  "consequences": {
    "positive": ["Standardized observability", "mTLS without app changes", "Circuit breaking"],
    "negative": ["Sidecar overhead ~30ms p99", "Control plane resource cost", "Learning curve"]
  },
  "actors": ["arch-committee", "platform-team"],
  "affected_entities": ["all-microservices", "platform-team", "ci-cd-pipeline"],
  "causal_predecessors": ["inc_2023_09_cascade_failure"],
  "supersedes": "adr_031_manual_mtls",
  "tags": ["networking", "security", "pci", "istio"]
}
```

### Incident Post-Mortem as Institutional Event

```json
{
  "id": "inc_2023_09_cascade_failure",
  "type": "incident",
  "severity": "P0",
  "timestamp": "2023-09-14T03:47:00Z",
  "duration_minutes": 187,
  "title": "Auth service cascade failure affecting all user-facing services",
  "timeline": [
    {"t": "+0m", "event": "Auth service begins returning 503"},
    {"t": "+3m", "event": "API gateway retry storm begins"},
    {"t": "+12m", "event": "Database connection pool exhausted"},
    {"t": "+34m", "event": "On-call engineer paged"},
    {"t": "+187m", "event": "Service restored after connection pool flush"}
  ],
  "root_cause": "Auth service had no circuit breaker. Downstream services retried aggressively on 503s, exhausting DB connections.",
  "contributing_factors": [
    "No rate limiting on internal traffic",
    "Retry policies not coordinated across services",
    "No connection pool monitoring alerts"
  ],
  "remediation": [
    "Added circuit breakers to auth service (completed 2023-09-21)",
    "Standardized retry policies (completed 2023-10-05)",
    "Added connection pool alerts (completed 2023-09-18)"
  ],
  "causal_successors": ["adr_042_service_mesh"],
  "affected_entities": ["auth-service", "api-gateway", "user-db", "all-user-facing-services"],
  "tags": ["cascade", "circuit-breaker", "availability"]
}
```

---

## Entity Types for the Knowledge Graph

### System Entity
```json
{
  "id": "svc_auth",
  "type": "system",
  "name": "auth-service",
  "owner_team": "platform-team",
  "dependencies": ["user-db", "redis-cache", "email-service"],
  "dependents": ["api-gateway", "mobile-app", "admin-portal"],
  "criticality": "P0",
  "tags": ["auth", "identity", "pci"]
}
```

### Team Entity
```json
{
  "id": "team_platform",
  "type": "team",
  "name": "Platform Engineering",
  "owns_systems": ["auth-service", "api-gateway", "service-mesh"],
  "on_call_rotation": true
}
```

### Person Entity (for decision provenance — keep minimal for privacy)
```json
{
  "id": "person_alice_eng",
  "type": "person",
  "role": "Principal Engineer",
  "team": "team_platform",
  "decisions_as_owner": ["adr_042_service_mesh", "adr_039_redis_clustering"]
}
```

---

## Ingestion Templates

### For Meeting Notes → Institutional Events

When processing unstructured meeting notes, extract:
1. **Decisions made** → create `type: decision` event nodes
2. **Problems identified** → create `type: incident` or `type: finding` nodes
3. **Actions assigned** → link as `causal_successors` on the relevant decision node

### For Slack/Email Threads → Institutional Events

For significant threads:
1. Summarize the thread into a single event node
2. Capture the final decision and the key arguments made
3. Link to any documents referenced in the thread
4. Tag the actors (people who influenced the outcome)
