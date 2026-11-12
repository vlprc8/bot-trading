"""Stratégies de court terme (dans la journée, ou 1 jour), sur bougies de 15 minutes.

Règles écrites le 12/11/2026, AVANT tout test sur les vraies données.
Bougies de la séance : n°0 = 9:30-9:45, n°1 = 9:45-10:00, ..., n°24 = 15:30-15:45, n°25 = 15:45-16:00
(heure de New York ; ajouter 6 h pour Paris en temps normal).

Pour ne jamais utiliser le futur : un signal se lit sur une bougie TERMINÉE, et l'achat se fait à
l'ouverture de la bougie SUIVANTE.

1. cassure_ouverture (actions, journée) : le range d'ouverture est la 1re bougie (9:30-9:45).
   Signal : la 1re bougie, de 9:45 à 14:45, qui clôture au-dessus du plus haut du range.
   Achat à l'ouverture de la bougie suivante. Stop : milieu du range. Objectif : 2 fois le risque.
   Sinon vente à la clôture (16:00). Filtre : clôture de la veille au-dessus de sa moyenne 200 jours.
2. rebond_trou (actions, journée) : l'action ouvre au moins 2 % sous la clôture de la veille (« trou »),
   mais la 2e bougie (9:45-10:00) clôture au-dessus du prix d'ouverture : les acheteurs reviennent.
   Achat à 10:00. Stop : plus bas des 30 premières minutes. Vente à la clôture. Même filtre 200 jours.
3. fin_de_seance (SPY et QQQ, journée) : si l'indice est en hausse à 10:00 par rapport à la veille,
   achat à 15:30 et vente à la clôture (effet « dernière demi-heure », Gao, Han, Li et Zhou, 2018).
4. chute_du_jour (actions, 1 jour) : à 15:45, l'action perd au moins 3 % sur la journée alors qu'elle
   est au-dessus de sa moyenne 200 jours : achat à 15:45, vente le lendemain à 15:45.
"""

import numpy as np
import pandas as pd

ACTIONS = "actions"
INDICES = ["SPY", "QQQ"]


def par_jour(df):
    """{date: (o, h, l, c)} pour les jours complets (26 bougies), plus la série des clôtures du jour."""
    jours = {}
    for d, g in df.groupby(df.index.normalize()):
        if len(g) != 26:
            continue                       # demi-séance ou trou dans les données : on saute ce jour
        jours[d] = (g["open"].to_numpy(), g["high"].to_numpy(), g["low"].to_numpy(), g["close"].to_numpy())
    clo = pd.Series({d: v[3][-1] for d, v in jours.items()}).sort_index()
    return jours, clo


def sortie(o, h, l, c, i0, stop=None, objectif=None, i_fin=None):
    """Simule la sortie à partir de la bougie i0 (achat à son ouverture). Le stop passe avant l'objectif
    si les deux sont touchés dans la même bougie. Retourne (prix, motif, bougie)."""
    i_fin = len(c) - 1 if i_fin is None else i_fin
    for i in range(i0, i_fin + 1):
        if stop is not None and o[i] <= stop and i > i0:
            return o[i], "stop (ouverture)", i
        if objectif is not None and o[i] >= objectif and i > i0:
            return o[i], "objectif (ouverture)", i
        if stop is not None and l[i] <= stop:
            return stop, "stop", i
        if objectif is not None and h[i] >= objectif:
            return objectif, "objectif", i
    return c[i_fin], "clôture", i_fin


def trades_symbole(symbole, df, strategies):
    """Tous les trades possibles d'une valeur, pour chaque stratégie demandée."""
    jours, clo = par_jour(df)
    mm200 = clo.rolling(200, min_periods=200).mean()
    dates = list(clo.index)
    out = []
    for k in range(1, len(dates)):
        d, veille = dates[k], dates[k - 1]
        o, h, l, c = jours[d]
        prec = clo[veille]
        tendance = not np.isnan(mm200[veille]) and prec > mm200[veille]

        if "cassure_ouverture" in strategies and tendance:
            haut, bas = h[0], l[0]
            for i in range(1, 22):                       # bougies de 9:45 à 14:45
                if c[i] > haut:
                    entree = o[i + 1]
                    stop = (haut + bas) / 2
                    if entree > stop:
                        obj = entree + 2 * (entree - stop)
                        px, motif, j = sortie(o, h, l, c, i + 1, stop, obj)
                        out.append(("cassure_ouverture", symbole, d, i + 1, entree, d, px, motif,
                                    (i, -(c[i] / haut - 1))))
                    break

        if "rebond_trou" in strategies and tendance:
            trou = o[0] / prec - 1
            if trou <= -0.02 and c[1] > o[0]:
                entree, stop = o[2], min(l[0], l[1])
                if entree > stop:
                    px, motif, j = sortie(o, h, l, c, 2, stop)
                    out.append(("rebond_trou", symbole, d, 2, entree, d, px, motif, (trou,)))

        if "fin_de_seance" in strategies and c[1] / prec - 1 > 0:
            out.append(("fin_de_seance", symbole, d, 24, o[24], d, c[25], "clôture", (0,)))

        if "chute_du_jour" in strategies and tendance and k + 1 < len(dates):
            baisse = c[24] / prec - 1                     # à 15:45, sur la journée
            if baisse <= -0.03:
                lendemain = dates[k + 1]
                out.append(("chute_du_jour", symbole, d, 25, o[25], lendemain, jours[lendemain][0][25],
                            "lendemain 15:45", (baisse,)))
    return out


COLONNES = ["strategie", "symbole", "jour_entree", "bougie_entree", "prix_entree", "jour_sortie", "prix_sortie",
            "motif", "score"]
UNIVERS = {"cassure_ouverture": ACTIONS, "rebond_trou": ACTIONS, "fin_de_seance": "indices",
           "chute_du_jour": ACTIONS}
POSITIONS = {"cassure_ouverture": 5, "rebond_trou": 5, "fin_de_seance": 2, "chute_du_jour": 5}
