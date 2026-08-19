//! ACP integration boundary using the official Agent Client Protocol Rust SDK.
//!
//! Supports both one-shot and persistent interactive sessions.
use agent_client_protocol::{AcpAgent, AcpAgentConfig, Agent, Client};
use agent_client_protocol::schema::{ProtocolVersion, v1::{ContentBlock, InitializeRequest, NewSessionRequest, PromptRequest, TextContent}};
use anyhow::Result;
use std::path::PathBuf;

#[derive(Debug, Clone)]
pub struct AgentLaunch {
    pub command: String,
    pub args: Vec<String>,
    pub cwd: PathBuf,
}

pub fn component(spec: &AgentLaunch) -> AcpAgent {
    AcpAgent::new(AcpAgentConfig::new(&spec.command).args(spec.args.clone()))
}

pub fn hermes(cwd: PathBuf) -> AcpAgent {
    component(&AgentLaunch {
        command: "hermes".into(),
        args: vec!["acp".into()],
        cwd,
    })
}

/// One-shot ACP execution: send prompt, get response, session ends.
pub async fn one_shot(spec: AgentLaunch, prompt: String) -> Result<String> {
    let cwd = spec.cwd.clone();
    let agent = component(&spec);
    let text = Client
        .builder()
        .connect_with(agent, |connection: agent_client_protocol::ConnectionTo<Agent>| async move {
            connection
                .send_request(InitializeRequest::new(ProtocolVersion::V1))
                .block_task()
                .await?;

            let session_response = connection
                .send_request(NewSessionRequest::new(cwd))
                .block_task()
                .await?;

            let prompt_response = connection
                .send_request(PromptRequest::new(
                    session_response.session_id,
                    vec![ContentBlock::Text(TextContent::new(prompt))],
                ))
                .block_task()
                .await?;

            // The prompt response contains the final stop_reason but not the text directly
            // Text comes via SessionNotification with AgentMessageChunk
            // For one-shot, we return the stop reason as confirmation
            Ok(format!("Session completed with stop reason: {:?}", prompt_response.stop_reason))
        })
        .await?;
    Ok(text)
}

/// Persistent session handle.
pub struct PersistentSession {
    pub session_id: String,
    pub workspace: PathBuf,
    pub agent_command: String,
}

/// Session info for the API
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SessionInfo {
    pub session_id: String,
    pub workspace: String,
    pub agent: String,
    pub created_at: String,
    pub prompt_count: u32,
}
