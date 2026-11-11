"""Écrit rapport/RESULTATS.md et rapport/courbes.png."""

import datetime
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, "rapport")

# Critères fixés AVANT de voir les résultats. Les 4 premiers : lot n°1 (11/11/2026).
# Les 2 derniers ont été ajoutés le 11/11/2026 AVANT de tester le lot n°2, parce qu'on teste
# désormais beaucoup de stratégies : plus on en teste, plus une d'elles peut « passer » par chance.
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


CRITERES_EN_PLUS = [
    "A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)",
    "Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)",
]


def _par_strategie(lignes, prefixe):
    return {l["strategie"]: l for l in lignes or [] if l["periode"].startswith(prefixe)}


def verdicts(lignes, lignes_stress=None):
    """Pour chaque stratégie : liste (critère, réussi)."""
    verif = _par_strategie(lignes, "verification")
    reglage = _par_strategie(lignes, "reglage")
    stress = _par_strategie(lignes_stress, "verification")
    ref = next(l for n, l in verif.items() if n.startswith("REFERENCE"))
    out = {}
    for nom, l in verif.items():
        if nom.startswith("REFERENCE"):
            continue
        crit = [(texte, bool(test(l, ref))) for _, texte, test in CRITERES]
        crit.append((CRITERES_EN_PLUS[0], bool(reglage.get(nom, {}).get("sharpe", -9) >= 0.3)))
        if lignes_stress is not None:
            crit.append((CRITERES_EN_PLUS[1], bool(stress.get(nom, {}).get("rendement_annuel", -9) > 0)))
        out[nom] = crit
    return out


def ecrire(lignes, courbes, config, lignes_stress=None, synthetique=False, dossier=DOSSIER, descriptions=None):
    os.makedirs(dossier, exist_ok=True)
    verd = verdicts(lignes, lignes_stress)
    verif = _par_strategie(lignes, "verification")
    classement = sorted(verd, key=lambda n: (-sum(r for _, r in verd[n]), -(verif[n].get("sharpe") or -9)))
    # Graphique : la référence et les 5 meilleures, échelle logarithmique
    garder = [n for n in courbes if n.startswith("REFERENCE")] + classement[:5]
    fig, ax = plt.subplots(figsize=(11, 6))
    for nom, s in [(n, courbes[n]) for n in garder if n in courbes]:
        ax.plot(s.index, s.values, label=nom, linewidth=2.2 if nom.startswith("REFERENCE") else 1.2,
                color="black" if nom.startswith("REFERENCE") else None)
    ax.set_yscale("log")
    ax.axvline(np.datetime64("2019-01-01"), color="grey", linestyle="--", linewidth=1)
    ax.text(np.datetime64("2019-02-01"), ax.get_ylim()[0] * 1.05, "vérification", color="grey")
    ax.set_title("Capital de départ %s $ (échelle log), frais %.2f %% par côté : référence et 5 meilleures"
                 % ("{:,.0f}".format(config.get("capital", 100000)).replace(",", " "), 100 * config["frais"]))
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
    L.append("Règles de simulation : capital de départ %s $, décision le soir à la clôture, ordre à "
             "l'ouverture du lendemain, %d positions au plus (environ 1/%d du capital chacune), frais %.2f %% "
             "par achat et par vente, fractions d'actions, pas de levier." % (
                 "{:,.0f}".format(config.get("capital", 100000)).replace(",", " "), config["max_positions"],
                 config["max_positions"], 100 * config["frais"]))
    if config.get("sl"):
        L.append("")
        L.append("Variantes « + SL/TP » : stop loss à %g x ATR(14) sous le prix d'achat, take profit à %g x ATR(14) "
                 "au-dessus, actifs dès le lendemain de l'achat ; les sorties de la stratégie restent en place."
                 % (config["sl"], config["tp"]))
    L.append("")
    L.append("![courbes](courbes.png)")
    L.append("")
    L.append("## Classement (période de vérification, 2019 à aujourd'hui)")
    L.append("")
    L.append("| Stratégie | Critères réussis | Rendement / an | Pire baisse | Sharpe | Trades / mois |")
    L.append("|---|---|---|---|---|---|")
    ref = next(l for n, l in verif.items() if n.startswith("REFERENCE"))
    L.append("| REFERENCE (acheter SPY et garder) | - | %s | %s | %s | - |" % (
        _pct(ref.get("rendement_annuel"), True), _pct(ref.get("pire_baisse")), _num(ref.get("sharpe"))))
    for n in classement:
        l = verif[n]
        L.append("| %s | %d / %d | %s | %s | %s | %s |" % (
            n, sum(r for _, r in verd[n]), len(verd[n]), _pct(l.get("rendement_annuel"), True),
            _pct(l.get("pire_baisse")), _num(l.get("sharpe")), _num(l.get("trades_par_mois"), "%.1f")))
    L.append("")
    if descriptions:
        L.append("## Les règles de chaque stratégie")
        L.append("")
        for nom, d in descriptions.items():
            L.append("- **%s** : %s" % (nom, d))
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
    for nom in classement:
        crit = verd[nom]
        ok = all(r for _, r in crit)
        L.append("**%s : %s**" % (nom, "PASSE les %d critères" % len(crit) if ok else "ne passe pas"))
        for texte, r in crit:
            L.append("- %s %s" % ("✅" if r else "❌", texte))
        L.append("")
    L.append("Un backtest réussi n'est pas une promesse : c'est le droit de passer à la simulation "
             "en temps réel (compte fictif), qui seule dira si la stratégie tient.")
    with open(os.path.join(dossier, "RESULTATS.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return os.path.join(dossier, "RESULTATS.md")
