"""NIH Office of Dietary Supplements consumer fact sheets (U.S. federal government work)."""
import re, time
from bs4 import BeautifulSoup
from common import get, sections_from_html, write, words

SHEETS = [('ttc', 'folate'), ('body', 'iron'), ('body', 'calcium'), ('body', 'vitamind'), ('body', 'vitaminb12'), ('pregnancy', 'iodine'), ('pregnancy', 'omega3fattyacids')]
NAMES = {'folate': 'Folate', 'iron': 'Iron', 'calcium': 'Calcium', 'vitamind': 'VitaminD', 'vitaminb12': 'VitaminB12', 'iodine': 'Iodine', 'omega3fattyacids': 'Omega3FattyAcids'}
for cat, s in SHEETS:
    url = f'https://ods.od.nih.gov/factsheets/{NAMES[s]}-Consumer/'
    try:
        soup = BeautifulSoup(get(url), 'html.parser')
        main = soup.select_one('#cs-content') or soup.select_one('main') or soup.body
        title = soup.find('h1').get_text(' ', strip=True) if soup.find('h1') else s
        secs = sections_from_html(main)
        m = re.search(r'Updated:\s*([A-Z][a-z]+ \d{1,2}, \d{4})', soup.get_text(' '))
        art = {'id': f'ods-{s}', 'category': cat, 'title': title, 'url': url, 'lang': 'en', 'publisher': 'NIH ODS',
               'source': 'Office of Dietary Supplements, U.S. National Institutes of Health (ods.od.nih.gov)',
               'attribution': 'U.S. federal government work (NIH ODS). Ask your doctor or pharmacist before taking supplements.',
               'noTranslate': False, 'reviewed': m.group(1) if m else '', 'sections': secs}
        if words(art) > 150: write('ods', art); print('OK', art['id'], words(art))
        else: print('THIN', art['id'])
    except Exception as e:
        print('FAIL', s, e)
    time.sleep(1)
