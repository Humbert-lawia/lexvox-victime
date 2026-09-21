#!/usr/bin/env bash
#
# publish-daily.sh — routine de publication quotidienne LEXVOX.
#
#   tools/publish-daily.sh victime    -> queue-aivf.json  -> Sanity (lexvox-victime.com)
#   tools/publish-daily.sh medical    -> queue-wp.json    -> medical.lexvox-avocat.fr
#   tools/publish-daily.sh accident   -> queue-wp.json    -> victime-accident.lexvox-avocat.fr
#
# La routine prend les premiers items 'todo' dans l'ordre de la file, controle
# chaque article atelier (QA + preflight), publie le premier qui passe, puis
# met a jour la file et le tracker. Un article recale n'est jamais publie et
# n'est jamais modifie : il est journalise, et la routine passe au suivant.
#
# Le mode par defaut est le dry-run : rien n'est publie sans --publish.
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

STATE="python3 tools/publish_daily_state.py"

SITE=""
COUNT=1
FORCE_SLUG=""
PUBLISH=0
AT="now"
COMMIT=0
PUSH=0
LIST_ONLY=0

usage() {
  sed -n '3,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  cat <<'USAGE'
Options :
  -n, --count N     nombre d'articles a traiter (defaut : 1)
      --slug SLUG   force cet article au lieu du premier candidat de la file
      --publish     publie reellement (sinon : dry-run, aucune ecriture distante)
      --at ISO|now  date de mise en ligne Sanity (defaut : now) [site victime]
      --commit      commit les mises a jour de file et de tracker
      --push        git pull --rebase origin main, puis push (implique --commit)
      --list        affiche les candidats de la file et sort
  -h, --help        cette aide

Codes de sortie : 0 succes | 1 usage | 2 aucun article publiable | 3 secret manquant
                  4 traitement partiel (moins d'articles publies que demande)
USAGE
}

OUT=""
# Le statut est capture d'abord : sans cela, le nettoyage ecraserait le code
# de sortie du script.
cleanup() { rc=$?; [ -n "$OUT" ] && rm -f "$OUT"; exit "$rc"; }
trap cleanup EXIT

log()  { printf '%s\n' "$*"; }
step() { printf '\n[%s] %s\n' "$1" "$2"; }
die()  { printf 'ERREUR publish-daily : %s\n' "$*" >&2; exit "${2:-1}"; }

# ---------------------------------------------------------------- arguments
[ $# -ge 1 ] || { usage; exit 1; }
SITE="$1"; shift
case "$SITE" in
  victime|medical|accident) ;;
  -h|--help) usage; exit 0 ;;
  *) die "site inconnu : $SITE (attendu : victime, medical ou accident)" ;;
esac

while [ $# -gt 0 ]; do
  case "$1" in
    -n|--count) COUNT="${2:?--count attend un nombre}"; shift 2 ;;
    --slug)     FORCE_SLUG="${2:?--slug attend un slug}"; shift 2 ;;
    --publish)  PUBLISH=1; shift ;;
    --at)       AT="${2:?--at attend une date ISO ou now}"; shift 2 ;;
    --commit)   COMMIT=1; shift ;;
    --push)     PUSH=1; COMMIT=1; shift ;;
    --list)     LIST_ONLY=1; shift ;;
    -h|--help)  usage; exit 0 ;;
    *) die "option inconnue : $1" ;;
  esac
done

case "$COUNT" in
  ''|*[!0-9]*) die "--count attend un entier positif (recu : $COUNT)" ;;
  0) die "--count 0 : rien a faire." ;;
esac

case "$SITE" in
  victime)  QA="tools/qa_article_aivf.py"; CIBLE="Sanity — lexvox-victime.com" ;;
  medical)  QA="tools/qa_article_wp.py";   CIBLE="WordPress — medical.lexvox-avocat.fr" ;;
  accident) QA="tools/qa_article_wp.py";   CIBLE="WordPress — victime-accident.lexvox-avocat.fr" ;;
esac

# ------------------------------------------------------------------ secrets
# Controles avant tout travail : une routine qui echoue sur le jeton apres la
# QA fait perdre le benefice de la QA.
check_secrets() {
  [ "$PUBLISH" -eq 1 ] || return 0
  if [ "$SITE" = victime ]; then
    [ -n "${SANITY_API_TOKEN:-}" ] || die "SANITY_API_TOKEN absent de l'environnement." 3
  else
    local u p
    u="WP_$(printf '%s' "$SITE" | tr '[:lower:]' '[:upper:]')_USER"
    p="WP_$(printf '%s' "$SITE" | tr '[:lower:]' '[:upper:]')_APP_PASSWORD"
    [ -n "${!u:-}" ] && [ -n "${!p:-}" ] || die "secrets WordPress absents : $u / $p" 3
  fi
}

# --------------------------------------------------------------- candidats
candidates_json() { $STATE candidates "$SITE"; }

# Champs du candidat d'indice $1, rendus comme affectations shell a evaluer.
# Un seul interpreteur par candidat : la file WordPress compte 150 items.
candidate_vars() {
  python3 -c '
import json, shlex, sys
a = json.loads(sys.argv[1])[int(sys.argv[2])]
for var, cle in (("ID", "id"), ("SLUG", "slug"), ("PATH_HTML", "path"),
                 ("TYPE", "type"), ("EXISTS", "exists")):
    print("%s=%s" % (var, shlex.quote(str(a.get(cle, "")))))' "$CANDIDATES" "$1"
}

CANDIDATES="$(candidates_json)"
TOTAL="$(python3 -c 'import json,sys;print(len(json.loads(sys.argv[1])))' "$CANDIDATES")"

if [ "$LIST_ONLY" -eq 1 ]; then
  log "Candidats 'todo' — site $SITE ($TOTAL en file)"
  python3 -c '
import json, sys
for a in json.loads(sys.argv[1]):
    if not a["exists"]:
        etat = "atelier absent"
    elif a["nw_score"] is None:
        etat = "NW non mesure"
    else:
        etat = "NW " + str(a["nw_score"])
    print("  id %3d  %-52s %s" % (a["id"], a["slug"], etat))' "$CANDIDATES"
  exit 0
fi

[ "$TOTAL" -gt 0 ] || die "aucun item 'todo' dans la file du site $SITE" 2

if [ -n "$FORCE_SLUG" ]; then
  python3 -c '
import json, sys
slugs = [a["slug"] for a in json.loads(sys.argv[1])]
sys.exit(0 if sys.argv[2] in slugs else 1)' "$CANDIDATES" "$FORCE_SLUG" \
    || die "slug absent des items 'todo' du site $SITE : $FORCE_SLUG" 2
  COUNT=1
fi

check_secrets

log "Routine de publication — site $SITE"
log "  cible      : $CIBLE"
log "  mode       : $([ "$PUBLISH" -eq 1 ] && echo 'PUBLICATION REELLE' || echo 'dry-run (aucune ecriture distante)')"
log "  a traiter  : $COUNT article(s) sur $TOTAL candidat(s)"

# Preflight global du depot (marqueurs de conflit, JSON-LD, metas, secrets).
if [ "$SITE" = victime ]; then
  step preflight "controle global du depot"
  python3 tools/preflight.py || die "preflight en echec — rien n'est publie."
fi

# ------------------------------------------------------------------- boucle
PUBLISHED=0
SKIPPED_QA=""
MISSING=0
MISSING_FIRST=""
i=0
while [ "$PUBLISHED" -lt "$COUNT" ] && [ "$i" -lt "$TOTAL" ]; do
  eval "$(candidate_vars "$i")"
  i=$((i + 1))

  if [ -n "$FORCE_SLUG" ] && [ "$SLUG" != "$FORCE_SLUG" ]; then
    continue
  fi

  # Un item sans article atelier n'est pas une anomalie : il reste a rediger.
  # On ne detaille que les premiers, le bilan donne le compte exact.
  if [ "$EXISTS" != "True" ]; then
    MISSING=$((MISSING + 1))
    if [ "$MISSING" -le 3 ]; then
      log "id $ID ($SLUG) : atelier absent, article a rediger."
      MISSING_FIRST="$MISSING_FIRST  id $ID ($SLUG)"$'\n'
    fi
    continue
  fi

  step "id $ID" "$SLUG"

  PILIER=""
  case "$TYPE" in *pilier*) PILIER="--pilier" ;; esac

  if ! python3 "$QA" "$PATH_HTML" $PILIER; then
    log "  QA en echec — article NON publie, statut inchange. Article suivant."
    SKIPPED_QA="$SKIPPED_QA  id $ID ($SLUG)"$'\n'
    continue
  fi

  if [ "$PUBLISH" -eq 0 ]; then
    if [ "$SITE" = victime ]; then
      python3 tools/sanity_publish.py "$PATH_HTML" --dry-run --publish-at "$AT"
    else
      log "  dry-run WordPress : l'appel de controle exige les secrets du site ;"
      log "  relancer avec --publish une fois WP_*_USER et WP_*_APP_PASSWORD poses."
    fi
    log "  DRY-RUN : article pret. Relancer avec --publish pour mettre en ligne."
    PUBLISHED=$((PUBLISHED + 1))
    continue
  fi

  OUT="$(mktemp)"
  if [ "$SITE" = victime ]; then
    python3 tools/sanity_publish.py "$PATH_HTML" --publish-at "$AT" | tee "$OUT"
    URL="$(sed -n 's/^PUBLIÉ : \([^ ]*\).*/\1/p' "$OUT" | tail -1)"
    [ -n "$URL" ] || die "publication Sanity sans URL en sortie — file et tracker non modifies."
    $STATE mark-done "$SITE" --id "$ID" --url "$URL" \
      --published-at "$(date -u +%Y-%m-%d\ %H:%MZ)"
  else
    python3 tools/wp_publish.py "$PATH_HTML" | tee "$OUT"
    URL="$(sed -n 's/^\[post\] #[0-9]* publie : \(.*\)$/\1/p' "$OUT" | tail -1)"
    POST_ID="$(sed -n 's/^\[post\] #\([0-9]*\) publie : .*/\1/p' "$OUT" | tail -1)"
    MEDIA_ID="$(sed -n 's/^\[media\] #\([0-9]*\).*/\1/p' "$OUT" | tail -1)"
    [ -n "$URL" ] || die "publication WordPress sans URL en sortie — file et tracker non modifies."
    $STATE mark-done "$SITE" --id "$ID" --url "$URL" \
      ${POST_ID:+--post-id "$POST_ID"} ${MEDIA_ID:+--media-id "$MEDIA_ID"}
  fi
  rm -f "$OUT"; OUT=""
  log "  EN LIGNE : $URL"
  PUBLISHED=$((PUBLISHED + 1))
done

# --------------------------------------------------------------- restitution
step bilan "$PUBLISHED article(s) traite(s) sur $COUNT demande(s)"
if [ -n "$SKIPPED_QA" ]; then
  log "Ecartes par la QA (statut 'todo' inchange, rien n'a ete publie pour eux) :"
  printf '%s' "$SKIPPED_QA"
  log "  Les remonter au seuil avec le skill /nw-optimisation, puis relancer."
fi
if [ "$MISSING" -gt 0 ]; then
  log "Items sans article atelier : $MISSING. Premiers de la file :"
  printf '%s' "$MISSING_FIRST"
  if [ "$SITE" = victime ]; then
    log "  Les rediger avec le skill /article-aivf."
  else
    log "  Les rediger selon PROMPT-PIPELINE-WP.md."
  fi
fi

if [ "$PUBLISHED" -eq 0 ]; then
  die "aucun article publiable dans la file du site $SITE." 2
fi

if [ "$PUBLISH" -eq 1 ] && [ "$COMMIT" -eq 1 ]; then
  step git "archivage de la file et du tracker"
  for f in queue-aivf.json queue-wp.json PUBLICATION-TRACKER.md PUBLICATION-TRACKER-WP.md; do
    [ -f "$f" ] && git add "$f" || true
  done
  # Regle 1 du depot : jamais de marqueur de conflit committe.
  git diff --cached --check || die "marqueurs de conflit dans l'index — commit interrompu."
  if git diff --cached --quiet; then
    log "  rien a committer."
  else
    git commit -m "Routine $SITE : $PUBLISHED article(s) publie(s) le $(date -u +%Y-%m-%d)"
    if [ "$PUSH" -eq 1 ]; then
      git pull --rebase origin main
      git push -u origin HEAD
    else
      log "  commit local pose. Pousser avec : git pull --rebase origin main && git push"
    fi
  fi
elif [ "$PUBLISH" -eq 1 ]; then
  log "File et tracker mis a jour dans l'arbre de travail. Relancer avec --commit pour les archiver."
fi

# Moins d'articles publies que demande : la routine a fait son travail, mais la
# file manque d'articles au standard. Code distinct pour qu'une tache planifiee
# le signale sans confondre avec un echec.
[ "$PUBLISHED" -lt "$COUNT" ] && exit 4
exit 0
