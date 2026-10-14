import json,os,glob,collections,datetime as dt,statistics as st
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
P=lambda t: dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
solo=[];batch=[];early=[]
for f in glob.glob(root+'/*/subagents/*.jsonl')+glob.glob(root+'/*.jsonl'):
    mt=os.path.getmtime(f)
    if mt<dt.datetime(2026,9,1).timestamp(): continue
    pend={}; msgcount=collections.Counter(); idmsg={}
    lines=[json.loads(l) for l in open(f,encoding='utf-8',errors='ignore') if l.strip().startswith('{')]
    for e in lines:
        if e.get('type')=='assistant':
            m=e.get('message') or {}
            for b in m.get('content') or []:
                if isinstance(b,dict) and b.get('type')=='tool_use': msgcount[m.get('id')]+=1; idmsg[b['id']]=m.get('id')
    for e in lines:
        c=(e.get('message') or {}).get('content')
        if not isinstance(c,list) or not e.get('timestamp'): continue
        for b in c:
            if not isinstance(b,dict):continue
            if b.get('type')=='tool_use' and b['name']=='Edit': pend[b['id']]=P(e['timestamp'])
            if b.get('type')=='tool_result' and b.get('tool_use_id') in pend:
                t0=pend.pop(b['tool_use_id']); d=P(e['timestamp'])-t0
                (solo if msgcount[idmsg.get(b['tool_use_id'])]==1 else batch).append(d)
                if t0<dt.datetime(2026,9,20).timestamp(): early.append(d)
for n,v in [('solo',solo),('batch',batch),('before 09-20',early)]:
    if v: print(f"{n:12} n={len(v):5} p50={st.median(v):.1f}s mean={st.mean(v):.1f}s total={sum(v)/3600:.1f}h")
