import json,glob,collections,os
evs=[]
for f in glob.glob('C:/Projects/agora-consulta-fe/.ai-kit/runs/*/events.jsonl'):
    for l in open(f,encoding='utf-8'):
        try:e=json.loads(l)
        except:continue
        evs.append(e)
# dedupe by tuid+ev
seen=set();E=[]
for e in evs:
    k=(e.get('tuid'),e['ev'],e['sid'],e.get('ts'))
    if k in seen: continue
    seen.add(k);E.append(e)
post=[e for e in E if e['ev'] in('PostToolUse','PostToolUseFailure') and e.get('ms')]
by=collections.defaultdict(lambda:collections.Counter())
cnt=collections.defaultdict(lambda:collections.Counter())
for e in post:
    who='main' if e['agent'] in ('main',None,'') else 'sub'
    by[e['sid']][(who,e.get('cls'))]+=e['ms']/60000
    cnt[e['sid']][(who,e.get('cls'))]+=1
tot={s:sum(c.values()) for s,c in by.items()}
for s in sorted(tot,key=lambda s:-tot[s])[:14]:
    c=by[s]
    print(f"\n### {s} total tool-min={tot[s]:.0f}")
    for (k,v) in c.most_common(9):
        print(f"   {k[0]:4} {str(k[1]):18} {v:7.1f} min  n={cnt[s][k]}")
# global
g=collections.Counter();gn=collections.Counter()
for s in by:
    for k,v in by[s].items(): g[k[1]]+=v; gn[k[1]]+=cnt[s][k]
print("\n### GLOBAL tool minutes by class")
for k,v in g.most_common(): print(f"  {str(k):20} {v:8.1f} min n={gn[k]}  avg={v*60/max(gn[k],1):.1f}s")
