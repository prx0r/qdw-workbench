# Architecture

## 1. Narrow waist

Workbench exposes QDW; it does not replace QDW. `qdw-node` exposes machine capabilities; it does not decide whether work is good. ACP exposes coding agents; it does not define QDW lifecycle.

```text
Human
  |
Workbench (Tauri)
  |---------------- QDW Bridge ---------------- QDWSystem
  |                                               |-- HumanQueue
  |                                               |-- Products
  |                                               |-- Factories
  |                                               |-- Verification
  |                                               `-- Ledger
  |
  |---------------- qdw-node(s)
  |                    |-- CPU/RAM
  |                    |-- PTY/process
  |                    |-- git/worktrees
  |                    `-- context/handover spool
  |
  `---------------- ACP runtime(s)
                       `-- Hermes first
```

## 2. Why Tauri

The app uses Tauri 2 so the Rust core owns privileged OS operations and the frontend runs in the system WebView. The frontend never receives secrets such as SSH private keys or provider credentials.

## 3. Node federation

Each workstation/VPS runs an optional `qdw-node`. Nodes normally bind only to `127.0.0.1`. The desktop starts SSH forwards such as:

```text
127.0.0.1:19021 -> ssh -> vps-a:127.0.0.1:9902
```

A node advertises *observed* resource state:

- logical CPUs
- one-minute load average
- total/available memory
- disk free/total for configured workspace root
- active child process count
- timestamp and node boot id

The node never claims scheduler suitability. Estate/QDW may derive a route from these observations.

## 4. Workspace identity

A workspace is a configured filesystem path plus native Git information when present: remote URL, branch and commit OID. Workbench does not mint a replacement identity for Git content.

## 5. Context compiler

Inputs:

```text
Task + Workspace + AgentRuntime + TokenBudget + Provider fragments
```

Providers submit `ContextFragment`s with:

- stable provider id
- source URI/native identity
- observed timestamp
- content hash
- estimated token count
- priority
- trust class (`canonical`, `verified`, `observed`, `memory`, `ephemeral`)
- content

The compiler is deterministic for the same fragments and policy. Ordering is trust class, priority, source id. It reserves explicit headroom for the turn itself and returns dropped fragments rather than hiding truncation.

It is a **compiler**, not shared mutable memory.

## 6. Context pressure policy

Default policy:

```text
70%  WARN
82%  PREPARE_HANDOVER
92%  HANDOVER_REQUIRED
```

The UI shows system/tool/skills/memory/repo/task/conversation buckets independently where the runtime supplies them. On PREPARE_HANDOVER, Workbench asks the active agent to produce the structured handover prompt in `docs/HANDOVER_PROTOCOL.md`. The resulting Markdown is sent to qdw-node and stored under `.qdw/handovers/<session>/...` plus a SHA-256 record in node SQLite.

## 7. Agent runtime

ACP stable protocol v1 is the primary boundary. Workbench must negotiate `protocolVersion`; it must not infer wire compatibility from SDK package version. Hermes runs as `hermes acp`, retaining its own memory, skills and provider configuration.

The first implementation keeps ACP in a separate `acp-host` Rust crate so upgrading the official ACP SDK cannot destabilize qdw-node or QDW integration.

## 8. Telemetry

Operational execution events are represented with OpenTelemetry-compatible trace/span identifiers and GenAI-like fields, then stored locally in SQLite. QDW-specific fields are namespaced `qdw.*`.

Telemetry is *not authority*. A successful span does not release a product. QDW receipts/certificates remain the state transition proof.

Cost dimensions remain separate:

```text
cash_usd: Option<f64>
input_tokens
output_tokens
cached_tokens
compute_ms
wall_ms
human_ms
subscription_units: Option<f64>
```

## 9. Human queue

Workbench reads pending actions from QDW and sends decisions through the bridge. The bridge calls `system.human.approve/decline/cancel`, preserving QDW's actor requirement, idempotency and request-payload binding.

Human commentary is stored inside the decision payload so later agents can consume it as provenance-bearing human evidence.

## 10. Gold standards / factory templates

Do not copy Dell directories as a template. Define a versioned factory + verification plan + reference product digest. Dell can be the reference instance for `api-product/v1`; new products must satisfy the conformance contract independently.

## 11. Data locations

```text
~/.config/qdw-workbench/config.toml     desktop configuration
~/.local/share/qdw-workbench/           desktop non-authoritative cache
<workspace>/.qdw/handovers/             handover artifacts
<workspace>/.qdw/context/               optional context manifests
~/.local/share/qdw-node/node.db         node event/usage spool
```
