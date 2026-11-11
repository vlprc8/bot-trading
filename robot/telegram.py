"""Envoi et lecture des messages Telegram (bibliothèque standard)."""

import json
import os
import urllib.parse
import urllib.request


class Telegram:
    def __init__(self, jeton=None, chat_id=None):
        self.jeton = jeton or os.environ.get("TELEGRAM_TOKEN", "")
        self.chat_id = chat_id
        if not self.jeton:
            raise RuntimeError("jeton Telegram absent : secret TELEGRAM_TOKEN")

    def _appel(self, methode, params):
        url = "https://api.telegram.org/bot%s/%s" % (self.jeton, methode)
        req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode())
        with urllib.request.urlopen(req, timeout=30) as r:
            rep = json.loads(r.read().decode())
        if not rep.get("ok"):
            raise RuntimeError("Telegram %s : %s" % (methode, rep.get("description")))
        return rep["result"]

    def moi(self):
        return self._appel("getMe", {})

    def envoyer(self, texte):
        if not self.chat_id:
            print("[telegram non connecté] " + texte)
            return None
        # Telegram limite un message à 4096 caractères
        for i in range(0, len(texte), 3900):
            self._appel("sendMessage", {"chat_id": self.chat_id, "text": texte[i:i + 3900],
                                        "parse_mode": "HTML", "disable_web_page_preview": "true"})

    def nouveaux_messages(self, decalage=0):
        """Retourne (messages [(chat_id, texte)], nouveau décalage)."""
        maj = self._appel("getUpdates", {"offset": decalage, "timeout": 0})
        msgs, dernier = [], decalage
        for u in maj:
            dernier = max(dernier, u["update_id"] + 1)
            m = u.get("message") or {}
            if m.get("text"):
                msgs.append((m["chat"]["id"], m["text"].strip()))
        return msgs, dernier
