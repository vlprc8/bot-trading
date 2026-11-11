# Bot de trading swing (simulation)

Objectif : trouver une stratégie qui achète et revend en quelques jours (swing trading),
la tester honnêtement sur 20 ans de vrais cours, puis la faire tourner automatiquement
sur un compte **fictif** Alpaca, avec des notifications Telegram. Aucun argent réel.

## Où on en est

| Étape | Quoi | État |
|---|---|---|
| 1 | Comptes : GitHub, Alpaca (fictif), bot Telegram | en cours |
| 2 | Récupérer 20 ans de cours journaliers (Yahoo Finance) | prêt, à lancer |
| 3 | Labo de backtest : 2 stratégies swing x 2 univers, contre « acheter le S&P 500 et garder » | prêt, à lancer |
| 4 | Choisir avec des critères fixés à l'avance | après l'étape 3 |
| 5 | Le bot en compte fictif : ordres auto, Telegram, garde-fous | à faire |
| 6 | 2 à 3 mois de simulation, bilan mensuel | à faire |

## Lancer le backtest

Dans GitHub : onglet **Actions** > **Backtest** > **Run workflow**. Environ 5 minutes.
Le résultat s'affiche dans le résumé de l'exécution et est enregistré dans
[`rapport/RESULTATS.md`](rapport/RESULTATS.md).

## Les stratégies testées

Écrites **avant** de voir les résultats, pour ne pas ajuster le passé :

- **rebond_court** : acheter une valeur en tendance haussière (au-dessus de sa moyenne
  200 jours) après 2-3 jours de baisse (RSI 2 sous 10) ; revendre au rebond (clôture
  au-dessus de la moyenne 5 jours) ou au bout de 5 jours.
- **cassure_courte** : acheter une valeur qui fait son plus haut de 20 jours, en tendance
  haussière ; revendre si elle casse son plus bas de 5 jours, ou au bout de 10 jours.

Chacune sur deux univers : 17 **ETF** (indices, secteurs, or, obligations ; aucun biais)
et 50 **grandes actions** US (biaisé : ce sont les gagnantes d'aujourd'hui).

## Les règles pour ne pas se mentir

- Décision le soir à la clôture, ordre à l'ouverture du lendemain : jamais de prix du futur
  (des tests le vérifient à chaque lancement).
- Frais de 0,10 % à chaque achat et chaque vente, plus un test avec des frais doublés.
- Réglage sur 2006-2018, vérification sur 2019-aujourd'hui.
- Une stratégie n'est retenue que si, sur la vérification : Sharpe meilleur que la
  référence, pire baisse moins grave que -30 %, facteur de profit d'au moins 1,2,
  au moins 100 trades.

## Fichiers

```
lancer_backtest.py   le point d'entrée
lab/univers.py       les valeurs testées
lab/donnees.py       téléchargement et lecture des cours
lab/strategies.py    les règles des stratégies
lab/moteur.py        la simulation jour par jour
lab/stats.py         les chiffres (rendement, pire baisse, Sharpe...)
lab/rapport.py       le rapport et le graphique
tests/               les tests du moteur
```

Pas un conseil financier. Un backtest réussi n'est pas une promesse de gain.
