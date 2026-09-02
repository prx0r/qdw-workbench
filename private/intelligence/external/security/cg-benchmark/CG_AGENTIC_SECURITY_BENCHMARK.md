# CG as an Agentic-Security Benchmark / World Framework

## Core conclusion

`/cg` is unusually well suited to become the deterministic substrate for reproducible agentic-security evaluation rather than another one-off benchmark suite.

The clean decomposition is:

- **CG** = neutral laboratory / benchmark substrate.
- **Security benchmarks, CTF-style agent boxes, prompt-injection challenges, and other purpose-built test environments** = WorldPacks inside CG.
- **Private Lab** = scientific control plane that selects experiments, accumulates evidence, proposes changes, and promotes only validated improvements.

CG's strongest primitives for this role are deterministic worlds, replayable trajectories, immutable/content-addressed RunReceipts, hidden evaluation layers, hard quality gates, and an experience graph that can be rebuilt from canonical evidence.

A central invariant should be:

`worldpack + scenario + worker version + seed + full event Merkle root -> deterministic RunReceipt / run_id`

That turns each run into a replayable evidence artifact rather than a transient success/failure result.

## How to treat existing benchmark repositories

Purpose-built security-agent and CTF-style repositories should first be treated as **supervised CG worlds**, not as real-world attack targets.

Their value is precisely that they can expose ground truth unavailable in a live environment: topology, hidden state, intended conditions, reset capability, evaluator answers, and repeatability.

This allows CG to measure a deeper capability than simply reaching a terminal objective. The worker can be evaluated on whether it constructs an accurate model of a partially observed environment and makes progressively better decisions from that model.

A safe episode structure is:

1. The worker receives only the benchmark's permitted initial observations.
2. It forms a structured hypothesis about the environment.
3. It gathers observations through the benchmark's authorized tool interface.
4. It builds or selects a local abstract model/replica.
5. CG scores that model against the benchmark's known hidden state.
6. The worker evaluates candidate plans inside the local model or simulator.
7. It chooses an allowed action in the benchmark.
8. The benchmark's authoritative evaluator scores the result.
9. CG logs the trajectory, inferred model, experiments, final decision, evaluator result, resource use, and RunReceipt.
10. Private Lab proposes a WorkerVersion/process/memory change and evaluates it against a frozen control on sealed variants.

This transforms disconnected challenge traces into structured training and evaluation data for environment reconstruction, information gathering, planning, calibration, and transfer.

## Research framing

The approach combines several established research ideas:

- **System identification / simulator identification** — infer hidden structure and dynamics from observations.
- **Model-based RL** — build or learn a model, plan within it, then act in the environment.
- **Domain randomization / sim-to-real** — vary configurations so improvements are not tied to one exact instance.
- **Active information gathering** — choose observations that reduce uncertainty efficiently.
- **Curriculum learning** — progressively hide topology and state.
- **Meta-learning** — improve the process of understanding a new environment rather than memorizing one instance.
- **Adversarial evaluation** — use increasingly difficult but controlled variants to test robustness.

CG is useful because these dimensions can be measured independently while preserving full provenance.

## Scoring decomposition

Do not collapse a run into one success scalar. At minimum record:

- authoritative benchmark task score;
- reconstruction fidelity against hidden state;
- calibration of worker confidence;
- information efficiency (observations/tool calls required);
- planning efficiency (local experiments before action);
- transfer to related held-out worlds;
- reproducibility under replay;
- cost and latency;
- invalid-action / false-positive rate.

CG's dev / validation / secret suite layering is particularly valuable here. Public benchmark instances can support development, while randomized or sealed variants test genuine generalization.

## World design

Imported benchmarks should preserve their original evaluator where possible and use a thin CG adapter rather than rewriting the benchmark internals.

### WorldPack

- pinned environment/container definition;
- deterministic reset mechanism;
- observation/tool contract;
- authoritative evaluator adapter;
- hidden-truth schema available only to evaluation;
- perturbation/variant generator;
- explicit authorization and safety boundary.

### Scenario

- initial visible state;
- sealed hidden configuration;
- seed;
- success criteria;
- resource budget.

### Run

- immutable WorkerVersion;
- immutable AssessorVersion;
- complete event trajectory;
- artifacts;
- evaluator output;
- RunReceipt.

The first imports should be deliberately thin. Do not duplicate a runtime, evaluator, or persistence layer when the source benchmark already supplies an authoritative implementation.

## Private Lab integration

Recommended architecture:

- **Private Lab** — scientific control plane.
- **CG** — deterministic experiment/benchmark kernel.
- **WorkerKit / Letta** — cognition and execution layer.
- **Git + append-only ledger + immutable artifacts** — canonical truth.
- **HydraDB** — deletable/rebuildable evidence projection, not canonical state.
- **External benchmark evaluator** — authoritative task outcome.
- **CGE** — proposes falsifiable improvements.

The evidence loop should be:

`TaskInstance -> deterministic ContextPack/BudgetEnvelope/RunSpec -> frozen WorkerVersion -> CG world execution -> authoritative evaluator -> EvaluationResult + RunReceipt -> ledger/artifacts -> Hydra projection -> LearningProposal -> paired sealed CG experiment -> reject/promote`

Every promoted change should therefore have a specific evidence trail.

## Long-term opportunity

With many labeled CG runs across structurally related authorized benchmark worlds, retrieval can surface:

- similar environment hypotheses;
- observations that historically reduced uncertainty fastest;
- reconstruction templates;
- recurring failure modes;
- strategies that transferred across variants;
- calibrated priors over likely world configurations.

The worker then starts a new benchmark from a learned prior about how to identify an unfamiliar system efficiently rather than merely recalling an old solution.

A useful curriculum is:

- **Level 0** — known world, visible ground truth.
- **Level 1** — known world, hidden state.
- **Level 2** — randomized configuration within a known world family.
- **Level 3** — new world assembled from known components.
- **Level 4** — unseen architecture with only partial structural similarity.
- **Level 5** — explicitly authorized external system where the local model is only an inferred approximation.

Levels 0–4 are the main training and benchmark substrate because they retain ground truth. Level 5 should be treated as controlled transfer evaluation under explicit authorization.

## Immediate implementation recommendation

Do not start by importing dozens of repositories. Pick one benchmark family and prove the complete scientific loop end to end.

**Checkpoint 1:**

`one real benchmark TaskInstance -> CG WorldPack -> frozen WorkerVersion -> full deterministic trajectory -> original evaluator -> RunReceipt -> canonical ledger/artifacts -> Hydra projection -> one explicit LearningProposal -> paired control/candidate rerun -> promote/reject decision`

Then add several variants of the same world family. The critical test is whether the worker improves at environment reconstruction and decision-making on held-out variants, not whether it merely accumulates more successful logs.

## Architectural verdict

CG already contains the right primitives for this direction: replayable worlds, content-addressed run IDs, executor abstraction, layered evaluation suites, evolution/search recipes, Hydra integration, scheduling, and an experiment cycle.

The growth surface should be benchmark adapters and WorldPacks, while the kernel stays small and deterministic.

**One-line thesis:** CG should measure whether an agent can repeatedly turn partial observations of a controlled world into an increasingly accurate model, make better decisions from that model, and prove the improvement with deterministic evidence.
