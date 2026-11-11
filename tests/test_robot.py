import datetime
import os
import sys
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lab import donnees, moteur, strategies  # noqa: E402
from robot import decisions  # noqa: E402


def simuler_en_direct(data, poche, debut="2006-01-01", fin="2009-12-31"):
    """Rejoue le robot jour par jour comme en vrai : le matin de D, décision sur les cours jusqu'à D-1,
    exécution à l'ouverture de D. Retourne les trades fermés (symbole, entrée, sortie)."""
    sessions = sorted(set().union(*[df.index for df in data.values()]))
    sessions = [d for d in sessions if d <= pd.Timestamp(fin)]
    positions, trades = [], []
    for k in range(1, len(sessions)):
        jour, veille = sessions[k], sessions[k - 1]
        if veille < pd.Timestamp(debut):
            continue
        mois = [d for d in sessions if d.to_period("M") == jour.to_period("M")]
        ventes, achats = decisions.decider(poche, data, positions, set(), jour, veille, mois, 1e9, 1e12)
        for p, _ in ventes:
            positions.remove(p)
            trades.append((p["symbole"], p["date_entree"], jour))
        for s, qte, prix, _ in achats:
            positions.append({"poche": poche["nom"], "symbole": s, "qte": qte, "date_entree": jour,
                              "prix_entree": prix})
    return trades


class MemeRegleQueLeLabo(unittest.TestCase):
    """Le robot doit prendre EXACTEMENT les mêmes trades que le backtest : sinon le backtest ne prouve rien."""

    def comparer(self, nom_strat, symboles, max_positions):
        data = donnees.synthetiques(symboles, debut="2005-01-03", fin="2009-12-31")
        poche = {"nom": "test", "strategie": nom_strat, "symboles": symboles, "part": 1.0,
                 "max_positions": max_positions}
        live = simuler_en_direct(data, poche)
        strat = decisions.STRATEGIES[nom_strat]
        bt = moteur.backtest(data, strat, capital=1e9, max_positions=max_positions, frais=0.0)["trades"]
        bt = [(r.symbole, r.entree, r.sortie) for r in bt.itertuples() if r.sortie <= pd.Timestamp("2009-12-31")]
        self.assertGreater(len(bt), 20)
        # deux ventes le même jour peuvent être notées dans un ordre différent : on trie
        cle = lambda t: (t[2], t[0], t[1])  # noqa: E731
        self.assertEqual(sorted(live, key=cle)[:len(bt)], sorted(bt, key=cle))

    def test_cassure_courte(self):
        self.comparer("cassure_courte", ["A", "B", "C", "D"], 2)

    def test_rebond_court(self):
        self.comparer("rebond_court", ["A", "B", "C", "D"], 2)

    def test_tournant_du_mois(self):
        self.comparer("tournant_du_mois", ["SPY"], 1)


class Garde(unittest.TestCase):
    def test_cours_pas_a_jour_ignores_et_valeur_tenue_ailleurs_exclue(self):
        data = donnees.synthetiques(["A", "B"], debut="2005-01-03", fin="2008-12-31")
        poche = {"nom": "t", "strategie": "rebond_court", "symboles": ["A", "B"], "part": 1.0, "max_positions": 5}
        strat = strategies.RebondCourt()
        jours = [d for d in data["A"].index if bool(strat.signaux(data["A"])[0].loc[d])]
        veille = jours[-1]
        jour = data["A"].index[data["A"].index.get_loc(veille) + 1]
        _, achats = decisions.decider(poche, data, [], set(), jour, veille, [], 1e6, 1e6)
        self.assertIn("A", [a[0] for a in achats])
        _, achats = decisions.decider(poche, data, [], {"A"}, jour, veille, [], 1e6, 1e6)
        self.assertNotIn("A", [a[0] for a in achats])
        vieux = dict(data, A=data["A"][data["A"].index < veille])
        _, achats = decisions.decider(poche, vieux, [], set(), jour, veille, [], 1e6, 1e6)
        self.assertNotIn("A", [a[0] for a in achats])

    def test_jamais_un_ordre_au_dessus_du_plafond(self):
        data = donnees.synthetiques(["SPY"], debut="2005-01-03", fin="2008-12-31")
        poche = {"nom": "t", "strategie": "tournant_du_mois", "symboles": ["SPY"], "part": 1.0, "max_positions": 1}
        sessions = list(data["SPY"].index)
        mois = [d for d in sessions if d.to_period("M") == pd.Period("2008-06")]
        _, achats = decisions.decider(poche, data, [], set(), mois[-2], mois[-3], mois, 1e6, 15000)
        s, qte, prix, _ = achats[0]
        self.assertLessEqual(qte * prix, 15000)

    def test_l_url_du_compte_reel_est_refusee(self):
        from robot.alpaca import Alpaca, AlpacaErreur
        with self.assertRaises(AlpacaErreur):
            Alpaca("k", "s", url="https://api.alpaca.markets/v2")


if __name__ == "__main__":
    unittest.main()
