# ADR-002: Use Redis for Interview Session Management

| Field | Value |
|-------|-------|
| **ID** | ADR-002 |
| **Date** | 2026-07-15 |
| **Status** | Accepted |
| **Implemented In** | Phase 1, Milestone 1.2 |
| **Decided By** | Lead Architect |

---

## Context

The Adaptive AI Interview Assistant is a stateful system. Every active interview session
requires tracking:
- Current question index and history
- Candidate's answer history (for the adaptive engine)
- Competency confidence scores (live updates)
- Session expiry (interviews have a defined time limit)
- Real-time state updates as the conversation progresses

The session state must be:
1. **Fast** — every question-response cycle reads/writes session state (sub-millisecond)
2. **Ephemeral** — sessions expire automatically after the interview ends
3. **Serializable** — the state can be serialized to JSON and deserialized back
4. **Recoverable** — if the API restarts, in-progress sessions survive

---

## Problem

Where should we store live interview session state?

---

## Options Considered

### Option A: In-Memory (Python dict)
- Fastest possible access — O(1) dict lookup
- Zero infrastructure
- **Fatal flaw**: State is lost on every API restart or deployment
- **Fatal flaw**: Does not scale beyond a single process (horizontal scaling impossible)
- Acceptable only for a local prototype with a single user

### Option B: SQLite / PostgreSQL
- Persistent, survives restarts
- ACID transactions — safe against corruption
- **Problem**: Relational databases are optimized for long-lived structured data, not
  short-lived volatile session records
- TTL-based expiry requires a background job or cron — extra complexity
- Latency: PostgreSQL network round-trip is 1–5ms per query vs Redis < 0.1ms

### Option C: Redis ✅
- **Purpose-built for session management** — used by almost every major web application
- **Native TTL support** — `SETEX key 3600 value` automatically expires the session after 1 hour
- **Sub-millisecond latency** — Redis is an in-memory store with optional persistence
- **Pub/Sub built-in** — enables real-time updates (future: WebSocket interview feed)
- **Scales horizontally** — Redis Cluster supports sharding
- **Persistence options**: RDB snapshots or AOF log for crash recovery

### Option D: MongoDB
- Flexible document store — good for JSON-like session objects
- More operationally complex than Redis for pure session use
- Latency higher than Redis for single-record reads

---

## Decision

**Use Redis for all interview session state.**

---

## Advantages

1. **Purpose-built for sessions** — Redis was designed for exactly this use case.
   GitHub, Twitter, Stack Overflow, and Discord all use Redis for session state.

2. **Automatic expiry** — TTL is a first-class Redis feature. When an interview ends
   or times out, the session key expires automatically. No background cleanup jobs needed.

3. **Minimal latency impact** — Session read/write adds < 0.1ms to each request.
   This keeps the adaptive interview loop feeling instantaneous.

4. **Data structure flexibility** — Redis supports strings, hashes, lists, and sorted sets.
   We store session state as a JSON string under a UUID key. In future we can use Redis
   sorted sets to rank candidates by competency score.

5. **Readiness probe integration** — Redis connectivity is checked in our
   `GET /api/v1/health/ready` endpoint, giving us operational visibility.

6. **Research credibility** — Redis is the industry standard for session management.
   Using it demonstrates production-grade architecture awareness.

---

## Disadvantages

1. **Infrastructure requirement** — Redis must be running locally (via Docker) or
   as a managed service (AWS ElastiCache, Upstash). This adds setup complexity.

2. **Memory limits** — Redis is memory-resident. For very large interview histories
   (thousands of questions), memory pressure could occur. Mitigation: store only the
   last N answers in Redis; persist full history to PostgreSQL.

3. **No built-in query** — You cannot do `SELECT * FROM sessions WHERE topic = 'DSA'`.
   For analytics queries we use PostgreSQL (M1.3+).

---

## Future Implications

- In M1.3, PostgreSQL will store the permanent interview transcript after the session ends.
  Redis holds the **live** state; PostgreSQL holds the **archived** state.
- In M5.1 (Report Generation), the report generator reads from PostgreSQL, not Redis,
  because the session will have already been archived by then.
- In a production deployment, use Redis Sentinel or Redis Cluster for high availability.
- The Redis connection pool must use async client (`redis.asyncio`) to avoid blocking
  FastAPI's event loop.
