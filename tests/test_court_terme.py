import unittest

import numpy as np
import pandas as pd

from lab.court_terme import donnees
from lab.court_terme import strategies as S


def journee(jour, prix):
    """Fabrique une journée de 26 bougies de 15 min à partir de 26 (o, h, l, c)."""
    idx = pd.date_range(pd.Timestamp(jour) + pd.Timedelta(hours=9, minutes=30), periods=26, freq="15min")
    return pd.DataFrame(prix, index=idx, columns=["open", "high", "low", "close"])


def plat(jour, p):
    return journee(jour, [(p, p + 0.1, p - 0.1, p)] * 26)


class TestCourtTerme(unittest.TestCase):
    def test_sortie_stop_avant_objectif(self):
        o = np.array([10, 10, 10.]); h = np.array([10, 12, 10.]); l = np.array([10, 8, 10.]); c = o
        self.assertEqual(S.sortie(o, h, l, c, 0, stop=9, objectif=11)[1], "stop")

    def test_sortie_cloture(self):
        o = np.array([10, 10.2, 10.1]); c = np.array([10.1, 10.2, 10.4])
        px, motif, _ = S.sortie(o, o + 0.1, o - 0.1, c, 0, stop=9, objectif=12)
        self.assertEqual((px, motif), (10.4, "clôture"))

    def _historique(self, derniere):
        jours = pd.bdate_range("2020-01-01", periods=210)
        dfs = [plat(d, 100 + 0.05 * k) for k, d in enumerate(jours[:-1])]
        dfs.append(journee(jours[-1], derniere))
        return pd.concat(dfs), jours[-1]

    def test_cassure_ouverture(self):
        barres = [(110, 111, 109, 110.5)]                   # range : 109 - 111
        barres += [(110.5, 110.9, 110.2, 110.6)] * 4
        barres += [(110.6, 112, 110.5, 111.8)]              # bougie n°5 : clôture au-dessus de 111
        barres += [(111.8, 112, 111.5, 111.9)] * 20
        df, jour = self._historique(barres)
        t = [x for x in S.trades_symbole("X", df, ["cassure_ouverture"]) if x[2] == jour]
        self.assertEqual(len(t), 1)
        self.assertEqual(t[0][3], 6)                         # achat à l'ouverture de la bougie suivante
        self.assertAlmostEqual(t[0][4], 111.8)
        self.assertEqual(t[0][7], "clôture")

    def test_pas_de_futur(self):
        """Changer ce qui se passe après l'entrée ne doit pas changer le signal ni le prix d'achat."""
        barres = [(110, 111, 109, 110.5)] + [(110.5, 110.9, 110.2, 110.6)] * 4 + [(110.6, 112, 110.5, 111.8)]
        a = barres + [(111.8, 112, 111.5, 111.9)] * 20
        b = barres + [(111.8, 125, 111.5, 124)] * 20
        ta = S.trades_symbole("X", self._historique(a)[0], ["cassure_ouverture"])[-1]
        tb = S.trades_symbole("X", self._historique(b)[0], ["cassure_ouverture"])[-1]
        self.assertEqual(ta[2:5], tb[2:5])

    def test_synthetiques_26_bougies(self):
        df = donnees.synthetiques(["SPY"], debut="2024-01-02", fin="2024-01-31")["SPY"]
        self.assertTrue((df.groupby(df.index.normalize()).size() == 26).all())


if __name__ == "__main__":
    unittest.main()
