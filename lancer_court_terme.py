#!/usr/bin/env python3
"""Labo court terme : stratégies dans la journée ou sur 1 jour, bougies de 15 minutes depuis 2016.

    python lancer_court_terme.py --telecharger    # Alpaca (secrets ALPACA_API_KEY / ALPACA_SECRET_KEY)
    python lancer_court_terme.py                  # avec les données déjà téléchargées
    python lancer_court_terme.py --synthetique    # données inventées, pour tester le code
"""

import argparse
import sys

import pandas as pd

from lab import univers
from lab.court_terme import backtest, donnees
from lab.court_terme import strategies as S


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--telecharger", action="store_true")
    ap.add_argument("--synthetique", action="store_true")
    ap.add_argument("--frais", type=float, default=0.0005, help="par côté (0.0005 = 0,05 %%)")
    a = ap.parse_args(argv)
    symboles = list(dict.fromkeys(S.INDICES + univers.GRANDES_ACTIONS))
    if a.synthetique:
        data = donnees.synthetiques(symboles)
    else:
        if a.telecharger:
            for s in symboles:
                try:
                    df = donnees.telecharger(s)
                    print("  %-6s %s bougies" % (s, 0 if df is None else len(df)), flush=True)
                except Exception as exc:
                    print("  %-6s ECHEC : %s" % (s, exc), flush=True)
        data = donnees.charger(symboles)
    if "SPY" not in data:
        print("Pas de données SPY.")
        return 1
    print("Calcul des trades sur %d valeurs..." % len(data), flush=True)
    lignes = []
    for s, df in data.items():
        strats = [n for n, u in S.UNIVERS.items() if (u == "indices") == (s in S.INDICES)]
        lignes += S.trades_symbole(s, df, strats)
    tous = pd.DataFrame(lignes, columns=S.COLONNES)
    _, clo_spy = S.par_jour(data["SPY"])
    calendrier = clo_spy.index
    reference = clo_spy / clo_spy.iloc[0]
    res, courbes, _ = backtest.evaluer(tous, calendrier, reference, a.frais)
    res_stress, _, _ = backtest.evaluer(tous, calendrier, reference, 2 * a.frais)
    chemin = backtest.ecrire(res, res_stress, courbes, reference, a.frais, synthetique=a.synthetique)
    for l in res:
        if l["periode"].startswith("verification"):
            print("  %-36s rendement/an %+6.1f %%  pire baisse %6.1f %%  trades %s" % (
                l["strategie"][:36], 100 * l.get("rendement_annuel", float("nan")),
                100 * l.get("pire_baisse", float("nan")), l.get("nb_trades", "-")))
    print("Rapport : " + chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
