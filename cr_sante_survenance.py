"""NIVEAU 1 — Ton métier Euroditas en ~100 lignes.
Trois gestionnaires envoient leurs bordereaux dans trois formats différents (la vraie vie),
on consolide, puis on produit le CR par survenance : cascade TTC -> HT -> nette,
charge = prestations payées + PSAP (cadences) + FMT, résultat et S/P.
Données 100 % simulées."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(11)

# ---------- 1) Trois bordereaux, trois formats (comme dans ta boîte mail) ----------
def bordereau(n, style):
    surv = rng.choice([2023, 2024, 2025], n, p=[.20, .35, .45])
    regl = surv + rng.choice([0, 1], n, p=[.855, .145])          # payé l'année même ou en N+1
    keep = regl <= 2025                                           # arrêté au 31/12/2025
    surv, regl = surv[keep], regl[keep]
    college = rng.choice(["Cadres", "Non-cadres"], len(surv), p=[.3, .7])
    montant = rng.gamma(2, 40, len(surv)).round(2)
    if style == 1:   # AlphaGest : propre, dates ISO
        return pd.DataFrame({"date_soin": [f"{s}-06-15" for s in surv], "date_reglement": [f"{r}-09-10" for r in regl],
                             "college": college, "presta_rc": montant})
    if style == 2:   # BetaSante : dates FR, collèges en code
        return pd.DataFrame({"DateActe": [f"15/06/{s}" for s in surv], "DatePaiement": [f"10/09/{r}" for r in regl],
                             "Categorie": np.where(college == "Cadres", "C", "NC"), "Remboursement": montant})
    # GammaTP : années brutes, montants texte à virgule
    return pd.DataFrame({"dt_surv": surv, "dt_regl": regl, "col": college,
                         "montant": [f"{m:.2f}".replace(".", ",") for m in montant]})

brut = {"AlphaGest": bordereau(4000, 1), "BetaSante": bordereau(4000, 2), "GammaTP": bordereau(4000, 3)}
print("Aperçu des 3 formats reçus :")
for g, df in brut.items():
    print(f"  {g:10s} → colonnes {list(df.columns)}")

# ---------- 2) Consolidation : trois formats -> UNE table ----------
def normalise(g, df):
    if g == "AlphaGest":
        out = pd.DataFrame({"survenance": df.date_soin.str[:4].astype(int), "reglement": df.date_reglement.str[:4].astype(int),
                            "college": df.college, "montant": df.presta_rc})
    elif g == "BetaSante":
        out = pd.DataFrame({"survenance": df.DateActe.str[-4:].astype(int), "reglement": df.DatePaiement.str[-4:].astype(int),
                            "college": df.Categorie.map({"C": "Cadres", "NC": "Non-cadres"}), "montant": df.Remboursement})
    else:
        out = pd.DataFrame({"survenance": df.dt_surv, "reglement": df.dt_regl, "college": df.col,
                            "montant": df.montant.str.replace(",", ".").astype(float)})
    out["gestionnaire"] = g
    return out

presta = pd.concat([normalise(g, df) for g, df in brut.items()], ignore_index=True)
print(f"\n→ consolidé : {len(presta):,} lignes, un seul schéma. Payé par gestionnaire (k€) :")
print((presta.pivot_table(index="survenance", columns="gestionnaire", values="montant", aggfunc="sum") / 1000).round(1).to_string())

# ---------- 3) Cadence observée sur les survenances liquidées, PSAP sur la verte ----------
cad = (presta[(presta.survenance <= 2024) & (presta.reglement == presta.survenance)].montant.sum()
       / presta[presta.survenance <= 2024].montant.sum())
print(f"\nCadence à fin N (observée sur 2023-2024, liquidées) : {cad:.2%}  ← ta « N = 98,57 % », ici {cad:.2%}")

cr = presta.groupby("survenance").montant.sum().to_frame("payé")
cr["ultime"] = np.where(cr.index < 2025, cr["payé"], cr["payé"] / cad)   # 2025 : remise à l'ultime
cr["PSAP"] = cr["ultime"] - cr["payé"]

# ---------- 4) La cascade et le CR (cotisations calées pour l'exemple : S/P cible 88 %) ----------
cr["cotis_HT"] = (cr["ultime"] / 0.88).round(0)
cr["cotis_TTC"] = (cr["cotis_HT"] * 1.1327).round(0)
cr["chargements"] = (0.20 * cr["cotis_HT"]).round(0)
cr["cotis_nette"] = cr["cotis_HT"] - cr["chargements"]
cr["FMT"] = (0.008 * cr["cotis_HT"]).round(0)                            # rangée côté charge, comme dans TON outil
cr["charge"] = cr["payé"] + cr["PSAP"] + cr["FMT"]
cr["résultat"] = (cr["cotis_nette"] - cr["charge"]).round(0)
cr["S/P (HT)"] = (cr["charge"] / cr["cotis_HT"]).map("{:.1%}".format)

print("\n================ CR SANTÉ PAR SURVENANCE (k€) — arrêté 31/12/2025 ================")
print((cr[["cotis_TTC", "cotis_HT", "chargements", "cotis_nette", "payé", "PSAP", "FMT", "charge", "résultat"]] / 1000).round(1).to_string())
print(cr[["S/P (HT)"]].to_string())
print("\nLecture : 2023-2024 quasi liquidées (PSAP ≈ 0) ; 2025 porte la PSAP — sans elle, son S/P")
print("paraîtrait trompeusement bon. Et note le ratio combiné : 88,8 % + 20 % de frais = 108,8 % → les trois\nannées sont en PERTE malgré un S/P sous 100 % — voilà pourquoi le re-tarif existe.")
