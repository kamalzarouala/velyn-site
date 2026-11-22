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
# Hub pages whose text lives on sub-pages: merged into one article, each sub-page under its own heading.
EXTRA = {'menopause': ['conditions/menopause/symptoms', 'conditions/menopause/treatment', 'conditions/menopause/things-you-can-do']}
PAGES = [
    ('cycle', 'periods', ['conditions/periods', 'womens-health/periods']),
    ('cycle', 'heavy-periods', ['conditions/heavy-periods']),
    ('cycle', 'period-pain', ['symptoms/period-pain', 'conditions/period-pain']),
    ('cycle', 'period-problems', ['conditions/periods/period-problems']),
    ('cycle', 'starting-periods', ['conditions/periods/starting-periods']),
    ('cycle', 'stopped-or-missed-periods', ['symptoms/missed-or-late-periods', 'conditions/stopped-or-missed-periods']),
    ('cycle', 'irregular-periods', ['symptoms/irregular-periods', 'conditions/irregular-periods']),
    ('cycle', 'pre-menstrual-syndrome', ['conditions/pre-menstrual-syndrome']),
    ('cycle', 'polycystic-ovary-syndrome', ['conditions/polycystic-ovary-syndrome-pcos', 'conditions/polycystic-ovary-syndrome', 'womens-health/polycystic-ovary-syndrome-pcos', 'conditions/polycystic-ovary-syndrome-pcos/symptoms']),
    ('cycle', 'endometriosis', ['conditions/endometriosis']),
    ('body', 'vaginal-discharge', ['symptoms/vaginal-discharge', 'conditions/vaginal-discharge', 'womens-health/vaginal-discharge', 'symptoms/unusual-vaginal-discharge']),
    ('body', 'thrush-in-men-and-women', ['conditions/thrush-in-men-and-women']),
    ('body', 'bacterial-vaginosis', ['conditions/bacterial-vaginosis']),
    ('body', 'urinary-tract-infections-utis', ['conditions/urinary-tract-infections-utis']),
    ('menopause', 'menopause', ['conditions/menopause']),
    ('ttc', 'infertility', ['conditions/infertility']),
    ('pregnancy', 'ectopic-pregnancy', ['conditions/ectopic-pregnancy']),
    ('pregnancy', 'miscarriage', ['conditions/miscarriage']),
    ('pregnancy', 'pre-eclampsia', ['conditions/pre-eclampsia']),
    ('pregnancy', 'gestational-diabetes', ['conditions/gestational-diabetes']),
    ('postpartum', 'post-natal-depression', ['mental-health/conditions/post-natal-depression', 'mental-health/conditions/post-natal-depression/overview', 'conditions/post-natal-depression', 'conditions/post-natal-depression/overview', 'mental-health/conditions/postnatal-depression']),
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


ASPECT = {'Overview': '', 'Symptoms': 'Symptoms', 'Causes': 'Causes', 'Diagnosis': 'Diagnosis', 'Treatment': 'Treatment',
          'Prevention': 'Prevention', 'LivingWith': 'Living with it', 'Prognosis': 'Outlook', 'RiskFactors': 'Risk factors',
          'Complications': 'Complications', 'SelfCare': 'Self-care', 'ScreeningAndTests': 'Tests', 'Usage': 'How to use'}


def texts(node):
    """All text pieces below a node, in order (skips the Overview's one-word navigation tiles)."""
    out = []
    for p in (node.get('hasPart') or node.get('mainEntityOfPage') or []) if isinstance(node, dict) else []:
        if not isinstance(p, dict): continue
        if p.get('hasPart') or (isinstance(p.get('mainEntityOfPage'), list) and p['mainEntityOfPage']):
            h = p.get('headline') or ''
            if h: out.append(f'<h3>{h}</h3>')
            out.extend(texts(p)); continue
        t = (p.get('text') or '').strip()
        if not t or ('<' not in t and len(t.split()) < 4): continue  # tiles like "Symptoms"
        h = p.get('headline') or ''
        if h and h != node.get('headline'): out.append(f'<h3>{h}</h3>')
        out.append(html_of(t))
    return out


def page_html(d):
    parts = []
    hp = [p for p in (d.get('hasPart') or []) if isinstance(p, dict)]
    if hp:  # condition pages: one HealthTopicContent per aspect
        for p in hp:
            asp = (p.get('hasHealthAspect') or '').rsplit('/', 1)[-1].replace('HealthAspect', '')
            head = p.get('headline') or ASPECT.get(asp, asp)
            body = texts(p)
            if asp == 'Overview' and not body and p.get('description'):
                body = [f"<p>{p['description']}</p>"]
            if not body: continue
            if head: parts.append(f'<h2>{head}</h2>')
            parts.extend(body)
    else:  # general pages: sections in mainEntityOfPage
        for sec in d.get('mainEntityOfPage') or []:
            if not isinstance(sec, dict): continue
            head = sec.get('headline') or (sec.get('name') if sec.get('name') not in ('section heading', 'markdown') else '')
            body = texts(sec)
            if not body: continue
            if head: parts.append(f'<h2>{head}</h2>')
            parts.extend(body)
    if not parts and d.get('description'):
        parts.append(f"<p>{d['description']}</p>")
    return ''.join(parts)


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
    secs = sections_from_html(BeautifulSoup(page_html(d), 'html.parser'))
    return [x for x in secs if x['blocks']]


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
                for sp in EXTRA.get(slug, []) + subpages(d):  # hub page: add the official sub-pages, each under its own heading
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
