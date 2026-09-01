# Private Lab — Architecture & Operations Guide

## What is Private Lab?

Private Lab is the **control plane** for Moltwork. It orchestrates modules, pools, and workers to find economic opportunities, learn capabilities, and transfer knowledge across domains.

```
PRIVATE LAB
     │
     ├── modules own their ecosystems
     ├── pools bridge cross-module knowledge
     ├── HydraDB stores empirical evidence
     ├── Git holds promoted capabilities
     └── Letta owns worker cognition
```

## Architecture

### Three Layers

| Layer | What it owns | Example |
|-------|-------------|---------|
| **Module** | Venue-specific intelligence | `/bitt` owns Bittensor, `/oracle` owns market discovery |
| **Pool** | Cross-module capability evidence | Security pool, forecasting pool |
| **Lab** | Cross-module allocation | Which pools get budget, which opportunities to boost |

### Three Granularity Levels

| Level | Example | Who owns it |
|-------|---------|-------------|
| **Program** | Bitsec SN60 | Module (`/bitt`) |
| **Campaign** | Bitsec Round 42 with worker v17 | Module + Private Lab |
| **Run** | One local SCA-Bench evaluation | MWGym/WorkerKit/Hydra |

### The Loop

```
INGEST     Module reports status / Oracle finds opportunity
     ↓
PROFILE    What capabilities does this require?
     ↓
MATCH      Which pools have relevant evidence?
     ↓
VALUE      Given our history, how attractive is it?
     ↓
ALLOCATE   Is it worth spending budget?
     ↓
ASSEMBLE   Build ContextPack from pool evidence
     ↓
DISPATCH   Send assignment to module
     ↓
OUTCOME    Record result in HydraDB
     ↓
LEARN      CGE tests, Git promotes
```

## Key Components

### Module Contract (`lab/modules/`)

Modules report status to Private Lab via standardized models:

```python
ModuleStatus(
    module_id="bitt",
    module_name="Bittensor",
    programs=[ModuleProgram(
        program_id="bittensor/sn60",
        name="Bitsec",
        state="LIVE_COMPETE",
        capability_demand={"security": 0.99, "smart_contract": 0.94},
        our_performance=ModulePerformance(score=0.81, rank=4),
        possible_actions=["train", "submit", "hold"],
    )]
)
```

### Pool Matcher (`lab/pools/matcher.py`)

Matches capability demands to relevant pools using cosine similarity with hierarchical shrinkage:

```python
demand = CapabilityDemand(demands={"security": 0.98, "solidity": 0.84})
matches = match_demand_to_pools(demand)
# → [PoolMatch(pool_id="security", relevance=0.95, evidence_strength=0.7),
#    PoolMatch(pool_id="smart-contract-security", relevance=0.88, evidence_strength=0.5)]
```

### Context Compiler (`lab/context/compiler.py`)

Assembles bounded context packs from pool evidence:

```
SecurityLabBrief (8000 tokens):
  20% doctrine (always included)
  25% findings (relevant to task)
  15% skills (promoted, relevant)
  10% venue intel
  10% worker memory
  15% task content
  5% budget info
```

### Lab Controller (`lab/controller/__init__.py`)

Orchestrates the full loop:

```python
controller = LabController()
controller.ingest_module_status(bitt_status)
match = controller.ingest_opportunity(immunefi_bounty)
decision = controller.allocate(match.opportunity_id, module_id="bitt")
assignment = controller.dispatch(decision)
controller.record_outcome(decision.decision_id, outcome)
```

### Lab Scientist (`lab/scientist/__init__.py`)

Reads evidence, proposes experiments, never judges:

```python
scientist = LabScientist()
analysis = scientist.analyze_pool_performance("security")
# → {"recommendations": ["Many observations but few validated findings..."]}
```

### Module Registry (`lab/modules/registry.py`)

Tracks all modules and their programs:

```python
registry = ModuleRegistry()
registry.register_module(bitt_status)
registry.get_programs_by_state("LIVE_COMPETE")
registry.get_programs_by_pool("security")
```

## HydraDB Graph Structure

### Nodes

```
Worker, WorkerVersion, Run, Studio, TaskInstance, Experiment,
LearningProposal, Finding, CapabilityPool, Venue, Program,
OpportunityMatch, AllocationDecision
```

### Edges

```
HAS_VERSION, RAN, IN_STUDIO, ATTEMPTED, PART_OF, SUPPORTED_BY,
CREATED, VALID_IN, TRANSFERRED_TO, COST, RECEIVED, PRODUCED,
MEMBER_OF (Worker→Pool), CONTRIBUTES_TO (Run→Pool),
EXECUTED_AT (Run→Venue), APPLIES_TO (Finding→Pool),
HAS_VENUE (Pool→Venue)
```

### Write Constraints

- Only `CREATE (a)-[:EDGE]->(b)` works (creates both nodes + edge)
- Node `id` must be integer (`hash_id()` converts strings)
- MATCH is read-only
- Graph is immutable by design

## Security Lab (First Implementation)

### Schools

| School | Venues | Transfer from Bitsec |
|--------|--------|---------------------|
| code-audit | Bitsec, Immunefi, Cantina, Sherlock, Google OSS VRP | 95% |
| ai-redteam | Huntr, HackerOne AI | 60% |
| adversarial-systems | RedTeam SN61 | 50% |

### Markets (14 total)

Bitsec SN60, Immunefi (competitions + bounties), Cantina (competitions + bounties), Sherlock (contests + bounties), Google OSS VRP, Huntr AI Challenges, HackerOne (AI + general), HackenProof, Intigriti, RedTeam SN61, Security Tooling API

### Success Metric

```
VALID_FINDING_RATE × IMPACT × REPRODUCIBILITY × ACCEPTANCE_PROBABILITY
- FALSE_POSITIVE_COST - INFERENCE_COST
```

## Running the Lab

```bash
# Start HydraDB
./scripts/hydradb-setup.sh

# Start Lab API
cd /root/private-lab
python3 -m uvicorn lab.api:app --host 0.0.0.0 --port 8500

# Test pool matching
curl -X POST http://localhost:8500/v1/match \
  -H "Content-Type: application/json" \
  -d '{"demands": {"security": 0.98, "solidity": 0.84}}'

# Test module status
curl -X POST http://localhost:8500/v1/modules/status \
  -H "Content-Type: application/json" \
  -d '{"module_id": "bitt", "module_name": "Bittensor", "programs": []}'
```

## File Structure

```
private-lab/
├── lab/
│   ├── __init__.py
│   ├── api.py                    # FastAPI endpoints
│   ├── contracts/__init__.py     # Pydantic models (all entities)
│   ├── modules/
│   │   ├── __init__.py           # Module contract (ModuleStatus, PoolMatch, etc.)
│   │   └── registry.py          # Module registry
│   ├── pools/
│   │   ├── __init__.py
│   │   ├── matcher.py           # Pool matching (cosine + shrinkage)
│   │   └── security/            # Security pool assets
│   ├── context/
│   │   ├── __init__.py
│   │   └── compiler.py          # Context pack assembly
│   ├── controller/
│   │   └── __init__.py          # Lab controller (full loop)
│   └── scientist/
│       └── __init__.py          # Experiment proposals
├── integrations/hydra/          # HydraDB client
├── studios/                     # Venue adapters (stubs)
├── pools/security/              # Security pool (doctrine, skills, benchmarks)
├── scripts/                     # Setup scripts
├── AGENTS.md
├── ARCHITECTURE-MODULES-2026-09-01.md
├── PLAN-CAPABILITY-POOLS-2026-09-01.md
└── HANDOVER-2026-09-01.md
```
