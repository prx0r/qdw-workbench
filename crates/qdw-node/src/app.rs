use crate::{config::NodeConfig, git, handover, metrics, process::{ProcessRegistry,ProcessSpec}, pty::PtyRegistry, session::SessionStore, store::Store};
use axum::{extract::{Path,Query,State},http::StatusCode,routing::{get,post},Json,Router};
use qdw_workbench_contracts::{ContextPolicy,ContextFragment,CompiledContext,GitState,HandoverRecord,RunEvent,compile_context};
use serde::Deserialize;
use std::{path::PathBuf,sync::Arc};
use tower_http::{cors::CorsLayer,trace::TraceLayer};
use uuid::Uuid;

pub struct AppState { pub config:NodeConfig, pub store:Store, pub processes:ProcessRegistry, pub sessions:SessionStore, pub ptys:PtyRegistry }
pub type Shared=Arc<AppState>;

pub fn router(state:Shared)->Router{
    Router::new()
      .route("/v1/health",get(health))
      .route("/v1/metrics",get(node_metrics))
      .route("/v1/git/state",get(git_state))
      .route("/v1/git/diff",get(git_diff))
      .route("/v1/git/worktree",post(worktree))
      .route("/v1/process",post(proc_spawn))
      .route("/v1/process/{id}/wait",post(proc_wait))
      .route("/v1/process/{id}/kill",post(proc_kill))
      .route("/v1/events",post(event))
      .route("/v1/context/compile",post(context_compile))
      .route("/v1/handovers",post(put_handover))
      .route("/v1/handovers/{session}/latest",get(latest_handover))
      .route("/v1/sessions",get(list_sessions))
      .route("/v1/sessions",post(create_session))
      .route("/v1/sessions/{id}/prompt",post(prompt_session))
      .route("/v1/sessions/{id}",get(get_session).delete(delete_session))
      .route("/v1/pty",post(pty_spawn))
      .route("/v1/pty/{id}/write",post(pty_write))
      .route("/v1/pty/{id}/read",get(pty_read))
      .route("/v1/pty/{id}",get(pty_info).delete(pty_close))
      .route("/v1/pty",get(pty_list))
      .layer(TraceLayer::new_for_http()).layer(CorsLayer::permissive()).with_state(state)
}
async fn health(State(s):State<Shared>)->Json<serde_json::Value>{Json(serde_json::json!({"status":"ok","node_id":s.config.node_id,"version":env!("CARGO_PKG_VERSION")}))}
async fn node_metrics(State(s):State<Shared>)->Result<Json<qdw_workbench_contracts::NodeMetrics>,ApiError>{
    Ok(Json(metrics::collect(&s.config.node_id,s.config.workspace_roots.first().map(|p|p.as_path()),s.processes.count()).await?))
}
#[derive(Deserialize)]struct W{workspace:PathBuf}
async fn git_state(Query(q):Query<W>)->Result<Json<GitState>,ApiError>{Ok(Json(git::state(&q.workspace).await?))}
#[derive(Deserialize)]struct D{workspace:PathBuf,scope:Option<String>}
async fn git_diff(Query(q):Query<D>)->Result<Json<serde_json::Value>,ApiError>{let d=git::diff(&q.workspace,q.scope.as_deref().unwrap_or("uncommitted")).await?;Ok(Json(serde_json::json!({"diff":d})))}
#[derive(Deserialize)]struct WT{repo:PathBuf,branch:String,dest:PathBuf}
async fn worktree(Json(x):Json<WT>)->Result<StatusCode,ApiError>{git::create_worktree(&x.repo,&x.branch,&x.dest).await?;Ok(StatusCode::CREATED)}
async fn proc_spawn(State(s):State<Shared>,Json(spec):Json<ProcessSpec>)->Result<Json<crate::process::ProcessStarted>,ApiError>{Ok(Json(s.processes.spawn(spec).await?))}
async fn proc_wait(State(s):State<Shared>,Path(id):Path<String>)->Result<Json<serde_json::Value>,ApiError>{Ok(Json(s.processes.wait(Uuid::parse_str(&id)?).await?))}
async fn proc_kill(State(s):State<Shared>,Path(id):Path<String>)->Result<StatusCode,ApiError>{s.processes.kill(Uuid::parse_str(&id)?)?;Ok(StatusCode::NO_CONTENT)}
async fn event(State(s):State<Shared>,Json(e):Json<RunEvent>)->Result<StatusCode,ApiError>{s.store.append_event(&e)?;Ok(StatusCode::CREATED)}
#[derive(Deserialize)]struct CompileReq{fragments:Vec<ContextFragment>,policy:ContextPolicy}
async fn context_compile(Json(r):Json<CompileReq>)->Json<CompiledContext>{Json(compile_context(r.fragments,r.policy))}
async fn put_handover(State(s):State<Shared>,Json(h):Json<HandoverRecord>)->Result<Json<serde_json::Value>,ApiError>{
    if !h.verify(){return Err(ApiError(anyhow::anyhow!("handover digest mismatch")))}
    let path=handover::persist(PathBuf::from(&h.workspace).as_path(),&h)?; s.store.put_handover(&h)?; Ok(Json(serde_json::json!({"handover_id":h.handover_id,"path":path,"sha256":h.body_sha256})))
}
async fn latest_handover(State(s):State<Shared>,Path(session):Path<String>)->Result<Json<Option<HandoverRecord>>,ApiError>{Ok(Json(s.store.latest_handover(&session)?))}

pub struct ApiError(anyhow::Error);
impl<E> From<E> for ApiError where E:Into<anyhow::Error>{fn from(e:E)->Self{Self(e.into())}}
impl axum::response::IntoResponse for ApiError{fn into_response(self)->axum::response::Response{(StatusCode::BAD_REQUEST,Json(serde_json::json!({"error":self.0.to_string()}))).into_response()}}

// --- Session management endpoints ---

async fn list_sessions(State(s):State<Shared>)->Json<serde_json::Value>{
    Json(serde_json::json!(s.sessions.list()))
}

#[derive(Deserialize)]
struct CreateSessionReq{workspace:String,agent_command:Option<String>,agent_args:Option<Vec<String>>}

async fn create_session(State(s):State<Shared>,Json(req):Json<CreateSessionReq>)->Result<Json<serde_json::Value>,ApiError>{
    let agent=req.agent_command.unwrap_or_else(||"hermes".into());
    let info=s.sessions.create(req.workspace,agent);
    Ok(Json(serde_json::json!(info)))
}

async fn get_session(State(s):State<Shared>,Path(id):Path<String>)->Result<Json<serde_json::Value>,ApiError>{
    s.sessions.get(&id).map(|i|Json(serde_json::json!(i))).ok_or_else(||ApiError(anyhow::anyhow!("session not found")))
}

async fn delete_session(State(s):State<Shared>,Path(id):Path<String>)->Result<StatusCode,ApiError>{
    s.sessions.remove(&id).ok_or_else(||ApiError(anyhow::anyhow!("session not found")))?;
    Ok(StatusCode::NO_CONTENT)
}

#[derive(Deserialize)]
struct PromptReq{prompt:String}

async fn prompt_session(State(s):State<Shared>,Path(id):Path<String>,Json(req):Json<PromptReq>)->Result<Json<serde_json::Value>,ApiError>{
    let session=s.sessions.get(&id).ok_or_else(||ApiError(anyhow::anyhow!("session not found")))?;
    s.sessions.increment_prompt(&id);

    // Build agent launch from session info
    let spec=qdw_acp_host::AgentLaunch{
        command:session.agent_command.clone(),
        args:vec!["acp".into()],
        cwd:std::path::PathBuf::from(&session.workspace),
    };

    // Execute prompt via ACP
    let response=qdw_acp_host::session_prompt(spec,req.prompt).await.map_err(|e|ApiError(e))?;

    Ok(Json(serde_json::json!({
        "session_id":id,
        "response":response,
        "prompt_count":session.prompt_count+1
    })))
}

// --- PTY endpoints ---

async fn pty_spawn(State(s):State<Shared>,Json(spec):Json<crate::pty::PtySpec>)->Result<Json<serde_json::Value>,ApiError>{
    let session=s.ptys.spawn(spec).map_err(|e|ApiError(e))?;
    Ok(Json(serde_json::json!(session)))
}

async fn pty_write(State(s):State<Shared>,Path(id):Path<String>,Json(body):Json<crate::pty::PtyWrite>)->Result<StatusCode,ApiError>{
    s.ptys.write(&id,&body.data).map_err(|e|ApiError(e))?;
    Ok(StatusCode::OK)
}

async fn pty_read(State(s):State<Shared>,Path(id):Path<String>)->Result<Json<serde_json::Value>,ApiError>{
    let data=s.ptys.read(&id).map_err(|e|ApiError(e))?;
    Ok(Json(serde_json::json!(data)))
}

async fn pty_info(State(s):State<Shared>,Path(id):Path<String>)->Result<Json<serde_json::Value>,ApiError>{
    s.ptys.list().iter().find(|p|p.session_id==id)
        .map(|p|Json(serde_json::json!(p)))
        .ok_or_else(||ApiError(anyhow::anyhow!("PTY session not found")))
}

async fn pty_close(State(s):State<Shared>,Path(id):Path<String>)->Result<StatusCode,ApiError>{
    s.ptys.remove(&id).ok_or_else(||ApiError(anyhow::anyhow!("PTY session not found")))?;
    Ok(StatusCode::NO_CONTENT)
}

async fn pty_list(State(s):State<Shared>)->Json<serde_json::Value>{
    Json(serde_json::json!(s.ptys.list()))
}
