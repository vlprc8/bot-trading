"""Assemble les trades en portefeuille, calcule les chiffres et écrit rapport/COURT_TERME.md."""

import datetime
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from lab import stats  # noqa: E402
from lab.court_terme import strategies as S  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PERIODES = {"tout": ("2016-01-01", None), "reglage (2016-2020)": ("2016-01-01", "2020-12-31"),
            "verification (2021-auj.)": ("2021-01-01", None)}


def portefeuille(trades, nb_positions, frais, calendrier):
    """Chaque jour, on garde les `nb_positions` meilleurs signaux ; chacun reçoit 1/nb_positions du capital.
    Rendement du jour = somme des trades qui se terminent ce jour-là, pondérés."""
    if trades.empty:
        return pd.Series(1.0, index=calendrier), trades
    t = trades.sort_values(["jour_entree", "score"]).groupby("jour_entree").head(nb_positions).copy()
    t["rendement"] = t["prix_sortie"] * (1 - frais) / (t["prix_entree"] * (1 + frais)) - 1
    jour = t.groupby("jour_sortie")["rendement"].sum() / nb_positions
    r = jour.reindex(calendrier).fillna(0.0)
    return (1 + r).cumprod(), t


def stats_trades(t):
    if t is None or t.empty:
        return {"nb_trades": 0}
    g, p = t[t["rendement"] > 0], t[t["rendement"] <= 0]
    ans = max(1e-9, (t["jour_sortie"].max() - t["jour_entree"].min()).days / 365.25)
    return {"nb_trades": len(t), "trades_par_mois": len(t) / (ans * 12), "taux_reussite": len(g) / len(t),
            "trade_moyen": t["rendement"].mean(),
            "facteur_profit": g["rendement"].sum() / -p["rendement"].sum() if len(p) and p["rendement"].sum() < 0 else np.nan}


def tranche(s, d, f):
    s = s[s.index >= pd.Timestamp(d)]
    return s[s.index <= pd.Timestamp(f)] if f else s


def evaluer(tous, calendrier, reference, frais):
    lignes, courbes, details = [], {}, {}
    for nom in S.UNIVERS:
        t = tous[tous["strategie"] == nom]
        eq, prises = portefeuille(t, S.POSITIONS[nom], frais, calendrier)
        courbes[nom], details[nom] = eq, prises
    for per, (d, f) in PERIODES.items():
        lignes.append(dict(periode=per, strategie="REFERENCE (acheter SPY et garder)",
                           **stats.stats_courbe(tranche(reference, d, f))))
        for nom in S.UNIVERS:
            pr = details[nom]
            pr = pr[(pr["jour_sortie"] >= pd.Timestamp(d)) & ((pr["jour_sortie"] <= pd.Timestamp(f)) if f else True)]
            lignes.append(dict(periode=per, strategie=nom, **stats.stats_courbe(tranche(courbes[nom], d, f)),
                               **stats_trades(pr)))
    return lignes, courbes, details


def _p(x, s=False):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else (("%+.1f %%" if s else "%.1f %%") % (100 * x))


def _n(x, f="%.2f"):
    return "-" if x is None or (isinstance(x, float) and np.isnan(x)) else f % x


def verdicts(lignes, lignes_stress):
    v = {l["strategie"]: l for l in lignes if l["periode"].startswith("verification")}
    r = {l["strategie"]: l for l in lignes if l["periode"].startswith("reglage")}
    st = {l["strategie"]: l for l in lignes_stress if l["periode"].startswith("verification")}
    ref = next(l for n, l in v.items() if n.startswith("REFERENCE"))
    out = {}
    for nom, l in v.items():
        if nom.startswith("REFERENCE"):
            continue
        out[nom] = [
            ("Gagnante sur la vérification (2021-2026), frais compris", l.get("rendement_annuel", -1) > 0),
            ("Gagnante aussi sur le réglage (2016-2020)", r.get(nom, {}).get("rendement_annuel", -1) > 0),
            ("Reste gagnante avec des frais doublés (0,10 % par côté)", st.get(nom, {}).get("rendement_annuel", -1) > 0),
            ("Au moins 200 trades sur la vérification", l.get("nb_trades", 0) >= 200),
            ("Facteur de profit d'au moins 1,2", (l.get("facteur_profit") or 0) >= 1.2),
            ("Sharpe meilleur que la référence", (l.get("sharpe") or -9) > (ref.get("sharpe") or 9)),
            ("Pire baisse moins grave que -30 %", (l.get("pire_baisse") or -1) > -0.30),
        ]
    return out


def ecrire(lignes, lignes_stress, courbes, reference, frais, synthetique=False):
    dossier = os.path.join(RACINE, "rapport")
    os.makedirs(dossier, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(reference.index, reference.values / reference.iloc[0], color="black", linewidth=2, label="REFERENCE SPY")
    for nom, s in courbes.items():
        ax.plot(s.index, s.values, linewidth=1.2, label=nom)
    ax.set_yscale("log")
    ax.axvline(np.datetime64("2021-01-01"), color="grey", linestyle="--", linewidth=1)
    ax.set_title("Court terme : 1 $ investi (échelle log), frais %.2f %% par côté" % (100 * frais))
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(dossier, "court_terme.png"), dpi=110)
    plt.close(fig)

    L = ["# Labo court terme (journée et 1 jour)", "",
         "Généré le %s. %s" % (datetime.date.today().isoformat(),
                               "**DONNÉES SYNTHÉTIQUES : test du code uniquement.**" if synthetique else
                               "Données : Alpaca, bougies de 15 minutes ajustées, séance normale, depuis 2016."),
         "", "Frais : %.2f %% par achat et par vente (grandes valeurs très échangées), test de résistance à 0,10 %%. "
         "Réglage 2016-2020, vérification 2021 à aujourd'hui. Critères fixés avant le test." % (100 * frais),
         "", "![courbes](court_terme.png)", ""]
    entetes = ["Stratégie", "Rendement / an", "Pire baisse", "Sharpe", "Trades / mois", "Réussite", "Trade moyen",
               "Facteur profit"]
    for per in PERIODES:
        L += ["## Période : %s" % per, "", "| " + " | ".join(entetes) + " |", "|" + "---|" * len(entetes)]
        for l in [x for x in lignes if x["periode"] == per]:
            L.append("| " + " | ".join([l["strategie"], _p(l.get("rendement_annuel"), True), _p(l.get("pire_baisse")),
                                        _n(l.get("sharpe")), _n(l.get("trades_par_mois"), "%.1f"),
                                        _p(l.get("taux_reussite")), _p(l.get("trade_moyen"), True),
                                        _n(l.get("facteur_profit"))]) + " |")
        L.append("")
    L += ["## Verdict (critères fixés à l'avance)", ""]
    for nom, crit in verdicts(lignes, lignes_stress).items():
        ok = all(r for _, r in crit)
        L.append("**%s : %s**" % (nom, "PASSE les %d critères" % len(crit) if ok else
                                   "%d / %d critères" % (sum(r for _, r in crit), len(crit))))
        L += ["- %s %s" % ("✅" if r else "❌", t) for t, r in crit] + [""]
    with open(os.path.join(dossier, "COURT_TERME.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return os.path.join(dossier, "COURT_TERME.md")
