use crate::config::{self,Config};
use qdw_workbench_contracts::{ContextFragment,ContextPolicy,CompiledContext,HandoverRecord,NodeMetrics};
use serde_json::Value;
use std::{path::PathBuf,process::Stdio};
use tokio::process::Command;

#[tauri::command] pub fn load_config()->Config{config::load()}

#[tauri::command]
pub async fn qdw_get(path:String)->Result<Value,String>{
    let c=config::load(); let url=format!("{}{}",c.qdw_url.trim_end_matches('/'),if path.starts_with('/') {path}else{format!("/{path}")});
    reqwest::Client::new().get(url).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn qdw_post(path:String,body:Value)->Result<Value,String>{
    let c=config::load(); let url=format!("{}{}",c.qdw_url.trim_end_matches('/'),if path.starts_with('/') {path}else{format!("/{path}")});
    reqwest::Client::new().post(url).json(&body).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn node_metrics()->Result<Vec<NodeMetrics>,String>{
    let c=config::load(); let client=reqwest::Client::new(); let mut out=Vec::new();
    for n in c.nodes { if let Ok(r)=client.get(format!("{}/v1/metrics",n.url.trim_end_matches('/'))).send().await { if let Ok(m)=r.json::<NodeMetrics>().await {out.push(m);} } }
    Ok(out)
}

#[tauri::command]
pub async fn node_get(node_id:String,path:String)->Result<Value,String>{
    let c=config::load(); let n=c.nodes.into_iter().find(|n|n.id==node_id).ok_or("unknown node")?; let url=format!("{}{}",n.url.trim_end_matches('/'),if path.starts_with('/') {path}else{format!("/{path}")});
    reqwest::Client::new().get(url).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}


#[tauri::command]
pub async fn node_post(node_id:String,path:String,body:Value)->Result<Value,String>{
    let c=config::load(); let n=c.nodes.into_iter().find(|n|n.id==node_id).ok_or("unknown node")?;
    let url=format!("{}{}",n.url.trim_end_matches('/'),if path.starts_with('/') {path}else{format!("/{path}")});
    reqwest::Client::new().post(url).json(&body).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn acp_one_shot(command:String,args:Vec<String>,workspace:String,prompt:String)->Result<String,String>{
    let cwd=std::fs::canonicalize(workspace).map_err(e)?;
    qdw_acp_host::one_shot(qdw_acp_host::AgentLaunch{command,args,cwd},prompt).await.map_err(e)
}

#[tauri::command]
pub async fn compile_context(node_id:String,fragments:Vec<ContextFragment>,policy:ContextPolicy)->Result<CompiledContext,String>{
    let c=config::load(); let n=c.nodes.into_iter().find(|n|n.id==node_id).ok_or("unknown node")?;
    reqwest::Client::new().post(format!("{}/v1/context/compile",n.url.trim_end_matches('/'))).json(&serde_json::json!({"fragments":fragments,"policy":policy})).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn persist_handover(node_id:String,h:HandoverRecord)->Result<Value,String>{
    let c=config::load(); let n=c.nodes.into_iter().find(|n|n.id==node_id).ok_or("unknown node")?;
    reqwest::Client::new().post(format!("{}/v1/handovers",n.url.trim_end_matches('/'))).json(&h).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn git_state(node_id:String,workspace:String)->Result<Value,String>{
    let c=config::load(); let n=c.nodes.into_iter().find(|n|n.id==node_id).ok_or("unknown node")?;
    reqwest::Client::new().get(format!("{}/v1/git/state",n.url.trim_end_matches('/'))).query(&[("workspace",workspace)]).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn ssh_tunnel_start(node_id:String)->Result<Value,String>{
    let c=config::load(); let n=c.nodes.into_iter().find(|n|n.id==node_id).ok_or("unknown node")?; let s=n.ssh.ok_or("node has no ssh tunnel config")?;
    let forward=format!("127.0.0.1:{}:127.0.0.1:{}",s.local_port,s.remote_port);
    let child=Command::new("ssh").args(["-N","-L",&forward,"-o","ExitOnForwardFailure=yes","-o","ServerAliveInterval=30","-o","ServerAliveCountMax=3","--",&s.host]).stdin(Stdio::null()).stdout(Stdio::null()).stderr(Stdio::piped()).spawn().map_err(e)?;
    Ok(serde_json::json!({"pid":child.id(),"node_id":node_id,"forward":forward}))
}

#[tauri::command]
pub async fn list_files(workspace:String)->Result<Vec<String>,String>{
    let out=Command::new("git").args(["ls-files"]).current_dir(&workspace).output().await.map_err(e)?;
    if !out.status.success(){return Err(String::from_utf8_lossy(&out.stderr).into_owned())}
    Ok(String::from_utf8_lossy(&out.stdout).lines().map(|s|s.to_string()).collect())
}

#[tauri::command]
pub async fn read_text_file(workspace:String,path:String)->Result<String,String>{
    let base=std::fs::canonicalize(&workspace).map_err(e)?; let p=std::fs::canonicalize(base.join(path)).map_err(e)?;
    if !p.starts_with(&base){return Err("path escapes workspace".into())} std::fs::read_to_string(p).map_err(e)
}

#[tauri::command]
pub async fn write_text_file(workspace:String,path:String,content:String)->Result<Value,String>{
    let base=std::fs::canonicalize(&workspace).map_err(e)?; let joined=base.join(path); let parent=joined.parent().ok_or("no parent")?; let parent_c=std::fs::canonicalize(parent).map_err(e)?;
    if !parent_c.starts_with(&base){return Err("path escapes workspace".into())} std::fs::write(&joined,content.as_bytes()).map_err(e)?;
    Ok(serde_json::json!({"path":joined,"bytes":content.len()}))
}

#[tauri::command]
pub async fn memory_recent(kind:Option<String>,limit:Option<u32>)->Result<Value,String>{
    let c=config::load(); let mut url=format!("{}/v1/memory/recent",c.qdw_url.trim_end_matches('/'));
    let mut params=Vec::new();
    if let Some(k)=kind{params.push(format!("kind={k}"));}
    if let Some(l)=limit{params.push(format!("limit={l}"));}
    if !params.is_empty(){url.push('?'); url.push_str(&params.join("&"));}
    reqwest::Client::new().get(url).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn memory_search(q:String,limit:Option<u32>)->Result<Value,String>{
    let c=config::load(); let l=limit.unwrap_or(10);
    let url=format!("{}/v1/memory/search?q={}&limit={}",c.qdw_url.trim_end_matches('/'),q,l);
    reqwest::Client::new().get(url).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

// --- Session management commands ---

#[tauri::command]
pub async fn session_list()->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().get(format!("{}/v1/sessions",c.qdw_url.trim_end_matches('/'))).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn session_create(workspace:String,agent_command:Option<String>)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().post(format!("{}/v1/sessions",c.qdw_url.trim_end_matches('/'))).json(&serde_json::json!({"workspace":workspace,"agent_command":agent_command})).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn session_prompt(session_id:String,prompt:String)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().post(format!("{}/v1/sessions/{}/prompt",c.qdw_url.trim_end_matches('/'),session_id)).json(&serde_json::json!({"prompt":prompt})).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn session_close(session_id:String)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().delete(format!("{}/v1/sessions/{}",c.qdw_url.trim_end_matches('/'),session_id)).send().await.map_err(e)?.error_for_status().map_err(e)?;
    Ok(serde_json::json!({"closed":true}))
}

// --- PTY commands ---

#[tauri::command]
pub async fn pty_spawn(cwd:String,shell:Option<String>,cols:Option<u16>,rows:Option<u16>)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().post(format!("{}/v1/pty",c.qdw_url.trim_end_matches('/'))).json(&serde_json::json!({"cwd":cwd,"shell":shell,"cols":cols,"rows":rows})).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn pty_write(session_id:String,data:String)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().post(format!("{}/v1/pty/{}/write",c.qdw_url.trim_end_matches('/'),session_id)).json(&serde_json::json!({"data":data})).send().await.map_err(e)?.error_for_status().map_err(e)?;
    Ok(serde_json::json!({"written":data.len()}))
}

#[tauri::command]
pub async fn pty_read(session_id:String)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().get(format!("{}/v1/pty/{}/read",c.qdw_url.trim_end_matches('/'),session_id)).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn pty_list()->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().get(format!("{}/v1/pty",c.qdw_url.trim_end_matches('/'))).send().await.map_err(e)?.error_for_status().map_err(e)?.json().await.map_err(e)
}

#[tauri::command]
pub async fn pty_close(session_id:String)->Result<Value,String>{
    let c=config::load();
    reqwest::Client::new().delete(format!("{}/v1/pty/{}",c.qdw_url.trim_end_matches('/'),session_id)).send().await.map_err(e)?.error_for_status().map_err(e)?;
    Ok(serde_json::json!({"closed":true}))
}

fn e(x:impl std::fmt::Display)->String{x.to_string()}
