"""Envoi et lecture des messages Telegram, avec boutons Oui / Non (bibliothèque standard)."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request


class Telegram:
    def __init__(self, jeton=None, chat_id=None):
        self.jeton = (jeton or os.environ.get("TELEGRAM_TOKEN", "")).strip()  # espaces collés par erreur
        self.chat_id = chat_id
        if not self.jeton:
            raise RuntimeError("jeton Telegram absent : secret TELEGRAM_TOKEN")

    def _appel(self, methode, params):
        url = "https://api.telegram.org/bot%s/%s" % (self.jeton, methode)
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                rep = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:      # Telegram renvoie 400 avec une description lisible
            try:
                rep = json.loads(e.read().decode())
            except Exception:
                rep = {"ok": False, "description": "HTTP %s" % e.code}
        if not rep.get("ok"):
            raise RuntimeError("Telegram %s : %s" % (methode, rep.get("description")))
        return rep["result"]

    def moi(self):
        return self._appel("getMe", {})

    def envoyer(self, texte, boutons=None):
        """Envoie un message (découpé si trop long). boutons : [(libellé, donnée), ...] sur une ligne.
        Retourne l'identifiant du dernier message envoyé."""
        if not self.chat_id:
            print("[telegram non connecté] " + texte)
            return None
        morceaux = [texte[i:i + 3900] for i in range(0, len(texte), 3900)] or [""]
        dernier = None
        for k, m in enumerate(morceaux):
            params = {"chat_id": self.chat_id, "text": m, "parse_mode": "HTML", "disable_web_page_preview": "true"}
            if boutons and k == len(morceaux) - 1:
                params["reply_markup"] = json.dumps(
                    {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in boutons]]})
            dernier = self._appel("sendMessage", params)["message_id"]
        return dernier

    def modifier(self, message_id, texte):
        """Remplace le texte d'un message et retire ses boutons."""
        try:
            self._appel("editMessageText", {"chat_id": self.chat_id, "message_id": message_id, "text": texte,
                                            "parse_mode": "HTML", "disable_web_page_preview": "true"})
        except Exception as exc:
            print("modification du message %s : %s" % (message_id, exc))

    def repondre_bouton(self, callback_id, texte):
        try:
            self._appel("answerCallbackQuery", {"callback_query_id": callback_id, "text": texte[:190]})
        except Exception as exc:  # un appui trop ancien ne peut plus recevoir de réponse : sans gravité
            print("réponse au bouton : %s" % exc)

    def evenements(self, decalage=0, attente=0):
        """Retourne (événements, nouveau décalage). Un événement est un dict :
        {"type": "message", "chat": id, "texte": ..., "reponse_a": message_id ou None}
        {"type": "bouton", "chat": id, "donnee": ..., "callback": id, "message": message_id}"""
        maj = self._appel("getUpdates", {"offset": decalage, "timeout": attente,
                                         "allowed_updates": json.dumps(["message", "callback_query"])})
        evts, dernier = [], decalage
        for u in maj:
            dernier = max(dernier, u["update_id"] + 1)
            if "callback_query" in u:
                c = u["callback_query"]
                evts.append({"type": "bouton", "chat": c["message"]["chat"]["id"], "donnee": c.get("data", ""),
                             "callback": c["id"], "message": c["message"]["message_id"]})
            elif (u.get("message") or {}).get("text"):
                m = u["message"]
                evts.append({"type": "message", "chat": m["chat"]["id"], "texte": m["text"].strip(),
                             "reponse_a": (m.get("reply_to_message") or {}).get("message_id")})
        return evts, dernier

    def nouveaux_messages(self, decalage=0, attente=0):
        """Compatibilité : seulement les messages texte, [(chat, texte)]."""
        evts, dernier = self.evenements(decalage, attente)
        return [(e["chat"], e["texte"]) for e in evts if e["type"] == "message"], dernier
