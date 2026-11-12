#!/usr/bin/env python3
"""Lance le labo de backtest.

    python lancer_backtest.py --telecharger     # récupère les données Yahoo puis teste tout
    python lancer_backtest.py                   # teste avec les données déjà dans data/
    python lancer_backtest.py --synthetique     # données inventées, pour vérifier que le code tourne

Le résultat est dans rapport/RESULTATS.md (tableaux + verdict) et rapport/courbes.png.
"""

import argparse
import os
import sys

import pandas as pd

from lab import donnees, moteur, rapport, stats, strategies, univers


def main(argv=None):
    ap = argparse.ArgumentParser(description="Labo de backtest swing.")
    ap.add_argument("--telecharger", action="store_true", help="télécharger les cours depuis Yahoo")
    ap.add_argument("--synthetique", action="store_true", help="données inventées (test du code)")
    ap.add_argument("--frais", type=float, default=0.001, help="frais par côté (0.001 = 0,10 %%)")
    ap.add_argument("--positions", type=int, default=5, help="positions simultanées au maximum")
    ap.add_argument("--capital", type=float, default=1000.0, help="capital de départ en dollars")
    ap.add_argument("--sl", type=float, default=3.0, help="stop de sécurité en multiples d'ATR (variante + stop)")
    ap.add_argument("--tp", type=float, default=None, help="take profit en multiples d'ATR (aucun par défaut)")
    ap.add_argument("--lot", type=int, default=0, help="0 = lots 1 et 2 ; 3 = stratégies de la recherche (lot 3)")
    a = ap.parse_args(argv)

    lot3 = a.lot == 3
    liste_strats = strategies.LOT_3 if lot3 else strategies.TOUTES
    dossier = os.path.join(rapport.DOSSIER, "lot3") if lot3 else rapport.DOSSIER
    symboles = univers.tous_les_symboles()
    if lot3:
        symboles = list(dict.fromkeys(symboles + univers.sp500_historique_symboles() + ["^VIX"]))
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

    for s, df in data.items():
        df.attrs["symbole"] = s
    if lot3:
        strategies.RotationEtf.univers_fixe = {"etf": univers.ETF}
        if "^VIX" in data:
            strategies.Panique.vix = data.pop("^VIX")["close"]
        elif a.synthetique:
            spy = data["SPY"]["close"]
            strategies.Panique.vix = 20 * (spy.rolling(20).std() / spy.rolling(20).std().mean()).bfill()
        else:
            liste_strats = [st for st in liste_strats if st.nom != "panique_vix"]
            print("Pas de données VIX : panique_vix sautée.")

    reference = moteur.acheter_et_garder(data[univers.REFERENCE], capital=a.capital, frais=a.frais, fractions=True)
    resultats, stress = {}, {}
    variantes = [("", None, None), (" + stop", a.sl, a.tp)]
    plan = [(st, st.univers_fixe or univers.UNIVERS) for st in liste_strats]
    if lot3:
        histo = {"sp500_historique": [s for s in univers.sp500_historique_symboles() if s in data]}
        plan += [(strategies.SeulementMembres(st), histo) for st in liste_strats + strategies.LOT_1
                 if st.univers_fixe is None]
    for strat, univ in plan:
        for nom_u, liste in univ.items():
            sous = {s: data[s] for s in liste if s in data}
            pos = strat.max_positions or a.positions
            for suffixe, sl, tp in variantes:
                nom = "%s / %s%s" % (strat.nom, nom_u, suffixe)
                print("Backtest %-38s sur %d valeurs..." % (nom, len(sous)))
                reglages = dict(capital=a.capital, max_positions=pos, fractions=True, sl_atr=sl, tp_atr=tp)
                resultats[nom] = moteur.backtest(sous, strat, frais=a.frais, **reglages)
                stress[nom] = moteur.backtest(sous, strat, frais=2 * a.frais, **reglages)

    if lot3:
        for f, cible in ((a.frais, resultats), (2 * a.frais, stress)):
            cible["nuit (SPY+QQQ) / indices"] = nuit({k: data[k] for k in ("SPY", "QQQ") if k in data}, a.capital, f)

    lignes = stats.tableau(resultats, reference)
    ref_stress = moteur.acheter_et_garder(data[univers.REFERENCE], capital=a.capital, frais=2 * a.frais, fractions=True)
    lignes_stress = stats.tableau(stress, ref_stress)
    courbes = {"REFERENCE SPY": reference}
    courbes.update({n: r["equity"] for n, r in resultats.items()})
    descriptions = {s.nom: s.description for s in liste_strats + (strategies.LOT_1 if lot3 else [])}
    if lot3:
        descriptions["nuit (SPY+QQQ)"] = "Achat de SPY et QQQ (moitié-moitié) à la clôture, revente à l'ouverture le lendemain, chaque jour"
    chemin = rapport.ecrire(lignes, courbes, dossier=dossier, descriptions=descriptions, config={"frais": a.frais, "max_positions": a.positions, "capital": a.capital, "sl": a.sl, "tp": a.tp},
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


def nuit(data, capital, frais):
    """Effet « nuit » : acheté à la clôture, revendu à l'ouverture du lendemain. Le moteur exécute
    à l'ouverture, donc cette stratégie est calculée à part, de façon directe."""
    r = pd.concat({s: df["open"] * (1 - frais) / (df["close"].shift(1) * (1 + frais)) - 1 for s, df in data.items()},
                  axis=1).dropna()
    r = r[r.index >= pd.Timestamp("2006-01-01")]
    eq = capital * (1 + r.mean(axis=1)).cumprod()
    lignes = []
    for s in r.columns:
        for d, x in r[s].items():
            lignes.append({"symbole": s, "entree": d, "sortie": d, "rendement": x,
                           "pnl": x * capital / len(r.columns), "jours": 1, "motif": "ouverture"})
    return {"equity": eq, "exposition": pd.Series(1.0, index=eq.index), "trades": pd.DataFrame(lignes),
            "ouvertes": []}


if __name__ == "__main__":
    sys.exit(main())
