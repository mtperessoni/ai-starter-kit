import json,os,glob,collections,re,datetime as dt,statistics as st
root=os.path.expanduser('~/.claude/projects')
TEST=re.compile(r'pytest|unittest|vitest|jest|gates\.sh (one|related|verify|close|compare)')
FAIL=re.compile(r'\bFAILED\b|\d+ failed|FAIL\b|AssertionError|Error:|errors? during collection|Exit code [1-9]|exit code [1-9]|Traceback')
PASS=re.compile(r'\bOK\b|\d+ passed|Tests? +\d+ passed|passed in')
def is_test_file(p):
    p=p.replace(chr(92),'/'); return bool(re.search(r'/__tests__/|/tests?/|test_[^/]*\.py$|\.test\.|\.spec\.',p))
after_fail=collections.Counter(); streaks=[]; agents_loop=0; agents=0; rerun_same_fail=0
for f in glob.glob(root+'/*/*/subagents/*.jsonl')+glob.glob(root+'/*/*.jsonl'):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    seq=[]  # ('test',cmd,failed) or ('edit',is_test)
    pend={}
    for l in open(f,encoding='utf-8',errors='ignore'):
        if not l.startswith('{'): continue
        e=json.loads(l); c=(e.get('message') or {}).get('content')
        if not isinstance(c,list): continue
        for b in c:
            if not isinstance(b,dict): continue
            if b.get('type')=='tool_use':
                i=b.get('input') or {}
                if b['name'] in('Bash','PowerShell') and TEST.search(i.get('command','')) and not re.match(r'\s*(rtk )?(grep|cat|sed|ls|git )',i.get('command','')):
                    pend[b['id']]=i['command']
                elif b['name'] in('Edit','Write','MultiEdit'):
                    seq.append(('edit',is_test_file(i.get('file_path',''))))
            if b.get('type')=='tool_result' and b.get('tool_use_id') in pend:
                cmd=pend.pop(b['tool_use_id']); txt=json.dumps(b.get('content'))[-4000:]
                failed=bool(FAIL.search(txt)) and not (PASS.search(txt) and not re.search(r'\d+ failed|FAILED',txt))
                seq.append(('test',cmd,failed))
    tests=[x for x in seq if x[0]=='test']
    if not tests: continue
    agents+=1
    # streak of consecutive failing test runs
    s=0;mx=0
    for x in tests:
        s=s+1 if x[2] else 0; mx=max(mx,s)
    streaks.append(mx)
    if mx>=3: agents_loop+=1
    # what was edited between a failing run and the next run
    for i,x in enumerate(seq):
        if x[0]=='test' and x[2]:
            j=i+1; t=c_=0
            while j<len(seq) and seq[j][0]=='edit':
                t+=seq[j][1]; c_+=not seq[j][1]; j+=1
            if j<len(seq) and seq[j][0]=='test':
                if seq[j][1]==x[1] and t==0 and c_==0: rerun_same_fail+=1
                k='only TEST files edited' if t and not c_ else 'only CODE edited' if c_ and not t else 'BOTH edited' if t and c_ else 'nothing edited (rerun/other cmd)'
                after_fail[k]+=1
T=sum(after_fail.values())
print("agents that ran tests:",agents)
print("after a FAILING run, before the next run:")
for k,v in after_fail.most_common(): print(f"   {k:34} {v:5} {100*v/T:4.1f}%")
print("identical command rerun with no edit in between:",rerun_same_fail)
print("agents with >=3 consecutive failing runs:",agents_loop, f"({100*agents_loop/agents:.0f}%)", " max streak:",max(streaks), " p90 streak:",sorted(streaks)[int(.9*(len(streaks)-1))])
