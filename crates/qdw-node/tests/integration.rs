use qdw_node::git;
#[tokio::test]
async fn git_state_uses_real_git_repo(){
    let d=tempfile::tempdir().unwrap();
    let run=|args:&[&str]| std::process::Command::new("git").args(args).current_dir(d.path()).output().unwrap();
    assert!(run(&["init","-q"]).status.success());
    assert!(run(&["config","user.email","test@example.invalid"]).status.success());
    assert!(run(&["config","user.name","QDW Test"]).status.success());
    std::fs::write(d.path().join("a.txt"),"a").unwrap(); assert!(run(&["add","a.txt"]).status.success()); assert!(run(&["commit","-qm","init"]).status.success());
    let s=git::state(d.path()).await.unwrap(); assert!(s.head_oid.as_ref().is_some_and(|x|x.len()>=40)); assert!(!s.dirty);
    std::fs::write(d.path().join("a.txt"),"b").unwrap(); let s=git::state(d.path()).await.unwrap(); assert!(s.dirty);
}
