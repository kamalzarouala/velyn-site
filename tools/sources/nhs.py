"""NHS website content via the official API (Open Government Licence + NHS syndication terms).
Refreshed daily (NHS requires at least every 7 days). Attribution "Information from the NHS website".
Shown unchanged and not translated. Runs only when the NHS_API_KEY secret is set."""
import json, os, time
from bs4 import BeautifulSoup
from common import get, sections_from_html, write, words

KEY = os.environ.get('NHS_API_KEY', '')
BASE = os.environ.get('NHS_API_BASE', 'https://int.api.service.nhs.uk/nhs-website-content')
PAGES = [
    ('cycle', 'periods'), ('cycle', 'heavy-periods'), ('cycle', 'period-pain'), ('cycle', 'stopped-or-missed-periods'),
    ('cycle', 'irregular-periods'), ('cycle', 'pre-menstrual-syndrome'), ('cycle', 'polycystic-ovary-syndrome'),
    ('cycle', 'endometriosis'), ('body', 'vaginal-discharge'), ('body', 'thrush-in-men-and-women'),
    ('body', 'bacterial-vaginosis'), ('body', 'urinary-tract-infections-utis'), ('menopause', 'menopause'),
    ('ttc', 'infertility'), ('pregnancy', 'ectopic-pregnancy'), ('pregnancy', 'miscarriage'),
    ('pregnancy', 'pre-eclampsia'), ('pregnancy', 'gestational-diabetes'), ('postpartum', 'post-natal-depression'),
]
if not KEY:
    print('SKIP NHS: no key'); raise SystemExit
for cat, slug in PAGES:
    try:
        d = json.loads(get(f'{BASE}/conditions/{slug}', headers={'apikey': KEY}))
        secs = []
        for part in d.get('hasPart', []):
            if not isinstance(part, dict): continue
            head = part.get('headline') or part.get('name') or ''
            body = ''.join(p.get('text', '') for p in part.get('hasPart', []) if isinstance(p, dict)) or part.get('text', '')
            s = sections_from_html(BeautifulSoup(f'<h2>{head}</h2>{body}' if head else body, 'html.parser'))
            secs.extend(s)
        url = d.get('url', '').replace('nhswebsite-staging.nhs.uk', 'www.nhs.uk') or f'https://www.nhs.uk/conditions/{slug}/'
        art = {'id': f'nhs-{slug}', 'category': cat, 'title': d.get('name', slug), 'url': url, 'lang': 'en', 'publisher': 'NHS',
               'source': 'Information from the NHS website (nhs.uk)',
               'attribution': 'Information from the NHS website, refreshed daily. Contains public sector information licensed under the Open Government Licence v3.0.',
               'noTranslate': True, 'reviewed': (d.get('lastReviewed') or [''])[0] if isinstance(d.get('lastReviewed'), list) else (d.get('lastReviewed') or ''),
               'sections': secs}
        if words(art) > 150: write('nhs', art); print('OK', art['id'], words(art))
        else: print('THIN', art['id'], words(art))
    except Exception as e:
        print('FAIL', slug, e)
    time.sleep(7)
