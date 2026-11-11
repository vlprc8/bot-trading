"""Les décisions du robot : exactement les règles du labo, appliquées au dernier jour connu.

Le matin du jour D (avant l'ouverture), on regarde les cours jusqu'à la clôture de la veille
(D-1, dernière séance terminée) et on décide les ordres qui partiront à l'ouverture de D :
c'est la même chose que « décision le soir, ordre à l'ouverture du lendemain » dans le labo.
"""

import pandas as pd

from lab import strategies, univers

STRATEGIES = {s.nom: s for s in strategies.TOUTES}


def symboles_poche(poche):
    return list(poche.get("symboles") or univers.UNIVERS[poche["univers"]])


def _jusqua(df, jour):
    return df[df.index <= pd.Timestamp(jour)]


def decider_calendrier(poche, positions, jour, sessions_mois, budget_par_position, ordre_max):
    """Tournant du mois : achat à l'ouverture de l'avant-dernière séance du mois,
    vente à l'ouverture de la 4e séance du mois suivant."""
    jour = pd.Timestamp(jour)
    sessions = [pd.Timestamp(s) for s in sessions_mois]
    rang = sessions.index(jour) if jour in sessions else -1
    ventes, achats = [], []
    for p in positions:
        entree_mois_precedent = pd.Timestamp(p["date_entree"]).to_period("M") < jour.to_period("M")
        if entree_mois_precedent and rang >= 3:
            ventes.append((p, "4e séance du mois : fin de la fenêtre du tournant du mois"))
    if not positions and len(sessions) >= 2 and jour == sessions[-2]:
        for s in poche["symboles"]:
            achats.append((s, None, "avant-dernière séance du mois : début du tournant du mois"))
    return ventes, achats


def _atr(df):
    a = strategies.atr(df, 14)
    return float(a.iloc[-1]) if len(a) and not pd.isna(a.iloc[-1]) else None


def decider(poche, data, positions, detenus_ailleurs, jour, derniere_session, sessions_mois,
            capital_total, ordre_max):
    """Retourne (ventes [(position, raison)], achats [(symbole, montant_$, prix_ref, raison, atr)]).
    Le montant est en dollars : le robot achète des fractions d'actions."""
    strat = STRATEGIES[poche["strategie"]]
    montant = round(min(capital_total * poche["part"] / poche["max_positions"], ordre_max), 2)

    if strat.nom == "tournant_du_mois":
        ventes, brut = decider_calendrier(poche, positions, jour, sessions_mois, montant, ordre_max)
        achats = []
        for s, _, raison in brut:
            df = _jusqua(data.get(s, pd.DataFrame()), derniere_session)
            if df.empty or s in detenus_ailleurs or montant < 1:
                continue
            achats.append((s, montant, float(df["close"].iloc[-1]), raison, _atr(df)))
        return ventes, achats

    ventes = []
    for p in positions:
        df = _jusqua(data.get(p["symbole"], pd.DataFrame()), derniere_session)
        if df.empty:
            continue
        _, _, sortie = strat.signaux(df)
        detenue = int((df.index >= pd.Timestamp(p["date_entree"])).sum())
        if bool(sortie.iloc[-1]):
            ventes.append((p, "signal de sortie de %s" % strat.nom))
        elif detenue >= strat.jours_max:
            ventes.append((p, "durée max atteinte (%d séances)" % detenue))

    places = poche["max_positions"] - len(positions) + len(ventes)
    tenus = {p["symbole"] for p in positions} | set(detenus_ailleurs)
    candidats = []
    for s in symboles_poche(poche):
        if s in tenus or s not in data:
            continue
        df = _jusqua(data[s], derniere_session)
        if df.empty or df.index[-1] != pd.Timestamp(derniere_session):
            continue  # données pas à jour : on ne décide pas sur un vieux cours
        entree, score, _ = strat.signaux(df)
        if bool(entree.iloc[-1]):
            candidats.append((float(score.iloc[-1]), s, float(df["close"].iloc[-1]), _atr(df)))
    candidats.sort(key=lambda c: (c[0], c[1]))
    achats = []
    if montant >= 1:
        for _, s, prix, a in candidats[:max(0, places)]:
            achats.append((s, montant, prix, "signal d'entrée de %s" % strat.nom, a))
    return ventes, achats


def stop_securite(prix, atr, poche, config):
    """Le stop de sécurité d'une position (prix - stop_atr x ATR), ou None s'il est désactivé."""
    if not atr or not poche.get("stop_securite", True):
        return None
    return round(prix - config["stop_atr"] * atr, 2)
