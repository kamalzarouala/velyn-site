"""MedlinePlus health topic summaries (NLM, public domain) in English AND Spanish via the free web service.
Terms: say the information is from MedlinePlus.gov; do not use the logo or imply endorsement."""
import html, re, time, urllib.parse, xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from common import get, sections_from_html, write, words

TOPICS = [  # (category, slug, English title, Spanish title)
    ('cycle', 'menstruation', 'Menstruation', 'Menstruación'),
    ('cycle', 'pms', 'Premenstrual Syndrome', 'Síndrome premenstrual'),
    ('cycle', 'pcos', 'Polycystic Ovary Syndrome', 'Síndrome de ovario poliquístico'),
    ('cycle', 'endometriosis', 'Endometriosis', 'Endometriosis'),
    ('cycle', 'uterine-fibroids', 'Uterine Fibroids', 'Fibromas uterinos'),
    ('body', 'vaginal-diseases', 'Vaginal Diseases', 'Enfermedades vaginales'),
    ('body', 'uti', 'Urinary Tract Infections', 'Infecciones urinarias'),
    ('body', 'osteoporosis', 'Osteoporosis', 'Osteoporosis'),
    ('body', 'birth-control', 'Birth Control', 'Anticonceptivos'),
    ('ttc', 'infertility', 'Infertility', 'Infertilidad'),
    ('ttc', 'folic-acid', 'Folic Acid', 'Ácido fólico'),
    ('pregnancy', 'pregnancy', 'Pregnancy', 'Embarazo'),
    ('pregnancy', 'prenatal-care', 'Prenatal Care', 'Cuidado prenatal'),
    ('pregnancy', 'gestational-diabetes', 'Diabetes in Pregnancy', 'Diabetes y embarazo'),
    ('pregnancy', 'preeclampsia', 'Preeclampsia', 'Preeclampsia'),
    ('pregnancy', 'miscarriage', 'Pregnancy Loss', 'Pérdida del embarazo'),
    ('pregnancy', 'childbirth', 'Childbirth', 'Parto'),
    ('postpartum', 'postpartum-care', 'Postpartum Care', 'Cuidados posparto'),
    ('postpartum', 'postpartum-depression', 'Postpartum Depression', 'Depresión posparto'),
    ('postpartum', 'breastfeeding', 'Breastfeeding', 'Lactancia materna'),
    ('menopause', 'menopause', 'Menopause', 'Menopausia'),
]

def fetch(title, db):
    q = urllib.parse.urlencode({'db': db, 'term': f'title:"{title}"', 'retmax': 3})
    root = ET.fromstring(get(f'https://wsearch.nlm.nih.gov/ws/query?{q}'))
    for doc in root.iter('document'):
        fields = {c.get('name'): c for c in doc.iter('content')}
        t = BeautifulSoup(''.join(fields['title'].itertext()), 'html.parser').get_text(' ', strip=True) if 'title' in fields else ''
        if t.lower() != title.lower(): continue
        summary = html.unescape(''.join(fields['FullSummary'].itertext())) if 'FullSummary' in fields else ''
        return t, doc.get('url'), summary
    return None

for cat, slug, en, es in TOPICS:
    for lang, title, db in (('en', en, 'healthTopics'), ('es', es, 'healthTopicsSpanish')):
        try:
            r = fetch(title, db)
            if not r: print('MISS', lang, title); continue
            t, url, summary = r
            secs = sections_from_html(BeautifulSoup(summary, 'html.parser'))
            art = {'id': f'mlp-{slug}-{lang}', 'category': cat, 'title': t, 'url': url, 'lang': lang, 'publisher': 'MedlinePlus',
                   'source': 'MedlinePlus.gov, U.S. National Library of Medicine' if lang == 'en' else 'MedlinePlus.gov en español, Biblioteca Nacional de Medicina de EE. UU.',
                   'attribution': 'Information from MedlinePlus.gov (public domain). MedlinePlus does not endorse this app.',
                   'noTranslate': False, 'reviewed': '', 'sections': secs}
            if words(art) > 80: write('medlineplus', art); print('OK', art['id'], words(art))
            else: print('THIN', art['id'])
        except Exception as e:
            print('FAIL', lang, title, e)
        time.sleep(0.6)
