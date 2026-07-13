# -*- coding: utf-8 -*-
"""Pont MetaQuery : produit le MANIFESTE de traçabilité du dataset.
V1 autonome : génère le manifeste directement (requête 'virtuelle', dictionnaire, hash).
Le jour où metaquery_actuary expose une fonction d'export → remplacer build_manifest()
par l'appel réel ; le reste du pipeline ne change pas (c'est ça, une interface propre)."""
import hashlib, json, time, pandas as pd

SQL_VIRTUELLE = """SELECT age, anciennete, encours, tmg, ecart_taux, csp_code, region_code, rachat
FROM portefeuille_epargne
WHERE date_observation = '2026-06-30';"""

DICTIONNAIRE = {
    "age": "âge de l'assuré (années)", "anciennete": "ancienneté du contrat (années)",
    "encours": "encours du contrat (€)", "tmg": "taux minimum garanti (%)",
    "ecart_taux": "taux de marché − taux servi (%)",
    "csp_code": "code CSP (variable de contrôle)", "region_code": "code région (variable de contrôle)",
    "rachat": "cible : 1 si rachat total sur la période",
}

def build_manifest(csv_path="data_rachats.csv"):
    with open(csv_path, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    df = pd.read_csv(csv_path)
    manifest = {
        "dataset": csv_path, "sha256": sha, "lignes": len(df), "colonnes": list(df.columns),
        "requete_executee": SQL_VIRTUELLE, "dictionnaire": DICTIONNAIRE,
        "horodatage": time.strftime("%Y-%m-%d %H:%M:%S"),
        "producteur": "metaquery_bridge v0.1 (mode autonome)",
    }
    with open("outputs/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("manifest.json écrit — hash", sha[:12], "…")
    return manifest

if __name__ == "__main__":
    build_manifest()
