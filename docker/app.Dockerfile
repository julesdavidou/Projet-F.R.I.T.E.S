FROM python:3.11-slim

# Installation des outils système nécessaires pour l'audio (PyAudio / Speaches)
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation des dépendances Python pour éviter de les recalculer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie de l'intégralité du code source dans le conteneur
COPY . .

EXPOSE 8000

# On lance F.R.I.T.E.S.
# NB : à vérifier que cette commande fonctionne vraiement : peut-être qu'on aura des
# problèmes si chainlit n'est pas dans le PATH
CMD ["python", "-m", "chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]