"""Labo crypto : stratégies sur cours journaliers (Yahoo), marché ouvert 7 jours sur 7.

Règles et critères écrits le 12/11/2026, AVANT tout test sur les vraies données.
Décision à la clôture (minuit UTC), exécution à l'ouverture suivante, comme pour les actions.
Frais : 0,25 % par achat et par vente (tarif « taker » d'Alpaca pour les petits comptes), test à 0,50 %.
Réglage 2017-2021, vérification 2022 à aujourd'hui. Référence : acheter du Bitcoin et le garder.

Limite connue : les cryptos testées sont celles qui existent encore et sont listées chez Alpaca aujourd'hui
(biais du survivant). Beaucoup d'autres ont disparu entre-temps. Cela rend les résultats trop beaux.
"""

import datetime
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from lab import moteur, stats  # noqa: E402
from lab.strategies import Strategie, rsi, sma  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "data_crypto")
JOURS_AN = 365
DEBUT = "2017-01-01"
PERIODES = {"tout": ("2017-01-01", None), "reglage (2017-2021)": ("2017-01-01", "2021-12-31"),
            "verification (2022-auj.)": ("2022-01-01", None)}

# Symbole Yahoo -> nom. Cryptos proposées par Alpaca.
NOMS = {"BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana", "XRP-USD": "XRP",
        "DOGE-USD": "Dogecoin", "LTC-USD": "Litecoin", "BCH-USD": "Bitcoin Cash", "LINK-USD": "Chainlink",
        "AVAX-USD": "Avalanche", "DOT-USD": "Polkadot", "AAVE-USD": "Aave"}
PANIER = list(NOMS)
MAJEURES = ["BTC-USD", "ETH-USD"]


def dimanche(df):
    return pd.Series(df.index.dayofweek == 6, index=df.index)


class Tendance50(Strategie):
    """Suivi de tendance le plus simple : être investi quand le cours est au-dessus de sa moyenne 50 jours."""
    nom = "tendance_50"
    description = "Bitcoin et Ethereum : détenir quand la clôture est au-dessus de la moyenne 50 jours, sinon rester en dollars"
    jours_max = 10 ** 6
    univers_fixe = {"majeures": MAJEURES}
    max_positions = 2

    def signaux(self, df):
        c = df["close"]
        m = sma(c, 50)
        return (c > m).fillna(False), pd.Series(0.0, index=df.index), (c < m).fillna(False)


class Cassure20(Strategie):
    """Les « tortues » : acheter le plus haut de 20 jours, revendre au plus bas de 10 jours."""
    nom = "cassure_20"
    description = "Panier : achat si clôture = plus haut des 20 derniers jours ; vente si clôture < plus bas des 10 jours précédents"
    jours_max = 10 ** 6
    univers_fixe = {"panier": PANIER}
    max_positions = 3

    def signaux(self, df):
        c = df["close"]
        entree = c >= c.rolling(20, min_periods=20).max()
        sortie = c < c.shift(1).rolling(10, min_periods=10).min()
        return entree.fillna(False), -(c / c.shift(20) - 1), sortie.fillna(False)


class MomentumSemaine(Strategie):
    """Chaque dimanche, les cryptos qui ont le plus monté sur 4 semaines, en tendance (au-dessus de la MM50).
    On garde tant que la hausse sur 4 semaines reste positive et le cours au-dessus de la MM50."""
    nom = "momentum_semaine"
    description = ("Panier, chaque dimanche : achat des 3 meilleures sur 4 semaines (au-dessus de la moyenne 50 j) ; "
                   "vente un dimanche où la hausse sur 4 semaines devient négative ou le cours passe sous la MM50")
    jours_max = 10 ** 6
    univers_fixe = {"panier": PANIER}
    max_positions = 3

    def signaux(self, df):
        c, d = df["close"], dimanche(df)
        perf, m = c / c.shift(28) - 1, sma(c, 50)
        entree = d & (perf > 0) & (c > m)
        sortie = d & ((perf <= 0) | (c < m))
        return entree.fillna(False), -perf, sortie.fillna(False)


class RebondCrypto(Strategie):
    """Acheter un repli de court terme en tendance haussière (RSI 2 jours < 10), revendre au rebond."""
    nom = "rebond_crypto"
    description = ("Bitcoin et Ethereum : achat si clôture > moyenne 200 j ET RSI(2) < 10 ; "
                   "vente si clôture > moyenne 5 j, ou après 5 jours")
    jours_max = 5
    univers_fixe = {"majeures": MAJEURES}
    max_positions = 2

    def signaux(self, df):
        c = df["close"]
        r = rsi(c, 2)
        return ((c > sma(c, 200)) & (r < 10)).fillna(False), r, (c > sma(c, 5)).fillna(False)


TOUTES = [Tendance50(), Cassure20(), MomentumSemaine(), RebondCrypto()]


def telecharger(symboles=PANIER, dossier=DOSSIER):
    import yfinance as yf
    os.makedirs(dossier, exist_ok=True)
    for s in symboles:
        try:
            df = yf.download(s, start="2014-01-01", auto_adjust=True, progress=False, threads=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna()
            df.index.name = "date"
            df.to_csv(os.path.join(dossier, s + ".csv.gz"), compression="gzip")
            print("  %-9s %d jours depuis %s" % (s, len(df), df.index[0].date()), flush=True)
        except Exception as exc:
            print("  %-9s ECHEC : %s" % (s, exc), flush=True)


def charger(symboles=PANIER, dossier=DOSSIER):
    out = {}
    for s in symboles:
        p = os.path.join(dossier, s + ".csv.gz")
        if os.path.exists(p):
            out[s] = pd.read_csv(p, index_col=0, parse_dates=True).astype(float)
    return out


def synthetiques(symboles=PANIER, graine=5):
    rng = np.random.default_rng(graine)
    dates = pd.date_range("2015-01-01", "2026-11-01", freq="D")
    out = {}
    for k, s in enumerate(symboles):
        r = rng.normal(0.0008, 0.035 + 0.005 * (k % 4), len(dates))
        c = 100 * np.exp(np.cumsum(r))
        o = np.r_[c[0], c[:-1]]
        out[s] = pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.01, "low": np.minimum(o, c) * 0.99,
                               "close": c, "volume": 1e6}, index=pd.DatetimeIndex(dates, name="date"))
    return out


def tranche(s, d, f):
    s = s[s.index >= pd.Timestamp(d)]
    return s[s.index <= pd.Timestamp(f)] if f else s


def evaluer(data, frais, capital=1000.0):
    ref = moteur.acheter_et_garder(data["BTC-USD"], capital, frais, DEBUT, fractions=True)
    res = {}
    for st in TOUTES:
        sous = {s: data[s] for s in list(st.univers_fixe.values())[0] if s in data}
        res[st.nom] = moteur.backtest(sous, st, capital, st.max_positions, frais, DEBUT, fractions=True)
    lignes = []
    for per, (d, f) in PERIODES.items():
        lignes.append(dict(periode=per, strategie="REFERENCE (acheter du Bitcoin et garder)",
                           **stats.stats_courbe(tranche(ref, d, f), JOURS_AN), exposition=1.0))
        for nom, r in res.items():
            t = r["trades"]
            t = t[(t["sortie"] >= pd.Timestamp(d)) & ((t["sortie"] <= pd.Timestamp(f)) if f else True)]
            lignes.append(dict(periode=per, strategie=nom, **stats.stats_courbe(tranche(r["equity"], d, f), JOURS_AN),
                               **stats.stats_trades(t), exposition=tranche(r["exposition"], d, f).mean()))
    return lignes, res, ref


def _p(x, s=False):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else (("%+.1f %%" if s else "%.1f %%") % (100 * x))


def _n(x, f="%.2f"):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f % x


def verdicts(lignes, stress):
    v = {l["strategie"]: l for l in lignes if l["periode"].startswith("verification")}
    r = {l["strategie"]: l for l in lignes if l["periode"].startswith("reglage")}
    st = {l["strategie"]: l for l in stress if l["periode"].startswith("verification")}
    ref = next(l for n, l in v.items() if n.startswith("REFERENCE"))
    out = {}
    for nom, l in v.items():
        if nom.startswith("REFERENCE"):
            continue
        out[nom] = [
            ("Gagnante sur la vérification (2022-auj.), frais compris", l.get("rendement_annuel", -1) > 0),
            ("Gagnante aussi sur le réglage (2017-2021)", r[nom].get("rendement_annuel", -1) > 0),
            ("Reste gagnante avec des frais doublés (0,50 % par côté)", st[nom].get("rendement_annuel", -1) > 0),
            ("Au moins 30 trades sur la vérification", l.get("nb_trades", 0) >= 30),
            ("Sharpe meilleur que garder du Bitcoin", (l.get("sharpe") or -9) > (ref.get("sharpe") or 9)),
            ("Pire baisse au moins 2 fois moins grave que celle du Bitcoin",
             (l.get("pire_baisse") or -1) > 0.5 * (ref.get("pire_baisse") or 0)),
        ]
    return out


def ecrire(lignes, stress, res, ref, frais, synthetique=False):
    dossier = os.path.join(RACINE, "rapport")
    os.makedirs(dossier, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(ref.index, ref.values / ref.iloc[0], color="black", linewidth=2, label="REFERENCE Bitcoin")
    for nom, r in res.items():
        e = r["equity"]
        ax.plot(e.index, e.values / e.iloc[0], linewidth=1.2, label=nom)
    ax.set_yscale("log")
    ax.axvline(np.datetime64("2022-01-01"), color="grey", linestyle="--", linewidth=1)
    ax.set_title("Crypto : 1 $ investi (échelle log), frais %.2f %% par côté" % (100 * frais))
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(dossier, "crypto.png"), dpi=110)
    plt.close(fig)

    L = ["# Labo crypto", "", "Généré le %s. %s" % (
        datetime.date.today().isoformat(),
        "**DONNÉES SYNTHÉTIQUES : test du code uniquement.**" if synthetique else
        "Données : Yahoo Finance, cours journaliers en dollars."), "",
        "Frais : %.2f %% par achat et par vente, test de résistance au double. Réglage 2017-2021, vérification "
        "2022 à aujourd'hui. Décision à minuit (UTC), achat ou vente à l'ouverture suivante. Critères fixés avant "
        "le test. Attention : seules les cryptos qui existent encore sont testées (biais du survivant)." % (100 * frais),
        "", "![courbes](crypto.png)", "", "## Les stratégies", ""]
    L += ["- **%s** : %s" % (s.nom, s.description) for s in TOUTES] + [""]
    ent = ["Stratégie", "Rendement / an", "Pire baisse", "Sharpe", "Trades / mois", "Réussite", "Trade moyen",
           "Jours moyens", "Temps investi"]
    for per in PERIODES:
        L += ["## Période : %s" % per, "", "| " + " | ".join(ent) + " |", "|" + "---|" * len(ent)]
        for l in [x for x in lignes if x["periode"] == per]:
            L.append("| " + " | ".join([l["strategie"], _p(l.get("rendement_annuel"), True), _p(l.get("pire_baisse")),
                                        _n(l.get("sharpe")), _n(l.get("trades_par_mois"), "%.1f"),
                                        _p(l.get("taux_reussite")), _p(l.get("trade_moyen"), True),
                                        _n(l.get("jours_moyens"), "%.1f"), _p(l.get("exposition"))]) + " |")
        L.append("")
    L += ["## Verdict (critères fixés à l'avance)", ""]
    for nom, crit in verdicts(lignes, stress).items():
        ok = all(r for _, r in crit)
        L.append("**%s : %s**" % (nom, "PASSE les %d critères" % len(crit) if ok else
                                   "%d / %d critères" % (sum(r for _, r in crit), len(crit))))
        L += ["- %s %s" % ("✅" if r else "❌", t) for t, r in crit] + [""]
    with open(os.path.join(dossier, "CRYPTO.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return os.path.join(dossier, "CRYPTO.md")
