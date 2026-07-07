#!/usr/bin/env python3
"""Publication d'un article atelier vers WordPress — PIPELINE LEXVOX-WP.

Sites cibles (config dans queue-wp.json _meta.sites) :
  - medical  -> https://medical.lexvox-avocat.fr
  - accident -> https://victime-accident.lexvox-avocat.fr

Entree : wp-atelier/<site>/<slug>.html contenant un front-matter JSON en
commentaire HTML <!-- WP-META {...} --> avec :
  site, title, metaTitle, metaDescription, slug, categories[] (noms ou ids),
  ville, image (chemin relatif au depot ou au fichier), imageAlt.

Actions :
  1. Injection EXIF GPS (coordonnees de la ville, queue-wp.json
     _meta.seo_local.coordonnees) dans une COPIE de l'image, nommee
     <slug>-<ville>.jpg (piexif ; l'original n'est jamais modifie).
  2. POST /wp-json/wp/v2/media (Basic Auth, secrets env WP_<SITE>_USER /
     WP_<SITE>_APP_PASSWORD) puis pose de alt_text/title sur le media.
  3. POST /wp-json/wp/v2/posts {title, slug, status, content, excerpt,
     categories, featured_media, meta Yoast si inscriptible}.
  4. --dry-run : tout SAUF les POST (verifie auth en GET, collision de slug,
     categories, EXIF, et imprime le payload resume).

Usage :
  python3 tools/wp_publish.py wp-atelier/<site>/<slug>.html --dry-run
  python3 tools/wp_publish.py wp-atelier/<site>/<slug>.html            # publie

Aucun secret en argument ni en dur (regle 5 CLAUDE.md) : tout vient de l'env.
"""
import base64
import json
import mimetypes
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
QUEUE = REPO / "queue-wp.json"
META_RE = re.compile(r"<!--\s*WP-META\s*(\{.*?\})\s*-->", re.S)
ENV_VARS = {
    "medical": ("WP_MEDICAL_USER", "WP_MEDICAL_APP_PASSWORD"),
    "accident": ("WP_ACCIDENT_USER", "WP_ACCIDENT_APP_PASSWORD"),
}


def die(msg: str) -> None:
    sys.exit(f"ERREUR wp_publish : {msg}")


def load_queue_meta() -> dict:
    if not QUEUE.exists():
        die(f"{QUEUE} introuvable")
    return json.loads(QUEUE.read_text(encoding="utf-8"))["_meta"]


def auth_header(site: str) -> str:
    uvar, pvar = ENV_VARS[site]
    user, pwd = os.environ.get(uvar, ""), os.environ.get(pvar, "")
    if not user or not pwd:
        die(f"secrets env manquants : {uvar} / {pvar}")
    tok = base64.b64encode(f"{user}:{pwd}".encode()).decode()
    return f"Basic {tok}"


def request(method: str, url: str, site: str, data: bytes | None = None,
            content_type: str | None = None, extra: dict | None = None) -> tuple[int, dict | list]:
    headers = {"Authorization": auth_header(site), "User-Agent": "lexvox-wp-pipeline/1.0"}
    if content_type:
        headers["Content-Type"] = content_type
    if extra:
        headers.update(extra)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return e.code, {"_error": body}


def deg_to_dms_rational(deg: float):
    d = int(deg)
    m_f = (deg - d) * 60
    m = int(m_f)
    s = round((m_f - m) * 60 * 10000)
    return ((d, 1), (m, 1), (s, 10000))


def inject_gps(src: Path, dest: Path, lat: float, lon: float) -> None:
    import piexif  # dependance : pip install piexif

    shutil.copyfile(src, dest)
    try:
        exif = piexif.load(str(dest))
    except Exception:
        exif = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    exif["GPS"] = {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: deg_to_dms_rational(abs(lat)),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: deg_to_dms_rational(abs(lon)),
    }
    piexif.insert(piexif.dump(exif), str(dest))


def resolve_categories(names_or_ids: list, site_cfg: dict) -> list[int]:
    existing = {k.lower(): v for k, v in site_cfg["categories_existantes"].items()}
    out = []
    for c in names_or_ids:
        if isinstance(c, int):
            out.append(c)
        elif str(c).isdigit():
            out.append(int(c))
        elif str(c).lower() in existing:
            out.append(existing[str(c).lower()])
        else:
            die(f"categorie inconnue pour ce site : {c!r} (jamais de creation de categorie — "
                f"disponibles : {sorted(site_cfg['categories_existantes'])})")
    return sorted(set(out))


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    files = [a for a in argv if not a.startswith("--")]
    if len(files) != 1:
        print(__doc__)
        return 1
    path = Path(files[0])
    if not path.exists():
        die(f"{path} introuvable")

    html = path.read_text(encoding="utf-8")
    m = META_RE.search(html)
    if not m:
        die("front-matter <!-- WP-META {...} --> absent")
    meta = json.loads(m.group(1))
    site = meta.get("site")
    if site not in ENV_VARS:
        die(f"WP-META.site invalide : {site!r}")

    qmeta = load_queue_meta()
    site_cfg = qmeta["sites"][site]
    api = site_cfg["api"]
    slug = meta["slug"]
    ville = meta["ville"]
    coords = qmeta["seo_local"]["coordonnees"].get(ville)
    if not coords:
        die(f"coordonnees GPS inconnues pour la ville {ville!r} (queue-wp.json _meta.seo_local)")

    # ---- 0. auth + collision de slug (aussi en dry-run)
    code, me = request("GET", f"{api}/users/me?context=edit", site)
    if code != 200:
        die(f"auth WordPress {site} : HTTP {code} {me}")
    print(f"[auth] {site} OK — user #{me['id']} ({', '.join(me.get('roles', []))})")

    code, dup = request("GET", f"{api}/posts?slug={urllib.parse.quote(slug)}&status=publish,draft,future,pending", site)
    if code == 200 and dup:
        die(f"slug deja pris sur {site} : {slug} (post #{dup[0]['id']}) — anti-cannibalisation")
    print(f"[slug] {slug} libre sur {site}")

    cats = resolve_categories(meta.get("categories", []), site_cfg)
    print(f"[categories] {meta.get('categories')} -> ids {cats}")

    # ---- 1. EXIF GPS sur une copie de l'image
    img_src = (path.parent / meta["image"]) if (path.parent / meta["image"]).exists() else REPO / meta["image"]
    if not img_src.exists():
        die(f"image introuvable : {meta['image']}")
    lat, lon = coords
    tmpdir = Path(tempfile.mkdtemp(prefix="wp-publish-"))
    img_up = tmpdir / f"{slug}-{ville}.jpg"
    inject_gps(img_src, img_up, lat, lon)
    import piexif
    gps_check = piexif.load(str(img_up))["GPS"]
    if not gps_check.get(piexif.GPSIFD.GPSLatitude):
        die("injection EXIF GPS echouee")
    print(f"[exif] GPS {lat},{lon} ({ville}) injecte -> {img_up.name} "
          f"({img_up.stat().st_size // 1024} Ko)")

    # ---- corps du post : tout le fichier sauf le front-matter WP-META
    content = META_RE.sub("", html, count=1).strip()
    excerpt = meta.get("metaDescription", "").strip()

    post_payload = {
        "title": meta["title"],
        "slug": slug,
        "status": meta.get("status", "publish"),
        "content": content,
        "excerpt": excerpt,
        "categories": cats,
    }
    yoast_meta = {}
    if meta.get("metaTitle"):
        yoast_meta["_yoast_wpseo_title"] = meta["metaTitle"]
    if meta.get("metaDescription"):
        yoast_meta["_yoast_wpseo_metadesc"] = meta["metaDescription"]
    if yoast_meta:
        post_payload["meta"] = yoast_meta

    if dry:
        print("\n[dry-run] AUCUN POST envoye. Payload post :")
        resume = {k: (v[:120] + "…" if isinstance(v, str) and len(v) > 120 else v)
                  for k, v in post_payload.items() if k != "content"}
        resume["content"] = f"<{len(content)} caracteres HTML>"
        print(json.dumps(resume, ensure_ascii=False, indent=2))
        print(f"[dry-run] media a uploader : {img_up.name} avec alt={meta.get('imageAlt')!r}")
        return 0

    # ---- 2. upload media
    ctype = mimetypes.guess_type(str(img_up))[0] or "image/jpeg"
    code, media = request(
        "POST", f"{api}/media", site, data=img_up.read_bytes(), content_type=ctype,
        extra={"Content-Disposition": f'attachment; filename="{img_up.name}"'},
    )
    if code not in (200, 201):
        die(f"upload media : HTTP {code} {media}")
    media_id = media["id"]
    print(f"[media] #{media_id} uploade : {media.get('source_url')}")
    alt_payload = json.dumps({
        "alt_text": meta.get("imageAlt", ""),
        "title": meta.get("title", slug),
    }).encode()
    code, _ = request("POST", f"{api}/media/{media_id}", site, data=alt_payload,
                      content_type="application/json")
    print(f"[media] alt_text pose (HTTP {code})")

    # ---- 3. creation du post
    post_payload["featured_media"] = media_id
    code, post = request("POST", f"{api}/posts", site,
                         data=json.dumps(post_payload).encode(), content_type="application/json")
    if code not in (200, 201):
        die(f"creation post : HTTP {code} {post}")
    link = post.get("link")
    print(f"[post] #{post['id']} publie : {link}")

    # verification metas Yoast persistees
    got = {k: v for k, v in (post.get("meta") or {}).items() if k.startswith("_yoast")}
    if yoast_meta and not any(got.get(k) for k in yoast_meta):
        print("[yoast] ATTENTION : metas Yoast non persistees via REST — "
              "a poser manuellement (logguer dans PUBLICATION-TRACKER-WP.md)")

    # ---- 4. verification HTTP 200 en front
    try:
        with urllib.request.urlopen(link, timeout=60) as r:
            print(f"[verif] GET {link} -> HTTP {r.status}")
    except Exception as e:  # pragma: no cover
        print(f"[verif] GET {link} a echoue : {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
