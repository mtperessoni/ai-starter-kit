import json, os, glob, re, sys, collections, datetime as dt

ROOT = os.path.expanduser('~/.claude/projects/c--Projects-agora-consulta-fe')
SINCE = dt.datetime(2026, 10, 13, 12, tzinfo=dt.timezone.utc).timestamp()
SKIP = {'9b25fd41'}
OUT = sys.argv[1]

TEST = re.compile(r'pytest|vitest|jest|gates\.sh (one|related|verify|baseline|compare|close|full|offline)|run_tests|npm test|yarn test')
GATE = re.compile(r'gate\.py|gates\.sh (docs|ratchet|lint|trailers|html|imports)|eslint|tsc --noEmit|ruff|mypy')
POLL = re.compile(r'\bsleep\b|until |while true|tail -f|Monitor')
BIGDOC = re.compile(r'docs/(prd|trd)/|changes/|design\.md|plan\.md|decisions\.md|state\.md|code-structure|invariants|testing\.md|constitution|CLAUDE\.md|AGENTS\.md|SKILL\.md|rules/')


def P(t):
    return dt.datetime.fromisoformat(t.replace('Z', '+00:00')).timestamp()


def kind_of_path(p):
    p = (p or '').replace('\\', '/')
    if '/Temp/' in p or '/scratchpad' in p or '/tmp/' in p:
        return 'scratch'
    if re.search(r'/(__tests__|tests?)/|\.test\.|\.spec\.|test_[^/]*\.py$', p):
        return 'tests'
    if re.search(r'/docs/(prd|trd|adr)/|/changes/|/CLAUDE\.md$|/AGENTS\.md$|/docs/flow\.md|/memory/', p):
        return 'docs'
    if re.search(r'/\.claude/|/scripts/|ai-kit|/\.specify/|ai-starter-kit/', p):
        return 'process'
    if re.search(r'/src/|/app/|/api/|/features/|/infra/', p):
        return 'product'
    return 'other'


def phase(name, inp):
    if name in ('Read', 'Grep', 'Glob'):
        return 'localize'
    if name in ('Edit', 'Write', 'MultiEdit', 'NotebookEdit'):
        k = kind_of_path(inp.get('file_path'))
        return {'product': 'fix', 'tests': 'test_edit', 'docs': 'docs', 'process': 'process'}.get(k, 'other_edit')
    if name in ('Bash', 'PowerShell'):
        c = inp.get('command', '')
        if TEST.search(c):
            return 'verify'
        if GATE.search(c):
            return 'gate'
        if POLL.search(c):
            return 'poll'
        if re.search(r'\b(cat|head|tail|sed -n|grep|rg|find|ls|wc|git (log|show|diff|status|grep))\b', c):
            return 'localize'
        return 'bash_other'
    if name in ('Agent', 'Task', 'SendMessage'):
        return 'orchestrate'
    if name in ('TodoWrite', 'TaskCreate', 'TaskUpdate'):
        return 'plan'
    if name == 'AskUserQuestion':
        return 'ask'
    return 'other'


def scan(f):
    s = dict(ts=[], asks=0, ask_wait=0.0, turns=0, msgs=set(), ctx=[], out_tok=0, in_tok=0, cr=0, cw=0,
             models=collections.Counter(), tools=collections.Counter(), phases=collections.Counter(),
             edits=collections.Counter(), edit_files=collections.Counter(), reads=collections.Counter(),
             bigdoc_reads=0, errors=0, compacts=0, dispatch=[], todo=0, first_edit_idx=None, n_calls=0,
             streak_max=0, fail_streak_max=0, big_results=0, result_chars=0, tests=0, tests_fail=0,
             tests_after_last_fix=0, edits_after_first=0, first_prompt=None, bg=0)
    pend = {}
    last_sig, streak = None, 0
    fail_streak = 0
    calls_seq = []
    for line in open(f, encoding='utf-8', errors='ignore'):
        if not line.startswith('{'):
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        t = e.get('timestamp')
        if t:
            s['ts'].append(P(t))
        if e.get('type') == 'system' and 'compact' in (e.get('subtype') or ''):
            s['compacts'] += 1
        if e.get('isCompactSummary'):
            s['compacts'] += 1
        m = e.get('message') or {}
        c = m.get('content')
        if e.get('type') == 'user' and isinstance(c, str) and s['first_prompt'] is None and not c.startswith('<'):
            s['first_prompt'] = c[:120].replace('\n', ' ')
        if e.get('type') == 'assistant':
            mid = m.get('id')
            if mid and mid not in s['msgs']:
                s['msgs'].add(mid)
                u = m.get('usage') or {}
                ctx = (u.get('input_tokens') or 0) + (u.get('cache_read_input_tokens') or 0) + (u.get('cache_creation_input_tokens') or 0)
                if ctx:
                    s['ctx'].append(ctx)
                s['in_tok'] += u.get('input_tokens') or 0
                s['cr'] += u.get('cache_read_input_tokens') or 0
                s['cw'] += u.get('cache_creation_input_tokens') or 0
                s['out_tok'] += u.get('output_tokens') or 0
                s['models'][(m.get('model') or '?')] += 1
                s['turns'] += 1
        if not isinstance(c, list):
            continue
        for b in c:
            if not isinstance(b, dict):
                continue
            if b.get('type') == 'tool_use':
                name, inp = b.get('name'), b.get('input') or {}
                s['n_calls'] += 1
                s['tools'][name] += 1
                ph = phase(name, inp)
                s['phases'][ph] += 1
                calls_seq.append(ph)
                sig = name + json.dumps(inp, sort_keys=True)[:2000]
                streak = streak + 1 if sig == last_sig else 1
                last_sig = sig
                s['streak_max'] = max(s['streak_max'], streak)
                pend[b['id']] = (name, inp, ph, t)
                if name in ('Edit', 'Write', 'MultiEdit'):
                    k = kind_of_path(inp.get('file_path'))
                    s['edits'][k] += 1
                    s['edit_files'][inp.get('file_path')] += 1
                    if k == 'product' and s['first_edit_idx'] is None:
                        s['first_edit_idx'] = s['n_calls']
                if name == 'Read':
                    fp = (inp.get('file_path') or '').replace('\\', '/')
                    s['reads'][fp] += 1
                    if BIGDOC.search(fp):
                        s['bigdoc_reads'] += 1
                if name in ('TodoWrite', 'TaskCreate', 'TaskUpdate'):
                    s['todo'] += 1
                if name == 'AskUserQuestion':
                    s['asks'] += 1
                if name in ('Bash', 'PowerShell') and inp.get('run_in_background'):
                    s['bg'] += 1
                if name in ('Agent', 'Task'):
                    s['dispatch'].append((inp.get('subagent_type') or 'general-purpose', inp.get('model') or '-',
                                          (inp.get('description') or '')[:50], inp.get('run_in_background')))
            if b.get('type') == 'tool_result':
                p = pend.pop(b.get('tool_use_id'), None)
                rc = b.get('content')
                txt = rc if isinstance(rc, str) else json.dumps(rc)[:200000]
                s['result_chars'] += len(txt)
                if len(txt) > 20000:
                    s['big_results'] += 1
                err = bool(b.get('is_error'))
                if err:
                    s['errors'] += 1
                if p:
                    name, inp, ph, t0 = p
                    if name == 'AskUserQuestion' and t0 and t:
                        s['ask_wait'] += P(t) - P(t0)
                    if ph == 'verify':
                        s['tests'] += 1
                        failed = err or bool(re.search(r'\b(\d+ failed|FAIL\b|failures?=|Error:|exit code [1-9])', txt[:20000]))
                        if failed:
                            s['tests_fail'] += 1
                            fail_streak += 1
                        else:
                            fail_streak = 0
                        s['fail_streak_max'] = max(s['fail_streak_max'], fail_streak)
    # verification after the last product edit
    if 'fix' in calls_seq:
        last_fix = len(calls_seq) - 1 - calls_seq[::-1].index('fix')
        tail = calls_seq[last_fix + 1:]
        s['tests_after_last_fix'] = sum(1 for x in tail if x in ('verify', 'gate'))
        s['tail_after_last_fix'] = len(tail)
    else:
        s['tail_after_last_fix'] = 0
    s['repatch'] = sum(v - 1 for k, v in s['edit_files'].items() if kind_of_path(k) == 'product' and v > 1)
    s['reread'] = sum(v - 1 for v in s['reads'].values() if v > 1)
    return s


def active(ts):
    ts = sorted(ts)
    return sum(min(b - a, 900) for a, b in zip(ts, ts[1:]))


def merge(a, b):
    for k in ('phases', 'tools', 'edits', 'models'):
        a[k].update(b[k])
    for k in ('turns', 'out_tok', 'in_tok', 'cr', 'cw', 'errors', 'compacts', 'bigdoc_reads', 'reread', 'repatch',
              'big_results', 'tests', 'tests_fail', 'n_calls', 'todo', 'bg', 'tests_after_last_fix', 'tail_after_last_fix'):
        a[k] += b[k]
    a['ctx'] += b['ctx']
    a['streak_max'] = max(a['streak_max'], b['streak_max'])
    a['fail_streak_max'] = max(a['fail_streak_max'], b['fail_streak_max'])


rows = []
for f in sorted(glob.glob(ROOT + '/*.jsonl')):
    sid = os.path.basename(f)[:8]
    if sid in SKIP:
        continue
    s = scan(f)
    if not s['ts'] or max(s['ts']) < SINCE:
        continue
    subs = []
    for sf in glob.glob(f[:-6] + '/subagents/*.jsonl'):
        ss = scan(sf)
        if ss['ts']:
            ss['file'] = os.path.basename(sf)
            subs.append(ss)
    rows.append((sid, s, subs))

with open(OUT, 'w', encoding='utf-8') as o:
    tot_main = None
    for sid, s, subs in sorted(rows, key=lambda r: min(r[1]['ts'])):
        start = dt.datetime.fromtimestamp(min(s['ts']))
        wall = (max(s['ts']) - min(s['ts'])) / 3600
        act = active(s['ts']) / 3600
        agg = scan.__defaults__ if False else None
        sub_tot = dict(phases=collections.Counter(), tools=collections.Counter(), edits=collections.Counter(),
                       models=collections.Counter(), ctx=[], turns=0, out_tok=0, in_tok=0, cr=0, cw=0, errors=0,
                       compacts=0, bigdoc_reads=0, reread=0, repatch=0, big_results=0, tests=0, tests_fail=0,
                       n_calls=0, todo=0, bg=0, streak_max=0, fail_streak_max=0, tests_after_last_fix=0,
                       tail_after_last_fix=0)
        sub_act = 0
        orient = []
        big_subs = 0
        for ss in subs:
            merge(sub_tot, ss)
            sub_act += active(ss['ts'])
            if ss['first_edit_idx']:
                orient.append(ss['first_edit_idx'])
            if ss['ctx'] and max(ss['ctx']) > 150000:
                big_subs += 1
        o.write(f"\n## {sid} start={start:%m-%d %H:%M} wall={wall:.1f}h active={act:.1f}h askwait={s['ask_wait']/3600:.1f}h asks={s['asks']}\n")
        o.write(f"prompt: {s['first_prompt']}\n")
        o.write(f"MAIN turns={s['turns']} calls={s['n_calls']} peakctx={max(s['ctx'] or [0])//1000}k medctx={sorted(s['ctx'] or [0])[len(s['ctx'] or [0])//2]//1000}k cache_read={s['cr']/1e6:.1f}M cw={s['cw']/1e6:.1f}M out={s['out_tok']/1e3:.0f}k compacts={s['compacts']} models={dict(s['models'])}\n")
        o.write(f"MAIN phases={dict(s['phases'].most_common())} edits={dict(s['edits'])} todo={s['todo']} bg={s['bg']}\n")
        dc = collections.Counter((d[0], d[1]) for d in s['dispatch'])
        o.write(f"DISPATCH n={len(s['dispatch'])} by(type,model)={dict(dc.most_common(8))}\n")
        if subs:
            o.write(f"SUBS n={len(subs)} active={sub_act/3600:.1f}h turns={sub_tot['turns']} calls={sub_tot['n_calls']} peakctx={max(sub_tot['ctx'] or [0])//1000}k subs>150k={big_subs} cache_read={sub_tot['cr']/1e6:.1f}M cw={sub_tot['cw']/1e6:.1f}M out={sub_tot['out_tok']/1e3:.0f}k models={dict(sub_tot['models'])}\n")
            o.write(f"SUBS phases={dict(sub_tot['phases'].most_common())} edits={dict(sub_tot['edits'])}\n")
            o.write(f"SUBS orient_calls_before_first_product_edit median={sorted(orient)[len(orient)//2] if orient else '-'} n={len(orient)} repatch={sub_tot['repatch']} reread={sub_tot['reread']} bigdoc_reads={sub_tot['bigdoc_reads']} big_results={sub_tot['big_results']} errors={sub_tot['errors']} tests={sub_tot['tests']} fail={sub_tot['tests_fail']} fail_streak_max={sub_tot['fail_streak_max']} id_streak_max={sub_tot['streak_max']} verify_after_last_fix={sub_tot['tests_after_last_fix']}/{sub_tot['tail_after_last_fix']} todo={sub_tot['todo']}\n")
        o.write(f"MAIN repatch={s['repatch']} reread={s['reread']} bigdoc_reads={s['bigdoc_reads']} big_results={s['big_results']} errors={s['errors']} tests={s['tests']} fail={s['tests_fail']} id_streak_max={s['streak_max']} verify_after_last_fix={s['tests_after_last_fix']}/{s['tail_after_last_fix']}\n")
print(len(rows), 'sessions')
