import json, os, glob, re, sys, collections, datetime as dt

ROOT = os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
SINCE = dt.datetime(2026, 10, 13, 12, tzinfo=dt.timezone.utc).timestamp()
SKIP = {'9b25fd41'}


def P(t):
    return dt.datetime.fromisoformat(t.replace('Z', '+00:00')).timestamp()


def entries(f):
    for line in open(f, encoding='utf-8', errors='ignore'):
        if line.startswith('{'):
            try:
                yield json.loads(line)
            except Exception:
                pass


def first_ctx_and_tokens(f):
    seen, first, tot, turns = set(), None, 0, 0
    for e in entries(f):
        if e.get('type') != 'assistant':
            continue
        m = e.get('message') or {}
        if m.get('id') in seen:
            continue
        seen.add(m.get('id'))
        u = m.get('usage') or {}
        ctx = (u.get('input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0)
        if ctx and first is None:
            first = ctx
        tot += ctx + (u.get('output_tokens') or 0)
        turns += 1
    return first, tot, turns


def describe(f):
    for e in entries(f):
        if e.get('type') != 'user':
            continue
        c = (e.get('message') or {}).get('content')
        texts = [c] if isinstance(c, str) else [b.get('text', '') for b in (c or []) if isinstance(b, dict) and b.get('type') == 'text']
        for t in texts:
            t2 = re.sub(r'<[^>]+>.*?</[^>]+>', '', t, flags=re.S).strip()
            if t2 and not t2.startswith('Another Claude session') and not t2.startswith('Caveat'):
                return t2[:110].replace('\n', ' ')
    return '?'


ERR = collections.Counter()
ERR_EX = {}
first_main, first_sub = [], []
tok_main = tok_sub = 0
per_file_edits = collections.Counter()
sessions = []
for f in sorted(glob.glob(ROOT + '/*.jsonl')):
    sid = os.path.basename(f)[:8]
    if sid in SKIP:
        continue
    ts = [P(e['timestamp']) for e in entries(f) if e.get('timestamp')]
    if not ts or max(ts) < SINCE:
        continue
    fc, tot, turns = first_ctx_and_tokens(f)
    if fc:
        first_main.append(fc)
    tok_main += tot
    subtot = 0
    files = [f] + glob.glob(f[:-6] + '/subagents/*.jsonl')
    for sf in files[1:]:
        fc2, t2, _ = first_ctx_and_tokens(sf)
        if fc2:
            first_sub.append(fc2)
        subtot += t2
    tok_sub += subtot
    sessions.append((sid, tot / 1e6, subtot / 1e6, describe(f)))
    for sf in files:
        pend = {}
        for e in entries(sf):
            c = (e.get('message') or {}).get('content')
            if not isinstance(c, list):
                continue
            for b in c:
                if not isinstance(b, dict):
                    continue
                if b.get('type') == 'tool_use':
                    pend[b['id']] = b.get('name')
                    if b.get('name') in ('Edit', 'Write', 'MultiEdit'):
                        fp = ((b.get('input') or {}).get('file_path') or '').replace('\\', '/')
                        if re.search(r'/(src|api|features|infra|app)/', fp) and not re.search(r'__tests__|/tests?/|\.test\.', fp):
                            per_file_edits[(sid, fp)] += 1
                if b.get('type') == 'tool_result' and b.get('is_error'):
                    name = pend.get(b.get('tool_use_id'), '?')
                    rc = b.get('content')
                    txt = rc if isinstance(rc, str) else json.dumps(rc)
                    txt = txt[:300]
                    if re.search(r'not been read|Read it first|read the file', txt, re.I): k = 'read-before-edit'
                    elif re.search(r'String to replace not found|not found in file|old_string', txt, re.I): k = 'edit-string-mismatch'
                    elif re.search(r'modified since|has been modified', txt, re.I): k = 'file-changed-since-read'
                    elif re.search(r'exceeds maximum allowed tokens|too large', txt, re.I): k = 'read-too-large'
                    elif re.search(r'hook|blocked|denied|permission|not allowed', txt, re.I): k = 'hook/permission'
                    elif re.search(r'Exit code', txt): k = name + ':exit-code'
                    elif re.search(r'does not exist|No such file|ENOENT|not found', txt, re.I): k = 'path-not-found'
                    elif re.search(r'timed out|timeout', txt, re.I): k = 'timeout'
                    elif re.search(r'interrupt|rejected|doesn.t want', txt, re.I): k = 'user-interrupt/reject'
                    else: k = name + ':other'
                    ERR[k] += 1
                    ERR_EX.setdefault(k, txt[:160].replace('\n', ' '))

med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
print(f"first-turn ctx main: median={med(first_main)//1000}k min={min(first_main)//1000}k max={max(first_main)//1000}k n={len(first_main)}")
print(f"first-turn ctx sub:  median={med(first_sub)//1000}k min={min(first_sub)//1000}k max={max(first_sub)//1000}k n={len(first_sub)}")
print(f"tokens processed (ctx+out summed per turn): main={tok_main/1e6:.0f}M subs={tok_sub/1e6:.0f}M main share={tok_main/(tok_main+tok_sub):.0%}")
print("\nerrors:")
for k, v in ERR.most_common(15):
    print(f"  {v:5} {k} | {ERR_EX[k]}")
dist = collections.Counter()
for (sid, fp), n in per_file_edits.items():
    dist['1' if n == 1 else '2-3' if n <= 3 else '4-9' if n <= 9 else '10+'] += 1
print("\nproduct files by edit count:", dict(dist), "files=", len(per_file_edits), "edits=", sum(per_file_edits.values()))
print("top re-edited:", [(s, os.path.basename(p), n) for (s, p), n in per_file_edits.most_common(8)])
print("\nsessions (main M tokens, subs M tokens, ask):")
for s in sessions:
    print(f"  {s[0]} main={s[1]:7.1f}M subs={s[2]:7.1f}M | {s[3]}")
