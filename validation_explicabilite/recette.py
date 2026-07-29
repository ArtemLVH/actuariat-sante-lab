# -*- coding: utf-8 -*-
"""Recette automatisée — Bloc D (R1 sceaux + R3 vraisemblance métier).
Rejoue en une commande les contrôles faits à la main lors du branchement
MetaQuery -> pipeline XAI. Sortie : outputs/recette.json + console.
Usage : python recette.py"""
import hashlib, json
from pathlib import Path
import pandas as pd

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

resultats = {}

# ---- R1 : non-régression des sceaux (3 empreintes, 1 verdict) ----
h_extract = sha256_of("extract.csv")
h_source  = sha256_of("data_rachats.csv")
with open("outputs/manifest.json", encoding="utf-8") as f:
    manifest = json.load(f)
h_manifeste = manifest["extraction"]["sha256"]

r1_ok = (h_extract == h_manifeste == h_source)
resultats["R1_sceaux"] = {
    "verdict": "PASS" if r1_ok else "FAIL",
    "sha256_extract": h_extract,
    "sha256_manifeste": h_manifeste,
    "sha256_source": h_source,
}

# ---- R3 : vraisemblance métier sur l'extraction ----
df = pd.read_csv("extract.csv")
attendues = ["age", "anciennete", "encours", "tmg",
             "ecart_taux", "csp_code", "region_code", "rachat"]
controles = {}
controles["colonnes_attendues_dans_l_ordre"] = "PASS" if list(df.columns) == attendues else "FAIL"
controles["aucune_valeur_manquante"] = "PASS" if int(df.isna().sum().sum()) == 0 else "FAIL"
controles["rachat_binaire"] = "PASS" if set(df["rachat"].unique()) <= {0, 1} else "FAIL"
controles["age_entre_18_et_100"] = "PASS" if df["age"].between(18, 100).all() else "FAIL"
controles["anciennete_positive"] = "PASS" if (df["anciennete"] >= 0).all() else "FAIL"
controles["encours_strictement_positif"] = "PASS" if (df["encours"] > 0).all() else "FAIL"
tx = float(df["rachat"].mean())
controles["taux_rachat_entre_4_et_12_pct"] = "PASS" if 0.04 <= tx <= 0.12 else "FAIL"

r3_ok = all(v == "PASS" for v in controles.values())
resultats["R3_vraisemblance"] = {
    "verdict": "PASS" if r3_ok else "FAIL",
    "taux_rachat": round(tx, 4),
    "lignes": int(len(df)),
    "controles": controles,
}

# ---- verdict global + écriture ----
verdict = "PASS" if (r1_ok and r3_ok) else "FAIL"
resultats["verdict_global"] = verdict
Path("outputs").mkdir(exist_ok=True)
with open("outputs/recette.json", "w", encoding="utf-8") as f:
    json.dump(resultats, f, indent=2, ensure_ascii=False)

print("=" * 50)
print("RECETTE - verdict global :", verdict)
print("R1 sceaux :", resultats["R1_sceaux"]["verdict"], "| empreinte", h_extract[:16], "...")
print("R3 vraisemblance :", resultats["R3_vraisemblance"]["verdict"],
      "|", len(df), "lignes | taux de rachat", f"{tx:.2%}")
for k, v in controles.items():
    print("  " + ("OK " if v == "PASS" else "KO ") + k)
print("detail ecrit -> outputs/recette.json")
print("=" * 50)