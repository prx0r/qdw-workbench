import {useState,useEffect,useRef,useCallback} from 'react';import {api} from '../api';import {useQdw} from '../store';
export function TerminalPanel(){
  const workspace=useQdw(s=>s.workspace);
  const [ptyId,setPtyId]=useState<string|null>(null);
  const [output,setOutput]=useState('');
  const [input,setInput]=useState('');
  const [busy,setBusy]=useState(false);
  const outRef=useRef<HTMLPreElement>(null);
  const pollRef=useRef<number|null>(null);

  const spawnPty=async()=>{
    if(!workspace)return;
    try{
      const r=await api.ptySpawn(workspace,undefined,80,24);
      setPtyId(r.session_id);
      setOutput('');
    }catch{}
  };

  const readOutput=useCallback(async()=>{
    if(!ptyId)return;
    try{
      const r=await api.ptyRead(ptyId);
      if(r.data){setOutput(x=>x+r.data)}
    }catch{}
  },[ptyId]);

  useEffect(()=>{
    if(ptyId){
      pollRef.current=window.setInterval(readOutput,200);
      return()=>{if(pollRef.current)clearInterval(pollRef.current)};
    }
  },[ptyId,readOutput]);

  useEffect(()=>{if(outRef.current)outRef.current.scrollTop=outRef.current.scrollHeight},[output]);

  const sendCommand=async()=>{
    if(!input.trim()||!ptyId||busy)return;
    const cmd=input;setInput('');setBusy(true);
    setOutput(x=>x+`$ ${cmd}\n`);
    try{
      await api.ptyWrite(ptyId,cmd+'\n');
    }catch(e){setOutput(x=>x+`Error: ${String(e)}\n`)}
    finally{setBusy(false)}
  };

  const closePty=async()=>{
    if(!ptyId)return;
    if(pollRef.current)clearInterval(pollRef.current);
    await api.ptyClose(ptyId).catch(()=>{});
    setPtyId(null);setOutput('');
  };

  if(!ptyId){
    return <div className="terminal"><div style={{padding:8}}>
      <button onClick={spawnPty} disabled={!workspace}>Open Terminal</button>
      {!workspace&&<small style={{marginLeft:8}}>Select a workspace first</small>}
    </div></div>;
  }

  return <div className="terminal"><div style={{display:'flex',gap:4,padding:'4px 6px',borderBottom:'1px solid #252b33'}}>
    <small style={{color:'#747f8e'}}>PTY · {workspace?.split('/').pop()}</small>
    <button onClick={closePty} className="ghost" style={{fontSize:9,marginLeft:'auto'}}>Close</button>
  </div>
  <pre ref={outRef} style={{height:120,overflow:'auto',padding:'4px 6px',margin:0,fontFamily:'ui-monospace,monospace',fontSize:11,color:'#bfc8d4',whiteSpace:'pre-wrap',wordBreak:'break-word'}}>{output}</pre>
  <div style={{display:'flex',gap:4,padding:'4px 6px',borderTop:'1px solid #252b33'}}>
    <input value={input} onChange={e=>setInput(e.target.value)}
      onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault();sendCommand()}}}
      placeholder="$ " style={{flex:1,background:'#0d1014',color:'#dce1e8',border:'1px solid #303844',padding:'4px 6px',fontFamily:'ui-monospace,monospace',fontSize:11}}/>
    <button onClick={sendCommand} disabled={busy||!input.trim()}>Send</button>
  </div></div>;
}
