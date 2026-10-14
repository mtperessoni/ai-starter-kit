import json,os,glob,collections,re,datetime as dt
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
def P(t): return dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
def analyze(f):
    ents=[]
    for l in open(f,encoding='utf-8',errors='ignore'):
        try:e=json.loads(l)
        except:continue
        if e.get('timestamp'): ents.append(e)
    model=tool=human=0.0; out=inp=cr=cw=0; pend={}; repos=collections.Counter(); prev=None; ntool=0
    toolby=collections.Counter()
    for e in ents:
        t=P(e['timestamp']); m=e.get('message') or {}
        c=m.get('content')
        if e.get('type')=='assistant':
            u=m.get('usage') or {}
            out+=u.get('output_tokens',0);inp+=u.get('input_tokens',0);cr+=u.get('cache_read_input_tokens',0);cw+=u.get('cache_creation_input_tokens',0)
            if prev is not None and prev[1]!='assistant': model+=min(t-prev[0],900)
            elif prev is not None: model+=min(t-prev[0],900)
            if isinstance(c,list):
                for b in c:
                    if b.get('type')=='tool_use':
                        pend[b['id']]=(t,b.get('name'),json.dumps(b.get('input',{}))[:300]); ntool+=1
            prev=(t,'assistant')
        elif e.get('type')=='user':
            if isinstance(c,list) and any(b.get('type')=='tool_result' for b in c if isinstance(b,dict)):
                for b in c:
                    if isinstance(b,dict) and b.get('type')=='tool_result' and b.get('tool_use_id') in pend:
                        t0,n,i=pend.pop(b['tool_use_id']); d=t-t0
                        tool+=d; toolby[n]+=d
                prev=(t,'tool')
            else:
                if prev is not None and isinstance(c,str) and not c.startswith('<task-notification') and 'agent-message' not in c[:200]:
                    human+=t-prev[0]
                prev=(t,'user')
        for r in ['ai-starter-kit','clara-ai','modulo-integrador','agora-consulta-fe']:
            if r in json.dumps(c)[:5000] if c else False: repos[r]+=1
    span=(P(ents[-1]['timestamp'])-P(ents[0]['timestamp'])) if ents else 0
    return dict(span=span,model=model,tool=tool,human=human,out=out,inp=inp,cr=cr,cw=cw,ntool=ntool,toolby=toolby,repos=repos,n=len(ents))
rows=[]
for f in sorted(glob.glob(root+'/*.jsonl')):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    sid=os.path.basename(f)[:8]
    m=analyze(f)
    if m['span']<3600: continue
    subs=glob.glob(f[:-6]+'/subagents/*.jsonl')
    S=[analyze(s) for s in subs]
    sm=sum(x['model'] for x in S); st=sum(x['tool'] for x in S); stok=sum(x['out'] for x in S); scr=sum(x['cr'] for x in S)
    st_tool=collections.Counter()
    for x in S: st_tool.update(x['toolby'])
    rp=collections.Counter(); rp.update(m['repos'])
    for x in S: rp.update(x['repos'])
    rows.append((sid,m,len(S),sm,st,stok,scr,rp,st_tool))
    print(f"\n## {sid} span={m['span']/3600:.1f}h | MAIN model={m['model']/3600:.1f}h tool={m['tool']/3600:.1f}h human={m['human']/3600:.1f}h out={m['out']/1e3:.0f}k cacheRead={m['cr']/1e6:.1f}M | SUBS n={len(S)} model={sm/3600:.1f}h tool={st/3600:.1f}h out={stok/1e3:.0f}k cacheRead={scr/1e6:.1f}M")
    print("   main tool:",{k:round(v/60) for k,v in m['toolby'].most_common(5)},"min")
    print("   sub tool :",{k:round(v/60) for k,v in st_tool.most_common(5)},"min")
    print("   repos    :",dict(rp.most_common(4)))
