# PRIVATE LAB — Revised Module Architecture

**Date:** 2026-09-01 (revision)
**Status:** Canonical — supersedes previous centralized Oracle design

---

## The Correction

The previous design had:

```text
Oracle → Security Pool → Bitsec adapter
```

This is too centralized. Bitsec's internal tasks should never become global Oracle opportunities.

## The Correct Architecture

```text
                    ┌────────────────────────┐
                    │      PRIVATE LAB       │
                    │    qdw-workbench       │
                    │                        │
                    │ allocator / scientist  │
                    │ context / budgets      │
                    └──────────┬─────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
 MARKET ORACLE              /BITT                 OTHER MODULE
 external markets       Bittensor specialist
        │                      │
 Immunefi                  Bitt Oracle
 Cantina                       │
 MoltJobs                 subnet selection
 etc.                           │
                         ┌─────┴─────┐
                         ▼           ▼
                      Bitsec       Ridges
                       SN60         SN62
                         │
                    internal rounds
                    local eval
                    miner submission
                    TAO outcomes
        │                      │
        └──────────────┬───────┘
                       ▼
                 CAPABILITY GRAPH
                       │
                 ┌─────┴──────┐
                 ▼            ▼
              SECURITY      CODING
                 │
                 ▼
                    HYDRADB
              empirical evidence
                 │
                 ▼
                   GIT
             promoted capability
                 │
                 ▼
                  LETTA
              worker cognition
```

## Key Principles

### Modules own their ecosystems

| Module | Owns |
|--------|------|
| `/bitt` | Chain state, subnet discovery, economics, registration, wallet, mechanisms, rounds, leaderboards, local reproduction, miner packaging, submission, emissions |
| `/oracle` | External economic programs, jobs, bounties from the internet |
| `/metaculus` | Questions, forecasts, submissions, scoring |
| Future modules | Their own venue-specific intelligence |

### Private Lab owns cross-module allocation

Private Lab does NOT micromanage modules. It receives standardized status and reasons about allocation.

### Capability Pools bridge modules

Knowledge transfers through pools, not through a centralized Oracle. A Bitsec finding about access control enters the Security Pool. An Immunefi bounty draws from the same pool.

## Three Granularity Levels

| Level | Example | Who owns it |
|-------|---------|-------------|
| **Program** | Bitsec SN60 | Module (`/bitt`) |
| **Campaign** | Bitsec Round 42 with worker v17 | Module + Private Lab |
| **Run/Episode** | One local SCA-Bench evaluation | MWGym/WorkerKit/Hydra |

Global Oracle operates at program/opportunity level.
Module operates at campaign level.
WorkerKit/MWGym operates at run level.

## Module Contract

Modules expose a standardized API, not internal databases:

```text
GET  /v1/module/status
GET  /v1/programs
GET  /v1/programs/{id}
GET  /v1/programs/{id}/actions
GET  /v1/programs/{id}/performance
POST /v1/programs/{id}/train
POST /v1/programs/{id}/submit
POST /v1/programs/{id}/allocate
```

Private Lab doesn't know how Bitsec submission works. It receives:

```json
{
  "action": "submit_candidate",
  "program": "bittensor/sn60",
  "worker_version": "sec-v17",
  "estimated_cost_usd": 1.82,
  "estimated_reward_tao": 0.74,
  "confidence": 0.68
}
```

## What Enters Private Lab

Not:

```text
Bitsec benchmark project #813
Bitsec validator job #4928
```

But:

```yaml
program:
  id: bittensor/sn60
  module: bitt
  venue: bitsec

state:
  mode: LIVE_COMPETE
  current_round: 42
  registration_state: registered

economics:
  expected_reward: ...
  marginal_submission_cost: ...
  capital_at_risk: ...

capability_demand:
  security: 0.99
  smart_contract_security: 0.94
  vulnerability_detection: 0.98

our_state:
  worker_version: sec-v12
  sealed_score: 0.81
  external_rank: 4
  recent_delta: +0.07

possible_actions:
  - train
  - submit_candidate
  - hold
  - explore_new_worker
```

## Cross-Module Knowledge Transfer

```
/bitt runs Bitsec
  → capability evidence enters Security Pool in Hydra
  → "sec-v17 strong at access-control, weak at oracle manipulation"

Global Oracle discovers Immunefi bounty
  → bounty requires Solidity + upgradeable protocol + access-control
  → Pool Matcher sees: Security Pool has strong access-control evidence
  → Opportunity gets boosted

Result: Bitsec training improves Immunefi performance
```

## The Two Oracles

| Oracle | Scope | What it does |
|--------|-------|-------------|
| **MarketOracle** (`/oracle`) | Internet-wide | Discovers external jobs, bounties, programs |
| **BittensorIntelligence** (`/bitt/oracle`) | Bittensor-specific | Scans subnets, assesses mechanisms, ranks opportunities |

Private Lab consumes both. They never compete.

## Module Status Format

Each module reports to Private Lab in a standardized format:

```json
{
  "module_id": "bitt",
  "programs": [
    {
      "id": "bittensor/sn60",
      "name": "Bitsec",
      "state": "LIVE_COMPETE",
      "capability_demand": {"security": 0.99, "smart_contract": 0.94},
      "our_performance": {"score": 0.81, "rank": 4, "delta": 0.07},
      "possible_actions": ["train", "submit", "hold"],
      "estimated_costs": {"submit": 1.82, "train": 0.40},
      "estimated_rewards": {"tao": 0.74, "confidence": 0.68}
    }
  ]
}
```

## Pool Matching Happens on Both Sides

A `/bitt` campaign says:

```text
I am consuming:
  security=.98
  smart-contract-security=.91
```

An Immunefi opportunity says:

```text
I require:
  security=.95
  smart-contract=.90
  solidity=.85
```

That's how knowledge crosses the boundary.

## What We're Freezing

1. Modules own their ecosystems. Private Lab does not reach into module databases.
2. Private Lab receives standardized program status, not raw internal state.
3. Capability Pools are the bridge for cross-module knowledge transfer.
4. Three granularity levels: Program → Campaign → Run.
5. Two Oracles: MarketOracle (external) + ModuleIntelligence (internal).
6. Pool matching happens on both sides — modules declare what they consume, opportunities declare what they require.
