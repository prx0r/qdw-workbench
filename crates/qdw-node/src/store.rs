use anyhow::Result;
use qdw_workbench_contracts::{HandoverRecord, RunEvent};
use rusqlite::{params, Connection};
use std::{path::Path, sync::Mutex};

pub struct Store { con: Mutex<Connection> }
impl Store {
    pub fn open(path:&Path)->Result<Self>{
        if let Some(p)=path.parent(){std::fs::create_dir_all(p)?;}
        let con=Connection::open(path)?;
        con.pragma_update(None,"journal_mode","WAL")?;
        con.execute_batch(r#"
        CREATE TABLE IF NOT EXISTS run_events(
          event_id TEXT PRIMARY KEY, occurred_at TEXT NOT NULL, trace_id TEXT NOT NULL,
          span_id TEXT NOT NULL, kind TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_run_events_trace ON run_events(trace_id, occurred_at);
        CREATE TABLE IF NOT EXISTS handovers(
          handover_id TEXT PRIMARY KEY, source_session_id TEXT NOT NULL, created_at TEXT NOT NULL,
          workspace TEXT NOT NULL, body_sha256 TEXT NOT NULL, payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_handovers_session ON handovers(source_session_id, created_at);
        "#)?;
        Ok(Self{con:Mutex::new(con)})
    }
    pub fn append_event(&self,e:&RunEvent)->Result<()> {
        let payload=serde_json::to_string(e)?; let con=self.con.lock().unwrap();
        con.execute("INSERT OR IGNORE INTO run_events(event_id,occurred_at,trace_id,span_id,kind,payload_json) VALUES(?,?,?,?,?,?)",
          params![e.event_id.to_string(),e.occurred_at.to_rfc3339(),e.trace_id,e.span_id,e.kind,payload])?; Ok(())
    }
    pub fn put_handover(&self,h:&HandoverRecord)->Result<()> {
        let payload=serde_json::to_string(h)?; let con=self.con.lock().unwrap();
        con.execute("INSERT INTO handovers(handover_id,source_session_id,created_at,workspace,body_sha256,payload_json) VALUES(?,?,?,?,?,?)",
          params![h.handover_id.to_string(),h.source_session_id,h.created_at.to_rfc3339(),h.workspace,h.body_sha256,payload])?; Ok(())
    }
    pub fn latest_handover(&self,session:&str)->Result<Option<HandoverRecord>>{
        let con=self.con.lock().unwrap(); let mut s=con.prepare("SELECT payload_json FROM handovers WHERE source_session_id=? ORDER BY created_at DESC LIMIT 1")?;
        let mut rows=s.query(params![session])?; if let Some(r)=rows.next()? { let raw:String=r.get(0)?; Ok(Some(serde_json::from_str(&raw)?)) } else {Ok(None)}
    }
}
