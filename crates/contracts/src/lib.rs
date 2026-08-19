use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct NodeMetrics {
    pub node_id: String,
    pub boot_id: String,
    pub observed_at: DateTime<Utc>,
    pub logical_cpus: usize,
    pub load_1m: f64,
    pub mem_total_bytes: u64,
    pub mem_available_bytes: u64,
    pub disk_total_bytes: Option<u64>,
    pub disk_available_bytes: Option<u64>,
    pub active_child_processes: usize,
}

impl NodeMetrics {
    pub fn mem_used_ratio(&self) -> Option<f64> {
        if self.mem_total_bytes == 0 { return None; }
        Some(1.0 - (self.mem_available_bytes as f64 / self.mem_total_bytes as f64))
    }

    pub fn stale(&self, now: DateTime<Utc>, max_age_seconds: i64) -> bool {
        now.signed_duration_since(self.observed_at).num_seconds() > max_age_seconds
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ContextTrust {
    Canonical,
    Verified,
    Observed,
    Memory,
    Ephemeral,
}

impl ContextTrust {
    pub fn rank(&self) -> u8 {
        match self {
            Self::Canonical => 0,
            Self::Verified => 1,
            Self::Observed => 2,
            Self::Memory => 3,
            Self::Ephemeral => 4,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContextFragment {
    pub provider_id: String,
    pub source_uri: String,
    pub observed_at: DateTime<Utc>,
    pub sha256: String,
    pub token_estimate: u64,
    pub priority: i32,
    pub trust: ContextTrust,
    pub title: String,
    pub content: String,
}

impl ContextFragment {
    pub fn new(
        provider_id: impl Into<String>,
        source_uri: impl Into<String>,
        observed_at: DateTime<Utc>,
        token_estimate: u64,
        priority: i32,
        trust: ContextTrust,
        title: impl Into<String>,
        content: impl Into<String>,
    ) -> Self {
        let content = content.into();
        Self {
            provider_id: provider_id.into(),
            source_uri: source_uri.into(),
            observed_at,
            sha256: sha256_hex(content.as_bytes()),
            token_estimate,
            priority,
            trust,
            title: title.into(),
            content,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContextPolicy {
    pub version: String,
    pub max_tokens: u64,
    pub reserve_tokens: u64,
}

impl ContextPolicy {
    pub fn usable_tokens(&self) -> u64 { self.max_tokens.saturating_sub(self.reserve_tokens) }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CompiledContext {
    pub compiler_version: String,
    pub policy: ContextPolicy,
    pub selected: Vec<ContextFragment>,
    pub dropped: Vec<ContextFragment>,
    pub selected_tokens: u64,
    pub digest: String,
}

pub fn compile_context(mut fragments: Vec<ContextFragment>, policy: ContextPolicy) -> CompiledContext {
    fragments.sort_by(|a, b| {
        a.trust.rank().cmp(&b.trust.rank())
            .then_with(|| b.priority.cmp(&a.priority))
            .then_with(|| a.provider_id.cmp(&b.provider_id))
            .then_with(|| a.source_uri.cmp(&b.source_uri))
    });
    let cap = policy.usable_tokens();
    let mut selected = Vec::new();
    let mut dropped = Vec::new();
    let mut used = 0u64;
    for f in fragments {
        if used.saturating_add(f.token_estimate) <= cap {
            used = used.saturating_add(f.token_estimate);
            selected.push(f);
        } else {
            dropped.push(f);
        }
    }
    let manifest = serde_json::json!({
        "compiler_version": "qdw-context-v1",
        "policy": &policy,
        "selected": selected.iter().map(|f| (&f.provider_id, &f.source_uri, &f.sha256, f.token_estimate)).collect::<Vec<_>>(),
    });
    let bytes = serde_json::to_vec(&manifest).expect("manifest serializes");
    CompiledContext {
        compiler_version: "qdw-context-v1".into(),
        policy,
        selected,
        dropped,
        selected_tokens: used,
        digest: sha256_hex(&bytes),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UsageDimensions {
    pub cash_usd: Option<f64>,
    pub input_tokens: Option<u64>,
    pub output_tokens: Option<u64>,
    pub cached_tokens: Option<u64>,
    pub compute_ms: Option<u64>,
    pub wall_ms: Option<u64>,
    pub human_ms: Option<u64>,
    pub subscription_units: Option<f64>,
}

impl Default for UsageDimensions {
    fn default() -> Self {
        Self { cash_usd: None, input_tokens: None, output_tokens: None, cached_tokens: None,
               compute_ms: None, wall_ms: None, human_ms: None, subscription_units: None }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct RunEvent {
    pub event_id: Uuid,
    pub trace_id: String,
    pub span_id: String,
    pub parent_span_id: Option<String>,
    pub occurred_at: DateTime<Utc>,
    pub kind: String,
    pub attributes: BTreeMap<String, serde_json::Value>,
    pub usage: UsageDimensions,
}

impl RunEvent {
    pub fn new(kind: impl Into<String>, trace_id: impl Into<String>, span_id: impl Into<String>) -> Self {
        Self { event_id: Uuid::now_v7(), trace_id: trace_id.into(), span_id: span_id.into(),
               parent_span_id: None, occurred_at: Utc::now(), kind: kind.into(),
               attributes: BTreeMap::new(), usage: UsageDimensions::default() }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GitState {
    pub workspace: String,
    pub head_oid: Option<String>,
    pub branch: Option<String>,
    pub remote: Option<String>,
    pub dirty: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContextUsage {
    pub session_id: String,
    pub used_tokens: u64,
    pub max_tokens: u64,
    pub exact: bool,
    pub buckets: BTreeMap<String, u64>,
    pub observed_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ContextPressure { Normal, Warn, PrepareHandover, HandoverRequired }

pub fn context_pressure(used: u64, max: u64) -> ContextPressure {
    if max == 0 { return ContextPressure::Normal; }
    let p = used as f64 / max as f64;
    if p >= 0.92 { ContextPressure::HandoverRequired }
    else if p >= 0.82 { ContextPressure::PrepareHandover }
    else if p >= 0.70 { ContextPressure::Warn }
    else { ContextPressure::Normal }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct HandoverRecord {
    pub handover_id: Uuid,
    pub source_session_id: String,
    pub created_at: DateTime<Utc>,
    pub workspace: String,
    pub git: GitState,
    pub context_used_tokens: Option<u64>,
    pub context_max_tokens: Option<u64>,
    pub runtime_id: Option<String>,
    pub model_id: Option<String>,
    pub body_sha256: String,
    pub body: String,
}

impl HandoverRecord {
    pub fn new(source_session_id: String, git: GitState, body: String) -> Self {
        Self {
            handover_id: Uuid::now_v7(), source_session_id, created_at: Utc::now(),
            workspace: git.workspace.clone(), git, context_used_tokens: None, context_max_tokens: None,
            runtime_id: None, model_id: None, body_sha256: sha256_hex(body.as_bytes()), body,
        }
    }
    pub fn verify(&self) -> bool { self.body_sha256 == sha256_hex(self.body.as_bytes()) }
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    let mut h = Sha256::new(); h.update(bytes); hex::encode(h.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn context_never_exceeds_budget() {
        let now=Utc::now();
        let fs=(0..10).map(|i| ContextFragment::new("p",format!("s:{i}"),now,100,10-i,ContextTrust::Observed,format!("f{i}"),"x".repeat(10))).collect();
        let c=compile_context(fs,ContextPolicy{version:"1".into(),max_tokens:550,reserve_tokens:150});
        assert!(c.selected_tokens <= 400);
        assert!(!c.dropped.is_empty());
    }
    #[test]
    fn canonical_beats_memory_under_pressure() {
        let now=Utc::now();
        let memory=ContextFragment::new("hindsight","mem:1",now,100,999,ContextTrust::Memory,"memory","m");
        let canonical=ContextFragment::new("qdw","qdw:invariant",now,100,-100,ContextTrust::Canonical,"invariant","c");
        let c=compile_context(vec![memory,canonical.clone()],ContextPolicy{version:"1".into(),max_tokens:150,reserve_tokens:50});
        assert_eq!(c.selected[0].sha256,canonical.sha256);
    }
    #[test]
    fn subscription_is_not_cash() {
        let u=UsageDimensions{subscription_units:Some(1.0),..Default::default()};
        assert_eq!(u.cash_usd,None);
    }
    #[test]
    fn mutated_handover_fails_digest() {
        let git=GitState{workspace:"/tmp/x".into(),head_oid:None,branch:None,remote:None,dirty:false};
        let mut h=HandoverRecord::new("s".into(),git,"hello".into());
        assert!(h.verify()); h.body.push('x'); assert!(!h.verify());
    }
    #[test]
    fn pressure_thresholds_are_stable() {
        assert_eq!(context_pressure(699,1000),ContextPressure::Normal);
        assert_eq!(context_pressure(700,1000),ContextPressure::Warn);
        assert_eq!(context_pressure(820,1000),ContextPressure::PrepareHandover);
        assert_eq!(context_pressure(920,1000),ContextPressure::HandoverRequired);
    }
}
