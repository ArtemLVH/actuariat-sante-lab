# -*- coding: utf-8 -*-
"""SOLUTIONS de référence — à n'ouvrir qu'après avoir tenté (>15 min de blocage)."""
import numpy as np, pandas as pd, shap, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
from lime.lime_tabular import LimeTabularExplainer
from report_engine import build_report

FEATURES = ["age", "anciennete", "encours", "tmg", "ecart_taux", "csp_code", "region_code"]
ATTENTES_METIER = {
    "ecart_taux": "moteur n°1 (rachat dynamique)", "anciennete": "moteur n°2 (pic fiscal 8 ans)",
    "age": "effet modéré (retraite 62+)", "tmg": "effet faible (protecteur)",
    "encours": "aucun effet codé", "csp_code": "LEURRE", "region_code": "LEURRE",
}
df = pd.read_csv("data_rachats.csv"); X, y = df[FEATURES], df["rachat"]

# TODO 1 — modèle
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
model = XGBClassifier(max_depth=4, n_estimators=300, learning_rate=0.05, subsample=0.9,
                      eval_metric="logloss", random_state=0)
model.fit(X_train, y_train)
auc_train = roc_auc_score(y_train, model.predict_proba(X_train)[:, 1])
auc_test  = roc_auc_score(y_test,  model.predict_proba(X_test)[:, 1])
print(f"AUC train {auc_train:.3f} | AUC test {auc_test:.3f}")

# TODO 2 — SHAP
explainer = shap.TreeExplainer(model)
sv = explainer(X_test)
plt.figure(); shap.plots.beeswarm(sv, max_display=7, show=False)
plt.title("SHAP — qui pilote le rachat ?", loc="left"); plt.tight_layout()
plt.savefig("outputs/shap_beeswarm.png", dpi=130, bbox_inches="tight"); plt.close()
imp_shap = pd.Series(np.abs(sv.values).mean(axis=0), index=FEATURES)
proba = model.predict_proba(X_test)[:, 1]
idx_A = X_test.index[int(np.argmax(proba))]
cand_B = X_test[X_test.anciennete == 8]
idx_B = cand_B.index[int(np.argmax(model.predict_proba(cand_B)[:, 1]))]
for key, idx in [("A", idx_A), ("B", idx_B)]:
    pos = X_test.index.get_loc(idx)
    plt.figure(); shap.plots.waterfall(sv[pos], max_display=7, show=False)
    plt.title(f"Contrat {key} — pourquoi cette proba ?", loc="left"); plt.tight_layout()
    plt.savefig(f"outputs/shap_waterfall_{key}.png", dpi=130, bbox_inches="tight"); plt.close()
print("figures SHAP écrites | idx_A", idx_A, "| idx_B", idx_B)

# TODO 3 — LIME (2 tirages par individu pour la stabilité)
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
print("LIME ok :", {k: v for k, v in lime_top.items()})

# TODO 4 — rapport
build_report(imp_shap, lime_top, auc_train, auc_test, idx_A, idx_B, X_test, model,
             attentes_metier=ATTENTES_METIER)
