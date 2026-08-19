use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, path::PathBuf, process::Stdio, sync::{Arc,Mutex}};
use tokio::process::{Child, Command};
use uuid::Uuid;

#[derive(Debug,Clone,Serialize,Deserialize)]
pub struct ProcessSpec { pub cwd:PathBuf, pub argv:Vec<String>, pub env:HashMap<String,String> }
#[derive(Debug,Clone,Serialize,Deserialize)]
pub struct ProcessStarted { pub process_id:Uuid, pub pid:Option<u32> }

#[derive(Clone,Default)]
pub struct ProcessRegistry(Arc<Mutex<HashMap<Uuid,Child>>>);
impl ProcessRegistry {
    pub fn count(&self)->usize{self.0.lock().unwrap().len()}
    pub async fn spawn(&self,spec:ProcessSpec)->Result<ProcessStarted>{
        if spec.argv.is_empty(){anyhow::bail!("argv empty")}
        let mut cmd=Command::new(&spec.argv[0]); cmd.args(&spec.argv[1..]).current_dir(&spec.cwd).envs(&spec.env).stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::piped()).kill_on_drop(true);
        let child=cmd.spawn()?; let pid=child.id(); let id=Uuid::now_v7(); self.0.lock().unwrap().insert(id,child); Ok(ProcessStarted{process_id:id,pid})
    }
    pub async fn wait(&self,id:Uuid)->Result<serde_json::Value>{
        let mut child=self.0.lock().unwrap().remove(&id).ok_or_else(||anyhow::anyhow!("unknown process"))?;
        let out=child.wait_with_output().await?;
        Ok(serde_json::json!({"exit_code":out.status.code(),"success":out.status.success(),"stdout":String::from_utf8_lossy(&out.stdout),"stderr":String::from_utf8_lossy(&out.stderr)}))
    }
    pub fn kill(&self,id:Uuid)->Result<()> {
        let mut m=self.0.lock().unwrap(); let child=m.get_mut(&id).ok_or_else(||anyhow::anyhow!("unknown process"))?; child.start_kill()?; Ok(())
    }
}
