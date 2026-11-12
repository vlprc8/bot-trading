"""Petit client pour l'API Alpaca, compte FICTIF uniquement (bibliothèque standard)."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

URL_FICTIF = "https://paper-api.alpaca.markets/v2"
URL_DONNEES = "https://data.alpaca.markets"     # cours et actualités (gratuits, flux IEX)


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

    def _appel(self, methode, chemin, params=None, corps=None, base=None):
        url = (base or self.url) + chemin
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

    def derniers_prix(self, symboles):
        """{symbole: dernier prix échangé} en direct (flux gratuit IEX)."""
        if not symboles:
            return {}
        rep = self._appel("GET", "/v2/stocks/trades/latest", {
            "symbols": ",".join(symbole_alpaca(s) for s in symboles), "feed": "iex"}, base=URL_DONNEES)
        return {k.replace(".", "-"): float(v["p"]) for k, v in (rep or {}).get("trades", {}).items()}

    def actualites(self, symbole, n=3):
        """Les derniers titres d'actualité d'une action : [(date, titre, source, lien)]."""
        rep = self._appel("GET", "/v1beta1/news", {"symbols": symbole_alpaca(symbole), "limit": n,
                                                    "sort": "desc"}, base=URL_DONNEES)
        return [(a.get("created_at", "")[:10], a.get("headline", ""), a.get("source", ""), a.get("url", ""))
                for a in (rep or {}).get("news", [])]

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

    def annuler(self, identifiant):
        return self._appel("DELETE", "/orders/%s" % identifiant)

    def passer_ordre(self, symbole, cote, ref, qte=None, montant=None, stop=None):
        """Ordre valable pour la journée. Achat : `montant` en dollars (fractions d'actions).
        Vente : `qte` (fractions possibles), au marché, ou en ordre stop si `stop` est donné."""
        corps = {"symbol": symbole_alpaca(symbole), "side": cote, "time_in_force": "day",
                 "client_order_id": ref[:48], "type": "stop" if stop else "market"}
        if montant is not None:
            corps["notional"] = "%.2f" % montant
        else:
            corps["qty"] = ("%.9f" % qte).rstrip("0").rstrip(".")
        if stop:
            corps["stop_price"] = "%.2f" % stop
        return self._appel("POST", "/orders", corps=corps)
