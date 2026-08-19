# Testing and Anti-Cheat Contract

The Workbench is specifically prohibited from proving itself with UI snapshots or mocked PASS flags.

## Layers

### L0: static
- `cargo fmt --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- frontend TypeScript typecheck
- Python bridge lint/typecheck

### L1: unit
- deterministic context compilation
- resource parsing
- SHA-256 handover binding
- QDW bridge payload translation
- cost dimensionality (subscription != USD)

### L2: contract
- node HTTP contract against a real spawned `qdw-node`
- QDW bridge against a temporary SQLite fixture matching QDW tables
- approval request must change through QDW HumanQueue adapter, not frontend state
- Git state must be produced by a real temporary Git repository

### L3: adversarial / mutation
Every trust-critical checker has a deliberately broken variant:

- fake node metrics timestamp -> freshness test fails
- handover body mutation after write -> digest verification fails
- approval id reused with altered payload -> bridge/QDW rejects
- fake `VERIFIED` supplied by frontend -> release/status API ignores/rejects it
- context compiler that exceeds token budget -> property test catches it
- cost adapter coercing `None`/subscription to `$0` -> dimensionality test catches it

A green suite against a deliberately broken implementation is a failing test suite.

### L4: live integration
Run on a disposable machine/CI:

1. Build release qdw-node.
2. Measure idle RSS and CPU for 60 seconds.
3. Start a temporary workspace and git repo.
4. Start bridge against an installed QDW checkout.
5. Launch Hermes ACP and negotiate a session.
6. Open/edit a file through the Workbench path.
7. Produce context pressure and a handover.
8. Verify the handover digest and Git OID.
9. Create a real HumanQueue request and approve it through the bridge.
10. Assert the QDW ledger contains the transition.

### L5: release qualification
Release only if:
- all mandatory checks have immutable logs/artifact digests;
- resource budgets are measured, not declared;
- one prior red/failing fixture remains archived to prove the harness catches defects.

## No-cheat rules

- No production code path may branch on `CI=true`, `TEST=true`, fixture names or known test IDs to return success.
- No test may monkeypatch the function whose behavior it claims to prove unless the test explicitly tests the caller's error handling.
- The release certificate must be generated from command receipts and artifact hashes after tests run.
- A test count alone is not evidence. Record command, exit status, code commit and output digest.
- Do not retry a failed live test until green and discard the red run. Archive both.
- Resource claims include machine/OS/kernel/build configuration.
