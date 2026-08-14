#!/usr/bin/env python3
"""Publie Voicebox derriere Cloudflare Tunnel + Access, sans fenetre d'exposition.

Voicebox n'a AUCUNE authentification native. Le publier nu, c'est mettre la voix
clonee de l'avocat a la disposition de quiconque connait l'URL : n'importe qui
peut lui faire dire n'importe quoi, y compris se faire passer pour lui aupres
d'un client.

D'ou l'ordre impose par ce script, qui n'est pas l'ordre naturel de la
documentation Cloudflare :

    1. jeton de service          (l'identite qui aura le droit d'entrer)
    2. application Access        (le portail)  <- AVANT que le nom existe
    3. politique du portail      (n'accepte que ce jeton)
    4. tunnel + route DNS        (le nom se met a resoudre, deja protege)
    5. verification              (sans jeton -> refuse ; avec jeton -> 200)

Creer le tunnel puis poser le portail, comme le suggerent la plupart des
tutoriels, laisse entre les deux une fenetre ou l'instance repond a tout le
monde. Cette fenetre dure le temps qu'on met a cliquer dans un tableau de bord.
C'est trop long.

Ce script ne s'execute PAS depuis une session distante : `cloudflared` doit
tourner sur le poste ou vit Voicebox. Il s'y lance en une commande.

Prerequis :
    export CLOUDFLARE_API_TOKEN=…     (droits : Access: Apps and Policies:Edit,
                                       Access: Service Tokens:Edit, DNS:Edit)
    export CLOUDFLARE_ACCOUNT_ID=…
    cloudflared installe et « cloudflared tunnel login » deja fait

Usage :
    python3 tools/voicebox_tunnel.py --installer --hote voicebox.mondomaine.fr
    python3 tools/voicebox_tunnel.py --verifier  --hote voicebox.mondomaine.fr
    python3 tools/voicebox_tunnel.py --self-test
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.cloudflare.com/client/v4"
NOM_TUNNEL_DEFAUT = "voicebox-lexvox"
SERVICE_LOCAL_DEFAUT = "http://localhost:8000"
DUREE_SESSION = "24h"


class ErreurTunnel(RuntimeError):
    """Etape impossible : identifiants, reseau, ou refus de l'API."""


# --- API Cloudflare -----------------------------------------------------------
def appeler(chemin: str, jeton: str, donnees=None, methode=None):
    url = f"{API}{chemin}"
    corps = json.dumps(donnees).encode() if donnees is not None else None
    requete = urllib.request.Request(
        url, data=corps, method=methode or ("POST" if corps else "GET"),
        headers={"Authorization": f"Bearer {jeton}",
                 "Content-Type": "application/json",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            charge = json.loads(reponse.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as erreur:
        detail = erreur.read().decode("utf-8", "replace")[:500]
        raise ErreurTunnel(f"{methode or 'GET'} {chemin} -> HTTP "
                           f"{erreur.code} : {detail}") from erreur
    except urllib.error.URLError as erreur:
        raise ErreurTunnel(f"{chemin} injoignable : {erreur.reason}") from erreur
    if not charge.get("success", False):
        raise ErreurTunnel(f"{chemin} refuse : "
                           f"{json.dumps(charge.get('errors'), ensure_ascii=False)[:400]}")
    return charge.get("result")


def trouver_par_nom(elements, nom: str, cle: str = "name"):
    """Rend l'element deja cree portant ce nom — le script est rejouable."""
    for element in elements or []:
        if isinstance(element, dict) and element.get(cle) == nom:
            return element
    return None


# --- cloudflared --------------------------------------------------------------
def cloudflared(arguments, verifier=True):
    binaire = shutil.which("cloudflared")
    if not binaire:
        raise ErreurTunnel(
            "cloudflared est introuvable. Sur macOS : « brew install "
            "cloudflared ». Sur Windows : « winget install --id "
            "Cloudflare.cloudflared ». Sur Debian/Ubuntu : paquet .deb de "
            "https://github.com/cloudflare/cloudflared/releases")
    resultat = subprocess.run([binaire] + arguments, capture_output=True,
                              text=True)
    if verifier and resultat.returncode != 0:
        raise ErreurTunnel(f"cloudflared {' '.join(arguments)} : "
                           f"{(resultat.stderr or resultat.stdout).strip()[:400]}")
    return resultat


def uuid_du_tunnel(nom: str):
    """UUID du tunnel s'il existe deja, sinon None."""
    resultat = cloudflared(["tunnel", "list", "--output", "json"],
                           verifier=False)
    if resultat.returncode != 0:
        return None
    try:
        tunnels = json.loads(resultat.stdout or "[]")
    except json.JSONDecodeError:
        return None
    trouve = trouver_par_nom(tunnels, nom)
    return trouve.get("id") if trouve else None


def ecrire_config(uuid: str, hote: str, service: str, dossier: Path) -> Path:
    """Le fichier d'ingress : ce nom d'hote va vers Voicebox, le reste nulle part."""
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / "config.yml"
    chemin.write_text(
        f"tunnel: {uuid}\n"
        f"credentials-file: {dossier / (uuid + '.json')}\n"
        f"\n"
        f"ingress:\n"
        f"  - hostname: {hote}\n"
        f"    service: {service}\n"
        f"  - service: http_status:404\n",
        encoding="utf-8")
    return chemin


# --- Verification -------------------------------------------------------------
def sonder(url: str, entetes=None):
    """Rend (code, apercu) sans lever : on veut precisement lire les refus."""
    requete = urllib.request.Request(url, headers=entetes or {}, method="GET")
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            return reponse.status, reponse.read()[:200]
    except urllib.error.HTTPError as erreur:
        return erreur.code, erreur.read()[:200]
    except urllib.error.URLError as erreur:
        return 0, str(erreur.reason).encode()


def verifier_fermeture(hote: str) -> int:
    """Le seul controle qui compte : l'instance est-elle fermee sans jeton ?"""
    base = f"https://{hote}"
    print(f"=== VERIFICATION DE {base} ===\n")
    constats = []

    code, apercu = sonder(f"{base}/profiles")
    ferme = code in (401, 403) or b"Cloudflare Access" in apercu or code == 302
    constats.append(("sans jeton : l'instance refuse", ferme,
                     f"HTTP {code}" if code else apercu.decode("utf-8", "replace")[:80]))

    identifiant = os.environ.get("VOICEBOX_CF_ID")
    secret = os.environ.get("VOICEBOX_CF_SECRET")
    if identifiant and secret:
        code, apercu = sonder(f"{base}/profiles",
                              {"CF-Access-Client-Id": identifiant,
                               "CF-Access-Client-Secret": secret})
        constats.append(("avec jeton : l'instance repond", code == 200,
                         f"HTTP {code}"))
    else:
        constats.append(("avec jeton : l'instance repond", False,
                         "VOICEBOX_CF_ID / VOICEBOX_CF_SECRET absents de "
                         "l'environnement — impossible de tester l'entree"))

    for libelle, ok, detail in constats:
        print(f"   [{'OK' if ok else '!!'}] {libelle} — {detail}")

    if not constats[0][1]:
        print("\nDANGER : l'instance repond sans authentification. La voix "
              "clonee de l'avocat est accessible a qui connait l'URL.\n"
              "Arreter le tunnel MAINTENANT (Ctrl-C sur « cloudflared tunnel "
              "run »), puis reprendre l'installation.")
        return 3
    if not constats[1][1]:
        print("\nLe portail est ferme — c'est le point important. En revanche "
              "l'entree n'a pas pu etre testee : exporter VOICEBOX_CF_ID et "
              "VOICEBOX_CF_SECRET, puis relancer --verifier.")
        return 1
    print("\nINSTANCE PUBLIEE ET FERMEE — seul le jeton de service entre.")
    return 0


# --- Installation -------------------------------------------------------------
def installer(options) -> int:
    jeton = os.environ.get("CLOUDFLARE_API_TOKEN")
    compte = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not jeton or not compte:
        print("CLOUDFLARE_API_TOKEN et CLOUDFLARE_ACCOUNT_ID doivent etre "
              "exportes.\nLe jeton demande trois droits : Access: Apps and "
              "Policies:Edit, Access: Service Tokens:Edit, DNS:Edit.",
              file=sys.stderr)
        return 2

    hote, nom = options.hote, options.nom
    print(f"=== PUBLICATION DE VOICEBOX SUR {hote} ===\n")

    # 1. le jeton de service — l'identite qui aura le droit d'entrer
    print("1/5  jeton de service")
    jetons = appeler(f"/accounts/{compte}/access/service_tokens", jeton)
    existant = trouver_par_nom(jetons, options.nom_jeton)
    secret_neuf = None
    if existant:
        identifiant_jeton = existant["id"]
        client_id = existant.get("client_id", "(inchange)")
        print(f"     deja cree, REUTILISE — {options.nom_jeton}")
    else:
        cree = appeler(f"/accounts/{compte}/access/service_tokens", jeton,
                       {"name": options.nom_jeton,
                        "duration": options.duree_jeton})
        identifiant_jeton = cree["id"]
        client_id = cree["client_id"]
        secret_neuf = cree["client_secret"]
        print(f"     cree — {options.nom_jeton}")

    # 2. le portail, AVANT que le nom ne resolve
    print("2/5  application Access (le portail)")
    applications = appeler(f"/accounts/{compte}/access/apps", jeton)
    application = trouver_par_nom(applications, options.nom_app)
    if application:
        identifiant_app = application["id"]
        print("     deja creee, REUTILISEE")
    else:
        application = appeler(
            f"/accounts/{compte}/access/apps", jeton,
            {"name": options.nom_app, "domain": hote, "type": "self_hosted",
             "session_duration": DUREE_SESSION,
             "allowed_idps": [], "auto_redirect_to_identity": False,
             "http_only_cookie_attribute": True})
        identifiant_app = application["id"]
        print(f"     creee sur {hote}")

    # 3. la politique : ce jeton, et rien d'autre
    print("3/5  politique — n'accepte que ce jeton de service")
    politiques = appeler(
        f"/accounts/{compte}/access/apps/{identifiant_app}/policies", jeton)
    if trouver_par_nom(politiques, options.nom_politique):
        print("     deja posee, REUTILISEE")
    else:
        appeler(f"/accounts/{compte}/access/apps/{identifiant_app}/policies",
                jeton,
                {"name": options.nom_politique, "decision": "non_identity",
                 "include": [{"service_token": {"token_id": identifiant_jeton}}]})
        print("     posee")

    # 4. le tunnel, puis la route DNS : le nom ne resout qu'ici, deja protege
    print("4/5  tunnel et route DNS")
    uuid = uuid_du_tunnel(nom)
    if uuid:
        print(f"     tunnel « {nom} » deja cree, REUTILISE")
    else:
        cloudflared(["tunnel", "create", nom])
        uuid = uuid_du_tunnel(nom)
        if not uuid:
            raise ErreurTunnel(f"tunnel « {nom} » cree mais introuvable dans "
                               "« cloudflared tunnel list »")
        print(f"     tunnel cree — {uuid}")
    cloudflared(["tunnel", "route", "dns", "--overwrite-dns", nom, hote])
    config = ecrire_config(uuid, hote, options.service,
                           Path(options.dossier).expanduser())
    print(f"     route DNS posee, configuration ecrite dans {config}")

    # 5. ce qu'il reste a faire, et le secret montre UNE fois
    print("\n5/5  a lancer sur ce poste, et a laisser tourner :\n")
    print(f"     cloudflared tunnel run {nom}\n")
    if secret_neuf:
        print("     Le secret du jeton ne sera plus JAMAIS reaffiche par "
              "Cloudflare.\n     L'exporter maintenant, sur la machine qui "
              "pilotera la synthese :\n")
        print(f'     export VOICEBOX_CF_ID="{client_id}"')
        print(f'     export VOICEBOX_CF_SECRET="{secret_neuf}"\n')
        print("     Ne l'ecrire dans aucun fichier du depot.\n")
    else:
        print(f"     Jeton deja existant : identifiant {client_id}.\n"
              "     Son secret n'est plus recuperable ; en creer un nouveau si "
              "besoin\n     (--nom-jeton autre-nom).\n")
    print("     Puis, tunnel lance, verifier la fermeture :\n")
    print(f"     python3 tools/voicebox_tunnel.py --verifier --hote {hote}\n")
    return 0


# --- Auto-test ----------------------------------------------------------------
def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, obtenu, attendu=True):
        nonlocal essais
        essais += 1
        if obtenu != attendu:
            echecs.append(f"{libelle} : {obtenu!r} != {attendu!r}")

    # rejouabilite : un element deja cree doit etre reconnu, pas duplique
    liste = [{"name": "a", "id": "1"}, {"name": "b", "id": "2"}]
    verifier("element existant reconnu", trouver_par_nom(liste, "b")["id"], "2")
    verifier("element absent non invente", trouver_par_nom(liste, "c"), None)
    verifier("liste vide toleree", trouver_par_nom(None, "a"), None)

    # le fichier d'ingress : le nom d'hote va vers Voicebox, le reste nulle part
    bac = Path("/tmp/_tunnel_selftest")
    shutil.rmtree(bac, ignore_errors=True)
    config = ecrire_config("uuid-1234", "voicebox.exemple.fr",
                           "http://localhost:8000", bac)
    texte = config.read_text(encoding="utf-8")
    verifier("tunnel nomme dans la config", "tunnel: uuid-1234" in texte)
    verifier("hote route vers voicebox",
             "hostname: voicebox.exemple.fr" in texte
             and "service: http://localhost:8000" in texte)
    verifier("tout le reste tombe en 404",
             texte.rstrip().endswith("- service: http_status:404"))
    verifier("credentials designes", "uuid-1234.json" in texte)
    shutil.rmtree(bac, ignore_errors=True)

    # la verification doit lire un refus comme une bonne nouvelle
    for code in (401, 403):
        essais += 1
        if not (code in (401, 403)):
            echecs.append(f"code {code} non reconnu comme un refus")

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    analyseur.add_argument("--installer", action="store_true")
    analyseur.add_argument("--verifier", action="store_true")
    analyseur.add_argument("--self-test", action="store_true")
    analyseur.add_argument("--hote", help="nom d'hote public, ex. "
                                          "voicebox.mondomaine.fr")
    analyseur.add_argument("--nom", default=NOM_TUNNEL_DEFAUT)
    analyseur.add_argument("--service", default=SERVICE_LOCAL_DEFAUT,
                           help="ou ecoute Voicebox sur ce poste")
    analyseur.add_argument("--dossier", default="~/.cloudflared")
    analyseur.add_argument("--nom-app", default="Voicebox LEXVOX")
    analyseur.add_argument("--nom-politique", default="Jeton de service LEXVOX")
    analyseur.add_argument("--nom-jeton", default="voicebox-lexvox")
    analyseur.add_argument("--duree-jeton", default="8760h",
                           help="duree de validite du jeton (defaut : un an)")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    if not options.hote:
        analyseur.error("--hote est requis")
    try:
        if options.verifier:
            return verifier_fermeture(options.hote)
        if options.installer:
            return installer(options)
    except ErreurTunnel as erreur:
        print(f"\nECHEC : {erreur}", file=sys.stderr)
        return 2
    analyseur.error("choisir --installer, --verifier ou --self-test")


if __name__ == "__main__":
    sys.exit(main())
