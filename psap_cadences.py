"""Provisionnement santé : triangle de paiements -> cadences -> chain ladder -> PSAP.
Simule 5 survenances, construit le triangle cumulé, en déduit les cadences (comme
la fameuse N = 98,57 %), projette la charge ultime et calcule la PSAP.
Bonus : la « remise à l'ultime » d'un S/P récent. Données 100 % simulées."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
survenances = [2021, 2022, 2023, 2024, 2025]
pattern = np.array([0.845, 0.140, 0.012, 0.003])       # part payée en année N, N+1, N+2, N+3

# ---------- 1) Simulation des paiements ----------
ultimes_vrais = 10_000 * (1.04 ** np.arange(5)) * rng.normal(1, 0.02, 5)   # en k€
inc = np.outer(ultimes_vrais, pattern) * rng.normal(1, 0.03, (5, 4))       # incréments bruités
cum = inc.cumsum(axis=1)
tri = pd.DataFrame(cum, index=survenances, columns=[f"fin N+{j}" for j in range(4)])
for i, s in enumerate(survenances):                    # masquer le futur (arrêté au 31/12/2025)
    tri.iloc[i, (2025 - s + 1):] = np.nan
print("Triangle des paiements CUMULÉS (k€) — arrêté au 31/12/2025 :")
print(tri.round(0).to_string(), "\n")

# ---------- 2) Chain ladder : facteurs de développement ----------
f = []
for j in range(3):
    num = sum(tri.iloc[i, j+1] for i in range(5) if not np.isnan(tri.iloc[i, j+1]))
    den = sum(tri.iloc[i, j]   for i in range(5) if not np.isnan(tri.iloc[i, j+1]))
    f.append(num / den)
print("Facteurs de développement f_j :", [round(x, 4) for x in f])
cad = 1 / np.cumprod(f[::-1])[::-1]                    # cadence cumulée à fin N+j
cad = np.append(cad, 1.0)
print("→ CADENCES cumulées : fin N = {:.2%} · fin N+1 = {:.2%} · fin N+2 = {:.2%} · fin N+3 = 100 %".format(*cad[:3]))
print("  (ta colonne Euroditas « N = 98,57 % », la voilà : ici fin N+1 ≈ {:.2%})\n".format(cad[1]))

# ---------- 3) Charge ultime et PSAP par survenance ----------
rows = []
for i, s in enumerate(survenances):
    dernier_j = min(2025 - s, 3)
    paye = tri.iloc[i, dernier_j]
    ultime = paye * np.prod(f[dernier_j:]) if dernier_j < 3 else paye
    rows.append([s, paye, ultime, ultime - paye])
res = pd.DataFrame(rows, columns=["survenance", "payé (k€)", "ultime (k€)", "PSAP (k€)"]).set_index("survenance")
print(res.round(0).to_string())
print(f"\nPSAP TOTALE au 31/12/2025 : {res['PSAP (k€)'].sum():,.0f} k€\n")

# ---------- 4) La remise à l'ultime d'un S/P récent ----------
cotis_2025 = ultimes_vrais[-1] / 0.80                  # cotisations calées pour un S/P cible 80 %
sp_vu = res.loc[2025, "payé (k€)"] / cotis_2025
sp_ultime = res.loc[2025, "ultime (k€)"] / cotis_2025
print(f"S/P 2025 « vu » au 31/12 (payé seul)  : {sp_vu:.1%}  ← trompeur, il manque les tardifs")
print(f"S/P 2025 remis à l'ultime (payé+PSAP) : {sp_ultime:.1%} ← le vrai — celui du dossier d'appel d'offres")

# ---------- 5) BONI / MALI : la même survenance vue à deux arrêtés ----------
p0, p1 = tri.loc[2024, "fin N+0"], tri.loc[2024, "fin N+1"]
u_fin2024 = p0 / cad[0]          # ultime estimé de la survenance 2024, vu au 31/12/2024
u_fin2025 = p1 / cad[1]          # le même, ré-estimé au 31/12/2025 (un an de réel en plus)
ecart = u_fin2024 - u_fin2025
print(f"\nBONI/MALI — survenance 2024 : ultime vu fin 2024 = {u_fin2024:,.0f} k€ ; revu fin 2025 = {u_fin2025:,.0f} k€")
print(f"→ écart = {ecart:+,.0f} k€ : {'BONI (on avait trop provisionné)' if ecart > 0 else 'MALI (pas assez provisionné)'} —")
print("  c'est cet écart qui ressort en « résultat sur exercices antérieurs » dans le comptable,")
print("  et le pont exact entre vision comptable et vision survenance.")
