"""Lab Contracts — Pydantic models for the Moltwork Lab.

From spec §10: All cross-module interfaces exchange these contracts.
Do not pass mystery dictionaries through the Lab.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


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
    DOCTRINE = "DOCTRINE"


# ─── Core Entities ─────────────────────────────────────────────────────

class LabManifest(BaseModel):
    lab_id: str
    version: str = "0.1"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    studios: list[str] = Field(default_factory=list)


class StudioManifest(BaseModel):
    studio_id: str
    name: str
    task_families: list[str] = Field(default_factory=list)
    evaluator_versions: list[str] = Field(default_factory=list)
    modes: list[str] = Field(default_factory=list)  # REPLAY, SHADOW, LIVE


class Worker(BaseModel):
    worker_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_version_id: str = ""
    letta_agent_id: str = ""
    metadata: dict = Field(default_factory=dict)


class WorkerVersion(BaseModel):
    version_id: str
    worker_id: str
    parent_version_id: str = ""
    agent_runtime: str = ""
    model_policy: str = ""
    memory_revision: str = ""
    skill_versions: list[str] = Field(default_factory=list)
    tool_policy: str = ""
    process_policy: str = ""
    routing_policy: str = ""
    context_policy: str = ""
    git_commits: dict = Field(default_factory=dict)  # {repo: commit}
    git_digests: dict = Field(default_factory=dict)  # {repo: sha256}
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Capability Pools ─────────────────────────────────────────────────

class CapabilityScope(BaseModel):
    """Orthogonal dimension: what domain/capabilities a task or finding relates to.

    A run belongs to ONE venue and ONE or MORE capability pools.
    """
    domains: list[str] = Field(default_factory=list)      # security, forecasting, coding
    subdomains: list[str] = Field(default_factory=list)    # smart_contract, binary_analysis
    capabilities: list[str] = Field(default_factory=list)  # solidity, fuzzing, exploit_reasoning


class CapabilityPool(BaseModel):
    """A domain pool — workers join pools, findings flow into pools, skills promote within pools."""
    pool_id: str
    name: str                                              # security, forecasting, coding, research
    subdomains: list[str] = Field(default_factory=list)
    initial_venues: list[str] = Field(default_factory=list)  # bittensor/sn60, immunefi, etc.
    shared_assets: list[str] = Field(default_factory=list)   # doctrine, skills, findings
    context_policy: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Venue(BaseModel):
    """A market/protocol where workers compete. Distinct from capability pools."""
    venue_id: str
    name: str                                              # bitsec-sn60, immunefi, metaculus
    pool_ids: list[str] = Field(default_factory=list)      # which pools this venue draws from
    protocol: str = ""                                     # bittensor, immunefi, metaculus, cantina
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Task & Run ────────────────────────────────────────────────────────

class TaskInstance(BaseModel):
    task_id: str
    studio_id: str
    task_family: str
    split: Split
    capability_scope: CapabilityScope = Field(default_factory=CapabilityScope)
    seed: int | None = None
    content: dict = Field(default_factory=dict)  # task-specific data
    evaluation_data: dict = Field(default_factory=dict)  # hidden labels
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunSpec(BaseModel):
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
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunReceipt(BaseModel):
    run_id: str
    spec: RunSpec
    success: bool = False
    artifacts: list[str] = Field(default_factory=list)  # artifact refs
    trajectory_ref: str = ""
    cost_events: list[str] = Field(default_factory=list)
    evaluation_result_id: str = ""
    external_outcome_id: str = ""
    git_commit: str = ""
    workspace_path: str = ""
    duration_ms: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Artifacts ─────────────────────────────────────────────────────────

class ArtifactRef(BaseModel):
    artifact_id: str
    name: str
    media_type: str = ""
    sha256: str = ""
    uri: str = ""
    size_bytes: int = 0
    derived_from: list[str] = Field(default_factory=list)


class TrajectoryRef(BaseModel):
    trajectory_id: str
    run_id: str
    format: str = "letta-trajectory"
    content_hash: str = ""
    step_count: int = 0


# ─── Budget ────────────────────────────────────────────────────────────

class BudgetEnvelope(BaseModel):
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


class BudgetEvent(BaseModel):
    event_id: str
    run_id: str
    category: str = ""  # cash, token, compute, human
    provider: str = ""
    amount: float = 0.0
    unit: str = ""  # USD, tokens, ms, seconds
    dimension: str = ""  # actual_cash, shadow_quota, subscription, local_compute
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RouteDecision(BaseModel):
    decision_id: str
    run_id: str
    model: str = ""
    provider: str = ""
    reason: str = ""
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    budget_envelope_id: str = ""


# ─── Evaluation ────────────────────────────────────────────────────────

class EvaluationSpec(BaseModel):
    spec_id: str
    evaluator_version: str = ""
    gates: list[dict] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    hidden: bool = True  # worker must not see this


class EvaluationResult(BaseModel):
    result_id: str
    run_id: str
    spec_id: str
    success: bool = False
    scores: dict = Field(default_factory=dict)  # metric -> value
    gates_passed: int = 0
    gates_total: int = 0
    gate_details: list[dict] = Field(default_factory=list)
    overall_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Experiments ───────────────────────────────────────────────────────

class ExperimentSpec(BaseModel):
    experiment_id: str
    hypothesis: str = ""
    control_worker_version: str = ""
    candidate_worker_version: str = ""
    studio_id: str = ""
    task_family: str = ""
    split: Split = Split.SECRET
    n_tasks: int = 0
    metrics: list[str] = Field(default_factory=list)
    promotion_rule: str = ""  # e.g. "quality_delta > 0 AND confidence > 0.95"
    status: ExperimentStatus = ExperimentStatus.DESIGNED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResult(BaseModel):
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
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Learning ──────────────────────────────────────────────────────────

class LearningProposal(BaseModel):
    proposal_id: str
    source_run_ids: list[str] = Field(default_factory=list)
    target: str = ""  # memory, skill, process, routing, context
    hypothesis: str = ""
    patch: dict = Field(default_factory=dict)
    confidence: float = 0.0
    experiment_id: str = ""
    status: str = "pending"  # pending, tested, promoted, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MemoryRevision(BaseModel):
    revision_id: str
    worker_id: str
    memory_type: str = ""  # lesson, skill, heuristic, warning
    content: str = ""
    source_proposal_id: str = ""
    git_commit: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SkillVersion(BaseModel):
    skill_id: str
    version: str = ""
    name: str = ""
    description: str = ""
    content_hash: str = ""
    git_commit: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Findings ──────────────────────────────────────────────────────────

class Finding(BaseModel):
    finding_id: str
    tier: FindingTier = FindingTier.OBSERVATION
    studio_id: str = ""
    capability_scope: CapabilityScope = Field(default_factory=CapabilityScope)
    claim: str = ""
    evidence_experiment_ids: list[str] = Field(default_factory=list)
    evidence_run_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    valid_in: list[str] = Field(default_factory=list)  # venue IDs where transfer was demonstrated
    transferred_to: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Context ───────────────────────────────────────────────────────────

class ContextFragment(BaseModel):
    fragment_id: str
    source_id: str = ""
    source_type: str = ""  # doctrine, finding, memory, task, budget
    trust_tier: str = ""   # canonical, verified, observed, memory, ephemeral
    capability_scope: CapabilityScope = Field(default_factory=CapabilityScope)
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    sha256: str = ""
    token_estimate: int = 0
    priority: int = 0
    title: str = ""
    content: str = ""
    studio_id: str = ""


class ContextPack(BaseModel):
    pack_id: str
    fragments: list[ContextFragment] = Field(default_factory=list)
    total_tokens: int = 0
    dropped_fragments: list[ContextFragment] = Field(default_factory=list)
    budget_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── External ──────────────────────────────────────────────────────────

class ExternalSubmissionReceipt(BaseModel):
    submission_id: str
    run_id: str
    venue: str = ""  # metaculus, bittensor, hackathon
    external_id: str = ""
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class ExternalOutcomeReceipt(BaseModel):
    outcome_id: str
    submission_id: str
    status: str = ""  # won, lost, pending, resolved
    reward_usd: float = 0.0
    score: float = 0.0
    feedback: str = ""
    observed_at: datetime = Field(default_factory=datetime.utcnow)
