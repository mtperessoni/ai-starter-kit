import json,os,glob,re,collections
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
def bucket(d):
    d=d.lower()
    for k,pat in [('review/recheck','review|re-?check|verif|audit|adversar|confirm'),('fix','fix|correct|address|repair|resolve'),('implement/task','implement|task|t\d|executor|wave|card|build|write test'),('docs/prd/trd','prd|trd|docs|changelog|plan|decision|promot'),('survey/research','survey|map|research|explore|investig|find|analy|sweep'),('close/gates','close|gate|suite|baseline|retro')]:
        if re.search(pat,d): return k
    return 'other'
for sid in ['ecde3293','d012bb2c','b89cdea1','33d0c972','9b22d6ed','9ab322ae']:
    f=glob.glob(f"{root}/{sid}*.jsonl")[0]; c=collections.Counter(); sm=0; ty=collections.Counter()
    for l in open(f,encoding='utf-8',errors='ignore'):
        if '"tool_use"' not in l: continue
        e=json.loads(l)
        for b in (e.get('message') or {}).get('content') or []:
            if isinstance(b,dict) and b.get('type')=='tool_use':
                if b['name'] in('Agent','Task'):
                    i=b.get('input') or {}; c[bucket(i.get('description','')+' '+i.get('prompt','')[:200])]+=1; ty[i.get('subagent_type','general-purpose')]+=1
                if b['name']=='SendMessage': sm+=1
    print(f"{sid}: dispatches={sum(c.values())} resumes(SendMessage)={sm} | {dict(c.most_common())} | types={dict(ty.most_common(5))}")
