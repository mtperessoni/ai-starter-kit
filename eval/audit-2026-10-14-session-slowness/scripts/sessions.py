import json,os,glob,sys,datetime as dt
root=os.path.expanduser('~/.claude/projects')
rows=[]
for proj in ['c--Projects-agora-consulta-fe','c--Projects-modulo-integrador','c--Users-Peressoni--claude-agora']:
    for f in glob.glob(os.path.join(root,proj,'*.jsonl')):
        if os.path.getmtime(f) < dt.datetime(2026,10,1).timestamp(): continue
        ts=[];users=0;asst=0;first=None
        for l in open(f,encoding='utf-8',errors='ignore'):
            try:e=json.loads(l)
            except:continue
            t=e.get('timestamp')
            if t: ts.append(dt.datetime.fromisoformat(t.replace('Z','+00:00')))
            if e.get('type')=='user' and isinstance(e.get('message',{}).get('content'),str):
                users+=1
                if first is None: first=e['message']['content'][:90].replace('\n',' ')
            if e.get('type')=='assistant': asst+=1
        if not ts: continue
        ts.sort()
        # active time: sum gaps < 15min
        act=sum(min((b-a).total_seconds(),900) for a,b in zip(ts,ts[1:]))
        idle=sum((b-a).total_seconds() for a,b in zip(ts,ts[1:]) if (b-a).total_seconds()>900)
        subs=len(glob.glob(os.path.join(f[:-6],'subagents','*.jsonl')))
        rows.append((ts[0],proj[:20],os.path.basename(f)[:8],(ts[-1]-ts[0]).total_seconds()/3600,act/3600,idle/3600,users,asst,subs,os.path.getsize(f)//1024,first))
rows.sort()
for r in rows:
    print(f"{r[0]:%m-%d %H:%M} {r[1]:20} {r[2]} wall={r[3]:5.1f}h active={r[4]:4.1f}h idle={r[5]:4.1f}h usr={r[6]:3} asst={r[7]:4} subs={r[8]:3} {r[9]:6}KB | {r[10]}")
