"""Le code d'une norme : moteur de délégation de souscription (santé collective).
Une grille de délégation n'est QUE des règles → donc c'est codable. Trois boutons
rouges : TROP GROS, HORS PRIX, TROP BIZARRE. Sinon : le souscripteur signe seul."""

NORME = {
    "effectif_max_seul": 2000,        # vies : au-delà → comité
    "cotisations_max_seul": 3.0,      # M€/an : au-delà → comité
    "ecart_bareme_max": 0.05,         # ±5 % autour du barème autorisé seul
    "plancher": 0.95,                 # jamais < 95 % du prix technique sans dérogation
}

def decision(d):
    motifs, derog = [], False
    if d["effectif"] > NORME["effectif_max_seul"]:
        motifs.append(f"TROP GROS — {d['effectif']:,} vies > {NORME['effectif_max_seul']:,}")
    if d["cotisations_M"] > NORME["cotisations_max_seul"]:
        motifs.append(f"TROP GROS — {d['cotisations_M']} M€ > {NORME['cotisations_max_seul']} M€")
    if d["tarif"] < d["prix_technique"] * NORME["plancher"]:
        motifs.append(f"HORS PRIX — tarif {d['tarif']} € sous le plancher ({d['prix_technique']*NORME['plancher']:.0f} €) → DÉROGATION")
        derog = True
    elif abs(d["tarif"] / d["prix_bareme"] - 1) > NORME["ecart_bareme_max"]:
        motifs.append(f"HORS PRIX — écart au barème {d['tarif']/d['prix_bareme']-1:+.0%} > ±5 %")
    if d.get("hors_catalogue"):
        motifs.append("TROP BIZARRE — garanties hors catalogue")
    if d.get("sp_historique", 0) > 1.0:
        motifs.append(f"TROP BIZARRE — reprise sensible, S/P historique {d['sp_historique']:.0%}")
    if derog:      niveau = "DÉROGATION : formulaire + validation référent + REGISTRE"
    elif motifs:   niveau = "VALIDATION SUPÉRIEURE / comité"
    else:          niveau = "signature du souscripteur SEUL"
    return niveau, motifs

def formulaire_derogation(d, sp_previsionnel):
    return {"demandeur": "Sophie", "client": d["nom"], "ecart": f"{d['tarif']/d['prix_technique']-1:+.0%} vs prix technique",
            "justification": d["justification"], "sp_previsionnel": sp_previsionnel, "statut": "validée par référent", "revue_N+1": None}

dossiers = [
    {"nom": "PME Ficelle (80 sal.)", "effectif": 80, "cotisations_M": 0.12, "tarif": 1500, "prix_bareme": 1500, "prix_technique": 1500},
    {"nom": "Groupe Mastodonte (6 000 sal.)", "effectif": 6000, "cotisations_M": 9.5, "tarif": 1480, "prix_bareme": 1350, "prix_technique": 1430, "sp_historique": 0.92},
    {"nom": "Client Stratégix (900 sal.)", "effectif": 900, "cotisations_M": 1.4, "tarif": 1270, "prix_bareme": 1480, "prix_technique": 1450,
     "justification": "compte multi-lignes, équilibre global avec la prévoyance"},
]

registre = []
for d in dossiers:
    niveau, motifs = decision(d)
    print(f"■ {d['nom']}\n  → {niveau}")
    for m in motifs: print(f"    · {m}")
    if "DÉROGATION" in niveau:
        registre.append(formulaire_derogation(d, sp_previsionnel=0.93))
    print()

print("REGISTRE DES DÉROGATIONS :", registre[0], sep="\n")
# … un an plus tard, la relecture N+1 :
registre[0]["revue_N+1"] = {"sp_reel": 1.04, "verdict": "le pari a PERDU (104 % vs 93 % promis) → resserrer la norme / re-tarifer"}
print("\nREVUE N+1 :", registre[0]["revue_N+1"])

print("\nRappels de la règle graduée : barème = prix de départ de la grille · prix technique = coût réel")
print("estimé du dossier · plancher = technique × 95 %. Et les 3 vitesses de l'approbation produit :")
print("catalogue (heures) · assemblage (jours) · produit nouveau (semaines-mois) — la lenteur est voulue :")
print("une erreur de norme est industrielle.")
