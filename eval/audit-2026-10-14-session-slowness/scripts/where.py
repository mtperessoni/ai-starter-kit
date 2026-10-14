import json,os,glob,collections,re,datetime as dt
root=os.path.expanduser('~/.claude/projects')
def cat(p):
    p=p.replace(chr(92),'/').lower()
    if 'ai-starter-kit' in p or '.ai-starter-kit' in p: return 'kit (process tooling)'
    if '/tmp/' in p or 'scratchpad' in p or '/temp/' in p: return 'scratch'
    if re.search(r'/\.claude/|/scripts/gates|gate\.py|/state/|prd-flow|/\.specify/|claude\.md|agents\.md|memory/',p): return 'process (.claude, state, gates)'
    if re.search(r'/docs/(prd|trd|adr)|/changes/|/specs/|changelog|/docs/',p): return 'docs (prd/trd/changes)'
    if re.search(r'/__tests__/|/tests?/|test_|\.test\.|\.spec\.|/eval',p): return 'tests/evals'
    if re.search(r'/src/|\.py$|\.tsx?$|\.java$',p): return 'product code'
    return 'other'
c=collections.Counter(); byday=collections.defaultdict(collections.Counter)
for f in glob.glob(root+'/*/*.jsonl')+glob.glob(root+'/*/*/subagents/*.jsonl'):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    for l in open(f,encoding='utf-8',errors='ignore'):
        if '"tool_use"' not in l: continue
        e=json.loads(l)
        for b in (e.get('message') or {}).get('content') or []:
            if isinstance(b,dict) and b.get('type')=='tool_use' and b['name'] in('Edit','Write','MultiEdit'):
                k=cat((b.get('input') or {}).get('file_path','')); c[k]+=1
                byday[e['timestamp'][5:10]][k]+=1
T=sum(c.values())
for k,v in c.most_common(): print(f"  {k:32} {v:6} {100*v/T:5.1f}%")
