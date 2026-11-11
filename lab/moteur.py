"""Le moteur de backtest : rejoue une stratégie jour par jour sur l'historique.

Règles de simulation (les mêmes que le futur bot) :
  - le soir du jour t, après la clôture, on calcule les signaux avec les données jusqu'à t ;
  - les ordres partent à l'OUVERTURE du jour t+1, au prix d'ouverture ;
  - les ventes passent avant les achats ;
  - au plus `max_positions` positions, chacune d'environ 1/max_positions du capital ;
  - des frais (commission + écart achat/vente + glissement) sont retirés à chaque achat
    et à chaque vente : `frais` = 0,001 veut dire 0,10 % par côté ;
  - actions entières uniquement, jamais de levier ni de vente à découvert.
Aucune donnée du futur n'est utilisée : les tests le vérifient.
"""

import math

import numpy as np
import pandas as pd


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
    for j, s in enumerate(symboles):
        df = donnees[s]
        entree, score, sortie = strategie.signaux(df)
        df = df.reindex(idx)
        O[:, j] = df["open"].to_numpy()
        C[:, j] = df["close"].to_numpy()
        E[:, j] = entree.reindex(idx).fillna(False).to_numpy(dtype=bool)
        S[:, j] = score.reindex(idx).fillna(np.inf).to_numpy()
        X[:, j] = sortie.reindex(idx).fillna(False).to_numpy(dtype=bool)
    return idx, symboles, O, C, E, S, X


def backtest(donnees, strategie, capital=100_000.0, max_positions=5, frais=0.001, debut="2006-01-01"):
    """Retourne {"equity": Series, "exposition": Series, "trades": DataFrame, "ouvertes": list}."""
    idx, symboles, O, C, E, S, X = _matrices(donnees, strategie)
    derniere = pd.DataFrame(C).ffill().to_numpy()  # dernier cours connu, pour valoriser
    debut = pd.Timestamp(debut)
    cash = float(capital)
    positions = {}          # j -> dict(qte, cout, i_entree)
    a_vendre, a_acheter = set(), []
    trades, eq, expo, dates = [], [], [], []
    eq_veille = cash

    for i in range(len(idx)):
        if idx[i] < debut:
            continue
        # 1. Ouverture : exécuter les ordres décidés la veille au soir
        for j in sorted(a_vendre):
            px = O[i, j]
            if np.isnan(px):
                continue  # pas de cotation aujourd'hui : on réessaie demain
            p = positions.pop(j)
            recette = p["qte"] * px * (1 - frais)
            cash += recette
            trades.append({"symbole": symboles[j], "entree": idx[p["i_entree"]], "sortie": idx[i],
                           "prix_entree": p["prix"], "prix_sortie": px, "qte": p["qte"],
                           "rendement": recette / p["cout"] - 1, "pnl": recette - p["cout"],
                           "jours": i - p["i_entree"]})
        a_vendre = {j for j in a_vendre if j in positions}
        for j in a_acheter:
            px = O[i, j]
            if np.isnan(px) or px <= 0:
                continue
            budget = min(eq_veille / max_positions, cash / (1 + frais))
            qte = math.floor(budget / px)
            if qte < 1:
                continue
            cout = qte * px * (1 + frais)
            cash -= cout
            positions[j] = {"qte": qte, "prix": px, "cout": cout, "i_entree": i}
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
                                           "qte", "rendement", "pnl", "jours"])
    ouvertes = [symboles[j] for j in positions]
    return {"equity": pd.Series(eq, index=pd.DatetimeIndex(dates), name=strategie.nom),
            "exposition": pd.Series(expo, index=pd.DatetimeIndex(dates)),
            "trades": trades, "ouvertes": ouvertes}


def acheter_et_garder(df, capital=100_000.0, frais=0.001, debut="2006-01-01"):
    """La référence : tout investir le premier jour à l'ouverture, ne plus rien faire."""
    df = df[df.index >= pd.Timestamp(debut)]
    qte = math.floor(capital / (df["open"].iloc[0] * (1 + frais)))
    reste = capital - qte * df["open"].iloc[0] * (1 + frais)
    return pd.Series(reste + qte * df["close"], name="reference")
