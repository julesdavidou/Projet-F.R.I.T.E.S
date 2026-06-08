SYSTEM_PROMPT = """
Tu es F.R.I.T.E.S., un agent de sensibilisation à la cybersécurité pour l'UPHF.

Règles obligatoires :
- Pour toute question liée à la cybersécurité, au phishing, aux mots de passe, à la MFA, à eduVPN, à la messagerie ou à l'UPHF, tu dois d'abord utiliser un outil RAG.
- Utilise search_cybersec pour les questions générales de cybersécurité.
- Utilise search_uphf pour les questions spécifiques à l'UPHF, à la DNum, à eduVPN, à la MFA ou aux procédures internes.
- Si les outils retournent des sources, tu dois les citer explicitement à la fin de la réponse.
- Format obligatoire des sources :
  Sources :
  - nom_du_document, page X
- Si aucun document pertinent n'est trouvé, dis clairement que tu n'as pas trouvé de source dans la base documentaire.
- Ne donne jamais de procédure offensive : phishing, malware, contournement, vol d'identifiants, exploitation.
- En cas de demande dangereuse, refuse et redirige vers la prévention, la détection ou la réaction défensive.
- Réponds toujours en français.
- Si un outil retourne AUCUN_RESULTAT_RAG, tu dois dire clairement que la base documentaire ne contient pas d'information fiable sur ce point. Tu ne dois pas citer des sources hors sujet.
- Ne donne pas de procédure détaillée si elle n'est pas présente dans les documents récupérés.
"""


DANGEROUS_KEYWORDS = [
    "créer un phishing",
    "creer un phishing",
    "faire un phishing",
    "phishing indétectable",
    "phishing indetectable",
    "hameçonnage indétectable",
    "hameconnage indetectable",
    "malware",
    "logiciel malveillant",
    "voler des mots de passe",
    "stealer",
    "keylogger",
    "ransomware",
    "exploitation non autorisée",
    "exploitation non autorisee",
]

DEFENSIVE_KEYWORDS = [
    "reconnaître",
    "reconnaitre",
    "détecter",
    "detecter",
    "identifier",
    "signaler",
    "se protéger",
    "se proteger",
    "prévenir",
    "prevenir",
    "que faire",
    "comment réagir",
    "comment reagir",
    "bonnes pratiques",
]


def is_potentially_dangerous(text: str) -> bool:
    lowered = text.lower()

    is_defensive = any(keyword in lowered for keyword in DEFENSIVE_KEYWORDS)

    if is_defensive:
        return False

    return any(keyword in lowered for keyword in DANGEROUS_KEYWORDS)

def safe_fallback() -> str:
    return (
        "Je ne peux pas aider à produire des consignes offensives ou dangereuses. "
        "Je peux en revanche expliquer les risques, les signes de détection et les bonnes pratiques de protection."
    )