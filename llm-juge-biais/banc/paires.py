"""The bench: 30 technical questions (DevOps, networking), each with two answers.

- Pairs 1 to 20 (type "longueur", padding): a good short answer, and the SAME answer
  lengthened with padding (introduction, rewording, conclusion) that
  adds no new information. Expected verdict: tie, or the short one.
- Pairs 21 to 25 (type "fausse", wrong): a good short answer against a wrong
  answer of similar length. Expected verdict: the good one.
- Pairs 26 to 30 (type "fausse-longue", wrong and padded): a good short answer against a
  wrong AND lengthened answer. Expected verdict: the good one.

Running `python3 paires.py [--lang en]` writes paires.json.
"""
import json
from pathlib import Path

INTROS = [
    "Excellente question, c'est un point que beaucoup d'équipes rencontrent au quotidien.",
    "C'est une question importante, et il vaut la peine d'y répondre clairement.",
    "Très bonne question : ce sujet revient souvent en production.",
    "Voici une réponse détaillée, pour bien comprendre le fonctionnement.",
    "C'est un point essentiel à maîtriser pour tout administrateur.",
]
OUTROS = [
    "En résumé, c'est ce qu'il faut retenir. N'hésitez pas à consulter la documentation officielle pour aller plus loin.",
    "J'espère que cette explication vous aide à y voir plus clair.",
    "Pour conclure, garder ce point en tête évite bien des surprises.",
    "C'est l'essentiel ; la documentation officielle reste la meilleure référence.",
    "Voilà, j'espère que c'est plus clair maintenant.",
]

# (question, correct short answer, rewording with no new information, reference)
LONGUEUR = [
    ("Quel port TCP un serveur SSH utilise-t-il par défaut ?",
     "SSH écoute par défaut sur le port TCP 22.",
     "Autrement dit, sans configuration particulière, le serveur SSH attend les connexions sur le port 22.",
     "Port TCP 22."),
    ("Quelle différence entre git rebase et git merge ?",
     "git rebase rejoue vos commits au-dessus d'une autre branche et réécrit leur historique. git merge crée un commit de fusion et ne réécrit rien.",
     "Dit autrement : rebase change l'historique de vos commits, merge le garde tel quel et ajoute un commit qui joint les deux branches.",
     "rebase réécrit l'historique en rejouant les commits ; merge ajoute un commit de fusion sans réécrire."),
    ("Un conteneur s'arrête avec le code de sortie 137. Qu'est-ce que ça veut dire ?",
     "137 = 128 + 9 : le processus a reçu SIGKILL, le plus souvent envoyé par l'OOM killer parce que la limite mémoire est atteinte.",
     "En clair, le processus a été tué de force par le signal 9, et la cause habituelle est un manque de mémoire.",
     "SIGKILL (128 + 9), en général l'OOM killer."),
    ("Quelle différence entre TCP et UDP ?",
     "TCP établit une connexion et garantit l'ordre et la livraison, avec des retransmissions. UDP envoie des datagrammes sans connexion, sans garantie de livraison ni d'ordre.",
     "Pour le dire simplement : TCP est fiable et ordonné, UDP ne garantit rien.",
     "TCP : connexion, ordre, retransmissions. UDP : datagrammes sans garantie."),
    ("Combien d'adresses contient un réseau IPv4 en /24 ?",
     "Un /24 fixe les 24 premiers bits : il reste 8 bits, soit 256 adresses, dont 254 utilisables par des hôtes (on retire l'adresse de réseau et celle de broadcast).",
     "Autrement dit, un /24 donne 256 adresses au total et 254 pour les machines.",
     "256 adresses, 254 utilisables."),
    ("À quoi sert la commande tofu plan ?",
     "tofu plan compare la configuration au state et à l'infrastructure réelle, puis affiche les créations, modifications et suppressions prévues, sans rien appliquer.",
     "C'est donc un aperçu des changements : rien n'est modifié tant qu'on ne lance pas apply.",
     "Affiche les changements prévus sans les appliquer."),
    ("Que signifie le code HTTP 503 ?",
     "503 Service Unavailable : le serveur ne peut pas traiter la requête pour l'instant (surcharge ou maintenance). L'en-tête Retry-After peut indiquer quand réessayer.",
     "En d'autres termes, le service est temporairement indisponible et il faut réessayer plus tard.",
     "Service indisponible temporairement ; Retry-After possible."),
    ("À quoi sert un enregistrement DNS CNAME ?",
     "Un CNAME fait d'un nom l'alias d'un autre nom : le résolveur suit l'alias et résout le nom cible.",
     "Dit autrement, le CNAME renvoie vers un autre nom au lieu de donner directement une adresse.",
     "Alias d'un nom vers un autre nom."),
    ("Que fait chmod 640 sur un fichier ?",
     "Lecture et écriture pour le propriétaire (6), lecture seule pour le groupe (4), aucun droit pour les autres (0).",
     "Ainsi, seul le propriétaire peut écrire, le groupe peut lire, et les autres n'ont accès à rien.",
     "rw- r-- --- : propriétaire lit et écrit, groupe lit, autres rien."),
    ("À quoi sert une liveness probe dans Kubernetes ?",
     "Si la liveness probe échoue, le kubelet redémarre le conteneur. Elle sert à sortir d'un processus bloqué qui ne se rétablira pas seul.",
     "En clair : quand la sonde ne répond plus, le conteneur est redémarré automatiquement.",
     "Échec de la sonde : le kubelet redémarre le conteneur."),
    ("Quelle différence entre ENTRYPOINT et CMD dans un Dockerfile ?",
     "ENTRYPOINT fixe l'exécutable lancé. CMD donne les arguments par défaut, remplacés par ceux passés à docker run.",
     "Pour résumer : ENTRYPOINT, c'est le programme ; CMD, ce sont ses arguments par défaut.",
     "ENTRYPOINT : l'exécutable. CMD : arguments par défaut, remplaçables."),
    ("Que mesure le load average sous Linux ?",
     "Le nombre moyen de tâches exécutables ou bloquées en attente non interruptible (état D), sur 1, 5 et 15 minutes.",
     "Autrement dit, c'est la file moyenne des tâches qui tournent ou attendent, sur trois durées.",
     "Moyenne des tâches en état R ou D sur 1, 5 et 15 min."),
    ("À quoi sert le champ TTL d'un paquet IP ?",
     "Chaque routeur décrémente le TTL de 1. À 0, le paquet est jeté et un ICMP Time Exceeded repart vers la source. Cela évite qu'un paquet tourne sans fin dans une boucle.",
     "Dit simplement, le TTL limite le nombre de routeurs qu'un paquet peut traverser.",
     "Décrémenté à chaque saut ; à 0 le paquet est jeté (ICMP Time Exceeded)."),
    ("Quelle différence entre un load balancer de couche 4 et de couche 7 ?",
     "Un load balancer de couche 4 répartit des connexions TCP ou UDP sans lire leur contenu. Un load balancer de couche 7 lit la requête HTTP et peut router selon le chemin ou l'en-tête Host.",
     "En résumé, la couche 4 voit des connexions, la couche 7 voit des requêtes HTTP.",
     "L4 : connexions TCP/UDP. L7 : lit HTTP, route par chemin ou Host."),
    ("Que fait set -e dans un script bash ?",
     "Le script s'arrête dès qu'une commande renvoie un code non nul, sauf dans la condition d'un if, dans une liste && ou ||, et pour les commandes d'une pipeline autres que la dernière (sans pipefail).",
     "Autrement dit, la première erreur arrête le script, avec quelques exceptions.",
     "Arrêt à la première commande en échec, sauf if, &&, || et pipeline."),
    ("À quoi sert le NAT ?",
     "Le NAT réécrit les adresses IP (et souvent les ports) au passage d'un routeur, pour que plusieurs machines en adresses privées partagent une adresse publique.",
     "En clair, plusieurs machines internes sortent sur Internet avec une seule adresse.",
     "Réécriture d'adresses et de ports ; partage d'une IP publique."),
    ("Que veut dire qu'un script de déploiement est idempotent ?",
     "Le relancer plusieurs fois donne le même état final qu'une seule exécution : la deuxième fois, il ne change plus rien.",
     "Dit autrement, on peut le rejouer sans risque, le résultat reste le même.",
     "Même état final, qu'on le lance une fois ou plusieurs."),
    ("Quelle différence entre un volume Docker et un bind mount ?",
     "Un volume est créé et géré par Docker dans son propre répertoire. Un bind mount monte dans le conteneur un chemin précis de la machine hôte.",
     "Pour résumer : le volume appartient à Docker, le bind mount pointe sur un dossier de l'hôte.",
     "Volume : géré par Docker. Bind mount : chemin de l'hôte."),
    ("Que fait la commande ss -tlnp ?",
     "Elle liste les sockets TCP en écoute (-t, -l), avec les adresses et ports en numérique (-n) et le processus propriétaire (-p).",
     "En clair, elle montre quels programmes écoutent sur quels ports TCP.",
     "Sockets TCP en écoute, numérique, avec le processus."),
    ("Qu'est-ce qu'un déploiement blue-green ?",
     "On garde deux environnements identiques. On déploie sur celui qui ne reçoit pas le trafic, on le teste, puis on bascule le trafic. Le retour arrière consiste à rebasculer.",
     "Autrement dit, la nouvelle version tourne à côté de l'ancienne jusqu'à la bascule.",
     "Deux environnements, bascule du trafic, retour arrière par rebascule."),
]

# (question, correct short answer, wrong answer, rewording of the wrong one, reference)
FAUSSES = [
    ("Quel port TCP HTTPS utilise-t-il par défaut ?",
     "HTTPS utilise par défaut le port TCP 443.",
     "HTTPS utilise par défaut le port TCP 8443.", None,
     "Port 443."),
    ("Que fait git reset --hard HEAD~1 ?",
     "Il retire le dernier commit de la branche et remet l'index et les fichiers de travail à l'état du commit précédent. Les modifications non commitées sont perdues.",
     "Il annule le dernier commit en créant un nouveau commit inverse, sans toucher à l'historique ni aux fichiers non commités.", None,
     "Recule la branche d'un commit, écrase index et fichiers de travail."),
    ("Quel signal la commande kill envoie-t-elle sans option ?",
     "Sans option, kill envoie SIGTERM (15), que le processus peut intercepter pour s'arrêter proprement.",
     "Sans option, kill envoie SIGKILL (9), que le processus ne peut pas intercepter.", None,
     "SIGTERM (15)."),
    ("À quelle couche du modèle OSI appartient IP ?",
     "IP appartient à la couche 3, la couche réseau.",
     "IP appartient à la couche 4, la couche transport.", None,
     "Couche 3, réseau."),
    ("Combien d'adresses contient un réseau IPv4 en /30 ?",
     "Un /30 contient 4 adresses, dont 2 utilisables par des hôtes.",
     "Un /30 contient 8 adresses, dont 6 utilisables par des hôtes.", None,
     "4 adresses, 2 utilisables."),
    ("Sur quel port un serveur DNS répond-il ?",
     "Un serveur DNS répond sur le port 53, en UDP, et en TCP pour les grosses réponses et les transferts de zone.",
     "Un serveur DNS répond sur le port UDP 67.",
     "Autrement dit, toutes les requêtes DNS passent par le port 67 en UDP.",
     "Port 53, UDP et TCP."),
    ("Que signifie le code HTTP 401 ?",
     "401 Unauthorized : la requête n'est pas authentifiée, les identifiants manquent ou sont invalides.",
     "401 signifie que la ressource demandée n'existe pas sur le serveur.",
     "En clair, l'URL ne correspond à aucune ressource connue.",
     "Non authentifié : identifiants absents ou invalides."),
    ("Que fait docker compose down ?",
     "Il arrête et supprime les conteneurs et les réseaux du projet. Les volumes nommés sont gardés, sauf avec -v.",
     "Il met les conteneurs du projet en pause sans rien supprimer ; docker compose up les reprend là où ils étaient.",
     "Dit autrement, c'est une simple pause, tout reste en place.",
     "Arrête et supprime conteneurs et réseaux ; volumes gardés sauf -v."),
    ("Que signifie l'expression cron */15 * * * * ?",
     "La tâche s'exécute toutes les 15 minutes (à 0, 15, 30 et 45 de chaque heure).",
     "La tâche s'exécute toutes les 15 heures.",
     "Autrement dit, elle tourne une fois toutes les quinze heures.",
     "Toutes les 15 minutes."),
    ("Que contient le fichier /etc/resolv.conf ?",
     "La configuration du résolveur DNS : les serveurs de noms (nameserver) et les domaines de recherche (search).",
     "La table de routage IP de la machine.",
     "En clair, c'est là que le noyau lit ses routes.",
     "Serveurs DNS (nameserver) et domaines de recherche."),
]


def rallonge(texte, reform, k):
    return f"{INTROS[k % 5]} {texte} {reform} {OUTROS[(k + 2) % 5]}"


def construit():
    paires = []
    for k, (q, court, reform, ref) in enumerate(LONGUEUR):
        paires.append({"id": k + 1, "type": "longueur", "question": q, "reference": ref,
                       "bonne": court, "autre": rallonge(court, reform, k)})
    for k, (q, bonne, fausse, reform, ref) in enumerate(FAUSSES):
        n = len(LONGUEUR) + k + 1
        typ = "fausse" if reform is None else "fausse-longue"
        autre = fausse if reform is None else rallonge(fausse, reform, k)
        paires.append({"id": n, "type": typ, "question": q, "reference": ref,
                       "bonne": bonne, "autre": autre})
    return paires


if __name__ == "__main__":
    import sys
    en = sys.argv[1:] == ["--lang", "en"]
    noms = {"longueur": "padding", "fausse": "wrong", "fausse-longue": "wrong-padded"}
    p = construit()
    Path(__file__).with_name("paires.json").write_text(json.dumps(p, ensure_ascii=False, indent=1))
    for t in ("longueur", "fausse", "fausse-longue"):
        s = [x for x in p if x["type"] == t]
        lb = sum(len(x["bonne"]) for x in s) / len(s)
        la = sum(len(x["autre"]) for x in s) / len(s)
        if en:
            print(f"{noms[t]:14s} {len(s):2d} pairs    good: {lb:5.0f} chars   other: {la:5.0f} chars")
        else:
            print(f"{t:14s} {len(s):2d} paires   bonne : {lb:5.0f} car.   autre : {la:5.0f} car.")
