# Temporal Reasoning Patterns

## Graph Schema for Temporal Events

### Node Labels
- `Event` — any institutional event (decision, incident, change, policy update)
- `Entity` — system, team, person, or concept that events affect

### Relationship Types

| Relationship | Direction | Meaning |
|---|---|---|
| `CAUSED` | Event → Event | A directly caused B |
| `TRIGGERED` | Event → Event | A initiated the process that led to B |
| `PRECEDED` | Event → Event | A happened before B (no causal claim) |
| `SUPERSEDED_BY` | Event → Event | B replaced A |
| `INVOLVES` | Event → Entity | Event affects this entity |
| `OWNED_BY` | Event → Entity | Entity was responsible for this event |

### Example Graph Fragment (Cypher)

```cypher
// Create the cascade failure incident
CREATE (cascade:Event {
  id: 'inc_cascade_2023',
  type: 'incident',
  timestamp: datetime('2023-09-14T03:47:00Z'),
  title: 'Auth cascade failure'
})

// Create the service mesh ADR that followed
CREATE (mesh_adr:Event {
  id: 'adr_service_mesh_2023',
  type: 'decision',
  timestamp: datetime('2023-11-08T10:00:00Z'),
  title: 'Adopt Istio service mesh'
})

// Create the causal relationship
CREATE (cascade)-[:CAUSED {
  rationale: 'Cascade failure exposed need for circuit breakers and traffic management',
  identified_by: 'arch-committee',
  lag_days: 55
}]->(mesh_adr)

// Link both to affected entity
MATCH (auth:Entity {id: 'svc_auth'})
CREATE (cascade)-[:INVOLVES]->(auth)
CREATE (mesh_adr)-[:INVOLVES]->(auth)
```

---

## Temporal Query Patterns

### Pattern: Find all events that caused a given event

```cypher
MATCH (target:Event {id: $target_id})
CALL apoc.path.subgraphNodes(target, {
  relationshipFilter: '<CAUSED|<TRIGGERED',
  maxLevel: $max_hops
}) YIELD node AS ancestor
RETURN ancestor
ORDER BY ancestor.timestamp ASC
```

### Pattern: Find all consequences of a given event

```cypher
MATCH (source:Event {id: $source_id})
CALL apoc.path.subgraphNodes(source, {
  relationshipFilter: 'CAUSED>|TRIGGERED>',
  maxLevel: $max_hops
}) YIELD node AS consequence
RETURN consequence
ORDER BY consequence.timestamp ASC
```

### Pattern: Timeline for a specific entity

```cypher
MATCH (entity:Entity {id: $entity_id})<-[:INVOLVES]-(event:Event)
WHERE event.timestamp >= $start AND event.timestamp <= $end
RETURN event
ORDER BY event.timestamp ASC
```

### Pattern: Find "orphaned" events with no causal predecessors

```cypher
MATCH (e:Event)
WHERE NOT (e)<-[:CAUSED]-() AND NOT (e)<-[:TRIGGERED]-()
  AND e.timestamp < datetime() - duration({months: 3})
RETURN e
ORDER BY e.timestamp DESC
```

Use this to find events that were ingested but never linked — candidates for retroactive causal annotation.

---

## Temporal Reasoning Anti-Patterns

### Anti-Pattern 1: Treating time as a sort key only
Sorting events by timestamp and feeding them as a flat list loses causal structure. Two events close in time may be unrelated; two events far apart may be causally connected. Always traverse causal edges, not just time.

### Anti-Pattern 2: Conflating correlation with causation in the graph
Do not create `CAUSED` edges for events that merely co-occurred. Use `PRECEDED` for temporal proximity and `CAUSED` only when there is documented evidence of causation. Hallucinated causal edges are worse than missing ones.

### Anti-Pattern 3: Unbounded causal traversal
Without a hop limit, causal traversal on a densely connected org history graph can return thousands of ancestor events. Set `maxLevel: 4` as default; increase only for explicit deep-history queries.

### Anti-Pattern 4: Ingesting documents as events
A document is not an event. An ADR document represents a decision event — extract the event, capture the document as a linked artifact. The event node is what gets queried; the document is reference material.
