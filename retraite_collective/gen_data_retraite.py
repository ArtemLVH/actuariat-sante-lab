# -*- coding: utf-8 -*-
"""Portefeuille retraite collective synthétique (PERO, type ex-art. 83).
5 000 salariés d'une entreprise fictive — AUCUNE donnée réelle.
Sortie : data_salaries.csv. Usage : python gen_data_retraite.py"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 5000

age = rng.integers(22, 65, N)                              # 22 à 64 ans
anciennete = np.minimum(age - 22, rng.integers(0, 30, N))  # jamais plus que l'âge ne le permet
categorie = rng.choice(["cadre", "non_cadre"], N, p=[0.25, 0.75])
salaire = np.where(categorie == "cadre",
                   rng.lognormal(np.log(52000), 0.25, N),
                   rng.lognormal(np.log(30000), 0.20, N)).round(0)
taux_cotis = np.where(categorie == "cadre", 0.10, 0.06)    # employeur + salarié
encours = (salaire * taux_cotis * anciennete * rng.uniform(0.8, 1.2, N)).round(0)

df = pd.DataFrame({
    "id_salarie": np.arange(1, N + 1),
    "age": age, "anciennete": anciennete, "categorie": categorie,
    "salaire": salaire, "taux_cotis": taux_cotis, "encours": encours,
})
df.to_csv("data_salaries.csv", index=False)
print(f"data_salaries.csv : {len(df)} salaries, {df.shape[1]} colonnes")
print(f"age moyen {df.age.mean():.1f} | anciennete moyenne {df.anciennete.mean():.1f} ans")
print(f"salaire moyen {df.salaire.mean():,.0f} EUR | encours total {df.encours.sum()/1e6:.1f} MEUR")
print(df.groupby("categorie").size().to_string())