import json, time, traceback
from nhs import fetch
for p in ['conditions/periods', 'conditions/periods?childArticles=true', 'conditions/periods?modules=true', 'conditions/pre-eclampsia', 'conditions/menopause', 'conditions/polycystic-ovary-syndrome-pcos?childArticles=true','mental-health/conditions/post-natal-depression','conditions/post-natal-depression?childArticles=true','symptoms/vaginal-discharge','conditions/period-pain']:
    try:
        d = fetch(p); time.sleep(3)
        print('=====', p, 'NONE' if d is None else '')
        if d: print('DUMP', json.dumps({k: v for k, v in d.items() if k not in ('@context','copyrightHolder','license','author','breadcrumb')}, ensure_ascii=False)[:3500])
    except Exception as e:
        print('=====', p, 'ERR', repr(e)[:300])
