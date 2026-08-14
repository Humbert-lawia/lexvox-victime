#!/usr/bin/env python3
"""Synthese vocale LOCALE via Voicebox — remplace ElevenLabs.

Voicebox (voicebox.sh) est une application libre qui tourne sur le poste du
cabinet et expose une API REST locale. Trois consequences qui comptent ici :
aucun texte ne sort de la machine, aucun abonnement, aucun quota de
caracteres. Pour un cabinet d'avocats, le premier point n'est pas un detail.

Contrat utilise (docs.voicebox.sh) :
    POST /generate   {profile_id, text, language, seed, engine, model_size,
                      max_chunk_chars, instruct} -> {id, audio_path, duration}
    GET  /audio/{id} -> le fichier audio
    GET  /profiles   -> les profils de voix, dont la voix clonee de l'avocat
    GET  /openapi.json -> le schema REEL de l'instance installee

⚠️ Piege documente : la page publique de /generate annonce
« language: ^(en|zh)$ » alors que l'application revendique 23 langues et
embarque des moteurs multilingues (Chatterbox Multilingual, LuxTTS). La
verite est dans le /openapi.json de VOTRE instance, pas dans la doc du site.
`--diagnostic` la lit et refuse d'aller plus loin si le francais n'est pas
accepte : mieux vaut le savoir avant d'avoir monte 72 episodes.

Deux moteurs, une seule interface — meme principe que ffmpeg_moteur.py :

    MoteurVoicebox : parle a l'API locale, rend un fichier audio.
    MoteurManuel   : n'appelle rien, ecrit le .txt a coller dans l'interface
                     graphique. C'est le repli si l'API n'est pas joignable,
                     et le mode par defaut tant que les profils ne sont pas
                     renseignes.

Usage :
    python3 tools/voix_moteur.py --diagnostic
    python3 tools/voix_moteur.py --self-test
"""

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_DEFAUT = "podcasts/voicebox.json"

# Moteurs livres avec Voicebox (docs.voicebox.sh/developer/tts-generation).
# Seuls les multilingues nous interessent : le corpus est en francais.
MOTEURS_TTS = ("qwen", "qwen_custom_voice", "luxtts", "chatterbox",
               "chatterbox_turbo", "tada", "kokoro")
MOTEURS_MULTILINGUES = ("chatterbox", "luxtts", "qwen_custom_voice", "qwen")

# /generate refuse un texte de plus de 5000 caracteres. Nos segments font
# quelques centaines de caracteres : la marge est confortable, mais un
# gabarit modifie sans precaution pourrait la franchir.
TEXTE_MAX = 5000

# Au-dela de max_chunk_chars, Voicebox decoupe le texte et RACCORDE les
# morceaux par un fondu. Sur une signature sonore, ce raccord s'entend. Nos
# segments etant courts, on releve simplement le seuil pour qu'aucun segment
# ne soit jamais coupe.
CHUNK_DEFAUT = 1200


class ErreurVoix(RuntimeError):
    """Panne de synthese : configuration, reseau ou refus de l'API."""


def _http(url: str, donnees=None, timeout=600, brut=False, entetes_sup=None):
    """Appel HTTP minimal (bibliotheque standard, aucune dependance).

    `brut=True` recupere un corps binaire. L'en-tete Accept suit ce que l'on
    demande vraiment : reclamer « application/json » pour telecharger un MP3
    fait repondre 406 a tout serveur qui applique la negociation de contenu —
    et le refus tombe APRES la generation, donc apres le temps de calcul.
    """
    corps = None
    entetes = {"Accept": "audio/*, application/octet-stream, */*" if brut
               else "application/json"}
    if donnees is not None:
        corps = json.dumps(donnees).encode("utf-8")
        entetes["Content-Type"] = "application/json"
    entetes.update(entetes_sup or {})
    requete = urllib.request.Request(url, data=corps, headers=entetes,
                                     method="POST" if corps else "GET")
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as reponse:
            charge = reponse.read()
    except urllib.error.HTTPError as erreur:
        detail = erreur.read().decode("utf-8", "replace")[:400]
        raise ErreurVoix(f"{url} -> HTTP {erreur.code} : {detail}") from erreur
    except urllib.error.URLError as erreur:
        raise ErreurVoix(
            f"{url} injoignable ({erreur.reason}). Voicebox est-il lance sur "
            "ce poste, et le serveur demarre ?") from erreur
    if brut:
        return charge
    try:
        return json.loads(charge.decode("utf-8", "replace"))
    except json.JSONDecodeError as erreur:
        # Une page HTML a la place du JSON est presque toujours un portail
        # d'authentification qui repond 200 : le dire, plutot que « reponse non
        # JSON », qui laisse chercher du cote du serveur alors que le probleme
        # est dans les en-tetes.
        debut = charge.lstrip()[:15].lower()
        piste = (" — on dirait une page HTML, typiquement l'ecran de connexion "
                 "d'un portail d'authentification. Verifier les en-tetes "
                 "(variables d'environnement exportees ?)."
                 if debut.startswith(b"<") else "")
        raise ErreurVoix(f"{url} : reponse non JSON{piste} "
                         f"Recu : {apercu(charge)}") from erreur


def ressemble_a_de_l_audio(donnees: bytes) -> bool:
    """Vrai si les premiers octets sont ceux d'un format audio connu.

    Un code 200 ne prouve pas qu'on a recu du son. Derriere un portail
    d'authentification — exactement le montage propose pour exposer Voicebox —
    une requete mal authentifiee rend volontiers une page de connexion en HTML,
    avec un code 200. Sans ce controle, cette page finissait ecrite dans un
    fichier .mp3, et la panne n'apparaissait qu'au montage, plus loin.
    """
    if donnees[:3] == b"ID3":                       # MP3 etiquete
        return True
    if donnees[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xfa"):
        return True                                 # trame MPEG nue
    if donnees[:4] == b"RIFF" and donnees[8:12] == b"WAVE":
        return True
    if donnees[:4] == b"fLaC" or donnees[:4] == b"OggS":
        return True
    if donnees[4:8] == b"ftyp":                     # M4A / AAC
        return True
    return False


def apercu(donnees: bytes, taille: int = 80) -> str:
    """Debut lisible d'une reponse inattendue, pour un message d'erreur utile."""
    texte = donnees[:taille].decode("utf-8", "replace").strip()
    texte = " ".join(texte.split())
    return f"« {texte} … »" if texte else f"{len(donnees)} octets illisibles"


def resoudre_entetes(config: dict) -> dict:
    """Rend les en-tetes d'authentification, lus dans l'ENVIRONNEMENT.

    La configuration ne porte que des RENVOIS (« env:NOM_DE_VARIABLE »), jamais
    la valeur. Un jeton a deja du etre purge de l'historique de ce depot : on
    refuse donc explicitement une valeur ecrite en clair, meme si
    podcasts/voicebox.json est ignore par git — un fichier ignore se copie, se
    joint a un courriel et se retrouve dans une sauvegarde.
    """
    entetes = {}
    for nom, valeur in (config.get("auth_headers") or {}).items():
        if not isinstance(valeur, str):
            raise ErreurVoix(f"en-tete « {nom} » : valeur invalide")
        if not valeur.startswith("env:"):
            raise ErreurVoix(
                f"en-tete « {nom} » : ecrire « env:NOM_DE_VARIABLE », pas le "
                "secret lui-meme. Le jeton vit dans l'environnement, jamais "
                "dans un fichier.")
        variable = valeur[4:].strip()
        secret = os.environ.get(variable)
        if not secret:
            raise ErreurVoix(
                f"variable d'environnement « {variable} » vide ou absente "
                f"(en-tete « {nom} »). L'exporter avant de lancer la commande.")
        entetes[nom] = secret
    return entetes


def verifier_url(base: str):
    """Interdit d'envoyer la voix de l'avocat en clair sur un reseau.

    En local (127.0.0.1 / localhost) le texte ne quitte pas la machine et http
    suffit. Des que l'instance est ailleurs, le trafic porte le texte lu ET la
    voix clonee de l'avocat : il lui faut du chiffrement.
    """
    partie = urllib.parse.urlsplit(base)
    hote = (partie.hostname or "").lower()
    local = hote in ("localhost", "127.0.0.1", "::1", "0.0.0.0")
    if partie.scheme == "https" or local:
        return
    raise ErreurVoix(
        f"« {base} » : une instance distante doit etre en https. En http, le "
        "texte lu et la voix clonee de l'avocat circulent en clair.")


def charger_config(chemin: str) -> dict:
    fichier = Path(chemin)
    if not fichier.is_file():
        raise ErreurVoix(
            f"configuration absente : {fichier}. Copier "
            "podcasts/voicebox.exemple.json et y mettre les identifiants de "
            "profil rendus par « python3 tools/voix_moteur.py --diagnostic ».")
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erreur:
        raise ErreurVoix(f"{fichier} : JSON invalide — {erreur}") from erreur


class MoteurManuel:
    """Aucun appel : ecrit le texte a coller dans l'interface Voicebox."""

    nom = "manuel"
    automatique = False

    def __init__(self, config=None):
        self.config = config or {}

    def verifier(self):
        return True

    def synthetiser(self, texte: str, sortie: Path, chaine: str,
                    segment: str = "") -> dict:
        cible = sortie.with_suffix(".txt")
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(texte + "\n", encoding="utf-8")
        return {"mode": "manuel", "texte": str(cible), "audio": None,
                "consigne": f"coller {cible.name} dans Voicebox, voix clonee "
                            f"de la chaine {chaine}, puis enregistrer sous "
                            f"{sortie.name}"}


class MoteurVoicebox:
    """Synthese par l'API REST locale de Voicebox."""

    nom = "voicebox"
    automatique = True

    def __init__(self, config: dict):
        self.config = config
        self.base = str(config.get("base_url", "http://localhost:8000")).rstrip("/")
        verifier_url(self.base)
        self.entetes = resoudre_entetes(config)
        self.profils = config.get("profils", {}) or {}
        self.moteur = config.get("engine", "chatterbox")
        self.langue = config.get("language", "fr")
        self.taille = config.get("model_size")
        self.chunk = int(config.get("max_chunk_chars", CHUNK_DEFAUT))
        self.instruct = config.get("instruct") or ""
        self.graines = config.get("graines", {}) or {}
        self.delai = int(config.get("timeout_s", 600))
        self._contraintes = None

    def _appel(self, chemin, donnees=None, timeout=None, brut=False):
        return _http(f"{self.base}{chemin}", donnees=donnees,
                     timeout=timeout or self.delai, brut=brut,
                     entetes_sup=self.entetes)

    # -- contrat reel de l'instance --------------------------------------
    def contraintes(self) -> dict:
        """Lit UNE FOIS le /openapi.json de l'instance et en tire ses limites.

        Le diagnostic lisait deja ce schema, mais la synthese, elle, envoyait
        des valeurs en dur. Une instance qui plafonne `max_chunk_chars` plus bas
        que notre reglage rendait alors un 422 incomprehensible, apres coup.
        Autant demander a l'instance ce qu'elle accepte, plutot que le supposer.
        """
        if self._contraintes is None:
            try:
                schema = self._appel("/openapi.json", timeout=30)
            except ErreurVoix:
                schema = {}          # instance muette : on garde nos defauts
            self._contraintes = lire_contraintes(schema)
        return self._contraintes

    # -- verifications ---------------------------------------------------
    def verifier(self):
        if self.moteur not in MOTEURS_TTS:
            raise ErreurVoix(
                f"moteur « {self.moteur} » inconnu de Voicebox. Choisir parmi "
                f"{', '.join(MOTEURS_TTS)}.")
        if not self.profils:
            raise ErreurVoix(
                "aucun profil de voix configure. Lancer « --diagnostic » pour "
                "lister les profils de votre instance, puis renseigner leur "
                "identifiant par chaine dans la configuration.")
        self._appel("/profiles", timeout=30)
        return True

    def profil_de(self, chaine: str) -> str:
        profil = self.profils.get(chaine)
        if not profil:
            raise ErreurVoix(
                f"aucun profil de voix pour la chaine « {chaine} ». La voix "
                "qui parle doit etre celle de l'avocat qui signe les articles "
                "de cette chaine — ne pas prendre celle d'une autre.")
        return profil

    # -- synthese --------------------------------------------------------
    def synthetiser(self, texte: str, sortie: Path, chaine: str,
                    segment: str = "") -> dict:
        if not texte.strip():
            raise ErreurVoix("texte vide")
        maxi = self.contraintes().get("texte_max") or TEXTE_MAX
        if len(texte) > maxi:
            raise ErreurVoix(
                f"texte de {len(texte)} caracteres : /generate refuse au-dela "
                f"de {maxi}. Decouper en segments.")

        limites = self.contraintes()
        if not langue_acceptee(self.langue, limites):
            raise ErreurVoix(
                f"l'instance refuse la langue « {self.langue} » "
                f"(contrainte declaree : {limites.get('langue_detail')}). "
                "Lancer « --diagnostic » : c'est le piege documente de "
                "Voicebox, dont la doc publique annonce l'anglais et le "
                "chinois seuls.")

        # Le decoupage automatique de Voicebox raccorde les morceaux par un
        # fondu, audible sur une signature : on demande donc un seuil au moins
        # egal a la longueur du texte — sans jamais depasser ce que l'instance
        # declare accepter, sous peine d'un 422 apres coup.
        chunk = max(self.chunk, len(texte) + 1)
        plafond = limites.get("chunk_max")
        if plafond:
            chunk = min(chunk, plafond)
            if len(texte) >= chunk:
                print(f"--- avertissement : segment de {len(texte)} caracteres "
                      f"pour un decoupage plafonne a {chunk} par l'instance : "
                      "Voicebox va raccorder deux morceaux, le fondu peut "
                      "s'entendre. Raccourcir le segment. ---", file=sys.stderr)
        demande = {
            "profile_id": self.profil_de(chaine),
            "text": texte,
            "language": self.langue,
            "max_chunk_chars": chunk,
        }
        if self.moteur:
            demande["engine"] = self.moteur
        if self.taille:
            demande["model_size"] = self.taille
        if self.instruct:
            demande["instruct"] = self.instruct
        # Une graine fixe rend la prise REPRODUCTIBLE : c'est ce qui permet de
        # refabriquer a l'identique un bloc invariant (jingle, relance) si le
        # fichier est perdu, sans que la signature de la serie ne derive.
        graine = self.graines.get(segment, self.graines.get("defaut"))
        if graine is not None:
            demande["seed"] = int(graine)

        reponse = self._appel("/generate", donnees=demande)
        identifiant = reponse.get("id")
        if not identifiant:
            raise ErreurVoix(f"/generate n'a pas rendu d'identifiant : "
                             f"{str(reponse)[:200]}")

        sortie.parent.mkdir(parents=True, exist_ok=True)
        audio = self._appel(
            f"/audio/{urllib.parse.quote(str(identifiant))}", brut=True)
        if len(audio) < 1024:
            raise ErreurVoix(
                f"audio rendu par /audio/{identifiant} suspect "
                f"({len(audio)} octets) — generation probablement echouee")
        if not ressemble_a_de_l_audio(audio):
            raise ErreurVoix(
                f"/audio/{identifiant} n'a pas rendu de l'audio mais "
                f"{apercu(audio)}. Un serveur derriere un portail "
                "d'authentification repond souvent 200 avec une page de "
                "connexion : verifier les en-tetes d'authentification.")
        sortie.write_bytes(audio)
        return {"mode": "voicebox", "audio": str(sortie),
                "id": identifiant, "duree_s": reponse.get("duration"),
                "graine": demande.get("seed"),
                "moteur": self.moteur, "langue": self.langue}


def charger(nom: str, chemin_config: str = CONFIG_DEFAUT):
    if nom == "manuel":
        return MoteurManuel()
    if nom == "voicebox":
        return MoteurVoicebox(charger_config(chemin_config))
    raise ErreurVoix(f"moteur de voix inconnu : {nom}")


# --- Lecture du contrat declare par l'instance --------------------------------
def _schema_generation(schema: dict) -> dict:
    """Le schema de la requete /generate, quel que soit son nom."""
    for nom, corps in (schema.get("components", {})
                       .get("schemas", {}) or {}).items():
        if "generation" not in nom.lower() and "request" not in nom.lower():
            continue
        if "language" in ((corps.get("properties") or {})):
            return corps
    return {}


def _entier(champ, cle):
    """Lit une borne entiere, y compris cachee dans un anyOf."""
    if not isinstance(champ, dict):
        return None
    if isinstance(champ.get(cle), int):
        return champ[cle]
    for variante in champ.get("anyOf") or []:
        if isinstance(variante, dict) and isinstance(variante.get(cle), int):
            return variante[cle]
    return None


def lire_contraintes(schema: dict) -> dict:
    """Les limites que l'instance declare : langue, longueur, decoupage."""
    corps = _schema_generation(schema)
    proprietes = corps.get("properties") or {}
    nom, forme, valeur = _langues_acceptees(schema)
    return {
        "langue_forme": forme,
        "langue_valeur": valeur,
        "langue_detail": (f"{forme} {valeur}" if forme in ("pattern", "enum")
                          else "aucune contrainte declaree"),
        "texte_max": _entier(proprietes.get("text"), "maxLength"),
        "chunk_max": _entier(proprietes.get("max_chunk_chars"), "maximum"),
        "schema": nom,
    }


def langue_acceptee(langue: str, limites: dict) -> bool:
    """Vrai si l'instance accepte cette langue, d'apres son propre schema."""
    forme, valeur = limites.get("langue_forme"), limites.get("langue_valeur")
    if forme == "pattern":
        return bool(re.match(valeur, langue))
    if forme == "enum":
        return langue in valeur
    return True          # schema muet ou champ libre : on laisse passer


# --- Diagnostic ---------------------------------------------------------------
def _langues_acceptees(schema: dict):
    """Extrait du schema OpenAPI la contrainte reelle sur `language`."""
    composants = schema.get("components", {}).get("schemas", {})
    for nom, corps in composants.items():
        if "generation" not in nom.lower() and "request" not in nom.lower():
            continue
        champ = (corps.get("properties", {}) or {}).get("language")
        if not champ:
            continue
        for cle in ("pattern", "enum"):
            if cle in champ:
                return nom, cle, champ[cle]
        for variante in champ.get("anyOf", []) or []:
            for cle in ("pattern", "enum"):
                if cle in variante:
                    return nom, cle, variante[cle]
        return nom, "libre", None
    return None, None, None


def diagnostiquer(chemin_config: str) -> int:
    """Confronte l'instance Voicebox installee aux besoins du projet."""
    print("=== DIAGNOSTIC VOICEBOX ===\n")
    try:
        config = charger_config(chemin_config)
    except ErreurVoix as erreur:
        print(f"[!!] {erreur}")
        config = {}
    base = str(config.get("base_url", "http://localhost:8000")).rstrip("/")
    print(f"instance : {base}\n")

    constats, bloquants = [], []

    def point(libelle, ok, detail, bloquant=False):
        constats.append((libelle, ok, detail))
        if not ok and bloquant:
            bloquants.append(libelle)

    # Le diagnostic doit interroger l'instance EXACTEMENT comme le fera la
    # synthese : meme adresse, memes en-tetes. Sans cela, sur une instance
    # publiee derriere un portail, l'outil cense verifier que tout va bien
    # serait le seul a echouer — et il ferait chercher la panne au mauvais
    # endroit.
    entetes = {}
    try:
        verifier_url(base)
    except ErreurVoix as erreur:
        point("transport", False, str(erreur)[:200], bloquant=True)
    try:
        entetes = resoudre_entetes(config)
        if entetes:
            point("authentification", True,
                  f"{len(entetes)} en-tete(s) : {', '.join(sorted(entetes))}")
    except ErreurVoix as erreur:
        point("authentification", False, str(erreur)[:250], bloquant=True)

    def interroger(chemin, timeout=30):
        return _http(f"{base}{chemin}", timeout=timeout, entetes_sup=entetes)

    try:
        schema = interroger("/openapi.json")
        point("serveur joignable", True, base)
    except ErreurVoix as erreur:
        point("serveur joignable", False, str(erreur)[:250], bloquant=True)
        schema = None

    if schema:
        chemins = set(schema.get("paths", {}))
        for route in ("/generate", "/profiles"):
            point(f"route {route} exposee", route in chemins,
                  "presente" if route in chemins else "absente", bloquant=True)
        audio = [c for c in chemins if c.startswith("/audio/")]
        point("route /audio/{id} exposee", bool(audio),
              audio[0] if audio else "absente", bloquant=True)

        nom, forme, valeur = _langues_acceptees(schema)
        langue = config.get("language", "fr")
        if forme == "pattern":
            import re as _re
            accepte = bool(_re.match(valeur, langue))
            point(f"langue « {langue} » acceptee par {nom}", accepte,
                  f"contrainte {valeur}", bloquant=True)
        elif forme == "enum":
            accepte = langue in valeur
            point(f"langue « {langue} » acceptee par {nom}", accepte,
                  f"valeurs {valeur}", bloquant=True)
        elif forme == "libre":
            point(f"langue « {langue} »", True,
                  "aucune contrainte declaree dans le schema")
        else:
            point("contrainte de langue lisible", False,
                  "champ `language` introuvable dans le schema")

    try:
        profils = interroger("/profiles")
        liste = profils if isinstance(profils, list) else profils.get("profiles", [])
        point("profils de voix disponibles", bool(liste),
              f"{len(liste)} profil(s)", bloquant=True)
        if liste:
            print("Profils declares sur cette instance :")
            for profil in liste:
                if isinstance(profil, dict):
                    print(f"   - {profil.get('id', '?')}  "
                          f"{profil.get('name', '(sans nom)')}")
            print()
        declares = {c: p for c, p in (config.get("profils") or {}).items() if p}
        connus = {p.get("id") for p in liste if isinstance(p, dict)}
        for chaine, identifiant in declares.items():
            point(f"profil de la chaine {chaine} reconnu",
                  identifiant in connus, identifiant, bloquant=True)
        if not declares:
            point("profils renseignes dans la configuration", False,
                  "aucun — recopier ci-dessus l'identifiant de la voix clonee",
                  bloquant=True)
    except ErreurVoix as erreur:
        point("profils de voix disponibles", False, str(erreur)[:200],
              bloquant=True)

    moteur = config.get("engine", "chatterbox")
    point("moteur multilingue", moteur in MOTEURS_MULTILINGUES,
          f"{moteur} — le corpus est en francais, un moteur anglophone "
          "prononcerait mal les noms propres" if moteur not in
          MOTEURS_MULTILINGUES else moteur)

    for libelle, ok, detail in constats:
        print(f"   [{'OK' if ok else '!!'}] {libelle} — {detail}")

    if bloquants:
        print("\nDIAGNOSTIC : INSTANCE INUTILISABLE EN L'ETAT")
        for libelle in bloquants:
            print(f"  bloquant : {libelle}")
        print("\nRepli disponible sans rien installer : --moteur manuel, qui "
              "ecrit les textes a coller dans l'interface graphique.")
        return 3
    print("\nDIAGNOSTIC : INSTANCE CONFORME — synthese automatique possible.")
    return 0


# --- Auto-test ----------------------------------------------------------------
def self_test() -> int:
    essais, echecs = 0, []

    def verifier(libelle, condition):
        nonlocal essais
        essais += 1
        if not condition:
            echecs.append(libelle)

    # lecture du schema OpenAPI : les trois formes rencontrees
    verifier("pattern lu", _langues_acceptees(
        {"components": {"schemas": {"GenerationRequest": {"properties": {
            "language": {"pattern": "^(en|zh)$"}}}}}})[2] == "^(en|zh)$")
    verifier("enum lu", _langues_acceptees(
        {"components": {"schemas": {"GenerationRequest": {"properties": {
            "language": {"enum": ["en", "fr"]}}}}}})[2] == ["en", "fr"])
    verifier("anyOf lu", _langues_acceptees(
        {"components": {"schemas": {"GenerationRequest": {"properties": {
            "language": {"anyOf": [{"type": "null"},
                                   {"enum": ["fr"]}]}}}}}})[2] == ["fr"])
    verifier("schema muet", _langues_acceptees({"components": {}})[0] is None)

    # le moteur manuel doit ecrire un .txt et ne rien appeler
    dossier = Path("/tmp/_voix_selftest")
    shutil.rmtree(dossier, ignore_errors=True)
    resultat = MoteurManuel().synthetiser("Bonjour.", dossier / "intro.mp3",
                                          "victimes", "question")
    verifier("moteur manuel ecrit le texte",
             (dossier / "intro.txt").read_text(encoding="utf-8").strip()
             == "Bonjour.")
    verifier("moteur manuel n'invente pas d'audio", resultat["audio"] is None)
    shutil.rmtree(dossier, ignore_errors=True)

    # garde-fous de MoteurVoicebox, sans reseau
    moteur = MoteurVoicebox({"profils": {"victimes": "abc"},
                             "engine": "chatterbox", "language": "fr"})
    verifier("profil resolu", moteur.profil_de("victimes") == "abc")
    for cas, appel in (
            ("chaine sans profil", lambda: moteur.profil_de("permis")),
            ("texte vide", lambda: moteur.synthetiser("  ", Path("/tmp/x.mp3"),
                                                      "victimes")),
            ("texte trop long", lambda: moteur.synthetiser(
                "a" * (TEXTE_MAX + 1), Path("/tmp/x.mp3"), "victimes"))):
        essais += 1
        try:
            appel()
            echecs.append(f"cas non detecte : {cas}")
        except ErreurVoix:
            pass

    essais += 1
    try:
        MoteurVoicebox({"profils": {"victimes": "a"}, "engine": "inexistant"}).verifier()
        echecs.append("moteur TTS inconnu accepte")
    except ErreurVoix:
        pass

    essais += 1
    try:
        MoteurVoicebox({"engine": "chatterbox"}).verifier()
        echecs.append("absence de profil non detectee")
    except ErreurVoix:
        pass

    verifier("moteur manuel disponible sans configuration",
             charger("manuel").nom == "manuel")

    # --- contraintes lues dans le schema de l'instance ---------------------
    schema = {"components": {"schemas": {"GenerationRequest": {"properties": {
        "language": {"pattern": "^(en|zh)$"},
        "text": {"maxLength": 3000},
        "max_chunk_chars": {"anyOf": [{"type": "null"},
                                      {"type": "integer", "maximum": 1000}]}}}}}}
    limites = lire_contraintes(schema)
    verifier("plafond de decoupage lu", limites["chunk_max"] == 1000)
    verifier("longueur maximale lue", limites["texte_max"] == 3000)
    verifier("langue refusee par le pattern",
             langue_acceptee("fr", limites) is False)
    verifier("langue acceptee par le pattern", langue_acceptee("en", limites))
    verifier("schema muet : rien n'est impose",
             langue_acceptee("fr", lire_contraintes({})) is True)
    verifier("schema muet : aucun plafond invente",
             lire_contraintes({})["chunk_max"] is None)

    # --- en-tete Accept : un binaire ne se demande pas en JSON --------------
    # Le 406 tombait APRES la generation, donc apres le temps de calcul.
    vus = {}

    def _faux_urlopen(requete, timeout=None):
        vus[requete.full_url] = dict(requete.headers)
        binaire = "/audio/" in requete.full_url

        class _Reponse:
            def read(self_inner):
                return b"\x00" * 2048 if binaire else b"[]"

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False
        return _Reponse()

    vrai_urlopen = urllib.request.urlopen
    urllib.request.urlopen = _faux_urlopen
    try:
        _http("http://x/audio/1", brut=True)
        _http("http://x/profiles")
    finally:
        urllib.request.urlopen = vrai_urlopen
    verifier("audio demande en binaire",
             "audio" in vus["http://x/audio/1"]["Accept"])
    verifier("json demande en json",
             vus["http://x/profiles"]["Accept"] == "application/json")

    # --- transport et secrets ----------------------------------------------
    essais += 1
    try:
        verifier_url("http://voicebox.exemple.fr")
        echecs.append("instance distante en clair acceptee")
    except ErreurVoix:
        pass
    for correct in ("http://localhost:8000", "http://127.0.0.1:8000",
                    "https://voicebox.exemple.fr"):
        essais += 1
        try:
            verifier_url(correct)
        except ErreurVoix:
            echecs.append(f"url legitime refusee : {correct}")

    essais += 1
    try:
        resoudre_entetes({"auth_headers": {"X-Jeton": "secret-en-clair"}})
        echecs.append("secret en clair accepte dans la configuration")
    except ErreurVoix:
        pass
    essais += 1
    try:
        resoudre_entetes({"auth_headers": {"X-Jeton": "env:_VOIX_ABSENTE_"}})
        echecs.append("variable d'environnement absente non signalee")
    except ErreurVoix:
        pass
    os.environ["_VOIX_TEST_"] = "valeur-de-test"
    verifier("jeton lu dans l'environnement",
             resoudre_entetes({"auth_headers": {"X-Jeton": "env:_VOIX_TEST_"}})
             == {"X-Jeton": "valeur-de-test"})
    os.environ.pop("_VOIX_TEST_", None)
    verifier("aucune authentification par defaut", resoudre_entetes({}) == {})

    # --- ce qui revient de /audio doit etre de l'audio ----------------------
    verifier("mp3 etiquete reconnu", ressemble_a_de_l_audio(b"ID3\x03\x00" + b"\0" * 40))
    verifier("trame mpeg nue reconnue", ressemble_a_de_l_audio(b"\xff\xfb\x90\x00"))
    verifier("wav reconnu", ressemble_a_de_l_audio(b"RIFF\x24\x08\x00\x00WAVEfmt "))
    verifier("page de connexion refusee", not ressemble_a_de_l_audio(
        b"<!DOCTYPE html><html><head><title>Sign in"))
    verifier("erreur json refusee",
             not ressemble_a_de_l_audio(b'{"detail":"Not authenticated"}'))
    verifier("apercu lisible dans le message",
             "Not authenticated" in apercu(b'{"detail":"Not authenticated"}'))

    # --- une page HTML au lieu du JSON doit designer le portail --------------
    # Sans cela, le message disait « reponse non JSON » et faisait chercher la
    # panne du cote du serveur alors qu'elle est dans les en-tetes.
    def _rend(charge):
        def _faux(requete, timeout=None):
            class _R:
                def read(self_inner):
                    return charge

                def __enter__(self_inner):
                    return self_inner

                def __exit__(self_inner, *a):
                    return False
            return _R()
        return _faux

    vrai = urllib.request.urlopen
    for libelle, charge, attendu in (
            ("page de connexion designee comme telle",
             b"<!DOCTYPE html><html><head><title>Sign in</title>", "portail"),
            ("json casse reste un simple defaut de format",
             b"{ceci n'est pas du json", None)):
        urllib.request.urlopen = _rend(charge)
        essais += 1
        try:
            _http("http://x/openapi.json")
            echecs.append(f"{libelle} : aucune erreur levee")
        except ErreurVoix as erreur:
            texte = str(erreur)
            if attendu and attendu not in texte:
                echecs.append(f"{libelle} : « {texte[:80]} »")
            if attendu is None and "portail" in texte:
                echecs.append(f"{libelle} : portail evoque a tort")
            if "Recu" not in texte:
                echecs.append(f"{libelle} : la reponse recue n'est pas montree")
        finally:
            urllib.request.urlopen = vrai

    for echec in echecs:
        print(f"  !! {echec}")
    print(f"auto-test : {essais - len(echecs)}/{essais} verifications passees")
    return 1 if echecs else 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--config", default=CONFIG_DEFAUT)
    analyseur.add_argument("--diagnostic", action="store_true",
                           help="confronte l'instance Voicebox aux besoins")
    analyseur.add_argument("--self-test", action="store_true")
    options = analyseur.parse_args()

    if options.self_test:
        return self_test()
    if options.diagnostic:
        return diagnostiquer(options.config)
    analyseur.error("choisir --diagnostic ou --self-test")


if __name__ == "__main__":
    sys.exit(main())
