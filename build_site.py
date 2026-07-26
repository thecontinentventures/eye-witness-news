import os
import re
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

def extract_image_url(entry):
    """Extracts main story image from various RSS enclosure/media formats."""
    # 1. Check media_content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if isinstance(media, dict) and 'url' in media:
                return media['url']
    
    # 2. Check media_thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for media in entry.media_thumbnail:
            if isinstance(media, dict) and 'url' in media:
                return media['url']

    # 3. Check enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image/'):
                return enc.get('href')

    # 4. Fallback: Parse <img> tag from entry summary/description
    summary_html = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary_html, re.IGNORECASE)
    if match:
        return match.group(1)

    # 5. Generic stock fallback if feed has no media
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"

def fetch_latest_news():
    articles = []
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
                        "link": entry.link,
                        "image": extract_image_url(entry)
                    })
            else:
                print(f"Warning: {source} returned status {response.status_code}")
        except Exception as e:
            print(f"Error fetching feed from {source}: {e}")

    # Fallback default if all feeds fail
    if not articles:
        articles.append({
            "source": "Eye Witness Desk",
            "title": "Global News Monitoring Active",
            "summary": "Tracking real-time breaking news from regional and international streams.",
            "link": "https://nation.africa",
            "image": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=800&q=80"
        })

    return articles

def generate_ai_roundup(articles):
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is missing!")
        # Generate raw HTML dynamically from fetched articles if API key is missing
        hero = articles[0]
        grid_items = articles[1:4] if len(articles) > 1 else articles
        
        grid_html = ""
        for a in grid_items:
            grid_html += f"""
            <article class="card">
                <a href="{a['link']}" target="_blank" rel="noopener" class="card-link">
                    <img src="{a['image']}" alt="Story Image" class="card-img">
                    <span class="card-tag">{a['source']}</span>
                    <h3>{a['title']}</h3>
                </a>
                <p>{a['summary'][:150]}...</p>
                <a href="{a['link']}" target="_blank" rel="noopener" class="read-more-link">Read More &rarr;</a>
            </article>
            """

        return f"""
        <div class="hero-story">
            <a href="{hero['link']}" target="_blank" rel="noopener" class="story-link">
                <img src="{hero['image']}" alt="Lead Story" class="hero-img">
                <span class="badge">TOP DEVELOPMENT</span>
                <h2>{hero['title']}</h2>
            </a>
            <p>{hero['summary']}</p>
            <div class="key-takeaway"><strong>Key Takeaway:</strong> Live update captured from {hero['source']}.</div>
            <a href="{hero['link']}" target="_blank" rel="noopener" class="read-more-btn">Read Full Article &rarr;</a>
        </div>
        <div class="grid-container">
            {grid_html}
        </div>
        """

    prompt_content = "\n".join([
        f"- Source: {a['source']}\n  Title: {a['title']}\n  Summary: {a['summary']}\n  Link: {a['link']}\n  Image: {a['image']}"
        for a in articles
    ])
    
    prompt = f"""
    You are the Chief Editor for 'Eye Witness News'.
    Below are live wire items collected today:
    {prompt_content}

    Task:
    Write a sleek, modern news briefing using standard HTML tags only.

    Structure requirement:
    1. A single lead story wrapper:
       <div class="hero-story">
           <a href="[ORIGINAL_STORY_LINK]" target="_blank" rel="noopener" class="story-link">
               <img src="[ORIGINAL_STORY_IMAGE]" alt="Lead Story" class="hero-img">
               <span class="badge">TOP DEVELOPMENT</span>
               <h2>Headline</h2>
           </a>
           <p>Overview text...</p>
           <div class="key-takeaway"><strong>Key Takeaway:</strong> Brief summary point...</div>
           <a href="[ORIGINAL_STORY_LINK]" target="_blank" rel="noopener" class="read-more-btn">Read Full Article &rarr;</a>
       </div>

    2. A grid section <div class="grid-container"> containing 3 distinct card items:
       <article class="card">
           <a href="[ARTICLE_LINK]" target="_blank" rel="noopener" class="card-link">
               <img src="[ARTICLE_IMAGE]" alt="Story Image" class="card-img">
               <span class="card-tag">CATEGORY</span>
               <h3>Title</h3>
           </a>
           <p>Brief summary paragraph...</p>
           <a href="[ARTICLE_LINK]" target="_blank" rel="noopener" class="read-more-link">Read More &rarr;</a>
       </article>

    Do not include markdown code fence formatting (no ```html). Output pure, raw HTML directly.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        # Sanitize code fence tags if LLM ignores formatting rules
        content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
        return content
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return "<p>Error generating AI briefing. Check logs.</p>"

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
            --primary: #dc2626;
            --primary-hover: #b91c1c;
            --dark: #0f172a;
            --dark-card: #1e293b;
            --gray-bg: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            background-color: var(--gray-bg);
            color: var(--text-main);
            -webkit-font-smoothing: antialiased;
        }}

        .top-bar {{
            background: var(--dark);
            color: var(--text-muted);
            font-size: 0.8rem;
            padding: 10px 0;
            border-bottom: 1px solid #334155;
        }}
        .top-bar-inner {{
            max-width: 1140px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .live-indicator {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #4ade80;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .pulse {{
            width: 8px;
            height: 8px;
            background-color: #4ade80;
            border-radius: 50%;
            display: inline-block;
            animation: pulse-ring 1.8s infinite;
        }}
        @keyframes pulse-ring {{
            0% {{ box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }}
            70% {{ box-shadow: 0 0 0 8px rgba(74, 222, 128, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }}
        }}

        header {{
            background: #ffffff;
            border-bottom: 3px solid var(--primary);
            padding: 22px 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
        }}
        .header-inner {{
            max-width: 1140px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .logo {{
            font-size: 2.2rem;
            font-weight: 900;
            letter-spacing: -1px;
            color: var(--dark);
            text-transform: uppercase;
            text-decoration: none;
        }}
        .logo span {{ color: var(--primary); }}
        .tagline {{ font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }}

        .container {{
            max-width: 1140px;
            margin: 30px auto;
            padding: 0 20px;
        }}

        .hero-story {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 35px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
            position: relative;
            overflow: hidden;
        }}
        .hero-img {{
            width: 100%;
            max-height: 400px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .story-link {{
            text-decoration: none;
            color: inherit;
            display: block;
        }}
        .story-link:hover h2 {{ color: var(--primary); }}
        .badge {{
            background: var(--primary);
            color: #ffffff;
            font-size: 0.7rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 12px;
        }}
        .hero-story h2 {{
            font-size: 1.9rem;
            color: var(--dark);
            margin-bottom: 15px;
            line-height: 1.3;
            letter-spacing: -0.5px;
            transition: color 0.2s ease;
        }}
        .hero-story p {{
            font-size: 1.05rem;
            color: var(--text-main);
            margin-bottom: 20px;
        }}
        .key-takeaway {{
            background: #f1f5f9;
            border-left: 4px solid var(--primary);
            padding: 12px 16px;
            border-radius: 0 6px 6px 0;
            font-size: 0.95rem;
            color: #334155;
            margin-bottom: 20px;
        }}
        .read-more-btn {{
            display: inline-block;
            background: var(--dark);
            color: #ffffff;
            padding: 10px 18px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: background 0.2s ease;
        }}
        .read-more-btn:hover {{ background: var(--primary); }}

        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
            margin-bottom: 35px;
        }}
        .card {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            display: flex;
            flex-direction: column;
        }}
        .card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.08);
        }}
        .card-img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .card-link {{ text-decoration: none; color: inherit; }}
        .card-link:hover h3 {{ color: var(--primary); }}
        .card-tag {{
            font-size: 0.7rem;
            font-weight: 700;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            display: block;
        }}
        .card h3 {{
            font-size: 1.25rem;
            color: var(--dark);
            margin-bottom: 12px;
            line-height: 1.35;
            transition: color 0.2s ease;
        }}
        .card p {{
            font-size: 0.95rem;
            color: var(--text-muted);
            margin-bottom: 15px;
            flex-grow: 1;
        }}
        .read-more-link {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 700;
            font-size: 0.88rem;
        }}
        .read-more-link:hover {{ text-decoration: underline; }}

        .sources-section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            border: 1px solid var(--border);
        }}
        .sources-section h3 {{
            font-size: 1.2rem;
            color: var(--dark);
            margin-bottom: 6px;
        }}
        .source-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 12px;
            margin-top: 15px;
        }}
        .source-chip {{
            background: var(--gray-bg);
            padding: 12px 14px;
            border-radius: 8px;
            border: 1px solid var(--border);
            font-size: 0.85rem;
        }}
        .source-badge {{
            background: var(--dark);
            color: #ffffff;
            font-size: 0.65rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 800;
            display: inline-block;
            margin-bottom: 6px;
            text-transform: uppercase;
        }}
        .source-chip a {{
            color: var(--text-main);
            text-decoration: none;
            font-weight: 600;
            display: block;
            line-height: 1.3;
        }}
        .source-chip a:hover {{ color: var(--primary); }}

        footer {{
            background: var(--dark);
            color: var(--text-muted);
            padding: 35px 20px;
            margin-top: 60px;
            text-align: center;
            font-size: 0.85rem;
        }}
        footer a {{ color: #94a3b8; text-decoration: none; margin: 0 8px; }}
        footer a:hover {{ color: #ffffff; }}

        @media (max-width: 768px) {{
            .hero-story {{ padding: 25px; }}
            .hero-story h2 {{ font-size: 1.5rem; }}
            .logo {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>

    <div class="top-bar">
        <div class="top-bar-inner">
            <div class="live-indicator">
                <span class="pulse"></span> LIVE MONITORING
            </div>
            <div>Updated: {current_date}</div>
        </div>
    </div>

    <header>
        <div class="header-inner">
            <div>
                <a href="#" class="logo">Eye Witness <span>News</span></a>
                <div class="tagline">Automated Global Insights & Regional Intel Desk</div>
            </div>
        </div>
    </header>

    <div class="container">
        <main>
            {ai_content}
        </main>

        <section class="sources-section">
            <h3>Verified Wire Feeds</h3>
            <p style="font-size: 0.85rem; color: var(--text-muted);">Real-time sources captured during this briefing cycle:</p>
            <div class="source-grid">
                {sources_list_html}
            </div>
        </section>
    </div>

    <footer>
        <p>&copy; {datetime.datetime.now().year} Eye Witness News. All rights reserved.</p>
    </footer>

</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    print("Fetching live RSS feeds...")
    news_items = fetch_latest_news()
    print(f"Successfully retrieved {len(news_items)} wire stories.")
    print("Generating Eye Witness News briefing...")
    ai_summary = generate_ai_roundup(news_items)
    print("Compiling landing page index.html...")
    build_index_html(ai_summary, news_items)
    print("Eye Witness News build completed successfully!")
