# -*- coding: utf-8 -*-
"""Génère un portefeuille épargne synthétique avec mécanique de rachat CONNUE.
L'intérêt : on sait quelles variables pilotent VRAIMENT le rachat →
on pourra vérifier si SHAP/LIME les retrouvent (= l'explicabilité comme outil de VALIDATION).
Vrais moteurs : ecart_taux (fort), anciennete (pic fiscal à 8 ans), age (départ retraite 62+).
Faible : tmg. LEURRES sans aucun effet : csp_code, region_code."""
import numpy as np, pandas as pd, hashlib, json, time
rng = np.random.default_rng(42)
N = 12000
age = rng.integers(25, 86, N)
anciennete = rng.integers(0, 21, N)
encours = np.round(np.exp(rng.normal(9.6, 0.8, N)), 2)
tmg = rng.choice([0.0, 1.0, 1.5, 2.5], N, p=[0.45, 0.25, 0.20, 0.10])
taux_marche = np.round(rng.uniform(1.0, 4.5, N), 2)
taux_servi = np.maximum(tmg, 2.0)
ecart_taux = np.round(taux_marche - taux_servi, 2)
csp_code = rng.integers(1, 9, N)        # LEURRE
region_code = rng.integers(1, 14, N)    # LEURRE
p = (0.030
     + 0.080 * (anciennete == 8)
     + 0.060 * np.clip(ecart_taux, 0, None) ** 1.5 / (2.5 ** 1.5) * 2.0
     + 0.020 * (age >= 62)
     - 0.004 * (tmg >= 2.5))
p = np.clip(p + rng.normal(0, 0.004, N), 0.001, 0.95)
rachat = rng.binomial(1, p)
df = pd.DataFrame(dict(age=age, anciennete=anciennete, encours=encours, tmg=tmg,
                       ecart_taux=ecart_taux, csp_code=csp_code, region_code=region_code,
                       rachat=rachat))
df.to_csv("data_rachats.csv", index=False)
print("data_rachats.csv :", df.shape, "| taux de rachat moyen :", round(df.rachat.mean(), 4))
