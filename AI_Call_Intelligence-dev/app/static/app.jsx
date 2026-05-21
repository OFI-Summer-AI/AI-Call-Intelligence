// Update boot message now that Babel is running
(function(){var m=document.getElementById('boot-msg');if(m)m.textContent='Starting…';})();

const {useState,useEffect,useCallback,useRef,useMemo}=React;
const {ResponsiveContainer,BarChart,Bar,XAxis,YAxis,Tooltip,PieChart,Pie,Cell,AreaChart,Area,CartesianGrid}=Recharts;

// ── SVG Icon primitives ────────────────────────────────────────────────────
const Svg=({s=16,c="",children})=>(
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor"
       strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={c}>{children}</svg>
);
const IcoHome=p=><Svg {...p}><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></Svg>;
const IcoFiles=p=><Svg {...p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></Svg>;
const IcoLive=p=><Svg {...p}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></Svg>;
const IcoCal=p=><Svg {...p}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></Svg>;
const IcoReq=p=><Svg {...p}><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></Svg>;
const IcoBack=p=><Svg {...p}><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></Svg>;
const IcoDl=p=><Svg {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></Svg>;
const IcoRefresh=p=><Svg {...p}><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></Svg>;
const IcoUpload=p=><Svg {...p}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></Svg>;
const IcoSearch=p=><Svg {...p}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></Svg>;
const IcoCheck=p=><Svg {...p}><polyline points="20 6 9 17 4 12"/></Svg>;
const IcoAlert=p=><Svg {...p}><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></Svg>;
const IcoShield=p=><Svg {...p}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></Svg>;
const IcoUser=p=><Svg {...p}><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></Svg>;
const IcoClock=p=><Svg {...p}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></Svg>;
const IcoChevD=p=><Svg {...p}><polyline points="6 9 12 15 18 9"/></Svg>;
const IcoChevR=p=><Svg {...p}><polyline points="9 18 15 12 9 6"/></Svg>;
const IcoX=p=><Svg {...p}><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></Svg>;
const IcoLink=p=><Svg {...p}><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></Svg>;
const IcoSpin=({s=16,c=""})=><svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={"spin "+c}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>;
const IcoMenu=p=><Svg {...p}><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></Svg>;
const IcoPanelLeft=p=><Svg {...p}><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></Svg>;
const IcoPanelRight=p=><Svg {...p}><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="15" y1="3" x2="15" y2="21"/></Svg>;

// ── Utilities ──────────────────────────────────────────────────────────────
const API=(typeof window.__API_BASE__!=='undefined'&&window.__API_BASE__&&!window.__API_BASE__.startsWith('__'))?window.__API_BASE__:'http://localhost:8000';
const prettify=id=>{const n=id.replace(/_\d{4}-\d{2}-\d{2}T[\d-]+$/,'');return(n.replace(/_/g,' ').replace(/-/g,' ').replace(/\b\w/g,c=>c.toUpperCase())||id).trim();};
const parseDate=id=>{const m=id.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})/);if(!m)return'';const[,y,mo,d,h,mi]=m;return new Date(+y,+mo-1,+d,+h,+mi).toLocaleString('en',{weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});};
const getDuration=t=>{if(!t?.length)return'-';const p=(t[t.length-1].end||'00:00:00').split(':');try{const m=+p[0]*60+ +p[1];return m?`${m} min`:'<1 min';}catch{return'-';}};
const countMinutes=recs=>recs.reduce((s,r)=>{const t=r.transcript||[];if(!t.length)return s;const p=(t[t.length-1].end||'0:0').split(':');try{return s+ +p[0]*60+ +p[1];}catch{return s;}},0);
const confColor=v=>v==null?'#6b7280':v>=85?'#c9a84c':v>=65?'#a07830':'#1a1a1a';
const scoreColor=v=>v==null?'#6b7280':v>=8?'#c9a84c':v>=6?'#a07830':'#1a1a1a';
const riskColor=n=>n===0?'#c9a84c':n<=3?'#a07830':'#1a1a1a';

// ── API helpers ────────────────────────────────────────────────────────────
const apiFetch=(path,opts)=>fetch(API+path,opts).then(r=>r.json());

// ── Small shared components ────────────────────────────────────────────────
const SectionLabel=({children,mt=false})=>(
  <div className={`text-xs font-bold uppercase tracking-widest text-gold-dark border-b border-gray-200 pb-2 ${mt?'mt-6':''} mb-4`}>{children}</div>
);

const StatCard=({num,label,color='#3b82f6',small=false})=>(
  <div className="bg-gray-50 border border-gray-200 rounded-2xl p-4 text-center hover:border-gold-border transition-all card-hover stat-shimmer">
    <div className={`font-extrabold leading-none ${small?'text-2xl':'text-3xl'}`} style={{color}}>{num}</div>
    <div className="text-xs font-bold uppercase tracking-widest text-gray-400 mt-2">{label}</div>
  </div>
);

const Badge=({label,type='neutral'})=>{
  const map={green:'bg-gold-light text-gold-dark border-gold-border',amber:'bg-gold-light text-gold-dark border-gold-border',red:'bg-gray-900 text-white border-gray-800',blue:'bg-gold-light text-gold-dark border-gold-border',neutral:'bg-gray-100 text-gray-600 border-gray-200'};
  return <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold border ${map[type]||map.neutral}`}>{label}</span>;
};

const FieldCard=({label,value,color='#3b82f6'})=>(
  <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-3" style={{borderLeft:`4px solid ${color}`}}>
    <div className="text-xs font-bold uppercase tracking-wider mb-2" style={{color}}>{label}</div>
    {Array.isArray(value)
      ?<div>{value.filter(Boolean).map((v,i)=><div key={i} className="flex gap-2 py-1 border-b border-gray-100 last:border-0 text-sm text-gray-800"><span style={{color}} className="font-bold mt-0.5">›</span>{v}</div>)}</div>
      :<div className="text-sm font-medium text-gray-900">{value||'—'}</div>}
  </div>
);

const Chip=({label,color='gold'})=>{
  const s={gold:'bg-gold-light text-gold-dark border-gold-border',green:'bg-green-50 text-green-700 border-green-200'};
  return <span className={`inline-block border rounded px-2.5 py-0.5 text-xs font-semibold mr-1.5 mb-1 ${s[color]||s.gold}`}>{label}</span>;
};

const PillList=({title,items,accent})=>(
  <div className="rounded-xl border p-4" style={{background:'#fdf8ee',borderColor:'rgba(201,168,76,0.35)'}}>
    <div className="text-xs font-bold uppercase tracking-wider mb-3" style={{color:accent==='green'?'#c9a84c':'#1a1a1a'}}>{title}</div>
    {items.filter(Boolean).map((x,i)=>(
      <div key={i} className="flex gap-2 py-1.5 border-b last:border-0 text-sm" style={{borderColor:'rgba(201,168,76,0.2)'}}>
        <span className="font-bold mt-0.5" style={{color:accent==='green'?'#c9a84c':'#1a1a1a'}}>›</span>
        <span className="text-gray-800">{x}</span>
      </div>
    ))}
  </div>
);

const NumberedList=({title,items,accent='gold'})=>{
  const c={gold:'#a07830',green:'#c9a84c'};const bg={gold:'#fdf8ee',green:'#fdf8ee'};
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
      <div className="text-xs font-bold uppercase tracking-wider mb-3" style={{color:c[accent]}}>{title}</div>
      {items.filter(Boolean).map((x,i)=>(
        <div key={i} className="flex gap-3 py-1.5 border-b border-gray-100 last:border-0 items-start">
          <span className="w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-extrabold mt-0.5" style={{background:bg[accent],color:c[accent]}}>{i+1}</span>
          <span className="text-sm text-gray-800 leading-relaxed">{x}</span>
        </div>
      ))}
    </div>
  );
};

const Collapsible=({title,icon,children,defaultOpen=true})=>{
  const [open,setOpen]=useState(defaultOpen);
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-2xl overflow-hidden">
      <button onClick={()=>setOpen(v=>!v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-100 transition-all">
        <div className="flex items-center gap-2 text-gold-dark">
          {icon}
          <span className="text-xs font-bold uppercase tracking-widest">{title}</span>
        </div>
        {open?<IcoChevD s={13} c="text-gray-400"/>:<IcoChevR s={13} c="text-gray-400"/>}
      </button>
      {open&&<div className="px-4 pb-4">{children}</div>}
    </div>
  );
};

// ── Sidebar ────────────────────────────────────────────────────────────────
const NAV=[
  {id:'home',label:'Home',Icon:IcoHome},
  {id:'recordings',label:'Recordings',Icon:IcoFiles},
  {id:'live',label:'Live',Icon:IcoLive},
  {id:'calendar',label:'Calendar',Icon:IcoCal},
  {id:'requirements',label:'Requirements',Icon:IcoReq},
];

const Sidebar=({page,setPage,recordings,serverOk,collapsed,onToggle})=>{
  const totalMin=countMinutes(recordings);
  const usedPct=Math.min(Math.round(totalMin/300*100),100);
  return (
    <div className={`${collapsed?'w-14':'w-60'} flex-shrink-0 bg-gray-50 border-r border-gray-200 flex flex-col h-screen sticky top-0 overflow-hidden transition-all duration-200`} style={{minWidth:collapsed?'3.5rem':'15rem'}}>
      {/* Header */}
      <div className={`flex items-center border-b border-gray-200 px-3 py-4 ${collapsed?'justify-center':'justify-between'}`}>
        {!collapsed&&(
          <div className="min-w-0 mr-2">
            <div className="text-base font-extrabold text-gold-dark tracking-tight leading-tight truncate">Clario</div>
            <div className="text-xs text-gray-400 uppercase tracking-widest mt-0.5 truncate">Meeting Intelligence</div>
          </div>
        )}
        <button onClick={onToggle} title={collapsed?'Expand sidebar':'Collapse sidebar'}
          className="p-2 rounded-lg hover:bg-gray-200 text-gray-400 hover:text-gold-dark transition-all flex-shrink-0">
          <IcoPanelLeft s={16}/>
        </button>
      </div>

      {/* Nav */}
      <nav className={`flex-1 p-2 ${collapsed?'flex flex-col items-center gap-1':''}`}>
        {NAV.map(({id,label,Icon})=>(
          <button key={id} onClick={()=>setPage(id)} title={collapsed?label:undefined}
            className={`flex items-center rounded-lg font-medium transition-all
              ${collapsed?'w-10 h-10 justify-center':'w-full gap-3 px-3 py-2.5 mb-0.5 text-sm text-left'}
              ${page===id?'bg-gold-light text-gold-dark border border-gold-border':'text-gray-600 hover:bg-gray-100 hover:text-gold-dark border border-transparent'}`}>
            <Icon s={15}/>
            {!collapsed&&label}
          </button>
        ))}
      </nav>

      {/* Footer */}
      {collapsed?(
        <div className="py-4 flex flex-col items-center gap-2 border-t border-gray-200">
          <span className={`w-2 h-2 rounded-full ${serverOk?'bg-gold':'bg-gray-900'}`} title={serverOk?'Server online':'Server offline'}/>
        </div>
      ):(
        <div className="px-4 py-4 border-t border-gray-200">
          <div className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Usage</div>
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden mb-1.5">
            <div className="h-full bg-gold rounded-full transition-all" style={{width:`${usedPct}%`}}/>
          </div>
          <div className="text-xs text-gray-400">{totalMin} / 300 min</div>
          <div className={`flex items-center gap-1.5 mt-3 text-xs ${serverOk?'text-gold-dark':'text-gray-900'}`}>
            <span className={`w-2 h-2 rounded-full ${serverOk?'bg-gold':'bg-gray-900'}`}/>
            {serverOk?'Server online':'Server offline'}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Recording Card ─────────────────────────────────────────────────────────
const RecordingCard=({rec,onOpen})=>{
  const id=rec.job_id||'';
  const title=prettify(id);
  const date=parseDate(id);
  const dur=getDuration(rec.transcript);
  const f=rec.extracted_fields||{};
  const risks=(rec.risk_report?.risks)||[];
  const conf=f.conformance_score;
  const callS=f.call_score;
  const accentColor=riskColor(risks.length);
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 mb-3 hover:border-gold-border transition-all cursor-pointer fade-in group card-hover recording-card"
         style={{borderLeft:`4px solid ${accentColor}`}} onClick={()=>onOpen(id)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="font-bold text-gray-900 text-base truncate">{title}</div>
          <div className="text-xs text-gray-400 mt-1">{date||'Unknown date'}{dur&&dur!=='-'?` · ${dur}`:''}</div>
          <div className="flex flex-wrap gap-2 mt-3 items-center">
            {conf!=null&&<Badge label={`${Math.round(Number(conf))}% SOP`} type={conf>=85?'green':conf>=65?'amber':'red'}/>}
            {callS!=null&&<Badge label={`${Number(callS).toFixed(1)}/10`} type={callS>=8?'green':callS>=6?'amber':'red'}/>}
            {<Badge label={risks.length?`${risks.length} risk${risks.length>1?'s':''}`:'Clear'} type={risks.length===0?'green':risks.length<=3?'amber':'red'}/>}
          </div>
          {f.call_summary&&<p className="text-xs text-gray-400 italic mt-2 line-clamp-1">{f.call_summary}</p>}
        </div>
        <button className="flex items-center gap-1 text-xs font-semibold text-gold-dark border border-gold-border rounded-lg px-3 py-1.5 hover:bg-gold-light transition-all flex-shrink-0 group-hover:border-gold">
          View <IcoChevR s={13}/>
        </button>
      </div>
    </div>
  );
};

// ── Upload Section ─────────────────────────────────────────────────────────
const UploadSection=({onProcessed})=>{
  const [file,setFile]=useState(null);
  const [status,setStatus]=useState(null);
  const [msg,setMsg]=useState('');
  const [drag,setDrag]=useState(false);
  const ref=useRef();

  const handleFile=f=>{if(f)setFile(f);};
  const onDrop=e=>{e.preventDefault();setDrag(false);const f=e.dataTransfer.files[0];if(f)setFile(f);};

  const process=async()=>{
    if(!file)return;
    try{
      setStatus('uploading'); setMsg('Uploading…');
      const fd=new FormData(); fd.append('file',file);
      const up=await fetch(`${API}/api/upload-recording`,{method:'POST',body:fd}).then(r=>r.json());
      setStatus('processing'); setMsg('Processing with AI (this may take a minute)…');
      const proc=await apiFetch(`/api/process?filename=${encodeURIComponent(up.filename)}`);
      const jobId=proc.job_id;
      for(let i=0;i<600;i++){
        await new Promise(r=>setTimeout(r,5000));
        const s=await apiFetch(`/api/process-status/${jobId}`);
        if(s.status==='done'){setStatus('done');setMsg(`Done — "${prettify(jobId)}" is ready.`);setFile(null);onProcessed(jobId);return;}
        if(s.status==='error'){setStatus('error');setMsg(s.error||'Processing failed');return;}
      }
      setStatus('error');setMsg('Timed out — check server logs.');
    }catch(e){setStatus('error');setMsg(String(e));}
  };

  return (
    <div>
      <div className="text-xs font-bold uppercase tracking-widest text-gold-dark mb-1">Upload Recording</div>
      <div className="text-xs text-gray-400 mb-3">MP4, MOV, WAV, MP3, WebM — transcribed automatically</div>
      <div onDragOver={e=>{e.preventDefault();setDrag(true);}} onDragLeave={()=>setDrag(false)} onDrop={onDrop}
           className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${drag||file?'border-gold bg-gold-light':'border-gray-200 hover:border-gold-border'}`}
           onClick={()=>ref.current?.click()}>
        <input ref={ref} type="file" accept=".mp4,.webm,.mkv,.mov,.avi,.wav,.mp3,.m4a" className="hidden" onChange={e=>handleFile(e.target.files[0])}/>
        <IcoUpload s={22} c="mx-auto mb-2 text-gray-400"/>
        {file?<><div className="text-sm font-semibold text-gray-800 truncate">{file.name}</div><div className="text-xs text-gray-400">{(file.size/1048576).toFixed(1)} MB</div></>
             :<div className="text-sm text-gray-400">Drop file here or click to browse</div>}
      </div>
      {file&&status!=='uploading'&&status!=='processing'&&(
        <button onClick={process} className="w-full mt-3 py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-gold-dark to-gold hover:opacity-90 transition-all btn-gold-shine">
          Process Recording
        </button>
      )}
      {(status==='uploading'||status==='processing')&&(
        <div className="flex items-center gap-2 mt-3 text-sm text-gold-dark"><IcoSpin s={15}/>{msg}</div>
      )}
      {status==='done'&&<div className="mt-3 text-xs text-gold-dark font-medium">{msg}</div>}
      {status==='error'&&<div className="mt-3 text-xs text-gray-900 font-medium">{msg}</div>}
    </div>
  );
};

// ── Agent Join Panel ──────────────────────────────────────────────────────
const AgentPanel=()=>{
  const [meetings,setMeetings]=useState([]);
  const [url,setUrl]=useState('');
  const [platform,setPlatform]=useState(null);
  const [agentSt,setAgentSt]=useState({status:'stopped',uptime_sec:0,sessions_handled:0});
  const [joiningId,setJoiningId]=useState(null); // null | 'manual' | meeting index
  const [msg,setMsg]=useState('');
  const stColor={running:'text-gold-dark',starting:'text-gold',idle:'text-gray-600',stopped:'text-gray-400'};
  const platLabel={meet:'Google Meet',zoom:'Zoom',teams:'Teams'};
  const platColor={meet:'text-gold-dark',zoom:'text-gray-700',teams:'text-gray-600'};

  // Poll agent status every 5s
  useEffect(()=>{
    const poll=()=>apiFetch('/api/agent-status').then(s=>setAgentSt(s)).catch(()=>{});
    poll(); const iv=setInterval(poll,5000); return()=>clearInterval(iv);
  },[]);

  // Fetch calendar meetings every 30s
  useEffect(()=>{
    const load=()=>apiFetch('/api/upcoming-meetings').then(data=>setMeetings(Array.isArray(data)?data:[])).catch(()=>{});
    load(); const iv=setInterval(load,30000); return()=>clearInterval(iv);
  },[]);

  useEffect(()=>{
    const u=url.toLowerCase();
    if(u.includes('meet.google.com'))setPlatform('meet');
    else if(u.includes('zoom.us'))setPlatform('zoom');
    else if(u.includes('teams.microsoft.com')||u.includes('teams.live.com'))setPlatform('teams');
    else setPlatform(null);
  },[url]);

  const isActive=agentSt.status==='running'||agentSt.status==='starting';
  const fmt=t=>{try{return new Date(t).toLocaleTimeString('en',{hour:'2-digit',minute:'2-digit'});}catch{return t;}};

  const doJoin=async(meetUrl,meetPlatform,title,joinKey)=>{
    setJoiningId(joinKey); setMsg('');
    try{
      const r=await apiFetch('/api/join-now',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({meeting_url:meetUrl,platform:meetPlatform,title:title||'Meeting'})});
      if(r.error)setMsg('Error: '+r.error);
      else{setMsg('Bot is joining…');setUrl('');}
    }catch(e){setMsg('Failed: '+String(e));}
    finally{setJoiningId(null);}
  };

  const stopNow=async()=>{
    await apiFetch('/api/agent-stop',{method:'POST'}).catch(()=>{});
    setMsg('Stop signal sent.');
    setAgentSt(s=>({...s,status:'stopped'}));
  };

  return (
    <div>
      {/* Status row */}
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-bold ${stColor[agentSt.status]||'text-gray-400'}`}>● {agentSt.status}</span>
        {isActive&&(
          <button onClick={stopNow} className="text-xs text-red-500 border border-red-200 rounded px-2 py-0.5 hover:bg-red-50 transition-all">
            Stop
          </button>
        )}
      </div>

      {/* Active status card */}
      {isActive&&(
        <div className="bg-gold-light border border-gold-border rounded-lg p-2.5 text-xs mb-3">
          <div className="text-gold-dark font-semibold">Bot is in a meeting</div>
          {agentSt.uptime_sec>0&&<div className="text-gold mt-0.5">{Math.floor(agentSt.uptime_sec/60)}m {agentSt.uptime_sec%60}s uptime · {agentSt.sessions_handled||0} session{agentSt.sessions_handled!==1?'s':''}</div>}
        </div>
      )}

      {!isActive&&(
        <>
          {/* Calendar meetings */}
          {meetings.length>0?(
            <div className="mb-4">
              <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">From your calendar</div>
              {meetings.slice(0,4).map((m,i)=>(
                <div key={i} className="flex items-center gap-2 py-2 border-b border-gray-100 last:border-0">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">{m.title||'Meeting'}</div>
                    <div className={`text-xs ${platColor[m.platform]||'text-gray-400'}`}>{fmt(m.start_time)} · {m.platform}</div>
                  </div>
                  {m.join_url&&(
                    <button onClick={()=>doJoin(m.join_url,m.platform,m.title,i)}
                            disabled={joiningId!==null}
                            className="flex-shrink-0 px-3 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-gold-dark to-gold rounded-lg hover:opacity-90 disabled:opacity-50 flex items-center gap-1 btn-gold-shine">
                      {joiningId===i?<IcoSpin s={11}/>:<IcoLive s={11}/>}
                      {joiningId===i?'…':'Join'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          ):(
            <div className="text-xs text-gray-400 mb-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
              No meetings found in calendar.<br/>
              <span className="text-gold-dark font-medium">Paste a URL below</span> to join manually.
            </div>
          )}

          {/* Manual URL fallback */}
          <div className="text-xs text-gray-400 mb-1.5">Join by URL:</div>
          <div className="relative mb-2">
            <IcoLink s={13} c="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"/>
            <input value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://meet.google.com/…"
                   className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gold transition-all"/>
          </div>
          {platform&&<div className="mb-2 text-xs text-gold-dark font-medium">{platLabel[platform]} detected</div>}
          {url&&!platform&&<div className="mb-2 text-xs text-gray-900 font-medium">Unrecognised URL</div>}
          {platform&&(
            <button onClick={()=>doJoin(url,platform,'Manual Join','manual')} disabled={joiningId!==null}
                    className="w-full py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-gold-dark to-gold hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 btn-gold-shine">
              {joiningId==='manual'?<IcoSpin s={14}/>:<IcoLive s={14}/>}
              {joiningId==='manual'?'Starting…':'Join & Record'}
            </button>
          )}
        </>
      )}

      {msg&&<div className="mt-2 text-xs text-gray-500">{msg}</div>}
    </div>
  );
};

// ── Upcoming Meetings ──────────────────────────────────────────────────────
const UpcomingMeetings=()=>{
  const [meetings,setMeetings]=useState([]);
  useEffect(()=>{apiFetch('/api/upcoming-meetings').then(setMeetings).catch(()=>{});},[]);
  const fmt=t=>{try{return new Date(t).toLocaleTimeString('en',{hour:'2-digit',minute:'2-digit'});}catch{return t;}};
  const platColors={meet:'bg-gold-light text-gold-dark',zoom:'bg-gray-100 text-gray-700',teams:'bg-gray-100 text-gray-600'};
  return (
    <div>
      <div className="text-xs font-bold uppercase tracking-widest text-gold-dark mb-3">Upcoming Meetings</div>
      {meetings.length===0
        ?<div className="text-xs text-gray-400">No upcoming meetings detected — ensure the agent is running.</div>
        :meetings.slice(0,4).map((m,i)=>(
          <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
            <div>
              <div className="text-sm font-medium text-gray-900 truncate max-w-[140px]">{m.title||'Meeting'}</div>
              <div className="text-xs text-gray-400">{fmt(m.start_time)}</div>
            </div>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${platColors[m.platform]||'bg-gray-100 text-gray-600'}`}>{m.platform}</span>
          </div>
        ))
      }
    </div>
  );
};

// ── Home Dashboard ─────────────────────────────────────────────────────────
const QuickAction=({icon,label,desc,onClick,color='#c9a84c'})=>(
  <button onClick={onClick} className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-2xl hover:border-gold-border transition-all text-left w-full card-hover">
    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{background:`${color}18`,color}}>
      {icon}
    </div>
    <div>
      <div className="text-sm font-bold text-gray-900">{label}</div>
      <div className="text-xs text-gray-400">{desc}</div>
    </div>
    <IcoChevR s={14} c="ml-auto text-gray-300"/>
  </button>
);

const HomeDashboard=({recordings,onOpen,onProcessed,setPage,serverOk})=>{
  const needsReview=recordings.filter(r=>r.risk_report?.needs_review).length;
  const thisWeek=recordings.filter(r=>{
    const m=r.job_id?.match(/(\d{4})-(\d{2})-(\d{2})/);
    if(!m)return false;
    const d=new Date(+m[1],+m[2]-1,+m[3]);
    return(Date.now()-d.getTime())<7*86400000;
  }).length;
  const avgConf=recordings.length?Math.round(recordings.reduce((s,r)=>{const v=r.extracted_fields?.conformance_score;return v!=null?s+Number(v):s;},0)/Math.max(1,recordings.filter(r=>r.extracted_fields?.conformance_score!=null).length)):null;
  const recent=recordings.slice(0,3);
  const hour=new Date().getHours();
  const greeting=hour<12?'Good morning':hour<17?'Good afternoon':'Good evening';

  return (
    <div className="p-6 max-w-4xl">
      {/* Greeting */}
      <div className="mb-7">
        <div className="text-xs font-bold uppercase tracking-widest text-gold-dark mb-1">Dashboard</div>
        <h1 className="text-2xl font-extrabold text-gray-900">{greeting}</h1>
        <p className="text-sm text-gray-400 mt-1">{new Date().toLocaleDateString('en',{weekday:'long',month:'long',day:'numeric',year:'numeric'})}</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-3 mb-8">
        <div className="bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer">
          <div className="text-3xl font-extrabold text-gold-dark leading-none">{recordings.length}</div>
          <div className="text-xs font-bold uppercase tracking-widest text-gold mt-2">Total Calls</div>
        </div>
        <div className="bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer">
          <div className="text-3xl font-extrabold text-gray-900 leading-none">{countMinutes(recordings)}</div>
          <div className="text-xs font-bold uppercase tracking-widest text-gold mt-2">Minutes</div>
        </div>
        <div className="bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer">
          <div className="text-3xl font-extrabold leading-none" style={{color:'#a07830'}}>{avgConf!=null?`${avgConf}%`:'—'}</div>
          <div className="text-xs font-bold uppercase tracking-widest text-gold-dark mt-2">Avg SOP</div>
        </div>
        <div className="bg-gradient-to-br from-gold-light to-white border border-gold-border rounded-2xl p-4 text-center card-hover stat-shimmer">
          <div className="text-3xl font-extrabold leading-none text-gray-900">{needsReview}</div>
          <div className="text-xs font-bold uppercase tracking-widest mt-2 text-gold">Needs Review</div>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_280px] gap-6">
        {/* Left: recent recordings */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs font-bold uppercase tracking-widest text-gold-dark">Recent Recordings</div>
            {recordings.length>3&&(
              <button onClick={()=>setPage('recordings')} className="text-xs font-semibold text-gold-dark hover:text-gold border border-gold-border rounded-lg px-3 py-1 hover:bg-gold-light transition-all">
                View all {recordings.length} →
              </button>
            )}
          </div>
          {recent.length===0
            ?<div className="border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center">
               <div className="text-4xl mb-3">🎙</div>
               <div className="font-semibold text-gray-700 mb-1">No recordings yet</div>
               <div className="text-sm text-gray-400">Upload your first call recording to get started</div>
             </div>
            :recent.map(r=><RecordingCard key={r.job_id} rec={r} onOpen={onOpen}/>)
          }
          {thisWeek>0&&(
            <div className="mt-4 text-xs text-gray-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-400 inline-block"/>
              {thisWeek} recording{thisWeek>1?'s':''} this week
            </div>
          )}
        </div>

        {/* Right: quick actions */}
        <div className="space-y-3">
          <div className="text-xs font-bold uppercase tracking-widest text-gold-dark mb-4">Quick Actions</div>
          <QuickAction icon={<IcoUpload s={18}/>} label="Upload Recording" desc="Process a call with AI" onClick={()=>setPage('recordings')} color="#c9a84c"/>
          <QuickAction icon={<IcoLive s={18}/>} label="Live Transcription" desc="Transcribe mic or screen" onClick={()=>setPage('live')} color="#c9a84c"/>
          <QuickAction icon={<IcoCal s={18}/>} label="Calendar" desc="Connect & auto-join meetings" onClick={()=>setPage('calendar')} color="#a07830"/>
          <QuickAction icon={<IcoReq s={18}/>} label="Requirements" desc="View extracted requirements" onClick={()=>setPage('requirements')} color="#c9a84c"/>
          {needsReview>0&&(
            <div className="mt-2 bg-gray-900 border border-gray-700 rounded-xl p-3 text-xs text-white font-medium">
              {needsReview} recording{needsReview>1?'s':''} flagged for review
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Recordings Page ────────────────────────────────────────────────────────
const RecordingsPage=({recordings,onOpen,onProcessed})=>{
  const [q,setQ]=useState('');
  const filtered=q?recordings.filter(r=>(r.job_id||'').toLowerCase().includes(q.toLowerCase())||(r.extracted_fields?.client_name||'').toLowerCase().includes(q.toLowerCase())):recordings;
  const needsReview=recordings.filter(r=>r.risk_report?.needs_review).length;
  return (
    <div className="p-6">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">All Recordings</h1>
          <p className="text-sm text-gray-400 mt-1">{recordings.length} total · {needsReview} flagged</p>
        </div>
        <div className="relative">
          <IcoSearch s={14} c="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"/>
          <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search recordings…"
                 className="pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gold transition-all w-56"/>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3 mb-6">
        <StatCard num={recordings.length} label="Total" color="#c9a84c" small/>
        <StatCard num={countMinutes(recordings)} label="Minutes" color="#a07830" small/>
        <StatCard num={needsReview} label="Needs Review" color={needsReview?'#1a1a1a':'#c9a84c'} small/>
      </div>
      {filtered.length===0
        ?<div className="border border-gray-200 rounded-2xl p-16 text-center">
           <div className="text-gray-300 text-5xl mb-4">🔍</div>
           <div className="font-semibold text-gray-700">No matches</div>
           <div className="text-sm text-gray-400 mt-2">{q?'Try a different search term':'Upload a recording using the panel on the right'}</div>
         </div>
        :filtered.map(r=><RecordingCard key={r.job_id} rec={r} onOpen={onOpen}/>)
      }
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════════════
//  ANALYSIS DASHBOARD
// ══════════════════════════════════════════════════════════════════════════

const TopBar=({rec,onBack,onReanalyze,reanalyzing})=>{
  const id=rec.job_id||'';
  return (
    <div className="flex items-center gap-4 px-6 py-4 border-b border-gray-200 bg-white sticky top-0 z-10">
      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gold-dark transition-all">
        <IcoBack s={16}/> Back
      </button>
      <div className="flex-1 min-w-0">
        <div className="font-bold text-lg text-gray-900 truncate">{prettify(id)}</div>
        <div className="text-xs text-gray-400">{parseDate(id)||'Unknown date'} · {getDuration(rec.transcript)}</div>
      </div>
      <button onClick={onReanalyze} disabled={reanalyzing}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-gold-dark border border-gold-border rounded-lg hover:bg-gold-light transition-all disabled:opacity-50">
        {reanalyzing?<IcoSpin s={13}/>:<IcoRefresh s={13}/>} Re-analyze
      </button>
      <a href={`${API}/api/recordings/${id}/pdf`} target="_blank" rel="noreferrer"
         className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-gold-dark to-gold rounded-lg hover:opacity-90 transition-all btn-gold-shine">
        <IcoDl s={13}/> Download PDF
      </a>
    </div>
  );
};

const ScoreStrip=({f,risks,needsReview})=>{
  const conf=f.conformance_score; const callS=f.call_score; const indS=f.individual_score;
  const items=[
    {num:conf!=null?`${Math.round(Number(conf))}%`:'—',label:'Conformance',sub:f.conformance_status||'',color:confColor(conf)},
    {num:callS!=null?`${Number(callS).toFixed(1)}/10`:'—',label:'Call Quality',sub:(f.call_rating||'').toLowerCase(),color:scoreColor(callS)},
    {num:indS!=null?`${Number(indS).toFixed(1)}/10`:'—',label:'Individual',sub:'',color:scoreColor(indS)},
    {num:risks.length,label:'Risk Items',sub:needsReview?'Needs Review':'Clear',color:riskColor(risks.length)},
  ];
  return (
    <div className="grid grid-cols-4 gap-4 px-6 py-4 border-b border-gray-100">
      {items.map(({num,label,sub,color},i)=>(
        <div key={i} className="bg-gray-50 border border-gray-200 rounded-2xl p-4 text-center hover:border-gold-border transition-all">
          <div className="text-2xl font-extrabold" style={{color}}>{num}</div>
          <div className="text-xs font-bold uppercase tracking-widest text-gray-400 mt-1">{label}</div>
          {sub&&<div className="text-xs font-semibold mt-1.5 uppercase tracking-wider" style={{color}}>{sub}</div>}
        </div>
      ))}
    </div>
  );
};

const TabOverview=({f})=>(
  <div className="fade-in">
    <SectionLabel>Meeting Information</SectionLabel>
    <div className="grid grid-cols-2 gap-3 mb-2">
      <FieldCard label="Client / Account" value={f.client_name} color="#c9a84c"/>
      <FieldCard label="Client Problem"   value={f.client_problem} color="#a07830"/>
      <FieldCard label="Timeline"         value={f.timeline} color="#1a1a1a"/>
      <FieldCard label="Budget"           value={f.budget} color="#c9a84c"/>
    </div>
    {f.call_summary&&(
      <>
        <SectionLabel mt>Call Summary</SectionLabel>
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-800 leading-relaxed mb-2">{f.call_summary}</div>
      </>
    )}
    {(f.call_highlights?.length||f.call_concerns?.length)&&(
      <>
        <SectionLabel mt>Highlights &amp; Concerns</SectionLabel>
        <div className="grid grid-cols-2 gap-3 mb-2">
          {f.call_highlights?.length?<PillList title="Highlights" items={f.call_highlights} accent="green"/>:<div/>}
          {f.call_concerns?.length?<PillList title="Concerns" items={f.call_concerns} accent="red"/>:<div/>}
        </div>
      </>
    )}
    {(f.call_insights?.length||f.next_steps?.length)&&(
      <>
        <SectionLabel mt>Insights &amp; Next Actions</SectionLabel>
        <div className="grid grid-cols-2 gap-3 mb-2">
          {f.call_insights?.length?<NumberedList title="Key Insights" items={f.call_insights} accent="gold"/>:<div/>}
          {f.next_steps?.length?<NumberedList title="Next Actions" items={f.next_steps} accent="green"/>:<div/>}
        </div>
      </>
    )}
    {f.conclusions&&(
      <>
        <SectionLabel mt>Conclusions</SectionLabel>
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-5 text-sm text-gray-800 leading-relaxed" style={{borderLeft:'4px solid #c9a84c'}}>{f.conclusions}</div>
      </>
    )}
    {f.techstack_platform?.length&&(
      <>
        <SectionLabel mt>Tech Stack</SectionLabel>
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          {(Array.isArray(f.techstack_platform)?f.techstack_platform:[f.techstack_platform]).filter(Boolean).map((t,i)=><Chip key={i} label={t}/>)}
        </div>
      </>
    )}
  </div>
);

const SOP_SECTIONS=[
  ['Call Opening',15,'Professional greeting · Purpose clearly stated · Agenda set'],
  ['Needs Discovery',20,'Primary pain point identified · Open-ended questions asked · Understanding confirmed'],
  ['Qualification',15,'Budget explored · Timeline discussed · Decision-makers identified'],
  ['Solution Alignment',20,'Solution matched to problem · Technical requirements discussed · Value proposition communicated'],
  ['Objection Handling',15,'All objections acknowledged · Responded with evidence · Client satisfaction confirmed'],
  ['Call Closing',15,'Next steps defined · Follow-up timeline agreed · Positive close'],
];

const TabConformance=({f})=>{
  const [sopOpen,setSopOpen]=useState(false);
  const conf=f.conformance_score; const pct=conf!=null?Math.round(Number(conf)):null;
  const color=confColor(conf);
  const passed=f.conformance_passed||[]; const missed=f.conformance_missed||[];
  return (
    <div className="fade-in">
      <SectionLabel>SOP Score</SectionLabel>
      {pct!=null&&(
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-5 mb-4">
          <div className="flex items-end gap-3 mb-3">
            <span className="text-4xl font-extrabold" style={{color}}>{pct}</span>
            <span className="text-gray-400 text-lg mb-1">/100</span>
            <span className="ml-2 text-sm font-bold uppercase tracking-widest" style={{color}}>{f.conformance_status||''}</span>
          </div>
          <div className="h-2.5 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{width:`${pct}%`,background:color}}/>
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-400">
            <span>PASS ≥ 85</span><span>REVIEW 65–84</span><span>FAIL &lt; 65</span>
          </div>
        </div>
      )}
      {(passed.length||missed.length)&&(
        <div className="grid grid-cols-2 gap-3 mb-4">
          {passed.length?<PillList title="Criteria Met" items={passed} accent="green"/>:<div/>}
          {missed.length?<PillList title="Criteria Missed" items={missed} accent="red"/>:<div/>}
        </div>
      )}
      <button onClick={()=>setSopOpen(v=>!v)} className="flex items-center gap-2 text-sm text-gold-dark font-semibold hover:text-gold transition-all">
        {sopOpen?<IcoChevD s={14}/>:<IcoChevR s={14}/>} {sopOpen?'Hide':'View'} SOP Criteria Table
      </button>
      {sopOpen&&(
        <div className="mt-3 border border-gray-200 rounded-xl overflow-hidden">
          <div className="grid grid-cols-[160px_60px_1fr] bg-gray-50 border-b border-gray-200">
            {['Section','Max Pts','Criteria'].map(h=><div key={h} className="px-4 py-2 text-xs font-bold uppercase tracking-wider text-gray-400">{h}</div>)}
          </div>
          {SOP_SECTIONS.map(([name,pts,desc])=>(
            <div key={name} className="grid grid-cols-[160px_60px_1fr] border-b border-gray-100 last:border-0 hover:bg-gray-50">
              <div className="px-4 py-3 text-sm font-semibold text-gray-800">{name}</div>
              <div className="px-4 py-3 text-sm text-gold-dark font-bold">{pts}</div>
              <div className="px-4 py-3 text-sm text-gray-500">{desc}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SpeakerCard=({sp})=>{
  const [open,setOpen]=useState(false);
  const c=scoreColor(sp.score);
  return (
    <div className="border border-gray-200 rounded-xl mb-3 overflow-hidden bg-white">
      <button onClick={()=>setOpen(v=>!v)}
              className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-all">
        <div className="w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0" style={{background:`${c}18`,color:c}}>
          <IcoUser s={16}/>
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold text-gray-900">{sp.name||'Speaker'}</div>
          {sp.role&&<div className="text-xs text-gray-400 capitalize">{String(sp.role).replace(/_/g,' ')}</div>}
        </div>
        <div className="text-right flex-shrink-0 mr-3">
          <div className="text-lg font-extrabold" style={{color:c}}>{sp.score!=null?Number(sp.score).toFixed(1):'—'}</div>
          <div className="text-xs text-gray-400">/10</div>
        </div>
        <div className="w-20 flex-shrink-0">
          <div className="text-xs text-gray-400 text-right mb-1">{sp.talk_time_pct||0}% talk</div>
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{width:`${Math.min(sp.talk_time_pct||0,100)}%`,background:c}}/>
          </div>
        </div>
        {open?<IcoChevD s={13} c="text-gray-400 flex-shrink-0 ml-1"/>:<IcoChevR s={13} c="text-gray-400 flex-shrink-0 ml-1"/>}
      </button>
      {open&&(
        <div className="px-4 pb-4 border-t border-gray-100">
          {sp.summary&&<div className="text-sm text-gray-700 mt-3 mb-3 leading-relaxed italic">{sp.summary}</div>}
          {(sp.conformance_passed?.length||sp.conformance_missed?.length)&&(
            <div className="grid grid-cols-2 gap-3">
              {sp.conformance_passed?.length?<PillList title="Conformance Met" items={sp.conformance_passed} accent="green"/>:<div/>}
              {sp.conformance_missed?.length?<PillList title="Conformance Missed" items={sp.conformance_missed} accent="red"/>:<div/>}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const TabIndividual=({f})=>{
  const ind=f.individual_score; const color=scoreColor(ind);
  const confPassed=f.conformance_passed||[]; const confMissed=f.conformance_missed||[];
  const speakers=f.speaker_scores||[];
  const chartData=[
    {name:'Score',value:ind!=null?Number(ind):0},{name:'Remaining',value:ind!=null?10-Number(ind):10}
  ];
  const COLORS=[color,'#e5e7eb'];
  return (
    <div className="fade-in">
      <SectionLabel>Overall Score</SectionLabel>
      <div className="flex gap-6 mb-6">
        <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 flex flex-col items-center justify-center w-44 flex-shrink-0">
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={chartData} cx="50%" cy="50%" innerRadius={45} outerRadius={60} startAngle={90} endAngle={-270} dataKey="value" strokeWidth={0}>
                {chartData.map((_,i)=><Cell key={i} fill={COLORS[i]}/>)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="text-2xl font-extrabold -mt-2" style={{color}}>{ind!=null?Number(ind).toFixed(1):'—'}<span className="text-sm text-gray-400">/10</span></div>
          <div className="text-xs text-gray-400 uppercase tracking-wider mt-1">Individual</div>
        </div>
        <div className="flex-1">
          {f.individual_summary&&<div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-800 leading-relaxed mb-4">{f.individual_summary}</div>}
          {(confPassed.length||confMissed.length)&&(
            <div className="grid grid-cols-2 gap-3">
              {confPassed.length?<PillList title="Conformance Met" items={confPassed} accent="green"/>:<div/>}
              {confMissed.length?<PillList title="Conformance Missed" items={confMissed} accent="red"/>:<div/>}
            </div>
          )}
        </div>
      </div>
      {speakers.length>0&&(
        <>
          <SectionLabel mt>Speaker Breakdown ({speakers.length})</SectionLabel>
          <div className="text-xs text-gray-400 mb-3">Click a speaker to expand their strengths and improvements</div>
          {speakers.map((sp,i)=><SpeakerCard key={i} sp={sp}/>)}
        </>
      )}
      {speakers.length===0&&(
        <div className="border border-dashed border-gray-200 rounded-xl p-6 text-center text-gray-400 text-sm">
          Re-analyze the recording to get per-speaker breakdown
        </div>
      )}
    </div>
  );
};

const TabRisks=({f,risk})=>{
  const risks=risk?.risks||[]; const needsReview=risk?.needs_review;
  const tech=f.techstack_platform;
  return (
    <div className="fade-in">
      <SectionLabel>Risk Report</SectionLabel>
      <div className="flex gap-6">
        <div className="flex-1">
          {risks.length===0
            ?<div className="bg-gold-light border border-gold-border rounded-xl p-5 text-gold-dark font-medium text-sm">No risks identified in this recording.</div>
            :risks.map((r,i)=>{const desc=typeof r==='string'?r:(r.description||r.text||String(r));return(
              <div key={i} className="bg-gold-light border border-gold-border rounded-xl p-4 mb-3 text-sm text-gray-900 leading-relaxed" style={{borderLeft:'3px solid #c9a84c'}}>{desc}</div>
            );})
          }
        </div>
        <div className="w-36 flex-shrink-0">
          <div className={`rounded-xl p-4 text-center border ${needsReview?'bg-gray-900 border-gray-700':'bg-gold-light border-gold-border'}`}>
            {needsReview?<IcoAlert s={22} c="mx-auto mb-2 text-white"/>:<IcoShield s={22} c="mx-auto mb-2 text-gold-dark"/>}
            <div className={`text-xs font-bold uppercase tracking-wider ${needsReview?'text-white':'text-gold-dark'}`}>{needsReview?'Needs Review':'All Clear'}</div>
          </div>
        </div>
      </div>
      {tech&&(Array.isArray(tech)?tech:[tech]).filter(Boolean).length>0&&(
        <>
          <SectionLabel mt>Tech Stack</SectionLabel>
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
            {(Array.isArray(tech)?tech:[tech]).filter(Boolean).map((t,i)=><Chip key={i} label={t}/>)}
          </div>
        </>
      )}
    </div>
  );
};

const TabRequirements=({f})=>{
  const reqs=f.strict_requirements||[];
  const [q,setQ]=useState('');
  const filtered=useMemo(()=>reqs.filter(r=>{const s=typeof r==='string'?r:(r.title||r.description||String(r));return!q||s.toLowerCase().includes(q.toLowerCase());}),[ reqs,q]);
  if(!reqs.length)return <div className="text-sm text-gray-400 pt-4">No requirements extracted for this recording.</div>;
  return (
    <div className="fade-in">
      <SectionLabel>Requirements <span className="font-normal text-gray-400 normal-case tracking-normal text-xs">({reqs.length} items)</span></SectionLabel>
      <div className="relative mb-4">
        <IcoSearch s={14} c="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"/>
        <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search requirements…"
               className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:border-gold"/>
      </div>
      <div className="text-xs text-gray-400 mb-3">Showing {filtered.length} of {reqs.length}</div>
      <div className="max-h-[520px] overflow-y-auto pr-1">
        {filtered.map((r,i)=>{
          const text=typeof r==='string'?r:(r.title||r.description||String(r));
          const desc=typeof r==='object'?r.description:null;
          return(
            <div key={i} className="flex gap-3 items-start py-3 border-b border-gray-100 last:border-0 hover:bg-gray-50 rounded px-1 transition-all">
              <span className="bg-gold-light text-gold-dark border border-gold-border rounded px-2 py-0.5 text-xs font-bold flex-shrink-0 mt-0.5">REQ {String(i+1).padStart(2,'0')}</span>
              <div>
                <div className="text-sm text-gray-900 leading-snug">{text}</div>
                {desc&&desc!==text&&<div className="text-xs text-gray-400 mt-1">{desc}</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const TabTranscript=({transcript,jobId})=>{
  const sparkData=useMemo(()=>{
    if(!transcript?.length)return[];
    const step=Math.max(1,Math.floor(transcript.length/60));
    return transcript.filter((_,i)=>i%step===0).map(s=>({t:s.start?.slice(0,5)||'',len:(s.text||'').length}));
  },[transcript]);
  const full=(transcript||[]).map(s=>`[${(s.start||'').slice(0,8)}] ${s.text||''}`).join('\n');
  const dl=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([full],{type:'text/plain'}));a.download=`${jobId}_transcript.txt`;a.click();};
  if(!transcript?.length)return <div className="text-sm text-gray-400 pt-4">No transcript available.</div>;
  return (
    <div className="fade-in">
      <SectionLabel>Activity</SectionLabel>
      <div className="mb-5 bg-gray-50 border border-gray-200 rounded-xl p-3">
        <ResponsiveContainer width="100%" height={90}>
          <AreaChart data={sparkData} margin={{top:4,right:0,left:0,bottom:0}}>
            <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#c9a84c" stopOpacity={0.4}/><stop offset="100%" stopColor="#c9a84c" stopOpacity={0}/></linearGradient></defs>
            <Area type="monotone" dataKey="len" stroke="#c9a84c" fill="url(#g)" strokeWidth={1.5} dot={false}/>
            <XAxis dataKey="t" tick={{fontSize:9,fill:'#9ca3af'}} axisLine={false} tickLine={false} interval="preserveStartEnd"/>
            <YAxis hide/>
            <Tooltip contentStyle={{fontSize:11,borderRadius:6,border:'1px solid #e5e7eb'}} labelStyle={{color:'#6b7280'}} formatter={v=>[v+' chars','Length']}/>
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <SectionLabel>Segments · {transcript.length}</SectionLabel>
      <div className="max-h-[480px] overflow-y-auto border border-gray-200 rounded-xl divide-y divide-gray-100">
        {transcript.map((s,i)=>(
          <div key={i} className="flex gap-3 px-4 py-3 hover:bg-gray-50 transition-all">
            <span className="text-xs font-mono text-gray-400 flex-shrink-0 mt-0.5 w-14">{(s.start||'').slice(0,8)}</span>
            <span className="text-sm text-gray-800 leading-relaxed">{s.text||''}</span>
          </div>
        ))}
      </div>
      <button onClick={dl} className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-gold-dark border border-gold-border rounded-lg px-4 py-2 hover:bg-gold-light transition-all">
        <IcoDl s={13}/> Download Transcript (.txt)
      </button>
    </div>
  );
};

const TABS=[
  {id:'overview',label:'Overview',Icon:IcoHome},
  {id:'requirements',label:'Requirements',Icon:IcoReq},
  {id:'conformance',label:'Conformance',Icon:IcoCheck},
  {id:'individual',label:'Individual',Icon:IcoUser},
  {id:'risks',label:'Risks',Icon:IcoShield},
  {id:'transcript',label:'Transcript',Icon:IcoFiles},
];

const AnalysisDashboard=({rec,onBack,onUpdated})=>{
  const [tab,setTab]=useState('overview');
  const [reanalyzing,setReanalyzing]=useState(false);
  const f=rec.extracted_fields||{}; const risk=rec.risk_report||{}; const risks=risk.risks||[];

  const reanalyze=async()=>{
    setReanalyzing(true);
    try{const updated=await apiFetch(`/api/recordings/${rec.job_id}/reanalyze`,{method:'POST'});onUpdated(updated);}
    catch(e){alert('Re-analysis failed: '+e);}
    finally{setReanalyzing(false);}
  };

  return (
    <div className="min-h-screen bg-white">
      <TopBar rec={rec} onBack={onBack} onReanalyze={reanalyze} reanalyzing={reanalyzing}/>
      <ScoreStrip f={f} risks={risks} needsReview={risk.needs_review}/>
      <div className="flex border-b border-gray-200 px-6 bg-white sticky top-[69px] z-10">
        {TABS.map(({id,label,Icon})=>(
          <button key={id} onClick={()=>setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-all
              ${tab===id?'border-gold text-gold-dark':'border-transparent text-gray-500 hover:text-gray-800'}`}>
            <Icon s={13}/>{label}
          </button>
        ))}
      </div>
      <div className="px-6 py-6 max-w-5xl">
        {tab==='overview'&&<TabOverview f={f}/>}
        {tab==='conformance'&&<TabConformance f={f}/>}
        {tab==='individual'&&<TabIndividual f={f}/>}
        {tab==='risks'&&<TabRisks f={f} risk={risk}/>}
        {tab==='requirements'&&<TabRequirements f={f}/>}
        {tab==='transcript'&&<TabTranscript transcript={rec.transcript} jobId={rec.job_id}/>}
      </div>
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════════════
//  SECONDARY PAGES
// ══════════════════════════════════════════════════════════════════════════

const LivePage=()=>(
  <div className="flex-1 p-0">
    <div className="flex-1 flex flex-col items-center justify-center gap-6 p-10">
      <div className="text-center">
        <div className="text-gold-dark font-bold text-lg mb-2">Live Transcription</div>
        <p className="text-sm text-gray-400 mb-6 max-w-sm">
          Opens in a new tab so the browser can access your microphone and screen audio without restrictions.
        </p>
        <a href={`${API}/static/live_transcription.html`} target="_blank" rel="noopener noreferrer"
           className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-white text-sm"
           style={{background:'linear-gradient(135deg,#c9a84c,#a07830)'}}>
          Open Live Transcription
        </a>
      </div>
    </div>
  </div>
);

const CalendarPage=()=>{
  const googleOk=true;
  return (
    <div className="p-6 max-w-2xl fade-in">
      <h1 className="text-2xl font-extrabold text-gray-900 mb-1">Calendar Integration</h1>
      <p className="text-sm text-gray-400 mb-6">Connect your calendar to automatically join and record meetings</p>
      <div className="border border-gray-200 rounded-2xl overflow-hidden mb-6">
        {[['Google Calendar','Auto-joins Zoom, Meet and Teams from Google Calendar',googleOk],['Microsoft Outlook','Auto-joins Teams meetings from Outlook calendar',false]].map(([name,desc,ok])=>(
          <div key={name} className="flex items-center justify-between px-5 py-4 border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-all">
            <div><div className="font-semibold text-gray-900 text-sm">{name}</div><div className="text-xs text-gray-400 mt-0.5">{desc}</div></div>
            <Badge label={ok?'Connected':'Not connected'} type={ok?'green':'neutral'}/>
          </div>
        ))}
      </div>
      <details className="border border-gray-200 rounded-xl mb-3">
        <summary className="px-5 py-3 cursor-pointer text-sm font-semibold text-gold-dark hover:bg-gold-light transition-all rounded-xl">How to connect Google Calendar</summary>
        <div className="px-5 pb-4 text-sm text-gray-600 leading-relaxed pt-2">
          <ol className="list-decimal list-inside space-y-1">
            <li>Go to console.cloud.google.com → create a project</li>
            <li>Enable <strong>Google Calendar API</strong></li>
            <li>Create OAuth 2.0 credentials (Desktop app) → download as <code className="bg-gray-100 px-1 rounded">credentials.json</code></li>
            <li>Place <code className="bg-gray-100 px-1 rounded">credentials.json</code> in the project root</li>
            <li>Set <code className="bg-gray-100 px-1 rounded">ENABLE_GOOGLE_CALENDAR=true</code> in <code className="bg-gray-100 px-1 rounded">.env</code></li>
            <li>Run <code className="bg-gray-100 px-1 rounded">python -m app.main_agent</code> — browser opens for OAuth on first run</li>
          </ol>
        </div>
      </details>
      <details className="border border-gray-200 rounded-xl">
        <summary className="px-5 py-3 cursor-pointer text-sm font-semibold text-gold-dark hover:bg-gold-light transition-all rounded-xl">How to connect Microsoft Outlook / Teams</summary>
        <div className="px-5 pb-4 text-sm text-gray-600 leading-relaxed pt-2">
          <ol className="list-decimal list-inside space-y-1">
            <li>Go to portal.azure.com → App registrations → New</li>
            <li>Add delegated permission: <strong>Calendars.Read</strong> (Microsoft Graph)</li>
            <li>Set <code className="bg-gray-100 px-1 rounded">ENABLE_OUTLOOK_CALENDAR=true</code> and <code className="bg-gray-100 px-1 rounded">MICROSOFT_CLIENT_ID</code> in <code className="bg-gray-100 px-1 rounded">.env</code></li>
            <li>Run <code className="bg-gray-100 px-1 rounded">python -m app.main_agent</code> — device-code login appears once</li>
          </ol>
        </div>
      </details>
    </div>
  );
};

const RequirementsPage=()=>(
  <div className="p-6 max-w-2xl fade-in">
    <h1 className="text-2xl font-extrabold text-gray-900 mb-1">Requirements Extraction</h1>
    <p className="text-sm text-gray-400 mb-6">Open any recording and go to the <strong>Requirements</strong> tab to see extracted requirements.</p>
    <div className="border border-gray-200 rounded-2xl p-8 text-center text-gray-400">
      <IcoReq s={32} c="mx-auto mb-3 opacity-30"/>
      <div className="font-semibold text-gray-600 mb-1">No standalone report</div>
      <div className="text-sm">Requirements are extracted automatically during recording processing and viewable per-recording in the analysis dashboard.</div>
    </div>
  </div>
);

// ══════════════════════════════════════════════════════════════════════════
//  APP ROOT
// ══════════════════════════════════════════════════════════════════════════
const App=()=>{
  const [page,setPage]=useState('home');
  const [selectedId,setSelectedId]=useState(null);
  const [recordings,setRecordings]=useState([]);
  const [loading,setLoading]=useState(true);
  const [serverOk,setServerOk]=useState(false);
  const [sidebarOpen,setSidebarOpen]=useState(true);
  const [rightOpen,setRightOpen]=useState(true);

  const loadRecordings=useCallback(()=>{
    apiFetch('/api/recordings').then(data=>{setRecordings(Array.isArray(data)?data:[]);setServerOk(true);}).catch(()=>setServerOk(false)).finally(()=>setLoading(false));
  },[]);

  useEffect(()=>{loadRecordings();apiFetch('/health').then(()=>setServerOk(true)).catch(()=>{});},[loadRecordings]);

  const changePage=p=>{setPage(p);setSelectedId(null);};
  const openRecording=id=>setSelectedId(id);
  const closeRecording=()=>setSelectedId(null);

  const handleProcessed=jobId=>{
    loadRecordings();
    setTimeout(()=>{setSelectedId(jobId);setPage('recordings');},400);
  };

  const handleUpdated=updated=>{
    setRecordings(prev=>prev.map(r=>r.job_id===updated.job_id?updated:r));
  };

  const selectedRec=selectedId?recordings.find(r=>r.job_id===selectedId):null;
  if(selectedRec){
    return <AnalysisDashboard rec={selectedRec} onBack={closeRecording} onUpdated={handleUpdated}/>;
  }

  const isFullWidth=page==='live';
  const loadingSpinner=<div className="flex items-center justify-center h-full text-gray-400 gap-2"><IcoSpin s={18}/>Loading…</div>;

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      <Sidebar page={page} setPage={changePage} recordings={recordings} serverOk={serverOk} collapsed={!sidebarOpen} onToggle={()=>setSidebarOpen(v=>!v)}/>
      <div className={`flex-1 overflow-y-auto ${isFullWidth?'flex flex-col':''}`}>
        {page==='live'&&<LivePage/>}
        {page==='calendar'&&<CalendarPage/>}
        {page==='requirements'&&<RequirementsPage/>}

        {/* HOME: dashboard overview + right panel */}
        {page==='home'&&(
          loading ? loadingSpinner :
          <div className="flex gap-0 h-full">
            <div className="flex-1 min-w-0 overflow-y-auto">
              <HomeDashboard recordings={recordings} onOpen={openRecording} onProcessed={handleProcessed} setPage={changePage} serverOk={serverOk}/>
            </div>
            <div className={`${rightOpen?'w-72':'w-10'} flex-shrink-0 border-l border-gray-200 h-screen sticky top-0 flex flex-col overflow-hidden transition-all duration-200`} style={{minWidth:rightOpen?'18rem':'2.5rem'}}>
              <div className={`flex border-b border-gray-200 py-2.5 flex-shrink-0 ${rightOpen?'justify-end px-3':'justify-center'}`}>
                <button onClick={()=>setRightOpen(v=>!v)} title={rightOpen?'Hide panel':'Show panel'}
                        className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gold-dark transition-all">
                  <IcoPanelRight s={15}/>
                </button>
              </div>
              {rightOpen&&(
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  <Collapsible title="Upload Recording" icon={<IcoUpload s={13}/>} defaultOpen={true}>
                    <UploadSection onProcessed={handleProcessed}/>
                  </Collapsible>
                  <Collapsible title="Join as Organizer" icon={<IcoLive s={13}/>} defaultOpen={true}>
                    <AgentPanel/>
                  </Collapsible>
                  <Collapsible title="Upcoming Meetings" icon={<IcoCal s={13}/>} defaultOpen={true}>
                    <UpcomingMeetings/>
                  </Collapsible>
                </div>
              )}
            </div>
          </div>
        )}

        {/* RECORDINGS: full list + upload panel */}
        {page==='recordings'&&(
          loading ? loadingSpinner :
          <div className="flex gap-0 h-full">
            <div className="flex-1 min-w-0 overflow-y-auto">
              <RecordingsPage recordings={recordings} onOpen={openRecording} onProcessed={handleProcessed}/>
            </div>
            <div className={`${rightOpen?'w-72':'w-10'} flex-shrink-0 border-l border-gray-200 h-screen sticky top-0 flex flex-col overflow-hidden transition-all duration-200`} style={{minWidth:rightOpen?'18rem':'2.5rem'}}>
              <div className={`flex border-b border-gray-200 py-2.5 flex-shrink-0 ${rightOpen?'justify-end px-3':'justify-center'}`}>
                <button onClick={()=>setRightOpen(v=>!v)} title={rightOpen?'Hide panel':'Show panel'}
                        className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gold-dark transition-all">
                  <IcoPanelRight s={15}/>
                </button>
              </div>
              {rightOpen&&(
                <div className="flex-1 overflow-y-auto p-4 space-y-3">
                  <Collapsible title="Upload Recording" icon={<IcoUpload s={13}/>} defaultOpen={true}>
                    <UploadSection onProcessed={handleProcessed}/>
                  </Collapsible>
                  <Collapsible title="Join as Organizer" icon={<IcoLive s={13}/>} defaultOpen={false}>
                    <AgentPanel/>
                  </Collapsible>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
