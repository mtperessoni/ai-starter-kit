import json,glob,collections,re
E=[];seen=set()
for f in glob.glob('C:/Projects/agora-consulta-fe/.ai-kit/runs/*/events.jsonl'):
    for l in open(f,encoding='utf-8'):
        try:e=json.loads(l)
        except:continue
        k=(e.get('tuid'),e['ev'])
        if k in seen: continue
        seen.add(k);E.append(e)
post=[e for e in E if e['ev'] in('PostToolUse','PostToolUseFailure') and e.get('ms')]
def repo(c):
    for r in ['ai-starter-kit','clara-ai','modulo-integrador','agora-consulta-fe','.ai-starter-kit']:
        if r in c: return r
    return '?'
def norm(c):
    c=re.sub(r'^cd [^&;]+(&&|;)\s*','',c)
    m=re.search(r'(gates\.sh \w+[- ]?\w*|pytest|unittest( discover)?|vitest|jest|tsc|eslint|yarn \w+|npx \w+|python -m \w+|gate\.py|retro|ruff|mypy)',c)
    return m.group(1) if m else c[:40]
for cls in ['test.single','test.full','test.related','shell','wait.test','powershell']:
    agg=collections.defaultdict(lambda:[0,0,0])
    for e in post:
        if e.get('cls')!=cls: continue
        k=(repo(e.get('cmd','')+e.get('repo','')),norm(e.get('cmd','')))
        a=agg[k];a[0]+=e['ms']/60000;a[1]+=1;a[2]=max(a[2],e['ms']/1000)
    print(f"\n### {cls}")
    for k,v in sorted(agg.items(),key=lambda x:-x[1][0])[:12]:
        print(f"  {v[0]:7.1f}min n={v[1]:4} avg={v[0]*60/v[1]:6.1f}s max={v[2]:6.0f}s  {k[0]:18} {k[1]}")
