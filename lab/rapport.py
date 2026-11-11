"""Écrit rapport/RESULTATS.md et rapport/courbes.png."""

import datetime
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "rapport")

# Critères fixés AVANT de voir les résultats. Jugés sur la période de vérification seulement.
CRITERES = [
    ("sharpe", "Sharpe meilleur que la référence (plus de gain pour le risque pris)",
     lambda l, ref: l.get("sharpe", np.nan) > ref.get("sharpe", np.nan)),
    ("pire_baisse", "Pire baisse moins grave que -30 %",
     lambda l, ref: l.get("pire_baisse", -1) > -0.30),
    ("facteur_profit", "Facteur de profit d'au moins 1,2 (gains / pertes)",
     lambda l, ref: l.get("facteur_profit", 0) >= 1.2),
    ("nb_trades", "Au moins 100 trades (sinon c'est peut-être de la chance)",
     lambda l, ref: l.get("nb_trades", 0) >= 100),
]


def _pct(x, signe=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return ("%+.1f %%" if signe else "%.1f %%") % (100 * x)


def _num(x, fmt="%.2f"):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    return fmt % x


def verdicts(lignes):
    """Pour chaque stratégie : liste (critère, réussi) sur la période de vérification."""
    verif = [l for l in lignes if l["periode"].startswith("verification")]
    ref = next(l for l in verif if l["strategie"].startswith("REFERENCE"))
    out = {}
    for l in verif:
        if l["strategie"].startswith("REFERENCE"):
            continue
        out[l["strategie"]] = [(texte, bool(test(l, ref))) for _, texte, test in CRITERES]
    return out


def ecrire(lignes, courbes, config, lignes_stress=None, synthetique=False, dossier=DOSSIER):
    os.makedirs(dossier, exist_ok=True)
    # Graphique : courbes de capital, échelle logarithmique
    fig, ax = plt.subplots(figsize=(11, 6))
    for nom, s in courbes.items():
        ax.plot(s.index, s.values, label=nom, linewidth=2.2 if nom.startswith("REFERENCE") else 1.2,
                color="black" if nom.startswith("REFERENCE") else None)
    ax.set_yscale("log")
    ax.axvline(np.datetime64("2019-01-01"), color="grey", linestyle="--", linewidth=1)
    ax.text(np.datetime64("2019-02-01"), ax.get_ylim()[0] * 1.05, "vérification", color="grey")
    ax.set_title("Capital de 100 000 $ (échelle log), frais %.2f %% par côté" % (100 * config["frais"]))
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(dossier, "courbes.png"), dpi=110)
    plt.close(fig)

    L = []
    L.append("# Résultats du backtest")
    L.append("")
    L.append("Généré le %s. %s" % (datetime.date.today().isoformat(),
             "**DONNÉES SYNTHÉTIQUES : test du moteur uniquement, aucune conclusion possible.**"
             if synthetique else "Données : Yahoo Finance, cours journaliers ajustés."))
    L.append("")
    L.append("Règles de simulation : décision le soir à la clôture, ordre à l'ouverture du lendemain, "
             "%d positions au plus (environ 1/%d du capital chacune), frais %.2f %% par achat et par vente, "
             "actions entières, pas de levier." % (config["max_positions"], config["max_positions"],
                                                   100 * config["frais"]))
    L.append("")
    L.append("![courbes](courbes.png)")
    L.append("")
    entetes = ["Stratégie", "Rendement / an", "Pire baisse", "Sharpe", "Trades / mois",
               "Réussite", "Trade moyen", "Jours moyens", "Facteur profit", "Investi"]
    for periode in dict.fromkeys(l["periode"] for l in lignes):
        L.append("## Période : %s" % periode)
        L.append("")
        L.append("| " + " | ".join(entetes) + " |")
        L.append("|" + "---|" * len(entetes))
        for l in [x for x in lignes if x["periode"] == periode]:
            L.append("| " + " | ".join([
                l["strategie"], _pct(l.get("rendement_annuel"), True), _pct(l.get("pire_baisse")),
                _num(l.get("sharpe")), _num(l.get("trades_par_mois"), "%.1f"), _pct(l.get("taux_reussite")),
                _pct(l.get("trade_moyen"), True), _num(l.get("jours_moyens"), "%.1f"),
                _num(l.get("facteur_profit")), _pct(l.get("exposition"))]) + " |")
        L.append("")
    if lignes_stress:
        L.append("## Test de résistance : frais doublés, période de vérification")
        L.append("")
        L.append("| Stratégie | Rendement / an | Sharpe | Facteur profit |")
        L.append("|---|---|---|---|")
        for l in lignes_stress:
            if l["periode"].startswith("verification") and not l["strategie"].startswith("REFERENCE"):
                L.append("| %s | %s | %s | %s |" % (l["strategie"], _pct(l.get("rendement_annuel"), True),
                                                     _num(l.get("sharpe")), _num(l.get("facteur_profit"))))
        L.append("")
    L.append("## Verdict (critères fixés à l'avance, période de vérification)")
    L.append("")
    for nom, crit in verdicts(lignes).items():
        ok = all(r for _, r in crit)
        L.append("**%s : %s**" % (nom, "PASSE les 4 critères" if ok else "ne passe pas"))
        for texte, r in crit:
            L.append("- %s %s" % ("✅" if r else "❌", texte))
        L.append("")
    L.append("Un backtest réussi n'est pas une promesse : c'est le droit de passer à la simulation "
             "en temps réel (compte fictif), qui seule dira si la stratégie tient.")
    with open(os.path.join(dossier, "RESULTATS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return os.path.join(dossier, "RESULTATS.md")
