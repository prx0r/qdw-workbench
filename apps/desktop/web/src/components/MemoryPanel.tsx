import {useEffect,useState} from 'react';import {api} from '../api';
type MemEntry={id:number;kind:string;source:string;content:string;created_at:string};
export function MemoryPanel(){const [entries,setEntries]=useState<MemEntry[]>([]);const [query,setQuery]=useState('');const [filter,setFilter]=useState<string|undefined>();
useEffect(()=>{api.memoryRecent(filter,20).then(setEntries).catch(()=>setEntries([]))},[filter]);
const search=async()=>{if(!query.trim())return;try{const r=await api.memorySearch(query,20);setEntries(r)}catch{}};
return <section><h3>Memory</h3><div style={{display:'flex',gap:4,marginBottom:8}}>
<input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==='Enter'&&search()} placeholder="Search memory…" style={{flex:1,background:'#0d1014',color:'white',border:'1px solid #303844',padding:'4px 6px'}}/>
<button onClick={search}>Search</button></div><div style={{display:'flex',gap:4,marginBottom:8}}>
{['','handover','product','approval','manual'].map(k=><button key={k} className={filter===k||(!k&&!filter)?'on':''} onClick={()=>setFilter(k||undefined)} style={{fontSize:10,padding:'2px 6px'}}>{k||'All'}</button>)}</div>
{entries.map(e=><div className="card" key={e.id}><div style={{display:'flex',justifyContent:'space-between'}}><b style={{fontSize:11}}>{e.kind}</b><small>{new Date(e.created_at).toLocaleTimeString()}</small></div><small>{e.source}</small><p style={{margin:0,fontSize:11,color:'#abb4c0'}}>{e.content.slice(0,200)}{e.content.length>200?'…':''}</p></div>)}
{!entries.length&&<small>No memory entries yet.</small>}</section>}
