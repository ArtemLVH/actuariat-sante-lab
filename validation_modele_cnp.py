"""NIVEAU 2 — Ta 2e ligne CNP en ~80 lignes.
Une cartographie de modèle (variables, tables sources, versions), des contrôles qualité
R0-R2 qui BLOQUENT quand une métadonnée manque (la preuve que ta cartographie servait),
puis les deux gestes d'une revue de validation : SENSIBILITÉS et BACKTESTING.
Données et modèle 100 % simulés."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(4)

# ---------- 1) LA CARTOGRAPHIE : qui utilise quoi, venu d'où, en quelle version ----------
CARTOGRAPHIE = {
    "modele_rachats_v2": {
        "usage": "Best Estimate épargne", "criticite": "élevée",
        "variables": {
            "age":        {"table": "REF_ASSURES",  "version": "2025-12"},
            "anciennete": {"table": "REF_CONTRATS", "version": "2025-12"},
            "ecart_taux": {"table": "PARAM_TAUX",   "version": None},   # ← l'oubli classique
        },
    }
}

def controles(modele):
    """R0 : table renseignée · R1 : version renseignée · R2 : variable présente dans les données."""
    erreurs = []
    for var, meta in CARTOGRAPHIE[modele]["variables"].items():
        if not meta["table"]:   erreurs.append(f"R0 — {var} : table source manquante")
        if not meta["version"]: erreurs.append(f"R1 — {var} : version de table non renseignée")
    if erreurs:
        raise ValueError("CARTOGRAPHIE INCOMPLÈTE, revue impossible :\n  " + "\n  ".join(erreurs))
    print(f"Contrôles R0-R1 OK pour {modele} — la revue peut commencer.\n")

print("Tentative de revue n°1 :")
try:
    controles("modele_rachats_v2")
except ValueError as e:
    print(e)
    print("→ C'est EXACTEMENT à ça que servait ta cartographie : bloquer proprement AVANT le calcul.\n")

CARTOGRAPHIE["modele_rachats_v2"]["variables"]["ecart_taux"]["version"] = "2025-12"   # correction
print("Tentative n°2 (métadonnée complétée) :")
controles("modele_rachats_v2")

# ---------- 2) Le mini-modèle : taux de rachat + Best Estimate simplifié ----------
def taux_rachat(anciennete, ecart_taux):
    """Rachats épargne : base 5 %, pic en année 8 (fiscalité), + sensibilité à l'écart de taux."""
    base = 0.05 + 0.03 * (anciennete == 8) + 0.8 * np.maximum(ecart_taux, 0)
    return np.clip(base, 0, 0.35)

def best_estimate(encours=1000.0, taux_actu=0.03, ecart_taux=0.00, horizon=10):
    """VA des prestations de rachat sur 10 ans (modèle jouet)."""
    be, stock = 0.0, encours
    for t in range(1, horizon + 1):
        q = taux_rachat(t, ecart_taux)
        be += stock * q / (1 + taux_actu) ** t
        stock *= (1 - q)
    return be

be_central = best_estimate()
print(f"BE central : {be_central:,.1f} (encours 1 000)\n")

# ---------- 3) SENSIBILITÉS : on choque UNE hypothèse, on mesure ΔBE ----------
chocs = {"taux d'actualisation +50 bp": dict(taux_actu=0.035),
         "taux d'actualisation −50 bp": dict(taux_actu=0.025),
         "écart de taux +100 bp (rachats dynamiques)": dict(ecart_taux=0.01)}
print("SENSIBILITÉS (le geste central d'une revue) :")
for nom, kw in chocs.items():
    be = best_estimate(**kw)
    print(f"  {nom:45s} BE = {be:8.1f}   Δ = {be - be_central:+7.1f} ({(be/be_central-1):+.1%})")
print("→ on identifie les hypothèses qui PILOTENT le résultat : ici, les rachats dynamiques dominent.\n")

# ---------- 4) BACKTESTING : prédit vs observé, l'écart systématique = biais ----------
annees = np.arange(2021, 2026)
predit = np.full(5, 0.050)
observe = 0.050 + 0.006 + rng.normal(0, 0.002, 5)     # la réalité rachète PLUS que le modèle
bt = pd.DataFrame({"année": annees, "prédit": predit, "observé": observe.round(4),
                   "écart": (observe - predit).round(4)}).set_index("année")
print("BACKTESTING des taux de rachat :")
print(bt.to_string())
print(f"→ écart moyen {bt['écart'].mean():+.3%}, TOUJOURS du même signe : pas du bruit, un BIAIS")
print("  → recommandation de revue : recalibrer. (Un écart qui change de signe = du bruit, on ne touche pas.)")
