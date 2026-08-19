# Session Handover Protocol

A handover is a durable artifact, not a vague chat summary.

The active agent is asked to write Markdown with these exact headings:

1. `Objective`
2. `Current State`
3. `Decisions and Invariants`
4. `Files/Repositories Changed`
5. `Commands and Tests Run`
6. `Evidence and Results`
7. `Failures / Negative Results`
8. `Open Risks`
9. `Next Actions (ordered)`
10. `Context Worth Carrying Forward`
11. `Things NOT To Rediscover`

The host adds metadata outside model control:

- handover id
- source session id
- created timestamp
- workspace absolute path
- Git HEAD OID and dirty state
- context used/max tokens
- runtime id/model id if known
- SHA-256 of the handover body

## Required behavior

- A model may author the body; it may not author its own digest/timestamp/Git OID.
- End-session always offers a handover when there has been meaningful activity.
- Context-pressure handovers are written before destructive compression when possible.
- Next session receives the newest handover as a high-priority *observed* fragment, not `canonical` truth.
- A handover can be superseded but is never silently mutated.
