"""NIVEAU 2 bis — Le pont entre le métier (niveau 1) et la validation (niveau 2) :
le RECETTAGE des bordereaux avant le CR — la 1re ligne de contrôle, ton geste Euroditas.
Même philosophie que MetaQuery Actuary (github.com/ArtemLVH/metaquery_actuary) :
rien ne se calcule tant que les contrôles ne sont pas verts, et tout laisse une trace.
Données 100 % simulées, anomalies injectées exprès."""
import json
import numpy as np
import pandas as pd

rng = np.random.default_rng(9)

# ---------- 1) Un bordereau de prestations avec des pièges dedans ----------
n = 4000
surv = rng.choice([2024, 2025], n, p=[.48, .52])
regl = surv + rng.choice([0, 1], n, p=[.86, .14])
df = pd.DataFrame({
    "gestionnaire": rng.choice(["AlphaGest", "BetaSante", "GammaTP"], n, p=[.40, .35, .25]),
    "survenance": surv, "reglement": regl,
    "college": rng.choice(["Cadres", "Non-cadres"], n, p=[.3, .7]),
    "montant": rng.gamma(2, 40, n),
})
df = df[df.reglement <= 2025].reset_index(drop=True)

# Injection d'anomalies (ce que la vraie vie t'envoie) :
df.loc[10, "montant"] = -250.0                                   # négatif non annulé
df.loc[20, "college"] = "Cadre"                                  # libellé hors référentiel
df.loc[30, "reglement"] = df.loc[30, "survenance"] - 1           # payé AVANT le soin
df = pd.concat([df, df.iloc[[40]]], ignore_index=True)           # doublon parfait
df.loc[(df.gestionnaire == "GammaTP") & (df.survenance == 2025), "montant"] *= 1.6   # dérive suspecte

REFERENTIEL = {"colleges": {"Cadres", "Non-cadres"},
               "gestionnaires": {"AlphaGest", "BetaSante", "GammaTP"}}

# ---------- 2) Les contrôles de recettage (R0 -> R3) ----------
audit = {"lignes": int(len(df)), "controles": []}
def controle(code, libelle, mask):
    nb = int(pd.Series(mask).sum())
    audit["controles"].append({"code": code, "libelle": libelle,
                               "anomalies": nb, "statut": "OK" if nb == 0 else "KO"})

controle("R0-schema", "colonnes attendues présentes",
         [c not in df.columns for c in ["gestionnaire", "survenance", "reglement", "college", "montant"]])
controle("R1-referentiel", "collège dans le référentiel", ~df.college.isin(REFERENTIEL["colleges"]))
controle("R1-referentiel", "gestionnaire dans le référentiel", ~df.gestionnaire.isin(REFERENTIEL["gestionnaires"]))
controle("R2-coherence", "montant strictement positif", df.montant <= 0)
controle("R2-coherence", "règlement >= survenance", df.reglement < df.survenance)
controle("R2-coherence", "aucun doublon parfait", df.duplicated())

vol = df.groupby(["gestionnaire", "survenance"]).montant.sum().unstack()
evol = vol[2025] / vol[2024] - 1
audit["evolution_2025_vs_2024"] = {g: f"{v:+.1%}" for g, v in evol.items()}
controle("R3-vraisemblance", "évolution annuelle dans [-20 % ; +20 %]", evol.abs() > 0.20)

# ---------- 3) Le verdict, façon MetaQuery : pas de vert, pas de CR ----------
print(f"Bordereau reçu : {len(df):,} lignes — {len(audit['controles'])} contrôles exécutés\n")
for c in audit["controles"]:
    print(f"  [{c['statut']}] {c['code']:16s} {c['libelle']} ({c['anomalies']} anomalie(s))")
print("\nÉvolution 2025 vs 2024 par gestionnaire :", audit["evolution_2025_vs_2024"])
kos = [c for c in audit["controles"] if c["statut"] == "KO"]
audit["verdict"] = "BLOQUÉ — corriger avant tout calcul" if kos else "VALIDÉ — le CR peut tourner"
print(f"\nVERDICT : {audit['verdict']}")
with open("audit.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, ensure_ascii=False, indent=2)
print("→ audit.json écrit : la trace qui rend le recettage AUDITABLE. Philosophie MetaQuery appliquée")
print("  au CR santé : séparer ce qui est PERMIS de ce qui est UTILISÉ — et tout se prouve après coup.")
print(f"  (La dérive GammaTP {audit['evolution_2025_vs_2024']['GammaTP']} n'est pas une erreur de données : c'est une question à poser —")
print("   changement de périmètre ? de système ? → exactement le réflexe rupture de cadence.)")
