"""Récupération et lecture des cours journaliers.

Source : Yahoo Finance via la bibliothèque yfinance (gratuit, non officiel).
Les cours sont AJUSTÉS (dividendes et divisions d'actions), indispensable pour
qu'un backtest ne voie pas de faux krachs le jour d'une division d'action.

Chaque valeur est enregistrée dans data/<SYMBOLE>.csv.gz avec les colonnes
date, open, high, low, close, volume.
"""

import os

import numpy as np
import pandas as pd

DOSSIER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
COLONNES = ["open", "high", "low", "close", "volume"]


def chemin(symbole, dossier=DOSSIER):
    return os.path.join(dossier, "%s.csv.gz" % symbole)


def telecharger(symboles, debut="2005-01-01", dossier=DOSSIER):
    """Télécharge les cours journaliers ajustés depuis Yahoo et les enregistre.
    Retourne (réussis, ratés)."""
    import yfinance as yf  # importé ici : inutile pour les tests hors ligne

    os.makedirs(dossier, exist_ok=True)
    ok, rates = [], []
    for s in symboles:
        try:
            df = yf.download(s, start=debut, auto_adjust=True, progress=False, threads=False)
        except Exception as exc:  # réseau, symbole inconnu, changement côté Yahoo...
            print("  %-6s ECHEC : %s" % (s, exc))
            rates.append(s)
            continue
        if df is None or df.empty:
            print("  %-6s ECHEC : aucune donnée" % s)
            rates.append(s)
            continue
        if isinstance(df.columns, pd.MultiIndex):  # yfinance récent : colonnes (champ, symbole)
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.lower)[COLONNES].dropna(subset=["open", "close"])
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        df.index.name = "date"
        df.to_csv(chemin(s, dossier), compression="gzip", float_format="%.6f")
        print("  %-6s %5d jours, du %s au %s" % (s, len(df), df.index[0].date(), df.index[-1].date()))
        ok.append(s)
    return ok, rates


def charger(symboles, dossier=DOSSIER):
    """Lit les fichiers enregistrés. Retourne {symbole: DataFrame}. Ignore les absents."""
    out = {}
    for s in symboles:
        p = chemin(s, dossier)
        if os.path.exists(p):
            df = pd.read_csv(p, index_col="date", parse_dates=["date"])
            out[s] = df[COLONNES].astype(float)
    return out


def synthetiques(symboles, debut="2005-01-03", fin="2026-10-30", graine=7):
    """Données inventées, pour tester le moteur sans réseau. NE PAS en tirer de conclusion."""
    rng = np.random.default_rng(graine)
    dates = pd.bdate_range(debut, fin)
    out = {}
    for k, s in enumerate(symboles):
        n = len(dates)
        tendance = 0.0003 + 0.0002 * (k % 3)
        bruit = rng.normal(0, 0.012 + 0.002 * (k % 5), n)
        rend = tendance + bruit - 0.15 * np.concatenate([[0], bruit[:-1]])  # un peu de retour à la moyenne
        close = 50 * np.exp(np.cumsum(rend))
        ouv = close * np.exp(rng.normal(0, 0.004, n))
        haut = np.maximum(ouv, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
        bas = np.minimum(ouv, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
        out[s] = pd.DataFrame({"open": ouv, "high": haut, "low": bas, "close": close,
                               "volume": rng.integers(1e6, 5e6, n).astype(float)},
                              index=pd.DatetimeIndex(dates, name="date"))
    return out
