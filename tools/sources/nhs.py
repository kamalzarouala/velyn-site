"""NHS website content via the official API (Open Government Licence + NHS syndication terms).
Refreshed daily (NHS requires at least every 7 days). Attribution "Information from the NHS website".
Shown unchanged and not translated. Runs only when the NHS_API_KEY secret is set."""
import json, os, time, urllib.error
import markdown as md
from bs4 import BeautifulSoup
from common import get, sections_from_html, write, words

KEY = os.environ.get('NHS_API_KEY', '')
BASE = os.environ.get('NHS_API_BASE', 'https://int.api.service.nhs.uk/nhs-website-content')
# Each page lists several paths: NHS moved some pages (e.g. PCOS, post-natal depression), first one that answers wins.
PAGES = [
    ('cycle', 'periods', ['conditions/periods', 'womens-health/periods']),
    ('cycle', 'heavy-periods', ['conditions/heavy-periods']),
    ('cycle', 'period-pain', ['conditions/period-pain', 'conditions/periods/period-pain']),
    ('cycle', 'stopped-or-missed-periods', ['conditions/stopped-or-missed-periods', 'conditions/periods/stopped-or-missed-periods']),
    ('cycle', 'irregular-periods', ['conditions/irregular-periods', 'conditions/periods/irregular-periods']),
    ('cycle', 'pre-menstrual-syndrome', ['conditions/pre-menstrual-syndrome']),
    ('cycle', 'polycystic-ovary-syndrome', ['conditions/polycystic-ovary-syndrome-pcos', 'conditions/polycystic-ovary-syndrome']),
    ('cycle', 'endometriosis', ['conditions/endometriosis']),
    ('body', 'vaginal-discharge', ['symptoms/vaginal-discharge', 'conditions/vaginal-discharge']),
    ('body', 'thrush-in-men-and-women', ['conditions/thrush-in-men-and-women']),
    ('body', 'bacterial-vaginosis', ['conditions/bacterial-vaginosis']),
    ('body', 'urinary-tract-infections-utis', ['conditions/urinary-tract-infections-utis']),
    ('menopause', 'menopause', ['conditions/menopause', 'womens-health/menopause']),
    ('ttc', 'infertility', ['conditions/infertility']),
    ('pregnancy', 'ectopic-pregnancy', ['conditions/ectopic-pregnancy']),
    ('pregnancy', 'miscarriage', ['conditions/miscarriage']),
    ('pregnancy', 'pre-eclampsia', ['conditions/pre-eclampsia']),
    ('pregnancy', 'gestational-diabetes', ['conditions/gestational-diabetes']),
    ('postpartum', 'post-natal-depression', ['mental-health/conditions/post-natal-depression', 'conditions/post-natal-depression']),
]


def fetch(path):
    """GET with retry on rate limit (429). Returns dict or None for 404."""
    for attempt in range(4):
        try:
            return json.loads(get(f'{BASE}/{path}', headers={'apikey': KEY}))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            if e.code == 429: time.sleep(20 * (attempt + 1)); continue
            raise
        except Exception as e:
            if '404' in str(e): return None
            if '429' in str(e): time.sleep(20 * (attempt + 1)); continue
            raise
    return None


def html_of(text):
    if not text: return ''
    return text if '<' in text[:200] else md.markdown(text)


def collect(node, out, head=''):
    """Walk the whole hasPart tree (any depth): headlines start sections, text/description becomes body."""
    if isinstance(node, list):
        for n in node: collect(n, out, head); return
    if not isinstance(node, dict): return
    h = node.get('headline') or (node.get('name') if node.get('@type') in ('WebPageElement', 'HealthTopicContent') else '')
    if h: out.append(f'<h2>{h}</h2>')
    t = node.get('text') or ''
    if t: out.append(html_of(t))
    for k in ('hasPart', 'mainEntityOfPage'):
        if k in node: collect(node[k], out)


def subpages(d):
    """Hub pages (periods, menopause) only list links: return their sub-page paths on the same topic."""
    links = []
    for k in ('relatedLink', 'significantLink', 'hasPart'):
        v = d.get(k)
        for x in (v if isinstance(v, list) else [v] if v else []):
            if isinstance(x, dict):
                u = x.get('url') or ''
                for p in (x.get('hasPart') or []) if k == 'hasPart' else []:
                    if isinstance(p, dict) and p.get('url'): links.append(p['url'])
                if u: links.append(u)
    base = (d.get('url') or '').rstrip('/')
    out = []
    for u in links:
        u = u.rstrip('/')
        if base and u.startswith(base + '/') and u not in out: out.append(u)
    return [u.split('nhs.uk/', 1)[-1] for u in out][:6]


def sections(d):
    parts = []; collect(d.get('hasPart', []), parts)
    if not parts and d.get('description'): parts.append(f"<p>{d['description']}</p>")
    secs = sections_from_html(BeautifulSoup(''.join(parts), 'html.parser'))
    return [s for s in secs if s['blocks']]


if __name__ == '__main__':
    if not KEY:
        print('SKIP NHS: no key'); raise SystemExit
    for cat, slug, paths in PAGES:
        try:
            d = None
            for p in paths:
                d = fetch(p); time.sleep(3)
                if d: break
            if not d: print('MISSING', slug, paths); continue
            secs = sections(d)
            if sum(len(b.get('p') or ' '.join(b.get('ul') or [])) for s in secs for b in s['blocks']) < 1500:
                for sp in subpages(d):  # hub page: add the official sub-pages, each under its own heading
                    sd = fetch(sp); time.sleep(3)
                    if not sd: continue
                    ss = sections(sd)
                    if ss: ss[0]['q'] = ss[0]['q'] or sd.get('name', '')
                    secs.extend(ss)
            url = (d.get('url') or '').replace('nhswebsite-staging.nhs.uk', 'www.nhs.uk') or f'https://www.nhs.uk/{paths[0]}/'
            rev = d.get('lastReviewed') or ''
            art = {'id': f'nhs-{slug}', 'category': cat, 'title': d.get('name', slug), 'url': url, 'lang': 'en', 'publisher': 'NHS',
                   'source': 'Information from the NHS website (nhs.uk)',
                   'attribution': 'Information from the NHS website, refreshed daily. Contains public sector information licensed under the Open Government Licence v3.0.',
                   'noTranslate': True, 'reviewed': rev[0] if isinstance(rev, list) and rev else (rev if isinstance(rev, str) else ''),
                   'sections': secs}
            n = words(art)
            if n > 150: write('nhs', art); print('OK', art['id'], n)
            else: print('THIN', art['id'], n, 'keys=', list(d.keys())[:15])
        except Exception as e:
            print('FAIL', slug, e)
