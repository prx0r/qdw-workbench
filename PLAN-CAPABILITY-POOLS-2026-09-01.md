# PRIVATE LAB — Capability Pool Architecture & Implementation Plan

**Date:** 2026-09-01
**Status:** Canonical Architecture
**Source:** Tom's Lab architectural spec

---

Yes. I think this is finally the clean architecture.

The critical realization is that **"pool" should not mean a rigid taxonomy category**. It should mean:

> **a reusable body of empirical experience, skills, doctrine, evaluators and priors that may help with this task.**

An opportunity can draw from **zero, one, or several pools**, with different relevance weights. That solves the awkward "coding is enormous" problem.

And `fleece` is highly relevant. Its reusable idea is exactly the one you need: **contextual allocation based on empirical history, with hierarchical borrowing when specific evidence is sparse**. Its Thompson allocator takes a context, actions, outcomes and shared Hydra history and balances exploitation with exploration.  Its school league then does a second layer of allocation across competing strategies/schools and records what survives, dies and transfers.

Do not copy Fleece's Hydra implementation literally — your current HydraDB integration has different write constraints and immutable semantics. Reuse the **decision theory and hierarchy**.

# 1. Yes: Private Lab becomes the system that runs everything

But I would **not physically merge Oracle and WorkerKit into the `qdw-workbench` repository**.

Your own current handover has already made the better decision:

> separate repos as modules; WorkerKit, MWGym and Oracle plug into Private Lab.

So think:

```text
repositories                          runtime

prx0r/qdw-workbench  ───────────────► PRIVATE LAB CONTROLLER
prx0r/mw/oracle      ── module ─────► │
workerkit            ── module ─────► │
mwgym                ── module ─────► │
cge                   ── module ─────► │
bitt                  ── adapter ────► │
fleece                ── library ────► │
                                      │
                                      ├── Letta
                                      ├── HydraDB
                                      ├── Git
                                      ├── Vault
                                      └── qdw-node estate
```

`qdw-workbench` owns:

* orchestration
* contracts
* context compilation
* pool selection
* budget allocation
* human approvals
* state display
* module lifecycle
* routing

Oracle does **discovery/intelligence**.

WorkerKit does **execution + receipts**.

MWGym/CGE do **learning experiments**.

HydraDB does **empirical memory**.

Git holds **promoted assets and lineage**.

Letta owns **individual persistent cognition**.

That separation is strong.

Your existing Workbench architecture already describes itself as a narrow waist/control plane rather than something that should swallow every subsystem.

---

# 2. Stop thinking `Opportunity → one category`

The better representation is:

```text
Opportunity
    ↓
Capability Demand Vector
```

Example Bitsec job:

```yaml
venue:
  type: bittensor
  id: sn60-bitsec

demands:
  security:              0.98
  smart_contract:        0.94
  code_reasoning:        0.87
  solidity:              0.84
  vulnerability_search:  0.96
  evidence_generation:   0.92
  report_writing:        0.63
  fuzzing:               0.44
```

Example Chrome-extension bounty:

```yaml
demands:
  software_engineering:  0.89
  browser_extension:     0.97
  javascript:            0.91
  web_api:               0.60
  security:              0.23
```

Example x402 API:

```yaml
demands:
  software_engineering:  0.88
  api_endpoint:          0.96
  payments:              0.83
  x402:                  0.99
  web_backend:           0.78
```

So there isn't a question:

> "Which one pool does this belong to?"

Instead:

> "Which bodies of experience have useful information for this job?"

That is a much better problem.

---

# 3. Pools should overlap

Start with:

```text
security
software-engineering
research
forecasting
game-dev
data-science
agent-engineering
```

but don't pretend that is the final ontology.

Underneath them you can have narrower scopes:

```text
security
├── smart-contract-security
├── OSS-security
├── web-security
├── AI-agent-security
└── adversarial-security

software-engineering
├── API-development
├── web-apps
├── browser-extensions
├── integrations
├── CLI-tools
└── blockchain-development
```

And crucially:

```text
smart-contract-security
```

can inherit from both:

```text
security
software-engineering
```

Likewise:

```text
x402-api
```

might pull from:

```text
API-development
blockchain-development
payments
agent-engineering
```

There is no reason these have to form a tree.

Make them a **graph**.

---

# 4. A pool is a queryable view over the Lab graph

Don't create separate Hydra databases.

Your current Private Lab explicitly uses **one HydraDB graph across all studios**, with logical isolation by properties.

So:

```text
(:Pool {id:"security"})
(:Pool {id:"smart-contract-security"})
(:Pool {id:"solidity"})
(:Pool {id:"software-engineering"})
```

and knowledge connects to pools:

```text
Finding ──APPLIES_TO────────► Pool
Skill ───VALID_IN───────────► Pool
Run ─────CONTRIBUTES_TO─────► Pool
Worker ──EXPERIENCED_IN─────► Pool
Task ────REQUIRES───────────► Pool
```

But edges need weights:

```text
(Finding)-[:APPLIES_TO {
    relevance: 0.94,
    evidence: 0.88
}]->(Pool)
```

And cross-pool transfer becomes explicit:

```text
(:Pool {smart-contract-security})
    -[:BORROWS_FROM {strength: 0.72}]->
(:Pool {security})
```

This is where Fleece becomes very useful.

---

# 5. Fleece gives you the cold-start solution

One of the strongest things in `pool_thompson.py` is hierarchical shrinkage.

It does not say:

> "We've never seen fish X in regime Y, therefore know nothing."

It combines:

```text
specific history
+
global history
```

weighted by how much specific evidence exists.

Apply that to Moltwork.

Suppose you have never done an Immunefi audit.

You *have* done:

```text
50 Bitsec Solidity runs
15 historical CVE Solidity runs
4 Sherlock replays
```

Then:

```text
P(success | Immunefi, Solidity reentrancy)
```

should borrow heavily from:

```text
smart-contract-security
    +
security
    +
solidity
    +
vulnerability-search
```

rather than defaulting to ignorance.

As real Immunefi outcomes arrive:

```text
venue-specific posterior
```

gradually dominates the generalized prior.

That is extremely elegant.

---

# 6. There are actually TWO allocation problems

Do not combine them yet.

### A. Knowledge allocation

> Which pools should this worker read from?

This happens **per opportunity**.

Cheap.

Example:

```text
Immunefi Solidity bounty

security                0.35
smart-contract-security 0.35
solidity                0.15
exploit-reasoning       0.10
report-writing          0.05
```

This controls ContextPack composition.

### B. Capital allocation

> Which opportunities/pools/studios deserve our $100 this week?

This is a different, higher-level decision.

Example:

```text
current available lab budget = $100

security        $58
forecasting     $14
coding          $18
game-dev        $5
exploration     $5
```

And inside Security:

```text
Bitsec experiments    $22
live Immunefi         $18
Cantina replay        $8
SN61 exploration      $5
security research     $5
```

This is where Fleece's **school league + capital allocation** maps much more directly. Its architecture explicitly ranks competing schools, maintains controls, kills weak strategies without deleting their evidence, and reallocates capital toward stronger performers.

Keep these two allocators separate.

---

# 7. The full Moltwork loop becomes excellent

Imagine Bitsec.

```text
Oracle discovers Bitsec
        ↓
Capability profiler
        ↓
security .98
smart_contract .94
solidity .84
        ↓
Pool Selector
        ↓
Security Pool + SmartContract Pool + Solidity Pool
        ↓
Context Compiler
        ↓
Git doctrine
+ Hydra evidence
+ worker's Letta memory
+ Bitsec venue intel
        ↓
WorkerKit executes
        ↓
Bitsec evaluates
        ↓
WorkerRun receipt
        ↓
Hydra records outcome
        ↓
CGE analyzes improvement proposal
        ↓
experiment
        ↓
promote/reject
```

Now an hour later Oracle discovers:

```text
Cantina bounty:
Solidity protocol
similar access-control architecture
same compiler version
same vulnerability class
```

The system shouldn't merely say:

> Security = security.

It can say:

```text
pool overlap                        very high
historical transfer evidence        high
worker success on analogous tasks   high
toolchain ready                     yes
context assets already available    yes
expected adaptation cost            low

⇒ BOOST OPPORTUNITY
```

That is where Oracle becomes qualitatively better.

---

# 8. Oracle should become performance-aware

Currently Oracle is mostly an external intelligence system:

```text
What money is available?
```

It needs to become:

```text
What money is available
×
what are WE unusually capable of doing?
```

So the Oracle score becomes something like:

```text
OpportunityScore =
    economic_value
  × acceptance_probability
  × capability_match
  × transferable_learning_value
  × strategic_option_value
  × liquidity
  - execution_cost
  - capital_risk
  - human_cost
  - opportunity_cost
```

The new fields are crucial:

```python
capability_match
estimated_success_probability
evidence_strength
nearest_prior_runs
pool_relevance
worker_fit
learning_value
```

Example:

```text
$800 random React job
capability match: .31

$250 security bounty
capability match: .92
previous analogous runs: 44
reusable learning value: .95

Oracle may correctly rank $250 > $800.
```

That's the exact kind of intelligence you want.

---

# 9. Oracle should query Private Lab, not maintain its own model of us

Important boundary.

Don't let Oracle develop a second capability database.

Instead:

```text
Oracle
   │
   │ GET /v1/lab/capability-profile
   │ GET /v1/lab/match/opportunity/{id}
   ▼
Private Lab
   │
   ├── Hydra
   ├── worker metrics
   ├── pool metrics
   └── current assets
```

Oracle owns:

```text
external world state
```

Private Lab owns:

```text
our state
```

Oracle combines the two for prioritization.

---

# 10. WorkerKit should be almost stupid

This is another useful simplification.

WorkerKit should not decide:

> Am I a security worker?

or:

> What memory should I retrieve?

or:

> Should I choose Bitsec instead of Cantina?

WorkerKit gets:

```python
ExecutionAssignment(
    opportunity=...,
    worker=...,
    worker_version=...,
    context_pack=...,
    tools=...,
    budget=...,
    evaluator=...,
)
```

Then it:

```text
executes
records trajectory
records artifacts
records costs
records receipts
returns result
```

Your frozen definition already has this exactly right: WorkerKit is the execution kernel that does the work and records receipts.

Keep it boring.

---

# 11. Private Lab becomes the brain

The control plane now does:

```text
INGEST
  Oracle opportunity

PROFILE
  What capabilities does this require?

MATCH
  Which pools contain relevant experience?

VALUE
  Given our history, how attractive is it?

ALLOCATE
  Is it worth spending budget?

ASSEMBLE
  Build ContextPack

SELECT
  Which WorkerVersion?

EXECUTE
  WorkerKit

EVALUATE
  venue + Harbor + evaluators

LEARN
  Hydra projection

EXPERIMENT
  CGE

PROMOTE
  Git

UPDATE BELIEF
  pool/worker/opportunity priors

RE-RANK
  Oracle
```

That's the product.

---

# 12. Letta now fits even better

Interesting current development: Letta itself now has **Git-backed shared memory repositories** specifically for multiple agents. Multiple cloud agents can attach the same repository, read/edit it using normal Git tools, commit/push changes and synchronize. Letta explicitly distinguishes that from each agent's personal MemFS. ([Letta Docs][1])

So your architecture is aligned with what Letta itself converged toward.

But I would still use Letta shared memory cautiously.

Use it for:

```text
shared working notes
current research
team conventions
living plans
```

Do not treat it as the scientific truth layer.

That remains:

```text
Hydra = evidence
Git main = promoted assets
```

Letta's shared repo can be:

```text
pools/security/shared-working/
```

while:

```text
pools/security/doctrine/
pools/security/skills/
```

are promotion-controlled.

---

# 13. Don't create `security-agent`, `coding-agent`, etc.

Another subtle point.

A **worker is not its pool**.

Example agent:

```text
worker-17

experience:
    security                 .91
    software-engineering     .74
    solidity                 .88
    research                 .42

current assignment:
    Immunefi
```

Next month that same persistent worker may become particularly good at:

```text
smart-contract-security
```

because it accumulated experience there.

Pools are shared intellectual ecosystems.

Workers develop their own capability profile from participation.

This allows specialization to emerge.

---

# 14. And don't force pools to be predefined forever

You had the right intuition.

Start with a modest taxonomy.

Then let Hydra reveal transfer structure.

Suppose over 300 runs you learn that:

```text
Chrome extension work
web scraping
browser automation
```

all strongly transfer to each other.

Then Private Lab might propose:

```text
CandidatePool:
    browser-agent-engineering
```

because tasks in these categories repeatedly benefit from the same:

```text
skills
tools
workers
findings
```

Conversely, perhaps:

```text
security
```

eventually becomes too broad because:

```text
AI red teaming
```

has almost zero transfer to:

```text
Solidity audits
```

Then the system learns to lower the shared coefficient.

You don't need to manually decide.

---

# 15. This becomes a graph-learning problem eventually

At first use rules.

Later you essentially have a bipartite/heterogeneous graph:

```text
Opportunity
Worker
Pool
Skill
Finding
Tool
Venue
ArtifactType
Language
Evaluator
```

with outcomes.

The interesting graph is:

```text
Opportunity ─requires────► Capability
Worker ──────has─────────► Capability
Finding ─────helps───────► Capability
Skill ───────valid_in────► Capability
Run ─────────used────────► Skill
Run ─────────attempted───► Opportunity
Run ─────────result──────► Outcome
```

Eventually the question:

> Which pools/context should I provide?

can literally be learned from historical success.

But **do not start with GNNs**.

Fleece itself has useful evidence here: its GAT experiment lost to simpler scoring, which is one reason its current architecture emphasizes explicit/bayesian allocators.

Start interpretable.

---

# 16. Proposed core contracts

Add these to `qdw-workbench/lab/contracts`.

```python
class CapabilityRef(BaseModel):
    id: str
    weight: float
    confidence: float
    source: str


class CapabilityProfile(BaseModel):
    capabilities: list[CapabilityRef]


class PoolManifest(BaseModel):
    pool_id: str
    name: str
    parent_pools: list[str] = []
    capability_centroid: dict[str, float] = {}
    git_root: str
    context_policy: str
    evaluator_ids: list[str] = []


class PoolMatch(BaseModel):
    pool_id: str
    relevance: float
    evidence_strength: float
    transfer_prior: float
    reasons: list[str]


class OpportunityMatch(BaseModel):
    opportunity_id: str
    capability_profile: CapabilityProfile
    pool_matches: list[PoolMatch]
    nearest_runs: list[str]
    candidate_workers: list[str]
    estimated_success: float
    estimated_cost_usd: float
    estimated_reward_usd: float
    learning_value: float


class AllocationDecision(BaseModel):
    opportunity_id: str
    worker_id: str
    budget_envelope_id: str
    selected_pools: list[PoolMatch]
    reason: str
```

That becomes the narrow waist.

---

# 17. Hydra schema expansion

Current Hydra creators only cover Worker, Run, Experiment, Finding and LearningProposal.

Next schema:

```text
Pool
Capability
Opportunity
Venue
SkillVersion
ContextPack
ExternalOutcome
AllocationDecision
```

Edges:

```text
Worker -[:HAS_EXPERIENCE]-> Pool
Pool -[:CONTAINS]-> Capability

Opportunity -[:REQUIRES]-> Capability
Opportunity -[:OFFERED_AT]-> Venue

Run -[:ATTEMPTED]-> Opportunity
Run -[:DREW_FROM]-> Pool

Finding -[:APPLIES_TO]-> Pool
SkillVersion -[:VALID_IN]-> Pool

Finding -[:TRANSFERRED_TO]-> Pool

AllocationDecision -[:FUNDED]-> Run
```

Remember Hydra's current immutable constraints: every state transition becomes new evidence rather than destructive updates. Your current integration explicitly freezes that model.

Good.

---

# 18. Context compilation

Your QDW architecture already has a deterministic Context Compiler with trust classes, priorities, stable source IDs and explicit token budgeting.

Extend provider sources:

```text
TaskProvider
VenueProvider
PoolDoctrineProvider
PoolFindingProvider
PoolSkillProvider
WorkerMemoryProvider
NearestRunProvider
BudgetProvider
HumanFeedbackProvider
```

For Bitsec:

```text
12k context budget

25% task/repo
20% security doctrine
20% nearest smart-contract findings
15% promoted skills
10% Bitsec venue intel
5% worker personal memory
5% budget/current plan
```

Dynamic, not fixed forever.

And record what was actually included.

That lets you later ask:

> Did including pool X actually improve outcomes?

Very important.

---

# 19. Pool selection v0 → v1 → v2

Don't overengineer first version.

### V0: deterministic matching

Use structured tags.

```text
exact capability match      +3
parent capability match     +1
same language               +2
same artifact type          +2
same venue                  +1
verified transfer finding   +3
```

Top 1–3 pools.

### V1: empirical weighted matching

Hydra provides:

```text
how often did context from pool X help task type Y?
```

Estimate:

```text
P(improvement | pool X, task context)
```

### V2: contextual Thompson sampling

Directly adapt the conceptual model from Fleece.

There:

```text
context = market regime
action  = fish
reward  = PnL
```

Here:

```text
context = opportunity capability profile
action  = pool/context mix
reward  = evaluation improvement / economic outcome
```

Then pool selection naturally explores occasionally.

---

# 20. Add an exploration budget

This matters once the lab starts earning.

If you allocate 100% toward what currently looks best, you get trapped.

Use something like:

```text
70% exploit
20% adjacent exploration
10% frontier
```

So Security might currently dominate.

But:

```text
$70 → proven Security opportunities
$20 → adjacent things like RedTeam / OSS
$10 → unrelated promising new pool
```

Fleece's Thompson sampling has exactly the desirable property: uncertain options continue receiving enough allocation to gather evidence.

---

# 21. Budget should eventually flow at multiple levels

Eventually:

```text
LAB BUDGET
   │
   ├── Security pool
   │      ├── Bitsec
   │      ├── Immunefi
   │      ├── Cantina
   │      └── experiments
   │
   ├── Forecasting pool
   │      ├── Metaculus
   │      └── other
   │
   └── Software pool
          ├── MoltJobs
          ├── Algora
          └── agent markets
```

But don't literally allocate by pool first.

A better solver eventually evaluates individual candidate actions:

```text
action:
"spend $1.80 and 45 mins evaluating worker sec-v12
on Bitsec replay #17"

action:
"spend $4.50 and 2 hours attacking Immunefi opportunity X"

action:
"spend $0.40 assessing a new MoltJobs API bounty"
```

Then pools are a source of priors.

This prevents weird accounting when one opportunity belongs to 4 pools.

---

# 22. Your allocator is actually scheduling experiments + work

This is more interesting than ordinary portfolio allocation.

Each candidate has two potential returns:

```text
economic_return
learning_return
```

So:

```text
Utility =
    expected_money
  + λ × expected_information_gain
  + μ × strategic_transfer_value
  - expected_cost
  - risk
```

Bitsec may have only moderate immediate revenue but huge:

```text
learning value
benchmark value
transfer value
```

Therefore the Lab funds it.

That's rational.

---

# 23. Fleece Orca maps onto the future Lab Scientist

Another valuable piece of Fleece is `Orca`.

Importantly, Orca is deliberately:

> **generator, never judge**.

It reads control gaps, failures and trait evidence from Hydra and proposes experiments, while deterministic evaluation decides whether those proposals are valid.

That is exactly what your global Lab Scientist should do.

Rename the concept, not necessarily the code:

```text
Lab Scientist

reads:
  Hydra findings
  pool performance
  Oracle opportunity distribution
  budgets
  graveyard/rejected experiments

proposes:
  try security skill X
  split pool Y
  merge pool A/B
  test Bitsec learning on Cantina
  increase security exploration budget

NEVER:
  declares itself correct
```

MWGym/Harbor/evaluators remain judges.

Excellent architecture.

---

# 24. Repo layout I would converge on

```text
qdw-workbench/
│
├── lab/
│   ├── contracts/
│   ├── controller/
│   │   ├── ingest.py
│   │   ├── match.py
│   │   ├── allocate.py
│   │   ├── dispatch.py
│   │   └── outcome.py
│   │
│   ├── pools/
│   │   ├── registry.py
│   │   ├── matcher.py
│   │   ├── allocator.py
│   │   └── context.py
│   │
│   ├── scientist/
│   │   ├── propose.py
│   │   └── experiment_queue.py
│   │
│   └── context/
│
├── pools/
│   └── security/
│       ├── manifest.yaml
│       ├── doctrine/
│       ├── skills/
│       ├── evaluators/
│       ├── playbooks/
│       └── benchmarks/
│
├── venues/
│   ├── bittensor/
│   │   ├── sn60.py
│   │   └── sn61.py
│   ├── immunefi.py
│   └── cantina.py
│
├── integrations/
│   ├── oracle/
│   ├── workerkit/
│   ├── mwgym/
│   ├── hydra/
│   ├── letta/
│   └── cge/
│
└── apps/
```

Note I changed:

```text
studios/
```

to conceptually:

```text
venues/
```

You don't have to rename it immediately.

But I would stop using "Studio" for both capability and external environment.

---

# 25. Full implementation sequence

This is what I would hand to the coding agent.

### Phase 0 — Freeze terminology

Write one ADR:

```text
ADR-POOL-001

Pool       = shared capability/experience scope
Venue      = external earning/evaluation surface
World      = controlled evaluation environment
Worker     = persistent acting agent
Campaign   = coordinated attempt at an opportunity
Oracle     = external opportunity intelligence
PrivateLab = allocator/controller
```

No more ambiguity.

### Phase 1 — Contracts

Add:

```text
CapabilityProfile
PoolManifest
PoolMatch
OpportunityMatch
AllocationDecision
PoolContribution
TransferEvidence
```

to the canonical QDW contracts.

Update `RunSpec` with:

```python
pool_matches: list[PoolMatch]
opportunity_id: str
venue_id: str
```

Do not delete `studio_id` yet.

### Phase 2 — Security Pool

Implement one pool only:

```text
pools/security/
```

Manifest plus initial skill/docs.

No Forecasting pool rewrite yet.

Security is the integration test.

### Phase 3 — Oracle normalization

Every Oracle opportunity must output:

```text
venue
reward
deadline
artifact type
languages
capability profile
verification mechanism
risk
agent autonomy
```

Add `/security` as UI filter, but internally use full capability profiles.

### Phase 4 — Oracle ↔ Lab API

Private Lab endpoints:

```text
POST /v1/opportunities/ingest
POST /v1/match
GET  /v1/pools
GET  /v1/pools/security
GET  /v1/workers/capabilities
POST /v1/allocate
```

Oracle calls `/match` before final ranking.

### Phase 5 — Hydra pool schema

Add:

```text
Pool
Capability
Opportunity
Venue
```

and graph projection functions.

Add queries:

```text
nearest_runs(opportunity)
findings_for_profile(profile)
skills_for_profile(profile)
worker_fit(profile)
pool_transfer_stats(source,target)
```

### Phase 6 — Context Compiler

Create the pool providers.

Compile one reproducible:

```text
SecurityLabBrief
```

for a Bitsec task.

Hash it.

Record the exact ContextPack in RunSpec.

### Phase 7 — WorkerKit adapter

Private Lab creates Assignment.

WorkerKit executes Assignment.

WorkerKit returns immutable receipt.

No intelligence in WorkerKit.

### Phase 8 — Bitsec end-to-end

The checkpoint:

```text
Oracle Bitsec opportunity
→ Security pool match
→ ContextPack
→ Letta worker
→ WorkerKit
→ Bitsec local evaluator
→ RunReceipt
→ EvaluationResult
→ Hydra
```

Nothing mocked.

### Phase 9 — Learning

Turn failed/successful runs into:

```text
LearningProposal
Finding
```

Run CGE control vs candidate.

Promote into Git only when evaluator says yes.

### Phase 10 — Cross-venue transfer

Add historical Cantina/Immunefi evaluation.

Take a **Bitsec-derived promoted skill** and run:

```text
control without skill
vs
candidate with skill
```

on non-Bitsec tasks.

This proves the entire pool thesis.

### Phase 11 — Performance-aware Oracle

Now Oracle asks:

```text
What's available?
+
What have we become good at?
```

Rank similar security opportunities higher.

### Phase 12 — Fleece allocator adaptation

Only after you have actual outcomes.

Implement:

```text
PoolContextAllocator
```

inspired by ThompsonPoolAllocator.

Don't make this a dependency on the Fleece trading package.

Extract a generic tiny library:

```text
allocation/
    posterior.py
    thompson.py
    hierarchical.py
```

Then both Fleece and Private Lab could eventually consume it.

### Phase 13 — Budget allocator

Once several real opportunity types exist:

```text
expected money
expected learning
strategic transfer
cost
risk
```

Allocate budget across actions.

### Phase 14 — Emergent pool proposals

Lab Scientist can propose:

```text
split security
merge browser-extension + browser-automation
create x402-service-engineering
```

but requires an experiment demonstrating that the proposed grouping improves retrieval/routing.

---

# 26. The first killer demo

Don't build 12 pools.

Build this:

```text
1. Bitsec task enters Oracle.

2. Oracle classifies:
   security / smart-contract / solidity.

3. Lab routes to Security Pool.

4. Worker receives relevant shared Security experience.

5. Worker executes Bitsec.

6. Score recorded.

7. Lab discovers:
   "auth-first review improved score."

8. CGE validates it.

9. Skill promoted to Security pool Git.

10. Oracle discovers an unrelated Cantina/Immunefi task
    with matching capability fingerprint.

11. It gets unusually high OpportunityScore
    because Lab knows our demonstrated capability.

12. A worker receives the Bitsec-derived skill.

13. It performs better than control on the new venue.

14. Hydra records TRANSFER_CLAIM.
```

If you make **that exact loop real**, you have demonstrated nearly the complete Moltwork thesis.

Not a marketplace.

Not an agent framework.

Not a memory database.

A system that:

> **finds economic environments, learns capabilities in one environment, recognizes where those capabilities transfer, reallocates attention and money toward those opportunities, and empirically gets better.**

Security is an exceptionally good first domain because you already have Bitsec as the training/evaluation engine, many economically meaningful adjacent venues, and objective enough outcomes to tell whether the "hive mind" is actually improving rather than merely accumulating notes.

The next engineering move should therefore be **Pool/Capability contracts + Security Pool + Oracle→Lab match API**, before touching more sophisticated CGE evolution or multi-domain allocation. Once that narrow waist exists, everything else has an obvious place.
