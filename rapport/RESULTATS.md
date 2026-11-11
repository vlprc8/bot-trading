# Résultats du backtest

Généré le 2026-11-11. Données : Yahoo Finance, cours journaliers ajustés.

Règles de simulation : capital de départ 1 000 $, décision le soir à la clôture, ordre à l'ouverture du lendemain, 5 positions au plus (environ 1/5 du capital chacune), frais 0.10 % par achat et par vente, fractions d'actions, pas de levier.

Variantes « + SL/TP » : stop loss à 2 x ATR(14) sous le prix d'achat, take profit à 3 x ATR(14) au-dessus, actifs dès le lendemain de l'achat ; les sorties de la stratégie restent en place.

![courbes](courbes.png)

## Classement (période de vérification, 2019 à aujourd'hui)

| Stratégie | Critères réussis | Rendement / an | Pire baisse | Sharpe | Trades / mois |
|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | - | +16.9 % | -33.7 % | 0.91 | - |
| cassure_courte / actions | 3 / 6 | +8.7 % | -24.5 % | 0.53 | 13.4 |
| tournant_du_mois / spy | 3 / 6 | +3.5 % | -16.9 % | 0.43 | 1.0 |
| rebond_court / actions | 3 / 6 | +4.6 % | -24.6 % | 0.34 | 18.5 |
| retournement_hebdo / etf | 3 / 6 | +2.8 % | -23.7 % | 0.32 | 12.2 |
| momentum_hebdo / actions + SL/TP | 2 / 6 | +15.4 % | -32.3 % | 0.72 | 21.4 |
| tournant_du_mois / spy + SL/TP | 2 / 6 | +2.3 % | -15.5 % | 0.33 | 1.0 |
| cassure_courte / actions + SL/TP | 2 / 6 | +3.6 % | -27.7 % | 0.29 | 15.2 |
| rebond_court / etf + SL/TP | 2 / 6 | +1.5 % | -13.9 % | 0.25 | 9.7 |
| cassure_courte / etf | 2 / 6 | +1.6 % | -12.8 % | 0.22 | 9.7 |
| retournement_hebdo / etf + SL/TP | 2 / 6 | +1.4 % | -18.8 % | 0.19 | 12.7 |
| rebond_court / etf | 2 / 6 | +1.1 % | -13.8 % | 0.18 | 8.7 |
| cassure_courte / etf + SL/TP | 2 / 6 | +1.2 % | -12.1 % | 0.18 | 10.8 |
| rebond_court / actions + SL/TP | 2 / 6 | +1.5 % | -29.3 % | 0.17 | 19.8 |
| retournement_hebdo / actions + SL/TP | 2 / 6 | -1.9 % | -40.7 % | 0.02 | 19.5 |
| momentum_hebdo / etf + SL/TP | 2 / 6 | -0.6 % | -26.6 % | -0.00 | 18.6 |
| retournement_hebdo / actions | 2 / 6 | -2.7 % | -46.6 % | -0.01 | 19.4 |
| momentum_hebdo / actions | 1 / 6 | +7.0 % | -36.0 % | 0.40 | 21.4 |
| cloture_basse / actions | 1 / 6 | -3.4 % | -42.4 % | -0.14 | 35.0 |
| cloture_basse / actions + SL/TP | 1 / 6 | -3.6 % | -43.4 % | -0.16 | 35.5 |
| momentum_hebdo / etf | 1 / 6 | -2.9 % | -31.5 % | -0.18 | 18.2 |
| cloture_basse / etf | 1 / 6 | -2.1 % | -37.3 % | -0.22 | 20.6 |
| cloture_basse / etf + SL/TP | 1 / 6 | -2.3 % | -38.2 % | -0.26 | 20.8 |

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
| rebond_court / etf | +0.2 % | -23.7 % | 0.07 | 8.2 | 60.3 % | +0.0 % | 3.3 | 1.02 | 25.5 % |
| rebond_court / etf + SL/TP | +0.0 % | -19.1 % | 0.04 | 9.0 | 59.3 % | +0.0 % | 2.8 | 1.00 | 24.0 % |
| rebond_court / actions | +5.1 % | -38.8 % | 0.41 | 17.4 | 60.5 % | +0.1 % | 3.3 | 1.11 | 54.4 % |
| rebond_court / actions + SL/TP | +1.7 % | -42.1 % | 0.19 | 18.7 | 59.8 % | +0.1 % | 2.9 | 1.03 | 51.8 % |
| cassure_courte / etf | -0.1 % | -21.3 % | 0.03 | 9.3 | 43.6 % | +0.0 % | 6.9 | 0.99 | 61.3 % |
| cassure_courte / etf + SL/TP | -0.7 % | -27.6 % | -0.04 | 10.2 | 43.3 % | -0.0 % | 6.0 | 0.97 | 58.3 % |
| cassure_courte / actions | +4.3 % | -53.4 % | 0.33 | 12.8 | 42.9 % | +0.2 % | 7.0 | 1.09 | 85.4 % |
| cassure_courte / actions + SL/TP | +2.7 % | -40.7 % | 0.25 | 14.3 | 43.3 % | +0.1 % | 5.9 | 1.04 | 80.9 % |
| cloture_basse / etf | -3.2 % | -52.2 % | -0.37 | 18.9 | 53.9 % | -0.1 % | 2.0 | 0.88 | 36.2 % |
| cloture_basse / etf + SL/TP | -4.0 % | -58.6 % | -0.51 | 19.2 | 53.9 % | -0.1 % | 1.9 | 0.86 | 34.5 % |
| cloture_basse / actions | -0.3 % | -55.7 % | 0.06 | 33.5 | 54.7 % | +0.0 % | 2.1 | 1.00 | 66.7 % |
| cloture_basse / actions + SL/TP | -1.0 % | -53.6 % | 0.00 | 34.0 | 54.9 % | -0.0 % | 2.0 | 0.99 | 64.1 % |
| retournement_hebdo / etf | +2.9 % | -23.7 % | 0.33 | 11.6 | 52.8 % | +0.1 % | 4.8 | 1.11 | 53.7 % |
| retournement_hebdo / etf + SL/TP | +1.9 % | -18.8 % | 0.25 | 12.1 | 51.6 % | +0.1 % | 4.3 | 1.06 | 49.0 % |
| retournement_hebdo / actions | +5.8 % | -46.6 % | 0.38 | 19.0 | 52.4 % | +0.2 % | 4.8 | 1.05 | 87.3 % |
| retournement_hebdo / actions + SL/TP | +3.0 % | -48.0 % | 0.25 | 19.1 | 52.0 % | +0.1 % | 4.4 | 1.03 | 79.6 % |
| momentum_hebdo / etf | -2.0 % | -45.1 % | -0.11 | 17.8 | 51.6 % | -0.0 % | 4.8 | 0.95 | 81.8 % |
| momentum_hebdo / etf + SL/TP | -1.5 % | -40.8 % | -0.09 | 18.1 | 51.0 % | -0.0 % | 4.3 | 0.96 | 73.7 % |
| momentum_hebdo / actions | +4.5 % | -51.0 % | 0.31 | 21.0 | 51.8 % | +0.1 % | 4.8 | 1.06 | 96.5 % |
| momentum_hebdo / actions + SL/TP | +7.8 % | -53.3 % | 0.46 | 21.1 | 51.8 % | +0.2 % | 4.3 | 1.12 | 86.6 % |
| tournant_du_mois / spy | +0.2 % | -30.6 % | 0.07 | 1.0 | 58.4 % | +0.0 % | 5.0 | 1.02 | 23.9 % |
| tournant_du_mois / spy + SL/TP | -0.2 % | -25.1 % | 0.02 | 1.0 | 56.8 % | +0.0 % | 4.4 | 0.97 | 20.9 % |

## Période : reglage (2006-2018)

| Stratégie | Rendement / an | Pire baisse | Sharpe | Trades / mois | Réussite | Trade moyen | Jours moyens | Facteur profit | Investi |
|---|---|---|---|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | +7.5 % | -55.2 % | 0.48 | - | - | - | - | - | 100.0 % |
| rebond_court / etf | -0.3 % | -15.3 % | -0.00 | 7.9 | 59.5 % | -0.0 % | 3.3 | 0.98 | 24.7 % |
| rebond_court / etf + SL/TP | -0.8 % | -15.2 % | -0.09 | 8.7 | 58.5 % | -0.0 % | 2.8 | 0.95 | 23.2 % |
| rebond_court / actions | +5.4 % | -25.2 % | 0.47 | 16.7 | 60.1 % | +0.1 % | 3.3 | 1.13 | 52.3 % |
| rebond_court / actions + SL/TP | +1.9 % | -27.9 % | 0.21 | 18.0 | 59.8 % | +0.1 % | 2.9 | 1.04 | 49.7 % |
| cassure_courte / etf | -1.2 % | -21.3 % | -0.11 | 9.0 | 43.0 % | -0.0 % | 7.0 | 0.94 | 59.4 % |
| cassure_courte / etf + SL/TP | -1.9 % | -27.6 % | -0.20 | 9.8 | 42.6 % | -0.1 % | 6.1 | 0.92 | 56.9 % |
| cassure_courte / actions | +1.7 % | -53.4 % | 0.19 | 12.4 | 44.1 % | +0.1 % | 7.1 | 1.05 | 83.8 % |
| cassure_courte / actions + SL/TP | +2.2 % | -40.7 % | 0.22 | 13.8 | 44.3 % | +0.1 % | 6.1 | 1.05 | 79.9 % |
| cloture_basse / etf | -3.8 % | -41.6 % | -0.47 | 18.0 | 53.2 % | -0.1 % | 2.0 | 0.85 | 34.2 % |
| cloture_basse / etf + SL/TP | -5.0 % | -49.4 % | -0.66 | 18.3 | 53.3 % | -0.1 % | 1.9 | 0.82 | 32.6 % |
| cloture_basse / actions | +1.6 % | -37.8 % | 0.18 | 32.6 | 55.0 % | +0.0 % | 2.1 | 1.02 | 64.5 % |
| cloture_basse / actions + SL/TP | +0.6 % | -36.4 % | 0.11 | 33.1 | 55.2 % | +0.0 % | 2.0 | 1.01 | 62.0 % |
| retournement_hebdo / etf | +3.0 % | -17.8 % | 0.33 | 11.3 | 52.8 % | +0.1 % | 4.9 | 1.12 | 52.4 % |
| retournement_hebdo / etf + SL/TP | +2.3 % | -17.0 % | 0.28 | 11.7 | 51.8 % | +0.1 % | 4.3 | 1.08 | 47.7 % |
| retournement_hebdo / actions | +11.4 % | -45.6 % | 0.65 | 18.8 | 53.7 % | +0.3 % | 4.8 | 1.20 | 86.2 % |
| retournement_hebdo / actions + SL/TP | +6.1 % | -48.0 % | 0.42 | 18.9 | 53.2 % | +0.2 % | 4.4 | 1.10 | 78.4 % |
| momentum_hebdo / etf | -1.3 % | -25.3 % | -0.06 | 17.6 | 51.4 % | -0.0 % | 4.8 | 0.96 | 80.7 % |
| momentum_hebdo / etf + SL/TP | -2.0 % | -29.9 % | -0.14 | 17.8 | 50.6 % | -0.0 % | 4.3 | 0.95 | 73.2 % |
| momentum_hebdo / actions | +3.2 % | -51.0 % | 0.26 | 20.8 | 52.0 % | +0.1 % | 4.8 | 1.05 | 95.6 % |
| momentum_hebdo / actions + SL/TP | +3.4 % | -53.3 % | 0.27 | 20.9 | 51.7 % | +0.1 % | 4.3 | 1.05 | 86.1 % |
| tournant_du_mois / spy | -1.7 % | -30.6 % | -0.15 | 1.0 | 54.8 % | -0.1 % | 5.0 | 0.84 | 23.8 % |
| tournant_du_mois / spy + SL/TP | -1.6 % | -25.1 % | -0.15 | 1.0 | 53.5 % | -0.1 % | 4.4 | 0.85 | 21.1 % |

## Période : verification (2019-auj.)

| Stratégie | Rendement / an | Pire baisse | Sharpe | Trades / mois | Réussite | Trade moyen | Jours moyens | Facteur profit | Investi |
|---|---|---|---|---|---|---|---|---|---|
| REFERENCE (acheter SPY et garder) | +16.9 % | -33.7 % | 0.91 | - | - | - | - | - | 100.0 % |
| rebond_court / etf | +1.1 % | -13.8 % | 0.18 | 8.7 | 61.3 % | +0.1 % | 3.2 | 1.08 | 26.8 % |
| rebond_court / etf + SL/TP | +1.5 % | -13.9 % | 0.25 | 9.7 | 60.5 % | +0.1 % | 2.7 | 1.09 | 25.2 % |
| rebond_court / actions | +4.6 % | -24.6 % | 0.34 | 18.5 | 61.0 % | +0.1 % | 3.3 | 1.09 | 58.0 % |
| rebond_court / actions + SL/TP | +1.5 % | -29.3 % | 0.17 | 19.8 | 59.8 % | +0.1 % | 2.9 | 1.02 | 55.2 % |
| cassure_courte / etf | +1.6 % | -12.8 % | 0.22 | 9.7 | 44.5 % | +0.1 % | 6.9 | 1.06 | 64.3 % |
| cassure_courte / etf + SL/TP | +1.2 % | -12.1 % | 0.18 | 10.8 | 44.2 % | +0.1 % | 5.9 | 1.05 | 60.7 % |
| cassure_courte / actions | +8.7 % | -24.5 % | 0.53 | 13.4 | 41.1 % | +0.3 % | 6.9 | 1.12 | 88.2 % |
| cassure_courte / actions + SL/TP | +3.6 % | -27.7 % | 0.29 | 15.2 | 41.8 % | +0.1 % | 5.7 | 1.04 | 82.6 % |
| cloture_basse / etf | -2.1 % | -37.3 % | -0.22 | 20.6 | 54.8 % | -0.0 % | 2.0 | 0.94 | 39.7 % |
| cloture_basse / etf + SL/TP | -2.3 % | -38.2 % | -0.26 | 20.8 | 54.7 % | -0.0 % | 1.9 | 0.93 | 37.7 % |
| cloture_basse / actions | -3.4 % | -42.4 % | -0.14 | 35.0 | 54.3 % | -0.0 % | 2.1 | 0.96 | 70.2 % |
| cloture_basse / actions + SL/TP | -3.6 % | -43.4 % | -0.16 | 35.5 | 54.3 % | -0.0 % | 2.0 | 0.96 | 67.5 % |
| retournement_hebdo / etf | +2.8 % | -23.7 % | 0.32 | 12.2 | 52.9 % | +0.1 % | 4.8 | 1.09 | 56.0 % |
| retournement_hebdo / etf + SL/TP | +1.4 % | -18.8 % | 0.19 | 12.7 | 51.4 % | +0.1 % | 4.2 | 1.04 | 51.3 % |
| retournement_hebdo / actions | -2.7 % | -46.6 % | -0.01 | 19.4 | 50.4 % | -0.0 % | 4.8 | 0.96 | 89.2 % |
| retournement_hebdo / actions + SL/TP | -1.9 % | -40.7 % | 0.02 | 19.5 | 50.1 % | -0.0 % | 4.4 | 0.97 | 81.5 % |
| momentum_hebdo / etf | -2.9 % | -31.5 % | -0.18 | 18.2 | 52.0 % | -0.1 % | 4.8 | 0.93 | 83.6 % |
| momentum_hebdo / etf + SL/TP | -0.6 % | -26.6 % | -0.00 | 18.6 | 51.6 % | -0.0 % | 4.2 | 0.98 | 74.4 % |
| momentum_hebdo / actions | +7.0 % | -36.0 % | 0.40 | 21.4 | 51.5 % | +0.2 % | 4.8 | 1.08 | 98.0 % |
| momentum_hebdo / actions + SL/TP | +15.4 % | -32.3 % | 0.72 | 21.4 | 52.0 % | +0.3 % | 4.3 | 1.15 | 87.4 % |
| tournant_du_mois / spy | +3.5 % | -16.9 % | 0.43 | 1.0 | 64.2 % | +0.3 % | 5.0 | 1.38 | 24.0 % |
| tournant_du_mois / spy + SL/TP | +2.3 % | -15.5 % | 0.33 | 1.0 | 62.1 % | +0.2 % | 4.3 | 1.22 | 20.4 % |

## Test de résistance : frais doublés, période de vérification

| Stratégie | Rendement / an | Sharpe | Facteur profit |
|---|---|---|---|
| rebond_court / etf | -3.0 % | -0.37 | 0.81 |
| rebond_court / etf + SL/TP | -3.1 % | -0.41 | 0.84 |
| rebond_court / actions | -4.3 % | -0.16 | 0.92 |
| rebond_court / actions + SL/TP | -7.7 % | -0.41 | 0.87 |
| cassure_courte / etf | -3.0 % | -0.28 | 0.89 |
| cassure_courte / etf + SL/TP | -3.9 % | -0.39 | 0.87 |
| cassure_courte / actions | +2.0 % | 0.20 | 1.02 |
| cassure_courte / actions + SL/TP | -3.6 % | -0.12 | 0.95 |
| cloture_basse / etf | -11.3 % | -1.42 | 0.69 |
| cloture_basse / etf + SL/TP | -11.6 % | -1.54 | 0.69 |
| cloture_basse / actions | -18.4 % | -1.19 | 0.77 |
| cloture_basse / actions + SL/TP | -18.8 % | -1.26 | 0.78 |
| retournement_hebdo / etf | -3.0 % | -0.24 | 0.90 |
| retournement_hebdo / etf + SL/TP | -4.6 % | -0.43 | 0.86 |
| retournement_hebdo / actions | -11.4 % | -0.42 | 0.87 |
| retournement_hebdo / actions + SL/TP | -10.7 % | -0.42 | 0.87 |
| momentum_hebdo / etf | -11.1 % | -0.89 | 0.75 |
| momentum_hebdo / etf + SL/TP | -9.1 % | -0.80 | 0.80 |
| momentum_hebdo / actions | -3.4 % | -0.01 | 0.96 |
| momentum_hebdo / actions + SL/TP | +4.1 % | 0.29 | 1.04 |
| tournant_du_mois / spy | +1.0 % | 0.16 | 1.09 |
| tournant_du_mois / spy + SL/TP | -0.2 % | 0.02 | 0.97 |

## Verdict (critères fixés à l'avance, période de vérification)

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

**momentum_hebdo / actions + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ✅ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**tournant_du_mois / spy + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ✅ Facteur de profit d'au moins 1,2 (gains / pertes)
- ❌ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cassure_courte / actions + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / etf + SL/TP : ne passe pas**
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

**retournement_hebdo / etf + SL/TP : ne passe pas**
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

**cassure_courte / etf + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**rebond_court / actions + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / actions + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / etf + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ✅ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**retournement_hebdo / actions : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ✅ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**momentum_hebdo / actions : ne passe pas**
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

**cloture_basse / actions + SL/TP : ne passe pas**
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

**cloture_basse / etf : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

**cloture_basse / etf + SL/TP : ne passe pas**
- ❌ Sharpe meilleur que la référence (plus de gain pour le risque pris)
- ❌ Pire baisse moins grave que -30 %
- ❌ Facteur de profit d'au moins 1,2 (gains / pertes)
- ✅ Au moins 100 trades (sinon c'est peut-être de la chance)
- ❌ A aussi marché avant, sur 2006-2018 (Sharpe d'au moins 0,3)
- ❌ Reste gagnante avec des frais doublés (rendement annuel positif sur la vérification)

Un backtest réussi n'est pas une promesse : c'est le droit de passer à la simulation en temps réel (compte fictif), qui seule dira si la stratégie tient.
