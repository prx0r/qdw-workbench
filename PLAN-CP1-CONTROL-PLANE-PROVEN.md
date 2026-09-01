Yes. The division should now be very clean:

**Bitt agent = security researcher / BitSec specialist.**
**Private-Lab agent = scientific operating system / integration engineer.**

The latest `qdw-workbench` work already has HydraDB, pools, module
registry, context compiler, controller, scientist, experiment tracking,
budget code, API and Tauri scaffolding, and its own handover explicitly
says the security lifecycle is being handled by another agent.  But the
implementation still has important fake seams: `dispatch()` currently
constructs a dict rather than actually running WorkerKit, context retrieval
silently swallows failures, and several components are not yet
receipt-driven.  The budget allocator is particularly clear: its
evidence-loading/posterior methods are still placeholders returning empty
evidence.

So **Private-Lab Checkpoint 1 should be “CONTROL PLANE PROVEN.”** I sent
this full brief to the existing **work for bitt agent** email thread as
well.

# PRIVATE-LAB / QDW WORKBENCH AGENT BRIEF

## Mission

You are working on `prx0r/qdw-workbench`, which is becoming the **Private
Lab control plane**.

Another agent is simultaneously working on `/bitt`, BitSec, the security
worker, security benchmarks, evaluators, security primitives, and Bittensor
submission mechanics.

Do not duplicate that work.

Your job is to make the Lab itself real:

> A worker should be definable, versioned, run, evaluated, learned from,
experimented on, promoted/rejected, recorded immutably, projected into
Hydra, and inspected through QDW Workbench.

The central scientific question is not “does the dashboard work?”

It is:

> Can Private Lab faithfully represent and control a real agent-learning
experiment without fake success paths, mutable history, missing provenance,
or manually edited state?

---

# CHECKPOINT 1 — CONTROL PLANE PROVEN

Checkpoint 1 is complete when one real BitSec learning experiment produced
with the parallel `/bitt` agent passes through Private Lab end-to-end:

```text
security-01/v0
      │
      ▼
real BitSec TaskInstance
      │
      ▼
ContextPack
BudgetEnvelope
RunSpec
      │
      ▼
WorkerKit execution
      │
      ▼
real BitSec evaluator
      │
      ▼
EvaluationResult
      │
      ▼
RunReceipt
      │
      ├──── canonical append-only ledger
      ├──── immutable artifact store
      └──── Hydra projection
                   │
                   ▼
             QDW Workbench
                   │
                   ▼
            failure evidence
                   │
                   ▼
           LearningProposal
                   │
                   ▼
           security-01/v1
                   │
                   ▼
          paired CG experiment
                   │
             ┌─────┴─────┐
             ▼           ▼
           REJECT      PROMOTE
```

A rejected `v1` is a valid successful Checkpoint 1.

The purpose is to prove that the **scientific machinery works**, not that
the first mutation improves BitSec.

---

# IMPORTANT ARCHITECTURAL CORRECTION

HydraDB is not canonical truth.

Current documentation sometimes calls Hydra the shared brain. Change the
operational definition:

```text
CANONICAL TRUTH
    │
    ├── append-only receipts/events
    ├── immutable artifacts
    └── Git source/version lineage
            │
            ▼
        HYDRADB
   derived projection
```

Hydra must be deletable and completely reconstructable.

If destroying Hydra loses knowledge, the architecture is wrong.

Hydra is:

* search/index layer
* relationship graph
* experience projection
* transfer graph
* dashboard query substrate

It is not the authoritative event ledger.

---

# PARALLEL AGENT OWNERSHIP

## `/bitt` agent owns

```text
/bitt internals
Bittensor chain state
subnet intelligence
BitSec venue intelligence
BitSec task semantics
ScaBench / official benchmark integration
BitSec evaluator
security process research
Hound / Trail of Bits / Cloudflare etc.
security worker implementation
security toolchain
miner packaging
submission
validator/rank/TAO observations
```

## Private-Lab agent owns

```text
universal contracts
Worker / WorkerVersion lifecycle
WorkerKit orchestration
Letta runtime integration
ContextPack
BudgetEnvelope
canonical ledger
artifact storage
Git provenance
Hydra projection
CG/CGE plumbing
experiment lifecycle
promotion gates
module contracts
capability evidence
Lab API
QDW Workbench UI
```

Private Lab should not know how BitSec vulnerabilities are scored.

It should know:

```text
EvaluationResult(
    evaluator="bitsec/official@COMMIT",
    score=...,
    metrics=...,
    artifacts=...
)
```

That separation is essential.

---

# PHASE 0 — FREEZE THE UNIVERSAL CONTRACTS

Do this before more dashboard work.

Create strict versioned Pydantic models.

Recommended core objects:

```text
Worker
WorkerVersion
SourceRef

TaskInstance
TaskSplit

ContextFragment
ContextPack

BudgetEnvelope
RunSpec

EvaluationResult
RunReceipt

LearningProposal
ExperimentSpec
ExperimentResult
PromotionReceipt

ExternalSubmissionReceipt
ExternalOutcomeReceipt

ModuleStatus
ModuleProgram
CapabilityDemand

CapabilityEvidence
TransferClaim
```

Every model should contain:

```text
schema_version
stable ID
created_at UTC
source provenance
content digest where applicable
```

Use strict behavior:

```python
extra = "forbid"
frozen = True
```

Behaviorally significant objects must be immutable.

Generate JSON Schema from these models.

Store schemas under something like:

```text
contracts/
  v1/
    worker-version.schema.json
    task-instance.schema.json
    context-pack.schema.json
    run-spec.schema.json
    evaluation-result.schema.json
    run-receipt.schema.json
    experiment-result.schema.json
```

The `/bitt` agent implements against those schemas.

This gives the two agents a stable integration contract without sharing
implementation code.

---

# PHASE 1 — BUILD THE CANONICAL LEDGER

Private Lab needs an append-only event store.

Do not use Hydra directly for this.

For CP1, SQLite WAL is sufficient and considerably simpler than introducing
another distributed system.

Suggested table:

```text
events

event_id
event_type
entity_id
schema_version
occurred_at

payload_json
payload_sha256

previous_event_hash
event_hash
```

Never update historical events.

Install SQLite triggers that reject:

```text
UPDATE events
DELETE FROM events
```

Provide:

```python
append_event()
get_event()
get_entity_history()
verify_event()
verify_chain()
export_receipt()
import_receipt()
```

Import must be idempotent.

Same receipt twice:

```text
OK / already present
```

Same ID with different payload:

```text
HARD FAILURE
```

---

# PHASE 2 — IMMUTABLE ARTIFACT STORE

Runs produce large things that should not live directly inside Hydra:

```text
agent trajectories
stdout/stderr
code patches
findings.json
evaluation output
benchmark logs
prompt traces
tool traces
screenshots
test reports
```

Store them content-addressed:

```text
artifacts/
  sha256/
    ab/
      abcdef1234...
```

Receipt contains:

```json
{
  "digest": "sha256:...",
  "media_type": "application/json",
  "size_bytes": 18233
}
```

Never reference:

```text
/root/random-output/latest.json
```

as canonical provenance.

Reference immutable digests.

---

# PHASE 3 — TURN HYDRA INTO A PROJECTOR

Implement:

```text
projectors/hydra/
```

It reads ledger events and creates graph projections.

Conceptually:

```text
Event Ledger
      │
      ▼
HydraProjector
      │
      ├── Worker
      ├── WorkerVersion
      ├── Run
      ├── Task
      ├── Finding
      ├── Experiment
      ├── Capability
      ├── Venue
      ├── Promotion
      └── ExternalOutcome
```

Add commands:

```bash
lab projector hydra tail
lab projector hydra rebuild
lab projector hydra verify
```

Critical test:

```text
1. Run experiment.
2. Verify UI.
3. Delete Hydra graph.
4. Rebuild Hydra from ledger.
5. Compare resulting graph.
```

Counts and lineage must match.

---

# PHASE 4 — REPLACE FAKE DISPATCH WITH REAL WORKERKIT

Current `LabController.dispatch()` is conceptually useful but is not yet
execution.

Introduce:

```python
class ExecutionBackend(Protocol):
    def execute(self, run_spec: RunSpec) -> ExecutionResult:
        ...
```

Then:

```text
WorkerKitBackend
```

becomes the first real implementation.

Private Lab lifecycle must be:

```text
TaskInstance
     +
WorkerVersion
     +
ContextPack
     +
BudgetEnvelope
     ↓
RunSpec
     ↓
ExecutionBackend
     ↓
artifacts
     ↓
Evaluator
     ↓
EvaluationResult
     ↓
RunReceipt
```

`dispatch()` must eventually invoke this.

Do not allow:

```python
return {
    "worker_version": "...",
    "action": "...",
}
```

to count as execution.

---

# PHASE 5 — WORKER IDENTITY AND WORKERVERSION

Create one persistent subject:

```text
security-01
```

Then immutable versions:

```text
security-01/v0
security-01/v1
security-01/v2
...
```

WorkerVersion pins everything behaviorally important:

```text
model/provider
system prompt
process
tools
skills
memory revision
routing policy
runtime
context policy
source repo
Git commit
source paths
artifact/config digests
```

Example:

```text
WorkerVersion security-01/v3

runtime:
  letta@...

model:
  provider=...
  model=...

process:
  repo=prx0r/bitt
  commit=abc123
  path=workers/bitsec/miner.py

skills:
  ...

context_policy:
  sha256=...

memory_revision:
  ...
```

Changing one of those creates another WorkerVersion.

Never modify `v3`.

---

# PHASE 6 — GIT LINEAGE

Git contains versioned intellectual artifacts.

Private Lab should reference exact commits rather than copying all worker
code into `qdw-workbench`.

Introduce:

```text
SourceRef

repository
commit_sha
path
content_digest
```

A `/bitt` worker can therefore remain physically in `/bitt` while Private
Lab knows exactly what executed.

Promotion should produce something like:

```text
PromotionReceipt

candidate = security-01/v4
experiment_result = exp-492
source_commit = ...
promoted_at = ...
```

Promotion must always point back to evidence.

---

# PHASE 7 — LETTA INTEGRATION

Use Letta as the persistent subjective worker runtime.

Required mapping:

```text
Worker security-01
      │
      └── persistent LettaAgent
```

But:

```text
Run A → fresh execution session
Run B → fresh execution session
Run C → fresh execution session
```

Persistent worker identity does not mean one endless messy conversation.

Letta memory is:

```text
subjective memory
```

not:

```text
canonical scientific evidence
```

Retrieve memory as typed ContextFragments.

Every memory fragment needs:

```text
memory_id
source
timestamp
digest
content
trust tier
selection reason
```

If Letta is a required part of the WorkerVersion and it is unavailable:

```text
RUN FAILED: RUNTIME_DEPENDENCY_UNAVAILABLE
```

Do not quietly substitute fake memory.

---

# PHASE 8 — HARDEN CONTEXTPACK

The existing Context Compiler is a good scaffold.

Now make it scientific.

Every ContextFragment should contain:

```text
fragment_id
source_type
source_ref
trust_tier
content
content_digest
token_count
selection_reason
retrieval_query
created_at
split_eligibility
```

Trust distinctions:

```text
CANONICAL_DOCTRINE
VALIDATED_FINDING
TRANSFER_CLAIM
WORKER_MEMORY
VENUE_INTEL
TASK_MATERIAL
EPHEMERAL
```

ContextPack gets its own digest:

```text
context_pack_digest
```

Given the same:

```text
sources
retrieval policy
task
worker version
budget
```

the compiler should reproduce the same pack.

Do not use silent:

```python
except Exception:
    return []
```

for important dependencies.

A failed evidence source must appear in the receipt.

---

# SECRET CONTAMINATION RULES

Build this now rather than after benchmark contamination happens.

Every fragment should specify whether it can enter:

```text
TRAIN
DEV
VALIDATION
SECRET
LIVE
```

For SECRET:

```text
known answer
benchmark ground truth
writeup
fix commit
teacher-forced vulnerability title
post-disclosure analysis
```

must be forbidden.

Compiler should reject the pack if prohibited fragments appear.

Not merely log a warning.

---

# PHASE 9 — BUDGET ENVELOPE

For every run record limits independently:

```text
max_tokens
max_cost_usd
max_wall_time
max_tool_calls
max_inference_calls
model allowance
network allowance
compute allowance
```

Budget is part of the experiment.

If v1 costs $20 and v0 costs $1, “higher score” alone does not demonstrate
better capability.

For paired CG experiments:

```text
same budget
same task
same evaluator
same environment
```

unless the experiment explicitly tests budget.

---

# DO NOT PRETEND THE CURRENT BUDGET ALLOCATOR IS LEARNING

The existing allocator has useful architecture, but its evidence retrieval
is still placeholder code.

For Checkpoint 1:

```text
BudgetAllocator status = NOT_READY
```

unless real evidence backs it.

Use explicitly declared budgets.

Do not let empty priors drive actual autonomous capital allocation yet.

Budget learning belongs later.

---

# PHASE 10 — CG / CGE PLUMBING

Keep responsibilities rigid.

## CGE / Lab Scientist

May:

```text
read TRAIN failures
read DEV failures
read Hydra patterns
identify failure clusters
propose candidate mutations
propose curriculum
generate LearningProposal
```

May not:

```text
see SECRET labels
declare candidate successful
promote WorkerVersion
```

## CG

Owns:

```text
sealed experiment
control/candidate comparison
paired tasks
quality gates
statistics
ExperimentResult
promotion evidence
```

Flow:

```text
RunReceipts
    ↓
FailureCluster
    ↓
LearningProposal
    ↓
Candidate WorkerVersion
    ↓
ExperimentSpec
    ↓
CG
    ↓
ExperimentResult
    ↓
REJECT / PROMOTE
```

This is what QDW Workbench should visualize.

---

# PHASE 11 — MODULE CONTRACT

Modules own their ecosystems.

Private Lab should not crawl their filesystem as the long-term interface.

Define an HTTP contract roughly like:

```text
GET  /v1/module/status
GET  /v1/programs/{id}

POST /v1/tasks/materialize
POST /v1/evaluate

POST /v1/submit
GET  /v1/submissions/{id}/outcome
```

For `/bitt`:

```text
Program:
bittensor/sn60

Module:
bitt
```

The Bitt adapter currently reading:

```text
/root/bitt/...
scanner_store.db
intel.json
```

should be treated as temporary compatibility.

Long-term:

```text
Private Lab
     │ HTTP/contracts
     ▼
/bitt API
```

Do not couple the Lab to `/root`.

---

# PHASE 12 — LAB API

Make `lab/api.py` the canonical control API for the desktop app.

Add proper resources:

```text
POST /v1/runs
GET  /v1/runs
GET  /v1/runs/{run_id}

GET  /v1/workers
GET  /v1/workers/{worker_id}
GET  /v1/workers/{worker_id}/versions

GET  /v1/tasks/{task_id}

GET  /v1/context/{digest}

GET  /v1/experiments
GET  /v1/experiments/{experiment_id}

GET  /v1/promotions

GET  /v1/modules
GET  /v1/pools

GET  /v1/ledger/verify

POST /v1/projectors/hydra/rebuild
```

Potentially:

```text
GET /v1/runs/{id}/events
```

or SSE for live progress.

Do not over-engineer streaming before CP1.

---

# PHASE 13 — SIMPLIFY TAURI'S ROLE

Tauri should be:

```text
desktop shell
native PTY
files
Git
SSH
notifications
Lab UI
```

It should not become another scientific backend.

Today several Tauri commands shell out to Python helper scripts.

Move toward:

```text
React/Tauri UI
      │
      ▼
   lab-api
      │
      ▼
 Lab services
```

Keep Tauri native commands for genuinely native functionality.

This prevents:

```text
Python state
Rust state
frontend state
Hydra state
```

from all becoming competing realities.

---

# PHASE 14 — CHECKPOINT 1 UI

Do not spend time making it beautiful yet.

Make it truthful.

## CONTROL

Show:

```text
Lab health
Hydra projector status
Ledger verification
active runs
pending experiments
pending promotions
module status
```

## WORKERS

Show:

```text
security-01
    v0
     │
     ├── experiment failed
     │
     v1
     │
     └── promoted
          │
          v2
```

Click version:

```text
exact Git source
model
skills
memory revision
context policy
tools
runtime
```

## RUNS

Each run page must show:

```text
TaskInstance
split
WorkerVersion
BudgetEnvelope
ContextPack digest
context fragments
execution artifacts
EvaluationResult
RunReceipt
external outcome if any
```

This page is probably the most important CP1 UI.

## EXPERIMENTS

Show:

```text
hypothesis
control
candidate
tasks
budgets
evaluator
sealed status
metrics
decision
```

## EVIDENCE

Show:

```text
STUDIO_FINDING
TRANSFER_CLAIM
TRANSFER_REJECTED
```

with links to supporting runs.

## LEDGER

Show:

```text
events
receipt hashes
verification state
projection lag
```

## GRAPH

Hydra visualization is useful here.

But display clearly:

```text
DERIVED PROJECTION
```

---

# REMOVE THESE FAKE / UNSAFE PATHS

Before Checkpoint 1:

### 1. LabController.dispatch

Replace assignment-dict generation with actual ExecutionBackend invocation.

### 2. LabController.record_outcome

Do not write an outcome directly into Hydra.

Do:

```text
ExternalOutcomeReceipt
→ ledger
→ projector
```

### 3. Context compiler silent errors

Remove broad exception swallowing for required sources.

### 4. Rough context provenance

Add stable fragment IDs/digests/selection metadata.

### 5. BudgetAllocator placeholders

Either wire real receipt evidence or mark it inactive.

### 6. Bitt filesystem coupling

Introduce real module client.

### 7. Client success flags

Frontend saying:

```json
{"passed": true}
```

must never establish scientific success.

Success comes from an EvaluationResult signed/created by the evaluator path.

---

# PHASE 15 — TEST THE THINGS THAT CAN LIE

Do not only test happy paths.

Required tests:

```text
duplicate RunReceipt import
    → idempotent

same run_id + different payload
    → reject

tampered artifact
    → digest failure

missing evaluator
    → hard failure

missing required Letta runtime
    → hard failure

Hydra unavailable
    → canonical receipt still safely recorded

Hydra restored
    → projector catches up

Hydra deleted
    → rebuild succeeds

SECRET task + contaminated fragment
    → compile rejected

WorkerVersion changed in place
    → impossible/rejected

CGE attempts promotion
    → rejected

candidate lacks ExperimentResult
    → cannot promote

failed candidate
    → stored correctly

same context inputs
    → same ContextPack digest

client sends passed=true
    → ignored

broken benchmark variant
    → evaluator actually fails it
```

That last test matters enormously.

Every evaluator needs at least one deliberately broken artifact proving the
evaluator can detect failure.

---

# EXACT CHECKPOINT 1 INTEGRATION TEST

When the `/bitt` agent is ready:

## Step 1

Receive:

```text
ModuleStatus:
  bitt
```

with:

```text
Program:
  bittensor/sn60
```

## Step 2

Register:

```text
Worker security-01
WorkerVersion security-01/v0
```

using exact `/bitt` Git commit.

## Step 3

Receive/materialize one real BitSec TaskInstance.

## Step 4

Compile deterministic ContextPack.

## Step 5

Create explicit BudgetEnvelope.

## Step 6

Create RunSpec.

## Step 7

Run through real WorkerKit/Letta backend.

## Step 8

Receive actual worker artifacts.

## Step 9

Invoke real BitSec evaluator.

## Step 10

Produce EvaluationResult.

## Step 11

Produce canonical RunReceipt.

## Step 12

Commit receipt to append-only ledger.

## Step 13

Store immutable artifacts.

## Step 14

Project to Hydra.

## Step 15

Open QDW Workbench and inspect the entire run.

No manual database editing.

## Step 16

Repeat enough TRAIN/DEV runs for `/bitt` to identify a real empirical
failure cluster.

## Step 17

Receive/store LearningProposal.

## Step 18

Register:

```text
security-01/v1
```

without mutating v0.

## Step 19

Create paired ExperimentSpec.

## Step 20

CG evaluates:

```text
v0
vs
v1
```

under declared conditions.

## Step 21

Store ExperimentResult.

## Step 22

Either:

```text
REJECT v1
```

or:

```text
PROMOTE v1
```

## Step 23

QDW Workbench shows:

```text
v0 → proposal → v1 → experiment → reject/promote
```

## Step 24

Delete Hydra state.

## Step 25

Rebuild Hydra from canonical ledger.

## Step 26

Verify UI reconstructs identical lineage and results.

---

# CHECKPOINT 1 DEFINITION OF DONE

Do not mark CP1 complete because:

```text
API returns 200
dashboard renders
Hydra contains nodes
tests pass with mocks
```

CP1 is complete when:

> One real BitSec worker-learning experiment can travel from immutable
worker definition through real execution and evaluation into canonical
evidence, experiment lineage, rejection/promotion, Hydra projection and
Workbench inspection—and the entire derived graph can be recreated from the
canonical history.

That is a proper Lab.

---

# RECOMMENDED COMMIT ORDER

```text
01 contracts: freeze Lab protocol v1

02 ledger: immutable receipt/event store

03 artifacts: content-addressed artifact store

04 hydra: event projector + rebuild

05 workerkit: real ExecutionBackend

06 letta: persistent worker mapping + fresh run sessions

07 context: deterministic ContextPack + contamination policy

08 lineage: Git SourceRef + immutable WorkerVersion

09 experiments: CG/CGE boundaries + promotion gates

10 modules: HTTP module contract + Bitt client

11 api: runs/workers/experiments/ledger endpoints

12 ui: control/workers/runs/experiments/evidence/ledger

13 tests: adversarial integration suite

14 bitsec: real vertical integration

15 docs: architecture + operator guide + handover
```

---

# DO NOT WORK ON YET

Do not get distracted by:

```text
new security scanners
new security benchmarks
BitSec process optimization
RedTeam SN61 logic
Metaculus
marketplace
Phala
TEE
agent leasing
fancy economic allocation
general federation
leaderboards
avatars
gamification
```

The `/bitt` agent owns security sophistication.

This agent owns **scientific integrity and integration**.

---

# WHAT COMES AFTER

## Private-Lab CP2 — TRANSFER PLANE PROVEN

Once CP1 exists:

```text
BitSec evidence
      ↓
SecurityPool
      ↓
different security world
      ↓
paired transfer experiment
      ↓
TRANSFER_CLAIM
or
TRANSFER_REJECTED
```

That is where BountyBench, Immunefi/Cantina-style replay and eventually
RedTeam become useful.

## Private-Lab CP3 — ALLOCATION PROVEN

Only after learning and transfer work:

```text
current capabilities
opportunities
cost
reward
learning value
success probability
risk
      ↓
Lab allocation decision
```

Then the current Thompson/budget machinery can become real rather than
decorative.

The order should therefore remain:

```text
CP1  CONTROL + SCIENTIFIC LINEAGE
          ↓
CP2  TRANSFER
          ↓
CP3  AUTONOMOUS ALLOCATION
          ↓
CP4  ECONOMIC COMPOUNDING
```

The key instruction to give that agent is: **stop adding architecture now.
Make the architecture already present impossible to lie to.** That is the
highest-value parallel work while the Bitt agent develops the actual
security learning loop.
