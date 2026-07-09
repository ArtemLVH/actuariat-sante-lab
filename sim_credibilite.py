"""Pourquoi la taille du groupe décide : barème vs expérience (sigma/racine de n).
Simulation : consommation santé individuelle = soins courants (Gamma) + hospitalisation rare et chère.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

def conso_annuelle(n):
    """Consommation santé d'une personne sur UN an (en euros)."""
    routine = rng.gamma(2.0, 450.0, n)                              # soins courants
    hospit = (rng.random(n) < 0.04) * rng.gamma(1.5, 8000.0, n)     # 4 % : hospitalisation
    return routine + hospit

# ---- 1) À quoi ressemble le dataset : un client de 5 000 salariés sur 3 ans ----
n_sal, annees = 5000, [2023, 2024, 2025]
df = pd.DataFrame({
    "salarie_id": np.repeat(np.arange(1, n_sal + 1), len(annees)),
    "annee": np.tile(annees, n_sal),
})
df["conso"] = conso_annuelle(len(df)).round(0)
print(df.head(6).to_string(index=False))
print(f"→ {n_sal} salariés × {len(annees)} ans = {len(df):,} personnes-années (lignes)\n")

mu, sigma = df.conso.mean(), df.conso.std()
cotisation = mu / 0.80   # prime pure / 0,8 → S/P attendu = 80 % pour TOUT le monde
print(f"conso moyenne ≈ {mu:,.0f} € | écart-type individuel ≈ {sigma:,.0f} € | cotisation ≈ {cotisation:,.0f} €/tête → S/P attendu 80 %\n")

# ---- 2) La même cotisation juste, trois tailles de groupe, 2 000 groupes simulés ----
print(f"{'taille':>7} | {'S/P moyen':>9} | {'écart-type':>10} | {'σ/√n théo.':>10} | {'[5 % ; 95 %]':>17} | {'S/P>100 %':>9}")
for n in [40, 300, 5000]:
    sp = conso_annuelle(2000 * n).reshape(2000, n).mean(axis=1) / cotisation * 100
    theo = sigma / np.sqrt(n) / cotisation * 100
    print(f"{n:>7} | {sp.mean():>8.1f}% | {sp.std():>9.1f}% | {theo:>9.1f}% | [{np.percentile(sp,5):>6.1f}% ;{np.percentile(sp,95):>6.1f}%] | {(sp>100).mean()*100:>8.1f}%")
print("\nLecture : la cotisation est JUSTE pour tous — pourtant à 40 têtes, une part des groupes")
print("paraît catastrophique (S/P>100 %) par pur hasard. D'où : petit → barème, gros → expérience.")
print("\nNotes : ① σ/√n ne suppose que l'indépendance ; les intervalles utilisent le TCL (approximatif")
print("à n=40 : queue lourde → 21,6 % simulé vs ~26 % gaussien). ② S/P cible = 1 − chargements (80 % ↔ 20 %")
print("de frais) : ratio combiné = S/P + frais = 100 % à l'équilibre. ③ La dispersion vient de la QUEUE")
print("(hospitalisations rares et chères), pas des zéros : plancher de conso quasi universel + queue rare.")
