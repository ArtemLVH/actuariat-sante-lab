# Validation & explicabilité d'un modèle de rachat (XAI)

Pipeline de validation de bout en bout : données tracées par manifeste → modèle
XGBoost → explications SHAP & LIME croisées → rapport de validation auto-généré.

## Démarche
- Portefeuille synthétique (12 000 contrats) à mécanique de rachat **connue**
  (écart de taux, pic fiscal à 8 ans, départs en retraite) + **deux variables
  leurres** sans aucun effet (contrôle négatif).
- L'explicabilité est utilisée comme **outil de validation** : le modèle
  retrouve-t-il les vrais moteurs ? Ignore-t-il le bruit ?
- Chaque explication référence un **manifeste de traçabilité** (requête exécutée,
  dictionnaire, hash SHA-256) — pont avec le projet `metaquery_actuary`.

## Résultats — cycle v1 → v2
| | v1 (300 arbres, prof. 4) | v2 (100 arbres, prof. 2, mcw 20) |
|---|---|---|
| AUC train / test | 0.878 / 0.644 | 0.688 / 0.682 |
| Écart train-test | 0.234 (surapprentissage) | 0.006 |
| Importance des leurres | 0.097 / 0.084 (rangs 5-6) | 0.025 / 0.023 (÷4) |

La v1 détecte un surapprentissage massif et des leurres captés par le modèle ;
la v2 remédie par contrainte de complexité — l'AUC out-of-sample **monte** (+0.04)
avec un modèle plus simple, et le moteur principal (`ecart_taux`) reste intact.
LIME en contre-expertise : top-3 identique à SHAP, stabilité mesurée
(Jaccard 1.00, deux tirages sur deux contrats).

Enseignement : **un test automatisé alerte, le validateur arbitre** — la règle de
rang signale encore les leurres en v2, la lecture des magnitudes conclut au bruit
résiduel acceptable.

## Exécution
python gen_data.py
python metaquery_bridge.py
python pipeline_xai.py
Sorties : `outputs/rapport_validation_explicabilite.md` + figures SHAP
(beeswarm global, waterfalls individuels).

## Fichiers
- `gen_data.py` — génération du portefeuille synthétique
- `metaquery_bridge.py` — manifeste de traçabilité
- `pipeline_xai.py` — entraînement, SHAP, LIME, comparaison
- `report_engine.py` — génération du rapport de validation
- `outputs/` — rapport, manifeste, figures
