"""Tarification santé collective : GLM fréquence x coût = la grille (le barème).
Simule un portefeuille de personnes-années, cache dedans de vrais effets (âge, zone,
formule, lien, branche/IDCC) + un piège (les seniors choisissent les formules riches),
puis montre : (1) la grille multiplicative e^beta, (2) les deux failles des moyennes
par case que le GLM répare. Données 100 % simulées."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

rng = np.random.default_rng(42)
n = 60_000

# ---------- 1) Simulation du portefeuille (une ligne = une personne-année) ----------
lien = rng.choice(["assure", "conjoint", "enfant"], n, p=[0.55, 0.20, 0.25])
age = np.where(lien == "enfant", rng.integers(0, 18, n), rng.integers(22, 68, n))
age_tr = pd.cut(age, [-1, 17, 29, 39, 49, 59, 99],
                labels=["0-17", "18-29", "30-39", "40-49", "50-59", "60+"]).astype(str)
zone = rng.choice(["Province", "IDF"], n, p=[0.70, 0.30])
idcc = rng.choice(["1486_Syntec", "1979_HCR", "BTP", "Autres"], n, p=[0.30, 0.20, 0.25, 0.25])
# LE PIÈGE : la probabilité de choisir la formule premium augmente avec l'âge
p_premium = {"0-17": .20, "18-29": .10, "30-39": .20, "40-49": .30, "50-59": .40, "60+": .55}
u = rng.random(n)
formule = np.where(u < [p_premium[a] for a in age_tr], "premium",
           np.where(u < [p_premium[a] + .45 for a in age_tr], "confort", "eco"))

M_AGE = {"0-17": 1.15, "18-29": 0.85, "30-39": 1.0, "40-49": 1.05, "50-59": 1.25, "60+": 1.55}
M_FOR = {"eco": 0.90, "confort": 1.0, "premium": 1.15}          # effet PUR de la garantie
lam = (4.0 * np.vectorize(M_AGE.get)(age_tr) * np.where(zone == "IDF", 1.10, 1.0)
       * np.vectorize(M_FOR.get)(formule) * np.where(lien == "enfant", 1.25, np.where(lien == "conjoint", 1.05, 1.0))
       * np.select([idcc == "1486_Syntec", idcc == "1979_HCR", idcc == "BTP"], [0.95, 1.05, 1.12], 1.0))
nb_actes = rng.poisson(lam)
scale = 30 * np.where(zone == "IDF", 1.20, 1.0) * np.vectorize({"eco": .85, "confort": 1.0, "premium": 1.30}.get)(formule)
cout_total = np.array([rng.gamma(2.0, s, k).sum() if k > 0 else 0.0 for k, s in zip(nb_actes, scale)])

df = pd.DataFrame(dict(age_tr=age_tr, zone=zone, formule=formule, lien=lien, idcc=idcc,
                       nb_actes=nb_actes, cout_total=cout_total))
print(df.head(5).to_string(index=False))
print(f"→ {n:,} personnes-années · conso moyenne {df.cout_total.mean():,.0f} €\n")

# enfant ⟺ 0-17 par construction : colinéarité parfaite (aliasing) → deux coefficients ±inf qui se
# compensent. On replie 'enfant' sur la référence : l'effet enfant est porté par la ligne « âge 0-17 ».
df["lien_glm"] = np.where(df.lien == "enfant", "assure", df.lien)

# ---------- 2) GLM fréquence (Poisson, lien log) ----------
f_freq = 'nb_actes ~ C(age_tr, Treatment("30-39")) + C(zone) + C(formule, Treatment("confort")) + C(lien_glm, Treatment("assure")) + C(idcc, Treatment("Autres"))'
glm_f = smf.glm(f_freq, data=df, family=sm.families.Poisson()).fit()

# ---------- 3) GLM coût moyen par acte (Gamma, lien log, pondéré par le nb d'actes) ----------
d2 = df[df.nb_actes > 0].copy()
d2["cout_moyen"] = d2.cout_total / d2.nb_actes
f_cout = 'cout_moyen ~ C(age_tr, Treatment("30-39")) + C(zone) + C(formule, Treatment("confort")) + C(lien_glm, Treatment("assure")) + C(idcc, Treatment("Autres"))'
glm_c = smf.glm(f_cout, data=d2, family=sm.families.Gamma(sm.families.links.Log()), var_weights=d2.nb_actes).fit()

def grille(res, titre):
    g = np.exp(res.params).round(3)
    g.index = [i.replace('C(age_tr, Treatment("30-39"))', "âge ").replace('C(formule, Treatment("confort"))', "formule ")
                .replace('C(lien_glm, Treatment("assure"))', "lien ").replace('C(idcc, Treatment("Autres"))', "idcc ")
                .replace("C(zone)", "zone ").replace("[T.", "").replace("]", "") for i in g.index]
    print(f"--- {titre} : les multiplicateurs e^β (la grille) ---")
    print(g.to_string(), "\n")

grille(glm_f, "FRÉQUENCE (actes/an)")
grille(glm_c, "COÛT par acte (€)")
print("NB : pas de ligne « lien enfant » — enfant ⟺ 0-17 ici (aliasing parfait) ; l'effet est porté par")
print("« âge 0-17 » : e^β ≈ 1,44 ≈ 1,15 (âge) × 1,25 (enfant). En portefeuille réel, les enfants rattachés")
print("jusqu'à ~25 ans désalignent les deux variables et rendent les effets séparables.\n")

# Prime pure d'un profil = fréquence prédite x coût prédit
profil = pd.DataFrame([dict(age_tr="40-49", zone="IDF", formule="confort", lien_glm="assure", idcc="BTP")])
pp = glm_f.predict(profil).iloc[0] * glm_c.predict(profil).iloc[0]
print(f"Prime pure « 40-49 · IDF · confort · assuré · BTP » = {glm_f.predict(profil).iloc[0]:.2f} actes × "
      f"{glm_c.predict(profil).iloc[0]:.2f} € = {pp:,.0f} €/an\n")

# ---------- 4) Faille n°1 des moyennes : les effets mélangés ----------
brut = df.groupby("formule").cout_total.mean()
print("--- Faille 1 : moyenne BRUTE par formule (piégée par l'âge des adhérents) ---")
print((brut / brut["confort"]).round(3).to_string())
print("→ le brut fait croire que premium coûte", round(float(brut['premium']/brut['confort']), 2),
      "x confort ; l'effet PUR (vrai = 1.15 x 1.30 ≈ 1.50 sur le coût total) est démêlé par le GLM,")
print("  le reste venait des seniors qui CHOISISSENT premium. La moyenne attribue à la garantie ce qui vient de l'âge.\n")

# ---------- 5) Faille n°2 : les cases minces ----------
cells = df.groupby(["age_tr", "zone", "formule", "lien", "idcc"]).cout_total.agg(["size", "mean"])
minces = cells[cells["size"] < 30]
print(f"--- Faille 2 : {len(minces)} cases sur {len(cells)} ont moins de 30 obs ({len(minces)/len(cells):.0%}) ---")
ex = minces.sort_values("size").iloc[0]
print(f"Exemple : case {minces.sort_values('size').index[0]} → n = {int(ex['size'])}, moyenne observée {ex['mean']:,.0f} €")
print("→ tarifer cette case sur sa moyenne = tarifer du bruit (ton σ/√n) ; le GLM la lisse avec toute l'info voisine.")
print("\nPhrase d'équilibre : « les moyennes par case (un TCD) et le burning cost suffisent tant que les")
print("cases sont épaisses ; le GLM démêle les effets corrélés et tient les cases minces — un raffinement")
print("précieux, pas une nécessité vitale en santé. »")
