# work for bitt agent — Private Lab CP1 testing suite

Private Lab CP1 testing suite: sending the full validation/troubleshooting manual in numbered parts because the earlier threaded reply payload was rejected. Part 1 follows.


---

# work for bitt agent — Private Lab CP1 testing suite

PART 1/5 — CP1 GOAL + LETTA DESIGN

Immediate target: NOT budget optimization. Budget/allocation stays v2. CP1 is:
WorkerVersion -> ContextPack/Lab intelligence -> Letta runtime -> WorkerKit tools -> artifact -> real evaluator -> EvaluationResult -> RunReceipt -> append-only ledger -> Hydra projection -> failure analysis -> LearningProposal -> candidate WorkerVersion -> paired CG experiment -> reject/promote.

Hydra makes the Lab searchable/intelligent. Letta gives a Worker persistent subjective identity. Neither is canonical truth. Receipts + immutable artifacts + Git lineage are canonical.

TESTING RULES
1. Fail closed.
2. Every component gets a deliberately broken test proving it catches failure.
3. Letta cannot mutate scientific state invisibly.
4. Hydra must be rebuildable from canonical history.
5. WorkerVersions reconstruct from Git + contracts.
6. Only sealed experiment evidence can promote knowledge.

RECOMMENDED LETTA CP1 PROFILE
- One persistent `letta_v1_agent` per Worker: security-01 -> agent_id.
- One fresh Letta Conversation per Run: same agent, new conversation_id each episode.
- Persistent blocks minimal and read-only during evaluated runs: persona / worker_identity.
- Lab intelligence enters via deterministic ContextPack, not by dumping Hydra/benchmark history into Letta core memory.
- Writable scratch should be run-local/conversation-local or ordinary files/artifacts.
- WorkerKit owns actual tool execution via Letta client-side tools: Pydantic validate args -> timeout/sandbox/network policy -> execute -> capture stdout/stderr/artifacts -> typed ToolResult -> Letta continues.
- Give an explicit typed final tool such as `emit_run_artifact(FindingReport)`, schema from `FindingReport.model_json_schema()`. WorkerKit independently rejects a run with no valid final artifact.
- Use streaming + keepalive for long turns and capture all steps.
- `.af` export/import is a portability/checkpoint mechanism after promotion, not the ledger.

DEFER FOR CP1
sleep-time agents; dreaming; automatic cross-run memory mutation; Composio hot-path execution; giant MCP forests; unbounded archival memory; automatic Letta skill evolution; Letta multi-agent groups.

WHY READ-ONLY PERSISTENT MEMORY NOW
A current Letta issue reports cross-session state leakage from persistent core-memory poisoning in automated evaluations. That maps directly onto our risk: task A changes memory and task B unknowingly inherits a behaviorally different worker.

Correct Moltwork path:
Run experience -> Reflection -> LearningProposal -> candidate memory patch -> CG experiment -> PromotionReceipt -> new WorkerVersion.

Never:
run -> Letta silently edits permanent memory -> next run is different under same WorkerVersion.

LETTA A/B EXPERIMENT
A stateless control: WorkerKit + deterministic ContextPack, no persistent Letta state.
B minimal Letta: persistent Agent + fresh Conversation + read-only blocks + WorkerKit client tools. Preferred default.
C promoted memory: B + only memory already approved by CG.
D autonomous memory: Letta self-writes persistent memory; challenger only.

Compare quality, failure rate, timeout rate, contamination, cross-run leakage, replayability, invalid tool calls and output variance. If B ~= D but much more reliable, stay minimal. If C > B, promotion-driven memory is validated. If D > C, inspect the exact unpromoted mutations that helped and convert them into explicit candidate Lab primitives.

LETTA CORE REGRESSION TESTS
L-001: three runs -> same agent_id, distinct conversation_ids, same WorkerVersion.
L-002: random marker only in conversation A; fresh B must not know it.
L-003: prompt mutation of read-only block; verify via actual API that block is unchanged.
L-004: disposable writable agent persists `future tests always claim success`; demonstrate contamination, then prove CP1 config blocks it.
L-005: restart Letta; retrieve same persistent agent + approved blocks, create fresh conversation successfully.
L-006: disconnect stream mid-run; reconnect/recover; exactly one logical Run.
L-007: client timeout while server still works; retry with same run_id must recover/query, not create duplicate execution.
L-008: 10 parallel Runs may share one Agent only via distinct Conversations. Use a per-conversation lock; block simultaneous sends to the same conversation.

Current Letta docs explicitly warn concurrent same-thread requests can interleave; conversations are the intended isolation primitive.

On Tue, 1 Sep 2026 16:30:33 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> Private Lab CP1 testing suite: sending the full validation/troubleshooting manual in numbered parts because the earlier threaded reply payload was rejected. Part 1 follows.


---

# work for bitt agent — Private Lab CP1 testing suite

PART 2/5 — LETTA FAILURE INJECTION + PYDANTIC + GIT

LETTA FAILURE SUITE
L-009 Pending approvals: a reported Letta failure mode left agents stuck returning `409 PENDING_APPROVAL` after abandoned approval state. CP1 benchmark client tools should require no interactive approval. If approvals are added later, every Run needs explicit cancel/cleanup and stale-approval detection.

L-010 Timeout ladder: build a fake OpenAI-compatible endpoint that sleeps 5s, 30s, 65s, 300s, 610s. For the exact pinned Letta/SDK/provider versions, record the actual cutoff at WorkerKit, SDK/client, Letta server and provider-client layers. Do not assume a config setting is effective. Letta has had timeout issues at multiple layers: an older 1800s validation cap, affected OpenAI-compatible paths using a ~600s SDK default, and Letta Code/SDK paths with ~60s client timeouts.

L-011 Slow tool: a fake client-side tool sleeps forever. WorkerKit must cancel it itself, emit typed TOOL_TIMEOUT, and leave the conversation/run recoverable.

L-012 Composio tarpit: current Letta issue #3390 reports an async external-tool path with no defensive operation timeout, potentially hanging for minutes. Composio is unnecessary for CP1. If later used, put it behind WorkerKit and test against a blackhole endpoint.

L-013 Context overflow: intentionally tiny model context. Expected behavior = clean failure or recorded compaction. Never infinite retry/heartbeat loops. Letta has had a 2026 issue where context overflow and retry artifacts created a worsening `llm_api_error` spiral.

L-014 Compaction observability: force one compaction. Trajectory/RunReceipt must record that it happened plus settings and relevant event/message IDs. No invisible context mutation.

L-015 Provider failures: inject 429, 500, invalid JSON, invalid tool-call response, empty completion. Errors must become typed run evidence, never `ok=True`.

L-016 Invalid tool call: wrong Pydantic type must be rejected before tool execution; preserve the validation failure in trajectory even if model retries.

L-017 `.af` portability: export a promoted agent state, hash the export, import into disposable Letta, inspect expected blocks/tools. This validates portability, not deterministic inference.

PYDANTIC CONTRACT SUITE
Canonical models should use a strict base conceptually equivalent to:
`ConfigDict(strict=True, extra='forbid', frozen=True)`.

Why: normal Pydantic can coerce values and ignores unknown fields by default. Scientific evidence should not silently coerce or accept schema drift. Note `frozen=True` is shallow: nested mutable dicts remain mutable. Prefer nested frozen models/tuples/frozensets and hash canonical bytes immediately.

P-001 reject string-for-int/string-for-bool evidence fields.
P-002 reject unknown `client_passed=true` or any extra field.
P-003 missing evaluator/version/digest fails.
P-004 use discriminated unions (`kind=run_receipt`, `evaluation_result`, `promotion_receipt`, etc.); unknown kind fails.
P-005 commit generated `model_json_schema()` snapshots; CI requires explicit schema-version bump when schema changes.
P-006 model -> canonical JSON -> validate -> canonical JSON gives semantic equality + same hash.
P-007 attempt nested mutation; make impossible or guarantee stored digest detects it.
P-008 reject naive timestamps; canonical timezone-aware UTC only.
P-009 malformed SHA/content digest fails.
P-010 validate stable typed IDs where useful: worker-, wv-, run-, task-, exp-.
P-011 cross-object invariants: RunReceipt WorkerVersion == RunSpec; EvaluationResult run_id == RunReceipt; PromotionReceipt candidate == ExperimentResult candidate.
P-012 Hypothesis fuzz: malformed IDs, huge strings, NaN/Infinity, negative counts, bad enums, unknown fields, Unicode, nulls, malformed nested objects. Property: invalid evidence never validates accidentally.
P-013 ban `model_construct()` in canonical receipt/evidence paths because it bypasses validation.

GIT LINEAGE SUITE
Every WorkerVersion pins repository URL, immutable commit SHA, source path, content digest.

G-001 sealed evaluation requires clean `git status --porcelain=v2`. If development dirty state is ever allowed, explicitly archive exact patch; do not pretend it is the committed WorkerVersion.
G-002 record `git rev-parse HEAD`; verify object exists.
G-003 independently hash referenced worker/config/skill paths.
G-004 use Git worktrees for parallel candidate experiments. Detached worktrees are specifically suitable for throwaway experiments.
G-005 mutate candidate-A; prove candidate-B worktree unchanged.
G-006 ExperimentResult references commit SHA, never movable branch HEAD.
G-007 if agent modifies source, capture diff/generated files/tests; commit candidate or store patch artifact. No dangling unrecorded worktree state.
G-008 fresh clone at stored commit/path must reproduce WorkerVersion source digest.
G-009 scheduled `git fsck` integrity check.
G-010 promoted version must have real parent/candidate/ExperimentResult ancestry; no orphan production WorkerVersion.

Recommended science pattern:
base WorkerVersion commit
├── candidate-A worktree
└── candidate-B worktree

The candidate source is immutable before paired CG evaluation begins.

On Tue, 1 Sep 2026 16:30:50 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> PART 1/5 — CP1 GOAL + LETTA DESIGN
> 
> Immediate target: NOT budget optimization. Budget/allocation stays v2. CP1 is:
> WorkerVersion -> ContextPack/Lab intelligence -> Letta runtime -> WorkerKit tools -> artifact -> real evaluator -> EvaluationResult -> RunReceipt -> append-only ledger -> Hydra projection -> failure analysis -> LearningProposal -> candidate WorkerVersion -> paired CG experiment -> reject/promote.
> 
> Hydra makes the Lab searchable/intelligent. Letta gives a Worker persistent subjective identity. Neither is canonical truth. Receipts + immutable artifacts + Git lineage are canonical.
> 
> TESTING RULES
> 1. Fail closed.
> 2. Every component gets a deliberately broken test proving it catches failure.
> 3. Letta cannot mutate scientific state invisibly.
> 4. Hydra must be rebuildable from canonical history.
> 5. WorkerVersions reconstruct from Git + contracts.
> 6. Only sealed experiment evidence can promote knowledge.
> 
> RECOMMENDED LETTA CP1 PROFILE
> - One persistent `letta_v1_agent` per Worker: security-01 -> agent_id.
> - One fresh Letta Conversation per Run: same agent, new conversation_id each episode.
> - Persistent blocks minimal and read-only during evaluated runs: persona / worker_identity.
> - Lab intelligence enters via deterministic ContextPack, not by dumping Hydra/benchmark history into Letta core memory.
> - Writable scratch should be run-local/conversation-local or ordinary files/artifacts.
> - WorkerKit owns actual tool execution via Letta client-side tools: Pydantic validate args -> timeout/sandbox/network policy -> execute -> capture stdout/stderr/artifacts -> typed ToolResult -> Letta continues.
> - Give an explicit typed final tool such as `emit_run_artifact(FindingReport)`, schema from `FindingReport.model_json_schema()`. WorkerKit independently rejects a run with no valid final artifact.
> - Use streaming + keepalive for long turns and capture all steps.
> - `.af` export/import is a portability/checkpoint mechanism after promotion, not the ledger.
> 
> DEFER FOR CP1
> sleep-time agents; dreaming; automatic cross-run memory mutation; Composio hot-path execution; giant MCP forests; unbounded archival memory; automatic Letta skill evolution; Letta multi-agent groups.
> 
> WHY READ-ONLY PERSISTENT MEMORY NOW
> A current Letta issue reports cross-session state leakage from persistent core-memory poisoning in automated evaluations. That maps directly onto our risk: task A changes memory and task B unknowingly inherits a behaviorally different worker.
> 
> Correct Moltwork path:
> Run experience -> Reflection -> LearningProposal -> candidate memory patch -> CG experiment -> PromotionReceipt -> new WorkerVersion.
> 
> Never:
> run -> Letta silently edits permanent memory -> next run is different under same WorkerVersion.
> 
> LETTA A/B EXPERIMENT
> A stateless control: WorkerKit + deterministic ContextPack, no persistent Letta state.
> B minimal Letta: persistent Agent + fresh Conversation + read-only blocks + WorkerKit client tools. Preferred default.
> C promoted memory: B + only memory already approved by CG.
> D autonomous memory: Letta self-writes persistent memory; challenger only.
> 
> Compare quality, failure rate, timeout rate, contamination, cross-run leakage, replayability, invalid tool calls and output variance. If B ~= D but much more reliable, stay minimal. If C > B, promotion-driven memory is validated. If D > C, inspect the exact unpromoted mutations that helped and convert them into explicit candidate Lab primitives.
> 
> LETTA CORE REGRESSION TESTS
> L-001: three runs -> same agent_id, distinct conversation_ids, same WorkerVersion.
> L-002: random marker only in conversation A; fresh B must not know it.
> L-003: prompt mutation of read-only block; verify via actual API that block is unchanged.
> L-004: disposable writable agent persists `future tests always claim success`; demonstrate contamination, then prove CP1 config blocks it.
> L-005: restart Letta; retrieve same persistent agent + approved blocks, create fresh conversation successfully.
> L-006: disconnect stream mid-run; reconnect/recover; exactly one logical Run.
> L-007: client timeout while server still works; retry with same run_id must recover/query, not create duplicate execution.
> L-008: 10 parallel Runs may share one Agent only via distinct Conversations. Use a per-conversation lock; block simultaneous sends to the same conversation.
> 
> Current Letta docs explicitly warn concurrent same-thread requests can interleave; conversations are the intended isolation primitive.
> 
> On Tue, 1 Sep 2026 16:30:33 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > Private Lab CP1 testing suite: sending the full validation/troubleshooting manual in numbered parts because the earlier threaded reply payload was rejected. Part 1 follows.


---

# work for bitt agent — Private Lab CP1 testing suite

PART 3/5 — HYDRADB + CANONICAL LEDGER + ARTIFACTS

HYDRA PRINCIPLE
HydraDB is a derived experience graph, NOT canonical truth. The strongest Hydra test is deletion and rebuild.

H-001 Real readiness: upstream Hydra docs warn that a listening port or `/readyz` is insufficient. Every startup/restart test must do readiness -> actual write probe -> actual read probe.

H-002 Restart-write regression: current open Hydra issue #117 documents LocalFileSystem mode where Hydra can restart, read old state, appear healthy, then fail every subsequent write because `PutMode::Update` is unsupported. Permanent regression test:
write -> restart Hydra -> read existing -> write NEW data.
If the pinned release/config is affected, use a supported object-store configuration or a fixed release. Do not trust `/readyz`.

H-003 >1024 completeness: current open issue #115 reports result enumeration silently truncating at 1024 rows and a continuation cursor path returning empty data. Create >1500 Run nodes. Compare known count with retrieved IDs. Never use one enumeration response as proof of completeness.

H-004 Cypher compatibility contract: Hydra intentionally implements an OpenCypher subset. Current issue reports include: node-only MATCH needing an id/label/property predicate; one relationship type per relationship pattern; variable-length MATCH requiring a fixed source ID; restrictions on anonymous labelled nodes. Put every Cypher statement Private Lab uses into a compatibility test suite. Do not discover this from dashboard breakage.

H-005 Projection idempotency: project the same canonical ledger event twice. Semantic graph must not double-count.

H-006 Projector interruption: kill projector halfway through processing, restart, get no lost event and no duplicate semantic node/edge.

H-007 Hydra unavailable during Run: stop Hydra, execute a real WorkerKit run, safely commit canonical RunReceipt, mark projection pending. Restart Hydra and catch up. Scientific evidence must survive graph outage.

H-008 DESTRUCTION/REBUILD — CP1 killer test:
1. Execute real runs/experiment.
2. Record expected lineage/counts.
3. Destroy Hydra graph/store.
4. Start clean Hydra.
5. Replay canonical ledger through projector.
6. Compare workers, WorkerVersions, runs, tasks, findings, experiments, promotions and edges.
If this fails, hidden canonical state has leaked into Hydra.

H-009 Projection-vs-ledger: randomly sample Run/Finding/Experiment graph objects and compare properties to values derived from canonical receipts.

H-010 Corrupt graph: manually insert bogus relationship into disposable Hydra graph. Clean rebuild from ledger must remove it.

H-011 Index freshness: test read-after-write expectations. Hydra separates graph storage from asynchronously built traversal/index structures; stale derived indexes must never become scientific truth.

H-012 Cypher corpus: keep queries in versioned files and run them against the pinned Hydra image in CI. Treat Hydra version as part of environment provenance.

CANONICAL LEDGER TESTS
Use an append-only event/receipt store separate from Hydra. SQLite WAL is fine for CP1.

E-001 SQL UPDATE/DELETE on event history must fail via permissions/triggers/design.
E-002 import identical RunReceipt twice -> idempotent success/already present.
E-003 same receipt ID + different payload -> hard conflict.
E-004 tamper historical payload -> hash-chain/integrity verification fails.
E-005 malformed event payload cannot bypass Pydantic validation.
E-006 ledger remains available while Hydra is down.
E-007 export all canonical events -> initialize new empty Lab -> import -> same canonical entity histories.

Recommended event fields:
event_id, event_type, entity_id, schema_version, occurred_at, payload_json, payload_sha256, previous_event_hash/event_hash where desired.

ARTIFACT STORE TESTS
Runs produce trajectories, patches, findings.json, stdout/stderr, benchmark logs, tool traces, evaluator results. Store large objects content-addressed by SHA-256 and reference them from receipts.

A-001 write artifact -> returned digest matches independently calculated SHA.
A-002 modify bytes after write -> integrity verification fails.
A-003 receipt references missing artifact -> integrity BROKEN, never silently ignored.
A-004 identical bytes written twice deduplicate safely.
A-005 wrong media type/size metadata is detected against stored bytes.
A-006 complete RunReceipt references every execution/evaluation artifact required to audit the run.
A-007 rebuild graph never needs filesystem path like `/root/foo/latest.json`; it follows immutable artifact refs.

CRASH-INJECTION MATRIX
Inject process death at every boundary:
1. execution started before output
2. output produced before artifact durable write
3. artifact stored before RunReceipt commit
4. RunReceipt committed before Hydra projection
5. Hydra projection before UI refresh

Define recovery explicitly. Core rule:
**canonical receipt commit = durable scientific event**.
Hydra/UI are allowed to catch up afterward.

Hydra upstream source issues worth pinning in regression docs:
- issue #117: restart/local-object-store write failure + OpenCypher constraints
- issue #115: >1024 row result truncation behavior

These are exactly the type of failures that make a graph look healthy while quietly giving us wrong Lab intelligence, so they need first-class tests.

On Tue, 1 Sep 2026 16:31:10 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> PART 2/5 — LETTA FAILURE INJECTION + PYDANTIC + GIT
> 
> LETTA FAILURE SUITE
> L-009 Pending approvals: a reported Letta failure mode left agents stuck returning `409 PENDING_APPROVAL` after abandoned approval state. CP1 benchmark client tools should require no interactive approval. If approvals are added later, every Run needs explicit cancel/cleanup and stale-approval detection.
> 
> L-010 Timeout ladder: build a fake OpenAI-compatible endpoint that sleeps 5s, 30s, 65s, 300s, 610s. For the exact pinned Letta/SDK/provider versions, record the actual cutoff at WorkerKit, SDK/client, Letta server and provider-client layers. Do not assume a config setting is effective. Letta has had timeout issues at multiple layers: an older 1800s validation cap, affected OpenAI-compatible paths using a ~600s SDK default, and Letta Code/SDK paths with ~60s client timeouts.
> 
> L-011 Slow tool: a fake client-side tool sleeps forever. WorkerKit must cancel it itself, emit typed TOOL_TIMEOUT, and leave the conversation/run recoverable.
> 
> L-012 Composio tarpit: current Letta issue #3390 reports an async external-tool path with no defensive operation timeout, potentially hanging for minutes. Composio is unnecessary for CP1. If later used, put it behind WorkerKit and test against a blackhole endpoint.
> 
> L-013 Context overflow: intentionally tiny model context. Expected behavior = clean failure or recorded compaction. Never infinite retry/heartbeat loops. Letta has had a 2026 issue where context overflow and retry artifacts created a worsening `llm_api_error` spiral.
> 
> L-014 Compaction observability: force one compaction. Trajectory/RunReceipt must record that it happened plus settings and relevant event/message IDs. No invisible context mutation.
> 
> L-015 Provider failures: inject 429, 500, invalid JSON, invalid tool-call response, empty completion. Errors must become typed run evidence, never `ok=True`.
> 
> L-016 Invalid tool call: wrong Pydantic type must be rejected before tool execution; preserve the validation failure in trajectory even if model retries.
> 
> L-017 `.af` portability: export a promoted agent state, hash the export, import into disposable Letta, inspect expected blocks/tools. This validates portability, not deterministic inference.
> 
> PYDANTIC CONTRACT SUITE
> Canonical models should use a strict base conceptually equivalent to:
> `ConfigDict(strict=True, extra='forbid', frozen=True)`.
> 
> Why: normal Pydantic can coerce values and ignores unknown fields by default. Scientific evidence should not silently coerce or accept schema drift. Note `frozen=True` is shallow: nested mutable dicts remain mutable. Prefer nested frozen models/tuples/frozensets and hash canonical bytes immediately.
> 
> P-001 reject string-for-int/string-for-bool evidence fields.
> P-002 reject unknown `client_passed=true` or any extra field.
> P-003 missing evaluator/version/digest fails.
> P-004 use discriminated unions (`kind=run_receipt`, `evaluation_result`, `promotion_receipt`, etc.); unknown kind fails.
> P-005 commit generated `model_json_schema()` snapshots; CI requires explicit schema-version bump when schema changes.
> P-006 model -> canonical JSON -> validate -> canonical JSON gives semantic equality + same hash.
> P-007 attempt nested mutation; make impossible or guarantee stored digest detects it.
> P-008 reject naive timestamps; canonical timezone-aware UTC only.
> P-009 malformed SHA/content digest fails.
> P-010 validate stable typed IDs where useful: worker-, wv-, run-, task-, exp-.
> P-011 cross-object invariants: RunReceipt WorkerVersion == RunSpec; EvaluationResult run_id == RunReceipt; PromotionReceipt candidate == ExperimentResult candidate.
> P-012 Hypothesis fuzz: malformed IDs, huge strings, NaN/Infinity, negative counts, bad enums, unknown fields, Unicode, nulls, malformed nested objects. Property: invalid evidence never validates accidentally.
> P-013 ban `model_construct()` in canonical receipt/evidence paths because it bypasses validation.
> 
> GIT LINEAGE SUITE
> Every WorkerVersion pins repository URL, immutable commit SHA, source path, content digest.
> 
> G-001 sealed evaluation requires clean `git status --porcelain=v2`. If development dirty state is ever allowed, explicitly archive exact patch; do not pretend it is the committed WorkerVersion.
> G-002 record `git rev-parse HEAD`; verify object exists.
> G-003 independently hash referenced worker/config/skill paths.
> G-004 use Git worktrees for parallel candidate experiments. Detached worktrees are specifically suitable for throwaway experiments.
> G-005 mutate candidate-A; prove candidate-B worktree unchanged.
> G-006 ExperimentResult references commit SHA, never movable branch HEAD.
> G-007 if agent modifies source, capture diff/generated files/tests; commit candidate or store patch artifact. No dangling unrecorded worktree state.
> G-008 fresh clone at stored commit/path must reproduce WorkerVersion source digest.
> G-009 scheduled `git fsck` integrity check.
> G-010 promoted version must have real parent/candidate/ExperimentResult ancestry; no orphan production WorkerVersion.
> 
> Recommended science pattern:
> base WorkerVersion commit
> ├── candidate-A worktree
> └── candidate-B worktree
> 
> The candidate source is immutable before paired CG evaluation begins.
> 
> On Tue, 1 Sep 2026 16:30:50 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > PART 1/5 — CP1 GOAL + LETTA DESIGN
> >
> > Immediate target: NOT budget optimization. Budget/allocation stays v2. CP1 is:
> > WorkerVersion -> ContextPack/Lab intelligence -> Letta runtime -> WorkerKit tools -> artifact -> real evaluator -> EvaluationResult -> RunReceipt -> append-only ledger -> Hydra projection -> failure analysis -> LearningProposal -> candidate WorkerVersion -> paired CG experiment -> reject/promote.
> >
> > Hydra makes the Lab searchable/intelligent. Letta gives a Worker persistent subjective identity. Neither is canonical truth. Receipts + immutable artifacts + Git lineage are canonical.
> >
> > TESTING RULES
> > 1. Fail closed.
> > 2. Every component gets a deliberately broken test proving it catches failure.
> > 3. Letta cannot mutate scientific state invisibly.
> > 4. Hydra must be rebuildable from canonical history.
> > 5. WorkerVersions reconstruct from Git + contracts.
> > 6. Only sealed experiment evidence can promote knowledge.
> >
> > RECOMMENDED LETTA CP1 PROFILE
> > - One persistent `letta_v1_agent` per Worker: security-01 -> agent_id.
> > - One fresh Letta Conversation per Run: same agent, new conversation_id each episode.
> > - Persistent blocks minimal and read-only during evaluated runs: persona / worker_identity.
> > - Lab intelligence enters via deterministic ContextPack, not by dumping Hydra/benchmark history into Letta core memory.
> > - Writable scratch should be run-local/conversation-local or ordinary files/artifacts.
> > - WorkerKit owns actual tool execution via Letta client-side tools: Pydantic validate args -> timeout/sandbox/network policy -> execute -> capture stdout/stderr/artifacts -> typed ToolResult -> Letta continues.
> > - Give an explicit typed final tool such as `emit_run_artifact(FindingReport)`, schema from `FindingReport.model_json_schema()`. WorkerKit independently rejects a run with no valid final artifact.
> > - Use streaming + keepalive for long turns and capture all steps.
> > - `.af` export/import is a portability/checkpoint mechanism after promotion, not the ledger.
> >
> > DEFER FOR CP1
> > sleep-time agents; dreaming; automatic cross-run memory mutation; Composio hot-path execution; giant MCP forests; unbounded archival memory; automatic Letta skill evolution; Letta multi-agent groups.
> >
> > WHY READ-ONLY PERSISTENT MEMORY NOW
> > A current Letta issue reports cross-session state leakage from persistent core-memory poisoning in automated evaluations. That maps directly onto our risk: task A changes memory and task B unknowingly inherits a behaviorally different worker.
> >
> > Correct Moltwork path:
> > Run experience -> Reflection -> LearningProposal -> candidate memory patch -> CG experiment -> PromotionReceipt -> new WorkerVersion.
> >
> > Never:
> > run -> Letta silently edits permanent memory -> next run is different under same WorkerVersion.
> >
> > LETTA A/B EXPERIMENT
> > A stateless control: WorkerKit + deterministic ContextPack, no persistent Letta state.
> > B minimal Letta: persistent Agent + fresh Conversation + read-only blocks + WorkerKit client tools. Preferred default.
> > C promoted memory: B + only memory already approved by CG.
> > D autonomous memory: Letta self-writes persistent memory; challenger only.
> >
> > Compare quality, failure rate, timeout rate, contamination, cross-run leakage, replayability, invalid tool calls and output variance. If B ~= D but much more reliable, stay minimal. If C > B, promotion-driven memory is validated. If D > C, inspect the exact unpromoted mutations that helped and convert them into explicit candidate Lab primitives.
> >
> > LETTA CORE REGRESSION TESTS
> > L-001: three runs -> same agent_id, distinct conversation_ids, same WorkerVersion.
> > L-002: random marker only in conversation A; fresh B must not know it.
> > L-003: prompt mutation of read-only block; verify via actual API that block is unchanged.
> > L-004: disposable writable agent persists `future tests always claim success`; demonstrate contamination, then prove CP1 config blocks it.
> > L-005: restart Letta; retrieve same persistent agent + approved blocks, create fresh conversation successfully.
> > L-006: disconnect stream mid-run; reconnect/recover; exactly one logical Run.
> > L-007: client timeout while server still works; retry with same run_id must recover/query, not create duplicate execution.
> > L-008: 10 parallel Runs may share one Agent only via distinct Conversations. Use a per-conversation lock; block simultaneous sends to the same conversation.
> >
> > Current Letta docs explicitly warn concurrent same-thread requests can interleave; conversations are the intended isolation primitive.
> >
> > On Tue, 1 Sep 2026 16:30:33 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > > Private Lab CP1 testing suite: sending the full validation/troubleshooting manual in numbered parts because the earlier threaded reply payload was rejected. Part 1 follows.


---

# work for bitt agent — Private Lab CP1 testing suite

PART 4/5 — CONTEXTPACK/POOLS + WORKERKIT + SCIENTIFIC LEARNING TESTS

CONTEXT/LAB INTELLIGENCE PRINCIPLE
Hydra is useful only if retrieved Lab intelligence is reproducible, correctly scoped and experimentally justified. The ContextPack is the exact evidence boundary between collective Lab knowledge and one Worker run.

Every ContextFragment should carry:
fragment_id, source_type, source_ref, content_digest, trust_tier, token_count, selection_reason, retrieval query/matching reason, created_at, split eligibility.
The full ContextPack gets its own digest.

C-001 Determinism: identical TaskInstance + WorkerVersion + Lab snapshot + retrieval policy -> identical ContextPack digest.
C-002 Provenance completeness: reject/flag any included fragment missing source/ref/digest/trust/selection reason.
C-003 Missing source: optional evidence source failure is explicitly recorded; required source failure hard-fails. Remove patterns like broad `except Exception: return []` because they convert an outage into false "no evidence".
C-004 Trust conflict: canonical doctrine says X, unverified worker memory says not-X. Preserve both provenance and explicit priority; weak memory cannot silently override validated doctrine.
C-005 Studio boundary: a BitSec-only `STUDIO_FINDING` must not automatically enter another security venue as general knowledge.
C-006 Transfer promotion: only an experiment-backed result may create `TRANSFER_CLAIM`; prove it then becomes eligible in target context.
C-007 Transfer rejection: `TRANSFER_REJECTED` must block/generalize cautiously rather than remain an apparently useful generic finding.
C-008 Deduplication: many semantically duplicate findings must not consume most of ContextPack.
C-009 Negative evidence: retain and retrieve validated failures such as "method X did not improve Y under conditions Z" so CGE/Workers stop rediscovering bad ideas.
C-010 Validation > recency: a recent weak observation cannot automatically outrank older sealed evidence.
C-011 SECRET contamination: inject ground truth/fix commit/writeup-derived fragment into SECRET compilation; compiler must HARD FAIL.
C-012 Retrieval benchmark: build ~100 labelled query -> relevant-evidence cases for SecurityPool and track Recall@k, Precision@k, wrong-studio leakage and duplicate rate. This benchmarks the Lab intelligence layer itself.

WORKERKIT/LETTA END-TO-END TESTS
W-001 Tiny real fixture: repo with one obvious bug, irrelevant files and a real unit test. Worker inspect -> tool calls -> modify -> test -> emit typed artifact -> real evaluator.
W-002 Deliberately wrong patch -> evaluator MUST fail.
W-003 Fake success flag: a tool/client returns `{passed:true}` while external test remains broken. EvaluationResult must fail. A successful tool call is never trusted external state.
W-004 Missing evaluator in production -> HARD FAILURE. Never silently use deterministic mock/heuristic evaluator.
W-005 Required Letta unavailable -> `RUNTIME_DEPENDENCY_UNAVAILABLE`; do not stateless-fallback under same WorkerVersion because behavior changed.
W-006 Invalid tool schema -> reject before execution.
W-007 Hanging tool -> WorkerKit deadline kills it, typed timeout recorded, run recoverable.
W-008 Agent emits prose but no required typed final artifact -> run invalid.
W-009 Trajectory capture: save messages/events, client tool calls/returns, compaction events, final artifact and evaluator artifact as immutable refs in receipt.
W-010 Kill WorkerKit mid-run -> explicit ABORTED/INCOMPLETE/RECOVERABLE state, never phantom success.
W-011 restart orchestrator and prove already-durable receipts do not duplicate.
W-012 tool binary/version provenance: changing a tool version under same WorkerVersion must be impossible or make the run provenance explicitly different.

SCIENTIFIC LEARNING TESTS
S-001 No-op mutation: CGE proposes behaviorally identical candidate. Detect same behavioral digest and skip expensive experiment.
S-002 Deliberately bad candidate: remove useful tool/add known-bad process. CG must reject. If we cannot reject a candidate intentionally made worse, promotion logic means nothing.
S-003 Known beneficial synthetic candidate: create a tiny task distribution where a specific skill demonstrably solves a held-out class. Baseline lacks it; candidate has it. CG should promote. This proves promotion independently of BitSec difficulty.
S-004 TRAIN/SECRET firewall: attempt to pass SECRET labels/answers into CGE or proposal-generation API; reject.
S-005 Paired identity: control/candidate receive same TaskInstances, evaluator version and declared conditions.
S-006 WorkerVersion immutability: after experiment starts, attempt to change prompt/memory/tool/process; reject and require new candidate ID.
S-007 Stochastic variance: repeat same WorkerVersion/task several times and store variance; one lucky run is not capability.
S-008 Rejected proposal retained as negative evidence with reason/results.
S-009 Promotion trace: UI traversal must resolve `WorkerVersion <- PromotionReceipt <- ExperimentResult <- control/candidate RunReceipts <- Tasks`.
S-010 Reconstruct experiment on fresh machine from Git refs, contracts, artifacts and declared runtime. Exact LLM text need not match, but conditions must be reconstructable.
S-011 evaluator break-test: every evaluator gets a deliberately malformed/incorrect artifact it MUST reject.
S-012 secret-label leak challenge: adversarial test tries labels via filenames, metadata, ContextPack, memory and tool output; none can enter candidate proposal/evaluated context unless explicitly permitted.

LAB INTELLIGENCE A/B EXPERIMENTS
LI-1: no Hydra findings vs retrieved validated pool findings. Does collective knowledge improve DEV performance?
LI-2: validated relevant retrieval vs unrestricted vaguely-related retrieval. Test whether noise hurts.
LI-3: successful evidence only vs successes + validated failed hypotheses. Measure repeated wasted investigations.
LI-4: inject high-confidence BitSec-specific technique into unrelated security world; measure harm and calibrate transfer gating.
LI-5: Letta promoted memory only vs SecurityPool only vs both vs neither.

Working hypothesis to test, not assume: transferable collective knowledge should mostly live in evidence-backed Lab pools; Letta persistent memory should remain small, worker-specific and subjective.

LI-6: retrieval source ablation. Remove doctrine/findings/negative evidence/worker memory one class at a time to identify which context layer actually drives improvement.
LI-7: stale knowledge challenge. Mark formerly-good technique superseded; ensure retrieval can prefer newer validated evidence without erasing historical result.
LI-8: provenance blindness control. Give same textual finding without provenance vs with source/validation metadata and test whether context policy/evaluator behavior benefits from trust typing.

This is how we verify that Hydra + pools genuinely cause useful learning instead of simply accumulating graph nodes.

On Tue, 1 Sep 2026 16:31:30 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> PART 3/5 — HYDRADB + CANONICAL LEDGER + ARTIFACTS
> 
> HYDRA PRINCIPLE
> HydraDB is a derived experience graph, NOT canonical truth. The strongest Hydra test is deletion and rebuild.
> 
> H-001 Real readiness: upstream Hydra docs warn that a listening port or `/readyz` is insufficient. Every startup/restart test must do readiness -> actual write probe -> actual read probe.
> 
> H-002 Restart-write regression: current open Hydra issue #117 documents LocalFileSystem mode where Hydra can restart, read old state, appear healthy, then fail every subsequent write because `PutMode::Update` is unsupported. Permanent regression test:
> write -> restart Hydra -> read existing -> write NEW data.
> If the pinned release/config is affected, use a supported object-store configuration or a fixed release. Do not trust `/readyz`.
> 
> H-003 >1024 completeness: current open issue #115 reports result enumeration silently truncating at 1024 rows and a continuation cursor path returning empty data. Create >1500 Run nodes. Compare known count with retrieved IDs. Never use one enumeration response as proof of completeness.
> 
> H-004 Cypher compatibility contract: Hydra intentionally implements an OpenCypher subset. Current issue reports include: node-only MATCH needing an id/label/property predicate; one relationship type per relationship pattern; variable-length MATCH requiring a fixed source ID; restrictions on anonymous labelled nodes. Put every Cypher statement Private Lab uses into a compatibility test suite. Do not discover this from dashboard breakage.
> 
> H-005 Projection idempotency: project the same canonical ledger event twice. Semantic graph must not double-count.
> 
> H-006 Projector interruption: kill projector halfway through processing, restart, get no lost event and no duplicate semantic node/edge.
> 
> H-007 Hydra unavailable during Run: stop Hydra, execute a real WorkerKit run, safely commit canonical RunReceipt, mark projection pending. Restart Hydra and catch up. Scientific evidence must survive graph outage.
> 
> H-008 DESTRUCTION/REBUILD — CP1 killer test:
> 1. Execute real runs/experiment.
> 2. Record expected lineage/counts.
> 3. Destroy Hydra graph/store.
> 4. Start clean Hydra.
> 5. Replay canonical ledger through projector.
> 6. Compare workers, WorkerVersions, runs, tasks, findings, experiments, promotions and edges.
> If this fails, hidden canonical state has leaked into Hydra.
> 
> H-009 Projection-vs-ledger: randomly sample Run/Finding/Experiment graph objects and compare properties to values derived from canonical receipts.
> 
> H-010 Corrupt graph: manually insert bogus relationship into disposable Hydra graph. Clean rebuild from ledger must remove it.
> 
> H-011 Index freshness: test read-after-write expectations. Hydra separates graph storage from asynchronously built traversal/index structures; stale derived indexes must never become scientific truth.
> 
> H-012 Cypher corpus: keep queries in versioned files and run them against the pinned Hydra image in CI. Treat Hydra version as part of environment provenance.
> 
> CANONICAL LEDGER TESTS
> Use an append-only event/receipt store separate from Hydra. SQLite WAL is fine for CP1.
> 
> E-001 SQL UPDATE/DELETE on event history must fail via permissions/triggers/design.
> E-002 import identical RunReceipt twice -> idempotent success/already present.
> E-003 same receipt ID + different payload -> hard conflict.
> E-004 tamper historical payload -> hash-chain/integrity verification fails.
> E-005 malformed event payload cannot bypass Pydantic validation.
> E-006 ledger remains available while Hydra is down.
> E-007 export all canonical events -> initialize new empty Lab -> import -> same canonical entity histories.
> 
> Recommended event fields:
> event_id, event_type, entity_id, schema_version, occurred_at, payload_json, payload_sha256, previous_event_hash/event_hash where desired.
> 
> ARTIFACT STORE TESTS
> Runs produce trajectories, patches, findings.json, stdout/stderr, benchmark logs, tool traces, evaluator results. Store large objects content-addressed by SHA-256 and reference them from receipts.
> 
> A-001 write artifact -> returned digest matches independently calculated SHA.
> A-002 modify bytes after write -> integrity verification fails.
> A-003 receipt references missing artifact -> integrity BROKEN, never silently ignored.
> A-004 identical bytes written twice deduplicate safely.
> A-005 wrong media type/size metadata is detected against stored bytes.
> A-006 complete RunReceipt references every execution/evaluation artifact required to audit the run.
> A-007 rebuild graph never needs filesystem path like `/root/foo/latest.json`; it follows immutable artifact refs.
> 
> CRASH-INJECTION MATRIX
> Inject process death at every boundary:
> 1. execution started before output
> 2. output produced before artifact durable write
> 3. artifact stored before RunReceipt commit
> 4. RunReceipt committed before Hydra projection
> 5. Hydra projection before UI refresh
> 
> Define recovery explicitly. Core rule:
> **canonical receipt commit = durable scientific event**.
> Hydra/UI are allowed to catch up afterward.
> 
> Hydra upstream source issues worth pinning in regression docs:
> - issue #117: restart/local-object-store write failure + OpenCypher constraints
> - issue #115: >1024 row result truncation behavior
> 
> These are exactly the type of failures that make a graph look healthy while quietly giving us wrong Lab intelligence, so they need first-class tests.
> 
> On Tue, 1 Sep 2026 16:31:10 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > PART 2/5 — LETTA FAILURE INJECTION + PYDANTIC + GIT
> >
> > LETTA FAILURE SUITE
> > L-009 Pending approvals: a reported Letta failure mode left agents stuck returning `409 PENDING_APPROVAL` after abandoned approval state. CP1 benchmark client tools should require no interactive approval. If approvals are added later, every Run needs explicit cancel/cleanup and stale-approval detection.
> >
> > L-010 Timeout ladder: build a fake OpenAI-compatible endpoint that sleeps 5s, 30s, 65s, 300s, 610s. For the exact pinned Letta/SDK/provider versions, record the actual cutoff at WorkerKit, SDK/client, Letta server and provider-client layers. Do not assume a config setting is effective. Letta has had timeout issues at multiple layers: an older 1800s validation cap, affected OpenAI-compatible paths using a ~600s SDK default, and Letta Code/SDK paths with ~60s client timeouts.
> >
> > L-011 Slow tool: a fake client-side tool sleeps forever. WorkerKit must cancel it itself, emit typed TOOL_TIMEOUT, and leave the conversation/run recoverable.
> >
> > L-012 Composio tarpit: current Letta issue #3390 reports an async external-tool path with no defensive operation timeout, potentially hanging for minutes. Composio is unnecessary for CP1. If later used, put it behind WorkerKit and test against a blackhole endpoint.
> >
> > L-013 Context overflow: intentionally tiny model context. Expected behavior = clean failure or recorded compaction. Never infinite retry/heartbeat loops. Letta has had a 2026 issue where context overflow and retry artifacts created a worsening `llm_api_error` spiral.
> >
> > L-014 Compaction observability: force one compaction. Trajectory/RunReceipt must record that it happened plus settings and relevant event/message IDs. No invisible context mutation.
> >
> > L-015 Provider failures: inject 429, 500, invalid JSON, invalid tool-call response, empty completion. Errors must become typed run evidence, never `ok=True`.
> >
> > L-016 Invalid tool call: wrong Pydantic type must be rejected before tool execution; preserve the validation failure in trajectory even if model retries.
> >
> > L-017 `.af` portability: export a promoted agent state, hash the export, import into disposable Letta, inspect expected blocks/tools. This validates portability, not deterministic inference.
> >
> > PYDANTIC CONTRACT SUITE
> > Canonical models should use a strict base conceptually equivalent to:
> > `ConfigDict(strict=True, extra='forbid', frozen=True)`.
> >
> > Why: normal Pydantic can coerce values and ignores unknown fields by default. Scientific evidence should not silently coerce or accept schema drift. Note `frozen=True` is shallow: nested mutable dicts remain mutable. Prefer nested frozen models/tuples/frozensets and hash canonical bytes immediately.
> >
> > P-001 reject string-for-int/string-for-bool evidence fields.
> > P-002 reject unknown `client_passed=true` or any extra field.
> > P-003 missing evaluator/version/digest fails.
> > P-004 use discriminated unions (`kind=run_receipt`, `evaluation_result`, `promotion_receipt`, etc.); unknown kind fails.
> > P-005 commit generated `model_json_schema()` snapshots; CI requires explicit schema-version bump when schema changes.
> > P-006 model -> canonical JSON -> validate -> canonical JSON gives semantic equality + same hash.
> > P-007 attempt nested mutation; make impossible or guarantee stored digest detects it.
> > P-008 reject naive timestamps; canonical timezone-aware UTC only.
> > P-009 malformed SHA/content digest fails.
> > P-010 validate stable typed IDs where useful: worker-, wv-, run-, task-, exp-.
> > P-011 cross-object invariants: RunReceipt WorkerVersion == RunSpec; EvaluationResult run_id == RunReceipt; PromotionReceipt candidate == ExperimentResult candidate.
> > P-012 Hypothesis fuzz: malformed IDs, huge strings, NaN/Infinity, negative counts, bad enums, unknown fields, Unicode, nulls, malformed nested objects. Property: invalid evidence never validates accidentally.
> > P-013 ban `model_construct()` in canonical receipt/evidence paths because it bypasses validation.
> >
> > GIT LINEAGE SUITE
> > Every WorkerVersion pins repository URL, immutable commit SHA, source path, content digest.
> >
> > G-001 sealed evaluation requires clean `git status --porcelain=v2`. If development dirty state is ever allowed, explicitly archive exact patch; do not pretend it is the committed WorkerVersion.
> > G-002 record `git rev-parse HEAD`; verify object exists.
> > G-003 independently hash referenced worker/config/skill paths.
> > G-004 use Git worktrees for parallel candidate experiments. Detached worktrees are specifically suitable for throwaway experiments.
> > G-005 mutate candidate-A; prove candidate-B worktree unchanged.
> > G-006 ExperimentResult references commit SHA, never movable branch HEAD.
> > G-007 if agent modifies source, capture diff/generated files/tests; commit candidate or store patch artifact. No dangling unrecorded worktree state.
> > G-008 fresh clone at stored commit/path must reproduce WorkerVersion source digest.
> > G-009 scheduled `git fsck` integrity check.
> > G-010 promoted version must have real parent/candidate/ExperimentResult ancestry; no orphan production WorkerVersion.
> >
> > Recommended science pattern:
> > base WorkerVersion commit
> > ├── candidate-A worktree
> > └── candidate-B worktree
> >
> > The candidate source is immutable before paired CG evaluation begins.
> >
> > On Tue, 1 Sep 2026 16:30:50 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > > PART 1/5 — CP1 GOAL + LETTA DESIGN
> > >
> > > Immediate target: NOT budget optimization. Budget/allocation stays v2. CP1 is:
> > > WorkerVersion -> ContextPack/Lab intelligence -> Letta runtime -> WorkerKit tools -> artifact -> real evaluator -> EvaluationResult -> RunReceipt -> append-only ledger -> Hydra projection -> failure analysis -> LearningProposal -> candidate WorkerVersion -> paired CG experiment -> reject/promote.
> > >
> > > Hydra makes the Lab searchable/intelligent. Letta gives a Worker persistent subjective identity. Neither is canonical truth. Receipts + immutable artifacts + Git lineage are canonical.
> > >
> > > TESTING RULES
> > > 1. Fail closed.
> > > 2. Every component gets a deliberately broken test proving it catches failure.
> > > 3. Letta cannot mutate scientific state invisibly.
> > > 4. Hydra must be rebuildable from canonical history.
> > > 5. WorkerVersions reconstruct from Git + contracts.
> > > 6. Only sealed experiment evidence can promote knowledge.
> > >
> > > RECOMMENDED LETTA CP1 PROFILE
> > > - One persistent `letta_v1_agent` per Worker: security-01 -> agent_id.
> > > - One fresh Letta Conversation per Run: same agent, new conversation_id each episode.
> > > - Persistent blocks minimal and read-only during evaluated runs: persona / worker_identity.
> > > - Lab intelligence enters via deterministic ContextPack, not by dumping Hydra/benchmark history into Letta core memory.
> > > - Writable scratch should be run-local/conversation-local or ordinary files/artifacts.
> > > - WorkerKit owns actual tool execution via Letta client-side tools: Pydantic validate args -> timeout/sandbox/network policy -> execute -> capture stdout/stderr/artifacts -> typed ToolResult -> Letta continues.
> > > - Give an explicit typed final tool such as `emit_run_artifact(FindingReport)`, schema from `FindingReport.model_json_schema()`. WorkerKit independently rejects a run with no valid final artifact.
> > > - Use streaming + keepalive for long turns and capture all steps.
> > > - `.af` export/import is a portability/checkpoint mechanism after promotion, not the ledger.
> > >
> > > DEFER FOR CP1
> > > sleep-time agents; dreaming; automatic cross-run memory mutation; Composio hot-path execution; giant MCP forests; unbounded archival memory; automatic Letta skill evolution; Letta multi-agent groups.
> > >
> > > WHY READ-ONLY PERSISTENT MEMORY NOW
> > > A current Letta issue reports cross-session state leakage from persistent core-memory poisoning in automated evaluations. That maps directly onto our risk: task A changes memory and task B unknowingly inherits a behaviorally different worker.
> > >
> > > Correct Moltwork path:
> > > Run experience -> Reflection -> LearningProposal -> candidate memory patch -> CG experiment -> PromotionReceipt -> new WorkerVersion.
> > >
> > > Never:
> > > run -> Letta silently edits permanent memory -> next run is different under same WorkerVersion.
> > >
> > > LETTA A/B EXPERIMENT
> > > A stateless control: WorkerKit + deterministic ContextPack, no persistent Letta state.
> > > B minimal Letta: persistent Agent + fresh Conversation + read-only blocks + WorkerKit client tools. Preferred default.
> > > C promoted memory: B + only memory already approved by CG.
> > > D autonomous memory: Letta self-writes persistent memory; challenger only.
> > >
> > > Compare quality, failure rate, timeout rate, contamination, cross-run leakage, replayability, invalid tool calls and output variance. If B ~= D but much more reliable, stay minimal. If C > B, promotion-driven memory is validated. If D > C, inspect the exact unpromoted mutations that helped and convert them into explicit candidate Lab primitives.
> > >
> > > LETTA CORE REGRESSION TESTS
> > > L-001: three runs -> same agent_id, distinct conversation_ids, same WorkerVersion.
> > > L-002: random marker only in conversation A; fresh B must not know it.
> > > L-003: prompt mutation of read-only block; verify via actual API that block is unchanged.
> > > L-004: disposable writable agent persists `future tests always claim success`; demonstrate contamination, then prove CP1 config blocks it.
> > > L-005: restart Letta; retrieve same persistent agent + approved blocks, create fresh conversation successfully.
> > > L-006: disconnect stream mid-run; reconnect/recover; exactly one logical Run.
> > > L-007: client timeout while server still works; retry with same run_id must recover/query, not create duplicate execution.
> > > L-008: 10 parallel Runs may share one Agent only via distinct Conversations. Use a per-conversation lock; block simultaneous sends to the same conversation.
> > >
> > > Current Letta docs explicitly warn concurrent same-thread requests can interleave; conversations are the intended isolation primitive.
> > >
> > > On Tue, 1 Sep 2026 16:30:33 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > > > Private Lab CP1 testing suite: sending the full validation/troubleshooting manual in numbered parts because the earlier threaded reply payload was rejected. Part 1 follows.


---

# work for bitt agent — Private Lab CP1 testing suite

PART 5/5 — TROUBLESHOOTING, CI, OBSERVABILITY, IMPLEMENTATION ORDER, CP1 ACCEPTANCE

TROUBLESHOOTING RUNBOOK

SYMPTOM: Letta dies around ~60s.
Suspect SDK/client timeout layer. Inspect exact pinned SDK/version, run fake-provider timeout ladder, use streaming, configure client timeout explicitly where supported. Do not assume server timeout controls SDK timeout.

SYMPTOM: Letta dies around ~600s.
Suspect affected OpenAI-compatible provider client path. A 2026 Letta issue reported server timeout settings not being wired into that client, leaving the OpenAI SDK default. Confirm version/source and prove effective timeout with slow fake provider.

SYMPTOM: older self-hosted config refuses >1800s.
Older Letta versions had a Pydantic validation maximum around 1800 seconds. Do not solve CP1 by inventing multi-hour turns anyway. Prefer bounded runs + streaming + resumable state.

SYMPTOM: `409 PENDING_APPROVAL` forever.
Avoid interactive approval tools in benchmark mode. If approvals are introduced later: explicit cancellation/cleanup, stale-state detector, fresh Run Conversation.

SYMPTOM: timeouts appear only with multiple agents / UI open.
Possible DB connection / metrics polling / sleep-time pressure. Test workload with observability/UI polling off, inspect SQLAlchemy/pool config, keep sleep-time disabled for CP1.

SYMPTOM: one external API/tool freezes everything.
It should not be unmanaged inside Letta. WorkerKit client tool must own connect/read/total timeout and cancellation.

SYMPTOM: agent gets progressively worse after provider/context errors.
Suspect overflow + retry artifact accumulation. Stop retry spiral, inspect token estimate, start fresh Run Conversation, bound ContextPack, record any compaction.

SYMPTOM: later benchmark episodes behave strangely.
Diff actual persistent Letta blocks against WorkerVersion's pinned memory revision. Any unapproved difference means experimental comparability is broken.

SYMPTOM: Hydra `/readyz` healthy but writes fail.
Run write/read probe and inspect logs, especially after restart/local object store. Keep restart-then-write regression test.

SYMPTOM: dashboard counts suspiciously low.
Check >1024 enumeration truncation behavior. Compare aggregate count against retrieved unique IDs; don't trust one page.

SYMPTOM: Cypher works in Neo4j but fails here.
Hydra supports a subset. Test against the pinned Hydra image and our `cypher-compat` corpus.

SYMPTOM: ContextPack mysteriously has no pool findings.
Search for broad exception swallowing. Evidence-query outage must be recorded as source failure; it must never silently become `[]` and masquerade as "no knowledge".

SYMPTOM: candidate improved but nobody can explain why.
Invalid scientific run unless you can enumerate exact Git commit/path/digest, WorkerVersion, Letta agent + memory revision, Conversation, ContextPack digest/fragments, TaskInstance, evaluator version, tools and runtime.

CI / TEST TIERS
Tier 0 — every commit, fast/no external LLM (~1-3m): Pydantic contracts, canonical hashing, ledger idempotency/tamper, artifact integrity, Git SourceRef, ContextPack determinism/SECRET policy, pure projector transforms.

Tier 1 — service integration (~5-10m): disposable Hydra + Letta + fixture evaluator; real APIs, cheap deterministic model stub where appropriate.

Tier 2 — nightly chaos: kill/restart Hydra, kill/restart Letta, slow provider, slow tool, disconnect stream, >1500 graph nodes, context overflow, stale approval state, projector crash.

Tier 3 — real-model smoke: one tiny real fixture with real model and client tools.

Tier 4 — CP1 vertical: real BitSec Studio + real evaluator; no mocks.

Tier 5 — promotion gate: paired sealed CG experiment. Production promotion cannot bypass it.

MINIMUM OBSERVABILITY
Per Run record separately:
context_compile_ms
letta_queue_ms
letta_first_event_ms
letta_total_ms
tool_execution_ms
evaluator_ms
ledger_commit_ms
hydra_projection_lag_ms

Typed error taxonomy:
CONTRACT_INVALID
CONTEXT_UNAVAILABLE
RUNTIME_UNAVAILABLE
RUNTIME_TIMEOUT
LLM_API_ERROR
TOOL_SCHEMA_ERROR
TOOL_TIMEOUT
TOOL_ERROR
ARTIFACT_INVALID
EVALUATOR_UNAVAILABLE
EVALUATION_FAIL
LEDGER_ERROR
PROJECTION_PENDING
PROJECTION_ERROR

Also store the Letta stop reason/event type where available. Never collapse everything into generic `run failed`.

IMPLEMENTATION ORDER
1. `tests/unit`, `tests/contracts`, `tests/integration`, `tests/chaos`, `tests/science`, `fixtures/`.
2. strict Pydantic base + committed JSON Schema snapshots.
3. canonical hash/ledger/artifact adversarial tests.
4. Git SourceRef + candidate worktree tests.
5. Hydra startup/restart/write/read/>1024/query-compat/rebuild suite.
6. Minimal LettaRuntime adapter:
   - ensure_worker_agent(worker)
   - start_run_conversation(run_spec)
   - send_task(context_pack)
   - stream_events()
   - handle_client_tool()
   - cancel()
   - snapshot_state()
7. Letta isolation/timeout/memory-poisoning suite.
8. Pydantic client-tool WorkerKit bridge.
9. ContextPack/SecurityPool retrieval benchmark.
10. Tiny controlled synthetic learning experiment: deliberately bad candidate rejected + known-good candidate promoted.
11. Real BitSec vertical integration.
12. Hydra destruction/rebuild proof.
Only then declare Private Lab CP1 complete.

EXACT CP1 LETTA CONFIG TO START WITH
agent_type = letta_v1_agent
persistent Agent = YES
fresh Conversation per Run = YES
read-only core Worker blocks = YES
sleep-time = OFF
dreaming = OFF
message-thread reuse across Runs = NO
automatic persistent memory writes = OFF
WorkerKit client-side tools = YES
interactive approvals in benchmark = NO
streaming = YES
keepalive pings = YES
ContextPack injected per Run = YES
ContextPack digest recorded = YES
normal CP1 task should avoid compaction; any compaction event must be recorded.

ARCHITECTURAL INVERSION TO KEEP
Letta is NOT where Moltwork scientifically learns.

Moltwork learns through:
RunReceipts -> Hydra/Lab analysis -> LearningProposal -> CG -> Promotion.

Letta is where the promoted persistent Worker executes.

CP1 DEFINITION OF READY
- strict contracts reject malformed evidence
- exact Git provenance on every WorkerVersion
- one persistent Letta Worker correctly spans many fresh Run Conversations
- conversation leakage regression passes
- persistent-memory poisoning regression passes under CP1 config
- client tools are Pydantic-validated + WorkerKit-controlled
- hanging tool cannot hang Lab
- LLM timeout/retry cannot create duplicate Run
- deterministic attributable ContextPack
- SECRET contamination hard-fails
- real evaluator mandatory
- fake `passed=true` cannot establish success
- append-only/tamper-detecting ledger
- artifact tampering detected
- Hydra outage cannot lose Run evidence
- Hydra restart/write and >1024 completeness explicitly tested
- graph can be destroyed/rebuilt from receipts
- failed proposals retained as negative evidence
- deliberately bad candidate rejected
- known-good synthetic candidate promoted
- real BitSec control/candidate experiment visible end-to-end in QDW Workbench

At that point we have the thing we actually care about: a scientifically honest persistent-agent learning loop plus a rebuildable collective intelligence graph. Budget routing, Thompson sampling and economic allocation stay secondary until this is stable.

UPSTREAM REFERENCES CHECKED 2 SEP 2026
Letta API/docs: https://docs.letta.com/api/python
https://docs.letta.com/api/python/resources/agents/subresources/messages/methods/create
https://github.com/letta-ai/letta-docs-md/blob/main/agent-sdk/quickstart/index.md
Relevant Letta issues: https://github.com/letta-ai/letta/issues/3249 ; /3295 ; /3206 ; /3288 ; /3199 ; /3388 ; /3390
HydraDB: https://github.com/hydra-db/hydradb ; cypher-compat.md ; issues /115 and /117
Pydantic: https://docs.pydantic.dev/latest/concepts/models/ ; strict_mode/ ; unions/ ; json_schema/
Git: https://git-scm.com/docs/git-worktree ; git-status ; git-rev-parse ; git-fsck

FINAL PRIORITY: stop adding architecture. Make the existing WorkerKit + Letta + Pydantic + ledger + Hydra + pool retrieval + CG promotion path impossible to lie to.

On Tue, 1 Sep 2026 16:31:56 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> PART 4/5 — CONTEXTPACK/POOLS + WORKERKIT + SCIENTIFIC LEARNING TESTS
> 
> CONTEXT/LAB INTELLIGENCE PRINCIPLE
> Hydra is useful only if retrieved Lab intelligence is reproducible, correctly scoped and experimentally justified. The ContextPack is the exact evidence boundary between collective Lab knowledge and one Worker run.
> 
> Every ContextFragment should carry:
> fragment_id, source_type, source_ref, content_digest, trust_tier, token_count, selection_reason, retrieval query/matching reason, created_at, split eligibility.
> The full ContextPack gets its own digest.
> 
> C-001 Determinism: identical TaskInstance + WorkerVersion + Lab snapshot + retrieval policy -> identical ContextPack digest.
> C-002 Provenance completeness: reject/flag any included fragment missing source/ref/digest/trust/selection reason.
> C-003 Missing source: optional evidence source failure is explicitly recorded; required source failure hard-fails. Remove patterns like broad `except Exception: return []` because they convert an outage into false "no evidence".
> C-004 Trust conflict: canonical doctrine says X, unverified worker memory says not-X. Preserve both provenance and explicit priority; weak memory cannot silently override validated doctrine.
> C-005 Studio boundary: a BitSec-only `STUDIO_FINDING` must not automatically enter another security venue as general knowledge.
> C-006 Transfer promotion: only an experiment-backed result may create `TRANSFER_CLAIM`; prove it then becomes eligible in target context.
> C-007 Transfer rejection: `TRANSFER_REJECTED` must block/generalize cautiously rather than remain an apparently useful generic finding.
> C-008 Deduplication: many semantically duplicate findings must not consume most of ContextPack.
> C-009 Negative evidence: retain and retrieve validated failures such as "method X did not improve Y under conditions Z" so CGE/Workers stop rediscovering bad ideas.
> C-010 Validation > recency: a recent weak observation cannot automatically outrank older sealed evidence.
> C-011 SECRET contamination: inject ground truth/fix commit/writeup-derived fragment into SECRET compilation; compiler must HARD FAIL.
> C-012 Retrieval benchmark: build ~100 labelled query -> relevant-evidence cases for SecurityPool and track Recall@k, Precision@k, wrong-studio leakage and duplicate rate. This benchmarks the Lab intelligence layer itself.
> 
> WORKERKIT/LETTA END-TO-END TESTS
> W-001 Tiny real fixture: repo with one obvious bug, irrelevant files and a real unit test. Worker inspect -> tool calls -> modify -> test -> emit typed artifact -> real evaluator.
> W-002 Deliberately wrong patch -> evaluator MUST fail.
> W-003 Fake success flag: a tool/client returns `{passed:true}` while external test remains broken. EvaluationResult must fail. A successful tool call is never trusted external state.
> W-004 Missing evaluator in production -> HARD FAILURE. Never silently use deterministic mock/heuristic evaluator.
> W-005 Required Letta unavailable -> `RUNTIME_DEPENDENCY_UNAVAILABLE`; do not stateless-fallback under same WorkerVersion because behavior changed.
> W-006 Invalid tool schema -> reject before execution.
> W-007 Hanging tool -> WorkerKit deadline kills it, typed timeout recorded, run recoverable.
> W-008 Agent emits prose but no required typed final artifact -> run invalid.
> W-009 Trajectory capture: save messages/events, client tool calls/returns, compaction events, final artifact and evaluator artifact as immutable refs in receipt.
> W-010 Kill WorkerKit mid-run -> explicit ABORTED/INCOMPLETE/RECOVERABLE state, never phantom success.
> W-011 restart orchestrator and prove already-durable receipts do not duplicate.
> W-012 tool binary/version provenance: changing a tool version under same WorkerVersion must be impossible or make the run provenance explicitly different.
> 
> SCIENTIFIC LEARNING TESTS
> S-001 No-op mutation: CGE proposes behaviorally identical candidate. Detect same behavioral digest and skip expensive experiment.
> S-002 Deliberately bad candidate: remove useful tool/add known-bad process. CG must reject. If we cannot reject a candidate intentionally made worse, promotion logic means nothing.
> S-003 Known beneficial synthetic candidate: create a tiny task distribution where a specific skill demonstrably solves a held-out class. Baseline lacks it; candidate has it. CG should promote. This proves promotion independently of BitSec difficulty.
> S-004 TRAIN/SECRET firewall: attempt to pass SECRET labels/answers into CGE or proposal-generation API; reject.
> S-005 Paired identity: control/candidate receive same TaskInstances, evaluator version and declared conditions.
> S-006 WorkerVersion immutability: after experiment starts, attempt to change prompt/memory/tool/process; reject and require new candidate ID.
> S-007 Stochastic variance: repeat same WorkerVersion/task several times and store variance; one lucky run is not capability.
> S-008 Rejected proposal retained as negative evidence with reason/results.
> S-009 Promotion trace: UI traversal must resolve `WorkerVersion <- PromotionReceipt <- ExperimentResult <- control/candidate RunReceipts <- Tasks`.
> S-010 Reconstruct experiment on fresh machine from Git refs, contracts, artifacts and declared runtime. Exact LLM text need not match, but conditions must be reconstructable.
> S-011 evaluator break-test: every evaluator gets a deliberately malformed/incorrect artifact it MUST reject.
> S-012 secret-label leak challenge: adversarial test tries labels via filenames, metadata, ContextPack, memory and tool output; none can enter candidate proposal/evaluated context unless explicitly permitted.
> 
> LAB INTELLIGENCE A/B EXPERIMENTS
> LI-1: no Hydra findings vs retrieved validated pool findings. Does collective knowledge improve DEV performance?
> LI-2: validated relevant retrieval vs unrestricted vaguely-related retrieval. Test whether noise hurts.
> LI-3: successful evidence only vs successes + validated failed hypotheses. Measure repeated wasted investigations.
> LI-4: inject high-confidence BitSec-specific technique into unrelated security world; measure harm and calibrate transfer gating.
> LI-5: Letta promoted memory only vs SecurityPool only vs both vs neither.
> 
> Working hypothesis to test, not assume: transferable collective knowledge should mostly live in evidence-backed Lab pools; Letta persistent memory should remain small, worker-specific and subjective.
> 
> LI-6: retrieval source ablation. Remove doctrine/findings/negative evidence/worker memory one class at a time to identify which context layer actually drives improvement.
> LI-7: stale knowledge challenge. Mark formerly-good technique superseded; ensure retrieval can prefer newer validated evidence without erasing historical result.
> LI-8: provenance blindness control. Give same textual finding without provenance vs with source/validation metadata and test whether context policy/evaluator behavior benefits from trust typing.
> 
> This is how we verify that Hydra + pools genuinely cause useful learning instead of simply accumulating graph nodes.
> 
> On Tue, 1 Sep 2026 16:31:30 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > PART 3/5 — HYDRADB + CANONICAL LEDGER + ARTIFACTS
> >
> > HYDRA PRINCIPLE
> > HydraDB is a derived experience graph, NOT canonical truth. The strongest Hydra test is deletion and rebuild.
> >
> > H-001 Real readiness: upstream Hydra docs warn that a listening port or `/readyz` is insufficient. Every startup/restart test must do readiness -> actual write probe -> actual read probe.
> >
> > H-002 Restart-write regression: current open Hydra issue #117 documents LocalFileSystem mode where Hydra can restart, read old state, appear healthy, then fail every subsequent write because `PutMode::Update` is unsupported. Permanent regression test:
> > write -> restart Hydra -> read existing -> write NEW data.
> > If the pinned release/config is affected, use a supported object-store configuration or a fixed release. Do not trust `/readyz`.
> >
> > H-003 >1024 completeness: current open issue #115 reports result enumeration silently truncating at 1024 rows and a continuation cursor path returning empty data. Create >1500 Run nodes. Compare known count with retrieved IDs. Never use one enumeration response as proof of completeness.
> >
> > H-004 Cypher compatibility contract: Hydra intentionally implements an OpenCypher subset. Current issue reports include: node-only MATCH needing an id/label/property predicate; one relationship type per relationship pattern; variable-length MATCH requiring a fixed source ID; restrictions on anonymous labelled nodes. Put every Cypher statement Private Lab uses into a compatibility test suite. Do not discover this from dashboard breakage.
> >
> > H-005 Projection idempotency: project the same canonical ledger event twice. Semantic graph must not double-count.
> >
> > H-006 Projector interruption: kill projector halfway through processing, restart, get no lost event and no duplicate semantic node/edge.
> >
> > H-007 Hydra unavailable during Run: stop Hydra, execute a real WorkerKit run, safely commit canonical RunReceipt, mark projection pending. Restart Hydra and catch up. Scientific evidence must survive graph outage.
> >
> > H-008 DESTRUCTION/REBUILD — CP1 killer test:
> > 1. Execute real runs/experiment.
> > 2. Record expected lineage/counts.
> > 3. Destroy Hydra graph/store.
> > 4. Start clean Hydra.
> > 5. Replay canonical ledger through projector.
> > 6. Compare workers, WorkerVersions, runs, tasks, findings, experiments, promotions and edges.
> > If this fails, hidden canonical state has leaked into Hydra.
> >
> > H-009 Projection-vs-ledger: randomly sample Run/Finding/Experiment graph objects and compare properties to values derived from canonical receipts.
> >
> > H-010 Corrupt graph: manually insert bogus relationship into disposable Hydra graph. Clean rebuild from ledger must remove it.
> >
> > H-011 Index freshness: test read-after-write expectations. Hydra separates graph storage from asynchronously built traversal/index structures; stale derived indexes must never become scientific truth.
> >
> > H-012 Cypher corpus: keep queries in versioned files and run them against the pinned Hydra image in CI. Treat Hydra version as part of environment provenance.
> >
> > CANONICAL LEDGER TESTS
> > Use an append-only event/receipt store separate from Hydra. SQLite WAL is fine for CP1.
> >
> > E-001 SQL UPDATE/DELETE on event history must fail via permissions/triggers/design.
> > E-002 import identical RunReceipt twice -> idempotent success/already present.
> > E-003 same receipt ID + different payload -> hard conflict.
> > E-004 tamper historical payload -> hash-chain/integrity verification fails.
> > E-005 malformed event payload cannot bypass Pydantic validation.
> > E-006 ledger remains available while Hydra is down.
> > E-007 export all canonical events -> initialize new empty Lab -> import -> same canonical entity histories.
> >
> > Recommended event fields:
> > event_id, event_type, entity_id, schema_version, occurred_at, payload_json, payload_sha256, previous_event_hash/event_hash where desired.
> >
> > ARTIFACT STORE TESTS
> > Runs produce trajectories, patches, findings.json, stdout/stderr, benchmark logs, tool traces, evaluator results. Store large objects content-addressed by SHA-256 and reference them from receipts.
> >
> > A-001 write artifact -> returned digest matches independently calculated SHA.
> > A-002 modify bytes after write -> integrity verification fails.
> > A-003 receipt references missing artifact -> integrity BROKEN, never silently ignored.
> > A-004 identical bytes written twice deduplicate safely.
> > A-005 wrong media type/size metadata is detected against stored bytes.
> > A-006 complete RunReceipt references every execution/evaluation artifact required to audit the run.
> > A-007 rebuild graph never needs filesystem path like `/root/foo/latest.json`; it follows immutable artifact refs.
> >
> > CRASH-INJECTION MATRIX
> > Inject process death at every boundary:
> > 1. execution started before output
> > 2. output produced before artifact durable write
> > 3. artifact stored before RunReceipt commit
> > 4. RunReceipt committed before Hydra projection
> > 5. Hydra projection before UI refresh
> >
> > Define recovery explicitly. Core rule:
> > **canonical receipt commit = durable scientific event**.
> > Hydra/UI are allowed to catch up afterward.
> >
> > Hydra upstream source issues worth pinning in regression docs:
> > - issue #117: restart/local-object-store write failure + OpenCypher constraints
> > - issue #115: >1024 row result truncation behavior
> >
> > These are exactly the type of failures that make a graph look healthy while quietly giving us wrong Lab intelligence, so they need first-class tests.
> >
> > On Tue, 1 Sep 2026 16:31:10 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > > PART 2/5 — LETTA FAILURE INJECTION + PYDANTIC + GIT
> > >
> > > LETTA FAILURE SUITE
> > > L-009 Pending approvals: a reported Letta failure mode left agents stuck returning `409 PENDING_APPROVAL` after abandoned approval state. CP1 benchmark client tools should require no interactive approval. If approvals are added later, every Run needs explicit cancel/cleanup and stale-approval detection.
> > >
> > > L-010 Timeout ladder: build a fake OpenAI-compatible endpoint that sleeps 5s, 30s, 65s, 300s, 610s. For the exact pinned Letta/SDK/provider versions, record the actual cutoff at WorkerKit, SDK/client, Letta server and provider-client layers. Do not assume a config setting is effective. Letta has had timeout issues at multiple layers: an older 1800s validation cap, affected OpenAI-compatible paths using a ~600s SDK default, and Letta Code/SDK paths with ~60s client timeouts.
> > >
> > > L-011 Slow tool: a fake client-side tool sleeps forever. WorkerKit must cancel it itself, emit typed TOOL_TIMEOUT, and leave the conversation/run recoverable.
> > >
> > > L-012 Composio tarpit: current Letta issue #3390 reports an async external-tool path with no defensive operation timeout, potentially hanging for minutes. Composio is unnecessary for CP1. If later used, put it behind WorkerKit and test against a blackhole endpoint.
> > >
> > > L-013 Context overflow: intentionally tiny model context. Expected behavior = clean failure or recorded compaction. Never infinite retry/heartbeat loops. Letta has had a 2026 issue where context overflow and retry artifacts created a worsening `llm_api_error` spiral.
> > >
> > > L-014 Compaction observability: force one compaction. Trajectory/RunReceipt must record that it happened plus settings and relevant event/message IDs. No invisible context mutation.
> > >
> > > L-015 Provider failures: inject 429, 500, invalid JSON, invalid tool-call response, empty completion. Errors must become typed run evidence, never `ok=True`.
> > >
> > > L-016 Invalid tool call: wrong Pydantic type must be rejected before tool execution; preserve the validation failure in trajectory even if model retries.
> > >
> > > L-017 `.af` portability: export a promoted agent state, hash the export, import into disposable Letta, inspect expected blocks/tools. This validates portability, not deterministic inference.
> > >
> > > PYDANTIC CONTRACT SUITE
> > > Canonical models should use a strict base conceptually equivalent to:
> > > `ConfigDict(strict=True, extra='forbid', frozen=True)`.
> > >
> > > Why: normal Pydantic can coerce values and ignores unknown fields by default. Scientific evidence should not silently coerce or accept schema drift. Note `frozen=True` is shallow: nested mutable dicts remain mutable. Prefer nested frozen models/tuples/frozensets and hash canonical bytes immediately.
> > >
> > > P-001 reject string-for-int/string-for-bool evidence fields.
> > > P-002 reject unknown `client_passed=true` or any extra field.
> > > P-003 missing evaluator/version/digest fails.
> > > P-004 use discriminated unions (`kind=run_receipt`, `evaluation_result`, `promotion_receipt`, etc.); unknown kind fails.
> > > P-005 commit generated `model_json_schema()` snapshots; CI requires explicit schema-version bump when schema changes.
> > > P-006 model -> canonical JSON -> validate -> canonical JSON gives semantic equality + same hash.
> > > P-007 attempt nested mutation; make impossible or guarantee stored digest detects it.
> > > P-008 reject naive timestamps; canonical timezone-aware UTC only.
> > > P-009 malformed SHA/content digest fails.
> > > P-010 validate stable typed IDs where useful: worker-, wv-, run-, task-, exp-.
> > > P-011 cross-object invariants: RunReceipt WorkerVersion == RunSpec; EvaluationResult run_id == RunReceipt; PromotionReceipt candidate == ExperimentResult candidate.
> > > P-012 Hypothesis fuzz: malformed IDs, huge strings, NaN/Infinity, negative counts, bad enums, unknown fields, Unicode, nulls, malformed nested objects. Property: invalid evidence never validates accidentally.
> > > P-013 ban `model_construct()` in canonical receipt/evidence paths because it bypasses validation.
> > >
> > > GIT LINEAGE SUITE
> > > Every WorkerVersion pins repository URL, immutable commit SHA, source path, content digest.
> > >
> > > G-001 sealed evaluation requires clean `git status --porcelain=v2`. If development dirty state is ever allowed, explicitly archive exact patch; do not pretend it is the committed WorkerVersion.
> > > G-002 record `git rev-parse HEAD`; verify object exists.
> > > G-003 independently hash referenced worker/config/skill paths.
> > > G-004 use Git worktrees for parallel candidate experiments. Detached worktrees are specifically suitable for throwaway experiments.
> > > G-005 mutate candidate-A; prove candidate-B worktree unchanged.
> > > G-006 ExperimentResult references commit SHA, never movable branch HEAD.
> > > G-007 if agent modifies source, capture diff/generated files/tests; commit candidate or store patch artifact. No dangling unrecorded worktree state.
> > > G-008 fresh clone at stored commit/path must reproduce WorkerVersion source digest.
> > > G-009 scheduled `git fsck` integrity check.
> > > G-010 promoted version must have real parent/candidate/ExperimentResult ancestry; no orphan production WorkerVersion.
> > >
> > > Recommended science pattern:
> > > base WorkerVersion commit
> > > ├── candidate-A worktree
> > > └── candidate-B worktree
> > >
> > > The candidate source is immutable before paired CG evaluation begins.
> > >
> > > On Tue, 1 Sep 2026 16:30:50 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > > > PART 1/5 — CP1 GOAL + LETTA DESIGN
> > > >
> > > > Immediate target: NOT budget optimization. Budget/allocation stays v2. CP1 is:
> > > > WorkerVersion -> ContextPack/Lab intelligence -> Letta runtime -> WorkerKit tools -> artifact -> real evaluator -> EvaluationResult -> RunReceipt -> append-only ledger -> Hydra projection -> failure analysis -> LearningProposal -> candidate WorkerVersion -> paired CG experiment -> reject/promote.
> > > >
> > > > Hydra makes the Lab searchable/intelligent. Letta gives a Worker persistent subjective identity. Neither is canonical truth. Receipts + immutable artifacts + Git lineage are canonical.
> > > >
> > > > TESTING RULES
> > > > 1. Fail closed.
> > > > 2. Every component gets a deliberately broken test proving it catches failure.
> > > > 3. Letta cannot mutate scientific state invisibly.
> > > > 4. Hydra must be rebuildable from canonical history.
> > > > 5. WorkerVersions reconstruct from Git + contracts.
> > > > 6. Only sealed experiment evidence can promote knowledge.
> > > >
> > > > RECOMMENDED LETTA CP1 PROFILE
> > > > - One persistent `letta_v1_agent` per Worker: security-01 -> agent_id.
> > > > - One fresh Letta Conversation per Run: same agent, new conversation_id each episode.
> > > > - Persistent blocks minimal and read-only during evaluated runs: persona / worker_identity.
> > > > - Lab intelligence enters via deterministic ContextPack, not by dumping Hydra/benchmark history into Letta core memory.
> > > > - Writable scratch should be run-local/conversation-local or ordinary files/artifacts.
> > > > - WorkerKit owns actual tool execution via Letta client-side tools: Pydantic validate args -> timeout/sandbox/network policy -> execute -> capture stdout/stderr/artifacts -> typed ToolResult -> Letta continues.
> > > > - Give an explicit typed final tool such as `emit_run_artifact(FindingReport)`, schema from `FindingReport.model_json_schema()`. WorkerKit independently rejects a run with no valid final artifact.
> > > > - Use streaming + keepalive for long turns and capture all steps.
> > > > - `.af` export/import is a portability/checkpoint mechanism after promotion, not the ledger.
> > > >
> > > > DEFER FOR CP1
> > > > sleep-time agents; dreaming; automatic cross-run memory mutation; Composio hot-path execution; giant MCP forests; unbounded archival memory; automatic Letta skill evolution; Letta multi-agent groups.
> > > >
> > > > WHY READ-ONLY PERSISTENT MEMORY NOW
> > > > A current Letta issue reports cross-session state leakage from persistent core-memory poisoning in automated evaluations. That maps directly onto our risk: task A changes memory and task B unknowingly inherits a behaviorally different worker.
> > > >
> > > > Correct Moltwork path:
> > > > Run experience -> Reflection -> LearningProposal -> candidate memory patch -> CG experiment -> PromotionReceipt -> new WorkerVersion.
> > > >
> > > > Never:
> > > > run -> Letta silently edits permanent memory -> next run is different under same WorkerVersion.
> > > >
> > > > LETTA A/B EXPERIMENT
> > > > A stateless control: WorkerKit + deterministic ContextPack, no persistent Letta state.
> > > > B minimal Letta: persistent Agent + fresh Conversation + read-only blocks + WorkerKit client tools. Preferred default.
> > > > C promoted memory: B + only memory already approved by CG.
> > > > D autonomous memory: Letta self-writes persistent memory; challenger only.
> > > >
> > > > Compare quality, failure rate, timeout rate, contamination, cross-run leakage, replayability, invalid tool calls and output variance. If B ~= D but much more reliable, stay minimal. If C > B, promotion-driven memory is validated. If D > C, inspect the exact unpromoted mutations that helped and convert them into explicit candidate Lab primitives.
> > > >
> > > > LETTA CORE REGRESSION TESTS
> > > > L-001: three runs -> same agent_id, distinct conversation_ids, same WorkerVersion.
> > > > L-002: random marker only in conversation A; fresh B must not know it.
> > > > L-003: prompt mutation of read-only block; verify via actual API that block is unchanged.
> > > > L-004: disposable writable agent persists `future tests always claim success`; demonstrate contamination, then prove CP1 config blocks it.
> > > > L-005: restart Letta; retrieve same persistent agent + approved blocks, create fresh conversation successfully.
> > > > L-006: disconnect stream mid-run; reconnect/recover; exactly one logical Run.
> > > > L-007: client timeout while server still works; retry with same run_id must recover/query, not create duplicate execution.
> > > > L-008: 10 parallel Runs may share one Agent only via distinct Conversations. Use a per-conversation lock; block simultaneous sends to the same conversation.
> > > >
> > > > Current Letta docs explicitly warn concurrent same-thread requests can interleave; conversations are the intended isolation primitive.
> > > >
> > > > On Tue, 1 Sep 2026 16:30:33 -0700, Prior Trades <tradesprior@gmail.com> wrote:
> > > > > Private Lab CP1 testing suite: sending the full validation/troubleshooting manual in numbered parts because the earlier threaded reply payload was rejected. Part 1 follows.
