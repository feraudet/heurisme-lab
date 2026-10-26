#!/usr/bin/env python3
"""Banc de l'article heurisme.fr sur Scion : N agents qui pushent sur un même repo git.

Deux modèles, sur la même charge (N commits, chacun sur un fichier différent) :
  A. git classique : chaque agent a son clone, commit, push ; refusé, il fait fetch + rebase et repushe.
  B. merge côté serveur : les changesets arrivent au serveur, qui construit le commit lui-même
     (plumbing git dans le repo bare) et avance main par compare-and-swap (update-ref <new> <old>).
     C'est le modèle de Scion ; ici le CAS se fait sur un fichier de ref git, pas sur une ligne Spanner.

Seule dépendance : git. Les temps varient d'un run à l'autre, les compteurs aussi (course réelle).
"""
import os, subprocess, sys, tempfile, threading, time, platform

N_LISTE = [1, 10, 50, 200]
OUVRIERS_SERVEUR = [1, 8]     # threads du serveur dans le modèle B
MAX_TENTATIVES = 2000          # garde-fou, jamais atteint dans nos runs

ENV = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null",
           GIT_AUTHOR_DATE="2026-10-26T12:00:00+0100", GIT_COMMITTER_DATE="2026-10-26T12:00:00+0100",
           GIT_TERMINAL_PROMPT="0",
           # pas de gc ni de maintenance auto en fond : elles nettoient objects/ pendant qu'un rebase y écrit
           GIT_CONFIG_COUNT="2", GIT_CONFIG_KEY_0="gc.auto", GIT_CONFIG_VALUE_0="0",
           GIT_CONFIG_KEY_1="maintenance.auto", GIT_CONFIG_VALUE_1="false")


def git(*args, cwd=None, env=None, entree=None, ok=True):
    r = subprocess.run(["git", *args], cwd=cwd, env=env or ENV, input=entree,
                       capture_output=True, text=True)
    if ok and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} : {r.stderr.strip()}")
    return r


def ident(nom):
    return ["-c", f"user.name={nom}", "-c", f"user.email={nom}@banc.invalid"]


def repo_initial(racine):
    nu = os.path.join(racine, "serveur.git")
    git("init", "-q", "--bare", "-b", "main", nu)
    graine = os.path.join(racine, "graine")
    git("init", "-q", "-b", "main", graine)
    with open(os.path.join(graine, "README"), "w") as f:
        f.write("monorepo du banc de test\n")
    git("add", "README", cwd=graine)
    git(*ident("graine"), "commit", "-q", "-m", "init", cwd=graine)
    git("push", "-q", nu, "main", cwd=graine)
    return nu


# ---------- A. git classique ----------
def modele_a(n):
    with tempfile.TemporaryDirectory() as racine:
        nu = repo_initial(racine)
        clones = []
        for i in range(n):                       # préparation, hors chrono
            c = os.path.join(racine, f"agent{i:03d}")
            git("clone", "-q", nu, c)
            with open(os.path.join(c, f"agent{i:03d}.txt"), "w") as f:
                f.write(f"changement de l'agent {i}\n")
            git("add", ".", cwd=c)
            git(*ident(f"agent{i:03d}"), "commit", "-q", "-m", f"agent {i}", cwd=c)
            clones.append(c)
        stats = [dict(push=0, refus_nff=0, refus_verrou=0, autres=0, rebase=0, fin=0.0) for _ in range(n)]
        depart = threading.Barrier(n + 1)

        def agent(i):
            c, s = clones[i], stats[i]
            depart.wait()
            for _ in range(MAX_TENTATIVES):
                s["push"] += 1
                r = git("push", "-q", "origin", "main", cwd=c, ok=False)
                if r.returncode == 0:
                    s["fin"] = time.perf_counter()
                    return
                err = r.stderr
                if "lock" in err:
                    s["refus_verrou"] += 1
                elif "non-fast-forward" in err or "fetch first" in err or "rejected" in err:
                    s["refus_nff"] += 1
                else:
                    s["autres"] += 1
                git("fetch", "-q", "origin", cwd=c)
                git(*ident(f"agent{i:03d}"), "rebase", "-q", "origin/main", cwd=c)
                s["rebase"] += 1
            raise RuntimeError(f"agent {i} : {MAX_TENTATIVES} tentatives")

        erreurs = []

        def agent_sur(i):
            try:
                agent(i)
            except Exception as e:          # une erreur d'agent arrête le banc de test, jamais un chiffre faux
                erreurs.append(e)

        fils = [threading.Thread(target=agent_sur, args=(i,)) for i in range(n)]
        for t in fils: t.start()
        depart.wait(); t0 = time.perf_counter()
        for t in fils: t.join()
        if erreurs:
            raise erreurs[0]
        duree = max(s["fin"] for s in stats) - t0
        fichiers = len(git("ls-tree", "--name-only", "main", cwd=nu).stdout.split())
        commits = int(git("rev-list", "--count", "main", cwd=nu).stdout)
        return stats, duree, fichiers, commits


# ---------- B. merge côté serveur, CAS sur la ref ----------
def modele_b(n, ouvriers):
    with tempfile.TemporaryDirectory() as racine:
        nu = repo_initial(racine)
        file = list(range(n))
        verrou_file = threading.Lock()
        stats = dict(cas_ok=0, cas_rate=0)
        verrou_stats = threading.Lock()

        def ouvrier(k):
            index = os.path.join(racine, f"index{k}")
            env = dict(ENV, GIT_INDEX_FILE=index)
            while True:
                with verrou_file:
                    if not file: return
                    i = file.pop(0)
                chemin = f"agent{i:03d}.txt"
                blob = git("hash-object", "-w", "--stdin", cwd=nu,
                           entree=f"changement de l'agent {i}\n").stdout.strip()
                while True:
                    tip = git("rev-parse", "refs/heads/main", cwd=nu).stdout.strip()
                    git("read-tree", tip, cwd=nu, env=env)
                    git("update-index", "--add", "--cacheinfo", f"100644,{blob},{chemin}", cwd=nu, env=env)
                    arbre = git("write-tree", cwd=nu, env=env).stdout.strip()
                    neuf = git(*ident(f"agent{i:03d}"), "commit-tree", arbre, "-p", tip,
                               "-m", f"agent {i}", cwd=nu).stdout.strip()
                    r = git("update-ref", "refs/heads/main", neuf, tip, cwd=nu, ok=False)
                    with verrou_stats:
                        stats["cas_ok" if r.returncode == 0 else "cas_rate"] += 1
                    if r.returncode == 0: break

        fils = [threading.Thread(target=ouvrier, args=(k,)) for k in range(ouvriers)]
        t0 = time.perf_counter()
        for t in fils: t.start()
        for t in fils: t.join()
        duree = time.perf_counter() - t0
        fichiers = len(git("ls-tree", "--name-only", "main", cwd=nu).stdout.split())
        commits = int(git("rev-list", "--count", "main", cwd=nu).stdout)
        return stats, duree, fichiers, commits


def ordres_de_grandeur():
    print("== 1. Les chiffres d'Anthropic, recalculés")
    co, taille = 25_000_000, 25e9
    print(f"25 M checkouts CI/jour x 25 Go (copie de travail compressée) = {co * taille / 1e15:.0f} Po/jour"
          "   (article : « more than 600 PB »)")
    print(f"merges/jour : mai 2 500 -> septembre 30 000 = x{30000 / 2500:.0f}")
    print(f"30 000 merges/jour = {30000 / 24:.0f} merges/heure en moyenne = un toutes les {86400 / 30000:.1f} s")
    print()


def main():
    print("$ python3 course_push.py")
    print(git("--version").stdout.strip(), "|", "Python", platform.python_version(), "|",
          platform.system(), platform.machine(), "|", os.cpu_count(), "CPU")
    print()
    ordres_de_grandeur()
    print("== 2. Modèle A : git classique, chaque agent pushe depuis son clone")
    print("N agents | push tentés | refus non-fast-forward | refus verrou | rebases | max par agent | durée | fichiers sur main | commits")
    for n in N_LISTE:
        stats, duree, fich, com = modele_a(n)
        push = sum(s["push"] for s in stats)
        print(f"{n:8d} | {push:11d} | {sum(s['refus_nff'] for s in stats):22d} | "
              f"{sum(s['refus_verrou'] for s in stats):12d} | {sum(s['rebase'] for s in stats):7d} | "
              f"{max(s['push'] for s in stats):13d} | {duree:5.1f} s | {fich - 1:17d} | {com - 1}")
        sys.stdout.flush()
    print("(fichiers et commits : README et commit initial retirés)")
    print()
    print("== 3. Modèle B : le serveur construit les commits, CAS sur main")
    print("threads | N changesets | CAS réussis | CAS ratés (main a bougé) | durée | fichiers sur main | commits")
    for ouvriers in OUVRIERS_SERVEUR:
        for n in N_LISTE:
            stats, duree, fich, com = modele_b(n, ouvriers)
            print(f"{ouvriers:7d} | {n:12d} | {stats['cas_ok']:11d} | {stats['cas_rate']:24d} | {duree:5.1f} s | {fich - 1:17d} | {com - 1}")
            sys.stdout.flush()
    print("(un CAS raté recommence sur le nouveau tip, sans clone, sans fetch, sans rebase côté client)")
    print()
    print("exit=0")


if __name__ == "__main__":
    main()
