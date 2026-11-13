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
        self.prix_direct = 100.0
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

    def derniers_prix(self, symboles):
        return {s: self.prix_direct for s in symboles}

    def annuler(self, i):
        self.ordres[i]["status"] = "canceled"

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
        self.envoyes, self.boutons, self.modifs, self.reponses, self.file = [], {}, {}, [], []
        self.chat_id = 42
        self.compteur = itertools.count(100)

    def envoyer(self, texte, boutons=None):
        i = next(self.compteur)
        self.envoyes.append(texte)
        if boutons:
            self.boutons[i] = boutons
        return i

    def modifier(self, message_id, texte):
        self.modifs[message_id] = texte

    def repondre_bouton(self, callback, texte):
        self.reponses.append(texte)

    def appuyer(self, message_id, choix):
        donnee = dict((b[0][2:], b[1]) for b in self.boutons[message_id])[choix]
        self.file.append({"type": "bouton", "chat": 42, "donnee": donnee, "callback": "c", "message": message_id})

    def evenements(self, decalage=0, attente=0):
        evts, self.file = self.file, []
        return evts, decalage + len(evts)


class Flux(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.anciens = {k: getattr(lancer_robot, k) for k in ("CONFIG", "ETAT", "JOURNAL", "cours", "Alpaca", "Telegram",
                                                              "prochains_resultats")}
        config = json.load(open(self.anciens["CONFIG"], encoding="utf-8"))
        config["poches"] = [p for p in config["poches"] if p["nom"] == "tournant"]
        config["poches"][0]["part"] = 1.0
        config["chat_id"] = 42
        lancer_robot.CONFIG = os.path.join(self.tmp, "config.json")
        lancer_robot.ETAT = os.path.join(self.tmp, "etat.json")
        lancer_robot.JOURNAL = os.path.join(self.tmp, "journal.csv")
        json.dump(config, open(lancer_robot.CONFIG, "w"))
        lancer_robot.cours = lambda symboles, jours=500: {s: DATA["SPY"] for s in symboles}
        lancer_robot.prochains_resultats = lambda s: None
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
        r.envoyer()          # même ordre que lancer_robot.main : envoyer, puis sauver
        r.sauver()
        return r

    def proposition_du_matin(self):
        # 29/06/2026 = avant-dernière séance de juin : la poche « tournant » PROPOSE d'acheter SPY
        self.passage("matin", "2026-06-29T03:00:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})              # rien ne part sans ton Oui
        msg_id = max(self.tg.boutons)
        msg = self.tg.envoyes[-1]
        for attendu in ("Acheter 980,00 $ de SPY", "Stop de sécurité", "Sortie prévue", "Historique 2019-2026",
                        "Je passe cet achat ?"):
            self.assertIn(attendu, msg)
        self.assertIn("1 proposition(s) d'achat", self.tg.envoyes[-2])
        return msg_id

    def test_non_ne_passe_aucun_ordre(self):
        msg_id = self.proposition_du_matin()
        self.tg.appuyer(msg_id, "Non")
        self.passage("validation", "2026-06-29T04:00:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})
        self.assertIn("Refusé", self.tg.modifs[msg_id])

    def test_sans_reponse_la_proposition_expire_a_l_ouverture(self):
        msg_id = self.proposition_du_matin()
        self.alpaca.ouvert = True
        self.passage("validation", "2026-06-29T09:40:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})
        self.assertIn("Expirée", self.tg.modifs[msg_id])

    def test_exemple_a_5_dollars(self):
        self.alpaca.ouvert = True
        self.passage("exemple", "2026-06-29T10:00:00-04:00")
        msg_id = max(self.tg.boutons)
        self.assertIn("TEST", self.tg.envoyes[-1])
        self.tg.appuyer(msg_id, "Oui")
        self.passage("validation", "2026-06-29T10:05:00-04:00")
        self.assertEqual([o["montant"] for o in self.alpaca.ordres.values()], [5.0])
        self.assertIn("exécution immédiate", self.tg.modifs[msg_id])

    def test_achat_stop_puis_stop_touche(self):
        msg_id = self.proposition_du_matin()
        self.tg.appuyer(msg_id, "Oui")
        self.passage("validation", "2026-06-29T04:00:00-04:00")
        achat = [o for o in self.alpaca.ordres.values() if o["cote"] == "buy"]
        self.assertEqual(len(achat), 1)
        self.assertAlmostEqual(achat[0]["montant"], 980.0)     # 98 % du cash : marge pour les frais
        self.assertIn("Accepté", self.tg.modifs[msg_id])
        self.assertIn("Ordre envoyé", self.tg.reponses[-1])

        self.alpaca.remplir("o1", 100.0, "2026-06-29T09:30:05-04:00")
        self.passage("soir", "2026-06-29T17:30:00-04:00")
        etat = json.load(open(lancer_robot.ETAT))
        pos = etat["positions"][0]
        self.assertAlmostEqual(pos["qte"], 9.8)
        self.assertLess(pos["stop"], 100.0)
        self.assertIn("Achat exécuté", self.tg.envoyes[-1])

        # le lendemain matin : un ordre stop de sécurité est posé pour la journée
        self.passage("matin", "2026-06-30T03:00:00-04:00")
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

    def position_achetee_hier(self):
        msg_id = self.proposition_du_matin()
        self.assertIn("je te demande si tu veux vendre", self.tg.envoyes[-1])
        self.tg.appuyer(msg_id, "Oui")
        self.passage("validation", "2026-06-29T04:00:00-04:00")
        self.alpaca.remplir("o1", 100.0, "2026-06-29T09:30:05-04:00")
        self.passage("soir", "2026-06-29T17:30:00-04:00")
        self.passage("matin", "2026-06-30T03:00:00-04:00")          # pose le stop de sécurité du jour
        return next(i for i, o in self.alpaca.ordres.items() if o["stop"])

    def en_seance(self, prix):
        self.alpaca.ouvert, self.alpaca.prix_direct = True, prix
        self.alpaca.maintenant = "2026-06-30T13:00:00-04:00"
        r = lancer_robot.Robot()
        r.reconcilier()
        r.surveiller_hausse(pd.Timestamp("2026-06-30").date())
        r.lire_commandes()
        r.envoyer()
        r.sauver()

    def ventes(self):
        return [o for o in self.alpaca.ordres.values() if o["cote"] == "sell" and not o["stop"]]

    def test_demande_de_vente_quand_ca_monte_fort(self):
        stop_id = self.position_achetee_hier()
        self.en_seance(121.0)                                    # +21 % : une demande, pas de vente automatique
        self.assertEqual(self.ventes(), [])
        msg_id = max(self.tg.boutons)
        self.assertIn("a pris +21,00 %", self.tg.envoyes[-1])
        self.assertIn("Je vends maintenant ?", self.tg.envoyes[-1])
        self.en_seance(125.0)                                    # même palier : pas de nouvelle demande
        self.assertEqual(max(self.tg.boutons), msg_id)
        self.tg.appuyer(msg_id, "Oui")                           # tu dis oui : stop annulé, vente au marché
        self.en_seance(124.0)
        self.assertEqual(self.alpaca.ordres[stop_id]["status"], "canceled")
        self.assertEqual(len(self.ventes()), 1)
        self.assertAlmostEqual(self.ventes()[0]["qte"], 9.8)
        self.assertIn("Vente envoyée à Alpaca", self.tg.modifs[msg_id])

    def test_non_on_garde_et_on_redemande_plus_haut(self):
        self.position_achetee_hier()
        self.en_seance(111.0)                                    # +11 % : demande au palier 10
        premier = max(self.tg.boutons)
        self.tg.appuyer(premier, "Non")
        self.en_seance(112.0)
        self.assertIn("on garde la position", self.tg.modifs[premier])
        self.assertEqual(self.ventes(), [])
        self.en_seance(116.0)                                    # +16 % : nouvelle demande au palier 15
        self.assertGreater(max(self.tg.boutons), premier)

    def test_rien_sous_10_pourcent(self):
        self.position_achetee_hier()
        n = len(self.tg.boutons)
        self.en_seance(108.0)
        self.assertEqual(len(self.tg.boutons), n)
        self.assertEqual(self.ventes(), [])

    def test_refuse_le_compte_a_100000(self):
        self.alpaca.equity = 100000.0
        self.passage("matin", "2026-06-29T03:00:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})
        self.assertIn("pas le compte à 1 000 $", self.tg.envoyes[-1])

    def test_pas_d_ordre_si_la_bourse_est_ouverte(self):
        self.alpaca.ouvert = True
        self.passage("matin", "2026-06-29T10:00:00-04:00")
        self.assertEqual(self.alpaca.ordres, {})

    def test_matin_en_retard_pas_d_achat_mais_un_message(self):
        self.alpaca.ouvert = True
        self.alpaca.maintenant = "2026-06-29T10:00:00-04:00"
        r = lancer_robot.Robot()
        r.matin(retard=True)
        r.envoyer()
        r.sauver()
        self.assertEqual(self.alpaca.ordres, {})          # aucun achat proposé ni passé
        self.assertIn("Passage en retard", self.tg.envoyes[-1])
        self.assertIn("1 signal", self.tg.envoyes[-1])


if __name__ == "__main__":
    unittest.main()
