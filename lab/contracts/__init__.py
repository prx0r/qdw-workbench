"""Lab Contracts — Frozen Pydantic models for the Moltwork Lab.

From spec §10: All cross-module interfaces exchange these contracts.
Do not pass mystery dictionaries through the Lab.

CRITICAL: These contracts are the integration boundary between agents.
The /bitt agent implements against these schemas.
Do not mutate published models — create new versions instead.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, ConfigDict


SCHEMA_VERSION = "1.0.0"


# ─── Enums ─────────────────────────────────────────────────────────────

class Split(str, Enum):
    TRAIN = "TRAIN"
    DEV = "DEV"
    VALIDATION = "VALIDATION"
    SECRET = "SECRET"
    LIVE = "LIVE"


class RunMode(str, Enum):
    REPLAY = "REPLAY"
    SHADOW = "SHADOW"
    LIVE = "LIVE"


class ExperimentStatus(str, Enum):
    DESIGNED = "DESIGNED"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    DISPUTED = "DISPUTED"


class FindingTier(str, Enum):
    OBSERVATION = "OBSERVATION"
    STUDIO_FINDING = "STUDIO_FINDING"
    TRANSFER_CLAIM = "TRANSFER_CLAIM"
    TRANSFER_REJECTED = "TRANSFER_REJECTED"
    DOCTRINE = "DOCTRINE"


class TrustTier(str, Enum):
    CANONICAL_DOCTRINE = "CANONICAL_DOCTRINE"
    VALIDATED_FINDING = "VALIDATED_FINDING"
    TRANSFER_CLAIM = "TRANSFER_CLAIM"
    WORKER_MEMORY = "WORKER_MEMORY"
    VENUE_INTEL = "VENUE_INTEL"
    TASK_MATERIAL = "TASK_MATERIAL"
    EPHEMERAL = "EPHEMERAL"


# ─── Frozen model config ──────────────────────────────────────────────

class FrozenModel(BaseModel):
    """Base for behaviorally significant immutable models."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION, description="Contract schema version")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_digest(self) -> str:
        """SHA-256 of serialized content for immutability verification."""
        raw = json.dumps(self.model_dump(), sort_keys=True, default=str)
        return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()


class MutableModel(BaseModel):
    """Base for models that may be updated (e.g., status fields)."""
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default=SCHEMA_VERSION)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Core Entities ─────────────────────────────────────────────────────

class SourceRef(FrozenModel):
    """Git provenance — exact commit where code/config lives."""
    repository: str = ""
    commit_sha: str = ""
    path: str = ""
    content_digest: str = ""


class LabManifest(FrozenModel):
    lab_id: str
    version: str = "0.1"
    studios: list[str] = Field(default_factory=list)


class StudioManifest(FrozenModel):
    studio_id: str
    name: str
    task_families: list[str] = Field(default_factory=list)
    evaluator_versions: list[str] = Field(default_factory=list)
    modes: list[str] = Field(default_factory=list)


class Worker(MutableModel):
    """Persistent worker identity. Never mutated after creation."""
    worker_id: str
    current_version_id: str = ""
    letta_agent_id: str = ""
    metadata: dict = Field(default_factory=dict)


class WorkerVersion(FrozenModel):
    """Immutable version of a worker. Changing any field creates a new version."""
    version_id: str
    worker_id: str
    parent_version_id: str = ""
    agent_runtime: str = ""
    model_provider: str = ""
    model_name: str = ""
    system_prompt_digest: str = ""
    memory_revision: str = ""
    skill_versions: list[str] = Field(default_factory=list)
    tool_policy: str = ""
    process_policy: str = ""
    routing_policy: str = ""
    context_policy: str = ""
    source: SourceRef = Field(default_factory=SourceRef)
    git_commits: dict = Field(default_factory=dict)
    git_digests: dict = Field(default_factory=dict)


# ─── Capability Pools ─────────────────────────────────────────────────

class CapabilityScope(FrozenModel):
    """Orthogonal dimension: what domain/capabilities a task or finding relates to."""
    domains: list[str] = Field(default_factory=list)
    subdomains: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class CapabilityPool(FrozenModel):
    """A domain pool — workers join pools, findings flow into pools."""
    pool_id: str
    name: str
    subdomains: list[str] = Field(default_factory=list)
    initial_venues: list[str] = Field(default_factory=list)
    shared_assets: list[str] = Field(default_factory=list)
    context_policy: dict = Field(default_factory=dict)


class Venue(FrozenModel):
    """A market/protocol where workers compete."""
    venue_id: str
    name: str
    pool_ids: list[str] = Field(default_factory=list)
    protocol: str = ""
    metadata: dict = Field(default_factory=dict)


# ─── Task & Run ────────────────────────────────────────────────────────

class TaskInstance(FrozenModel):
    """A single task to be executed. Immutable once created."""
    task_id: str
    studio_id: str
    task_family: str
    split: Split
    capability_scope: CapabilityScope = Field(default_factory=CapabilityScope)
    seed: int | None = None
    content: dict = Field(default_factory=dict)
    evaluation_data: dict = Field(default_factory=dict)


class BudgetEnvelope(FrozenModel):
    """Explicit resource limits for a run. Part of the experiment."""
    envelope_id: str
    cash_usd: float = 0.0
    token_limit: int = 0
    wall_seconds: int = 0
    model_call_limit: int = 0
    search_call_limit: int = 0
    compute_ms: int = 0
    allowed_providers: list[str] = Field(default_factory=list)
    quality_floor: float = 0.0
    escalation_policy: str = ""


class ContextFragment(FrozenModel):
    """A single piece of context with provenance and trust."""
    fragment_id: str
    source_type: str = ""
    source_ref: str = ""
    trust_tier: TrustTier = TrustTier.EPHEMERAL
    content: str = ""
    content_digest: str = ""
    token_count: int = 0
    selection_reason: str = ""
    retrieval_query: str = ""
    split_eligibility: list[Split] = Field(default_factory=list)
    title: str = ""
    sha256: str = ""
    priority: int = 0


class ContextPack(FrozenModel):
    """Deterministic context assembly. Same inputs → same digest."""
    pack_id: str
    fragments: list[ContextFragment] = Field(default_factory=list)
    total_tokens: int = 0
    dropped_fragments: list[ContextFragment] = Field(default_factory=list)
    budget_tokens: int = 0
    context_pack_digest: str = ""


class RunSpec(FrozenModel):
    """Complete specification for a run. Immutable once created."""
    run_id: str
    lab_id: str
    studio_id: str
    task_instance_id: str
    split: Split
    worker_id: str
    worker_version_id: str
    capability_scope: CapabilityScope = Field(default_factory=CapabilityScope)
    context_pack_id: str = ""
    budget_envelope_id: str = ""
    evaluator_version_id: str = ""
    seed: int | None = None
    mode: RunMode = RunMode.REPLAY


class RunReceipt(FrozenModel):
    """Immutable record of what happened during a run."""
    run_id: str
    spec: RunSpec
    success: bool = False
    artifacts: list[str] = Field(default_factory=list)
    trajectory_ref: str = ""
    cost_events: list[str] = Field(default_factory=list)
    evaluation_result_id: str = ""
    external_outcome_id: str = ""
    git_commit: str = ""
    workspace_path: str = ""
    duration_ms: int = 0


# ─── Artifacts ─────────────────────────────────────────────────────────

class ArtifactRef(FrozenModel):
    """Content-addressed artifact reference."""
    artifact_id: str
    name: str
    media_type: str = ""
    sha256: str = ""
    uri: str = ""
    size_bytes: int = 0
    derived_from: list[str] = Field(default_factory=list)


class TrajectoryRef(FrozenModel):
    """Reference to a worker's execution trajectory."""
    trajectory_id: str
    run_id: str
    format: str = "letta-trajectory"
    content_hash: str = ""
    step_count: int = 0


# ─── Budget ────────────────────────────────────────────────────────────

class BudgetEvent(FrozenModel):
    """Immutable cost record."""
    event_id: str
    run_id: str
    category: str = ""
    provider: str = ""
    amount: float = 0.0
    unit: str = ""
    dimension: str = ""


class RouteDecision(FrozenModel):
    """Model routing decision."""
    decision_id: str
    run_id: str
    model: str = ""
    provider: str = ""
    reason: str = ""
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    budget_envelope_id: str = ""


# ─── Evaluation ────────────────────────────────────────────────────────

class EvaluationSpec(FrozenModel):
    """What the evaluator checks. Hidden from worker."""
    spec_id: str
    evaluator_version: str = ""
    gates: list[dict] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    hidden: bool = True


class EvaluationResult(FrozenModel):
    """Immutable evaluation outcome. Success comes from this, not client flags."""
    result_id: str
    run_id: str
    spec_id: str
    success: bool = False
    scores: dict = Field(default_factory=dict)
    gates_passed: int = 0
    gates_total: int = 0
    gate_details: list[dict] = Field(default_factory=list)
    overall_score: float = 0.0


# ─── Experiments ───────────────────────────────────────────────────────

class ExperimentSpec(FrozenModel):
    """Controlled comparison between WorkerVersions."""
    experiment_id: str
    hypothesis: str = ""
    control_worker_version: str = ""
    candidate_worker_version: str = ""
    studio_id: str = ""
    task_family: str = ""
    split: Split = Split.SECRET
    n_tasks: int = 0
    metrics: list[str] = Field(default_factory=list)
    promotion_rule: str = ""
    status: ExperimentStatus = ExperimentStatus.DESIGNED


class ExperimentResult(FrozenModel):
    """Immutable experiment outcome. Only CG produces this."""
    result_id: str
    experiment_id: str
    control_quality: float = 0.0
    candidate_quality: float = 0.0
    quality_delta: float = 0.0
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    control_cost: float = 0.0
    candidate_cost: float = 0.0
    cost_delta: float = 0.0
    regressions: list[str] = Field(default_factory=list)
    promoted: bool = False
    reason: str = ""


# ─── Learning ──────────────────────────────────────────────────────────

class LearningProposal(FrozenModel):
    """Candidate change proposed by CGE/Lab Scientist."""
    proposal_id: str
    source_run_ids: list[str] = Field(default_factory=list)
    target: str = ""
    hypothesis: str = ""
    patch: dict = Field(default_factory=dict)
    confidence: float = 0.0
    experiment_id: str = ""
    status: str = "pending"


class PromotionReceipt(FrozenModel):
    """Record of a promotion decision. Always points back to evidence."""
    candidate: str
    experiment_result: str
    source_commit: str = ""
    reason: str = ""
    promoted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryRevision(FrozenModel):
    """Immutable memory snapshot."""
    revision_id: str
    worker_id: str
    memory_type: str = ""
    content: str = ""
    source_proposal_id: str = ""
    git_commit: str = ""


class SkillVersion(FrozenModel):
    """Immutable skill version."""
    skill_id: str
    version: str = ""
    name: str = ""
    description: str = ""
    content_hash: str = ""
    git_commit: str = ""


# ─── Findings ──────────────────────────────────────────────────────────

class Finding(FrozenModel):
    """Evidence with tier system and pool association."""
    finding_id: str
    tier: FindingTier = FindingTier.OBSERVATION
    studio_id: str = ""
    capability_scope: CapabilityScope = Field(default_factory=CapabilityScope)
    claim: str = ""
    evidence_experiment_ids: list[str] = Field(default_factory=list)
    evidence_run_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    valid_in: list[str] = Field(default_factory=list)
    transferred_to: list[str] = Field(default_factory=list)


class TransferClaim(FrozenModel):
    """A finding claimed to transfer across venues."""
    claim_id: str
    finding_id: str
    source_venue: str = ""
    target_venue: str = ""
    evidence_run_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    status: str = "pending"  # pending, supported, rejected


# ─── Context ───────────────────────────────────────────────────────────
# ContextFragment and ContextPack defined above with RunSpec


# ─── External ──────────────────────────────────────────────────────────

class ExternalSubmissionReceipt(FrozenModel):
    """Record of submission to external venue."""
    submission_id: str
    run_id: str
    venue: str = ""
    external_id: str = ""


class ExternalOutcomeReceipt(FrozenModel):
    """Record of external outcome."""
    outcome_id: str
    submission_id: str
    status: str = ""
    reward_usd: float = 0.0
    score: float = 0.0
    feedback: str = ""


# ─── Module Contract ──────────────────────────────────────────────────

class ModuleStatus(MutableModel):
    """Standardized module status report to Private Lab."""
    module_id: str
    module_name: str
    programs: list[ModuleProgram] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_revenue_usd: float = 0.0
    worker_versions: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


# ─── External Intelligence ────────────────────────────────────────────
# These are NEVER canonical evidence. They are prior intelligence.
# ExternalTrajectory ≠ RunReceipt. Never mutate one into the other.

class ExternalSource(FrozenModel):
    """Provenance for an external intelligence source."""
    source_id: str
    source_name: str
    source_uri: str = ""
    upstream_commit: str = ""
    license: str = ""
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trust_level: str = "external_prior"
    description: str = ""


class ExternalArtifact(FrozenModel):
    """A single artifact from an external source, with full provenance."""
    artifact_id: str
    source_id: str
    artifact_type: str = ""  # trajectory, writeup, taxonomy, skill, benchmark_result
    content_hash: str = ""
    task_family: str = ""
    task_id: str = ""
    benchmark_id: str = ""
    license: str = ""
    trust_level: str = "external_prior"
    metadata: dict = Field(default_factory=dict)


class ExternalTrajectory(FrozenModel):
    """An external trajectory — another system's execution trace.

    NON-NEGOCIABLE SEPARATION:
    ExternalTrajectory means "another system claims this under documented provenance."
    RunReceipt means "our worker performed this under our controlled execution contract."
    Never mutate one into the other.
    """
    trajectory_id: str
    source_id: str
    agent_name: str = ""
    model: str = ""
    scaffold: str = ""
    tools: list[str] = Field(default_factory=list)
    synthetic: bool = False
    human_authored: bool = False
    executed: bool = False
    verified: bool = False
    task_family: str = ""
    task_id: str = ""
    outcome: str = ""  # success, failure, partial
    score: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    wall_time_ms: int = 0
    tool_calls: list[dict] = Field(default_factory=list)
    events: list[dict] = Field(default_factory=list)
    contamination_tags: list[str] = Field(default_factory=list)
    license: str = ""
    content_hash: str = ""
    metadata: dict = Field(default_factory=dict)


class ExternalEpisode(FrozenModel):
    """A single episode within an external trajectory."""
    episode_id: str
    trajectory_id: str
    turn: int = 0
    observation: str = ""
    hypothesis: str = ""
    decision: str = ""
    tool_selected: str = ""
    tool_result: str = ""
    pivot: bool = False
    validation: str = ""
    outcome: str = ""
    tokens: int = 0


class ExternalFinding(FrozenModel):
    """A vulnerability finding from an external source."""
    finding_id: str
    source_id: str
    title: str = ""
    severity: str = ""
    category: str = ""
    description: str = ""
    impact: str = ""
    exploit_path: str = ""
    recommendation: str = ""
    location: str = ""
    verified: bool = False


class ExternalTechnique(FrozenModel):
    """A security technique/pattern from external knowledge."""
    technique_id: str
    source_id: str
    name: str = ""
    description: str = ""
    category: str = ""  # recon, exploitation, defense, analysis
    attack_surface: str = ""  # web, sca, agent, mcp, browser
    applicability: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    trust_level: str = "external_knowledge"


class ExternalBenchmarkResult(FrozenModel):
    """A benchmark result from an external evaluation."""
    result_id: str
    source_id: str
    benchmark_id: str = ""
    agent_name: str = ""
    model: str = ""
    score: float = 0.0
    metric: str = ""
    details: dict = Field(default_factory=list)
    provenance: str = ""
