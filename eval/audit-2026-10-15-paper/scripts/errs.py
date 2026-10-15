import json,os,glob,re,collections,datetime as dt
ROOT=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
SINCE=dt.datetime(2026,10,13,12,tzinfo=dt.timezone.utc).timestamp()
by=collections.Counter(); denied_cmd=collections.Counter(); rbw_next=collections.Counter(); ex=[]
for f in glob.glob(ROOT+'/*.jsonl'):
    sid=os.path.basename(f)[:8]
    if sid=='9b25fd41': continue
    for sf in [f]+glob.glob(f[:-6]+'/subagents/*.jsonl'):
        who='main' if sf==f else 'sub'
        pend={}; late=False
        for l in open(sf,encoding='utf-8',errors='ignore'):
            if not l.startswith('{'): continue
            e=json.loads(l)
            t=e.get('timestamp')
            if t and dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()>=SINCE: late=True
            if not late: continue
            for b in (e.get('message') or {}).get('content') or []:
                if not isinstance(b,dict): continue
                if b.get('type')=='tool_use': pend[b['id']]=(b['name'],b.get('input') or {})
                if b.get('type')=='tool_result' and b.get('is_error'):
                    rc=b.get('content'); txt=rc if isinstance(rc,str) else json.dumps(rc)
                    n,i=pend.get(b.get('tool_use_id'),('?',{}))
                    if 'auto mode classifier' in txt:
                        r=re.search(r'Reason: \[([^\]]+)\]',txt); by[(sid,who,'denied:'+(r.group(1) if r else '?'))]+=1
                        c=(i.get('command') or i.get('file_path') or '')[:70].replace('\n',' ')
                        denied_cmd[(n, re.sub(r'\s.*','',c) if n in('Bash','PowerShell') else os.path.splitext(c)[1])]+=1
                        if len(ex)<12: ex.append((sid,who,n,c,txt[txt.find('Reason'):txt.find('Reason')+120]))
                    elif 'has not been read yet' in txt:
                        by[(sid,who,'read-before-edit')]+=1
                        rbw_next[(n, os.path.splitext(i.get('file_path',''))[1])]+=1
agg=collections.Counter()
for (s,w,k),v in by.items(): agg[(w,k)]+=v
print('by who/kind:',agg.most_common())
print('top sessions:',sorted(((v,s,w,k) for (s,w,k),v in by.items()),reverse=True)[:12])
print('denied tool/cmd:',denied_cmd.most_common(15))
print('read-before-edit tool/ext:',rbw_next.most_common(8))
for x in ex: print(x)
