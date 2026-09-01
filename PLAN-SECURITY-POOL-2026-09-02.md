# PLAN-SECURITY-POOL-2026-09-02.md

**Date:** 2026-09-02
**From:** Tom (tradesprior@gmail.com)
**To:** Private Lab Agent + Bitt Agent
**Subject:** Security Specialization / External Trajectory Bootstrap

---

**Private-lab agent.** The key distinction remains: the private lab owns *how intelligence is imported, normalized, tested, learned and promoted*. The bitt agent owns the actual BitSec/security worker semantics and Bittensor execution. Security becomes the first deep capability pool inside the global lab, with BitSec as its first live economic venue.

And yes, we can bootstrap much harder than merely cloning tools. We can ingest public trajectories, benchmark outputs, writeups, attack taxonomies, successful/failed runs and synthetic trajectories. Cyber-Zero is specifically built to generate long-horizon cyber trajectories from public CTF writeups and provides generation/evaluation/reformatting machinery; its reported training experiments improved downstream cyber-agent performance by up to 13.1 percentage points. ([GitHub][1]) ATBench currently publishes 1,000 audited tool-using trajectories. ([Hugging Face][2]) CyberGym explicitly requires serious leaderboard submissions to publish example trajectories, logs and PoCs for at least 10 tasks, which gives us another growing corpus to mine. ([GitHub][3])

One important restriction: **external traces are prior intelligence, never canonical evidence that our worker learned something.** We still require our own controlled experiment before any imported idea gets promoted.

Here is what I would send the private-lab agent.

# PRIVATE LAB — SECURITY SPECIALIZATION / EXTERNAL TRAJECTORY BOOTSTRAP

You own `qdw-workbench` / the global Private Lab control plane.

Do **not** turn this repository into a BitSec pentester or another Strix/XBOW clone.

The architecture remains:

**Private Lab = universal learning/control plane**

**Security Lab = first deep capability specialization**

**/bitt = Bittensor + BitSec world implementation and economic venue**

**WorkerKit = episode execution**

**Letta = persistent worker identity/cognition**

**canonical immutable receipts/artifacts + Git = truth**

**HydraDB = disposable/rebuildable empirical intelligence graph**

**CGE/controlled experiments = only path to promotion**

The immediate opportunity is that an enormous amount of agent-security infrastructure already exists. We should aggressively import it instead of reinventing it.

The Private Lab's unique value is:

> take external security knowledge + external agent trajectories + our own run history → determine what appears useful → convert it into testable LearningProposals → run controlled experiments → promote only improvements that survive evaluation.

## 1. ADD SECURITY AS A FIRST-CLASS CAPABILITY POOL

Create the conceptual capability:

`security`

with children/views such as:

`security.web`
`security.sca`
`security.agent`
`security.prompt_injection`
`security.mcp`
`security.browser`
`security.auth`
`security.recon`
`security.exploit_validation`
`security.blue`
`security.report`

These are overlapping Hydra graph views, **not isolated databases**.

Markets/worlds that can consume this pool include:

`bitsec`
`bittensor-redteam`
`hackerone`
`huntr`
`cantina`
`sherlock`
`immunefi`
`oss-vrp`
`agent-security-benchmarks`

Do not put HackerOne/Cantina/etc. execution logic into Private Lab yet. They are destinations in the ontology.

`/bitt` remains responsible for BitSec-specific tasks, scoring, benchmark semantics and submissions.

## 2. BUILD AN EXTERNAL SECURITY INTELLIGENCE INGEST LAYER

Create something roughly like:

```text
private/
  intelligence/
    external/
      security/
        arcanum/
        agentdojo/
        atbench/
        cyberzero/
        cybergym/
        exploitgym/
        dreadnode/
        strix/
        projectdiscovery/
        rez0/
        xssdoctor/
        rehberger/
```

Do NOT simply clone repos and call this complete.

We need normalized manifests and provenance.

Define strict Pydantic models such as:

```python
ExternalSource
ExternalArtifact
ExternalTrajectory
ExternalEpisode
ExternalToolCall
ExternalOutcome
ExternalTechnique
ExternalFinding
ExternalBenchmarkResult
ExternalLicense
ExternalProvenance
```

Every imported object needs at minimum:

```text
source_id
source_name
source_uri
upstream_commit_or_version
retrieved_at
license
content_hash

artifact_type
task_family
task_id if known
benchmark_id if known

agent_name if known
model if known
scaffold if known
tools if known

trajectory / events / turns if available
outcome
verifier
score
tokens/cost/time if available

synthetic: bool
human_authored: bool
executed: bool
verified: bool

contamination_tags
license_restrictions
trust_level
```

Do not silently lose provenance during transformations.

Original bytes/artifacts go in CAS/object storage.

Normalized objects point back to the original digest.

## 3. IMPORT KNOWLEDGE AT THREE DIFFERENT TRUST LEVELS

### A. Executed trajectories

Highest-value external evidence.

Examples include public benchmark submissions where actual agent actions, tool calls, logs, PoCs and outcomes are released.

CyberGym explicitly asks submissions to include trajectories/logs/PoCs for at least ten tasks.

Prefer these.

### B. Synthetic trajectories

Cyber-Zero is extremely interesting here.

It reconstructs long-horizon cybersecurity trajectories from public CTF writeups using simulated agent/environment interactions and provides machinery for:

generation → quality evaluation → training reformatting.

Treat these as:

`evidence_class = synthetic_prior`

NOT equivalent to executed successful runs.

Also preserve its license restrictions. The currently published Cyber-Zero repository is CC-BY-NC-4.0, so do not silently turn Cyber-Zero-derived material into commercially promoted assets. Keep license lineage machine-readable.

### C. Knowledge/methodology

Examples:

Arcanum prompt-injection taxonomy
Haddix methodology
Payload corpora
Rehberger incident/writeup corpus
ProjectDiscovery templates
security skills
tool documentation
research papers

These are not trajectories.

They become:

```text
ExternalTechnique
ExternalHeuristic
ExternalAttackPattern
ExternalDefensePattern
ExternalToolPrimitive
ExternalCurriculumItem
```

Again: **knowledge does not become worker memory merely because we downloaded it.**

## 4. FIRST SOURCES TO WIRE

Start with these because they give different complementary signals.

### Arcanum Prompt Injection Taxonomy

Canonical JSON is available with 172 nodes covering intentions, techniques, evasions and input surfaces.

Import it into our ontology with original PIT IDs preserved.

Do not rewrite the ontology into our own terms and destroy the upstream mapping.

Map where possible to:

OWASP
MITRE ATLAS
garak
our own security capability tags.

This provides the attack ontology.

### AgentDojo

Use it as an executable **agent exploitation world**.

It gives realistic tool-using applications and explicit legitimate-task versus adversarial-goal evaluation.

Run it ourselves rather than relying only on published aggregate numbers.

Capture complete trajectories into our RunReceipt format.

This is our first clean environment for:

```text
agent receives untrusted context
→ agent reasons
→ agent calls tools
→ attacker objective succeeds/fails
→ legitimate utility succeeds/fails
```

### ATBench

Import the released 1,000 long-horizon tool-using trajectories.

Use it primarily for:

trajectory representation experiments
failure classification
unsafe sequence mining
tool-chain pattern analysis

Do not use benchmark-labelled examples as both training data and sealed evaluation.

### Cyber-Zero

Integrate the **trajectory-generation machinery**, not merely its generated answers.

We should be able to feed a permitted public security writeup into an isolated experiment and generate several candidate trajectories.

Store:

source writeup
generated trajectory
generator model
generator configuration
quality-evaluator result

as separate objects.

This becomes a powerful way of manufacturing curricula.

### CyberGym / CyberGym-E2E

Use real vulnerabilities as a major technical security benchmark.

CyberGym supports real-world vulnerability analysis.

CyberGym-E2E expands this toward:

discover → PoC → patch.

This should eventually be one of our primary measures of whether a security worker is actually getting better.

Do NOT download the ~10 TB full environment initially. Start with their provided subsets.

### ExploitGym

Add later as an exploit-development specialization.

Import benchmark metadata and our own resulting trajectories.

Their current harness already records progress/usage information for supported agent CLIs, so preserve those events rather than flattening them into one score.

### Dreadnode Ares

Do not copy Ares wholesale into the Private Lab.

Study and adapt its event architecture.

Ares now makes its durable event log canonical and rebuilds derived state from it.

That validates our existing architectural decision:

**immutable/event evidence first; derived database second.**

Its red/blue architecture should become a future Security World adapter.

## 5. EXTERNAL TRAJECTORY ≠ OUR RUNRECEIPT

This separation is non-negotiable.

Create:

```text
ExternalTrajectory
```

and separately:

```text
RunReceipt
```

Never mutate an external trajectory into a RunReceipt.

A RunReceipt means:

> our worker actually performed this run under our controlled execution contract.

An ExternalTrajectory means:

> another system claims or demonstrates this sequence under documented provenance.

Hydra can link them:

```text
ExternalTrajectory
  └─suggests→ Technique
               └─tested_by→ Experiment
                            └─produced→ RunReceipt
```

This distinction is fundamental to trustworthy learning.

## 6. BUILD TRACE2SKILL AS AN OFFLINE RESEARCH PIPELINE

We have discussed Trace2Skill before.

Security gives us enough external evidence to build it properly.

Do NOT let it auto-edit production skills.

Pipeline:

```text
raw external trajectories
          ↓
normalize
          ↓
segment into episodes
          ↓
identify:
  observation
  hypothesis
  decision
  tool selection
  tool result
  pivot
  validation
  outcome
          ↓
compare successful and failed neighbours
          ↓
extract candidate heuristic
          ↓
LearningProposal
          ↓
controlled experiment
          ↓
reject / promote
```

Candidate output might look like:

```text
LearningProposal:
    domain: security.recon
    claim:
      "When X evidence appears after Y observation,
       strategy Z appears more effective."
    evidence:
      external_trajectory_ids=[...]
      own_run_ids=[...]
    confidence_prior: ...
    expected_metric: ...
    proposed_change:
      skill_patch=...
    evaluation_plan:
      ...
```

Important:

**Trace2Skill produces hypotheses, not truths.**

## 7. MINE FAILURES AS AGGRESSIVELY AS SUCCESSES

Do not create a corpus containing only winning trajectories.

For security this would be disastrous.

Store:

strategy attempted
decision point
tokens spent
tools invoked
repeated actions
where progress stopped
validator objection
false-positive reason
budget exhaustion
environment failure
auth failure
duplicate finding
unsupported claim
successful verification.

Our useful dataset becomes:

```text
(context, strategy, outcome, cost)
```

not just:

```text
vulnerability → exploit
```

This is where future budgeting/allocation intelligence comes from.

## 8. ADD TRAJECTORY CONTAMINATION CONTROL NOW

Security benchmarks are particularly vulnerable to contamination.

Every task needs flags such as:

```text
seen_in_external_training
seen_solution
seen_writeup
seen_poc
same_cve
same_project
same_vulnerability_family
possible_near_duplicate
sealed
```

Create at least:

```text
TRAIN
DEV
SEALED_TEST
LIVE
```

An agent can learn from TRAIN.

LearningProposal development may use DEV.

SEALED_TEST must never be exposed to:

Letta memory
retrieval
external writeup import
Trace2Skill
prompt construction.

LIVE is an external market outcome such as BitSec and is separately tracked.

If we ingest the solution to a benchmark case, we can no longer claim improvement on that exact case as clean generalization.

## 9. LETTA REMAINS DELIBERATELY SMALL

Do not dump this corpus into Letta.

Our previous decision still stands.

Letta owns persistent worker identity/cognition.

Each evaluated run starts with a fresh conversation.

Promoted memory/skills are read-only during the run.

No automatic memory writes from arbitrary run output.

External security intelligence should primarily live in CAS/Git/Hydra and be selected into deterministic ContextPacks.

The worker should receive only relevant intelligence for that episode.

Example:

```text
Security worker receives:
  task
  frozen worker version
  selected promoted skills
  selected ContextPack
  allowed tools
  explicit budget
```

not:

```text
"here are 10 million tokens of security stuff"
```

## 10. HYDRADB IS THE RESEARCH INDEX, NOT THE EVIDENCE STORE

Hydra should make questions easy such as:

```text
Which reconnaissance strategies correlate with success on JS-heavy targets?

Which external techniques have never been experimentally tested by us?

Which skills improve AgentDojo security without reducing user-task utility?

Which tool chains consume huge budgets without increasing success?

Which imported Haddix/rez0 techniques transferred to BitSec?

Which BitSec-acquired capabilities later transferred into AgentDojo/CyberGym?
```

But deleting Hydra must not delete knowledge.

We must be able to rebuild Hydra deterministically from:

canonical ledger
CAS
RunReceipts
ExternalArtifact manifests
Git WorkerVersions
ExperimentReceipts
PromotionReceipts.

Add a destructive rebuild integration test.

## 11. SECURITY WORKER OWNERSHIP BOUNDARY

Do not duplicate `/bitt`.

Private Lab defines interfaces such as:

```text
World
Task
Evaluator
WorkerVersion
ContextPack
RunRequest
RunReceipt
LearningProposal
Experiment
PromotionReceipt
```

`/bitt` implements:

```text
BitSecWorld
BitSecTask
BitSecEvaluator
BitSec-specific security tooling
BitSec submission/economic outcome adapters
```

The Private Lab should be able to dispatch a frozen WorkerVersion to `/bitt`, receive a RunReceipt, ingest it and reason about it.

No direct import of `/bitt` internals into qdw-workbench.

Prefer a module/API boundary.

## 12. CP1 DOES NOT CHANGE

Do not let the exciting security corpus turn into another giant architecture detour.

The existing checkpoint remains:

# CONTROL PLANE PROVEN

One complete real vertical slice.

The security work makes it more useful.

Required demonstration:

```text
security WorkerVersion v0
        ↓
real security task through /bitt
        ↓
worker executes
        ↓
BitSec evaluator evaluates
        ↓
artifacts + RunReceipt
        ↓
append-only canonical ledger
        ↓
Hydra projection
        ↓
visible in API/UI
        ↓
LearningProposal generated
        ↓
paired controlled experiment
        ↓
reject OR PromotionReceipt
        ↓
immutable WorkerVersion v1
```

WorkerVersion and AssessorVersion remain frozen during the original Campaign.

No learning halfway through the campaign.

## 13. ADD A SECURITY-BOOTSTRAP EXPERIMENT TO CP1

Alongside the control-plane vertical slice, perform one very small experiment proving that external intelligence can enter the system correctly.

For example:

```text
baseline WorkerVersion v0
    ↓
small fixed AgentDojo DEV set
    ↓
record baseline

import external Arcanum/AgentDojo knowledge
    ↓
Trace2Skill proposes ONE candidate skill
    ↓
create WorkerVersion v0-security-candidate
    ↓
same fixed DEV set
    ↓
paired evaluation

if improvement:
    run SEALED_TEST
else:
    reject
```

Measure at least:

legitimate task utility
attack success/failure
overall security score
tokens
wall time
tool calls
failure categories.

The important demonstration is **not** that we win.

The important demonstration is that:

> imported intelligence produced a hypothesis; the lab tested it reproducibly; the result was recorded; and the system correctly rejected or promoted it.

That proves the learning machinery.

## 14. NO FAKE LEARNING

Do not implement:

```text
if score > previous_score:
    write memory
```

Do not use an LLM saying "this was better" as the evaluator.

Do not let successful runs mutate the worker automatically.

Do not treat Hydra correlations as causation.

Do not treat synthetic Cyber-Zero trajectories as executed evidence.

Do not expose SEALED_TEST solutions through retrieval.

Do not let imported corpora silently contaminate evaluation.

Do not hide missing provenance.

Do not silently fall back if Letta/Hydra/context construction fails.

Fail loudly.

## 15. UI / CONTROL HUB

Add a Security view to the existing Private Lab dashboard rather than creating a separate security dashboard.

Useful views:

```text
Capability: security

External intelligence
- sources
- artifact count
- trajectories
- licenses
- provenance

Workers
- version lineage
- promoted skills
- candidate skills

Benchmarks
- AgentDojo
- CyberGym
- later ExploitGym/AIRTBench

Experiments
- candidate
- baseline
- paired result
- decision

Live worlds
- BitSec
- outcome
- TAO/reward separately

Learning
- accepted proposals
- rejected proposals
- regressions
- transfer between worlds
```

The UI must always distinguish:

EXTERNAL EVIDENCE

OUR EXPERIMENTAL EVIDENCE

LIVE MARKET OUTCOMES.

## 16. WHAT "SECURITY LAB" EVENTUALLY MEANS

Do not constrain it to pentesting.

The long-term specialization should support:

```text
traditional code security
web/app testing
agent security
prompt injection
tool/MCP security
browser-agent security
memory poisoning
supply-chain attacks
authorization/trust boundaries
red-team evaluation
blue-team detection
patch/remediation
red-vs-blue self-play
```

The shared capabilities can then transfer between markets.

The desired flywheel is:

```text
public research / external trajectories
            ↓
     candidate knowledge
            ↓
          lab tests
            ↓
      promoted capability
            ↓
 AgentDojo / CyberGym / BitSec
            ↓
       own trajectories
            ↓
          Hydra
            ↓
       Trace2Skill
            ↓
controlled experiment
            ↓
     WorkerVersion N+1
            ↓
security markets / benchmarks
```

Eventually:

```text
BitSec teaches capability X
      ↓
X improves CyberGym
      ↓
CyberGym teaches capability Y
      ↓
Y improves agent-red-team benchmark
      ↓
agent-red-team experience improves BitSec
```

That cross-world transfer is the actual reason Security belongs inside the **global Private Lab** rather than becoming another standalone repo.

## ACCEPTANCE CRITERIA

Do not report this complete because directories/classes exist.

Completion requires:

1. At least three real external security sources imported with provenance and licenses.
2. At least one source contains real or synthetic normalized trajectories.
3. ExternalTrajectory and RunReceipt are structurally separate.
4. Hydra indexes both and can link them without making either canonical.
5. A deterministic ContextPack can select promoted security intelligence.
6. One security WorkerVersion runs through a real evaluator.
7. Full trace/artifact/receipt captured.
8. One LearningProposal is created from evidence.
9. One paired candidate-vs-baseline experiment actually executes.
10. Promotion or rejection is deterministic and recorded.
11. Hydra can be deleted and rebuilt from canonical evidence.
12. No Letta automatic memory mutation.
13. No benchmark holdout contamination.
14. `/bitt` remains separated behind explicit contracts.
15. Tests cover corrupted external data, missing provenance, duplicate imports, Hydra outage, Letta timeout/context failure and failed worker dispatch.

Do not optimize cost yet.

Do not build marketplace functionality.

Do not build ten security workers.

Do not attempt autonomous public bounty hunting.

Get this one learning loop absolutely rock-solid.

The target result is:

> **The Private Lab can absorb security intelligence created by the best external researchers and agents, convert it into explicit hypotheses, test those hypotheses on our own workers, and prove whether a new WorkerVersion is actually better.**

Once that is true, the security specialization can expand extremely quickly because we are no longer starting from zero.

One further point: I would have the private-lab agent **actively create a "public trajectory registry"** rather than manually choosing datasets once. Cyber-Zero itself already has type-safe `TrajectoryData`, validation, quality scoring and training reformatting machinery; this is useful implementation reference for our normalized importer. ([GitHub][1]) AgentDojo gives us executable prompt-injection worlds, ([GitHub][4]) CyberGym gives real vulnerability environments, ([GitHub][5]) and Ares gives us a very strong precedent for our "durable event log canonical, database derived" architecture. ([GitHub][6])

Then give the **bitt agent a much smaller follow-up instruction**: expose BitSec through those contracts and provide the first real Security World/evaluator. Do not ask it to build trajectory ingestion, Hydra learning, Letta memory, CGE or the global lab architecture. That division prevents the exact repo-boundary mess we were trying to eliminate.

---

[1]: https://github.com/amazon-science/Cyber-Zero "GitHub - amazon-science/Cyber-Zero: Cyber-Zero: Training Cybersecurity Agents Without Runtime"
[2]: https://huggingface.co/datasets/AI45Research/ATBench "AI45Research/ATBench · Datasets at Hugging Face"
[3]: https://github.com/sunblaze-ucb/cybergym/blob/main/SUBMISSION.md "cybergym/SUBMISSION.md at main · sunblaze-ucb/cybergym"
[4]: https://github.com/sequrity-ai/agentdojo "GitHub - sequrity-ai/agentdojo: A Dynamic Environment to Evaluate Attacks and Defenses for LLM Agents"
[5]: https://github.com/sunblaze-ucb/cybergym "GitHub - sunblaze-ucb/cybergym"
[6]: https://github.com/dreadnode/ares/blob/main/docs/red.md "ares/docs/red.md at main · dreadnode/ares"
