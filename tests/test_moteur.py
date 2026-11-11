import os
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lab import donnees, moteur, stats, strategies  # noqa: E402


class SignalFixe(strategies.Strategie):
    """Achète le jour `jour_achat` (décision à la clôture), ne sort qu'au bout de jours_max."""
    nom = "fixe"

    def __init__(self, jour_achat, jours_max=3):
        self.jour_achat, self.jours_max = jour_achat, jours_max

    def signaux(self, df):
        e = pd.Series(False, index=df.index)
        e.iloc[self.jour_achat] = True
        return e, pd.Series(0.0, index=df.index), pd.Series(False, index=df.index)


def serie(prix_ouv, prix_clo, debut="2010-01-04"):
    idx = pd.bdate_range(debut, periods=len(prix_ouv))
    return pd.DataFrame({"open": prix_ouv, "high": np.maximum(prix_ouv, prix_clo),
                         "low": np.minimum(prix_ouv, prix_clo), "close": prix_clo,
                         "volume": 1e6}, index=idx)


class Execution(unittest.TestCase):
    def test_achat_a_l_ouverture_du_lendemain_et_sortie_au_bout_de_3_jours(self):
        ouv = [10, 11, 12, 13, 14, 15, 16, 17]
        clo = [10.5, 11.5, 12.5, 13.5, 14.5, 15.5, 16.5, 17.5]
        df = serie(ouv, clo)
        res = moteur.backtest({"A": df}, SignalFixe(1), capital=1000, max_positions=1, frais=0.0,
                              debut="2000-01-01")
        t = res["trades"].iloc[0]
        self.assertEqual(t["entree"], df.index[2])     # signal le jour 1 -> achat à l'ouverture du jour 2
        self.assertEqual(t["prix_entree"], 12)
        self.assertEqual(t["sortie"], df.index[5])     # détenue 3 séances (2, 3, 4) -> vente ouverture jour 5
        self.assertEqual(t["prix_sortie"], 15)
        self.assertEqual(t["jours"], 3)
        self.assertEqual(t["qte"], 83)                 # floor(1000 / 12)
        self.assertAlmostEqual(res["equity"].iloc[-1], 1000 - 83 * 12 + 83 * 15)

    def test_les_frais_sont_payes_a_l_achat_et_a_la_vente(self):
        df = serie([10] * 8, [10] * 8)
        res = moteur.backtest({"A": df}, SignalFixe(0), capital=10000, max_positions=1, frais=0.001,
                              debut="2000-01-01")
        t = res["trades"].iloc[0]
        self.assertEqual(t["qte"], 999)                # floor(10000 / 1.001 / 10)
        cout, recette = 999 * 10 * 1.001, 999 * 10 * 0.999
        self.assertAlmostEqual(t["rendement"], recette / cout - 1)
        self.assertAlmostEqual(res["equity"].iloc[-1], 10000 - cout + recette)

    def test_jamais_plus_de_positions_que_permis_ni_de_cash_negatif(self):
        data = donnees.synthetiques(["A", "B", "C", "D", "E", "F", "G"], debut="2005-01-03", fin="2012-12-31")
        res = moteur.backtest(data, strategies.RebondCourt(), max_positions=3, frais=0.001)
        t = res["trades"]
        self.assertGreater(len(t), 50)
        for d in pd.bdate_range("2006-06-01", "2012-12-01", freq="17B"):
            ouvertes = ((t["entree"] <= d) & (t["sortie"] > d)).sum()
            self.assertLessEqual(ouvertes, 3, d)
        self.assertTrue((res["exposition"] <= 1.0000001).all())
        self.assertTrue((res["exposition"] >= 0).all())


class PasDeFutur(unittest.TestCase):
    def test_couper_les_donnees_ne_change_rien_au_passe(self):
        data = donnees.synthetiques(["A", "B", "C", "D"], debut="2005-01-03", fin="2014-12-31")
        coupe = pd.Timestamp("2011-06-30")  # fin de mois : le tournant du mois lit le calendrier
        court = {s: df[df.index <= coupe] for s, df in data.items()}
        for strat in strategies.TOUTES:
            plein = moteur.backtest(data, strat)["equity"]
            tronque = moteur.backtest(court, strat)["equity"]
            pd.testing.assert_series_equal(plein[plein.index <= coupe], tronque, check_names=False)

    def test_modifier_le_futur_ne_change_pas_les_signaux_passes(self):
        df = donnees.synthetiques(["A"])["A"]
        coupe = df.index[3000]
        trafique = df.copy()
        trafique.loc[trafique.index > coupe, ["open", "high", "low", "close"]] *= 3
        for strat in strategies.TOUTES:
            a = [x[x.index <= coupe] for x in strat.signaux(df)]
            b = [x[x.index <= coupe] for x in strat.signaux(trafique)]
            for x, y in zip(a, b):
                pd.testing.assert_series_equal(x, y)


class NouvellesStrategies(unittest.TestCase):
    def test_vendredi_et_tournant_du_mois(self):
        df = serie([10.0] * 45, [10.0] * 45, debut="2026-09-01")   # 1er sept. 2026 = mardi
        v = strategies.vendredi(df)
        self.assertTrue(all(d.weekday() == 4 for d in df.index[v.values][:-1]))
        e, _, x = strategies.TournantDuMois().signaux(df)
        self.assertEqual([d.strftime("%m-%d") for d in df.index[e.values]], ["09-28", "10-28"])  # 3e avant la fin
        self.assertEqual([d.strftime("%m-%d") for d in df.index[x.values]], ["09-03", "10-05"])  # 3e séance

    def test_ibs(self):
        df = pd.DataFrame({"open": [10.0], "high": [12.0], "low": [10.0], "close": [10.5]},
                          index=pd.DatetimeIndex(["2020-01-02"]))
        self.assertAlmostEqual(strategies.ibs(df).iloc[0], 0.25)

    def test_toutes_tournent_sans_regarder_le_futur(self):
        df = donnees.synthetiques(["A"])["A"]
        coupe = df.index[3000]
        trafique = df.copy()
        trafique.loc[trafique.index > coupe, ["open", "high", "low", "close"]] *= 3
        for strat in strategies.LOT_2:
            for x, y in zip(strat.signaux(df), strat.signaux(trafique)):
                pd.testing.assert_series_equal(x[x.index <= coupe], y[y.index <= coupe])


class Indicateurs(unittest.TestCase):
    def test_rsi_aux_extremes(self):
        hausse = pd.Series(np.arange(1, 50, dtype=float))
        self.assertAlmostEqual(strategies.rsi(hausse, 2).iloc[-1], 100.0)
        baisse = pd.Series(np.arange(50, 1, -1, dtype=float))
        self.assertAlmostEqual(strategies.rsi(baisse, 2).iloc[-1], 0.0)

    def test_stats_simples(self):
        idx = pd.bdate_range("2010-01-01", periods=253)
        eq = pd.Series(np.linspace(100, 110, 253), index=idx)
        st = stats.stats_courbe(eq)
        self.assertAlmostEqual(st["rendement_annuel"], 0.10, places=6)
        self.assertAlmostEqual(st["pire_baisse"], 0.0)


if __name__ == "__main__":
    unittest.main()
