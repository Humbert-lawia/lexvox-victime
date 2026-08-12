#!/usr/bin/env python3
"""Verrou cooperatif (claim / lease) sur les files de production LEXVOX.

Trois acteurs ecrivent sur main : sessions interactives, LEXVOX SEO Bot et
LAWIA Pipeline. Les files (queue-aivf.json, queue-wp.json) portent bien un
status todo/done, mais PAS l'information "qui travaille dessus en ce moment".
D'ou les collisions : deux acteurs prennent le meme item, produisent deux fois
le meme article, et se marchent dessus au rebase.

Ce module ajoute cette information manquante, sans dependance externe :

    item["claim"] = {"by": acteur, "at": ISO, "expires": ISO}
    item["gate"]  = {"question": str, "since": ISO, "by": acteur}

Un item est PRENABLE s'il est status "todo", sans gate ouverte, et sans claim
vivante. Une claim expiree est consideree comme libre (l'acteur a plante ou a
ete interrompu) : elle est reprise avec un avertissement.

Le verrou n'a de valeur que s'il est VISIBLE des autres acteurs : les commandes
mutantes font donc par defaut `git pull --rebase` avant et `git commit` +
`git push` apres (option --no-sync pour tester en local). En cas de push
rejete, la mutation est rejouee sur la version fraiche de la file, jusqu'a
5 tentatives (backoff 2/4/8/16 s) : jamais de marqueur de conflit, jamais de
perte de l'ecriture d'un autre acteur.

Usage typique d'une routine WordPress (3 articles/jour) :

    python3 tools/queue_lease.py claim --queue wp -n 3 --actor lawia-pipeline
    ... production + QA + publication ...
    python3 tools/queue_lease.py done --queue wp --id 4 --score 87 --url https://...

Et si la routine doit rendre la main a Me Humbert :

    python3 tools/queue_lease.py gate --queue wp --id 5 \\
        --question "Score NW plafonne a 82 : derogation editoriale ?"

Code retour : 0 = succes, 1 = echec (item deja pris, lease detenue par un
autre, validation KO...).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# TTL par defaut : duree de production realiste d'un item de la file.
QUEUES = {
    "aivf": {"path": "queue-aivf.json", "ttl": 180, "label": "LEXVOX-AIVF"},
    "wp": {"path": "queue-wp.json", "ttl": 120, "label": "LEXVOX-WP"},
}

MAX_PUSH_ATTEMPTS = 5
BACKOFF = [2, 4, 8, 16]
LOCK_STALE_SECONDS = 900  # verrou local considere mort au-dela de 15 min


# --------------------------------------------------------------------------
# Temps
# --------------------------------------------------------------------------
def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_iso(value):
    """Parse une date ISO ; tolere le suffixe Z. Retourne None si illisible."""
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def humanize(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    return f"{sign}{total // 3600}h{(total % 3600) // 60:02d}"


# --------------------------------------------------------------------------
# Acteur
# --------------------------------------------------------------------------
def resolve_actor(explicit=None) -> str:
    """--actor > $LEXVOX_ACTOR > git user.name > 'inconnu'."""
    if explicit:
        return explicit
    env = os.environ.get("LEXVOX_ACTOR")
    if env:
        return env
    try:
        out = subprocess.run(
            ["git", "config", "user.name"], cwd=ROOT,
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "inconnu"


# --------------------------------------------------------------------------
# Fichier de file
# --------------------------------------------------------------------------
def queue_path(queue: str) -> Path:
    return ROOT / QUEUES[queue]["path"]


def load(queue: str) -> dict:
    return json.loads(queue_path(queue).read_text(encoding="utf-8"))


def save(queue: str, data: dict) -> None:
    """Ecriture atomique, au format exact du fichier (indent 2, sans newline)."""
    path = queue_path(queue)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def find(data: dict, item_id: int):
    for item in data.get("articles", []):
        if item.get("id") == item_id:
            return item
    return None


# --------------------------------------------------------------------------
# Etat d'un item
# --------------------------------------------------------------------------
def claim_state(item: dict, moment=None):
    """Retourne (etat, claim) : 'libre' | 'vivante' | 'expiree'."""
    moment = moment or now()
    claim = item.get("claim")
    if not isinstance(claim, dict) or not claim.get("by"):
        return "libre", None
    expires = parse_iso(claim.get("expires"))
    if expires is None or expires <= moment:
        return "expiree", claim
    return "vivante", claim


def is_gated(item: dict) -> bool:
    gate = item.get("gate")
    return isinstance(gate, dict) and bool(gate.get("question"))


def blocking_reason(item: dict, actor: str, moment=None):
    """None si l'item est prenable par `actor`, sinon la raison du blocage.

    L'ordre compte : une lease vivante prime sur le status, sinon le refus
    afficherait "status in_progress" au lieu du nom de l'acteur qui detient
    l'item. Et un item 'in_progress' dont la lease a EXPIRE est reprenable,
    sans quoi une routine interrompue bloquerait sa tranche pour toujours.
    """
    state, claim = claim_state(item, moment)
    if state == "vivante" and claim.get("by") != actor:
        reste = parse_iso(claim["expires"]) - (moment or now())
        return f"deja pris par {claim['by']} (lease encore {humanize(reste)})"
    if is_gated(item):
        return f"decision utilisateur en attente : {item['gate'].get('question')}"
    status = item.get("status")
    if status in ("todo", "in_progress"):
        return None
    return f"status '{status}' (non reprenable)"


def claimable(data: dict, actor: str, site=None, moment=None):
    moment = moment or now()
    out = []
    for item in data.get("articles", []):
        if site and item.get("site") != site:
            continue
        if blocking_reason(item, actor, moment) is None:
            out.append(item)
    return out


# --------------------------------------------------------------------------
# Verrou local (protege deux processus de la MEME machine)
# --------------------------------------------------------------------------
class LocalLock:
    def __init__(self, queue: str):
        self.path = ROOT / f".queue-lease-{queue}.lock"
        self.held = False

    def __enter__(self):
        for attempt in range(30):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
                os.write(fd, f"{os.getpid()} {iso(now())}\n".encode())
                os.close(fd)
                self.held = True
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                except OSError:
                    continue
                if age > LOCK_STALE_SECONDS:
                    print(f"AVERTISSEMENT : verrou local mort ({int(age)} s), reprise.")
                    self.path.unlink(missing_ok=True)
                    continue
                time.sleep(1)
        raise SystemExit(f"Verrou local {self.path.name} occupe : un autre processus travaille sur cette file.")

    def __exit__(self, *exc):
        if self.held:
            self.path.unlink(missing_ok=True)
        return False


# --------------------------------------------------------------------------
# Git
# --------------------------------------------------------------------------
def git(*args, check=True, timeout=180):
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} : {proc.stderr.strip() or proc.stdout.strip()}")
    return proc


def current_branch() -> str:
    return git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()


def file_is_dirty(queue: str) -> bool:
    rel = QUEUES[queue]["path"]
    return bool(git("status", "--porcelain", "--", rel).stdout.strip())


def restore_file(queue: str) -> None:
    rel = QUEUES[queue]["path"]
    git("restore", "--staged", "--worktree", "--source=HEAD", "--", rel, check=False)


def apply_with_sync(queue: str, mutate, message: str, sync: bool, branch=None):
    """Applique `mutate(data)` sur la file, puis pull/commit/push si sync.

    `mutate` recoit le contenu FRAIS de la file a chaque tentative et retourne
    (ok, lignes_de_compte_rendu). Si ok est False, rien n'est ecrit.
    Rejouer la mutation sur la version fraiche evite tout conflit de rebase
    sur le JSON : on ne resout pas un conflit, on ne le cree jamais.
    """
    rel = QUEUES[queue]["path"]
    branch = branch or (current_branch() if sync else None)

    if sync and file_is_dirty(queue):
        raise SystemExit(
            f"{rel} a des modifications non committees : commit ou restaure-les avant "
            f"(ou relance avec --no-sync pour un essai local)."
        )

    for attempt in range(MAX_PUSH_ATTEMPTS):
        if sync:
            pull = git("pull", "--rebase", "origin", branch, check=False)
            if pull.returncode != 0:
                git("rebase", "--abort", check=False)
                raise SystemExit(f"git pull --rebase origin {branch} a echoue :\n{pull.stderr.strip()}")

        data = load(queue)
        ok, report = mutate(data)
        if not ok:
            for line in report:
                print(line)
            return False
        save(queue, data)

        if not sync:
            for line in report:
                print(line)
            print(f"\n(--no-sync : {rel} modifie localement, ni committe ni pousse.)")
            return True

        git("add", "--", rel)
        if not git("diff", "--cached", "--quiet", "--", rel, check=False).returncode:
            print("Aucun changement effectif a committer.")
            return True
        git("commit", "-m", message)

        push = git("push", "origin", f"HEAD:{branch}", check=False, timeout=300)
        if push.returncode == 0:
            for line in report:
                print(line)
            print(f"\nVerrou publie sur origin/{branch} (visible des autres acteurs).")
            return True

        # Push rejete : on annule NOTRE commit sans toucher au reste de l'arbre,
        # puis on rejoue la mutation sur la version fraiche de la file.
        git("reset", "--soft", "HEAD~1")
        restore_file(queue)
        wait = BACKOFF[min(attempt, len(BACKOFF) - 1)]
        print(f"Push rejete (tentative {attempt + 1}/{MAX_PUSH_ATTEMPTS}), nouvelle tentative dans {wait} s...")
        time.sleep(wait)

    raise SystemExit(f"Impossible de publier le verrou apres {MAX_PUSH_ATTEMPTS} tentatives.")


# --------------------------------------------------------------------------
# Commandes
# --------------------------------------------------------------------------
def describe(item: dict) -> str:
    site = f" [{item['site']}]" if item.get("site") else ""
    return f"id {item['id']}{site} {item['slug']}"


def cmd_status(args) -> int:
    moment = now()
    for queue in ([args.queue] if args.queue != "all" else list(QUEUES)):
        data = load(queue)
        articles = data.get("articles", [])
        counts = {}
        for item in articles:
            counts[item.get("status", "?")] = counts.get(item.get("status", "?"), 0) + 1
        print(f"=== {QUEUES[queue]['label']} ({QUEUES[queue]['path']}) — {len(articles)} items")
        print("    " + "  ".join(f"{k}: {v}" for k, v in sorted(counts.items())))

        vivantes, expirees, gates = [], [], []
        for item in articles:
            state, claim = claim_state(item, moment)
            if state == "vivante":
                vivantes.append((item, claim))
            elif state == "expiree":
                expirees.append((item, claim))
            if is_gated(item):
                gates.append(item)

        if vivantes:
            print(f"    Leases actives ({len(vivantes)}) :")
            for item, claim in vivantes:
                reste = parse_iso(claim["expires"]) - moment
                print(f"      {describe(item)} — {claim['by']}, expire dans {humanize(reste)}")
        if expirees:
            print(f"    Leases EXPIREES ({len(expirees)}, reprenables) :")
            for item, claim in expirees:
                print(f"      {describe(item)} — {claim['by']}, depuis {claim.get('at', '?')}")
        if gates:
            print(f"    Decisions en attente de Me Humbert ({len(gates)}) :")
            for item in gates:
                print(f"      {describe(item)} — {item['gate'].get('question')}")
        if not (vivantes or expirees or gates):
            print("    Aucune lease ni decision en attente.")

        libres = claimable(data, resolve_actor(args.actor), site=getattr(args, "site", None), moment=moment)
        print(f"    Prochain prenable : {describe(libres[0]) if libres else '(aucun)'}")
        print()
    return 0


def cmd_next(args) -> int:
    actor = resolve_actor(args.actor)
    data = load(args.queue)
    libres = claimable(data, actor, site=args.site)[: args.count]
    if args.json:
        print(json.dumps(libres, ensure_ascii=False, indent=2))
        return 0 if libres else 1
    if not libres:
        print("Aucun item prenable (file epuisee, tout est pris, ou decisions en attente).")
        return 1
    for item in libres:
        print(f"{describe(item)} — {item['title']}")
    return 0


def cmd_claim(args) -> int:
    actor = resolve_actor(args.actor)
    ttl = args.ttl or QUEUES[args.queue]["ttl"]
    moment = now()
    expires = moment + timedelta(minutes=ttl)

    def mutate(data):
        report = []
        if args.id:
            cibles, refuses = [], []
            for item_id in args.id:
                item = find(data, item_id)
                if item is None:
                    refuses.append(f"REFUS  id {item_id} : introuvable dans la file.")
                    continue
                reason = blocking_reason(item, actor, moment)
                if reason:
                    refuses.append(f"REFUS  {describe(item)} : {reason}")
                else:
                    cibles.append(item)
            if refuses:
                return False, refuses + ["", "Aucun verrou pose (demande explicite : tout ou rien)."]
        else:
            cibles = claimable(data, actor, site=args.site, moment=moment)[: args.count]
            if not cibles:
                return False, ["Aucun item prenable (file epuisee, tout est pris, ou decisions en attente)."]

        for item in cibles:
            state, claim = claim_state(item, moment)
            if state == "expiree":
                report.append(f"       (lease expiree de {claim['by']} reprise)")
            item["status"] = "in_progress"
            item["claim"] = {"by": actor, "at": iso(moment), "expires": iso(expires)}
            report.append(f"PRIS   {describe(item)} — {item['title']}")
        report.append(f"\nActeur : {actor} — lease {ttl} min, expire a {iso(expires)}.")
        return True, report

    ids = ",".join(str(i) for i in args.id) if args.id else f"{args.count} item(s)"
    message = f"file {args.queue} : claim {ids} par {actor}"
    return 0 if apply_with_sync(args.queue, mutate, message, not args.no_sync, args.branch) else 1


def _held_by(item, actor, force):
    """Verifie que `actor` detient la lease de l'item."""
    claim = item.get("claim")
    if not isinstance(claim, dict) or not claim.get("by"):
        return None if force else "aucune lease posee sur cet item"
    if claim["by"] != actor and not force:
        return f"lease detenue par {claim['by']} (utilise --force pour passer outre)"
    return None


def cmd_renew(args) -> int:
    actor = resolve_actor(args.actor)
    ttl = args.ttl or QUEUES[args.queue]["ttl"]
    expires = now() + timedelta(minutes=ttl)

    def mutate(data):
        item = find(data, args.id)
        if item is None:
            return False, [f"REFUS  id {args.id} : introuvable."]
        problem = _held_by(item, actor, args.force)
        if problem:
            return False, [f"REFUS  {describe(item)} : {problem}"]
        item.setdefault("claim", {"by": actor, "at": iso(now())})
        item["claim"]["by"] = actor
        item["claim"]["expires"] = iso(expires)
        return True, [f"PROLONGE {describe(item)} — lease jusqu'a {iso(expires)}."]

    message = f"file {args.queue} : renouvellement lease id {args.id} par {actor}"
    return 0 if apply_with_sync(args.queue, mutate, message, not args.no_sync, args.branch) else 1


def cmd_release(args) -> int:
    actor = resolve_actor(args.actor)

    def mutate(data):
        item = find(data, args.id)
        if item is None:
            return False, [f"REFUS  id {args.id} : introuvable."]
        problem = _held_by(item, actor, args.force)
        if problem:
            return False, [f"REFUS  {describe(item)} : {problem}"]
        item.pop("claim", None)
        if item.get("status") == "in_progress":
            item["status"] = "todo"
        if args.reason:
            item["note_lease"] = args.reason
        return True, [f"RENDU  {describe(item)} — repasse en 'todo'."]

    message = f"file {args.queue} : release id {args.id} par {actor}"
    return 0 if apply_with_sync(args.queue, mutate, message, not args.no_sync, args.branch) else 1


def cmd_done(args) -> int:
    actor = resolve_actor(args.actor)

    def mutate(data):
        item = find(data, args.id)
        if item is None:
            return False, [f"REFUS  id {args.id} : introuvable."]
        problem = _held_by(item, actor, args.force)
        if problem:
            return False, [f"REFUS  {describe(item)} : {problem}"]
        if args.score is not None and args.score < 85 and not args.derogation:
            return False, [
                f"REFUS  {describe(item)} : score NeuronWriter {args.score} < 85.",
                "       Seuil de publication (politique Me Humbert) : >= 85, ou derogation",
                "       documentee si > 80 — relancer avec --derogation \"<motif>\".",
            ]
        if args.derogation and (args.score is None or args.score <= 80):
            return False, ["REFUS  derogation editoriale impossible : elle exige un score > 80."]
        item["status"] = "done"
        item["date"] = args.date or now().strftime("%Y-%m-%d")
        if args.score is not None:
            item["neuronwriter_score"] = args.score
        if args.url:
            item["url"] = args.url
        if args.derogation:
            item["derogation"] = args.derogation
        item.pop("claim", None)
        item.pop("gate", None)
        return True, [f"FAIT   {describe(item)} — status 'done' le {item['date']}."]

    message = f"file {args.queue} : done id {args.id} par {actor}"
    return 0 if apply_with_sync(args.queue, mutate, message, not args.no_sync, args.branch) else 1


def cmd_gate(args) -> int:
    actor = resolve_actor(args.actor)

    def mutate(data):
        item = find(data, args.id)
        if item is None:
            return False, [f"REFUS  id {args.id} : introuvable."]
        item["gate"] = {"question": args.question, "since": iso(now()), "by": actor}
        item.pop("claim", None)
        if item.get("status") == "in_progress":
            item["status"] = "todo"
        return True, [
            f"MAIN RENDUE  {describe(item)}",
            f"       Question a Me Humbert : {args.question}",
            "       L'item est retire de la selection automatique jusqu'a 'ungate'.",
        ]

    message = f"file {args.queue} : decision utilisateur demandee sur id {args.id}"
    return 0 if apply_with_sync(args.queue, mutate, message, not args.no_sync, args.branch) else 1


def cmd_ungate(args) -> int:
    def mutate(data):
        item = find(data, args.id)
        if item is None:
            return False, [f"REFUS  id {args.id} : introuvable."]
        if not is_gated(item):
            return False, [f"REFUS  {describe(item)} : aucune decision en attente."]
        question = item["gate"].get("question")
        item.pop("gate", None)
        if args.decision:
            item["decision"] = args.decision
        report = [f"DEBLOQUE  {describe(item)} (question levee : {question})"]
        if args.decision:
            report.append(f"          Decision : {args.decision}")
        return True, report

    message = f"file {args.queue} : decision rendue sur id {args.id}"
    return 0 if apply_with_sync(args.queue, mutate, message, not args.no_sync, args.branch) else 1


NW_MARKER = re.compile(r"<!--\s*NEURONWRITER SCORE:(.*?)-->", re.IGNORECASE | re.DOTALL)


def has_derogation(item: dict) -> bool:
    """Une derogation editoriale est-elle documentee pour cet item ?

    Source de verite = le marqueur <!-- NEURONWRITER SCORE: ... --> de l'article
    atelier (regle CLAUDE.md). Le champ 'derogation' de la file, pose par la
    commande `done`, sert de repli pour les items WordPress qui n'ont pas de
    HTML local.
    """
    if item.get("derogation"):
        return True
    slug = item.get("slug")
    if not slug:
        return False
    article = ROOT / "actualites" / f"{slug}.html"
    if not article.exists():
        return False
    marker = NW_MARKER.search(article.read_text(encoding="utf-8", errors="ignore"))
    return bool(marker and "derogation" in marker.group(1).lower())


def cmd_validate(args) -> int:
    """Controle d'integrite des verrous — appele par la CI (validate.yml)."""
    moment = now()
    problems = []
    for queue in QUEUES:
        path = queue_path(queue)
        if not path.exists():
            continue
        data = load(queue)
        seen = set()
        for item in data.get("articles", []):
            item_id = item.get("id")
            label = f"{QUEUES[queue]['path']} id {item_id}"
            if item_id in seen:
                problems.append(f"{label} : id duplique dans la file")
            seen.add(item_id)

            claim = item.get("claim")
            if claim is not None:
                if not isinstance(claim, dict) or not claim.get("by"):
                    problems.append(f"{label} : champ 'claim' malforme (attendu {{by, at, expires}})")
                else:
                    for key in ("at", "expires"):
                        if parse_iso(claim.get(key)) is None:
                            problems.append(f"{label} : claim.{key} illisible ({claim.get(key)!r})")
                    if item.get("status") in ("done", "merged"):
                        problems.append(
                            f"{label} : status '{item['status']}' mais lease encore posee par "
                            f"{claim.get('by')} — la lease doit etre liberee a la cloture"
                        )
            if item.get("status") == "in_progress" and not claim:
                problems.append(f"{label} : status 'in_progress' sans lease — item orphelin")

            gate = item.get("gate")
            if gate is not None and (not isinstance(gate, dict) or not gate.get("question")):
                problems.append(f"{label} : champ 'gate' malforme (attendu {{question, since, by}})")

            score = item.get("neuronwriter_score")
            if item.get("status") == "done" and isinstance(score, int) and score < 85:
                if not has_derogation(item):
                    problems.append(
                        f"{label} : publie avec un score NeuronWriter {score} < 85 sans derogation "
                        f"documentee (ni champ 'derogation' dans la file, ni mention dans le marqueur "
                        f"<!-- NEURONWRITER SCORE: ... --> de l'article)"
                    )
                elif score <= 80:
                    problems.append(f"{label} : derogation documentee mais score {score} <= 80 (interdit)")

            slug = item.get("slug", "")
            if slug and not re.fullmatch(r"[a-z0-9-]+", slug):
                problems.append(f"{label} : slug non conforme ({slug!r})")

        stale = [
            item for item in data.get("articles", [])
            if claim_state(item, moment)[0] == "expiree"
        ]
        if stale and args.strict:
            for item in stale:
                problems.append(
                    f"{QUEUES[queue]['path']} id {item['id']} : lease expiree non liberee "
                    f"({item['claim'].get('by')})"
                )
        elif stale:
            print(f"Info : {len(stale)} lease(s) expiree(s) dans {QUEUES[queue]['path']} (reprenables).")

    if problems:
        print(f"{len(problems)} probleme(s) de coherence des files :")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("Files coherentes : verrous, gates et scores conformes.")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verrou cooperatif sur les files de production LEXVOX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(sp, mutating=True):
        sp.add_argument("--queue", choices=list(QUEUES), required=True, help="file ciblee")
        sp.add_argument("--actor", help="identite de l'acteur (defaut : $LEXVOX_ACTOR puis git user.name)")
        if mutating:
            sp.add_argument("--no-sync", action="store_true",
                            help="n'ecrit qu'en local : ni pull, ni commit, ni push (tests)")
            sp.add_argument("--branch", help="branche de synchronisation (defaut : branche courante)")
        return sp

    sp = sub.add_parser("status", help="etat des files : leases, gates, prochain item")
    sp.add_argument("--queue", choices=list(QUEUES) + ["all"], default="all")
    sp.add_argument("--actor")
    sp.add_argument("--site", help="filtre WordPress (medical | accident)")
    sp.set_defaults(func=cmd_status)

    sp = add_common(sub.add_parser("next", help="affiche les prochains items prenables"), mutating=False)
    sp.add_argument("-n", "--count", type=int, default=3)
    sp.add_argument("--site", help="filtre WordPress (medical | accident)")
    sp.add_argument("--json", action="store_true", help="sortie JSON exploitable par une routine")
    sp.set_defaults(func=cmd_next)

    sp = add_common(sub.add_parser("claim", help="pose un verrou sur un ou plusieurs items"))
    sp.add_argument("--id", type=int, nargs="+", help="ids explicites (defaut : les N prochains prenables)")
    sp.add_argument("-n", "--count", type=int, default=1)
    sp.add_argument("--site", help="filtre WordPress (medical | accident)")
    sp.add_argument("--ttl", type=int, help="duree de la lease en minutes")
    sp.set_defaults(func=cmd_claim)

    sp = add_common(sub.add_parser("renew", help="prolonge une lease en cours"))
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--ttl", type=int)
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_renew)

    sp = add_common(sub.add_parser("release", help="rend un item sans le publier"))
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--reason", help="motif conserve dans l'item")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_release)

    sp = add_common(sub.add_parser("done", help="cloture un item publie et libere la lease"))
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--score", type=int, help="score NeuronWriter reel (jamais invente)")
    sp.add_argument("--url", help="URL publiee")
    sp.add_argument("--date", help="date de publication (defaut : aujourd'hui, UTC)")
    sp.add_argument("--derogation", help="motif de derogation editoriale (score > 80 seulement)")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_done)

    sp = add_common(sub.add_parser("gate", help="rend la main a Me Humbert sur un item"))
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--question", required=True, help="question exacte posee a l'humain")
    sp.set_defaults(func=cmd_gate)

    sp = add_common(sub.add_parser("ungate", help="leve une decision en attente"))
    sp.add_argument("--id", type=int, required=True)
    sp.add_argument("--decision", help="decision rendue, conservee dans l'item")
    sp.set_defaults(func=cmd_ungate)

    sp = sub.add_parser("validate", help="controle d'integrite des files (CI)")
    sp.add_argument("--strict", action="store_true", help="echoue aussi sur les leases expirees")
    sp.set_defaults(func=cmd_validate)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command in ("status", "next", "validate"):
        return args.func(args)
    with LocalLock(args.queue):
        return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
