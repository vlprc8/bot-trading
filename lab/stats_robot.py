#!/usr/bin/env python3
"""Calcule, pour chaque poche du robot, ce que ses trades ont donné dans le passé
(même règles, même stop de sécurité), et l'écrit dans robot/statistiques.json.
Le robot s'en sert pour dire, à chaque trade, combien on gagne ou perd en général.

    python -m lab.stats_robot
"""

import json
import os

import pandas as pd

from lab import donnees, moteur, univers
from robot import decisions

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def stats_trades(t):
    g, p = t[t["rendement"] > 0], t[t["rendement"] <= 0]
    return {"trades": int(len(t)), "gagnants": round(len(g) / len(t), 4) if len(t) else None,
            "gain_moyen": round(float(g["rendement"].mean()), 4) if len(g) else None,
            "perte_moyenne": round(float(p["rendement"].mean()), 4) if len(p) else None,
            "pire": round(float(t["rendement"].min()), 4) if len(t) else None,
            "jours_moyens": round(float(t["jours"].mean()), 1) if len(t) else None,
            "stop_touche": round(float(t["motif"].str.startswith("stop").mean()), 4) if len(t) else None}


def main():
    config = json.load(open(os.path.join(RACINE, "robot", "config.json"), encoding="utf-8"))
    data = donnees.charger(univers.tous_les_symboles())
    out = {"periode": "2019-01-01 à aujourd'hui", "stop_atr": config["stop_atr"], "poches": {}}
    for poche in config["poches"]:
        strat = decisions.STRATEGIES[poche["strategie"]]
        sous = {s: data[s] for s in decisions.symboles_poche(poche) if s in data}
        sl = config["stop_atr"] if poche.get("stop_securite", True) else None
        r = moteur.backtest(sous, strat, capital=1000, max_positions=poche["max_positions"], frais=0.001,
                            fractions=True, sl_atr=sl)
        t = r["trades"]
        out["poches"][poche["nom"]] = stats_trades(t[t["sortie"] >= pd.Timestamp("2019-01-01")])
        print(poche["nom"], out["poches"][poche["nom"]])
    with open(os.path.join(RACINE, "robot", "statistiques.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


if __name__ == "__main__":
    main()
