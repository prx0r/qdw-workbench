use anyhow::Result;
use qdw_node::{app::{self,AppState},config::NodeConfig,process::ProcessRegistry,pty::PtyRegistry,session::SessionStore,store::Store};
use std::sync::Arc;
#[tokio::main]
async fn main()->Result<()> {
    tracing_subscriber::fmt().with_env_filter(tracing_subscriber::EnvFilter::from_default_env()).init();
    let cfg=load_config()?; let addr: std::net::SocketAddr = cfg.listen.parse()?; let store=Store::open(&cfg.state_db)?;
    let state=Arc::new(AppState{config:cfg.clone(),store,processes:ProcessRegistry::default(),sessions:SessionStore::new(),ptys:PtyRegistry::new()});
    tracing::info!(node_id=%cfg.node_id,listen=%cfg.listen,"qdw-node starting");
    let listener=tokio::net::TcpListener::bind(addr).await?; axum::serve(listener,app::router(state)).await?; Ok(())
}
fn load_config()->Result<NodeConfig>{
    let mut args=std::env::args().skip(1); let mut path=None;
    while let Some(a)=args.next(){if a=="--config"{path=args.next();}}
    if let Some(p)=path {Ok(toml::from_str(&std::fs::read_to_string(p)?)?)} else {Ok(NodeConfig::default())}
}
