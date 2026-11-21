"""CDC pages (public domain). CDC terms: content unchanged, links back kept, never sold for a fee
→ in the app CDC articles are always free and never translated or edited."""
import re, sys, time
from bs4 import BeautifulSoup
from common import get, sections_from_html, write, words

PAGES = [
    ('pregnancy', 'cdc-gestational-diabetes', 'https://www.cdc.gov/diabetes/about/gestational-diabetes.html'),
    ('pregnancy', 'cdc-high-blood-pressure-pregnancy', 'https://www.cdc.gov/high-blood-pressure-during-pregnancy/about/index.html'),
    ('pregnancy', 'cdc-urgent-warning-signs', 'https://www.cdc.gov/hearher/maternal-warning-signs/index.html'),
    ('pregnancy', 'cdc-vaccines-pregnancy', 'https://www.cdc.gov/vaccines-pregnancy/about/index.html'),
    ('pregnancy', 'cdc-alcohol-pregnancy', 'https://www.cdc.gov/alcohol-pregnancy/about/index.html'),
    ('pregnancy', 'cdc-medicines-pregnancy', 'https://www.cdc.gov/medicine-and-pregnancy/about/index.html'),
    ('pregnancy', 'cdc-stillbirth', 'https://www.cdc.gov/stillbirth/about/index.html'),
    ('ttc', 'cdc-folic-acid', 'https://www.cdc.gov/folic-acid/about/index.html'),
    ('ttc', 'cdc-preconception', 'https://www.cdc.gov/preconception-care/about/index.html'),
    ('postpartum', 'cdc-postpartum-depression', 'https://www.cdc.gov/reproductive-health/depression/index.html'),
    ('postpartum', 'cdc-breastfeeding-facts', 'https://www.cdc.gov/breastfeeding/php/about/index.html'),
    ('body', 'cdc-bv', 'https://www.cdc.gov/bacterial-vaginosis/about/index.html'),
    ('body', 'cdc-hpv', 'https://www.cdc.gov/hpv/about/index.html'),
    ('body', 'cdc-cervical-cancer', 'https://www.cdc.gov/cervical-cancer/about/index.html'),
    ('body', 'cdc-chlamydia', 'https://www.cdc.gov/chlamydia/about/index.html'),
]
for cat, slug, url in PAGES:
    try:
        soup = BeautifulSoup(get(url), 'html.parser')
        main = soup.select_one('main') or soup.body
        title = soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else slug
        secs = sections_from_html(main)
        m = re.search(r'(?:Last Reviewed|Page last reviewed)[:\s]+([A-Z][a-z]+ \d{1,2}, \d{4})', soup.get_text(' '))
        art = {'id': slug, 'category': cat, 'title': title, 'url': url, 'lang': 'en', 'publisher': 'CDC',
               'source': 'Centers for Disease Control and Prevention (CDC), cdc.gov',
               'attribution': 'Public domain content from CDC, shown unchanged. Its use does not imply endorsement by CDC.',
               'noTranslate': True, 'reviewed': m.group(1) if m else '', 'sections': secs}
        if words(art) > 150: write('cdc', art); print('OK', slug, len(secs), words(art))
        else: print('THIN', slug, words(art))
    except Exception as e:
        print('FAIL', slug, e)
    time.sleep(1)
