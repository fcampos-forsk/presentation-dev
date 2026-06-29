"""
=============================================================================
 DEMO D'INSTRUMENTATION MANUELLE - meme pipeline, outillage dans le code
=============================================================================

MEME pipeline que demo_profiling.py (memes fonctions, memes anti-patterns),
mais ici on N'UTILISE PAS de profileur externe (cProfile). On "outille" le
code nous-memes : decorateurs de chronometrage, gestionnaire de contexte pour
mesurer des blocs precis, compteurs d'appels, et un mini-rapport fait main.

But pedagogique : comparer les DEUX approches.

    cProfile / snakeviz (script 1)        Instrumentation manuelle (ce script)
    --------------------------------      ------------------------------------
    Externe, aucun changement de code     On modifie le code (decorateurs...)
    Mesure TOUT (y compris la stdlib)     On mesure SEULEMENT ce qu'on cible
    Granularite = la fonction             Granularite = au choix (meme un bloc)
    Overhead par appel important          Overhead quasi nul
    (~3 s ici a cause des millions        (~1 s : on ne perturbe presque pas
     d'appels recursifs instrumentes)      le programme)
    Vue : call-tree / sunburst            Vue : les chiffres qu'on a demandes
    Ideal pour DECOUVRIR le goulot        Ideal pour SURVEILLER un point connu

Lancer simplement :
    python demo_instrumentation.py
=============================================================================
"""

import random
import string
import time
from collections import defaultdict
from contextlib import contextmanager

# --- Parametres (identiques au script 1 pour une comparaison juste) -----------
NB_TRANSACTIONS = 4000
PROFONDEUR_SCORE = 24
SEED = 42

random.seed(SEED)


# =============================================================================
#  OUTILLAGE : notre "profileur maison"
# =============================================================================

# Registre des etapes (rempli par le decorateur @chrono)
_ETAPES = defaultdict(lambda: {"appels": 0, "temps": 0.0})
# Registre des sous-blocs (rempli par le gestionnaire de contexte bloc())
_SOUS_BLOCS = defaultdict(lambda: {"appels": 0, "temps": 0.0})


def chrono(fn):
    """
    Decorateur : mesure le temps cumule et le nombre d'appels d'une fonction.
    A poser sur les fonctions qu'on veut surveiller. Overhead : 2 appels a
    perf_counter() par execution -> negligeable au niveau d'une etape.
    ATTENTION : a NE PAS poser sur une fonction recursive appelee des millions
    de fois (l'overhead exploserait, exactement comme cProfile).
    """
    def wrapper(*args, **kwargs):
        debut = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            _ETAPES[fn.__name__]["temps"] += time.perf_counter() - debut
            _ETAPES[fn.__name__]["appels"] += 1
    return wrapper


@contextmanager
def bloc(nom):
    """
    Gestionnaire de contexte : chronometre un BLOC de code arbitraire.
    C'est la grande difference avec cProfile : on n'est pas limite aux
    frontieres de fonctions, on mesure exactement les lignes qu'on veut.
        with bloc("filtrage"):
            ...
    """
    debut = time.perf_counter()
    try:
        yield
    finally:
        _SOUS_BLOCS[nom]["temps"] += time.perf_counter() - debut
        _SOUS_BLOCS[nom]["appels"] += 1


def afficher_rapport(temps_total):
    """Mini-profileur fait main : affiche un tableau trie, facon pstats."""
    largeur = 64
    print("\n" + "=" * largeur)
    print(" RAPPORT D'INSTRUMENTATION (profileur maison)")
    print("=" * largeur)
    print(f"{'Etape':<26}{'appels':>8}{'temps (s)':>12}{'% total':>10}")
    print("-" * largeur)
    for nom, s in sorted(_ETAPES.items(), key=lambda x: x[1]["temps"], reverse=True):
        pct = 100 * s["temps"] / temps_total if temps_total else 0
        print(f"{nom:<26}{s['appels']:>8}{s['temps']:>12.4f}{pct:>9.1f}%")
    print("-" * largeur)
    print(f"{'TOTAL (horloge reelle)':<26}{'':>8}{temps_total:>12.4f}{100:>9.1f}%")

    if _SOUS_BLOCS:
        print("\n Detail des sous-blocs (impossible a obtenir avec cProfile) :")
        print("-" * largeur)
        for nom, s in sorted(_SOUS_BLOCS.items(), key=lambda x: x[1]["temps"], reverse=True):
            print(f"   {nom:<23}{s['appels']:>8}{s['temps']:>12.4f}")
    print("=" * largeur)


# =============================================================================
#  LE PIPELINE (identique au script 1 ; @chrono pose sur les 6 etapes)
# =============================================================================

@chrono
def generer_transactions(n):
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


def memes_transactions(a, b):
    return (a["client"] == b["client"]
            and a["produit"] == b["produit"]
            and a["montant"] == b["montant"])

@chrono
def detecter_doublons(transactions):
    """ANTI-PATTERN : double boucle O(n^2)."""
    doublons = []
    n = len(transactions)
    for i in range(n):
        for j in range(i + 1, n):
            if memes_transactions(transactions[i], transactions[j]):
                doublons.append((i, j))
    return doublons


def score_recursif(n):
    """ANTI-PATTERN : Fibonacci sans memoisation (recursion exponentielle).
    NOTE : on ne met PAS @chrono ici (millions d'appels -> overhead explosif)."""
    if n < 2:
        return n
    return score_recursif(n - 1) + score_recursif(n - 2)

@chrono
def calculer_scores_fidelite(transactions):
    clients = set(t["client"] for t in transactions)
    scores = {}
    for client in clients:
        # variation DETERMINISTE (reproductible d'un run a l'autre)
        base = PROFONDEUR_SCORE + (int(client.split("_")[1]) % 3)
        scores[client] = score_recursif(base)
    return scores


@chrono
def construire_rapport(transactions):
    """ANTI-PATTERN : concatenation (+=) + re-parcours imbrique."""
    clients = sorted(set(t["client"] for t in transactions))
    rapport = ""
    for client in clients:
        rapport += f"=== Rapport client {client} ===\n"
        for t in transactions:
            if t["client"] == client:
                rapport += f"  {t['ref']} | {t['produit']} | {t['montant']} EUR\n"
    return rapport


def mediane_naive(valeurs):
    triees = sorted(valeurs)
    milieu = len(triees) // 2
    if len(triees) % 2 == 0:
        return (triees[milieu - 1] + triees[milieu]) / 2
    return triees[milieu]

@chrono
def calculer_statistiques(transactions):
    """ANTI-PATTERN : group-by naif. On chronometre ICI deux sous-blocs
    distincts grace a bloc() -- chose impossible avec cProfile."""
    montants = [t["montant"] for t in transactions]
    stats = {"global": {}}

    with bloc("stats_global"):
        stats["global"]["total"] = sum(montants)
        stats["global"]["moyenne"] = sum(montants) / len(montants)
        stats["global"]["mediane"] = mediane_naive(montants)

    with bloc("stats_par_produit (group-by naif)"):
        produits = sorted(set(t["produit"] for t in transactions))
        stats["par_produit"] = {}
        for produit in produits:
            montants_p = [t["montant"] for t in transactions if t["produit"] == produit]
            if montants_p:
                stats["par_produit"][produit] = {
                    "total": sum(montants_p),
                    "mediane": mediane_naive(montants_p),
                    "min": sorted(montants_p)[0],
                    "max": sorted(montants_p)[-1],
                }
    return stats


@chrono
def compter_produits(transactions):
    compteur = {}
    for t in transactions:
        compteur[t["produit"]] = compteur.get(t["produit"], 0) + 1
    return sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:10]


# =============================================================================
#  ORCHESTRATION
# =============================================================================

def pipeline_complet():
    transactions = generer_transactions(NB_TRANSACTIONS)
    doublons = detecter_doublons(transactions)
    scores = calculer_scores_fidelite(transactions)
    rapport = construire_rapport(transactions)
    stats = calculer_statistiques(transactions)
    top_produits = compter_produits(transactions)
    return {
        "transactions": len(transactions),
        "doublons": len(doublons),
        "clients": len(scores),
        "total": stats["global"]["total"],
        "top": top_produits[0],
        "rapport": len(rapport),
    }


# =============================================================================
#  A RETENIR : quand utiliser quoi
# -----------------------------------------------------------------------------
#  cProfile + snakeviz  -> phase d'EXPLORATION : "ou est le goulot ?"
#                          On ne sait pas encore, on veut une vue complete.
#  Instrumentation      -> phase de SUIVI : "cette etape connue derape-t-elle ?"
#                          En prod, dans des logs, sur un point precis, sans
#                          ralentir l'application.
#  => Souvent on DECOUVRE avec cProfile, puis on SURVEILLE avec l'instrumentation.
# =============================================================================

if __name__ == "__main__":
    debut = time.perf_counter()
    resume = pipeline_complet()
    temps_total = time.perf_counter() - debut

    print("--- Resume ---")
    print(f"Transactions analysees : {resume['transactions']}")
    print(f"Doublons detectes      : {resume['doublons']}")
    print(f"Clients scores         : {resume['clients']}")
    print(f"Montant total          : {resume['total']:.2f} EUR")
    print(f"Top produit            : {resume['top'][0]} ({resume['top'][1]} ventes)")

    afficher_rapport(temps_total)