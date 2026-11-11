# Résultats du backtest

Généré le 2026-11-11. Données : Yahoo Finance, cours journaliers ajustés.

Règles de simulation : capital de départ 1 000 $, décision le soir à la clôture, ordre à l'ouverture du lendemain, 5 positions au plus (environ 1/5 du capital chacune), frais 0.10 % par achat et par vente, fractions d'actions, pas de levier.

Variantes « + stop » : stop de sécurité à 3 x ATR(14) sous le prix d'achat, actif dès le lendemain de l'achat ; les sorties de la stratégie restent en place.

![courbes](courbes.png)

## Classement (période de vérification, 2019 à aujourd'hui)

| Stratégie | Critères réussis | Rendement / an | Pire baisse | Sharpe | Trades / mois |
|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | - | +16.9 % | -33.7 % | 0.91 | - |
| momentum_hebdo / sp500 | 4 / 6 | +28.8 % | -54.3 % | 0.86 | 21.7 |
| retournement_hebdo / sp500 | 3 / 6 | +26.7 % | -41.7 % | 0.88 | 21.7 |
| retournement_hebdo / sp500 + stop | 3 / 6 | +24.8 % | -41.2 % | 0.84 | 21.7 |
| momentum_hebdo / sp500 + stop | 3 / 6 | +23.2 % | -52.5 % | 0.75 | 21.7 |
| cassure_courte / actions + stop | 3 / 6 | +10.7 % | -24.8 % | 0.63 | 13.5 |
| momentum_hebdo / actions + stop | 3 / 6 | +11.9 % | -34.5 % | 0.58 | 21.4 |
| cassure_courte / actions | 3 / 6 | +8.7 % | -24.5 % | 0.53 | 13.4 |
| tournant_du_mois / spy | 3 / 6 | +3.5 % | -16.9 % | 0.43 | 1.0 |
| tournant_du_mois / spy + stop | 3 / 6 | +2.9 % | -16.1 % | 0.38 | 1.0 |
| rebond_court / actions | 3 / 6 | +4.6 % | -24.6 % | 0.34 | 18.5 |
| retournement_hebdo / etf | 3 / 6 | +2.8 % | -23.7 % | 0.32 | 12.2 |
| rebond_court / actions + stop | 3 / 6 | +2.9 % | -29.2 % | 0.25 | 19.0 |
| retournement_hebdo / etf + stop | 3 / 6 | +1.6 % | -23.5 % | 0.21 | 12.4 |
| rebond_court / sp500 | 2 / 6 | +10.1 % | -45.5 % | 0.55 | 29.0 |
| cassure_courte / sp500 | 2 / 6 | +10.6 % | -51.6 % | 0.52 | 13.9 |
| cassure_courte / sp500 + stop | 2 / 6 | +9.7 % | -55.7 % | 0.49 | 14.0 |
| rebond_court / etf + stop | 2 / 6 | +1.6 % | -13.1 % | 0.25 | 9.1 |
| cassure_courte / etf + stop | 2 / 6 | +1.6 % | -12.3 % | 0.22 | 9.7 |
| cassure_courte / etf | 2 / 6 | +1.6 % | -12.8 % | 0.22 | 9.7 |
| rebond_court / etf | 2 / 6 | +1.1 % | -13.8 % | 0.18 | 8.7 |
| retournement_hebdo / actions + stop | 2 / 6 | -2.4 % | -44.6 % | 0.00 | 19.4 |
| retournement_hebdo / actions | 2 / 6 | -2.7 % | -46.6 % | -0.01 | 19.4 |
| rebond_court / sp500 + stop | 1 / 6 | +11.5 % | -36.4 % | 0.61 | 29.6 |
| momentum_hebdo / actions | 1 / 6 | +7.1 % | -36.0 % | 0.40 | 21.4 |
| cloture_basse / sp500 | 1 / 6 | -0.3 % | -45.7 % | 0.09 | 47.3 |
| cloture_basse / sp500 + stop | 1 / 6 | -1.3 % | -49.8 % | 0.04 | 47.5 |
| cloture_basse / actions | 1 / 6 | -3.4 % | -42.4 % | -0.14 | 35.0 |
| cloture_basse / actions + stop | 1 / 6 | -3.5 % | -42.8 % | -0.14 | 35.1 |
| momentum_hebdo / etf + stop | 1 / 6 | -2.7 % | -39.4 % | -0.17 | 18.3 |
| momentum_hebdo / etf | 1 / 6 | -2.9 % | -31.5 % | -0.18 | 18.2 |
| cloture_basse / etf + stop | 1 / 6 | -2.0 % | -38.2 % | -0.20 | 20.6 |
| cloture_basse / etf | 1 / 6 | -2.1 % | -37.3 % | -0.22 | 20.6 |

## Les règles de chaque stratégie

- **rebond_court** : Achat si clôture > moyenne 200 jours ET RSI(2) < 10 ; vente si clôture > moyenne 5 jours, ou après 5 jours
- **cassure_courte** : Achat si clôture = plus haute des 20 derniers jours ET > moyenne 200 jours ; vente si clôture < plus basse des 5 jours précédents, ou après 10 jours
- **cloture_basse** : Achat si clôture > moyenne 200 jours ET clôture dans les 15 % du bas de la journée (IBS < 0,15) ; vente si IBS > 0,7, ou après 3 jours
- **retournement_hebdo** : Chaque vendredi : parmi les valeurs > moyenne 200 jours, acheter celles qui ont le plus baissé sur 5 jours ; revendre le vendredi suivant
- **momentum_hebdo** : Chaque vendredi : acheter les valeurs > moyenne 200 jours qui ont le plus monté sur 3 mois (63 séances) ; revendre le vendredi suivant
- **tournant_du_mois** : Achat à l'ouverture de l'avant-dernière séance du mois ; vente à l'ouverture de la 4e séance du mois suivant

## Période : tout

| Stratégie | Rendement / an | Pire baisse | Sharpe | Trades / mois | Réussite | Trade moyen | Jours moyens | Facteur profit | Investi |
|---|---|---|---|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | +11.0 % | -55.2 % | 0.64 | - | - | - | - | - | 100.0 % |
| rebond_court / etf | +0.2 % | -23.7 % | 0.07 | 8.2 | 60.2 % | +0.0 % | 3.3 | 1.02 | 25.5 % |
| rebond_court / etf + stop | +0.1 % | -21.1 % | 0.05 | 8.5 | 59.9 % | +0.0 % | 3.1 | 1.01 | 24.9 % |
| rebond_court / actions | +5.1 % | -38.7 % | 0.41 | 17.4 | 60.5 % | +0.1 % | 3.3 | 1.11 | 54.5 % |
| rebond_court / actions + stop | +3.5 % | -39.2 % | 0.31 | 17.7 | 60.0 % | +0.1 % | 3.2 | 1.07 | 53.7 % |
| rebond_court / sp500 | +6.6 % | -45.5 % | 0.42 | 28.5 | 59.8 % | +0.1 % | 3.3 | 1.07 | 89.7 % |
| rebond_court / sp500 + stop | +5.8 % | -40.8 % | 0.39 | 29.1 | 59.7 % | +0.1 % | 3.2 | 1.07 | 88.2 % |
| cassure_courte / etf | -0.1 % | -21.3 % | 0.03 | 9.3 | 43.6 % | +0.0 % | 6.9 | 0.99 | 61.3 % |
| cassure_courte / etf + stop | -0.1 % | -21.7 % | 0.03 | 9.3 | 43.6 % | +0.0 % | 6.9 | 0.99 | 61.0 % |
| cassure_courte / actions | +4.3 % | -53.4 % | 0.34 | 12.8 | 42.9 % | +0.2 % | 7.0 | 1.09 | 85.4 % |
| cassure_courte / actions + stop | +5.1 % | -52.2 % | 0.38 | 12.8 | 42.9 % | +0.2 % | 7.0 | 1.12 | 84.9 % |
| cassure_courte / sp500 | +2.0 % | -76.2 % | 0.20 | 13.8 | 43.7 % | +0.1 % | 7.4 | 1.05 | 97.2 % |
| cassure_courte / sp500 + stop | +0.7 % | -77.0 % | 0.14 | 13.9 | 43.5 % | +0.1 % | 7.3 | 1.01 | 96.6 % |
| cloture_basse / etf | -3.2 % | -52.1 % | -0.37 | 18.9 | 53.9 % | -0.1 % | 2.0 | 0.88 | 36.2 % |
| cloture_basse / etf + stop | -3.7 % | -57.0 % | -0.45 | 19.0 | 53.9 % | -0.1 % | 2.0 | 0.86 | 35.7 % |
| cloture_basse / actions | -0.3 % | -55.6 % | 0.06 | 33.5 | 54.7 % | +0.0 % | 2.1 | 1.00 | 66.6 % |
| cloture_basse / actions + stop | -0.8 % | -59.0 % | 0.02 | 33.6 | 54.7 % | +0.0 % | 2.1 | 0.99 | 65.9 % |
| cloture_basse / sp500 | -2.0 % | -61.7 % | 0.00 | 46.5 | 55.7 % | -0.0 % | 2.1 | 0.98 | 93.1 % |
| cloture_basse / sp500 + stop | -3.6 % | -65.6 % | -0.09 | 46.7 | 55.6 % | -0.0 % | 2.1 | 0.97 | 92.2 % |
| retournement_hebdo / etf | +2.9 % | -23.7 % | 0.33 | 11.6 | 52.8 % | +0.1 % | 4.8 | 1.11 | 53.7 % |
| retournement_hebdo / etf + stop | +2.3 % | -23.5 % | 0.27 | 11.8 | 52.5 % | +0.1 % | 4.7 | 1.08 | 52.5 % |
| retournement_hebdo / actions | +5.8 % | -46.6 % | 0.38 | 19.0 | 52.4 % | +0.2 % | 4.8 | 1.05 | 87.3 % |
| retournement_hebdo / actions + stop | +5.3 % | -49.6 % | 0.36 | 19.1 | 52.4 % | +0.2 % | 4.7 | 1.05 | 85.6 % |
| retournement_hebdo / sp500 | +16.1 % | -58.4 % | 0.65 | 21.5 | 52.5 % | +0.4 % | 4.8 | 1.19 | 98.6 % |
| retournement_hebdo / sp500 + stop | +13.9 % | -58.8 % | 0.59 | 21.5 | 52.4 % | +0.3 % | 4.7 | 1.17 | 96.9 % |
| momentum_hebdo / etf | -2.0 % | -45.1 % | -0.11 | 17.8 | 51.6 % | -0.0 % | 4.8 | 0.95 | 81.8 % |
| momentum_hebdo / etf + stop | -1.9 % | -44.4 % | -0.11 | 17.9 | 51.3 % | -0.0 % | 4.7 | 0.95 | 79.7 % |
| momentum_hebdo / actions | +4.6 % | -51.0 % | 0.31 | 21.0 | 51.8 % | +0.1 % | 4.8 | 1.06 | 96.5 % |
| momentum_hebdo / actions + stop | +8.6 % | -49.4 % | 0.49 | 21.0 | 52.3 % | +0.2 % | 4.7 | 1.12 | 94.2 % |
| momentum_hebdo / sp500 | +14.7 % | -72.1 % | 0.58 | 21.7 | 51.8 % | +0.4 % | 4.8 | 1.21 | 99.3 % |
| momentum_hebdo / sp500 + stop | +10.3 % | -73.9 % | 0.47 | 21.7 | 51.0 % | +0.3 % | 4.7 | 1.15 | 96.5 % |
| tournant_du_mois / spy | +0.2 % | -30.6 % | 0.07 | 1.0 | 58.4 % | +0.0 % | 5.0 | 1.02 | 23.9 % |
| tournant_du_mois / spy + stop | +0.2 % | -30.6 % | 0.06 | 1.0 | 58.4 % | +0.0 % | 4.8 | 1.01 | 23.1 % |

## Période : reglage (2006-2018)

| Stratégie | Rendement / an | Pire baisse | Sharpe | Trades / mois | Réussite | Trade moyen | Jours moyens | Facteur profit | Investi |
|---|---|---|---|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | +7.5 % | -55.2 % | 0.48 | - | - | - | - | - | 100.0 % |
| rebond_court / etf | -0.3 % | -15.3 % | -0.00 | 7.9 | 59.4 % | -0.0 % | 3.3 | 0.98 | 24.7 % |
| rebond_court / etf + stop | -0.8 % | -16.3 % | -0.07 | 8.2 | 58.7 % | -0.0 % | 3.1 | 0.95 | 24.1 % |
| rebond_court / actions | +5.4 % | -25.1 % | 0.47 | 16.7 | 60.1 % | +0.1 % | 3.3 | 1.13 | 52.3 % |
| rebond_court / actions + stop | +3.8 % | -29.1 % | 0.36 | 17.0 | 59.8 % | +0.1 % | 3.2 | 1.08 | 51.7 % |
| rebond_court / sp500 | +4.5 % | -39.5 % | 0.33 | 28.2 | 59.5 % | +0.1 % | 3.3 | 1.05 | 88.4 % |
| rebond_court / sp500 + stop | +2.5 % | -40.8 % | 0.23 | 28.9 | 59.1 % | +0.1 % | 3.2 | 1.03 | 86.9 % |
| cassure_courte / etf | -1.2 % | -21.3 % | -0.11 | 9.0 | 43.0 % | -0.0 % | 7.0 | 0.94 | 59.4 % |
| cassure_courte / etf + stop | -1.2 % | -20.8 % | -0.11 | 9.0 | 43.0 % | -0.0 % | 6.9 | 0.94 | 59.2 % |
| cassure_courte / actions | +1.7 % | -53.4 % | 0.19 | 12.4 | 44.1 % | +0.1 % | 7.1 | 1.05 | 83.8 % |
| cassure_courte / actions + stop | +2.0 % | -52.2 % | 0.20 | 12.5 | 43.9 % | +0.1 % | 7.0 | 1.05 | 83.3 % |
| cassure_courte / sp500 | -2.9 % | -76.2 % | -0.03 | 13.8 | 43.0 % | -0.0 % | 7.4 | 0.94 | 96.8 % |
| cassure_courte / sp500 + stop | -4.5 % | -77.0 % | -0.11 | 14.0 | 42.9 % | -0.1 % | 7.3 | 0.91 | 96.2 % |
| cloture_basse / etf | -3.8 % | -41.5 % | -0.47 | 18.0 | 53.2 % | -0.1 % | 2.0 | 0.85 | 34.1 % |
| cloture_basse / etf + stop | -4.7 % | -48.4 % | -0.61 | 18.0 | 53.2 % | -0.1 % | 2.0 | 0.83 | 33.7 % |
| cloture_basse / actions | +1.6 % | -37.8 % | 0.18 | 32.6 | 55.0 % | +0.0 % | 2.1 | 1.02 | 64.5 % |
| cloture_basse / actions + stop | +0.9 % | -42.3 % | 0.14 | 32.7 | 55.0 % | +0.0 % | 2.1 | 1.01 | 63.8 % |
| cloture_basse / sp500 | -2.8 % | -49.9 % | -0.06 | 46.1 | 55.1 % | -0.0 % | 2.1 | 0.98 | 92.2 % |
| cloture_basse / sp500 + stop | -4.8 % | -54.8 % | -0.17 | 46.3 | 55.1 % | -0.0 % | 2.1 | 0.96 | 91.3 % |
| retournement_hebdo / etf | +3.0 % | -17.8 % | 0.33 | 11.3 | 52.8 % | +0.1 % | 4.9 | 1.12 | 52.4 % |
| retournement_hebdo / etf + stop | +2.6 % | -14.8 % | 0.31 | 11.4 | 52.5 % | +0.1 % | 4.7 | 1.10 | 51.0 % |
| retournement_hebdo / actions | +11.4 % | -45.6 % | 0.65 | 18.8 | 53.7 % | +0.3 % | 4.8 | 1.20 | 86.2 % |
| retournement_hebdo / actions + stop | +10.4 % | -49.6 % | 0.62 | 18.8 | 53.6 % | +0.3 % | 4.7 | 1.18 | 84.5 % |
| retournement_hebdo / sp500 | +10.3 % | -58.4 % | 0.50 | 21.4 | 51.6 % | +0.3 % | 4.8 | 1.15 | 98.0 % |
| retournement_hebdo / sp500 + stop | +7.9 % | -58.8 % | 0.42 | 21.4 | 51.6 % | +0.2 % | 4.7 | 1.11 | 96.2 % |
| momentum_hebdo / etf | -1.3 % | -25.3 % | -0.06 | 17.6 | 51.4 % | -0.0 % | 4.8 | 0.96 | 80.7 % |
| momentum_hebdo / etf + stop | -1.5 % | -23.9 % | -0.07 | 17.6 | 51.1 % | -0.0 % | 4.7 | 0.96 | 78.7 % |
| momentum_hebdo / actions | +3.2 % | -51.0 % | 0.26 | 20.8 | 52.0 % | +0.1 % | 4.8 | 1.05 | 95.6 % |
| momentum_hebdo / actions + stop | +6.8 % | -49.4 % | 0.42 | 20.8 | 52.4 % | +0.2 % | 4.7 | 1.11 | 93.1 % |
| momentum_hebdo / sp500 | +7.0 % | -72.1 % | 0.38 | 21.6 | 51.0 % | +0.2 % | 4.8 | 1.08 | 99.1 % |
| momentum_hebdo / sp500 + stop | +3.3 % | -73.9 % | 0.26 | 21.6 | 50.3 % | +0.1 % | 4.7 | 1.04 | 96.3 % |
| tournant_du_mois / spy | -1.7 % | -30.6 % | -0.15 | 1.0 | 54.8 % | -0.1 % | 5.0 | 0.84 | 23.8 % |
| tournant_du_mois / spy + stop | -1.5 % | -30.6 % | -0.12 | 1.0 | 54.8 % | -0.1 % | 4.9 | 0.86 | 23.3 % |

## Période : verification (2019-auj.)

| Stratégie | Rendement / an | Pire baisse | Sharpe | Trades / mois | Réussite | Trade moyen | Jours moyens | Facteur profit | Investi |
|---|---|---|---|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | +16.9 % | -33.7 % | 0.91 | - | - | - | - | - | 100.0 % |
| rebond_court / etf | +1.1 % | -13.8 % | 0.18 | 8.7 | 61.3 % | +0.1 % | 3.2 | 1.07 | 26.8 % |
| rebond_court / etf + stop | +1.6 % | -13.1 % | 0.25 | 9.1 | 61.6 % | +0.1 % | 3.0 | 1.10 | 26.2 % |
| rebond_court / actions | +4.6 % | -24.6 % | 0.34 | 18.5 | 61.0 % | +0.1 % | 3.3 | 1.09 | 58.0 % |
| rebond_court / actions + stop | +2.9 % | -29.2 % | 0.25 | 19.0 | 60.4 % | +0.1 % | 3.2 | 1.05 | 57.0 % |
| rebond_court / sp500 | +10.1 % | -45.5 % | 0.55 | 29.0 | 60.2 % | +0.2 % | 3.3 | 1.08 | 91.7 % |
| rebond_court / sp500 + stop | +11.5 % | -36.4 % | 0.61 | 29.6 | 60.6 % | +0.2 % | 3.2 | 1.09 | 90.3 % |
| cassure_courte / etf | +1.6 % | -12.8 % | 0.22 | 9.7 | 44.5 % | +0.1 % | 6.9 | 1.06 | 64.3 % |
| cassure_courte / etf + stop | +1.6 % | -12.3 % | 0.22 | 9.7 | 44.5 % | +0.1 % | 6.8 | 1.06 | 64.0 % |
| cassure_courte / actions | +8.7 % | -24.5 % | 0.53 | 13.4 | 41.1 % | +0.3 % | 6.9 | 1.12 | 88.2 % |
| cassure_courte / actions + stop | +10.7 % | -24.8 % | 0.63 | 13.5 | 41.4 % | +0.4 % | 6.8 | 1.15 | 87.5 % |
| cassure_courte / sp500 | +10.6 % | -51.6 % | 0.52 | 13.9 | 44.8 % | +0.4 % | 7.4 | 1.16 | 97.7 % |
| cassure_courte / sp500 + stop | +9.7 % | -55.7 % | 0.49 | 14.0 | 44.6 % | +0.4 % | 7.3 | 1.14 | 97.2 % |
| cloture_basse / etf | -2.1 % | -37.3 % | -0.22 | 20.6 | 54.8 % | -0.0 % | 2.0 | 0.94 | 39.7 % |
| cloture_basse / etf + stop | -2.0 % | -38.2 % | -0.20 | 20.6 | 54.8 % | -0.0 % | 2.0 | 0.94 | 39.0 % |
| cloture_basse / actions | -3.4 % | -42.4 % | -0.14 | 35.0 | 54.3 % | -0.0 % | 2.1 | 0.96 | 70.2 % |
| cloture_basse / actions + stop | -3.5 % | -42.8 % | -0.14 | 35.1 | 54.3 % | -0.0 % | 2.1 | 0.96 | 69.5 % |
| cloture_basse / sp500 | -0.3 % | -45.7 % | 0.09 | 47.3 | 56.7 % | +0.0 % | 2.1 | 1.00 | 94.5 % |
| cloture_basse / sp500 + stop | -1.3 % | -49.8 % | 0.04 | 47.5 | 56.5 % | +0.0 % | 2.1 | 0.99 | 93.6 % |
| retournement_hebdo / etf | +2.8 % | -23.7 % | 0.32 | 12.2 | 52.9 % | +0.1 % | 4.8 | 1.09 | 56.0 % |
| retournement_hebdo / etf + stop | +1.6 % | -23.5 % | 0.21 | 12.4 | 52.4 % | +0.1 % | 4.7 | 1.05 | 55.1 % |
| retournement_hebdo / actions | -2.7 % | -46.6 % | -0.01 | 19.4 | 50.4 % | -0.0 % | 4.8 | 0.96 | 89.2 % |
| retournement_hebdo / actions + stop | -2.4 % | -44.6 % | 0.00 | 19.4 | 50.4 % | -0.0 % | 4.7 | 0.96 | 87.3 % |
| retournement_hebdo / sp500 | +26.7 % | -41.7 % | 0.88 | 21.7 | 53.8 % | +0.5 % | 4.8 | 1.19 | 99.5 % |
| retournement_hebdo / sp500 + stop | +24.8 % | -41.2 % | 0.84 | 21.7 | 53.6 % | +0.5 % | 4.7 | 1.18 | 98.1 % |
| momentum_hebdo / etf | -2.9 % | -31.5 % | -0.18 | 18.2 | 52.0 % | -0.1 % | 4.8 | 0.93 | 83.6 % |
| momentum_hebdo / etf + stop | -2.7 % | -39.4 % | -0.17 | 18.3 | 51.6 % | -0.0 % | 4.7 | 0.94 | 81.3 % |
| momentum_hebdo / actions | +7.1 % | -36.0 % | 0.40 | 21.4 | 51.5 % | +0.2 % | 4.8 | 1.08 | 98.0 % |
| momentum_hebdo / actions + stop | +11.9 % | -34.5 % | 0.58 | 21.4 | 52.0 % | +0.3 % | 4.7 | 1.13 | 96.0 % |
| momentum_hebdo / sp500 | +28.8 % | -54.3 % | 0.86 | 21.7 | 53.1 % | +0.6 % | 4.8 | 1.25 | 99.5 % |
| momentum_hebdo / sp500 + stop | +23.2 % | -52.5 % | 0.75 | 21.7 | 52.3 % | +0.5 % | 4.7 | 1.20 | 96.8 % |
| tournant_du_mois / spy | +3.5 % | -16.9 % | 0.43 | 1.0 | 64.2 % | +0.3 % | 5.0 | 1.38 | 24.0 % |
| tournant_du_mois / spy + stop | +2.9 % | -16.1 % | 0.38 | 1.0 | 64.2 % | +0.2 % | 4.7 | 1.29 | 22.8 % |

## Test de résistance : frais doublés, période de vérification

| Stratégie | Rendement / an | Sharpe | Facteur profit |
|---|---|---|---|
| rebond_court / etf | -3.1 % | -0.37 | 0.81 |
| rebond_court / etf + stop | -2.8 % | -0.34 | 0.85 |
| rebond_court / actions | -4.3 % | -0.16 | 0.92 |
| rebond_court / actions + stop | -6.1 % | -0.27 | 0.90 |
| rebond_court / sp500 | -4.2 % | -0.08 | 0.96 |
| rebond_court / sp500 + stop | -3.3 % | -0.04 | 0.97 |
| cassure_courte / etf | -3.0 % | -0.27 | 0.89 |
| cassure_courte / etf + stop | -3.0 % | -0.28 | 0.89 |
| cassure_courte / actions | +2.0 % | 0.20 | 1.02 |
| cassure_courte / actions + stop | +3.8 % | 0.29 | 1.05 |
| cassure_courte / sp500 | +3.6 % | 0.27 | 1.05 |
| cassure_courte / sp500 + stop | +2.7 % | 0.23 | 1.03 |
| cloture_basse / etf | -11.3 % | -1.42 | 0.69 |
| cloture_basse / etf + stop | -11.2 % | -1.41 | 0.69 |
| cloture_basse / actions | -18.4 % | -1.18 | 0.77 |
| cloture_basse / actions + stop | -18.5 % | -1.21 | 0.77 |
| cloture_basse / sp500 | -20.6 % | -0.97 | 0.84 |
| cloture_basse / sp500 + stop | -20.3 % | -1.00 | 0.83 |
| retournement_hebdo / etf | -3.0 % | -0.24 | 0.90 |
| retournement_hebdo / etf + stop | -4.2 % | -0.36 | 0.87 |
| retournement_hebdo / actions | -11.4 % | -0.42 | 0.87 |
| retournement_hebdo / actions + stop | -11.1 % | -0.41 | 0.87 |
| retournement_hebdo / sp500 | +14.2 % | 0.57 | 1.10 |
| retournement_hebdo / sp500 + stop | +12.5 % | 0.52 | 1.09 |
| momentum_hebdo / etf | -11.1 % | -0.89 | 0.75 |
| momentum_hebdo / etf + stop | -10.9 % | -0.91 | 0.77 |
| momentum_hebdo / actions | -3.4 % | -0.01 | 0.96 |
| momentum_hebdo / actions + stop | +0.9 % | 0.16 | 1.01 |
| momentum_hebdo / sp500 | +16.1 % | 0.59 | 1.15 |
| momentum_hebdo / sp500 + stop | +11.1 % | 0.47 | 1.10 |
| tournant_du_mois / spy | +1.0 % | 0.16 | 1.09 |
| tournant_du_mois / spy + stop | +0.4 % | 0.09 | 1.02 |

## Verdict (critères fixés à l'avance, période de vérification)

**momentum_hebdo / sp500 : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ✅ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / sp500 : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / sp500 + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / sp500 + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ✅ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / actions + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / actions + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / actions : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**tournant_du_mois / spy : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ✅ Facteur de profit d'au moins 1,2 (gains / pertes)
- ❌ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**tournant_du_mois / spy + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ✅ Facteur de profit d'au moins 1,2 (gains / pertes)
- ❌ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / actions : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / etf : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / actions + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / etf + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / sp500 : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / sp500 : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / sp500 + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / etf + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / etf + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / etf : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / etf : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / actions + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / actions : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / sp500 + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / actions : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / sp500 : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / sp500 + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / actions : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / actions + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / etf + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / etf : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / etf + stop : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / etf : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

Un backtest réussi n'est pas une promesse : c'est le droit de passer à la simulation en temps réel (compte fictif), qui seule dira si la stratégie tient.
