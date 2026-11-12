"""Les chiffres qui comptent pour juger une stratégie."""

import numpy as np
import pandas as pd

PERIODES = {
    "tout": ("2006-01-01", None),
    "reglage (2006-2018)": ("2006-01-01", "2018-12-31"),
    "verification (2019-auj.)": ("2019-01-01", None),
}


def _tranche(s, debut, fin):
    s = s[s.index >= pd.Timestamp(debut)]
    if fin:
        s = s[s.index <= pd.Timestamp(fin)]
    return s


def stats_courbe(eq, jours_an=252):
    """Rendement annuel, pire baisse, volatilité, Sharpe, sur une courbe de capital."""
    eq = eq.dropna()
    if len(eq) < 2:
        return {}
    r = eq.pct_change().dropna()
    annees = len(r) / float(jours_an)
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / annees) - 1 if annees > 0 else np.nan
    dd = (eq / eq.cummax() - 1).min()
    vol = r.std() * np.sqrt(jours_an)
    sharpe = r.mean() / r.std() * np.sqrt(jours_an) if r.std() > 0 else np.nan
    return {"rendement_annuel": cagr, "pire_baisse": dd, "volatilite": vol, "sharpe": sharpe,
            "gain_total": eq.iloc[-1] / eq.iloc[0] - 1}


def stats_trades(trades):
    if trades is None or trades.empty:
        return {"nb_trades": 0}
    mois = max(1.0, (trades["sortie"].max() - trades["entree"].min()).days / 30.44)
    gagnants = trades[trades["rendement"] > 0]
    perdants = trades[trades["rendement"] <= 0]
    gain_brut = gagnants["pnl"].sum()
    perte_brute = -perdants["pnl"].sum()
    return {"nb_trades": int(len(trades)), "trades_par_mois": len(trades) / mois,
            "taux_reussite": len(gagnants) / len(trades), "trade_moyen": trades["rendement"].mean(),
            "jours_moyens": trades["jours"].mean(),
            "facteur_profit": gain_brut / perte_brute if perte_brute > 0 else np.nan}


def tableau(resultats, reference):
    """resultats : {nom: sortie de moteur.backtest}. reference : Series de la référence.
    Retourne une liste de lignes (dict) par période et par stratégie."""
    lignes = []
    for periode, (debut, fin) in PERIODES.items():
        ref = stats_courbe(_tranche(reference, debut, fin))
        lignes.append(dict(periode=periode, strategie="REFERENCE (acheter SPY et garder)", **ref,
                           nb_trades=1, exposition=1.0))
        for nom, res in resultats.items():
            eq = _tranche(res["equity"], debut, fin)
            t = res["trades"]
            t = t[(t["sortie"] >= pd.Timestamp(debut)) & ((t["sortie"] <= pd.Timestamp(fin)) if fin else True)]
            expo = _tranche(res["exposition"], debut, fin).mean()
            lignes.append(dict(periode=periode, strategie=nom, **stats_courbe(eq), **stats_trades(t),
                               exposition=expo))
    return lignes
