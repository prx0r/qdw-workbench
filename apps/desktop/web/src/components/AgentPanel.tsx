import {useState,useEffect,useRef} from 'react';import {api} from '../api';import {useQdw} from '../store';
type Msg={role:'user'|'agent';text:string};
type Session={session_id:string;workspace:string;agent_command:string;created_at:string;prompt_count:number};
export function AgentPanel(){
  const workspace=useQdw(s=>s.workspace);
  const [sessions,setSessions]=useState<Session[]>([]);
  const [activeSession,setActiveSession]=useState<string|null>(null);
  const [messages,setMessages]=useState<Record<string,Msg[]>>({});
  const [input,setInput]=useState('');
  const [busy,setBusy]=useState(false);
  const logRef=useRef<HTMLDivElement>(null);

  useEffect(()=>{api.sessionList().then((s:any)=>setSessions(Array.isArray(s)?s:[])).catch(()=>{})},[]);

  const msgs=activeSession?messages[activeSession]||[]:[];

  useEffect(()=>{if(logRef.current)logRef.current.scrollTop=logRef.current.scrollHeight},[msgs]);

  const startSession=async()=>{
    if(!workspace)return;
    try{
      const s=await api.sessionCreate(workspace,'hermes');
      setSessions(x=>[s,...x]);
      setActiveSession(s.session_id);
      setMessages(x=>({...x,[s.session_id]:[]}));
    }catch{}
  };

  const send=async()=>{
    if(!input.trim()||!activeSession||busy)return;
    const prompt=input;setInput('');setBusy(true);
    setMessages(x=>({...x,[activeSession]:[...(x[activeSession]||[]),{role:'user',text:prompt}]}));
    try{
      const r=await api.sessionPrompt(activeSession,prompt);
      const response=typeof r==='string'?r:(r as any).response||JSON.stringify(r);
      setMessages(x=>({...x,[activeSession]:[...(x[activeSession]||[]),{role:'agent',text:response}]}));
    }catch(e){
      setMessages(x=>({...x,[activeSession]:[...(x[activeSession]||[]),{role:'agent',text:`Error: ${String(e)}`}]}));
    }finally{setBusy(false)}
  };

  const closeSession=async(id:string)=>{
    await api.sessionClose(id).catch(()=>{});
    setSessions(x=>x.filter(s=>s.session_id!==id));
    if(activeSession===id)setActiveSession(null);
  };

  return <section className="agent-panel">
    <div className="agent-head">
      <div><b>Hermes</b><small>{activeSession?'Session active':'No session'} · {workspace||'select workspace'}</small></div>
      <div style={{display:'flex',gap:4}}>
        <button onClick={startSession} disabled={!workspace||busy} style={{fontSize:10}}>New Session</button>
        {activeSession&&<button onClick={()=>closeSession(activeSession)} className="ghost" style={{fontSize:10}}>Close</button>}
      </div>
    </div>
    {sessions.length>1&&<div style={{display:'flex',gap:2,flexWrap:'wrap',margin:'6px 0'}}>
      {sessions.map(s=><button key={s.session_id} className={activeSession===s.session_id?'on':''}
        onClick={()=>setActiveSession(s.session_id)} style={{fontSize:9,padding:'2px 5px'}}>
        {s.prompt_count} msgs
      </button>)}
    </div>}
    <div className="agent-log" ref={logRef}>
      {msgs.length?msgs.map((m,i)=><pre key={i} style={{color:m.role==='user'?'#7cb3ff':'#c0c8d4'}}>{m.role==='user'?'YOU: ':'HERMES: '}{m.text}</pre>)
      :<p>Start a session to begin a multi-turn coding conversation with Hermes.</p>}
    </div>
    <textarea value={input} onChange={e=>setInput(e.target.value)}
      onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}
      placeholder={activeSession?"Ask Hermes... (Enter to send)":"Start a session first"} disabled={!activeSession||busy}/>
    <button disabled={!activeSession||busy||!input.trim()} onClick={send}>{busy?'Thinking...':'Send'}</button>
  </section>
}
