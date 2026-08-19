use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Mutex;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionInfo {
    pub session_id: String,
    pub workspace: String,
    pub agent_command: String,
    pub created_at: String,
    pub prompt_count: u32,
    pub last_prompt_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionCreateRequest {
    pub workspace: String,
    pub agent_command: Option<String>,
    pub agent_args: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionPromptRequest {
    pub prompt: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionPromptResponse {
    pub session_id: String,
    pub response: String,
    pub prompt_count: u32,
}

pub struct SessionStore {
    sessions: Mutex<HashMap<String, SessionInfo>>,
}

impl SessionStore {
    pub fn new() -> Self {
        Self {
            sessions: Mutex::new(HashMap::new()),
        }
    }

    pub fn create(&self, workspace: String, agent_command: String) -> SessionInfo {
        let session_id = Uuid::now_v7().to_string();
        let now = chrono::Utc::now().to_rfc3339();
        let info = SessionInfo {
            session_id: session_id.clone(),
            workspace,
            agent_command,
            created_at: now,
            prompt_count: 0,
            last_prompt_at: None,
        };
        self.sessions.lock().unwrap().insert(session_id.clone(), info.clone());
        info
    }

    pub fn get(&self, session_id: &str) -> Option<SessionInfo> {
        self.sessions.lock().unwrap().get(session_id).cloned()
    }

    pub fn increment_prompt(&self, session_id: &str) {
        if let Some(s) = self.sessions.lock().unwrap().get_mut(session_id) {
            s.prompt_count += 1;
            s.last_prompt_at = Some(chrono::Utc::now().to_rfc3339());
        }
    }

    pub fn list(&self) -> Vec<SessionInfo> {
        self.sessions.lock().unwrap().values().cloned().collect()
    }

    pub fn remove(&self, session_id: &str) -> Option<SessionInfo> {
        self.sessions.lock().unwrap().remove(session_id)
    }
}
