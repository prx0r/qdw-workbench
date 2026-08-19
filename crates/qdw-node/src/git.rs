use anyhow::{Context, Result};
use qdw_workbench_contracts::GitState;
use std::path::Path;
use tokio::process::Command;

async fn git(cwd:&Path,args:&[&str])->Result<String>{
    let out=Command::new("git").args(args).current_dir(cwd).output().await.context("spawn git")?;
    if !out.status.success(){anyhow::bail!("git {:?}: {}",args,String::from_utf8_lossy(&out.stderr));}
    Ok(String::from_utf8_lossy(&out.stdout).trim().to_string())
}

pub async fn state(path:&Path)->Result<GitState>{
    let workspace=path.canonicalize().unwrap_or_else(|_|path.to_path_buf()).to_string_lossy().to_string();
    let head=git(path,&["rev-parse","HEAD"]).await.ok().filter(|s|!s.is_empty());
    let branch=git(path,&["branch","--show-current"]).await.ok().filter(|s|!s.is_empty());
    let remote=git(path,&["remote","get-url","origin"]).await.ok().filter(|s|!s.is_empty());
    let dirty=git(path,&["status","--porcelain"]).await.map(|s|!s.is_empty()).unwrap_or(false);
    Ok(GitState{workspace,head_oid:head,branch,remote,dirty})
}

pub async fn create_worktree(repo:&Path,branch:&str,dest:&Path)->Result<()> {
    if branch.trim().is_empty(){anyhow::bail!("empty branch")}
    let out=Command::new("git").args(["worktree","add","-b",branch,dest.to_string_lossy().as_ref()]).current_dir(repo).output().await?;
    if !out.status.success(){anyhow::bail!("git worktree failed: {}",String::from_utf8_lossy(&out.stderr));}
    Ok(())
}

pub async fn diff(path:&Path,scope:&str)->Result<String>{
    match scope {
        "uncommitted" => git(path,&["diff","--no-ext-diff"]).await,
        "staged" => git(path,&["diff","--cached","--no-ext-diff"]).await,
        "head" => git(path,&["show","--format=","--no-ext-diff","HEAD"]).await,
        _ => anyhow::bail!("unsupported diff scope"),
    }
}
