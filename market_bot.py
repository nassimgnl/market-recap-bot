#!/usr/bin/env python3
"""
Market Recap Bot v4 - Avec Reuters via NewsAPI
===============================================
Récupère les données des marchés + news Reuters VRAIES pour l'analyse IA.

Données : Yahoo Finance / Morningstar
News : Reuters via NewsAPI
IA : Claude (analyse basée sur news vraies)

Variables d'environnement requises:
  EMAIL_ADDRESS       -> ton adresse Gmail
  EMAIL_PASSWORD      -> mot de passe d'application Gmail (16 caractères)
  EMAIL_TO            -> où envoyer le recap
  ANTHROPIC_API_KEY   -> clé API Claude
  NEWSAPI_KEY         -> clé API NewsAPI (pour Reuters)
"""

import os
import smtplib
import ssl
import json
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yfinance as yf
import requests

# ============================================================================
# ACTIFS À SUIVRE
# ============================================================================

INDICES = {
    "US": {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Dow Jones": "^DJI",
    },
    "EUROPE": {
        "CAC 40": "^FCHI",
        "DAX": "^GDAXI",
        "FTSE 100": "^FTSE",
    },
    "ASIE": {
        "Nikkei 225": "^N225",
        "Hang Seng": "^HSI",
    },
}

CRYPTO = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
}

WATCHLIST = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "Amazon": "AMZN",
    "Meta": "META",
    "Tesla": "TSLA",
}

# ============================================================================
# RÉCUPÉRATION DES DONNÉES DE MARCHÉ
# ============================================================================

def get_price_change(ticker: str):
    """Retourne: (prix_actuel, variation_%), ou (None, None) si erreur"""
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if data.empty or len(data) < 2:
            return None, None
        
        last_close = data["Close"].iloc[-1]
        prev_close = data["Close"].iloc[-2]
        change = ((last_close - prev_close) / prev_close) * 100
        
        return float(last_close), float(change)
    except Exception:
        return None, None


def collect_indices(category):
    """Récupère les données d'une catégorie d'indices"""
    results = []
    for name, ticker in INDICES[category].items():
        price, change = get_price_change(ticker)
        if price is not None:
            results.append({
                "name": name,
                "price": price,
                "change": change,
                "color": "green" if change >= 0 else "red"
            })
    return results


def get_top_movers():
    """Top 3 hausses et 3 baisses de la watchlist"""
    all_moves = []
    for name, ticker in WATCHLIST.items():
        price, change = get_price_change(ticker)
        if price is not None:
            all_moves.append({
                "name": name,
                "price": price,
                "change": change,
                "color": "green" if change >= 0 else "red"
            })
    
    all_moves.sort(key=lambda x: x["change"])
    return {
        "gainers": list(reversed(all_moves[-3:])),
        "losers": all_moves[:3]
    }


def get_crypto_data():
    """Bitcoin et Ethereum"""
    results = []
    for name, ticker in CRYPTO.items():
        price, change = get_price_change(ticker)
        if price is not None:
            results.append({
                "name": name,
                "price": price,
                "change": change,
                "color": "green" if change >= 0 else "red"
            })
    return results


# ============================================================================
# RÉCUPÉRATION DES NEWS REUTERS VIA NEWSAPI
# ============================================================================

def get_reuters_news(api_key, days_back=1):
    """
    Récupère les news Reuters des derniers jours via NewsAPI.
    days_back=1 : news d'hier et d'aujourd'hui
    Retourne: [(titre, source, date), ...]
    """
    
    if not api_key:
        print("⚠️  NEWSAPI_KEY non définie")
        return []
    
    try:
        # Chercher les news Reuters des derniers jours
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "Reuters market finance",
            "sources": "reuters",
            "from": from_date,
            "to": to_date,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": api_key,
            "pageSize": 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            news = []
            for article in articles[:8]:  # Top 8 news
                news.append({
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", "Reuters"),
                    "date": article.get("publishedAt", ""),
                    "url": article.get("url", "")
                })
            return news
        else:
            print(f"⚠️  NewsAPI error: {response.status_code}")
            return []
    
    except Exception as e:
        print(f"⚠️  Erreur récupération news: {e}")
        return []


# ============================================================================
# GÉNÉRATION DE L'ANALYSE IA AVEC NEWS VRAIES
# ============================================================================

def generate_ai_analysis(us_indices, asia_indices, europe_indices, crypto, movers, reuters_news, is_monday):
    """
    Appelle Claude pour générer une analyse basée sur:
    - Les vrais chiffres des marchés
    - Les vraies news Reuters
    """
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY non définie")
        return None
    
    # Préparer le contexte
    def format_indices(indices):
        return ", ".join([f"{i['name']} {i['change']:+.2f}%" for i in indices])
    
    # News Reuters en texte
    news_text = "\n".join([f"- {n['title']}" for n in reuters_news[:5]])
    
    context = f"""Tu es un analyste financier expert. 

DONNÉES DES MARCHÉS D'AUJOURD'HUI:
- US: {format_indices(us_indices)}
- Asie: {format_indices(asia_indices)}
- Europe: {format_indices(europe_indices)}
- Crypto: {format_indices(crypto)}

ACTUALITÉS REUTERS (contexte):
{news_text}

Basé UNIQUEMENT sur les données et news ci-dessus, écris un résumé court (3-4 phrases) 
qui explique les mouvements des marchés en lien avec les news Reuters.

Sois précis, analytique, cite les secteurs/valeurs concernés.
Résumé:
"""
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-6",
                "max_tokens": 300,
                "messages": [
                    {"role": "user", "content": context}
                ]
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            analysis = data["content"][0]["text"].strip()
            return analysis
        else:
            print(f"⚠️  Erreur API Claude: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"⚠️  Erreur génération analyse: {e}")
        return None


# ============================================================================
# GÉNÉRATION HTML DE L'EMAIL
# ============================================================================

def format_change(change):
    """Formate la variation: +2.34% ou -1.56%"""
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f}%"


def build_html_email(is_monday, analysis, reuters_news):
    """Crée le HTML de l'email"""
    
    # Récupérer les données
    us_indices = collect_indices("US")
    europe_indices = collect_indices("EUROPE")
    asia_indices = collect_indices("ASIE")
    crypto = get_crypto_data()
    movers = get_top_movers()
    
    today = datetime.now().strftime("%A %d %B %Y").capitalize()
    us_label = "Clôture US — vendredi soir" if is_monday else "Clôture US — hier soir"
    asia_label = "Clôture Asie — ce matin" if is_monday else "Clôture Asie — cette nuit"
    
    def make_rows(indices):
        rows = ""
        for idx in indices:
            color = idx["color"]
            rows += f"""
            <tr>
              <td class="name">{idx["name"]}</td>
              <td class="price">{idx["price']:.2f}</td>
              <td class="change {color}">{format_change(idx["change"])}</td>
            </tr>
            """
        return rows
    
    def make_mover_rows(movers):
        rows = ""
        for m in movers:
            color = m["color"]
            rows += f"""
            <tr>
              <td class="mover-name">{m["name"]}</td>
              <td class="change {color}">{format_change(m["change"])}</td>
            </tr>
            """
        return rows
    
    # Section analyse IA
    analysis_section = ""
    if analysis:
        analysis_section = f"""
    <!-- ANALYSE -->
    <div class="section analysis-section">
      <div class="section-title">📊 Analyse du jour</div>
      <p class="analysis-text">{analysis}</p>
      <div class="source-note">Source: Données Yahoo Finance + News Reuters via NewsAPI</div>
    </div>
    """
    
    # Section news Reuters
    news_section = ""
    if reuters_news:
        news_html = ""
        for news in reuters_news[:5]:
            date_str = news["date"][:10] if news["date"] else ""
            news_html += f"""
            <div class="news-item">
              <div class="news-title">{news["title"]}</div>
              <div class="news-meta">{news["source"]} • {date_str}</div>
            </div>
            """
        
        news_section = f"""
    <!-- REUTERS NEWS -->
    <div class="section news-section">
      <div class="section-title">📰 Actualités Reuters</div>
      {news_html}
    </div>
    """
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recap Marchés</title>
<style>
  * {{ box-sizing: border-box; }}
  
  body {{
    margin: 0;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #f5f5f5;
    line-height: 1.5;
  }}
  
  .email {{
    max-width: 620px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  
  .header {{
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 30px 25px;
    text-align: center;
  }}
  
  .header h1 {{
    margin: 0 0 10px 0;
    font-size: 28px;
    font-weight: 700;
  }}
  
  .header p {{
    margin: 0;
    font-size: 13px;
    opacity: 0.9;
  }}
  
  .section {{
    padding: 25px;
    border-bottom: 1px solid #f0f0f0;
  }}
  
  .section:last-child {{
    border-bottom: none;
  }}
  
  .analysis-section {{
    background: linear-gradient(135deg, rgba(30, 60, 114, 0.05) 0%, rgba(42, 82, 152, 0.05) 100%);
    border-left: 4px solid #1e3c72;
  }}
  
  .analysis-text {{
    margin: 0 0 12px 0;
    font-size: 14px;
    line-height: 1.7;
    color: #1a1a1a;
    font-style: italic;
  }}
  
  .source-note {{
    font-size: 11px;
    color: #999;
    margin: 0;
  }}
  
  .news-section {{
    background: #fafafa;
  }}
  
  .news-item {{
    padding: 12px 0;
    border-top: 1px solid #f0f0f0;
  }}
  
  .news-item:first-child {{
    border-top: none;
  }}
  
  .news-title {{
    font-size: 13px;
    font-weight: 600;
    color: #333;
    line-height: 1.5;
  }}
  
  .news-meta {{
    font-size: 11px;
    color: #999;
    margin-top: 4px;
  }}
  
  .section-title {{
    font-size: 14px;
    font-weight: 700;
    color: #1e3c72;
    margin: 0 0 15px 0;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  
  td {{
    padding: 9px 0;
    font-size: 13px;
    border-top: 1px solid #f5f5f5;
  }}
  
  td:first-child {{ padding-left: 0; }}
  td:last-child {{ padding-right: 0; }}
  
  .name {{
    font-weight: 600;
    color: #333;
  }}
  
  .price {{
    text-align: right;
    color: #999;
    font-family: 'Courier New', monospace;
    font-size: 12px;
  }}
  
  .change {{
    text-align: right;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    width: 80px;
  }}
  
  .green {{ color: #16a34a; }}
  .red {{ color: #dc2626; }}
  
  .movers-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
  }}
  
  .movers-col-title {{
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
  }}
  
  .mover-row {{
    padding: 6px 0;
    font-size: 13px;
    border-top: 1px solid #f5f5f5;
  }}
  
  .mover-name {{
    font-weight: 500;
    color: #333;
  }}
  
  .footer {{
    padding: 20px 25px;
    background: #fafafa;
    border-top: 1px solid #f0f0f0;
    text-align: center;
    font-size: 11px;
    color: #999;
    line-height: 1.6;
  }}
  
  .logo {{
    font-size: 20px;
    margin-right: 8px;
  }}
</style>
</head>
<body>
  <div class="email">
    <!-- HEADER -->
    <div class="header">
      <h1><span class="logo">📊</span> Recap Marchés</h1>
      <p>{today}</p>
    </div>
    
    {analysis_section}
    {news_section}
    
    <!-- INDICES US -->
    <div class="section">
      <div class="section-title">🇺🇸 {us_label}</div>
      <div class="source-note">Source: Yahoo Finance / Morningstar</div>
      <table style="margin-top: 10px;">
        {make_rows(us_indices)}
      </table>
    </div>
    
    <!-- INDICES ASIE -->
    <div class="section">
      <div class="section-title">🌏 {asia_label}</div>
      <div class="source-note">Source: Yahoo Finance / Morningstar</div>
      <table style="margin-top: 10px;">
        {make_rows(asia_indices)}
      </table>
    </div>
    
    <!-- INDICES EUROPE -->
    <div class="section">
      <div class="section-title">🇪🇺 Ouverture Europe — ce matin</div>
      <div class="source-note">Source: Yahoo Finance / Morningstar</div>
      <table style="margin-top: 10px;">
        {make_rows(europe_indices)}
      </table>
    </div>
    
    <!-- CRYPTO -->
    <div class="section">
      <div class="section-title">₿ Crypto</div>
      <div class="source-note">Source: Yahoo Finance / CoinGecko</div>
      <table style="margin-top: 10px;">
        {make_rows(crypto)}
      </table>
    </div>
    
    <!-- TOP MOUVEMENTS -->
    <div class="section">
      <div class="section-title">📈 Top Mouvements</div>
      <div class="source-note">Source: Yahoo Finance / Morningstar</div>
      <div class="movers-grid" style="margin-top: 15px;">
        <div>
          <div class="movers-col-title green">🚀 Hausses</div>
          <table>
            {make_mover_rows(movers['gainers'])}
          </table>
        </div>
        <div>
          <div class="movers-col-title red">📉 Baisses</div>
          <table>
            {make_mover_rows(movers['losers'])}
          </table>
        </div>
      </div>
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
      <p><strong>Sources</strong><br>
      • Données marchés: Yahoo Finance / Morningstar<br>
      • News: Reuters via NewsAPI<br>
      • Analyse: Claude (Anthropic)<br>
      <small>Généré automatiquement chaque matin lundi-vendredi.</small></p>
    </div>
  </div>
</body>
</html>
"""
    return html


# ============================================================================
# ENVOI DE L'EMAIL
# ============================================================================

def send_email(html_content, is_monday):
    """Envoie l'email via Gmail"""
    
    sender = os.environ.get("EMAIL_ADDRESS")
    password = os.environ.get("EMAIL_PASSWORD")
    recipients_str = os.environ.get("EMAIL_TO")
    
    if not all([sender, password, recipients_str]):
        print("❌ Variables d'environnement manquantes!")
        return False
    
    recipients = [r.strip() for r in recipients_str.split(",")]
    
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    
    subject = "📊 Recap du Week-end" if is_monday else "📊 Recap Marchés"
    msg["Subject"] = f"{subject} — {datetime.now().strftime('%d/%m/%Y')}"
    
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        print("✅ Email envoyé avec succès!")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    is_monday = datetime.now().weekday() == 0
    
    print(f"🤖 Génération du recap... (lundi: {is_monday})")
    
    # Récupérer les données
    us_indices = collect_indices("US")
    asia_indices = collect_indices("ASIE")
    europe_indices = collect_indices("EUROPE")
    crypto = get_crypto_data()
    movers = get_top_movers()
    
    # Récupérer les news Reuters
    print("📰 Récupération des news Reuters...")
    newsapi_key = os.environ.get("NEWSAPI_KEY")
    reuters_news = get_reuters_news(newsapi_key, days_back=2)
    print(f"   → {len(reuters_news)} news trouvées")
    
    # Générer l'analyse IA basée sur news vraies
    print("🧠 Génération de l'analyse IA...")
    analysis = generate_ai_analysis(us_indices, asia_indices, europe_indices, crypto, movers, reuters_news, is_monday)
    
    # Générer et envoyer l'email
    html = build_html_email(is_monday, analysis, reuters_news)
    send_email(html, is_monday)


if __name__ == "__main__":
    main()
