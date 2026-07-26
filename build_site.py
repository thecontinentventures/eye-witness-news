import os
import datetime
import requests
import feedparser
from openai import OpenAI

# Initialize OpenAI client safely
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

FEEDS = {
    "Nation Africa": "https://nation.africa/kenya/rss",
    "Citizen Digital": "https://citizen.digital/news/rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml"
}

def fetch_latest_news():
    articles = []
    # Browser User-Agent header to avoid HTTP 403 blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for source, url in FEEDS.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                for entry in feed.entries[:2]:
                    articles.append({
                        "source": source,
                        "title": entry.title,
                        "summary": getattr(entry, 'summary', entry.title),
                        "link": entry.link
                    })
            else:
                print(f"Warning: {source} returned HTTP status {response.status_code}")
        except Exception as e:
            print(f"Error fetching feed from {source}: {e}")

    # Fallback if feeds fail
    if not articles:
        articles.append({
            "source": "Eye Witness Desk",
            "title": "Global News Monitoring Active",
            "summary": "Tracking breaking news from regional and international outlets.",
            "link": "https://nation.africa"
        })

    return articles

def generate_ai_roundup(articles):
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is missing!")
        return "<div class='hero-story'><h2>News Briefing Unavailable</h2><p>Please configure OPENAI_API_KEY in GitHub Repository Secrets.</p></div>"

    prompt_content = "\n".join([f"- [{a['source']}] {a['title']}: {a['summary']}" for a in articles])
    
    prompt = f"""
    You are the Senior Editor for 'Eye Witness News'.
    Below are top news items collected today:
    {prompt_content}

    Task:
    Write a sleek, modern news briefing formatted into standard HTML tags only.
    Structure requirement:
    1. A single primary <div class="hero-story"> featuring an <h2> headline, a <p> summary, and a brief status note.
    2. A <div class="grid-container"> containing 3 distinct <article class="card"> blocks for secondary developments (Regional, International, Tech/Biz). Each card needs an <h3> header and a <p> brief summary.

    Do not wrap output in markdown syntax (no ```html). Output clean HTML directly.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return """
        <div class="hero-story">
            <h2>Eye Witness Live Dispatch</h2>
            <p>Our automated systems are aggregating regional and global news streams. Full briefing updating shortly.</p>
        </div>
        """

def build_index_html(ai_content, raw_articles):
    current_date = datetime.datetime.now(datetime.timezone.utc).strftime("%B %d, %Y • %H:%M UTC")

    sources_list_html = ""
    for a in raw_articles:
        sources_list_html += f"""
        <div class="source-chip">
            <span class="source-badge">{a['source']}</span>
            <a href="{a['link']}" target="_blank" rel="noopener">{a['title']}</a>
        </div>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eye Witness News | Real-Time Global & Regional Intel</title>
    <style>
        :root {{
            --primary: #d32f2f;
            --dark: #0f172a;
            --gray-bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; background-color: var(--gray-bg); color: var(--text-main); }}
        .top-bar {{ background: var(--dark); color: var(--text-muted); font-size: 0.8rem; padding: 8px 0; }}
        .top-bar-inner {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }}
        .pulse {{ width: 8px; height: 8px; background-color: #4ade80; border-radius: 50%; display: inline-block; margin-right: 5px; }}
        header {{ background: #ffffff; border-bottom: 3px solid var(--primary); padding: 25px 0; }}
        .header-inner {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; }}
        .logo {{ font-size: 2.2rem; font-weight: 900; color: var(--dark); text-transform: uppercase; text-decoration: none; }}
        .logo span {{ color: var(--primary); }}
        .container {{ max-width: 1100px; margin: 30px auto; padding: 0 20px; }}
        .hero-story {{ background: var(--card-bg); border-radius: 12px; padding: 35px; margin-bottom: 30px; border: 1px solid var(--border); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); }}
        .hero-story h2 {{ font-size: 1.8rem; color: var(--dark); margin-bottom: 15px; }}
        .grid-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 35px; }}
        .card {{ background: var(--card-bg); padding: 25px; border-radius: 10px; border: 1px solid var(--border); }}
        .sources-section {{ background: var(--card-bg); border-radius: 12px; padding: 30px; border: 1px solid var(--border); }}
        .source-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin-top: 15px; }}
        .source-chip {{ background: var(--gray-bg); padding: 12px; border-radius: 8px; border: 1px solid var(--border); font-size: 0.85rem; }}
        .source-badge {{ background: var(--dark); color: #fff; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; display: inline-block; margin-bottom: 4px; }}
        footer {{ background: var(--dark); color: var(--text-muted); padding: 30px 20px; margin-top: 50px; text-align: center; font-size: 0.85rem; }}
        footer a {{ color: #94a3b8; text-decoration: none; margin: 0 8px; }}
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="top-bar-inner">
            <div><span class="pulse"></span> LIVE INTEL</div>
            <div>Updated: {current_date}</div>
        </div>
    </div>
    <header>
        <div class="header-inner">
            <a href="#" class="logo">Eye Witness <span>News</span></a>
            <div style="font-size:0.85rem; color: var(--text-muted);">Automated Global & Regional Coverage</div>
        </div>
    </header>
    <div class="container">
        <main>{ai_content}</main>
        <section class="sources-section">
            <h3>Verified Wire Feeds</h3>
            <div class="source-grid">{sources_list_html}</div>
        </section>
    </div>
    <footer>
        <p>&copy; {datetime.datetime.now().year} Eye Witness News. All rights reserved.</p>
        <p><a href="#">Privacy Policy</a> | <a href="#">Terms of Service</a></p>
    </footer>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    print("Fetching live feeds...")
    news_items = fetch_latest_news()
    print(f"Retrieved {len(news_items)} stories.")
    print("Generating AI briefing...")
    ai_summary = generate_ai_roundup(news_items)
    print("Building landing page...")
    build_index_html(ai_summary, news_items)
    print("Eye Witness News build successful!")
