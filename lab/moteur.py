"""Le moteur de backtest : rejoue une stratégie jour par jour sur l'historique.

Règles de simulation (les mêmes que le futur bot) :
  - le soir du jour t, après la clôture, on calcule les signaux avec les données jusqu'à t ;
  - les ordres partent à l'OUVERTURE du jour t+1, au prix d'ouverture ;
  - les ventes passent avant les achats ;
  - au plus `max_positions` positions, chacune d'environ 1/max_positions du capital ;
  - des frais (commission + écart achat/vente + glissement) sont retirés à chaque achat
    et à chaque vente : `frais` = 0,001 veut dire 0,10 % par côté ;
  - actions entières, ou fractions d'actions avec `fractions=True` (au moins 1 $ par ordre),
    jamais de levier ni de vente à découvert ;
  - take profit exceptionnel en option (`tp_pct`, par ex. 0.20 = vendre dès +20 %) ;
  - stop loss / take profit en option (`sl_atr`, `tp_atr`, en multiples de l'ATR 14 jours calculé
    le soir de la décision) : fixés au prix d'achat, actifs À PARTIR DU LENDEMAIN de l'achat
    (comme le robot : pas d'aller-retour dans la journée). Si l'ouverture saute le niveau, la vente
    se fait à l'ouverture ; si le stop et l'objectif sont touchés le même jour, on compte le stop.
Aucune donnée du futur n'est utilisée : les tests le vérifient.
"""

import math

import numpy as np
import pandas as pd

from lab import strategies


def _matrices(donnees, strategie):
    symboles = sorted(donnees)
    dates = sorted(set().union(*[df.index for df in donnees.values()]))
    idx = pd.DatetimeIndex(dates)
    T, N = len(idx), len(symboles)
    O = np.full((T, N), np.nan)
    C = np.full((T, N), np.nan)
    E = np.zeros((T, N), dtype=bool)
    S = np.full((T, N), np.inf)
    X = np.zeros((T, N), dtype=bool)
    H = np.full((T, N), np.nan)
    L = np.full((T, N), np.nan)
    A = np.full((T, N), np.nan)
    for j, s in enumerate(symboles):
        df = donnees[s]
        entree, score, sortie = strategie.signaux(df)
        df = df.reindex(idx)
        O[:, j] = df["open"].to_numpy()
        C[:, j] = df["close"].to_numpy()
        E[:, j] = entree.reindex(idx).fillna(False).to_numpy(dtype=bool)
        S[:, j] = score.reindex(idx).fillna(np.inf).to_numpy()
        X[:, j] = sortie.reindex(idx).fillna(False).to_numpy(dtype=bool)
        H[:, j] = df["high"].to_numpy()
        L[:, j] = df["low"].to_numpy()
        A[:, j] = strategies.atr(donnees[s], 14).reindex(idx).ffill().to_numpy()
    return idx, symboles, O, C, E, S, X, H, L, A


def backtest(donnees, strategie, capital=100_000.0, max_positions=5, frais=0.001, debut="2006-01-01",
             fractions=False, sl_atr=None, tp_atr=None, tp_pct=None):
    """Retourne {"equity": Series, "exposition": Series, "trades": DataFrame, "ouvertes": list}."""
    idx, symboles, O, C, E, S, X, H, L, A = _matrices(donnees, strategie)
    derniere = pd.DataFrame(C).ffill().to_numpy()  # dernier cours connu, pour valoriser
    debut = pd.Timestamp(debut)
    cash = float(capital)
    positions = {}          # j -> dict(qte, cout, i_entree)
    a_vendre, a_acheter = set(), []
    trades, eq, expo, dates = [], [], [], []
    eq_veille = cash

    def vendre(j, i, px, motif):
        nonlocal cash
        p = positions.pop(j)
        recette = p["qte"] * px * (1 - frais)
        cash += recette
        trades.append({"symbole": symboles[j], "entree": idx[p["i_entree"]], "sortie": idx[i],
                       "prix_entree": p["prix"], "prix_sortie": px, "qte": p["qte"],
                       "rendement": recette / p["cout"] - 1, "pnl": recette - p["cout"],
                       "jours": i - p["i_entree"], "motif": motif})

    for i in range(len(idx)):
        if idx[i] < debut:
            continue
        # 1. Ouverture : exécuter les ordres décidés la veille au soir
        for j in sorted(a_vendre):
            px = O[i, j]
            if np.isnan(px):
                continue  # pas de cotation aujourd'hui : on réessaie demain
            vendre(j, i, px, "signal")
        a_vendre = {j for j in a_vendre if j in positions}
        # 1 bis. Pendant la séance : stop loss et take profit des positions achetées avant aujourd'hui
        for j in sorted(positions):
            p = positions[j]
            if p["i_entree"] >= i or np.isnan(O[i, j]):
                continue
            o, h, l = O[i, j], H[i, j], L[i, j]
            sl, tp = p.get("sl"), p.get("tp")
            if sl is not None and o <= sl:
                vendre(j, i, o, "stop loss (ouverture)")
            elif tp is not None and o >= tp:
                vendre(j, i, o, "take profit (ouverture)")
            elif sl is not None and l <= sl:
                vendre(j, i, sl, "stop loss")
            elif tp is not None and h >= tp:
                vendre(j, i, tp, "take profit")
        a_vendre = {j for j in a_vendre if j in positions}
        for j in a_acheter:
            px = O[i, j]
            if np.isnan(px) or px <= 0:
                continue
            budget = min(eq_veille / max_positions, cash / (1 + frais))
            qte = budget / px if fractions else math.floor(budget / px)
            if (fractions and budget < 1) or (not fractions and qte < 1):
                continue
            cout = qte * px * (1 + frais)
            cash -= cout
            atr_veille = A[i - 1, j] if i > 0 else np.nan
            pos = {"qte": qte, "prix": px, "cout": cout, "i_entree": i}
            if not np.isnan(atr_veille):
                if sl_atr:
                    pos["sl"] = px - sl_atr * atr_veille
                if tp_atr:
                    pos["tp"] = px + tp_atr * atr_veille
            if tp_pct:
                pos["tp"] = px * (1 + tp_pct)
            positions[j] = pos
        a_acheter = []

        # 2. Clôture : valoriser le portefeuille
        investi = sum(p["qte"] * derniere[i, j] for j, p in positions.items())
        total = cash + investi
        dates.append(idx[i])
        eq.append(total)
        expo.append(investi / total if total > 0 else 0.0)
        eq_veille = total

        # 3. Le soir : décider des ordres de demain, avec les données jusqu'à aujourd'hui seulement
        for j, p in positions.items():
            detenue = i - p["i_entree"] + 1
            if X[i, j] or detenue >= strategie.jours_max:
                a_vendre.add(j)
        places = max_positions - len(positions) + len(a_vendre)
        if places > 0:
            cand = [j for j in np.flatnonzero(E[i]) if j not in positions and not np.isnan(C[i, j])]
            cand.sort(key=lambda j: (S[i, j], symboles[j]))
            a_acheter = cand[:places]

    trades = pd.DataFrame(trades, columns=["symbole", "entree", "sortie", "prix_entree", "prix_sortie",
                                           "qte", "rendement", "pnl", "jours", "motif"])
    ouvertes = [symboles[j] for j in positions]
    return {"equity": pd.Series(eq, index=pd.DatetimeIndex(dates), name=strategie.nom),
            "exposition": pd.Series(expo, index=pd.DatetimeIndex(dates)),
            "trades": trades, "ouvertes": ouvertes}


def acheter_et_garder(df, capital=100_000.0, frais=0.001, debut="2006-01-01", fractions=False):
    """La référence : tout investir le premier jour à l'ouverture, ne plus rien faire."""
    df = df[df.index >= pd.Timestamp(debut)]
    qte = capital / (df["open"].iloc[0] * (1 + frais))
    qte = qte if fractions else math.floor(qte)
    reste = capital - qte * df["open"].iloc[0] * (1 + frais)
    return pd.Series(reste + qte * df["close"], name="reference")
