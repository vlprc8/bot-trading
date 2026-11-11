#!/usr/bin/env python3
"""Le robot de trading, compte FICTIF Alpaca, notifications Telegram.

    python lancer_robot.py connexion   # relie Telegram (trouve ton chat) et vérifie Alpaca
    python lancer_robot.py matin       # 8h-9h : décide, envoie les ventes et les stops, PROPOSE les achats
    python lancer_robot.py validation  # toutes les 10 min jusqu'à l'ouverture : lit tes Oui / Non
    python lancer_robot.py exemple     # envoie une proposition de test (5 $), pour essayer les boutons
    python lancer_robot.py soir        # après la clôture : enregistre les exécutions, envoie le bilan
    python lancer_robot.py etat        # envoie l'état du portefeuille sur Telegram
    python lancer_robot.py stop        # urgence : annule les ordres, vend tout, met le robot en pause

Commandes Telegram (lues à chaque passage du robot) :
    /etat  /stop  /reprendre  /aide   et les boutons Oui / Non sous chaque proposition d'achat
"""

import argparse
import csv
import datetime
import json
import math
import os
import sys
import time
import traceback

import pandas as pd

from lab.univers import nom as nom_entreprise
from robot import decisions
from robot.alpaca import Alpaca
from robot.telegram import Telegram

RACINE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(RACINE, "robot", "config.json")
ETAT = os.path.join(RACINE, "robot", "etat.json")
JOURNAL = os.path.join(RACINE, "robot", "journal.csv")
STATS = os.path.join(RACINE, "robot", "statistiques.json")
COLONNES_JOURNAL = ["date_sortie", "poche", "symbole", "qte", "date_entree", "prix_entree", "prix_sortie",
                    "pnl", "rendement", "raison_sortie"]
AIDE = ("<b>Comment ça marche</b>\n"
        "• Vers 8h-9h (heure de Paris), le robot t'envoie ses propositions d'achat avec deux boutons : "
        "<b>✅ Oui</b> ou <b>❌ Non</b>. Tu as jusqu'à l'ouverture de Wall Street (15h30) pour répondre. "
        "Ta réponse est lue dans les 10 minutes et l'ordre apparaît alors dans Alpaca.\n"
        "• Les ventes et les stops de sécurité sont automatiques, pour protéger le capital.\n"
        "• Le soir vers 22h30, bilan de la journée.\n\n"
        "<b>Commandes</b> : /etat (portefeuille), /stop (tout vendre et mettre en pause), "
        "/reprendre, /aide")


# ---------------------------------------------------------------- fichiers

def lire_json(chemin, defaut):
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as fh:
            return json.load(fh)
    return defaut


def ecrire_json(chemin, donnees):
    with open(chemin, "w", encoding="utf-8") as fh:
        json.dump(donnees, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def etat_vide():
    return {"pause": False, "decalage_telegram": 0, "depart": None, "positions": [], "ordres": [],
            "propositions": [], "dernier_matin": None, "dernier_soir": None}


def ajouter_journal(ligne):
    nouveau = not os.path.exists(JOURNAL)
    with open(JOURNAL, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLONNES_JOURNAL)
        if nouveau:
            w.writeheader()
        w.writerow(ligne)


# ---------------------------------------------------------------- mise en forme

def dollars(x, signe=False):
    s = "{:,.2f}".format(abs(x)).replace(",", " ").replace(".", ",")
    return ("+" if x >= 0 else "-") + s + " $" if signe else ("-" if x < 0 else "") + s + " $"


def qte_txt(q):
    return ("%.4f" % q).rstrip("0").rstrip(".").replace(".", ",")


def titre(symbole):
    """« AAPL (Apple Inc.) »"""
    n = nom_entreprise(symbole)
    return symbole if n == symbole else "%s (%s)" % (symbole, n)


def pct(x):
    return ("%+.2f %%" % (100 * x)).replace(".", ",")


# ---------------------------------------------------------------- données

def cours(symboles, jours=500):
    import yfinance as yf
    debut = (datetime.date.today() - datetime.timedelta(days=jours)).isoformat()
    out = {}
    for s in symboles:
        try:
            df = yf.download(s, start=debut, auto_adjust=True, progress=False, threads=False)
        except Exception as exc:
            print("cours %s : %s" % (s, exc))
            continue
        if df is None or df.empty:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].dropna(subset=["close"])
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        out[s] = df.astype(float)
    return out


# ---------------------------------------------------------------- le robot

class Robot:
    def __init__(self):
        self.config = lire_json(CONFIG, {})
        self.etat = lire_json(ETAT, etat_vide())
        self.alpaca = Alpaca()
        self.tg = Telegram(chat_id=self.config.get("chat_id"))
        self.stats = lire_json(STATS, {}).get("poches", {})
        self.etat.setdefault("propositions", [])
        self.messages = []
        self.a_proposer = []     # propositions à envoyer, chacune avec ses boutons

    def dire(self, texte):
        self.messages.append(texte)

    def envoyer(self):
        if self.messages:
            print("--- message Telegram ---\n" + "\n\n".join(self.messages))
            self.tg.envoyer("\n\n".join(self.messages))
            self.messages = []
        for prop in self.a_proposer:
            print("--- proposition %s ---\n%s" % (prop["id"], prop["texte"]))
            prop["message_id"] = self.tg.envoyer(prop["texte"], boutons=[("✅ Oui", "oui:" + prop["id"]),
                                                                        ("❌ Non", "non:" + prop["id"])])
        self.a_proposer = []

    def sauver(self):
        ecrire_json(ETAT, self.etat)
        ecrire_json(CONFIG, self.config)

    # -- horloge de la bourse
    def aujourdhui_ny(self):
        h = self.alpaca.horloge()
        ts = pd.Timestamp(h["timestamp"])
        return h, ts.tz_convert("America/New_York").date()

    def sessions(self, debut, fin):
        return [pd.Timestamp(c["date"]).date() for c in self.alpaca.calendrier(debut.isoformat(), fin.isoformat())]

    # -- Telegram : commandes et réponses Oui / Non
    def lire_commandes(self, attente=0):
        chat = self.config.get("chat_id")
        evts, self.etat["decalage_telegram"] = self.tg.evenements(self.etat.get("decalage_telegram", 0), attente)
        for e in evts:
            if not chat or e["chat"] != chat:
                continue                      # on n'obéit qu'à ta conversation
            if e["type"] == "bouton":
                choix, _, pid = e["donnee"].partition(":")
                self.repondre_proposition(pid, choix == "oui", callback=e["callback"])
                continue
            texte = e["texte"]
            mot = texte.lower().strip(" !.")
            if mot in ("oui", "non"):
                attente_ = [p for p in self.etat["propositions"] if p["statut"] == "en_attente"]
                cible = next((p for p in attente_ if e.get("reponse_a") and p.get("message_id") == e["reponse_a"]),
                             attente_[0] if len(attente_) == 1 else None)
                if cible:
                    self.repondre_proposition(cible["id"], mot == "oui")
                elif attente_:
                    self.dire("Plusieurs propositions attendent : utilise les boutons sous chacune d'elles.")
                else:
                    self.dire("Aucune proposition en attente.")
                continue
            if not texte.startswith("/"):
                continue
            c = texte.split()[0].lower().split("@")[0]
            if c == "/stop":
                self.stop("commande /stop reçue sur Telegram")
            elif c == "/reprendre":
                self.etat["pause"] = False
                self.dire("▶️ Robot relancé : il reprendra ses propositions au prochain matin.")
            elif c == "/etat":
                self.dire(self.texte_etat())
            elif c in ("/aide", "/start", "/help"):
                self.dire(AIDE)
        return len(evts)

    def repondre_proposition(self, pid, accord, callback=None):
        prop = next((p for p in self.etat["propositions"] if p["id"] == pid), None)

        def info(t):
            if callback:
                self.tg.repondre_bouton(callback, t)
            else:
                self.dire(t)

        if prop is None:
            return info("Proposition introuvable (trop ancienne ?).")
        if prop["statut"] != "en_attente":
            return info("Déjà traitée : %s." % prop["statut"])
        if not accord:
            prop["statut"] = "refusee"
            self.tg.modifier(prop["message_id"], prop["texte"] + "\n\n❌ <b>Refusé</b> : aucun ordre.")
            return info("Refusé : aucun ordre.")
        ouvert = self.alpaca.horloge()["is_open"]
        if ouvert and not prop.get("test"):
            prop["statut"] = "expiree"
            self.tg.modifier(prop["message_id"], prop["texte"] + "\n\n⌛ <b>Trop tard</b> : la bourse a ouvert, "
                             "le prix n'est plus celui prévu. Aucun ordre.")
            return info("Trop tard : la bourse a déjà ouvert.")
        compte = self.alpaca.compte()
        engage = sum(o.get("montant") or 0 for o in self.etat["ordres"] if o.get("genre") == "achat")
        dispo = (float(compte["cash"]) - engage) * 0.98
        montant = round(min(prop["montant"], dispo), 2)
        if montant < 1:
            prop["statut"] = "refusee"
            self.tg.modifier(prop["message_id"], prop["texte"] + "\n\n⚠️ Plus assez de liquidités : aucun ordre.")
            return info("Plus assez de liquidités.")
        self.envoyer_ordre(prop["poche"], prop["symbole"], "buy", prop["raison"], prop["jour"], "achat",
                           montant=montant, atr=prop.get("atr"))
        prop["statut"] = "acceptee"
        quand = "exécution immédiate (la bourse est ouverte)" if ouvert else \
            "exécution à l'ouverture (15h30 heure de Paris en temps normal)"
        self.tg.modifier(prop["message_id"], prop["texte"] + "\n\n✅ <b>Accepté</b> : ordre d'achat de %s envoyé à "
                         "Alpaca, %s. Visible dans Alpaca, onglet Orders." % (dollars(montant), quand))
        info("✅ Ordre envoyé à Alpaca")

    def expirer_propositions(self, jour, ouvert):
        for p in self.etat["propositions"]:
            if p["statut"] != "en_attente":
                continue
            vieille = p["jour"] < str(jour)
            if vieille or (ouvert and not p.get("test")):
                p["statut"] = "expiree"
                self.tg.modifier(p["message_id"], p["texte"] + "\n\n⌛ <b>Expirée</b> : pas de réponse avant "
                                 "l'ouverture, aucun ordre.")
        # on garde 30 jours d'historique des propositions
        limite = str(jour - datetime.timedelta(days=30))
        self.etat["propositions"] = [p for p in self.etat["propositions"] if p["jour"] >= limite]

    def proposer(self, poche, symbole, montant, prix, raison, atr, jour, test=False, stats_de=None, sortie=None):
        n = len([p for p in self.etat["propositions"] if p["jour"] == str(jour)]) + 1
        pid = "%s-%d" % (jour.strftime("%m%d"), n)
        texte = self.texte_achat(poche, symbole, montant, prix, atr, stats_de=stats_de, sortie=sortie)
        texte += "\n\n<b>Je passe cet achat ?</b> Réponds avant l'ouverture (15h30)." if not test else \
            "\n\n<b>C'est un TEST</b> : appuie sur Oui pour voir l'ordre arriver dans Alpaca."
        prop = {"id": pid, "jour": str(jour), "poche": poche["nom"], "symbole": symbole, "montant": montant,
                "prix": prix, "atr": atr, "raison": raison, "statut": "en_attente", "texte": texte,
                "message_id": None, "test": test}
        self.etat["propositions"].append(prop)
        self.a_proposer.append(prop)
        return prop

    # -- exécutions : on regarde ce que sont devenus les ordres envoyés
    def reconcilier(self):
        restants = []
        for o in self.etat.get("ordres", []):
            d = self.alpaca.ordre(o["id"])
            statut, rempli = d.get("status"), float(d.get("filled_qty") or 0)
            final = statut in ("filled", "canceled", "expired", "rejected", "done_for_day", "replaced")
            if not final:
                restants.append(o)
                continue
            genre = o.get("genre", "achat" if o["cote"] == "buy" else "vente")
            if rempli > 0:
                prix = float(d["filled_avg_price"])
                quand = str(pd.Timestamp(d["filled_at"]).tz_convert("America/New_York").date())
                if o["cote"] == "buy":
                    poche = self.poche(o["poche"])
                    stop = decisions.stop_securite(prix, o.get("atr"), poche or {}, self.config)
                    self.etat["positions"].append({"poche": o["poche"], "symbole": o["symbole"], "qte": rempli,
                                                   "date_entree": quand, "prix_entree": prix, "stop": stop})
                    ligne = "✅ <b>Achat exécuté</b> [%s] %s %s à %s (%s)" % (
                        o["poche"], qte_txt(rempli), titre(o["symbole"]), dollars(prix), dollars(rempli * prix))
                    if stop:
                        ligne += "\n   🛑 Stop de sécurité %s (%s, soit %s au pire au prix du stop)" % (
                            dollars(stop), pct(stop / prix - 1), dollars((stop - prix) * rempli, True))
                    self.dire(ligne)
                else:
                    raison = "stop de sécurité touché" if genre == "stop" else o.get("raison", "")
                    self.enregistrer_vente(o, rempli, prix, quand, raison)
            if statut != "filled" and genre != "stop":   # un stop non déclenché expire chaque soir : normal
                self.dire("⚠️ Ordre %s [%s] %s : %s (exécuté %s)" % (
                    "d'achat" if o["cote"] == "buy" else "de vente", o["poche"], o["symbole"], statut,
                    qte_txt(rempli)))
        self.etat["ordres"] = restants

    def poche(self, nom):
        return next((p for p in self.config["poches"] if p["nom"] == nom), None)

    def enregistrer_vente(self, o, qte, prix, quand, raison):
        pos = next((p for p in self.etat["positions"]
                    if p["poche"] == o["poche"] and p["symbole"] == o["symbole"]), None)
        if pos is None:
            return
        pnl = (prix - pos["prix_entree"]) * qte
        r = prix / pos["prix_entree"] - 1
        ajouter_journal({"date_sortie": quand, "poche": o["poche"], "symbole": o["symbole"], "qte": round(qte, 6),
                         "date_entree": pos["date_entree"], "prix_entree": round(pos["prix_entree"], 4),
                         "prix_sortie": round(prix, 4), "pnl": round(pnl, 2), "rendement": round(r, 5),
                         "raison_sortie": raison})
        pos["qte"] -= qte
        if pos["qte"] <= 1e-6:
            self.etat["positions"].remove(pos)
        self.dire("%s <b>Vente exécutée</b> [%s] %s %s à %s : %s (%s), %s" % (
            "🟢" if pnl >= 0 else "🔴", o["poche"], qte_txt(qte), titre(o["symbole"]), dollars(prix),
            dollars(pnl, True), pct(r), raison))

    def envoyer_ordre(self, poche, symbole, cote, raison, jour, genre, qte=None, montant=None, stop=None, atr=None):
        ref = "%s-%s-%s-%s" % (jour, poche, symbole, genre)
        d = self.alpaca.passer_ordre(symbole, cote, ref, qte=qte, montant=montant, stop=stop)
        self.etat["ordres"].append({"id": d["id"], "poche": poche, "symbole": symbole, "cote": cote,
                                    "genre": genre, "qte": qte, "montant": montant, "atr": atr,
                                    "raison": raison, "date": str(jour)})

    # -- garde-fous
    def verifier_perte_totale(self, equity):
        dep = self.etat.get("depart")
        limite = self.config["garde_fous"]["perte_max_totale_pct"] / 100.0
        if dep and equity < dep["equity"] * (1 - limite):
            self.stop("perte totale au-delà de %d %% depuis le départ" % (100 * limite))
            return False
        return True

    def stop(self, pourquoi):
        try:
            self.alpaca.annuler_tout()
        except Exception as exc:
            print("annulation : %s" % exc)
        jour = datetime.date.today().isoformat()
        for p in list(self.etat["positions"]):
            if any(o["poche"] == p["poche"] and o["symbole"] == p["symbole"] and o.get("genre") == "vente"
                   for o in self.etat["ordres"]):
                continue
            self.envoyer_ordre(p["poche"], p["symbole"], "sell", "arrêt : " + pourquoi, jour, "arret", qte=p["qte"])
        self.etat["pause"] = True
        self.dire("🛑 <b>Robot en pause</b> : %s. Ordres en attente annulés, ventes de toutes les positions "
                  "envoyées (exécution à la prochaine ouverture si la bourse est fermée). /reprendre pour relancer."
                  % pourquoi)

    def texte_achat(self, poche, symbole, montant, prix, atr, stats_de=None, sortie=None):
        strat = decisions.STRATEGIES[poche["strategie"]]
        lignes = ["🟢 [%s] <b>Acheter %s de %s</b> (≈ %s action à ~%s)" % (
            poche["nom"], dollars(montant), titre(symbole), qte_txt(montant / prix), dollars(prix))]
        stop = decisions.stop_securite(prix, atr, poche, self.config)
        if stop:
            lignes.append("   🛑 Stop de sécurité ~%s : %s, soit %s au pire au prix du stop" % (
                dollars(stop), pct(stop / prix - 1), dollars(montant * (stop / prix - 1), True)))
        lignes.append("   🚪 Sortie prévue : %s" % (sortie or strat.sortie_texte))
        st = self.stats.get(stats_de or poche["nom"])
        if st and st.get("trades"):
            lignes.append("   📊 Historique 2019-2026 (%d trades) : %s gagnants ; quand ça gagne %s (≈ %s), "
                          "quand ça perd %s (≈ %s) ; durée moyenne %s jours" % (
                              st["trades"], ("%.0f %%" % (100 * st["gagnants"])),
                              pct(st["gain_moyen"]), dollars(montant * st["gain_moyen"], True),
                              pct(st["perte_moyenne"]), dollars(montant * st["perte_moyenne"], True),
                              str(st["jours_moyens"]).replace(".", ",")))
        return "\n".join(lignes)

    # -- les passages
    def matin(self, force=False):
        horloge, jour = self.aujourdhui_ny()
        self.reconcilier()
        self.lire_commandes()
        self.expirer_propositions(jour, horloge["is_open"])
        sessions = self.sessions(jour - datetime.timedelta(days=10), jour + datetime.timedelta(days=40))
        if jour not in sessions:
            print("Bourse fermée aujourd'hui (%s)." % jour)
            return
        if self.etat.get("dernier_matin") == str(jour) and not force:
            print("Déjà passé ce matin.")
            return
        if horloge["is_open"] and not force:
            self.dire("⏰ Passage du matin trop tard : la bourse est déjà ouverte. Aucun ordre aujourd'hui "
                      "(les ordres doivent partir à l'ouverture, comme dans le backtest).")
            return
        compte = self.alpaca.compte()
        equity = float(compte["equity"])
        plafond = self.config["garde_fous"].get("compte_max_usd")
        if plafond and equity > plafond:
            self.dire("⚠️ Le compte Alpaca relié a %s, au-dessus de %s : ce n'est pas le compte à 1 000 $. "
                      "Aucun ordre. Remets les clés du compte à 1 000 $ dans les secrets GitHub."
                      % (dollars(equity), dollars(plafond)))
            return
        if not self.etat.get("depart"):
            spy = cours(["SPY"], 15).get("SPY")
            self.etat["depart"] = {"date": str(jour), "equity": equity,
                                   "spy": float(spy["close"].iloc[-1]) if spy is not None else None}
        self.etat["dernier_matin"] = str(jour)
        if self.etat.get("pause"):
            self.dire("⏸️ Robot en pause : aucun nouvel ordre aujourd'hui. /reprendre pour relancer.")
            return
        if not self.verifier_perte_totale(equity):
            return
        veille = max(s for s in sessions if s < jour)
        mois = [s for s in sessions if s.year == jour.year and s.month == jour.month]
        tous = sorted({s for p in self.config["poches"] for s in decisions.symboles_poche(p)})
        data = cours(tous)
        data = {s: df[df.index <= pd.Timestamp(veille)] for s, df in data.items()}
        manquants = [s for s in tous if s not in data or data[s].empty or data[s].index[-1] != pd.Timestamp(veille)]
        ordre_max = self.config["garde_fous"]["ordre_max_usd"]
        ventes_txt, achats_prevus, vendus = [], [], set()
        # les positions de test (bouton « exemple ») sont revendues le lendemain matin
        for p in [p for p in self.etat["positions"] if p["poche"] == "test"]:
            self.envoyer_ordre("test", p["symbole"], "sell", "fin du test", jour, "vente", qte=p["qte"])
            vendus.add(("test", p["symbole"]))
            ventes_txt.append("🔵 [test] <b>Vendre %s %s</b> : fin du test" % (qte_txt(p["qte"]), titre(p["symbole"])))
        en_cours = {p["symbole"] for p in self.etat["propositions"] if p["statut"] in ("en_attente", "acceptee")
                    and p["jour"] == str(jour)}
        for poche in self.config["poches"]:
            mes = [p for p in self.etat["positions"] if p["poche"] == poche["nom"]]
            ailleurs = {p["symbole"] for p in self.etat["positions"] if p["poche"] != poche["nom"]}
            ailleurs |= {a[1] for a in achats_prevus} | en_cours
            ailleurs |= {o["symbole"] for o in self.etat["ordres"] if o["cote"] == "buy"}
            ventes, achats = decisions.decider(poche, data, mes, ailleurs, jour, veille, mois, equity, ordre_max)
            for p, raison in ventes:
                self.envoyer_ordre(poche["nom"], p["symbole"], "sell", raison, jour, "vente", qte=p["qte"])
                vendus.add((poche["nom"], p["symbole"]))
                ventes_txt.append("🔵 [%s] <b>Vendre %s %s</b> : %s" % (poche["nom"], qte_txt(p["qte"]), titre(p["symbole"]), raison))
            for s_, montant, prix, raison, atr in achats:
                achats_prevus.append((poche, s_, montant, prix, raison, atr))
        cash = float(compte["cash"]) * 0.98
        for poche, s_, montant, prix, raison, atr in achats_prevus:
            montant = round(min(montant, cash), 2)
            if montant < 1:
                continue
            self.proposer(poche, s_, montant, prix, raison, atr, jour)
            cash -= montant
        # stops de sécurité du jour pour les positions gardées (un ordre stop ne vaut que pour la journée)
        stops_txt = []
        for p in self.etat["positions"]:
            if (p["poche"], p["symbole"]) in vendus or not p.get("stop"):
                continue
            try:
                self.envoyer_ordre(p["poche"], p["symbole"], "sell", "stop de sécurité", jour, "stop",
                                   qte=p["qte"], stop=p["stop"])
                stops_txt.append("%s %s" % (p["symbole"], dollars(p["stop"])))
            except Exception as exc:
                self.dire("⚠️ Stop de sécurité non posé sur %s : %s" % (p["symbole"], str(exc)[:200]))
        lignes = ["☀️ <b>Le point du %s</b>" % jour.strftime("%d/%m"), "Capital : %s" % dollars(equity)]
        if ventes_txt:
            lignes.append("<b>Ventes automatiques</b> (exécution à l'ouverture, 15h30) :\n" + "\n".join(ventes_txt))
        if self.a_proposer:
            lignes.append("👇 <b>%d proposition(s) d'achat</b> dans les messages suivants : réponds ✅ Oui ou "
                          "❌ Non avant 15h30." % len(self.a_proposer))
        if not ventes_txt and not self.a_proposer:
            lignes.append("Aucun signal aujourd'hui : on ne touche à rien.")
        if stops_txt:
            lignes.append("🛑 Stops de sécurité en place : " + ", ".join(stops_txt))
        if manquants:
            lignes.append("<i>Cours manquants ou pas à jour, ignorés : %s</i>" % ", ".join(manquants))
        self.dire("\n\n".join(lignes))

    def validation(self, attente=0):
        """Lit tes Oui / Non. Avec `attente`, écoute Telegram pendant ce nombre de secondes."""
        horloge, jour = self.aujourdhui_ny()
        self.reconcilier()
        fin = time.time() + attente
        while True:
            reste = int(fin - time.time())
            self.lire_commandes(attente=max(0, min(25, reste)))
            if reste <= 0 or not any(p["statut"] == "en_attente" for p in self.etat["propositions"]):
                break
        self.expirer_propositions(jour, self.alpaca.horloge()["is_open"])

    def exemple(self):
        """Une proposition de TEST à 5 $, pour essayer les boutons et voir l'ordre arriver dans Alpaca."""
        _, jour = self.aujourdhui_ny()
        df = cours(["AAPL"], 60).get("AAPL")
        prix = float(df["close"].iloc[-1])
        atr = decisions._atr(df)
        poche = {"nom": "test", "strategie": "cassure_courte", "stop_securite": True}
        self.dire("🧪 Voici à quoi ressemble une proposition d'achat. Celle-ci est un <b>test à 5 $</b> : "
                  "si tu réponds Oui, l'ordre part sur ton compte fictif et tu le verras dans Alpaca "
                  "(onglet Orders). Le robot le revendra demain matin.\n\n"
                  "Pour un vrai trade, le montant serait d'environ 66 $ (1 000 $ ÷ 3 poches ÷ 5 positions).")
        self.proposer(poche, "AAPL", 5.0, prix, "test des boutons Oui / Non", atr, jour, test=True,
                      stats_de="cassure", sortie="revendu automatiquement demain matin (c'est un test)")

    def soir(self):
        horloge, jour = self.aujourdhui_ny()
        self.reconcilier()
        self.lire_commandes()
        self.expirer_propositions(jour, True)
        if self.etat.get("dernier_soir") == str(jour):
            return
        sessions = self.sessions(jour - datetime.timedelta(days=5), jour)
        if jour not in sessions:
            return
        self.etat["dernier_soir"] = str(jour)
        self.dire(self.texte_etat(titre="🌙 <b>Bilan du %s</b>" % jour.strftime("%d/%m")))

    def texte_etat(self, titre="📊 <b>État du portefeuille</b>"):
        c = self.alpaca.compte()
        eq, veille = float(c["equity"]), float(c.get("last_equity") or c["equity"])
        lignes = [titre, "Capital : <b>%s</b> (%s aujourd'hui)" % (dollars(eq), pct(eq / veille - 1))]
        dep = self.etat.get("depart")
        if dep:
            ligne = "Depuis le départ (%s) : %s" % (dep["date"], pct(eq / dep["equity"] - 1))
            spy = cours(["SPY"], 15).get("SPY")
            if spy is not None and dep.get("spy"):
                ligne += " | S&amp;P 500 : %s" % pct(float(spy["close"].iloc[-1]) / dep["spy"] - 1)
            lignes.append(ligne)
        pos = {p["symbol"].replace(".", "-"): p for p in self.alpaca.positions()}
        if self.etat["positions"]:
            lignes.append("Positions :")
            for p in self.etat["positions"]:
                a = pos.get(p["symbole"])
                prix = float(a["current_price"]) if a else p["prix_entree"]
                lignes.append("• [%s] %s %s, entrée %s le %s, %s (%s)%s" % (
                    p["poche"], qte_txt(p["qte"]), titre(p["symbole"]), dollars(p["prix_entree"]), p["date_entree"],
                    pct(prix / p["prix_entree"] - 1), dollars((prix - p["prix_entree"]) * p["qte"], True),
                    (", stop %s" % dollars(p["stop"])) if p.get("stop") else ""))
        else:
            lignes.append("Aucune position.")
        if os.path.exists(JOURNAL):
            j = pd.read_csv(JOURNAL)
            if len(j):
                lignes.append("Trades clôturés : %d, %d gagnants, total %s" % (
                    len(j), int((j["pnl"] > 0).sum()), dollars(float(j["pnl"].sum()), True)))
        if self.etat.get("pause"):
            lignes.append("⏸️ En pause.")
        return "\n".join(lignes)

    def connexion(self):
        import time
        moi = self.tg.moi()
        print("Bot Telegram : @%s (%s). J'attends un message pendant 4 minutes..." % (
            moi.get("username"), moi.get("first_name")))
        msgs, dec, fin = [], 0, time.time() + 240
        while not msgs and time.time() < fin:
            msgs, dec = self.tg.nouveaux_messages(dec, attente=25)
        if not msgs:
            raise SystemExit("Aucun message reçu par @%s : écris-lui « salut » sur Telegram, puis relance."
                             % moi.get("username"))
        self.config["chat_id"] = msgs[-1][0]
        self.etat["decalage_telegram"] = dec
        self.tg.chat_id = self.config["chat_id"]
        c = self.alpaca.compte()
        nom = moi.get("first_name", "bot")
        self.dire("✅ <b>%s est connecté !</b>\nCompte Alpaca FICTIF %s : %s de capital, statut %s.\n\n"
                  "Le robot passera chaque jour de bourse vers 8h-9h (propositions), toutes les 10 minutes "
                  "jusqu'à 15h30 (tes réponses) et vers 22h30 (bilan), heure de Paris."
                  % (nom, c.get("account_number", "?"), dollars(float(c["equity"])), c.get("status")))
        self.dire(AIDE)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Robot de trading (compte fictif).")
    ap.add_argument("mode", choices=["connexion", "matin", "validation", "exemple", "soir", "etat", "stop"])
    ap.add_argument("--force", action="store_true", help="matin : passer même si déjà fait ou marché ouvert")
    ap.add_argument("--attente", type=int, default=0, help="validation : écouter Telegram N secondes")
    a = ap.parse_args(argv)
    robot = Robot()
    try:
        if a.mode == "connexion":
            robot.connexion()
        elif a.mode == "matin":
            robot.matin(force=a.force)
        elif a.mode == "validation":
            robot.validation(attente=a.attente)
        elif a.mode == "exemple":
            robot.exemple()
        elif a.mode == "soir":
            robot.soir()
        elif a.mode == "etat":
            robot.reconcilier()
            robot.dire(robot.texte_etat())
        elif a.mode == "stop":
            robot.reconcilier()
            robot.stop("arrêt d'urgence lancé depuis GitHub")
    except Exception as exc:
        traceback.print_exc()
        robot.dire("❗ <b>Erreur du robot</b> (%s) : %s" % (a.mode, str(exc)[:300]))
        try:
            robot.envoyer()
        finally:
            robot.sauver()
        return 1
    try:
        robot.envoyer()      # d'abord envoyer : on garde l'identifiant des messages à boutons
    finally:
        robot.sauver()
    return 0


if __name__ == "__main__":
    sys.exit(main())
