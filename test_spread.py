import json
from collections import defaultdict

county_data = {
    'Budapest':        {'Fidesz': 33.12, 'Tisza': 32.81, 'DK': 12.30, 'Mi Hazánk': 4.46, 'MKKP': 5.92},
    'Baranya':         {'Fidesz': 46.59, 'Tisza': 27.14, 'DK': 9.39, 'Mi Hazánk': 6.31, 'MKKP': 3.60},
    'Bács-Kiskun':     {'Fidesz': 48.36, 'Tisza': 28.60, 'DK': 6.25, 'Mi Hazánk': 8.66, 'MKKP': 2.91},
    'Békés':           {'Fidesz': 45.57, 'Tisza': 29.82, 'DK': 7.23, 'Mi Hazánk': 8.67, 'MKKP': 2.63},
    'Borsod-Abaúj-Zemplén': {'Fidesz': 48.77, 'Tisza': 27.30, 'DK': 7.97, 'Mi Hazánk': 7.57, 'MKKP': 2.32},
    'Csongrád-Csanád': {'Fidesz': 38.32, 'Tisza': 31.71, 'DK': 7.84, 'Mi Hazánk': 8.52, 'MKKP': 4.03},
    'Fejér':           {'Fidesz': 45.88, 'Tisza': 29.21, 'DK': 7.14, 'Mi Hazánk': 7.42, 'MKKP': 3.83},
    'Győr-Moson-Sopron':{'Fidesz': 48.02, 'Tisza': 30.55, 'DK': 5.97, 'Mi Hazánk': 6.58, 'MKKP': 3.07},
    'Hajdú-Bihar':     {'Fidesz': 48.13, 'Tisza': 30.28, 'DK': 5.89, 'Mi Hazánk': 7.46, 'MKKP': 2.54},
    'Heves':           {'Fidesz': 47.13, 'Tisza': 28.74, 'DK': 7.41, 'Mi Hazánk': 7.34, 'MKKP': 2.42},
    'Jász-Nagykun-Szolnok': {'Fidesz': 47.16, 'Tisza': 29.69, 'DK': 7.21, 'Mi Hazánk': 6.91, 'MKKP': 2.23},
    'Komárom-Esztergom':{'Fidesz': 42.65, 'Tisza': 31.74, 'DK': 8.79, 'Mi Hazánk': 7.08, 'MKKP': 3.46},
    'Nógrád':          {'Fidesz': 51.60, 'Tisza': 24.43, 'DK': 8.04, 'Mi Hazánk': 8.85, 'MKKP': 2.30},
    'Pest':            {'Fidesz': 41.38, 'Tisza': 32.09, 'DK': 7.10, 'Mi Hazánk': 7.22, 'MKKP': 4.50},
    'Somogy':          {'Fidesz': 50.18, 'Tisza': 27.19, 'DK': 7.85, 'Mi Hazánk': 6.80, 'MKKP': 2.40},
    'Szabolcs-Szatmár-Bereg': {'Fidesz': 54.47, 'Tisza': 26.80, 'DK': 6.33, 'Mi Hazánk': 6.36, 'MKKP': 1.61},
    'Tolna':           {'Fidesz': 51.94, 'Tisza': 24.94, 'DK': 7.02, 'Mi Hazánk': 7.75, 'MKKP': 2.57},
    'Vas':             {'Fidesz': 51.30, 'Tisza': 26.73, 'DK': 7.15, 'Mi Hazánk': 5.91, 'MKKP': 2.98},
    'Veszprém':        {'Fidesz': 45.56, 'Tisza': 29.28, 'DK': 8.12, 'Mi Hazánk': 6.94, 'MKKP': 3.49},
    'Zala':            {'Fidesz': 49.83, 'Tisza': 28.19, 'DK': 7.14, 'Mi Hazánk': 6.74, 'MKKP': 2.52},
}

specific = {
    'Borsod-Abaúj-Zemplén 03': {'Fidesz': 55.0, 'Tisza': 22.0, 'DK': 8.0, 'Mi Hazánk': 9.0, 'MKKP': 2.0},
    'Borsod-Abaúj-Zemplén 04': {'Fidesz': 55.0, 'Tisza': 22.0, 'DK': 8.0, 'Mi Hazánk': 9.0, 'MKKP': 2.0},
    'Győr-Moson-Sopron 02':     {'Fidesz': 43.5, 'Tisza': 35.8, 'DK': 5.5, 'Mi Hazánk': 7.1, 'MKKP': 3.8},
    'Budapest 11':              {'Fidesz': 30.1, 'Tisza': 39.5, 'DK': 10.2, 'Mi Hazánk': 3.5, 'MKKP': 8.4},
    'Hajdú-Bihar 06':           {'Fidesz': 48.4, 'Tisza': 28.5, 'DK': 5.8, 'Mi Hazánk': 10.2, 'MKKP': 2.9},
    'Baranya 04':               {'Fidesz': 63.0, 'Tisza': 18.0, 'DK': 8.0, 'Mi Hazánk': 8.0, 'MKKP': 2.0},
    'Zala 03':                  {'Fidesz': 44.1, 'Tisza': 30.2, 'DK': 9.1, 'Mi Hazánk': 7.5, 'MKKP': 3.2},
}

geo = json.load(open('data/oevk.json', 'r', encoding='utf-8'))
oevk_names = sorted([f['properties']['name'] for f in geo['features']])
county_oevks = defaultdict(list)
for name in oevk_names:
    county = name.rsplit(' ', 1)[0]
    county_oevks[county].append(name)

ep_nat = {'Fidesz': 44.82, 'Tisza': 29.60, 'DK': 8.03, 'Mi Hazánk': 6.71, 'MKKP': 3.59}

def gen(spread):
    oevk_data = {}
    for county, names in county_oevks.items():
        if county not in county_data:
            for n in names:
                oevk_data[n] = dict(ep_nat)
            continue
        base = county_data[county]
        N = len(names)
        for i, name in enumerate(sorted(names)):
            if name in specific:
                oevk_data[name] = specific[name].copy()
                continue
            t = i / (N - 1) if N > 1 else 0.5
            offset = spread * (2 * t - 1)
            d = {
                'Fidesz': max(5, base['Fidesz'] + offset),
                'Tisza': max(5, base['Tisza'] - offset * 0.7),
                'DK': max(1, base['DK'] - offset * 0.1),
                'Mi Hazánk': max(1, base['Mi Hazánk'] + offset * 0.15),
                'MKKP': max(0.5, base['MKKP'] - offset * 0.05),
            }
            oevk_data[name] = {k: round(v, 2) for k, v in d.items()}
    return oevk_data

def simulate(oevk_data, user):
    parties = list(user.keys())
    mult = {p: (user[p] / ep_nat[p]) if ep_nat[p] > 0 else 0 for p in parties}
    oevk_wins = {p: 0 for p in parties}
    comp = {p: 0.0 for p in parties}
    avg_v = 5000000 / 106
    for name, base in oevk_data.items():
        raw = {p: base.get(p, 0) * mult[p] for p in parties}
        total = sum(raw.values())
        if total == 0:
            continue
        norm = {p: (v/total)*100 for p, v in raw.items()}
        ranked = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        winner = ranked[0][0]
        oevk_wins[winner] += 1
        w_v = (ranked[0][1]/100) * avg_v
        r_v = (ranked[1][1]/100) * avg_v
        comp[winner] += max(0, w_v - r_v + 1)
        for p in parties:
            if p != winner:
                comp[p] += (norm[p]/100) * avg_v
    mail = {'Fidesz':250000, 'Tisza':50000, 'Mi Hazánk':5000, 'DK':1000, 'MKKP':1000}
    list_v = {}
    for p in parties:
        lv = (user[p]/100)*5000000 + mail.get(p,0) + comp[p]
        if user[p] < 5:
            lv = 0
        list_v[p] = lv
    dh = []
    for p, v in list_v.items():
        if v > 0:
            for d in range(1, 94):
                dh.append((v/d, p))
    dh.sort(key=lambda x: x[0], reverse=True)
    list_m = {p: 0 for p in parties}
    for i in range(min(93, len(dh))):
        list_m[dh[i][1]] += 1
    total_m = {}
    for p in parties:
        total_m[p] = oevk_wins[p] + list_m[p]
    total_m['Fidesz'] += 1
    return oevk_wins, list_m, total_m

user = {'Tisza': 50, 'Fidesz': 39, 'Mi Hazánk': 5, 'DK': 3, 'MKKP': 3}

print("Target: Tisza 119 (75 OEVK + 44 list), Fidesz 75 (31 OEVK + 44 list), MH 5")
print()
for sp in [5.0, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 11.0, 12.0]:
    od = gen(sp)
    ow, lm, tm = simulate(od, user)
    t_str = f"Tisza {tm['Tisza']}(oevk={ow['Tisza']} list={lm['Tisza']})"
    f_str = f"Fidesz {tm['Fidesz']}(oevk={ow['Fidesz']} list={lm['Fidesz']})"
    m_str = f"MH {tm['Mi Hazánk']}"
    print(f"SPREAD={sp:5.1f}: {t_str}  {f_str}  {m_str}")
