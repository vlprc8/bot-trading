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

UNIVERS = {"etf": ETF, "actions": GRANDES_ACTIONS, "sp500": SP500}


def tous_les_symboles():
    vus, out = set(), []
    for s in [REFERENCE] + ETF + GRANDES_ACTIONS + SP500:
        if s not in vus:
            vus.add(s)
            out.append(s)
    return out
