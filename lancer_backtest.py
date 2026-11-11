#!/usr/bin/env python3
"""Lance le labo de backtest.

    python lancer_backtest.py --telecharger     # récupère les données Yahoo puis teste tout
    python lancer_backtest.py                   # teste avec les données déjà dans data/
    python lancer_backtest.py --synthetique     # données inventées, pour vérifier que le code tourne

Le résultat est dans rapport/RESULTATS.md (tableaux + verdict) et rapport/courbes.png.
"""

import argparse
import sys

from lab import donnees, moteur, rapport, stats, strategies, univers


def main(argv=None):
    ap = argparse.ArgumentParser(description="Labo de backtest swing.")
    ap.add_argument("--telecharger", action="store_true", help="télécharger les cours depuis Yahoo")
    ap.add_argument("--synthetique", action="store_true", help="données inventées (test du code)")
    ap.add_argument("--frais", type=float, default=0.001, help="frais par côté (0.001 = 0,10 %%)")
    ap.add_argument("--positions", type=int, default=5, help="positions simultanées au maximum")
    ap.add_argument("--capital", type=float, default=1000.0, help="capital de départ en dollars")
    ap.add_argument("--sl", type=float, default=2.0, help="stop loss en multiples d'ATR (variante SL/TP)")
    ap.add_argument("--tp", type=float, default=3.0, help="take profit en multiples d'ATR (variante SL/TP)")
    a = ap.parse_args(argv)

    symboles = univers.tous_les_symboles()
    if a.synthetique:
        data = donnees.synthetiques(symboles)
    else:
        if a.telecharger:
            print("Téléchargement de %d valeurs depuis Yahoo Finance..." % len(symboles))
            ok, rates = donnees.telecharger(symboles)
            print("%d réussies, %d ratées %s" % (len(ok), len(rates), rates or ""))
        data = donnees.charger(symboles)
    if univers.REFERENCE not in data:
        print("Pas de données pour %s : lance d'abord avec --telecharger." % univers.REFERENCE)
        return 1

    reference = moteur.acheter_et_garder(data[univers.REFERENCE], capital=a.capital, frais=a.frais, fractions=True)
    resultats, stress = {}, {}
    variantes = [("", None, None), (" + SL/TP", a.sl, a.tp)]
    for strat in strategies.TOUTES:
        for nom_u, liste in (strat.univers_fixe or univers.UNIVERS).items():
            sous = {s: data[s] for s in liste if s in data}
            pos = strat.max_positions or a.positions
            for suffixe, sl, tp in variantes:
                nom = "%s / %s%s" % (strat.nom, nom_u, suffixe)
                print("Backtest %-38s sur %d valeurs..." % (nom, len(sous)))
                reglages = dict(capital=a.capital, max_positions=pos, fractions=True, sl_atr=sl, tp_atr=tp)
                resultats[nom] = moteur.backtest(sous, strat, frais=a.frais, **reglages)
                stress[nom] = moteur.backtest(sous, strat, frais=2 * a.frais, **reglages)

    lignes = stats.tableau(resultats, reference)
    ref_stress = moteur.acheter_et_garder(data[univers.REFERENCE], capital=a.capital, frais=2 * a.frais, fractions=True)
    lignes_stress = stats.tableau(stress, ref_stress)
    courbes = {"REFERENCE SPY": reference}
    courbes.update({n: r["equity"] for n, r in resultats.items()})
    descriptions = {s.nom: s.description for s in strategies.TOUTES}
    chemin = rapport.ecrire(lignes, courbes, descriptions=descriptions, config={"frais": a.frais, "max_positions": a.positions, "capital": a.capital, "sl": a.sl, "tp": a.tp},
                            lignes_stress=lignes_stress, synthetique=a.synthetique)

    print("\nPériode de vérification (2019 à aujourd'hui) :")
    for l in lignes:
        if l["periode"].startswith("verification"):
            print("  %-36s rendement/an %+6.1f %%  pire baisse %6.1f %%  sharpe %5.2f  trades %s" % (
                l["strategie"][:36], 100 * l.get("rendement_annuel", float("nan")),
                100 * l.get("pire_baisse", float("nan")), l.get("sharpe", float("nan")),
                l.get("nb_trades", "-")))
    print("\nRapport : %s" % chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
