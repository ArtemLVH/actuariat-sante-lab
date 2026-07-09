# Actuariat santé collective — bac à sable Python

Quatre modules qui codent la boucle **tarification ↔ provisionnement** de l'assurance
collective santé, sur données **100 % simulées** (aucune donnée réelle).

| Module | Ce qu'il code | Le concept |
|---|---|---|
| `sim_credibilite.py` | S/P de groupes de 40 / 300 / 5 000 têtes ; σ/√n vérifié par simulation | pourquoi la taille décide entre barème et expérience |
| `moteur_delegation.py` | une norme de souscription en règles : seuils, plancher, dérogation, registre, revue N+1 | grille de délégation et contrôle a posteriori |
| `glm_prime_pure.py` | GLM fréquence (Poisson) × coût (Gamma), lien log → la grille multiplicative e^β ; les deux failles des moyennes par case | la tarification : l'usine à barème |
| `recettage_bordereaux.py` | contrôles R0-R3 sur bordereaux (référentiels, cohérence, vraisemblance), anomalies injectées, audit.json | le recettage : la 1re ligne de contrôle, pont métier ↔ validation |
| `psap_cadences.py` | triangle de paiements → cadences → chain ladder → PSAP ; remise à l'ultime d'un S/P récent | le provisionnement, et le pont vers la tarification |

## Projet lié
[MetaQuery Actuary](https://github.com/ArtemLVH/metaquery_actuary) — gouvernance d'extraction SQL au niveau champ : dictionnaire de champs gouverné, sélection par cas d'usage, SQL généré seulement si les règles passent (V1 mono-source → V3 jointures explicites), sorties query.sql / audit.json / explain.txt. Né de l'expérience en validation de modèles ; `recettage_bordereaux.py` en applique la philosophie au CR santé.

## Installation
```bash
pip install -r requirements.txt
python sim_credibilite.py   # puis les trois autres
```

Le fil rouge : la tarification fait un pari (la prime pure), l'année se vit, le
provisionnement complète (la PSAP), le S/P par survenance juge le pari — et le
prix de demain se construit sur le S/P remis à l'ultime d'hier. Deux machines,
une seule donnée qui circule.
