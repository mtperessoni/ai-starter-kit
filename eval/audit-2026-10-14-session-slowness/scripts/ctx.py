import json,os,glob,collections,datetime as dt,statistics as st
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
P=lambda t: dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
b=collections.defaultdict(list); outs=collections.defaultdict(list); tot=collections.Counter(); totn=collections.Counter()
for f in glob.glob(root+'/*/subagents/*.jsonl')+glob.glob(root+'/*.jsonl'):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    who='sub' if 'subagents' in f else 'main'
    prev=None; seen={}
    for l in open(f,encoding='utf-8',errors='ignore'):
        if not l.startswith('{'): continue
        e=json.loads(l)
        if not e.get('timestamp'): continue
        t=P(e['timestamp'])
        if e.get('type')=='assistant':
            m=e.get('message') or {}; mid=m.get('id')
            if mid not in seen and prev is not None:
                u=m.get('usage') or {}
                ctx=u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0)
                lat=t-prev
                if 0<lat<900:
                    mod=(m.get('model') or '?').replace('claude-','')[:9]
                    bk='<50k' if ctx<5e4 else '50-100k' if ctx<1e5 else '100-200k' if ctx<2e5 else '200-400k' if ctx<4e5 else '>400k'
                    b[(mod,bk)].append(lat); tot[(who,mod)]+=lat; totn[(who,mod)]+=1
                seen[mid]=1
            elif mid not in seen: seen[mid]=1
        prev=t
order=['<50k','50-100k','100-200k','200-400k','>400k']
for mod in ['opus-5-5','sonnet-5-']:
    print(mod)
    for bk in order:
        v=b.get((mod,bk),[])
        if v: print(f"   ctx {bk:9} turns={len(v):6} p50={st.median(v):5.1f}s mean={st.mean(v):5.1f}s total={sum(v)/3600:5.1f}h")
print({k:f"{v/3600:.1f}h/{totn[k]} turns" for k,v in tot.items()})
