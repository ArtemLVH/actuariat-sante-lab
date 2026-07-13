# -*- coding: utf-8 -*-
"""Moteur de rapport — fourni. Produit outputs/rapport_validation_explicabilite.md :
manifeste cité, performance, classement SHAP vs attentes métier (✅/⚠), test des leurres,
stabilité LIME (Jaccard), conclusion de validateur."""
import json
import pandas as pd

ATTENTES_ORDRE = ["ecart_taux", "anciennete", "age", "tmg"]   # vrais moteurs, du + fort au + faible
LEURRES = ["csp_code", "region_code"]

def _jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 1.0

def build_report(imp_shap, lime_top, auc_train, auc_test, idx_A, idx_B, X_test, model,
                 attentes_metier=None, out="outputs/rapport_validation_explicabilite.md"):
    with open("outputs/manifest.json", encoding="utf-8") as f:
        man = json.load(f)
    rank = list(imp_shap.sort_values(ascending=False).index)
    pos = {v: i + 1 for i, v in enumerate(rank)}
    lignes = []
    L = lignes.append
    L("# Rapport de validation — explicabilité du modèle de rachat\n")
    L(f"*Généré automatiquement — pipeline `actuariat-sante-lab` × `metaquery_actuary`*\n")
    L("## 1. Traçabilité des données (manifeste MetaQuery)")
    L(f"- Dataset : `{man['dataset']}` — {man['lignes']} lignes — SHA-256 `{man['sha256'][:16]}…`")
    L(f"- Horodatage : {man['horodatage']} — producteur : {man['producteur']}")
    L("- Requête exécutée jointe au manifeste (`outputs/manifest.json`).\n")
    L("## 2. Performance du modèle")
    L(f"- AUC train : **{auc_train:.3f}** — AUC test : **{auc_test:.3f}**")
    surapp = auc_train - auc_test > 0.05
    L(f"- Lecture validateur : {'⚠ écart train/test notable → surveiller le surapprentissage' if surapp else '✅ écart train/test contenu'}\n")
    L("## 3. Importance globale (SHAP) vs attentes métier")
    L("| Rang SHAP | Variable | |SHAP| moyen | Attente métier | Verdict |")
    L("|---|---|---|---|---|")
    att = attentes_metier or {}
    for i, v in enumerate(rank, 1):
        verdict = "✅" if (v in ATTENTES_ORDRE[:2] and i <= 2) or (v in LEURRES and i >= len(rank) - 1) \
                  else ("⚠ leurre trop haut !" if v in LEURRES else "—")
        L(f"| {i} | `{v}` | {imp_shap[v]:.4f} | {att.get(v, '')} | {verdict} |")
    leurres_ok = all(pos[l] >= len(rank) - 1 for l in LEURRES)
    verdict_leurres = "✅ le modèle ne capte pas le bruit" if leurres_ok else "⚠ ALERTE : le modèle exploite du bruit — à challenger"
    L(f"\n**Test des leurres** : csp_code en position {pos['csp_code']}, region_code en position "
      f"{pos['region_code']} → {verdict_leurres}\n")
    L("## 4. Explications locales — SHAP vs LIME sur les mêmes contrats")
    for label, idx in [("A (proba max)", idx_A), ("B (ancienneté = 8 ans)", idx_B)]:
        proba = float(model.predict_proba(X_test.loc[[idx]])[0, 1])
        L(f"### Contrat {label} — proba de rachat prédite : {proba:.1%}")
        L(f"- Caractéristiques : {X_test.loc[idx].to_dict()}")
        key = "A" if label.startswith("A") else "B"
        t1, t2 = lime_top[(key, 1)], lime_top[(key, 2)]
        L(f"- LIME top-5, tirage 1 : {t1}")
        L(f"- LIME top-5, tirage 2 : {t2}")
        jac = _jaccard(t1, t2)
        L(f"- **Stabilité LIME (Jaccard tirage1/tirage2) : {jac:.2f}** — "
          f"{'✅ stable' if jac >= 0.8 else '⚠ instable : LIME rééchantillonne localement, ses explications varient — raison pour laquelle on le croise avec SHAP'}")
        L(f"- Waterfall SHAP : `outputs/shap_waterfall_{key}.png`\n")
    L("## 5. Conclusion de validation (2e ligne)")
    L("- Les moteurs identifiés par SHAP sont confrontés aux attentes métier ci-dessus ; "
      "toute divergence (leurre haut placé, moteur attendu absent) constitue un point de challenge à documenter.")
    L("- LIME est utilisé en contre-expertise locale ; son instabilité éventuelle est mesurée, pas ignorée.")
    L("- Chaque explication référence un dataset tracé (manifeste, hash) : l'explication est auditables de bout en bout.")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))
    print("rapport écrit →", out)
