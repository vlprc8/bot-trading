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


def atr(df, n=14):
    """Average True Range : l'amplitude moyenne d'une journée, en dollars (moyenne simple)."""
    c_prec = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - c_prec).abs(), (df["low"] - c_prec).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


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
    univers_fixe = None     # sinon {nom: [symboles]} : remplace les univers par défaut
    max_positions = None    # sinon impose le nombre de positions

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


def ibs(df):
    """Internal Bar Strength : où la clôture tombe dans la bougie du jour (0 = au plus bas, 1 = au plus haut)."""
    etendue = (df["high"] - df["low"]).replace(0, np.nan)
    return ((df["close"] - df["low"]) / etendue).fillna(0.5)


def vendredi(df):
    """Dernière séance de la semaine (gère les vendredis fériés)."""
    semaine = df.index.to_series().dt.isocalendar()
    cle = semaine["year"].astype(str) + "-" + semaine["week"].astype(str)
    return pd.Series(cle.values != np.append(cle.values[1:], "fin"), index=df.index)


# ---------------------------------------------------------------- lot n°2 (enregistré le 11/11/2026,
# AVANT tout test sur les vraies données)

class ClotureBasse(Strategie):
    """IBS : une valeur en tendance haussière qui clôture tout en bas de sa journée a tendance
    à rebondir le lendemain ou le surlendemain. Documenté sur les indices US."""

    nom = "cloture_basse"
    description = ("Achat si clôture > moyenne 200 jours ET clôture dans les 15 % du bas de la journée (IBS < 0,15) ; "
                   "vente si IBS > 0,7, ou après 3 jours")
    jours_max = 3

    def signaux(self, df):
        c, x = df["close"], ibs(df)
        entree = (c > sma(c, 200)) & (x < 0.15)
        return entree.fillna(False), x, (x > 0.7).fillna(False)


class RetournementHebdo(Strategie):
    """Retournement de court terme (Jegadeesh 1990) : chaque fin de semaine, acheter les grandes
    valeurs en tendance haussière qui ont le plus baissé sur la semaine, les garder une semaine."""

    nom = "retournement_hebdo"
    description = ("Chaque vendredi : parmi les valeurs > moyenne 200 jours, acheter celles qui ont le plus "
                   "baissé sur 5 jours ; revendre le vendredi suivant")
    jours_max = 7

    def signaux(self, df):
        c, v = df["close"], vendredi(df)
        entree = v & (c > sma(c, 200)) & (c < c.shift(5))
        score = c / c.shift(5) - 1          # la plus forte baisse d'abord
        return entree.fillna(False), score, v


class MomentumHebdo(Strategie):
    """Momentum : chaque fin de semaine, garder les valeurs qui ont le plus monté sur 3 mois,
    en tendance haussière. Rotation hebdomadaire."""

    nom = "momentum_hebdo"
    description = ("Chaque vendredi : acheter les valeurs > moyenne 200 jours qui ont le plus monté sur "
                   "3 mois (63 séances) ; revendre le vendredi suivant")
    jours_max = 7

    def signaux(self, df):
        c, v = df["close"], vendredi(df)
        perf = c / c.shift(63) - 1
        entree = v & (c > sma(c, 200)) & (perf > 0)
        return entree.fillna(False), -perf, v


class TournantDuMois(Strategie):
    """Effet « tournant du mois » : les indices US montent en moyenne plus sur les derniers et
    premiers jours du mois (flux des salaires et des fonds de pension). Sur les ETF seulement."""

    nom = "tournant_du_mois"
    description = ("Achat à l'ouverture de l'avant-dernière séance du mois ; "
                   "vente à l'ouverture de la 4e séance du mois suivant")
    jours_max = 6
    univers_fixe = {"spy": ["SPY"]}
    max_positions = 1

    def signaux(self, df):
        idx = df.index.to_series()
        mois = idx.dt.to_period("M")
        reste = mois.groupby(mois).cumcount(ascending=False)    # séances restantes dans le mois
        rang = mois.groupby(mois).cumcount()                    # 0 = 1re séance du mois
        entree = pd.Series((reste == 2).values, index=df.index)  # décision le soir -> achat avant-dernière séance
        sortie = pd.Series((rang == 2).values, index=df.index)   # décision le soir de la 3e -> vente à l'ouv. de la 4e
        score = pd.Series(0.0, index=df.index)
        # NB : 'reste' s'appuie sur le calendrier de la bourse (connu à l'avance), pas sur les prix.
        return entree, score, sortie


LOT_1 = [RebondCourt(), CassureCourte()]
LOT_2 = [ClotureBasse(), RetournementHebdo(), MomentumHebdo(), TournantDuMois()]
TOUTES = LOT_1 + LOT_2
