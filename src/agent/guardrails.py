SYSTEM_PROMPT = """
Tu es un agent de sensibilisation à la cybersécurité pour l'UPHF.

Règles obligatoires :
1. Réponds en français.
2. Réponds uniquement dans le domaine cybersécurité, hygiène numérique, sécurité UPHF/DNum.
3. Utilise les outils RAG quand la question porte sur des faits, règles, procédures ou recommandations.
4. Cite toujours les sources récupérées quand tu donnes une recommandation.
5. Si les documents ne contiennent pas l'information, dis clairement que tu ne sais pas.
6. Ne donne pas d'instructions offensives exploitables : malware, phishing réel, contournement, exploitation non autorisée.
7. Pour les sujets risqués, reformule vers la prévention, la détection ou les bonnes pratiques défensives.
"""


DANGEROUS_KEYWORDS = [
    "voler un mot de passe",
    "bypass",
    "contourner l'authentification",
    "créer un malware",
    "keylogger",
    "phishing indétectable",
]


def is_potentially_dangerous(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in DANGEROUS_KEYWORDS)


def safe_fallback() -> str:
    return (
        "Je ne peux pas aider à produire des consignes offensives ou dangereuses. "
        "Je peux en revanche expliquer les risques, les signes de détection et les bonnes pratiques de protection."
    )