import json, sys

def fmt_date(d):
    if not d:
        return ""
    if isinstance(d, str):
        return d[:7]
    y = d.get("year") or ""
    m = d.get("month") or ""
    return f"{y}-{str(m).zfill(2)}" if m else str(y)

def fmt_dur(d):
    if not d:
        return ""
    y = d.get("years") or 0
    m = d.get("months") or 0
    parts = []
    if y:
        parts.append(f"{y}yr")
    if m:
        parts.append(f"{m}mo")
    return " ".join(parts)

batch = sys.argv[1] if len(sys.argv) > 1 else "output/batch-16.jsonl"

with open(batch, encoding="utf-8") as f:
    profiles = [json.loads(l) for l in f]

for i, p in enumerate(profiles):
    name = f"{p.get('first_name','') or ''} {p.get('middle_name','') or ''} {p.get('last_name','') or ''}".strip()
    slug = p.get('publicIdentifier', '') or p.get('public_identifier', '')
    headline = p.get('headline', '') or ''
    loc = p.get('location') or {}
    loc_name = loc.get('name', '')
    loc_cc = (loc.get('country') or {}).get('code', '')

    exp_lines = []
    for e in (p.get('experience') or []):
        co = (e.get('company') or {}).get('name', '?')
        for pos in (e.get('positions') or []):
            role = pos.get('role', '?')
            curr = pos.get('is_current_position', False)
            sd = fmt_date(pos.get('start_date'))
            ed = fmt_date(pos.get('end_date'))
            dur = fmt_dur(pos.get('duration'))
            flag = ' [CURRENT]' if curr else ''
            exp_lines.append(f'  {co}: {role} ({sd}-{ed}) {dur}{flag}')

    edu_lines = []
    for ed in (p.get('education') or []):
        inst = (ed.get('institute') or {}).get('name', '?')
        deg = ed.get('degree_program', '') or ''
        sy = fmt_date(ed.get('start_date'))
        ey = fmt_date(ed.get('end_date'))
        edu_lines.append(f'  {inst}: {deg} ({sy}-{ey})')

    langs = [l.get('language','') for l in (p.get('languages') or [])]

    print(f'=== {i+1}. {name} ({slug}) ===')
    print(f'  Headline: {headline}')
    print(f'  Location: {loc_name} ({loc_cc})')
    print(f'  Languages: {", ".join(langs)}')
    print('  Experience:')
    for l in exp_lines:
        print(l)
    print('  Education:')
    for l in edu_lines:
        print(l)
    print()
