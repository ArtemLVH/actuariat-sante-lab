# Rapport de validation — explicabilité du modèle de rachat

*Généré automatiquement — pipeline `actuariat-sante-lab` × `metaquery_actuary`*

## 1. Traçabilité des données (manifeste MetaQuery)
- Dataset : `data_rachats.csv` — 12000 lignes — SHA-256 `7914716c2b393d03…`
- Horodatage : 2026-07-13 15:12:05 — producteur : metaquery_bridge v0.1 (mode autonome)
- Requête exécutée jointe au manifeste (`outputs/manifest.json`).

## 2. Performance du modèle
- AUC train : **0.688** — AUC test : **0.682**
- Lecture validateur : ✅ écart train/test contenu

## 3. Importance globale (SHAP) vs attentes métier
| Rang SHAP | Variable | |SHAP| moyen | Attente métier | Verdict |
|---|---|---|---|---|
| 1 | `ecart_taux` | 0.4118 | moteur n°1 (rachat dynamique : écart taux marché − servi) | ✅ |
| 2 | `age` | 0.1785 | effet réel modéré (départs en retraite 62+) | — |
| 3 | `anciennete` | 0.0656 | moteur n°2 (pic fiscal à 8 ans) | — |
| 4 | `encours` | 0.0586 | aucun effet codé | — |
| 5 | `csp_code` | 0.0254 | LEURRE — aucun effet ; le modèle ne doit PAS s'y accrocher | ⚠ leurre trop haut ! |
| 6 | `region_code` | 0.0227 | LEURRE — aucun effet ; idem | ✅ |
| 7 | `tmg` | 0.0057 | effet faible (protecteur) | — |

**Test des leurres** : csp_code en position 5, region_code en position 6 → ⚠ ALERTE : le modèle exploite du bruit — à challenger

## 4. Explications locales — SHAP vs LIME sur les mêmes contrats
### Contrat A (proba max) — proba de rachat prédite : 23.6%
- Caractéristiques : {'age': 85.0, 'anciennete': 7.0, 'encours': 37550.46, 'tmg': 1.0, 'ecart_taux': 2.45, 'csp_code': 2.0, 'region_code': 10.0}
- LIME top-5, tirage 1 : ['ecart_taux', 'age', 'anciennete', 'encours', 'csp_code']
- LIME top-5, tirage 2 : ['ecart_taux', 'age', 'anciennete', 'encours', 'csp_code']
- **Stabilité LIME (Jaccard tirage1/tirage2) : 1.00** — ✅ stable
- Waterfall SHAP : `outputs/shap_waterfall_A.png`

### Contrat B (ancienneté = 8 ans) — proba de rachat prédite : 22.7%
- Caractéristiques : {'age': 82.0, 'anciennete': 8.0, 'encours': 20910.1, 'tmg': 1.5, 'ecart_taux': 2.4, 'csp_code': 5.0, 'region_code': 10.0}
- LIME top-5, tirage 1 : ['ecart_taux', 'age', 'anciennete', 'region_code', 'csp_code']
- LIME top-5, tirage 2 : ['ecart_taux', 'age', 'anciennete', 'csp_code', 'region_code']
- **Stabilité LIME (Jaccard tirage1/tirage2) : 1.00** — ✅ stable
- Waterfall SHAP : `outputs/shap_waterfall_B.png`

## 5. Conclusion de validation (2e ligne)
- Les moteurs identifiés par SHAP sont confrontés aux attentes métier ci-dessus ; toute divergence (leurre haut placé, moteur attendu absent) constitue un point de challenge à documenter.
- LIME est utilisé en contre-expertise locale ; son instabilité éventuelle est mesurée, pas ignorée.
- Chaque explication référence un dataset tracé (manifeste, hash) : l'explication est auditables de bout en bout.