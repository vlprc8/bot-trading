#!/usr/bin/env python3
"""Labo crypto.

    python lancer_crypto.py --telecharger    # cours Yahoo
    python lancer_crypto.py --synthetique    # données inventées, pour tester le code
"""

import argparse
import sys

from lab import crypto


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--telecharger", action="store_true")
    ap.add_argument("--synthetique", action="store_true")
    ap.add_argument("--frais", type=float, default=0.0025)
    a = ap.parse_args(argv)
    if a.synthetique:
        data = crypto.synthetiques()
    else:
        if a.telecharger:
            crypto.telecharger()
        data = crypto.charger()
    if "BTC-USD" not in data:
        print("Pas de données Bitcoin.")
        return 1
    lignes, res, ref = crypto.evaluer(data, a.frais)
    stress, _, _ = crypto.evaluer(data, 2 * a.frais)
    chemin = crypto.ecrire(lignes, stress, res, ref, a.frais, synthetique=a.synthetique)
    for l in lignes:
        if l["periode"].startswith("verification"):
            print("  %-42s rendement/an %+7.1f %%  pire baisse %6.1f %%  trades %s" % (
                l["strategie"][:42], 100 * l.get("rendement_annuel", float("nan")),
                100 * l.get("pire_baisse", float("nan")), l.get("nb_trades", "-")))
    print("Rapport : " + chemin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
