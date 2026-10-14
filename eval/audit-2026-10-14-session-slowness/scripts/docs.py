import json,os,glob,re,collections,datetime as dt,statistics as st
root=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
P=lambda t: dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()
def role(prompt,atype):
    if atype: 
        if 'docs' in atype: return 'docs'
        if 'executor' in atype: return 'impl'
        if 'review' in atype or 'recheck' in atype: return 'review'
        if 'surveyor' in atype: return 'survey'
    p=prompt[:600].lower()
    if re.search(r'review|re-?check|audit|verify',p): return 'review'
    if re.search(r'prd|trd|changelog|decisions\.md|plan\.md|docs/',p) and not re.search(r'implement|test first|failing test',p): return 'docs'
    if re.search(r'implement|test first|failing test|task card|t\d\d',p): return 'impl'
    return 'other'
R=collections.defaultdict(list)
DOCP=re.compile(r'docs/(prd|trd|adr)|changelog|/changes/|decisions\.md|plan\.md|state\.md|claude\.md|index\.md',re.I)
for f in glob.glob(root+'/*/subagents/agent-*.jsonl'):
    if os.path.getmtime(f)<dt.datetime(2026,10,1).timestamp(): continue
    meta=f[:-6]+'.meta.json'; atype=''
    if os.path.exists(meta):
        try: atype=json.load(open(meta)).get('agentType','')
        except: pass
    ents=[json.loads(l) for l in open(f,encoding='utf-8',errors='ignore') if l.startswith('{')]
    ents=[e for e in ents if e.get('timestamp')]
    if len(ents)<3: continue
    first=next((e for e in ents if e.get('type')=='user'),None)
    c=(first.get('message') or {}).get('content') if first else ''
    prompt=c if isinstance(c,str) else ' '.join(b.get('text','') for b in c if isinstance(b,dict))
    r=role(prompt,atype)
    reads=collections.Counter(); edits=0; docedits=0; gate=0; gatefail=0; turns=set(); outt=0; pend={}
    for e in ents:
        m=e.get('message') or {}
        if e.get('type')=='assistant' and m.get('id') not in turns:
            turns.add(m.get('id')); outt+=(m.get('usage') or {}).get('output_tokens',0)
        for b in m.get('content') or [] if isinstance(m.get('content'),list) else []:
            if not isinstance(b,dict): continue
            if b.get('type')=='tool_use':
                i=b.get('input') or {}
                if b['name']=='Read': reads[i.get('file_path','')]+=1
                if b['name'] in('Edit','Write'): edits+=1; docedits+=bool(DOCP.search(i.get('file_path','')))
                if b['name']=='Bash' and re.search(r'gate\.py|gates\.sh docs',i.get('command','')): pend[b['id']]=1; gate+=1
            if b.get('type')=='tool_result' and b.get('tool_use_id') in pend:
                pend.pop(b['tool_use_id']); t=json.dumps(b.get('content'))
                if re.search(r'FAIL|ERROR|G\d+ ',t): gatefail+=1
    wall=P(ents[-1]['timestamp'])-P(ents[0]['timestamp'])
    R[r].append(dict(wall=wall,turns=len(turns),edits=edits,docedits=docedits,gate=gate,gatefail=gatefail,rereads=sum(v-1 for v in reads.values() if v>1),out=outt,files=len(reads)))
for r,v in R.items():
    g=lambda k: st.median([x[k] for x in v]); s=lambda k: sum(x[k] for x in v)
    print(f"{r:7} n={len(v):4} wall p50={g('wall')/60:5.1f}min total={s('wall')/3600:5.1f}h | turns p50={g('turns'):4.0f} | edits p50={g('edits'):3.0f} (doc edits total {s('docedits')}) | gate runs={s('gate')} failing={s('gatefail')} | same-file rereads total={s('rereads')} | out tok p50={g('out')/1e3:.1f}k")
print("## active hours (gaps capped at 15 min)")
