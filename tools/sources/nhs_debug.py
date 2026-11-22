import json, re, time
from nhs import fetch, KEY
for p in ['conditions/periods', 'conditions/menopause', 'conditions/pre-eclampsia']:
    d = fetch(p); time.sleep(3)
    print('=====', p); print(json.dumps(d.get('hasPart'), ensure_ascii=False)[:2500])
found = set()
for page in range(1, 40):
    d = fetch(f'conditions?page={page}'); time.sleep(2)
    if not d: break
    s = json.dumps(d)
    for u in re.findall(r'https?://[^"]+', s):
        if re.search(r'period|pcos|polycystic|discharge|natal|menopause', u): found.add(u)
    if '"nextPage"' not in s and 'next' not in s.lower(): break
print('FOUND', sorted(found))
