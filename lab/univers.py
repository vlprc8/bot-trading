"""Les listes de valeurs testées.

ETF : aucun biais du survivant (ce sont des paniers qui existent tous depuis 2005 au moins).
GRANDES_ACTIONS : grandes valeurs US connues AUJOURD'HUI. Attention, c'est un univers
biaisé : on ne voit pas les sociétés qui ont coulé entre-temps, donc les résultats
sur cet univers sont flatteurs. On le teste quand même, mais on le juge plus sévèrement.
"""

REFERENCE = "SPY"  # acheter le S&P 500 et ne rien faire : la barre à battre

ETF = [
    "SPY",  # S&P 500
    "QQQ",  # Nasdaq 100
    "DIA",  # Dow Jones
    "IWM",  # petites capitalisations US
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",  # secteurs du S&P 500
    "EFA",  # pays développés hors US
    "EEM",  # pays émergents
    "TLT",  # obligations US 20 ans
    "GLD",  # or
]

GRANDES_ACTIONS = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "TSLA", "BRK-B", "JPM", "V",
    "JNJ", "WMT", "PG", "MA", "HD", "XOM", "CVX", "KO", "PEP", "MRK",
    "ABBV", "COST", "AVGO", "ORCL", "CSCO", "ADBE", "CRM", "NFLX", "AMD", "INTC",
    "QCOM", "TXN", "BAC", "WFC", "DIS", "MCD", "NKE", "UNH", "LLY", "PFE",
    "T", "VZ", "IBM", "CAT", "BA", "GE", "HON", "LOW", "SBUX", "GS",
]

def _sp500():
    """Les ~500 entreprises du S&P 500 (liste du 05/11/2026, github.com/datasets/s-and-p-500-companies).
    Même biais que GRANDES_ACTIONS : ce sont les membres d'AUJOURD'HUI."""
    import csv
    import os
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sp500.csv")
    with open(chemin, encoding="utf-8") as fh:
        return [r["symbole"] for r in csv.DictReader(fh)]


SP500 = _sp500()

NOMS_ETF = {
    "SPY": "fonds S&P 500 : les 500 plus grandes entreprises US",
    "IBM": "International Business Machines",
    "QQQ": "Invesco QQQ (Nasdaq 100)", "DIA": "SPDR Dow Jones Industrial Average ETF",
    "IWM": "iShares Russell 2000 (petites entreprises US)", "XLB": "ETF secteur Matériaux",
    "XLE": "ETF secteur Énergie", "XLF": "ETF secteur Finance", "XLI": "ETF secteur Industrie",
    "XLK": "ETF secteur Technologie", "XLP": "ETF secteur Consommation de base", "XLU": "ETF secteur Services publics",
    "XLV": "ETF secteur Santé", "XLY": "ETF secteur Consommation discrétionnaire",
    "EFA": "iShares MSCI EAFE (pays développés hors US)", "EEM": "iShares MSCI Emerging Markets (pays émergents)",
    "TLT": "iShares 20+ Year Treasury Bond (obligations US)", "GLD": "SPDR Gold Shares (or)",
}


def _noms():
    import csv
    import os
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sp500.csv")
    with open(chemin, encoding="utf-8") as fh:
        noms = {r["symbole"]: r["nom"] for r in csv.DictReader(fh)}
    noms.update(NOMS_ETF)
    return noms


NOMS = _noms()


def nom(symbole):
    """« AAPL » -> « Apple Inc. » (ou le symbole lui-même s'il est inconnu)."""
    return NOMS.get(symbole, symbole)

UNIVERS = {"etf": ETF, "actions": GRANDES_ACTIONS, "sp500": SP500}


def tous_les_symboles():
    vus, out = set(), []
    for s in [REFERENCE] + ETF + GRANDES_ACTIONS + SP500:
        if s not in vus:
            vus.add(s)
            out.append(s)
    return out


# --- S&P 500 « historique » : les membres de l'indice À CHAQUE DATE (github.com/fja05680/sp500) ---
# Pour retirer l'essentiel du biais du survivant : une valeur ne peut être achetée que les jours où
# elle faisait vraiment partie du S&P 500. Limites : les sociétés disparues (faillites, rachats) n'ont
# souvent plus de cours chez Yahoo, et les anciens noms de code (FB pour Meta…) ne sont pas retrouvés.
# Une partie du biais reste donc, mais beaucoup moins qu'avec la liste d'aujourd'hui.

import functools


@functools.lru_cache(maxsize=1)
def _historique():
    import os
    import pandas as pd
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sp500_historique.csv.gz")
    h = pd.read_csv(chemin, parse_dates=["date"])
    return [(d, set(t.split(","))) for d, t in zip(h["date"], h["tickers"])]


def sp500_historique_symboles():
    return sorted(set().union(*[t for _, t in _historique()]))


def membre_sp500(symbole, index):
    """Série vrai/faux : la valeur faisait-elle partie du S&P 500 ce jour-là ?"""
    import pandas as pd
    photos = _historique()
    s = pd.Series([symbole in t for _, t in photos], index=pd.DatetimeIndex([d for d, _ in photos]))
    return s.reindex(s.index.union(index)).ffill().reindex(index).fillna(False).astype(bool)
