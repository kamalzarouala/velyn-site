"""Shared helpers: polite HTTP, HTML → sections, article file writing."""
import json, pathlib, re, time, urllib.request
from bs4 import BeautifulSoup

UA = {'User-Agent': 'Mozilla/5.0 (VelynContentBot; +https://kamalzarouala.github.io/velyn-site/)'}
RAW = pathlib.Path('raw')

def get(url, headers=None, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **(headers or {})}), timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            if '429' in str(e) and i + 1 < tries:
                time.sleep(20 * (i + 1)); continue
            raise

STOP = re.compile(r'^(Sources|Related|More information|Did we answer|For more information|Resources|References|Page last|Content last|On This Page|Keep Reading|Related Pages|Print)', re.I)

def sections_from_html(node):
    for bad in node.select('nav, header, footer, script, style, .breadcrumb, form, aside, figure, .share, .feedback, button'):
        bad.decompose()
    sections, cur = [], None
    for el in node.find_all(['h2', 'h3', 'p', 'ul', 'ol']):
        if el.name in ('ul', 'ol') and el.find_parent(['ul', 'ol']): continue
        if el.name == 'p' and el.find_parent(['li']): continue
        txt = el.get_text(' ', strip=True)
        if not txt: continue
        if el.name in ('h2', 'h3'):
            cur = {'q': txt, 'blocks': []}; sections.append(cur); continue
        if cur is None:
            cur = {'q': '', 'blocks': []}; sections.append(cur)
        if el.name == 'p':
            if STOP.match(txt): continue
            cur['blocks'].append({'p': txt})
        else:
            items = [li.get_text(' ', strip=True) for li in el.find_all('li', recursive=False)]
            items = [i for i in items if i]
            if items: cur['blocks'].append({'ul': items})
    return [s for s in sections if s['blocks'] and not STOP.match(s['q'])]

def write(source, art):
    d = RAW / source; d.mkdir(parents=True, exist_ok=True)
    (d / f"{art['id']}.json").write_text(json.dumps(art, ensure_ascii=False, indent=1))

def words(art): return sum(len(json.dumps(s).split()) for s in art['sections'])
