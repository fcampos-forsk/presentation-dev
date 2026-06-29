"""
=============================================================================
 DEMO DE PROFILING - Pipeline d'analyse de transactions e-commerce
=============================================================================

Ce script simule un pipeline d'analyse de donnees VOLONTAIREMENT non optimise.
Il contient plusieurs goulots d'etranglement classiques, chacun illustrant
un anti-pattern de performance courant. Ideal pour une demo cProfile + snakeviz.

Pour profiler :
    python -m cProfile -o resultat.prof demo_profiling.py
    snakeviz resultat.prof

Les goulots d'etranglement (du plus au moins couteux) :
    1. detecter_doublons         -> O(n^2) au lieu d'un set      (TRES lent)
    2. calculer_scores_fidelite  -> recursion exponentielle      (lent)
    3. construire_rapport        -> concatenation de chaines en boucle
    4. calculer_statistiques     -> tris redondants + mediane naive
    5. compter_produits          -> rapide (point de comparaison)
=============================================================================
"""

import random
import string

# --- Parametres : ajustez-les pour allonger/raccourcir la demo ---------------
NB_TRANSACTIONS = 4000      # taille du jeu de donnees
PROFONDEUR_SCORE = 24       # profondeur de la recursion (attention : exponentiel)
SEED = 42

random.seed(SEED)


# === ETAPE 1 : generation des donnees ========================================

def generer_transactions(n):
    """Genere n transactions factices. Etape rapide, juste pour avoir des donnees."""
    produits = [f"PROD-{i:03d}" for i in range(50)]
    transactions = []
    for _ in range(n):
        transactions.append({
            "client": f"client_{random.randint(0, 25)}",
            "produit": random.choice(produits),
            "montant": float(random.randint(5, 500)),
            "ref": "".join(random.choices(string.ascii_uppercase + string.digits, k=8)),
        })
    return transactions


# === ETAPE 2 : detection de doublons (LE gros goulot) ========================

def memes_transactions(a, b):
    """Compare deux transactions champ par champ."""
    return (a["client"] == b["client"]
            and a["produit"] == b["produit"]
            and a["montant"] == b["montant"])

def detecter_doublons(transactions):
    """
    ANTI-PATTERN : double boucle O(n^2).
    On compare chaque transaction a toutes les autres.
    La bonne version utiliserait un set / un dictionnaire (O(n)).
    """
    doublons = []
    n = len(transactions)
    for i in range(n):
        for j in range(i + 1, n):
            if memes_transactions(transactions[i], transactions[j]):
                doublons.append((i, j))
    return doublons


# === ETAPE 3 : scores de fidelite (recursion exponentielle) ==================

def score_recursif(n):
    """
    ANTI-PATTERN : suite de Fibonacci sans memoisation.
    Recalcule sans cesse les memes valeurs => complexite exponentielle.
    Sert ici de "score de fidelite" fictif.
    """
    if n < 2:
        return n
    return score_recursif(n - 1) + score_recursif(n - 2)

def calculer_scores_fidelite(transactions):
    """Calcule un score (couteux) pour chaque client unique."""
    clients = set(t["client"] for t in transactions)
    scores = {}
    for client in clients:
        base = PROFONDEUR_SCORE + (hash(client) % 3)
        scores[client] = score_recursif(base)
    return scores


# === ETAPE 4 : construction d'un rapport texte ===============================

def construire_rapport(transactions):
    """
    ANTI-PATTERN : concatenation de chaines (+=) + re-parcours imbrique.
    Pour chaque client on re-parcourt TOUTES les transactions, et chaque '+='
    recree une nouvelle chaine en memoire.
    La bonne version : grouper en un seul passage + "".join(...).
    """
    clients = sorted(set(t["client"] for t in transactions))
    rapport = ""
    for client in clients:
        rapport += f"=== Rapport client {client} ===\n"
        for t in transactions:                      # re-scan complet par client
            if t["client"] == client:
                rapport += f"  {t['ref']} | {t['produit']} | {t['montant']} EUR\n"
    return rapport


# === ETAPE 5 : statistiques (tris redondants) ================================

def mediane_naive(valeurs):
    """Trie la liste a chaque appel, meme quand ce n'est pas necessaire."""
    triees = sorted(valeurs)
    milieu = len(triees) // 2
    if len(triees) % 2 == 0:
        return (triees[milieu - 1] + triees[milieu]) / 2
    return triees[milieu]

def calculer_statistiques(transactions):
    """
    ANTI-PATTERN : group-by naif. Pour CHAQUE produit on re-filtre toute la
    liste puis on la re-trie plusieurs fois. La bonne version ferait un seul
    passage (dictionnaire d'agregation) et trierait une seule fois si besoin.
    """
    montants = [t["montant"] for t in transactions]
    stats = {"global": {}}
    stats["global"]["total"] = sum(montants)
    stats["global"]["moyenne"] = sum(montants) / len(montants)   # re-somme
    stats["global"]["mediane"] = mediane_naive(montants)         # tri

    produits = sorted(set(t["produit"] for t in transactions))
    stats["par_produit"] = {}
    for produit in produits:
        # re-filtre la liste complete pour chaque produit
        montants_p = [t["montant"] for t in transactions if t["produit"] == produit]
        if montants_p:
            stats["par_produit"][produit] = {
                "total": sum(montants_p),
                "mediane": mediane_naive(montants_p),   # 1er tri
                "min": sorted(montants_p)[0],           # 2e tri redondant
                "max": sorted(montants_p)[-1],          # 3e tri redondant
            }
    return stats


# === ETAPE 6 : comptage des produits (rapide, point de repere) ===============

def compter_produits(transactions):
    """Version raisonnable : sert de point de comparaison 'rapide' dans le profil."""
    compteur = {}
    for t in transactions:
        compteur[t["produit"]] = compteur.get(t["produit"], 0) + 1
    top = sorted(compteur.items(), key=lambda x: x[1], reverse=True)
    return top[:10]


# === ORCHESTRATION ===========================================================

def pipeline_complet():
    print("1/6 Generation des donnees...")
    transactions = generer_transactions(NB_TRANSACTIONS)

    print("2/6 Detection des doublons (O(n^2))...")
    doublons = detecter_doublons(transactions)

    print("3/6 Calcul des scores de fidelite (recursif)...")
    scores = calculer_scores_fidelite(transactions)

    print("4/6 Construction du rapport texte...")
    rapport = construire_rapport(transactions)

    print("5/6 Calcul des statistiques...")
    stats = calculer_statistiques(transactions)

    print("6/6 Comptage des produits...")
    top_produits = compter_produits(transactions)

    print("\n--- Resume ---")
    print(f"Transactions analysees : {len(transactions)}")
    print(f"Doublons detectes      : {len(doublons)}")
    print(f"Clients scores         : {len(scores)}")
    print(f"Montant total          : {stats['global']['total']:.2f} EUR")
    print(f"Top produit            : {top_produits[0][0]} ({top_produits[0][1]} ventes)")
    print(f"Taille du rapport      : {len(rapport)} caracteres")


# =============================================================================
#  RECAP POUR LA PRESENTATION : chaque goulot et sa correction
# -----------------------------------------------------------------------------
#  detecter_doublons      O(n^2)              -> set / dict de cles      : O(n)
#  score_recursif         recursion expo.     -> memoisation (lru_cache) : O(n)
#  construire_rapport     += + re-scan        -> 1 passage + "".join()
#  calculer_statistiques  group-by naif       -> 1 dict d'agregation
# =============================================================================

if __name__ == "__main__":
    # --- Option A (recommandee) : profiler depuis la ligne de commande --------
    #     python -m cProfile -o resultat.prof demo_profiling.py
    #     snakeviz resultat.prof
    #
    # --- Option B : profiler depuis le script (decommentez le bloc ci-dessous)-
    #
    # import cProfile, pstats
    # profiler = cProfile.Profile()
    # profiler.enable()
    # pipeline_complet()
    # profiler.disable()
    # profiler.dump_stats("resultat.prof")
    # pstats.Stats(profiler).sort_stats("tottime").print_stats(12)
    # # puis dans un terminal :  snakeviz resultat.prof

    pipeline_complet()