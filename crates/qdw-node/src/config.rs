use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeConfig {
    pub node_id: String,
    pub listen: String,
    pub workspace_roots: Vec<PathBuf>,
    pub state_db: PathBuf,
}

impl Default for NodeConfig {
    fn default() -> Self {
        let home=std::env::var_os("HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("."));
        Self {
            node_id: hostname(),
            listen: "127.0.0.1:9902".into(),
            workspace_roots: vec![home.clone()],
            state_db: home.join(".local/share/qdw-node/node.db"),
        }
    }
}

fn hostname() -> String {
    std::fs::read_to_string("/etc/hostname").ok().map(|s|s.trim().to_string()).filter(|s|!s.is_empty()).unwrap_or_else(||"qdw-node".into())
}
