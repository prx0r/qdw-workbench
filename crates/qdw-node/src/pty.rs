use anyhow::{Context, Result};
use portable_pty::{CommandBuilder, NativePtySystem, PtySize, PtySystem};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::{Read, Write};
use std::sync::Mutex;
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PtySession {
    pub session_id: String,
    pub pid: Option<u32>,
    pub cols: u16,
    pub rows: u16,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PtySpec {
    pub cwd: String,
    pub shell: Option<String>,
    pub cols: Option<u16>,
    pub rows: Option<u16>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PtyWrite {
    pub data: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PtyRead {
    pub data: String,
    pub available: usize,
}

pub struct PtyRegistry {
    sessions: Mutex<HashMap<String, PtySessionData>>,
}

struct PtySessionData {
    session: PtySession,
    writer: Box<dyn Write + Send>,
    reader: Box<dyn Read + Send>,
}

impl PtyRegistry {
    pub fn new() -> Self {
        Self {
            sessions: Mutex::new(HashMap::new()),
        }
    }

    pub fn spawn(&self, spec: PtySpec) -> Result<PtySession> {
        let pty_system = NativePtySystem::default();
        let size = PtySize {
            rows: spec.rows.unwrap_or(24),
            cols: spec.cols.unwrap_or(80),
            pixel_width: 0,
            pixel_height: 0,
        };

        let pair = pty_system.openpty(size).context("failed to open PTY")?;

        let shell = spec.shell.unwrap_or_else(|| {
            std::env::var("SHELL").unwrap_or_else(|_| "/bin/bash".into())
        });

        let mut cmd = CommandBuilder::new(&shell);
        cmd.cwd(&spec.cwd);

        let child = pair.slave.spawn_command(cmd).context("failed to spawn PTY child")?;

        let writer = pair
            .master
            .take_writer()
            .context("failed to get PTY writer")?;
        let reader = pair
            .master
            .take_reader()
            .context("failed to get PTY reader")?;

        let session_id = uuid::Uuid::now_v7().to_string();
        let pid = child.process_id();
        let now = chrono::Utc::now().to_rfc3339();

        let session = PtySession {
            session_id: session_id.clone(),
            pid,
            cols: spec.cols.unwrap_or(80),
            rows: spec.rows.unwrap_or(24),
            created_at: now,
        };

        let data = PtySessionData {
            session: session.clone(),
            writer: Box::new(writer),
            reader: Box::new(reader),
        };

        self.sessions.lock().unwrap().insert(session_id.clone(), data);
        Ok(session)
    }

    pub fn write(&self, session_id: &str, data: &str) -> Result<()> {
        let mut sessions = self.sessions.lock().unwrap();
        let session = sessions
            .get_mut(session_id)
            .ok_or_else(|| anyhow::anyhow!("PTY session not found"))?;
        session.writer.write_all(data.as_bytes())?;
        session.writer.flush()?;
        Ok(())
    }

    pub fn read(&self, session_id: &str) -> Result<PtyRead> {
        let mut sessions = self.sessions.lock().unwrap();
        let session = sessions
            .get_mut(session_id)
            .ok_or_else(|| anyhow::anyhow!("PTY session not found"))?;

        let mut buf = [0u8; 4096];
        let mut output = String::new();
        let mut total = 0;

        // Non-blocking read with timeout
        session.reader.set_read_timeout(Some(Duration::from_millis(50))).ok();
        loop {
            match session.reader.read(&mut buf) {
                Ok(n) => {
                    if n == 0 {
                        break;
                    }
                    output.push_str(&String::from_utf8_lossy(&buf[..n]));
                    total += n;
                    if total >= 4096 {
                        break;
                    }
                }
                Err(ref e) if e.kind() == std::io::ErrorKind::WouldBlock => break,
                Err(ref e) if e.kind() == std::io::ErrorKind::TimedOut => break,
                Err(e) => return Err(e.into()),
            }
        }

        Ok(PtyRead {
            data: output,
            available: total,
        })
    }

    pub fn resize(&self, session_id: &str, cols: u16, rows: u16) -> Result<()> {
        let mut sessions = self.sessions.lock().unwrap();
        let _session = sessions
            .get_mut(session_id)
            .ok_or_else(|| anyhow::anyhow!("PTY session not found"))?;
        // TODO: resize requires holding the master fd, need to store it
        // For now, return Ok
        Ok(())
    }

    pub fn list(&self) -> Vec<PtySession> {
        self.sessions
            .lock()
            .unwrap()
            .values()
            .map(|s| s.session.clone())
            .collect()
    }

    pub fn remove(&self, session_id: &str) -> Option<PtySession> {
        self.sessions
            .lock()
            .unwrap()
            .remove(session_id)
            .map(|s| s.session)
    }

    pub fn count(&self) -> usize {
        self.sessions.lock().unwrap().len()
    }
}
