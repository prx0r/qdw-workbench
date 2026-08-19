use anyhow::{Context, Result};
use chrono::Utc;
use qdw_workbench_contracts::NodeMetrics;
use std::path::Path;
use tokio::process::Command;

pub async fn collect(node_id: &str, workspace_root: Option<&Path>, active_children: usize) -> Result<NodeMetrics> {
    let (total, available)=read_meminfo()?;
    let load_1m=std::fs::read_to_string("/proc/loadavg").ok().and_then(|s|s.split_whitespace().next()?.parse().ok()).unwrap_or(0.0);
    let logical_cpus=std::thread::available_parallelism().map(|x|x.get()).unwrap_or(1);
    let boot_id=std::fs::read_to_string("/proc/sys/kernel/random/boot_id").unwrap_or_else(|_|"unknown".into()).trim().to_string();
    let (disk_total_bytes,disk_available_bytes)=if let Some(root)=workspace_root { disk(root).await.unwrap_or((None,None)) } else {(None,None)};
    Ok(NodeMetrics{node_id:node_id.into(),boot_id,observed_at:Utc::now(),logical_cpus,load_1m,mem_total_bytes:total,mem_available_bytes:available,disk_total_bytes,disk_available_bytes,active_child_processes:active_children})
}

fn read_meminfo() -> Result<(u64,u64)> {
    let s=std::fs::read_to_string("/proc/meminfo").context("read /proc/meminfo")?;
    let mut total=None; let mut avail=None;
    for line in s.lines() {
        let mut p=line.split_whitespace(); let key=p.next().unwrap_or(""); let v=p.next().and_then(|x|x.parse::<u64>().ok());
        if key=="MemTotal:" { total=v.map(|x|x*1024); }
        if key=="MemAvailable:" { avail=v.map(|x|x*1024); }
    }
    Ok((total.context("MemTotal missing")?,avail.context("MemAvailable missing")?))
}

async fn disk(path:&Path)->Result<(Option<u64>,Option<u64>)>{
    let out=Command::new("df").args(["-Pk",path.to_string_lossy().as_ref()]).output().await?;
    if !out.status.success(){anyhow::bail!("df failed")}
    let line=String::from_utf8_lossy(&out.stdout).lines().nth(1).unwrap_or("").to_string();
    let cols=line.split_whitespace().collect::<Vec<_>>();
    if cols.len()<4{return Ok((None,None));}
    Ok((cols[1].parse::<u64>().ok().map(|x|x*1024),cols[3].parse::<u64>().ok().map(|x|x*1024)))
}
