"""Build content/library.json from freshly fetched articles, with safety checks.
An article replaces the published one only if it was fetched and is not suspiciously shorter (< 60% of the words).
Otherwise the last good version is kept. Every change is logged in content/CHANGELOG.md."""
import datetime, hashlib, json, pathlib, re

SKIP = {'breastfeeding-basics', 'heart-disease'}
ORDER = ['cycle', 'body', 'ttc', 'pregnancy', 'postpartum', 'menopause']
FOOT = re.compile(r'(?<=[.:;)!?])\s\d{1,2}(?:\s?[,–-]\s?\d{1,2})*(?=\s|$)')
KEEP = {'age', 'than', 'through', 'trisomy', 'of', 'to', 'under', 'week', 'weeks', 'day', 'days'}
END = re.compile(r'(\S+)\s\|?\s?\d{1,2}(?:,\s?\d{1,2})*$')

def clean(t):
    t = re.sub(r'\s+([.,;:])', r'\1', FOOT.sub('', t)).strip()
    m = END.search(t)
    if m and m.group(1).lower().strip('|') not in KEEP and not m.group(1).isdigit():
        t = t[:m.start()] + m.group(1)
    return t.strip(' |')

def words(a): return sum(len(json.dumps(s).split()) for s in a['sections'])

out = pathlib.Path('content'); out.mkdir(exist_ok=True)
lib_path = out / 'library.json'
old = {a['id']: a for a in json.loads(lib_path.read_text())['articles']} if lib_path.exists() else {}
new, log = {}, []
for f in sorted(pathlib.Path('raw/owh').glob('*.json')):
    d = json.loads(f.read_text())
    if d['id'] in SKIP: continue
    d['sections'] = [{'q': clean(s['q']), 'blocks': [{'p': clean(b['p'])} if 'p' in b else {'ul': [clean(i) for i in b['ul']]} for b in s['blocks']]} for s in d['sections']]
    prev = old.get(d['id'])
    if prev and words(d) < 0.6 * words(prev):
        log.append(f"- KEPT previous `{d['id']}`: new version too short ({words(d)} vs {words(prev)} words)")
        new[d['id']] = prev; continue
    if prev and json.dumps(prev['sections']) != json.dumps(d['sections']):
        log.append(f"- UPDATED `{d['id']}` ({words(prev)} → {words(d)} words, source reviewed {d.get('reviewed') or '?'})")
    if not prev: log.append(f"- ADDED `{d['id']}`: {d['title']}")
    new[d['id']] = d
for i, a in old.items():
    if i not in new:
        log.append(f"- KEPT previous `{i}`: not fetched this time")
        new[i] = a
arts = sorted(new.values(), key=lambda a: (ORDER.index(a['category']), a['title']))
body = json.dumps({'articles': arts}, ensure_ascii=False, separators=(',', ':'))
if not lib_path.exists() or lib_path.read_text() != body:
    lib_path.write_text(body)
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    (out / 'meta.json').write_text(json.dumps({'version': now, 'sha256': hashlib.sha256(body.encode()).hexdigest(),
                                               'articles': len(arts), 'format': 1}))
    cl = out / 'CHANGELOG.md'
    cl.write_text(f"## {now}\n" + ('\n'.join(log) or '- formatting only') + '\n\n' + (cl.read_text() if cl.exists() else ''))
print('\n'.join(log) or 'no change', '|', len(arts), 'articles')
