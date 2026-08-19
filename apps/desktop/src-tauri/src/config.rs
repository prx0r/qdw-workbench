use serde::{Deserialize,Serialize}; use std::path::PathBuf;
#[derive(Debug,Clone,Serialize,Deserialize)]pub struct NodeEndpoint{pub id:String,pub url:String,pub ssh:Option<SshNode>}
#[derive(Debug,Clone,Serialize,Deserialize)]pub struct SshNode{pub host:String,pub remote_port:u16,pub local_port:u16}
#[derive(Debug,Clone,Serialize,Deserialize)]pub struct Config{pub qdw_url:String,pub nodes:Vec<NodeEndpoint>,pub workspaces:Vec<PathBuf>}
impl Default for Config{fn default()->Self{Self{qdw_url:"http://127.0.0.1:9911".into(),nodes:vec![NodeEndpoint{id:"local".into(),url:"http://127.0.0.1:9902".into(),ssh:None}],workspaces:vec![]}}}
pub fn path()->PathBuf{let h=std::env::var_os("HOME").map(PathBuf::from).unwrap_or_else(||PathBuf::from("."));h.join(".config/qdw-workbench/config.toml")}
pub fn load()->Config{std::fs::read_to_string(path()).ok().and_then(|s|toml::from_str(&s).ok()).unwrap_or_default()}
