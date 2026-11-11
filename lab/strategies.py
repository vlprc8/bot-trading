"""Les stratégies swing testées. Chaque règle est écrite AVANT de voir les résultats.

Une stratégie fournit, pour une valeur, trois séries calculées à la CLÔTURE du jour t
(donc connues le soir du jour t, jamais avant) :
  - entree : True si on veut acheter (l'ordre part à l'OUVERTURE du jour t+1)
  - score  : pour classer les candidats quand il y en a plus que de places (petit = prioritaire)
  - sortie : True si on veut vendre (l'ordre part à l'OUVERTURE du jour t+1)
plus jours_max : on vend de toute façon après ce nombre de jours de détention.
"""

import numpy as np
import pandas as pd


def sma(s, n):
    return s.rolling(n, min_periods=n).mean()


def rsi(close, n):
    """RSI de Wilder."""
    delta = close.diff()
    hausse = delta.clip(lower=0).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    baisse = (-delta.clip(upper=0)).ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    rs = hausse / baisse.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(baisse > 0, 100.0)


class Strategie:
    nom = "?"
    description = "?"
    jours_max = 5

    def signaux(self, df):
        raise NotImplementedError


class RebondCourt(Strategie):
    """Acheter un repli de 2-3 jours dans une valeur en tendance haussière, revendre au rebond.
    Famille « RSI 2 » popularisée par Larry Connors : documentée depuis les années 2000,
    connue pour avoir perdu une partie de son efficacité depuis. On vérifie."""

    nom = "rebond_court"
    description = ("Achat si clôture > moyenne 200 jours ET RSI(2) < 10 ; "
                   "vente si clôture > moyenne 5 jours, ou après 5 jours")
    jours_max = 5

    def __init__(self, seuil_rsi=10.0):
        self.seuil_rsi = seuil_rsi

    def signaux(self, df):
        c = df["close"]
        r = rsi(c, 2)
        entree = (c > sma(c, 200)) & (r < self.seuil_rsi)
        sortie = c > sma(c, 5)
        return entree.fillna(False), r, sortie.fillna(False)


class CassureCourte(Strategie):
    """Acheter une valeur qui sort par le haut de ses 20 derniers jours, en tendance haussière,
    et la garder tant qu'elle ne casse pas le plus bas des 5 derniers jours (10 jours max)."""

    nom = "cassure_courte"
    description = ("Achat si clôture = plus haute des 20 derniers jours ET > moyenne 200 jours ; "
                   "vente si clôture < plus basse des 5 jours précédents, ou après 10 jours")
    jours_max = 10

    def signaux(self, df):
        c = df["close"]
        plus_haut_20 = c.shift(1).rolling(20, min_periods=20).max()
        plus_bas_5 = c.shift(1).rolling(5, min_periods=5).min()
        entree = (c > plus_haut_20) & (c > sma(c, 200))
        # score : la cassure la plus nette d'abord (négatif car petit = prioritaire)
        score = -(c / plus_haut_20 - 1)
        sortie = c < plus_bas_5
        return entree.fillna(False), score, sortie.fillna(False)


TOUTES = [RebondCourt(), CassureCourte()]
