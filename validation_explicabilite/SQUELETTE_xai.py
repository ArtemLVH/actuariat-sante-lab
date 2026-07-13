# -*- coding: utf-8 -*-
"""SQUELETTE — pipeline explicabilité & validation (TON code : 4 TODO).
Ordre d'exécution : gen_data.py → metaquery_bridge.py → CE FICHIER.
Objectif final : outputs/rapport_validation_explicabilite.md + 3 figures.
Si tu bloques > 15 min sur un TODO : SOLUTIONS_xai.py contient la référence."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEATURES = ["age", "anciennete", "encours", "tmg", "ecart_taux", "csp_code", "region_code"]
# Ce que le MÉTIER attend (la mécanique codée dans gen_data) — le rapport comparera à SHAP :
ATTENTES_METIER = {
    "ecart_taux": "moteur n°1 (rachat dynamique : écart taux marché − servi)",
    "anciennete": "moteur n°2 (pic fiscal à 8 ans)",
    "age":        "effet réel modéré (départs en retraite 62+)",
    "tmg":        "effet faible (protecteur)",
    "encours":    "aucun effet codé",
    "csp_code":   "LEURRE — aucun effet ; le modèle ne doit PAS s'y accrocher",
    "region_code":"LEURRE — aucun effet ; idem",
}

df = pd.read_csv("data_rachats.csv")
X, y = df[FEATURES], df["rachat"]

# ---------------------------------------------------------------- TODO 1
# Entraîne un XGBClassifier (max_depth=4, n_estimators=300, learning_rate=0.05,
# subsample=0.9) avec un split train/test 80/20 (random_state=0, stratify=y).
# Calcule l'AUC train ET test (sklearn.metrics.roc_auc_score sur predict_proba).
# → model, X_train, X_test, auc_train, auc_test
# Piège de validateur : si auc_train >> auc_test, dis-le dans le rapport (surapprentissage).
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
model = XGBClassifier(max_depth=2, n_estimators=100, learning_rate=0.05,
                      subsample=0.9, min_child_weight=20,
                      eval_metric="logloss", random_state=0)
model.fit(X_train, y_train)
auc_train = roc_auc_score(y_train, model.predict_proba(X_train)[:, 1])
auc_test  = roc_auc_score(y_test,  model.predict_proba(X_test)[:, 1])
print(f"AUC train {auc_train:.3f} | AUC test {auc_test:.3f}")

# ---------------------------------------------------------------- TODO 2
# SHAP : shap.TreeExplainer(model) → shap_values sur X_test.
# a) beeswarm global → outputs/shap_beeswarm.png
# b) importance globale = moyenne des |SHAP| par variable → Series triée `imp_shap`
# c) 2 waterfalls INDIVIDUELS → outputs/shap_waterfall_A.png / _B.png
#    Choisis A = le contrat de X_test avec la proba prédite la PLUS HAUTE,
#            B = un contrat avec anciennete == 8 (le pic fiscal en action).
# → imp_shap (Series), idx_A, idx_B

import shap

# L'explicateur : décompose chaque prédiction en contributions par variable
explainer = shap.TreeExplainer(model)
sv = explainer(X_test)          # valeurs SHAP de tous les contrats de test

# a) Vue globale : le beeswarm (chaque point = un contrat)
plt.figure()
shap.plots.beeswarm(sv, max_display=7, show=False)
plt.title("SHAP — qui pilote le rachat ?", loc="left")
plt.tight_layout()
plt.savefig("outputs/shap_beeswarm.png", dpi=130, bbox_inches="tight")
plt.close()

# b) Importance globale = moyenne des |SHAP| par variable
imp_shap = pd.Series(np.abs(sv.values).mean(axis=0), index=FEATURES).sort_values(ascending=False)
print(imp_shap)

# c) Deux contrats : A = proba max, B = ancienneté 8 ans (le pic fiscal)
proba = model.predict_proba(X_test)[:, 1]
idx_A = X_test.index[int(np.argmax(proba))]
cand_B = X_test[X_test.anciennete == 8]
idx_B = cand_B.index[int(np.argmax(model.predict_proba(cand_B)[:, 1]))]
for key, idx in [("A", idx_A), ("B", idx_B)]:
    pos = X_test.index.get_loc(idx)
    plt.figure()
    shap.plots.waterfall(sv[pos], max_display=7, show=False)
    plt.title(f"Contrat {key} — pourquoi cette proba ?", loc="left")
    plt.tight_layout()
    plt.savefig(f"outputs/shap_waterfall_{key}.png", dpi=130, bbox_inches="tight")
    plt.close()
print("figures SHAP écrites | A =", idx_A, "| B =", idx_B)

# ---------------------------------------------------------------- TODO 3
# LIME : lime.lime_tabular.LimeTabularExplainer(X_train.values,
#        feature_names=FEATURES, class_names=["reste","rachat"], mode="classification",
#        discretize_continuous=True)
# Explique les MÊMES individus A et B (model.predict_proba), num_features=5,
# et fais-le DEUX FOIS par individu avec des graines différentes (random_state du
# explainer ou np.random.seed) pour mesurer la STABILITÉ.
# → lime_top : dict {("A",1): [5 features], ("A",2): [...], ("B",1): ..., ("B",2): ...}

from lime.lime_tabular import LimeTabularExplainer

lime_top = {}
for seed in (1, 2):
    expl = LimeTabularExplainer(X_train.values, feature_names=FEATURES,
                                class_names=["reste", "rachat"], mode="classification",
                                discretize_continuous=True, random_state=seed)
    for key, idx in [("A", idx_A), ("B", idx_B)]:
        e = expl.explain_instance(X_test.loc[idx].values, model.predict_proba, num_features=5)
        feats = []
        for cond, _w in e.as_list():
            f = next((f for f in sorted(FEATURES, key=len, reverse=True) if f in cond), cond)
            feats.append(f)
        lime_top[(key, seed)] = feats
print("LIME :", lime_top)

# ---------------------------------------------------------------- TODO 4
# Comparaison & rapport : appelle build_report(...) de report_engine.py avec
# imp_shap, lime_top, auc_train, auc_test, idx_A, idx_B, X_test.
# Puis LIS le rapport généré et réponds aux 3 questions en bas de ce fichier.
from report_engine import build_report
# build_report(imp_shap, lime_top, auc_train, auc_test, idx_A, idx_B, X_test, model)

build_report(imp_shap, lime_top, auc_train, auc_test, idx_A, idx_B, X_test, model,
             attentes_metier=ATTENTES_METIER)

# ---------------------------------------------------------------- QUESTIONS FINALES (dans ta tête / le README)
# Q1. SHAP place-t-il les 2 LEURRES en bas du classement ? Si non, qu'est-ce que ça dirait du modèle ?
# Q2. Les top-5 de LIME sont-ils STABLES entre les 2 tirages ? Qu'en conclut un validateur ?
# Q3. Le waterfall de B montre-t-il le pic fiscal à 8 ans ? En une phrase : pourquoi c'est
#     exactement ce qu'un validateur 2e ligne cherche à vérifier ?
