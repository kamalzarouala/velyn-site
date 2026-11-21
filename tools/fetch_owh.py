"""Fetch womenshealth.gov (public domain) pages and extract them into structured JSON.
Runs in CI (the assistant's sandbox cannot reach the site). Output: raw/owh/<id>.json"""
import json, pathlib, re, sys, time, urllib.parse, urllib.request
from bs4 import BeautifulSoup
out = pathlib.Path('raw/owh'); out.mkdir(parents=True, exist_ok=True)
report = []
for line in pathlib.Path('tools/owh_urls.txt').read_text().splitlines():
    if not line.strip(): continue
    cat, slug, url = line.split('|')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (VelynContentBot; +https://github.com/kamalzarouala)'})
        html = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
    except Exception as e:
        report.append(f'FAIL {slug} {e}'); continue
    soup = BeautifulSoup(html, 'html.parser')
    title = (soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else slug)
    body = soup.select_one('main') or soup.body
    for bad in body.select('nav, header, footer, script, style, .breadcrumb, .share, form, aside, .feedback, figure'):
        bad.decompose()
    reviewed = ''
    m = re.search(r'(Page last updated|Content last reviewed)[:\s]+([A-Z][a-z]+ \d{1,2}, \d{4})', body.get_text(' '))
    if m: reviewed = m.group(2)
    sections, cur = [], None
    for el in body.find_all(['h2', 'h3', 'p', 'ul', 'ol']):
        if el.find_parent(['ul', 'ol']) and el.name in ('ul', 'ol'): continue
        txt = el.get_text(' ', strip=True)
        if not txt: continue
        if el.name in ('h2', 'h3'):
            cur = {'q': txt, 'blocks': []}; sections.append(cur); continue
        if cur is None:
            cur = {'q': '', 'blocks': []}; sections.append(cur)
        if el.name == 'p':
            if re.match(r'^(Page last updated|Content last reviewed|Sources|Return to top|Did we answer)', txt): continue
            cur['blocks'].append({'p': txt})
        else:
            items = [li.get_text(' ', strip=True) for li in el.find_all('li', recursive=False)]
            items = [i for i in items if i]
            if items: cur['blocks'].append({'ul': items})
    sections = [s for s in sections if s['blocks'] and not re.match(r'^(Sources|Related|More information|Did we answer|For more information)', s['q'])]
    words = sum(len(json.dumps(s).split()) for s in sections)
    (out / f'{slug}.json').write_text(json.dumps({'id': slug, 'category': cat, 'title': title, 'url': url,
        'source': 'Office on Women\'s Health, U.S. Department of Health and Human Services (womenshealth.gov)',
        'reviewed': reviewed, 'sections': sections}, ensure_ascii=False, indent=1))
    report.append(f'OK {slug}: {len(sections)} sections, ~{words} words, reviewed {reviewed or "?"}')
    time.sleep(1)
print('\n'.join(report))
