# Pack XAI — Explicabilité & validation (SHAP × LIME × MetaQuery)

**Objectif du jour** : connecter tes deux repos — un pipeline de validation de bout en bout :
extraction TRACÉE (manifeste MetaQuery) → modèle de rachat (XGBoost) → explications
(SHAP global + local, LIME en contre-expertise) → **rapport de validation auto-généré**.

## L'idée qui rend ce projet original
Les données sont synthétiques avec une mécanique de rachat **CONNUE** (écart de taux,
pic fiscal à 8 ans, retraite 62+) + **deux variables LEURRES** sans aucun effet
(csp_code, region_code). L'explicabilité devient donc un **outil de VALIDATION** :
SHAP retrouve-t-il les vrais moteurs ? Laisse-t-il les leurres en bas ?
→ C'est exactement le regard 2e ligne appliqué au ML.

## Ordre de marche (timebox : fin à 18h30 MAX)
1. `python3 gen_data.py` — le portefeuille (déjà fait ✅)
2. `python3 metaquery_bridge.py` — le manifeste de traçabilité (déjà fait ✅)
3. **`SQUELETTE_xai.py` — TON code, 4 TODO** : entraînement+AUC → SHAP (beeswarm + 2
   waterfalls) → LIME (2 individus × 2 tirages) → rapport via `report_engine.build_report`.
   Blocage > 15 min → `SOLUTIONS_xai.py` (référence complète, testée).
4. Lis `outputs/rapport_validation_explicabilite.md` et réponds aux 3 questions du squelette.

## ⚠ Le twist (et c'est voulu) : la v1 a DEUX anomalies réelles
Le run de référence détecte :
- **Surapprentissage** : AUC train 0.88 vs test 0.64 (événement rare ~7,7 %, modèle trop riche).
- **Un leurre qui grimpe** : region_code passe 5e — le modèle capte du bruit.

**Exercice de validateur (le vrai livrable)** : produis une v2 remédiée —
`max_depth=2`, `n_estimators=100`, ajoute `min_child_weight=20` — relance, et constate :
l'écart train/test se referme, les leurres redescendent, le test du rapport repasse ✅.
Ton git aura alors DEUX commits : « v1 : anomalies détectées » → « v2 : remédiation » —
c'est un cycle de validation complet, documenté. Aucun portfolio étudiant ne montre ça.

## Ce que ça devient sur GitHub
Nouveau module de `actuariat-sante-lab` (ex. `validation_explicabilite/`), avec le rapport
et les figures commités. Le README du repo gagne une ligne : « pipeline d'explicabilité
validé bout-en-bout, données tracées par manifeste (metaquery_actuary) ».

## La phrase d'entretien (dès jeudi si « projets perso » sort)
« Je connecte mes deux repos : un pipeline qui entraîne un modèle de rachat, l'explique
avec SHAP et LIME, compare les deux, teste des variables leurres, et génère un rapport de
validation qui cite le manifeste de traçabilité des données. La v1 a détecté du
surapprentissage et un leurre qui montait — la v2 documente la remédiation. »
