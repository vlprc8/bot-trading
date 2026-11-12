"""Bougies de 15 minutes depuis 2016, via l'API de données d'Alpaca (gratuite avec un compte, même fictif).

Seules les bougies de la séance normale sont gardées : 9:30 -> 15:45 (heure de New York), soit 26 par jour.
Les cours sont ajustés (dividendes, divisions d'actions). Les fichiers vont dans data_court_terme/
(pas dans le dépôt : trop gros ; GitHub les garde en cache entre deux lancements).
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOSSIER = os.path.join(RACINE, "data_court_terme")
URL = "https://data.alpaca.markets/v2/stocks/bars"


def _get(params):
    req = urllib.request.Request(URL + "?" + urllib.parse.urlencode(params), headers={
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"].strip(),
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"].strip(), "Accept": "application/json"})
    for essai in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:            # trop de requêtes : on attend
                time.sleep(15 * (essai + 1))
                continue
            raise RuntimeError("Alpaca %s : %s" % (e.code, e.read().decode()[:300]))
    raise RuntimeError("Alpaca : trop de refus 429")


def seance_normale(df):
    """Garde 9:30 -> 15:45 (heure de New York) et met l'index en heure de New York sans fuseau."""
    idx = df.index.tz_convert("America/New_York")
    df = df.set_axis(idx.tz_localize(None))
    m = df.index.hour * 60 + df.index.minute
    return df[(m >= 9 * 60 + 30) & (m <= 15 * 60 + 45)]


def telecharger(symbole, debut="2016-01-01", fin=None, dossier=DOSSIER):
    os.makedirs(dossier, exist_ok=True)
    fin = fin or (pd.Timestamp.utcnow() - pd.Timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    lignes, jeton = [], None
    while True:
        params = {"symbols": symbole.replace("-", "."), "timeframe": "15Min", "start": debut, "end": fin,
                  "limit": 10000, "adjustment": "all", "feed": "sip"}
        if jeton:
            params["page_token"] = jeton
        rep = _get(params)
        for b in (rep.get("bars") or {}).get(symbole.replace("-", "."), []):
            lignes.append((b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]))
        jeton = rep.get("next_page_token")
        if not jeton:
            break
        time.sleep(0.35)                # ~170 requêtes par minute, sous la limite de 200
    if not lignes:
        return None
    df = pd.DataFrame(lignes, columns=["t", "open", "high", "low", "close", "volume"])
    df.index = pd.to_datetime(df.pop("t"), utc=True)
    df = seance_normale(df)
    df.to_csv(os.path.join(dossier, "%s.csv.gz" % symbole), compression="gzip", float_format="%.4f")
    return df


def charger(symboles, dossier=DOSSIER):
    out = {}
    for s in symboles:
        p = os.path.join(dossier, "%s.csv.gz" % s)
        if os.path.exists(p):
            df = pd.read_csv(p, index_col=0, parse_dates=[0])
            out[s] = df.astype(float)
    return out


def synthetiques(symboles, debut="2016-01-04", fin="2026-10-30", graine=11):
    """Bougies inventées (26 par jour) pour tester le code. Aucune conclusion possible."""
    rng = np.random.default_rng(graine)
    jours = pd.bdate_range(debut, fin)
    heures = pd.timedelta_range("09:30:00", "15:45:00", freq="15min")
    out = {}
    for k, s in enumerate(symboles):
        n = len(jours) * len(heures)
        r = rng.normal(0.00002 * (1 + k % 3), 0.003, n)
        r[::len(heures)] += rng.normal(0, 0.008, len(jours))       # trou d'ouverture chaque matin
        c = 50 * np.exp(np.cumsum(r))
        o = np.concatenate([[50], c[:-1]])
        o[::len(heures)] = c[::len(heures)] / np.exp(r[::len(heures)]) * np.exp(r[::len(heures)])
        h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0015, n)))
        l_ = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0015, n)))
        idx = pd.DatetimeIndex([d + t for d in jours for t in heures])
        out[s] = pd.DataFrame({"open": o, "high": h, "low": l_, "close": c, "volume": 1e5}, index=idx)
    return out
