"""Petit client pour l'API Alpaca, compte FICTIF uniquement (bibliothèque standard)."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

URL_FICTIF = "https://paper-api.alpaca.markets/v2"


class AlpacaErreur(Exception):
    pass


def symbole_alpaca(s):
    """Yahoo écrit BRK-B, Alpaca écrit BRK.B."""
    return s.replace("-", ".")


class Alpaca:
    def __init__(self, cle=None, secret=None, url=URL_FICTIF):
        if url != URL_FICTIF:
            raise AlpacaErreur("ce robot ne parle qu'au compte FICTIF (%s)" % URL_FICTIF)
        self.cle = (cle or os.environ.get("ALPACA_API_KEY", "")).strip()
        self.secret = (secret or os.environ.get("ALPACA_SECRET_KEY", "")).strip()
        if not self.cle or not self.secret:
            raise AlpacaErreur("clés Alpaca absentes : secrets ALPACA_API_KEY et ALPACA_SECRET_KEY")
        self.url = url

    def _appel(self, methode, chemin, params=None, corps=None):
        url = self.url + chemin
        if params:
            url += "?" + urllib.parse.urlencode(params)
        donnees = json.dumps(corps).encode() if corps is not None else None
        req = urllib.request.Request(url, data=donnees, method=methode, headers={
            "APCA-API-KEY-ID": self.cle, "APCA-API-SECRET-KEY": self.secret,
            "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                texte = r.read().decode()
                return json.loads(texte) if texte else None
        except urllib.error.HTTPError as e:
            raise AlpacaErreur("%s %s -> HTTP %s : %s" % (methode, chemin, e.code, e.read().decode()[:300]))

    def compte(self):
        return self._appel("GET", "/account")

    def horloge(self):
        return self._appel("GET", "/clock")

    def calendrier(self, debut, fin):
        return self._appel("GET", "/calendar", {"start": debut, "end": fin})

    def positions(self):
        return self._appel("GET", "/positions")

    def ordre(self, identifiant):
        return self._appel("GET", "/orders/%s" % identifiant)

    def ordres_ouverts(self):
        return self._appel("GET", "/orders", {"status": "open", "limit": 500})

    def annuler_tout(self):
        return self._appel("DELETE", "/orders")

    def passer_ordre(self, symbole, qte, cote, ref):
        return self._appel("POST", "/orders", corps={
            "symbol": symbole_alpaca(symbole), "qty": str(int(qte)), "side": cote,
            "type": "market", "time_in_force": "day", "client_order_id": ref[:48]})
