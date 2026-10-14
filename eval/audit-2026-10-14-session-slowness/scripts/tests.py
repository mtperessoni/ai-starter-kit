import json,os,glob,collections,re,datetime as dt,statistics as st
root=os.path.expanduser('~/.claude/projects')
P=lambda t: dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
TEST=re.compile(r'pytest|unittest|vitest|jest|gates\.sh (one|related|verify|baseline|compare|close|full)|gate\.py')
def repo(c):
    for r in ['ai-starter-kit','clara-ai','modulo-integrador','agora-consulta-fe']:
        if r in c: return r
    return 'cwd?'
def kind(c):
    if re.search(r'unittest discover|pytest\s*(-q|-x|--)?\s*(tests/?)?\s*($|[>|&;])|gates\.sh (compare|close|baseline)|run_tests',c): return 'FULL'
    if re.search(r'gates\.sh (verify|related)',c): return 'related/verify'
    if re.search(r'gate\.py',c): return 'gate.py'
    return 'targeted'
by=collections.defaultdict(list); per_agent=[]; fails=collections.Counter(); tot=collections.Counter()
for f in glob.glob(root+'/*/*.jsonl')+glob.glob(root+'/*/*/subagents/*.jsonl'):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    pend={}; n=0; secs=0; cwd=''
    for l in open(f,encoding='utf-8',errors='ignore'):
        if not l.startswith('{'): continue
        e=json.loads(l); cwd=e.get('cwd',cwd)
        c=(e.get('message') or {}).get('content')
        if not isinstance(c,list) or not e.get('timestamp'): continue
        for b in c:
            if not isinstance(b,dict): continue
            if b.get('type')=='tool_use' and b['name'] in('Bash','PowerShell'):
                cmd=(b.get('input') or {}).get('command','')
                if TEST.search(cmd) and not cmd.lstrip().startswith(('grep','cat','sed','ls','rtk grep')): pend[b['id']]=(P(e['timestamp']),cmd)
            if b.get('type')=='tool_result' and b.get('tool_use_id') in pend:
                t0,cmd=pend.pop(b['tool_use_id']); d=P(e['timestamp'])-t0
                r=repo(cmd) if repo(cmd)!='cwd?' else repo(cwd)
                k=kind(cmd); by[(r,k)].append(d); n+=1; secs+=d
                txt=json.dumps(b.get('content'))[-3000:]
                failed=bool(re.search(r'FAILED|failed|Error|\bFAIL\b|exit code [1-9]|Exit code [1-9]',txt))
                fails[(r,failed)]+=1
    if n: per_agent.append((n,secs,os.path.basename(f)[:20],'sub' if 'subagents' in f else 'main'))
print("## test runs by repo/kind (all sessions since 10-01)")
for k,v in sorted(by.items(),key=lambda x:-sum(x[1])):
    print(f"  {k[0]:18} {k[1]:15} n={len(v):5} total={sum(v)/3600:5.1f}h p50={st.median(v):6.1f}s p90={sorted(v)[int(.9*(len(v)-1))]:6.1f}s max={max(v):5.0f}s")
print("\n## failing-output share:",{k:v for k,v in fails.items()})
per_agent.sort(reverse=True)
print("\n## agents with most test runs")
for a in per_agent[:12]: print(f"  runs={a[0]:3} time={a[1]/60:5.0f}min {a[3]} {a[2]}")
ns=[a[0] for a in per_agent if a[3]=='sub']
print("subagents running tests:",len(ns),"median runs",st.median(ns),"p90",sorted(ns)[int(.9*(len(ns)-1))])
