"""EXTENSION du n°4 (psap_cadences) — la provision avec ses barres d'erreur.
Le chain ladder donne UN chiffre. Ici on monte les trois barreaux au-dessus :
Mack (l'écart-type, sans hypothèse de loi), l'ODP (le chain ladder EST un GLM
Poisson surdispersé — preuve par le calcul), et le bootstrap England-Verrall
(la distribution complète → quantiles, dont le 99,5 % cher à Solvabilité 2).
Chaînage par la donnée : le triangle ci-dessous est la sortie de psap_cadences.py."""
import numpy as np
import pandas as pd
import statsmodels.api as sm

rng = np.random.default_rng(4)

# ---------- 0) La donnée d'entrée : le triangle cumulé du n°4 (k€) ----------
annees = [2021, 2022, 2023, 2024, 2025]
cols = [f"d{j}" for j in range(4)]
tri = pd.DataFrame(
    [[8199.0,  9601.0, 9726.0, 9756.0],
     [8676.0, 10162.0, 10289.0, 10321.0],
     [8836.0, 10340.0, 10472.0, np.nan],
     [9208.0, 10666.0, np.nan,  np.nan],
     [9726.0, np.nan,  np.nan,  np.nan]],
    index=pd.Index(annees, name="survenance"), columns=cols)
n, J = tri.shape
known = tri.notna().sum(axis=1).values          # nb de développements observés par ligne
print("Triangle cumulé repris de psap_cadences.py (k€) :")
print(tri.to_string(), "\n")

# ---------- 1) Chain ladder : le best estimate (rappel, 6 lignes) ----------
S = [tri.iloc[:n-1-j, j].sum() for j in range(J-1)]                 # assiettes des facteurs
f = np.array([tri.iloc[:n-1-j, j+1].sum() / S[j] for j in range(J-1)])
Chat = tri.copy()
for j in range(J-1):
    manque = Chat.iloc[:, j+1].isna()
    Chat.iloc[:, j+1] = np.where(manque, Chat.iloc[:, j] * f[j], Chat.iloc[:, j+1])
paye = pd.Series([tri.iloc[i].dropna().iloc[-1] for i in range(n)], index=tri.index)
ultime = Chat.iloc[:, -1]
psap = ultime - paye
print(f"f_j = {f.round(4)} → PSAP best estimate : {psap.sum():,.0f} k€ (le point unique du n°4)\n")

# ---------- 2) MACK : « de combien puis-je me tromper ? » (aucune hypothèse de loi) ----------
# sigma²_j = dispersion des facteurs individuels autour de f_j (pondérée), ddl = nb paires - 1
sig2 = np.array([(tri.iloc[:n-1-j, j] * (tri.iloc[:n-1-j, j+1] / tri.iloc[:n-1-j, j] - f[j])**2).sum()
                 / max(n - 2 - j, 1) for j in range(J-1)])
mse = np.zeros(n)
for i in range(n):
    for j in range(known[i] - 1, J - 1):                          # transitions encore à faire
        mse[i] += ultime.iloc[i]**2 * sig2[j] / f[j]**2 * (1/Chat.iloc[i, j] + 1/S[j])
cov_tot = 0.0
for i in range(n):
    for l in range(i + 1, n):
        for j in range(max(known[i], known[l]) - 1, J - 1):
            cov_tot += 2 * ultime.iloc[i] * ultime.iloc[l] * sig2[j] / f[j]**2 / S[j]
se = np.sqrt(mse)
se_tot = float(np.sqrt(mse.sum() + cov_tot))
mack = pd.DataFrame({"PSAP": psap.round(1), "écart-type": se.round(1),
                     "CV": [f"{s/p:.1%}" if p > 0 else "—" for s, p in zip(se, psap)]})
print("MACK — l'erreur d'estimation autour du best estimate :")
print(mack.to_string())
print(f"TOTAL : PSAP {psap.sum():,.0f} ± {se_tot:,.0f} k€  (CV {se_tot/psap.sum():.1%})")
print("→ même estimateur que le CL, plus son incertitude — sans choisir de loi.\n")

# ---------- 3) ODP : le chain ladder est un GLM déguisé (preuve par le calcul) ----------
inc = tri.copy(); inc.iloc[:, 1:] = tri.values[:, 1:] - tri.values[:, :-1]
long = inc.stack().dropna().rename("inc").reset_index(); long.columns = ["surv", "dev", "inc"]
glm = sm.GLM.from_formula("inc ~ C(surv) + C(dev)", data=long,
                          family=sm.families.Poisson()).fit(scale="X2")   # surdispersion estimée
grille = pd.DataFrame([(a, d) for a in annees for d in cols], columns=["surv", "dev"])
grille["mu"] = glm.predict(grille)
futur = grille[grille.apply(lambda r: pd.isna(tri.loc[r.surv, r.dev]), axis=1)]
psap_odp = futur.groupby("surv").mu.sum().reindex(annees).fillna(0)
comp = pd.DataFrame({"PSAP chain ladder": psap.round(1), "PSAP GLM Poisson (ODP)": psap_odp.round(1)})
print("ODP — GLM Poisson surdispersé, incréments ~ C(survenance) + C(développement) :")
print(comp.to_string())
print(f"→ identiques : le CL est l'estimateur du GLM croisé. Dispersion estimée phi = {glm.scale:.2f}.\n")

# ---------- 4) BOOTSTRAP England-Verrall : la distribution complète de la provision ----------
mu = glm.fittedvalues.values
r_pearson = (long.inc.values - mu) / np.sqrt(mu)
r_adj = r_pearson * np.sqrt(len(long) / glm.df_resid)             # correction de ddl
phi = float(glm.scale)
B, tirages = 5000, []
for _ in range(B):
    y_star = mu + rng.choice(r_adj, size=len(long), replace=True) * np.sqrt(mu)
    Cs = (long.assign(inc=y_star).pivot(index="surv", columns="dev", values="inc")
              .reindex(index=annees, columns=cols).cumsum(axis=1))
    fs = [Cs.iloc[:n-1-j, j+1].sum() / Cs.iloc[:n-1-j, j].sum() for j in range(J-1)]
    total = 0.0
    for i in range(n):                                            # erreur de process : Gamma(m, phi·m)
        c = Cs.iloc[i, known[i] - 1]
        for j in range(known[i] - 1, J - 1):
            m = max(c * (fs[j] - 1), 1e-8)
            x = rng.gamma(m / phi, phi); total += x; c += x
    tirages.append(total)
t = np.sort(np.array(tirages))
q = lambda p: t[int(p * B) - 1]
print(f"BOOTSTRAP ({B:,} rejeux des résidus + aléa de process) :")
print(f"  moyenne {t.mean():,.0f} k€ · écart-type {t.std():,.0f} k€ (Mack disait {se_tot:,.0f})")
print(f"  quantiles : 75 % = {q(.75):,.0f} · 95 % = {q(.95):,.0f} · 99,5 % = {q(.995):,.0f} k€")
print(f"→ provisionner au best estimate = {psap.sum():,.0f} ; le 99,5 % ({q(.995):,.0f}) est le langage")
print("  de Solvabilité 2 : la distribution, pas le point.\n")

print("Phrase d'équilibre : « un chiffre (chain ladder) → une erreur (Mack) → une loi (ODP)")
print("→ une distribution (bootstrap). En santé, queue courte : le déterministe + prudence suffit")
print("au quotidien ; ces barreaux deviennent indispensables quand la queue s'allonge (prévoyance)")
print("ou quand le régulateur demande un quantile. »")
