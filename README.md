# Market Recap Bot 📊

**Un bot qui t'envoie chaque matin (du lundi au vendredi) un email avec le recap des marchés.**

---

## 🎯 Ce qu'il fait

**Lundi matin** : Recap du week-end
- Clôture US (vendredi soir)
- Clôture Asie
- Bitcoin/Ethereum (mouvements du week-end)
- Top hausses/baisses de la semaine

**Mardi à vendredi matin** : Recap de la journée précédente + ouverture du jour
- Clôture US (hier soir)
- Clôture Asie (cette nuit)
- Ouverture Europe (ce matin)
- Bitcoin/Ethereum
- Top mouvements
- **Analyse IA basée sur les news Reuters du jour + hier**

**Exemple jeudi matin** :
- News Reuters du jeudi matin (juste lues)
- News Reuters du mercredi soir (fermeture US)
- Claude analyse : "Voici les chiffres de hier, voici les news du jour et d'hier, que s'est-il passé ?"

Email reçu = **mise en page HTML** (pas juste du texte brut).

**Sources** :
- **Données marchés** : Yahoo Finance / Morningstar
- **News** : Reuters via NewsAPI (news du jour + jour précédent)
- **Analyse** : Claude (basée sur vraies données + vraies news) (via yfinance)

---

## 📋 Mise en place (5 min)

### Étape 1️⃣ : Créer un mot de passe d'application Gmail

Google n'autorise pas d'envoyer des emails automatiquement avec ton mot de passe normal. Il faut créer un "mot de passe d'application" :

1. Va sur **https://myaccount.google.com/security**
2. Active **Validation en deux étapes** (si ce n'est pas fait)
3. Va sur **https://myaccount.google.com/apppasswords**
4. Sélectionne "Mail" et "Windows (ou ton device)"
5. Clique sur **Générer**
6. Google te crée un code à 16 caractères (ex: `abcd efgh ijkl mnop`)
   - **Copie ce code** → tu en auras besoin à l'étape 3

---

### Étape 2️⃣ : Créer un repo GitHub

1. Va sur **github.com**, crée un compte si besoin
2. Clique sur **New Repository**
3. Donne-lui un nom (ex: `market-recap-bot`)
4. Mets-le en **Private** (optionnel, mais plus sûr)
5. Crée le repo

Puis, ajoute les fichiers qu'on vient de créer :
- `market_bot.py`
- `requirements.txt`
- Le dossier `.github/workflows/run.yml`

**Simplest way** : dans GitHub, clique "Add file" → "Upload files" → glisse les fichiers (GitHub gardera la structure des dossiers).

---

### Étape 3️⃣ : Obtenir une clé API Claude (2 min)

Le bot utilise Claude pour générer un résumé intelligent des marchés. C'est gratuit !

1. Va sur **https://console.anthropic.com**
2. Crée un compte (gratuit, juste email + mot de passe)
3. Va dans **API Keys** (à gauche)
4. Clique **Create Key**
5. Donne-lui un nom (ex: "market-bot")
6. **Copie la clé** (longue chaîne commençant par `sk-...`)

---

### Étape 4️⃣ : Ajouter tous tes secrets GitHub

Les "secrets" = tes identifiants sont chiffrés sur GitHub (pas visibles).

1. Dans ton repo → **Settings** (en haut à droite)
2. À gauche → **Secrets and variables** → **Actions**
3. Clique sur **New repository secret** (bouton vert)

Crée ces **5 secrets** :

| Nom | Valeur |
|---|---|
| `EMAIL_ADDRESS` | Ton adresse Gmail (ex: `moi@gmail.com`) |
| `EMAIL_PASSWORD` | Le code à 16 caractères de l'étape 1 (sans espaces) |
| `EMAIL_TO` | L'adresse où tu veux reçevoir le recap |
| `ANTHROPIC_API_KEY` | Ta clé API Claude (commençant par `sk-...`) |
| `NEWSAPI_KEY` | Ta clé API NewsAPI (pour les news Reuters) |

**Exemple** : 
- Gmail code `abcd efgh ijkl mnop` → tu mets `abcdefghijklmnop` (sans espaces)
- Clé Claude `sk-ant-v0-abc123...` → tu la copies telle quelle
- Clé NewsAPI `xxxxxxxxxxxxx` → tu la copies telle quelle

---

### Étape 5️⃣ : Tester

1. Dans ton repo → **Actions** (en haut)
2. À gauche → **Daily Market Recap**
3. À droite → **Run workflow** (bouton bleu)
4. **Run workflow** (confirmation)

Attends **45-60 secondes**, tu dois recevoir le mail avec le résumé IA.

Si ça marche pas :
- Vérifie que les 4 secrets sont bien remplis (Settings → Secrets)
- Regarde les logs de GitHub (Actions → Daily Market Recap → dernier run → voir les logs rouges si erreur)
- L'API Claude prend un peu de temps la première fois

---

## ✅ C'est prêt !

Une fois testé, le bot envoie automatiquement un email chaque matin à ~**9h45 heure de Paris** (lundi à vendredi).

Ton PC n'a besoin d'être allumé.

---

## 🎨 Personnaliser

### Ajouter/retirer des indices ou actions

Ouvre `market_bot.py`, cherche la section `ACTIFS À SUIVRE` (vers le haut) :

```python
INDICES = {
    "US": {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        # Ajoute d'autres tickers ici
    },
    ...
}

WATCHLIST = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    # Ajoute d'autres actions ici
}
```

Les tickers respectent le format **Yahoo Finance** :
- Actions US : `AAPL` (Apple), `MSFT` (Microsoft), `NVDA` (Nvidia)...
- Actions FR : `MC.PA` (LVMH), `TTE.PA` (TotalEnergies)...
- Indices : `^GSPC` (S&P500), `^FCHI` (CAC40)...
- Crypto : `BTC-USD`, `ETH-USD`...

Cherche les tickers sur **https://finance.yahoo.com**.

### Changer l'horaire d'envoi

Fichier `.github/workflows/run.yml`, cherche cette ligne :

```yaml
- cron: "45 8 * * 1-5"
```

Change les nombres :
- `45` = minutes
- `8` = heure (en UTC)
- `1-5` = jours (1=lundi, 5=vendredi)

**Exemples** :
- `0 7 * * 1-5` → 7h00 UTC (~8h Paris)
- `30 8 * * 1-5` → 8h30 UTC (~9h30 Paris)

---

## 🛠️ Dépannage

**"Email ne reçoit pas"**
- Vérifie les secrets (Settings → Secrets → vérifie que c'est bien rempli)
- Regarde les logs GitHub (Actions → run → voir les erreurs rouges)

**"Erreur : invalid credentials"**
- Ton mot de passe d'application est faux → régénère-le sur myaccount.google.com/apppasswords
- Assure-toi d'avoir retiré les espaces du code 16 caractères

**"401 Unauthorized"**
- Validation en 2 étapes Gmail n'est pas activée → active-la avant de générer le mot de passe

---

**"Erreur : ANTHROPIC_API_KEY not defined"**
- Ta clé API Claude n'est pas dans les secrets GitHub → va dans Settings → Secrets → ajoute ANTHROPIC_API_KEY

---

## 🛠️ Tester en local (optionnel)

Si tu veux tester le bot sur ton PC avant :

```bash
pip install -r requirements.txt
export EMAIL_ADDRESS="toi@gmail.com"
export EMAIL_PASSWORD="xxxxxxxxxxxxxxxx"
export EMAIL_TO="toi@gmail.com"
export ANTHROPIC_API_KEY="sk-ant-v0-..."
python market_bot.py
```

---

## 📞 Questions ?

Si ça coince :
1. Regarde les logs GitHub (Actions → run → voir le message d'erreur en rouge)
2. Vérifie que les 4 secrets sont bien remplis (Settings → Secrets)
3. Essaie un run manuel (Actions → Run workflow)

---

**Voilà !** Le bot tourne ensuite tout seul chaque matin. 🚀
