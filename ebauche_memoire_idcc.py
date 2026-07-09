"""NIVEAU 3 — Ébauche de mémoire : correctifs tarifaires par IDCC (branche).
Volontairement inachevé : le geste central est codé, les pistes sont ouvertes.
Inspiration : le mémoire 2021 fait dans la direction (correctifs par IDCC vs code NAF,
tables d'expérience vs barème de place). Données 100 % simulées."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(21)

# ---------- 1) Un portefeuille multi-branches (avec de VRAIES différences cachées) ----------
BRANCHES = {"1486_Syntec": (30000, 0.95), "1979_HCR": (12000, 1.10), "BTP": (18000, 1.18),
            "3248_Metallurgie": (15000, 1.05), "petite_branche_X": (600, 1.30)}   # rare ET risquée
rows = []
for idcc, (n, risque_vrai) in BRANCHES.items():
    conso = rng.gamma(2.0, 600 * risque_vrai / 2, n)          # moyenne = 600 x risque
    rows.append(pd.DataFrame({"idcc": idcc, "conso": conso}))
pf = pd.concat(rows, ignore_index=True)

# ---------- 2) Le geste du mémoire : barème unique vs correctifs par IDCC ----------
tarif_unique = pf.conso.mean()                                  # le "barème de place" naïf
exp_branche = pf.groupby("idcc").conso.agg(["size", "mean"])
exp_branche["correctif_brut"] = exp_branche["mean"] / tarif_unique

# Crédibilité : la petite branche ne mérite pas 100 % de confiance dans son vécu
K = 5000
exp_branche["Z"] = exp_branche["size"] / (exp_branche["size"] + K)
exp_branche["correctif_credibilise"] = (exp_branche["Z"] * exp_branche["correctif_brut"] + (1 - exp_branche["Z"]) * 1.0)
exp_branche["risque_vrai"] = [BRANCHES[i][1] for i in exp_branche.index]

print(f"Tarif unique (barème naïf) : {tarif_unique:,.0f} €/tête\n")
print("CORRECTIFS PAR IDCC — le cœur du mémoire :")
print(exp_branche[["size", "correctif_brut", "Z", "correctif_credibilise", "risque_vrai"]]
      .round(3).sort_values("size", ascending=False).to_string())
print("""
Lecture : les grosses branches → correctif ≈ leur vécu (Z proche de 1) ; la petite branche
rare-et-risquée → son correctif brut est bruité, la crédibilité le tire vers 1 — c'est
exactement l'arbitrage biais-variance, et le vrai sujet : COMMENT choisir K par branche ?
""")

# ---------- 3) PISTES OUVERTES (à discuter en entretien / avec un encadrant) ----------
PISTES = [
    "1. Estimer K par branche (Bühlmann-Straub) au lieu d'un K unique : variance intra vs inter-branches.",
    "2. GLM avec C(idcc) + âge + zone : correctifs 'toutes choses égales' vs correctifs bruts — que reste-t-il de l'effet branche pur ?",
    "3. XGBoost + SHAP sur les mêmes données : le ML capte-t-il des interactions branche x âge que le GLM rate, et SHAP rend-il ça auditable ?",
    "4. Report de la réforme IJSS par branche : croiser distribution des salaires (1,4-1,8 SMIC) x IDCC → quelles branches absorbent le choc ?",
    "5. Ruptures de cadences par branche : détecter automatiquement un changement de rythme de liquidation (gestionnaire, réforme) avant qu'il ne fausse la PSAP.",
]
print("PISTES (l'ébauche s'arrête ici volontairement — matière à discussion) :")
print("\n".join(PISTES))
