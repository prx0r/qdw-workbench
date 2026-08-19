use anyhow::{Context,Result};
use qdw_workbench_contracts::HandoverRecord;
use std::path::{Path,PathBuf};

pub fn persist(workspace:&Path,h:&HandoverRecord)->Result<PathBuf>{
    if !h.verify(){anyhow::bail!("handover digest invalid before persistence")}
    let dir=workspace.join(".qdw/handovers").join(sanitize(&h.source_session_id)); std::fs::create_dir_all(&dir)?;
    let ts=h.created_at.format("%Y%m%dT%H%M%S%.3fZ"); let path=dir.join(format!("{}-{}.md",ts,h.handover_id));
    let front=serde_json::json!({"handover_id":h.handover_id,"source_session_id":h.source_session_id,"created_at":h.created_at,"git":h.git,"context_used_tokens":h.context_used_tokens,"context_max_tokens":h.context_max_tokens,"runtime_id":h.runtime_id,"model_id":h.model_id,"body_sha256":h.body_sha256});
    let text=format!("<!-- qdw-handover-metadata\n{}\n-->\n\n{}",serde_json::to_string_pretty(&front)?,h.body);
    std::fs::write(&path,text).with_context(||format!("write {}",path.display()))?; Ok(path)
}
fn sanitize(s:&str)->String{s.chars().map(|c|if c.is_ascii_alphanumeric()||c=='-'||c=='_'{c}else{'_'}).collect()}
