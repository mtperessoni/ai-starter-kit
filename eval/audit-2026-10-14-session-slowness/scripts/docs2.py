import json,os,glob,re,collections,datetime as dt
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
rd=collections.Counter(); rdkb=collections.Counter(); gcodes=collections.Counter(); bash=collections.Counter()
for f in glob.glob(root+'/*/subagents/agent-*.jsonl'):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    pend={}
    for l in open(f,encoding='utf-8',errors='ignore'):
        if not l.startswith('{'): continue
        e=json.loads(l); m=e.get('message') or {}
        if not isinstance(m.get('content'),list): continue
        for b in m['content']:
            if not isinstance(b,dict): continue
            if b.get('type')=='tool_use':
                i=b.get('input') or {}
                if b['name']=='Read':
                    p=i.get('file_path','').replace(chr(92),'/'); p=re.sub(r'.*/Projects/','',p); pend[b['id']]=('r',p)
                if b['name']=='Bash' and re.search(r'gate\.py|gates\.sh docs',i.get('command','')): pend[b['id']]=('g',None)
            if b.get('type')=='tool_result' and b.get('tool_use_id') in pend:
                k,p=pend.pop(b['tool_use_id']); t=json.dumps(b.get('content'))
                if k=='r': rd[p]+=1; rdkb[p]+=len(t)/1024
                else:
                    for g in set(re.findall(r'\b(G\d{1,2})\b',t)): gcodes[g]+=1
print("## most read bytes by subagents (KB, reads)")
for p,v in rdkb.most_common(15): print(f"  {v:8.0f}KB {rd[p]:4}x {p}")
print("## gate codes seen in gate outputs:",gcodes.most_common(15))
