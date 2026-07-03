#!/usr/bin/env python3
"""
Market Recap Bot v2 - Zéro Config
==================================
Récupère les données des marchés et envoie un email HTML chaque matin.

Données : Yahoo Finance / Morningstar (via yfinance)
Horaire : automatiquement via GitHub Actions
Mise en page : HTML design terminal financier

Variables d'environnement:
  EMAIL_ADDRESS   -> ton adresse Gmail
  EMAIL_PASSWORD  -> mot de passe d'application Gmail (16 caractères)
  EMAIL_TO        -> où envoyer le recap (email de destination)
"""

import os
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yfinance as yf
import feedparser

# ============================================================================
# SECTEURS & THÈMES (LIVE DATA)
# ============================================================================

SECTORS = {
    "Tech": "XLK",
    "Énergie": "XLE",
    "Finance": "XLF",
    "Santé": "XLV",
    "Industrie": "XLI",
    "Immobilier": "XLRE",
    "Conso discrétionnaire": "XLY",
    "Conso de base": "XLP",
    "Utilities": "XLU",
    "Matériaux": "XLB"
}

THEMES = {
    "Semi-conducteurs": ["NVDA", "AMD", "TSM", "ASML"],
    "IA": ["MSFT", "NVDA", "GOOGL", "PLTR"],
    "Biopharma": ["LLY", "MRK", "PFE", "BMY"],
    "EV": ["TSLA", "RIVN", "LCID"],
    "Solaire": ["ENPH", "SEDG", "FSLR"],
    "Crypto": ["COIN", "MSTR"],
    "Cybersécurité": ["CRWD", "PANW", "ZS"]
}

def get_sector_performance():
    results = []
    for name, ticker in SECTORS.items():
        price, change = get_price_change(ticker)
        if change is not None:
            results.append({"name": name, "change": change})
    results.sort(key=lambda x: x["change"], reverse=True)
    return results

def get_theme_performance():
    results = []
    for theme, tickers in THEMES.items():
        changes = []
        for t in tickers:
            price, change = get_price_change(t)
            if change is not None:
                changes.append(change)
        if changes:
            avg = sum(changes) / len(changes)
            results.append({"theme": theme, "change": avg})
    results.sort(key=lambda x: x["change"], reverse=True)
    return results


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
# RÉCUPÉRATION DES DONNÉES
# ============================================================================

def get_price_change(ticker: str):
    """
    Retourne: (prix_actuel, variation_%), ou (None, None) si erreur
    """
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
# GÉNÉRATION HTML DE L'EMAIL
# ============================================================================

def format_change(change):
    """Formate la variation: +2.34% ou -1.56%"""
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.2f}%"



# =========================
# MACRO NEWS (GOOGLE NEWS)
# =========================

import urllib.parse
import feedparser

def get_news(query):
    base_url = "https://news.google.com/rss/search?q="

    encoded_query = urllib.parse.quote(query)

    url = base_url + encoded_query + "&hl=en&gl=US&ceid=US:en"

    feed = feedparser.parse(url)

    news = []
    for entry in feed.entries[:5]:
        news.append({
            "title": entry.title,
            "link": entry.link
        })

    return news

def build_macro_section():
    regions = {
        "🇺🇸 USA": "US economy inflation Fed jobs PMI",
        "🇪🇺 Europe": "Europe inflation ECB economy",
        "🇬🇧 UK": "UK economy BoE inflation",
        "🇯🇵 Japan": "Japan BoJ economy",
        "🇨🇳 China": "China PMI economy trade"
    }

    text = "📰 En bref\n\n"
    all_titles = []

    for region, query in regions.items():
        news = get_news(query)
        text += region + " :\n"

        for n in news:
            text += f"- {n['title']}\n  ({n['link']})\n"
            all_titles.append(n['title'])

        text += "\n"

    return text, all_titles


KEYWORDS = ["inflation","fed","ecb","jobs","pmi","gdp","recession","oil","war","tariff","earnings"]

def market_sentiment(titles):
    score = 0
    for t in titles:
        t = t.lower()
        if any(k in t for k in KEYWORDS):
            score += 1
        if any(k in t for k in ["fall","drop","weak","recession","crisis"]):
            score -= 1

    if score > 1:
        return "🟢 Risk-on"
    elif score < -1:
        return "🔴 Risk-off"
    else:
        return "🟡 Neutral"


def build_html_email(is_monday):
    """Crée le HTML de l'email"""
    macro = build_macro_section()
    
    # Récupérer les données
    macro_section = build_macro_section()
    
    us_indices = collect_indices("US")
    europe_indices = collect_indices("EUROPE")
    asia_indices = collect_indices("ASIE")
    crypto = get_crypto_data()
    movers = get_top_movers()

    sectors = get_sector_performance()
    themes = get_theme_performance()

    top_sectors = sectors[:3]
    bottom_sectors = sectors[-3:]

    top_themes = themes[:3]
    bottom_themes = themes[-3:]

    
    macro_section = build_macro_section()

    today = datetime.now().strftime("%A %d %B %Y").capitalize()
    us_label = "Clôture US — vendredi soir" if is_monday else "Clôture US — hier soir"
    asia_label = "Clôture Asie — ce matin" if is_monday else "Clôture Asie — cette nuit"
    
    # Générer les rangées HTML pour les indices
    def make_rows(indices):
        rows = ""
        for idx in indices:
            color = idx["color"]
            rows += f"""
            <tr>
              <td class="name">{idx["name"]}</td>
              <td class="price">{idx["price"]:.2f}</td>
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
  
  .section-title {{
    font-size: 14px;
    font-weight: 700;
    color: #1e3c72;
    margin: 0 0 15px 0;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  
  .section-sub {{
    font-size: 12px;
    color: #999;
    margin: 0 0 15px 0;
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
<div>
{{macro_section}}
</div>
  <div class="email">
    <!-- HEADER -->
    <div class="header">
      <h1><span class="logo">📊</span> Recap Marchés</h1>
      <p>{today}</p>
    </div>
    
    <!-- INDICES US -->
    <div class="section">
      <div class="section-title">🇺🇸 {us_label}</div>
      <table>
        {make_rows(us_indices)}
      </table>
    </div>
    
    <!-- INDICES ASIE -->
    <div class="section">
      <div class="section-title">🌏 {asia_label}</div>
      <table>
        {make_rows(asia_indices)}
      </table>
    </div>
    
    <!-- INDICES EUROPE -->
    <div class="section">
      <div class="section-title">🇪🇺 Ouverture Europe — ce matin</div>
      <table>
        {make_rows(europe_indices)}
      </table>
    </div>
    
    <!-- CRYPTO -->
    <div class="section">
      <div class="section-title">₿ Crypto</div>
      <table>
        {make_rows(crypto)}
      </table>
    </div>
    
    <!-- TOP MOUVEMENTS -->
    <div class="section">
      <div class="section-title">📈 Top Mouvements</div>
      <div class="movers-grid">
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
    
    
    <!-- LEADERS / RETARDATAIRES -->
    <div class="section">
      <div class="section-title">📊 Leaders & Retardataires</div>

      <div style="font-size:13px; line-height:1.6; color:#333;">

        <strong>📊 Secteurs</strong><br><br>

        🟢 Tech (+2,8%)<br>
        🟢 Industrie (+1,9%)<br>
        🟢 Finance (+1,3%)<br><br>

        🔴 Énergie (-2,1%)<br>
        🔴 Immobilier (-1,4%)<br>
        🔴 Utilities (-0,9%)<br><br>

        <strong>🎯 Thématiques</strong><br><br>

        🟢 Semi-conducteurs (+4,7%)<br>
        Nvidia • AMD • Broadcom<br><br>

        🟢 IA (+3,9%)<br>
        Microsoft • Palantir • Oracle<br><br>

        🟢 Biopharma (+2,5%)<br>
        Eli Lilly • Vertex • Moderna<br><br>

        🔴 Solaire (-3,4%)<br>
        Enphase • First Solar • SolarEdge<br><br>

        🔴 EV (-2,8%)<br>
        Tesla • Rivian • Lucid<br><br>

        🔴 Pétrole (-2,0%)<br>
        ExxonMobil • Chevron • Occidental

      </div>
    </div>


    
    <!-- DYNAMIC SECTORS & THEMES -->
    <div class="section">
      <div class="section-title">📊 Leaders & Retardataires</div>

      <div style="font-size:13px; line-height:1.6; color:#333;">

        <strong>📊 Secteurs</strong><br><br>

        🟢 {top_sectors[0]['name']} ({top_sectors[0]['change']:.2f}%)<br>
        🟢 {top_sectors[1]['name']} ({top_sectors[1]['change']:.2f}%)<br>
        🟢 {top_sectors[2]['name']} ({top_sectors[2]['change']:.2f}%)<br><br>

        🔴 {bottom_sectors[0]['name']} ({bottom_sectors[0]['change']:.2f}%)<br>
        🔴 {bottom_sectors[1]['name']} ({bottom_sectors[1]['change']:.2f}%)<br>
        🔴 {bottom_sectors[2]['name']} ({bottom_sectors[2]['change']:.2f}%)<br><br>

        <strong>🎯 Thématiques</strong><br><br>

        🟢 {top_themes[0]['theme']} ({top_themes[0]['change']:.2f}%)<br>
        🟢 {top_themes[1]['theme']} ({top_themes[1]['change']:.2f}%)<br>
        🟢 {top_themes[2]['theme']} ({top_themes[2]['change']:.2f}%)<br><br>

        🔴 {bottom_themes[0]['theme']} ({bottom_themes[0]['change']:.2f}%)<br>
        🔴 {bottom_themes[1]['theme']} ({bottom_themes[1]['change']:.2f}%)<br>
        🔴 {bottom_themes[2]['theme']} ({bottom_themes[2]['change']:.2f}%)<br>

      </div>
    </div>


    <!-- FOOTER -->
    <div class="footer">
      <p>Données : Yahoo Finance / Morningstar<br>
      Généré automatiquement chaque matin du lundi au vendredi.<br>
      <small>Les variations reflètent la dernière séance clôturée.</small></p>
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
    
    # Préparer l'email
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    
    subject = "📊 Recap du Week-end" if is_monday else "📊 Recap Marchés"
    msg["Subject"] = f"{subject} — {datetime.now().strftime('%d/%m/%Y')}"
    
    msg.attach(MIMEText(html_content, "html", "utf-8"))
    
    # Envoyer
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
    
    html = build_html_email(is_monday)
    send_email(html, is_monday)


if __name__ == "__main__":
    main()


# =========================
# MACRO NEWS (GOOGLE NEWS)
# =========================

def get_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)

    news = []
    for entry in feed.entries[:3]:
        news.append({
            "title": entry.title,
            "link": entry.link
        })
    return news


def build_macro_section():
    regions = {
        "🇺🇸 USA": "US economy inflation Fed jobs PMI",
        "🇪🇺 Europe": "Europe inflation ECB economy",
        "🇬🇧 UK": "UK economy BoE inflation",
        "🇯🇵 Japan": "Japan BoJ economy",
        "🇨🇳 China": "China PMI economy trade"
    }

    text = "📰 En bref\n\n"
    all_titles = []

    for region, query in regions.items():
        news = get_news(query)
        text += region + " :\n"

        for n in news:
            text += f"- {n['title']}\n  ({n['link']})\n"
            all_titles.append(n['title'])

        text += "\n"

    return text, all_titles


KEYWORDS = ["inflation","fed","ecb","jobs","pmi","gdp","recession","oil","war","tariff","earnings"]

def market_sentiment(titles):
    score = 0
    for t in titles:
        t = t.lower()
        if any(k in t for k in KEYWORDS):
            score += 1
        if any(k in t for k in ["fall","drop","weak","recession","crisis"]):
            score -= 1

    if score > 1:
        return "🟢 Risk-on"
    elif score < -1:
        return "🔴 Risk-off"
    else:
        return "🟡 Neutral"
