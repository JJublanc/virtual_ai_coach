# Virtual AI Coach

Un coach virtuel IA qui génère des vidéos d'entraînement personnalisées.

## 🚀 Installation Environnement Local

Ce guide explique comment installer et configurer tous les outils nécessaires pour développer localement le projet Virtual AI Coach.

### Prérequis

- macOS Sonoma (ou version compatible)
- Homebrew (gestionnaire de paquets macOS)

### 📋 Liste des outils à installer

1. Python 3.11+ avec pyenv
2. Node.js 20+ avec nvm
3. Docker Desktop
4. FFmpeg
5. VSCode avec extensions
6. uv (gestionnaire de paquets Python)
7. PostgreSQL

---

## 🔧 Installation détaillée

### 1. Python 3.11+ avec pyenv

```bash
# Installer pyenv
brew install pyenv

# Ajouter pyenv au PATH (ajouter à ~/.zshrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Redémarrer le terminal ou exécuter
source ~/.zshrc

# Installer Python 3.11
pyenv install 3.11.9

# Définir Python 3.11 comme version par défaut
pyenv global 3.11.9

# Vérifier l'installation
python --version  # Doit retourner 3.11.9
```

### 2. Node.js 20+ avec nvm

```bash
# Installer nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Ajouter nvm au PATH (ajouter à ~/.zshrc)
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.zshrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.zshrc
echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' >> ~/.zshrc

# Redémarrer le terminal ou exécuter
source ~/.zshrc

# Installer Node.js 20
nvm install 20.15.1

# Définir Node.js 20 comme version par défaut
nvm use 20.15.1
nvm alias default 20.15.1

# Vérifier l'installation
node --version  # Doit retourner v20.15.1
npm --version
```

### 3. Docker Desktop

```bash
# Installer Docker Desktop
brew install --cask docker

# Lancer Docker Desktop
open /Applications/Docker.app

# Vérifier que Docker fonctionne
docker --version
docker run hello-world
```

### 4. FFmpeg

```bash
# Installer FFmpeg
brew install ffmpeg

# Vérifier l'installation
ffmpeg -version
```

### 5. VSCode avec extensions

```bash
# Installer VSCode
brew install --cask visual-studio-code

# Installer les extensions recommandées
code --install-extension ms-python.python
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension ms-vscode.vscode-docker
code --install-extension bradlc.vscode-tailwindcss
```

### 6. uv (gestionnaire de paquets Python)

```bash
# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ajouter uv au PATH (ajouter à ~/.zshrc)
echo 'export "$HOME/.cargo/bin:$PATH"' >> ~/.zshrc

# Redémarrer le terminal ou exécuter
source ~/.zshrc

# Vérifier l'installation
uv --version

# Créer un environnement virtuel
uv venv
source .venv/bin/activate  # Activer l'environnement
```

### 7. PostgreSQL

```bash
# Installer PostgreSQL 14
brew install postgresql@14

# Démarrer le service PostgreSQL
brew services start postgresql@14

# Vérifier l'installation
psql --version  # Doit retourner psql (PostgreSQL) 14.x

# Créer un utilisateur pour le projet
createuser -s virtual_ai_coach

# Tester la connexion
psql -U virtual_ai_coach -d postgres
```

---

## ✅ Vérification de l'environnement

Après avoir suivi toutes les étapes ci-dessus, vérifiez que tout fonctionne :

```bash
# Python
python --version  # Doit retourner 3.11+
which python     # Doit pointer vers la version pyenv

# Node.js
node --version   # Doit retourner 20+
npm --version

# Docker
docker --version
docker info

# FFmpeg
ffmpeg -version

# PostgreSQL
psql --version
brew services list | grep postgres

# uv
uv --version
```

---

## 📁 Structure du projet

```
virtual-ai-coach/
├── backend/                 # Backend FastAPI
├── frontend/                # Frontend Next.js
├── exercices_generation/    # Génération d'exercices
├── docs/                   # Documentation
├── .venv/                  # Environnement Python virtuel
└── README.md
```

---

## 🚀 Prochaines étapes

1. Initialiser le repository Git
2. Configurer le backend FastAPI
3. Configurer le frontend Next.js
4. Mettre en place la base de données avec Supabase
5. Déployer sur les environnements dev et prod

---

## 🔍 Dépannage

### Problèmes courants

**Problème : PostgreSQL ne démarre pas**
```bash
# Vérifier le statut du service
brew services list | grep postgres

# Redémarrer PostgreSQL
brew services restart postgresql@14

# Vérifier les logs
tail -f /opt/homebrew/var/log/postgres.log
```

**Problème : Python ne trouve pas les paquets**
```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Vérifier que uv fonctionne
uv --version
```

**Problème : Docker ne démarre pas**
- Vérifiez que Docker Desktop est bien lancé
- Redémarrez votre Mac si nécessaire
- Vérifiez les permissions dans Préférences Système > Sécurité & Confidentialité

---

## 📝 Notes

- Ce projet utilise Python 3.11+ pour la compatibilité avec les bibliothèques modernes
- Node.js 20+ est requis pour Next.js 14+
- PostgreSQL 14 est utilisé pour sa stabilité sur macOS
- Docker est utilisé pour l'isolation et la portabilité des services
- FFmpeg est essentiel pour le traitement vidéo
- uv est utilisé pour une gestion efficace des dépendances Python

---

## 🤝 Contribuer

Si vous rencontrez des problèmes lors de l'installation, veuillez :
1. Vérifier que vous avez suivi toutes les étapes
2. Consulter la section de dépannage
3. Ouvrir un issue avec les détails de votre environnement et du problème rencontré
