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

UNIVERS = {"etf": ETF, "actions": GRANDES_ACTIONS}


def tous_les_symboles():
    vus, out = set(), []
    for s in [REFERENCE] + ETF + GRANDES_ACTIONS:
        if s not in vus:
            vus.add(s)
            out.append(s)
    return out
