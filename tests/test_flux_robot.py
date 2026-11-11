"""Le robot de bout en bout, sans réseau : faux Alpaca, faux Telegram, cours synthétiques."""

import itertools
import json
import os
import shutil
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import lancer_robot  # noqa: E402
from lab import donnees  # noqa: E402

DATA = donnees.synthetiques(["SPY"], debut="2024-01-01", fin="2026-12-31")


class FauxAlpaca:
    def __init__(self):
        self.maintenant = "2026-06-29T08:00:00-04:00"
        self.ouvert = False
        self.equity = 1000.0
        self.ordres = {}
        self.compteur = itertools.count(1)

    def horloge(self):
        return {"timestamp": self.maintenant, "is_open": self.ouvert}

    def calendrier(self, debut, fin):
        return [{"date": d.strftime("%Y-%m-%d")} for d in pd.bdate_range(debut, fin)]

    def compte(self):
        return {"equity": str(self.equity), "cash": str(self.equity), "last_equity": str(self.equity),
                "account_number": "PAFAUX", "status": "ACTIVE"}

    def positions(self):
        return []

    def annuler_tout(self):
        pass

    def passer_ordre(self, symbole, cote, ref, qte=None, montant=None, stop=None):
        i = "o%d" % next(self.compteur)
        self.ordres[i] = {"symbole": symbole, "cote": cote, "qte": qte, "montant": montant, "stop": stop,
                          "status": "new"}
        return {"id": i}

    def remplir(self, i, prix, quand):
        o = self.ordres[i]
        qte = o["qte"] or o["montant"] / prix
        o.update(status="filled", filled_qty=str(qte), filled_avg_price=str(prix), filled_at=quand)

    def ordre(self, i):
        o = self.ordres[i]
        return {"status": o["status"], "filled_qty": o.get("filled_qty", "0"),
                "filled_avg_price": o.get("filled_avg_price"), "filled_at": o.get("filled_at")}


class FauxTelegram:
    def __init__(self):
        self.envoyes = []
        self.chat_id = 42

    def envoyer(self, texte):
        self.envoyes.append(texte)

    def nouveaux_messages(self, decalage=0, attente=0):
        return [], decalage


class Flux(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.anciens = {k: getattr(lancer_robot, k) for k in ("CONFIG", "ETAT", "JOURNAL", "cours", "Alpaca", "Telegram")}
        config = json.load(open(self.anciens["CONFIG"], encoding="utf-8"))
        config["poches"] = [p for p in config["poches"] if p["nom"] == "tournant"]
        config["poches"][0]["part"] = 1.0
        lancer_robot.CONFIG = os.path.join(self.tmp, "config.json")
        lancer_robot.ETAT = os.path.join(self.tmp, "etat.json")
        lancer_robot.JOURNAL = os.path.join(self.tmp, "journal.csv")
        json.dump(config, open(lancer_robot.CONFIG, "w"))
        lancer_robot.cours = lambda symboles, jours=500: {s: DATA["SPY"] for s in symboles}
        self.alpaca, self.tg = FauxAlpaca(), FauxTelegram()
        lancer_robot.Alpaca = lambda: self.alpaca
        lancer_robot.Telegram = lambda chat_id=None: self.tg

    def tearDown(self):
        for k, v in self.anciens.items():
            setattr(lancer_robot, k, v)
        shutil.rmtree(self.tmp)

    def passage(self, mode, maintenant):
        self.alpaca.maintenant = maintenant
        r = lancer_robot.Robot()
        getattr(r, mode)()
        r.sauver()
        r.envoyer()
        return r

    def test_achat_stop_puis_stop_touche(self):
        # 29/06/2026 = avant-dernière séance de juin : la poche « tournant » achète SPY pour 1 000 $
        self.passage("matin", "2026-06-29T08:00:00-04:00")
        achat = [o for o in self.alpaca.ordres.values() if o["cote"] == "buy"]
        self.assertEqual(len(achat), 1)
        self.assertAlmostEqual(achat[0]["montant"], 980.0)     # 98 % du cash : marge pour les frais
        msg = self.tg.envoyes[-1]
        for attendu in ("Acheter 980,00 $ de SPY", "Stop de sécurité", "Sortie prévue", "Historique 2019-2026"):
            self.assertIn(attendu, msg)

        self.alpaca.remplir("o1", 100.0, "2026-06-29T09:30:05-04:00")
        self.passage("soir", "2026-06-29T17:30:00-04:00")
        etat = json.load(open(lancer_robot.ETAT))
        pos = etat["positions"][0]
        self.assertAlmostEqual(pos["qte"], 9.8)
        self.assertLess(pos["stop"], 100.0)
        self.assertIn("Achat exécuté", self.tg.envoyes[-1])

        # le lendemain matin : un ordre stop de sécurité est posé pour la journée
        self.passage("matin", "2026-06-30T08:00:00-04:00")
        stops = [(i, o) for i, o in self.alpaca.ordres.items() if o["stop"]]
        self.assertEqual(len(stops), 1)
        self.assertAlmostEqual(stops[0][1]["qte"], 9.8)
        self.assertIn("Stops de sécurité en place", self.tg.envoyes[-1])

        # il se déclenche : la vente est enregistrée dans le journal avec sa raison
        self.alpaca.remplir(stops[0][0], pos["stop"], "2026-06-30T11:00:00-04:00")
        self.passage("soir", "2026-06-30T17:30:00-04:00")
        journal = pd.read_csv(lancer_robot.JOURNAL)
        self.assertEqual(journal.iloc[0]["raison_sortie"], "stop de sécurité touché")
        self.assertEqual(json.load(open(lancer_robot.ETAT))["positions"], [])

    def test_refuse_le_compte_a_100000(self):
        self.alpaca.equity = 100000.0
        self.passage("matin", "2026-06-29T08:00:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})
        self.assertIn("pas le compte à 1 000 $", self.tg.envoyes[-1])

    def test_pas_d_ordre_si_la_bourse_est_ouverte(self):
        self.alpaca.ouvert = True
        self.passage("matin", "2026-06-29T10:00:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})


if __name__ == "__main__":
    unittest.main()
