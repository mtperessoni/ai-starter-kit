import json,os,glob,re,collections,datetime as dt
ROOT=os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
SINCE=dt.datetime(2026,10,13,12,tzinfo=dt.timezone.utc).timestamp()
c=collections.Counter(); retry=collections.Counter()
for f in glob.glob(ROOT+'/*.jsonl'):
    if '9b25fd41' in f: continue
    for sf in glob.glob(f[:-6]+'/subagents/*.jsonl'):
        pend={}; seen_bash=collections.Counter(); seen_read=set(); late=False; after_err=None
        for l in open(sf,encoding='utf-8',errors='ignore'):
            if not l.startswith('{'): continue
            e=json.loads(l); t=e.get('timestamp')
            if t and dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()>=SINCE: late=True
            for b in (e.get('message') or {}).get('content') or []:
                if not isinstance(b,dict): continue
                if b.get('type')=='tool_use':
                    n,i=b['name'],b.get('input') or {}
                    pend[b['id']]=(n,i)
                    if n in('Bash','PowerShell'):
                        cmd=i.get('command','')
                        for m in re.finditer(r'([\w./\:-]+\.(?:py|ts|tsx|md|json))',cmd): seen_bash[os.path.basename(m.group(1))]+=1
                    if n=='Read': seen_read.add(os.path.basename(i.get('file_path','')))
                    if after_err is not None:
                        retry[n]+=1; after_err=None
                if b.get('type')=='tool_result' and b.get('is_error') and late:
                    rc=b.get('content'); txt=rc if isinstance(rc,str) else json.dumps(rc)
                    if 'has not been read yet' in txt:
                        n,i=pend.get(b.get('tool_use_id'),('?',{}))
                        bn=os.path.basename(i.get('file_path',''))
                        c['bash-touched-before' if seen_bash[bn] else 'never-touched']+=1
                        after_err=True
print(c, 'next call after error:',retry.most_common(5))
