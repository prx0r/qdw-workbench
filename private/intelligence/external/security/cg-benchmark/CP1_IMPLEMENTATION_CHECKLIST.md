# CP1 — First Authorized Security World

## Goal

Prove one complete, deterministic learning loop on a purpose-built benchmark or CTF environment with known ground truth.

## Import

- Pin the upstream benchmark commit/container digest.
- Preserve the benchmark's authoritative evaluator.
- Define deterministic reset behavior.
- Enumerate the exact observations and actions available to the worker.
- Separate worker-visible state from evaluator-only hidden truth.
- Define a resource budget (steps, tool calls, tokens, wall-clock policy).

## CG contracts

- WorldPack ID is content-addressed.
- Scenario ID includes seed and hidden configuration digest.
- WorkerVersion is immutable.
- AssessorVersion is immutable.
- Every event is appended to the canonical trajectory.
- Final RunReceipt commits to all relevant inputs and the event Merkle root.

## Measurements

Collect separately:

- task score;
- reconstruction score;
- confidence/calibration;
- number of observations;
- planning experiments;
- cost;
- latency;
- invalid-action count;
- replay consistency.

## Learning proposal

After the baseline run, require exactly one falsifiable proposal, for example:

- change an observation-selection policy;
- change a reconstruction representation;
- change memory retrieval criteria;
- change planning budget allocation;
- change a prompt/process primitive.

Do not mutate several dimensions at once in CP1.

## Paired evaluation

- Freeze control and candidate WorkerVersions.
- Evaluate both on the same sealed variant set and budget.
- Keep evaluator state hidden from both workers.
- Record all receipts.
- Promote only if the candidate satisfies hard gates and improves the target metric without unacceptable regressions.

## CP1 acceptance

CP1 passes when all of the following are true:

1. Re-running a frozen scenario produces the expected deterministic evidence/receipt semantics.
2. The source benchmark evaluator remains authoritative.
3. Reconstruction can be scored independently of task completion.
4. Hidden evaluation state never enters the worker context.
5. A candidate change can be compared fairly with its control.
6. Promotion/rejection is reproducible from canonical artifacts alone.
7. HydraDB can be deleted and rebuilt from the canonical ledger/artifacts without losing truth.
