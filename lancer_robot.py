#!/usr/bin/env python3
"""Le robot de trading, compte FICTIF Alpaca, notifications Telegram.

    python lancer_robot.py connexion   # relie Telegram (trouve ton chat) et vérifie Alpaca
    python lancer_robot.py matin       # avant l'ouverture : décide et envoie les ordres du jour
    python lancer_robot.py soir        # après la clôture : enregistre les exécutions, envoie le bilan
    python lancer_robot.py etat        # envoie l'état du portefeuille sur Telegram
    python lancer_robot.py stop        # urgence : annule les ordres, vend tout, met le robot en pause

Commandes Telegram (lues à chaque passage du robot, matin et soir) :
    /etat  /stop  /reprendre  /aide
"""

import argparse
import csv
import datetime
import json
import math
import os
import sys
import traceback

import pandas as pd

from robot import decisions
from robot.alpaca import Alpaca
from robot.telegram import Telegram

RACINE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(RACINE, "robot", "config.json")
ETAT = os.path.join(RACINE, "robot", "etat.json")
JOURNAL = os.path.join(RACINE, "robot", "journal.csv")
COLONNES_JOURNAL = ["date_sortie", "poche", "symbole", "qte", "date_entree", "prix_entree", "prix_sortie",
                    "pnl", "rendement", "raison_sortie"]
AIDE = ("<b>Commandes</b> (lues au prochain passage du robot, vers 13h30-14h30 et 22h30) :\n"
        "/etat : le portefeuille\n/stop : tout vendre et mettre en pause\n/reprendre : relancer\n/aide : ce message")


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
            "dernier_matin": None, "dernier_soir": None}


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
        self.messages = []

    def dire(self, texte):
        self.messages.append(texte)

    def envoyer(self):
        if self.messages:
            self.tg.envoyer("\n\n".join(self.messages))
            self.messages = []

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

    # -- Telegram : commandes reçues
    def lire_commandes(self):
        chat = self.config.get("chat_id")
        msgs, self.etat["decalage_telegram"] = self.tg.nouveaux_messages(self.etat.get("decalage_telegram", 0))
        cmds = [t.split()[0].lower().split("@")[0] for c, t in msgs if chat and c == chat and t.startswith("/")]
        for c in cmds:
            if c == "/stop":
                self.stop("commande /stop reçue sur Telegram")
            elif c == "/reprendre":
                self.etat["pause"] = False
                self.dire("▶️ Robot relancé : il reprendra ses décisions au prochain matin.")
            elif c == "/etat":
                self.dire(self.texte_etat())
            elif c in ("/aide", "/start", "/help"):
                self.dire(AIDE)

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
            if rempli > 0:
                prix = float(d["filled_avg_price"])
                quand = str(pd.Timestamp(d["filled_at"]).tz_convert("America/New_York").date())
                if o["cote"] == "buy":
                    self.etat["positions"].append({"poche": o["poche"], "symbole": o["symbole"], "qte": int(rempli),
                                                   "date_entree": quand, "prix_entree": prix})
                    self.dire("✅ <b>Achat exécuté</b> [%s] %d %s à %s" % (o["poche"], rempli, o["symbole"], dollars(prix)))
                else:
                    self.enregistrer_vente(o, int(rempli), prix, quand)
            if statut != "filled":
                self.dire("⚠️ Ordre %s %s %s : %s (exécuté %d sur %d)" % (
                    "d'achat" if o["cote"] == "buy" else "de vente", o["poche"], o["symbole"], statut,
                    rempli, o["qte"]))
        self.etat["ordres"] = restants

    def enregistrer_vente(self, o, qte, prix, quand):
        pos = next((p for p in self.etat["positions"]
                    if p["poche"] == o["poche"] and p["symbole"] == o["symbole"]), None)
        if pos is None:
            return
        pnl = (prix - pos["prix_entree"]) * qte
        r = prix / pos["prix_entree"] - 1
        ajouter_journal({"date_sortie": quand, "poche": o["poche"], "symbole": o["symbole"], "qte": qte,
                         "date_entree": pos["date_entree"], "prix_entree": round(pos["prix_entree"], 4),
                         "prix_sortie": round(prix, 4), "pnl": round(pnl, 2), "rendement": round(r, 5),
                         "raison_sortie": o.get("raison", "")})
        pos["qte"] -= qte
        if pos["qte"] <= 0:
            self.etat["positions"].remove(pos)
        self.dire("%s <b>Vente exécutée</b> [%s] %d %s à %s : %s (%s)" % (
            "🟢" if pnl >= 0 else "🔴", o["poche"], qte, o["symbole"], dollars(prix), dollars(pnl, True), pct(r)))

    def envoyer_ordre(self, poche, symbole, qte, cote, raison, jour):
        ref = "%s-%s-%s-%s" % (jour, poche, symbole, cote)
        d = self.alpaca.passer_ordre(symbole, qte, cote, ref)
        self.etat["ordres"].append({"id": d["id"], "poche": poche, "symbole": symbole, "qte": int(qte),
                                    "cote": cote, "raison": raison, "date": str(jour)})

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
            if any(o["poche"] == p["poche"] and o["symbole"] == p["symbole"] and o["cote"] == "sell"
                   for o in self.etat["ordres"]):
                continue
            self.envoyer_ordre(p["poche"], p["symbole"], p["qte"], "sell", "arrêt : " + pourquoi, jour)
        self.etat["pause"] = True
        self.dire("🛑 <b>Robot en pause</b> : %s. Ordres en attente annulés, ventes de toutes les positions "
                  "envoyées (exécution à la prochaine ouverture si la bourse est fermée). /reprendre pour relancer."
                  % pourquoi)

    # -- les passages
    def matin(self, force=False):
        horloge, jour = self.aujourdhui_ny()
        self.reconcilier()
        self.lire_commandes()
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
        ventes_txt, achats_txt = [], []
        achats_prevus = []
        for poche in self.config["poches"]:
            mes = [p for p in self.etat["positions"] if p["poche"] == poche["nom"]]
            en_vente = {(o["poche"], o["symbole"]) for o in self.etat["ordres"] if o["cote"] == "sell"}
            ailleurs = {p["symbole"] for p in self.etat["positions"] if p["poche"] != poche["nom"]}
            ailleurs |= {s for _, s, _, _, _ in achats_prevus}
            ailleurs |= {o["symbole"] for o in self.etat["ordres"] if o["cote"] == "buy"}
            ventes, achats = decisions.decider(poche, data, mes, ailleurs, jour, veille, mois, equity, ordre_max)
            for p, raison in ventes:
                if (p["poche"], p["symbole"]) in en_vente:
                    continue
                self.envoyer_ordre(poche["nom"], p["symbole"], p["qte"], "sell", raison, jour)
                ventes_txt.append("• [%s] vendre %d %s : %s" % (poche["nom"], p["qte"], p["symbole"], raison))
            for s, qte, prix, raison in achats:
                achats_prevus.append((poche["nom"], s, qte, prix, raison))
        cash = float(compte["cash"]) * 0.98
        for poche_nom, s, qte, prix, raison in achats_prevus:
            if qte * prix > cash:
                qte = math.floor(cash / prix)
            if qte < 1:
                achats_txt.append("• [%s] %s : signal, mais plus assez de liquidités" % (poche_nom, s))
                continue
            self.envoyer_ordre(poche_nom, s, qte, "buy", raison, jour)
            cash -= qte * prix
            achats_txt.append("• [%s] acheter %d %s (~%s) : %s" % (poche_nom, qte, s, dollars(qte * prix), raison))
        lignes = ["☀️ <b>Ordres du %s</b> (exécution à l'ouverture, 15h30 heure de Paris en temps normal)"
                  % jour.strftime("%d/%m")]
        lignes += ventes_txt + achats_txt or ["Aucun signal : on ne touche à rien aujourd'hui."]
        if manquants:
            lignes.append("<i>Cours manquants ou pas à jour, ignorés : %s</i>" % ", ".join(manquants))
        self.dire("\n".join(lignes))

    def soir(self):
        _, jour = self.aujourdhui_ny()
        self.reconcilier()
        self.lire_commandes()
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
                lignes.append("• [%s] %d %s, entrée %s le %s, %s" % (
                    p["poche"], p["qte"], p["symbole"], dollars(p["prix_entree"]), p["date_entree"],
                    pct(prix / p["prix_entree"] - 1)))
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
                  "Le robot passera chaque jour de bourse vers 13h30-14h30 (ordres) et 22h30-23h30 (bilan), heure de Paris."
                  % (nom, c.get("account_number", "?"), dollars(float(c["equity"])), c.get("status")))
        self.dire(AIDE)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Robot de trading (compte fictif).")
    ap.add_argument("mode", choices=["connexion", "matin", "soir", "etat", "stop"])
    ap.add_argument("--force", action="store_true", help="matin : passer même si déjà fait ou marché ouvert")
    a = ap.parse_args(argv)
    robot = Robot()
    try:
        if a.mode == "connexion":
            robot.connexion()
        elif a.mode == "matin":
            robot.matin(force=a.force)
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
        robot.sauver()
        robot.envoyer()
        return 1
    robot.sauver()
    robot.envoyer()
    return 0


if __name__ == "__main__":
    sys.exit(main())
