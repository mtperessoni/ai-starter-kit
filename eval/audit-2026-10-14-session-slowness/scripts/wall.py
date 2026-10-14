import json,os,glob,collections,re,datetime as dt
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
P=lambda t: dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
TEST=re.compile(r'pytest|unittest|vitest|jest|gates\.sh (one|related|verify|baseline|compare|close|full)|gate\.py|run_tests|test_')
WAIT=re.compile(r'sleep|until |while |seq 1|Monitor|tail -f|wait ')
def cls_tool(name,inp):
    if name=='AskUserQuestion': return 'human_question'
    if name in('Agent','Task'): return 'agent_fg'
    if name in('Bash','PowerShell'):
        c=inp.get('command','')
        if TEST.search(c): return 'bash_test'
        if WAIT.search(c): return 'bash_wait'
        return 'bash_other'
    if name in('Edit','Write','MultiEdit','NotebookEdit'): return 'edit'
    return 'other_tool'
def wall(f):
    ents=[json.loads(l) for l in open(f,encoding='utf-8',errors='ignore') if l.startswith('{')]
    ents=[e for e in ents if e.get('timestamp')]
    acc=collections.Counter(); pend={}; last_kind=None
    msgs=set(); outtok=0
    for i,e in enumerate(ents):
        t=P(e['timestamp'])
        if i>0:
            gap=t-P(ents[i-1]['timestamp'])
            if pend:
                kinds=set(pend.values())
                k=next((x for x in ['human_question','agent_fg','bash_test','bash_wait','bash_other','edit','other_tool'] if x in kinds))
                acc[k]+=gap
            else:
                c=(e.get('message') or {}).get('content')
                if e.get('type')=='assistant': acc['model']+=gap if gap<1800 else 0; acc['stall']+=gap if gap>=1800 else 0
                elif e.get('type')=='user' and isinstance(c,str):
                    if c.startswith('<task-notification') or 'agent-message' in c[:300]: acc['wait_bg_agent']+=gap
                    else: acc['human_turn']+=gap
                else: acc['misc']+=gap
        m=e.get('message') or {}; c=m.get('content')
        if e.get('type')=='assistant':
            if m.get('id') not in msgs:
                msgs.add(m.get('id'))
            u=m.get('usage') or {}
        if isinstance(c,list):
            for b in c:
                if not isinstance(b,dict): continue
                if b.get('type')=='tool_use': pend[b['id']]=cls_tool(b['name'],b.get('input') or {})
                if b.get('type')=='tool_result': pend.pop(b.get('tool_use_id'),None)
    return acc
tot_main=collections.Counter(); tot_sub=collections.Counter()
rows=[]
for f in sorted(glob.glob(root+'/*.jsonl')):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    a=wall(f); span=sum(a.values())
    if span<2*3600: continue
    sa=collections.Counter()
    for s in glob.glob(f[:-6]+'/subagents/*.jsonl'): sa.update(wall(s))
    tot_main.update(a); tot_sub.update(sa)
    h=lambda x:f"{x/3600:4.1f}"
    print(f"{os.path.basename(f)[:8]} span={h(span)}h | human={h(a['human_question']+a['human_turn'])} bgwait={h(a['wait_bg_agent'])} agentFG={h(a['agent_fg'])} model={h(a['model'])} test={h(a['bash_test'])} poll={h(a['bash_wait'])} bash={h(a['bash_other'])} edit={h(a['edit'])} stall={h(a['stall'])} || SUBS model={h(sa['model'])} test={h(sa['bash_test'])} poll={h(sa['bash_wait'])} bash={h(sa['bash_other'])} edit={h(sa['edit'])}")
print('\nMAIN totals h:',{k:round(v/3600,1) for k,v in tot_main.most_common()})
print('SUB  totals h:',{k:round(v/3600,1) for k,v in tot_sub.most_common()})
