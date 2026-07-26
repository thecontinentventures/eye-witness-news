import os
import feedparser
from openai import OpenAI

# Initialize OpenAI client using environment secrets
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# News RSS Feeds
FEEDS = {
    "Nation Africa": "https://nation.africa/kenya/rss",
    "Citizen Digital": "https://citizen.digital/news/rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC News": "http://feeds.bbci.co.uk/news/rss.xml"
}

def fetch_latest_news():
    articles = []
    for source, url in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]:  # Grab top 2 stories per source
                articles.append({
                    "source": source,
                    "title": entry.title,
                    "summary": getattr(entry, 'summary', entry.title),
                    "link": entry.link
                })
        except Exception as e:
            print(f"Error reading {source}: {e}")
    return articles

def generate_ai_roundup(articles):
    prompt_content = "\n".join([f"- [{a['source']}] {a['title']}: {a['summary']}" for a in articles])
    
    prompt = f"""
    You are the chief editor for 'Eye Witness News', a modern news briefing platform.
    Below are current news snippets gathered from global and regional outlets:
    
    {prompt_content}

    Task:
    Write an engaging, 4-paragraph global news briefing for Eye Witness News.
    - Organize the coverage clearly (e.g., Regional Focus, International Affairs, Tech & Business).
    - Provide a high-level briefing that synthesizes facts across sources without line-by-line copying or plagiarizing.
    - Format output using standard HTML tags only (<h3> headers and <p> body tags).
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

def build_index_html(ai_content, raw_articles):
    sources_list_html = ""
    for a in raw_articles:
        sources_list_html += f"""
        <li>
            <strong>[{a['source']}]</strong> <a href="{a['link']}" target="_blank" rel="noopener">{a['title']}</a>
        </li>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eye Witness News | Independent Global & Regional Briefings</title>
    <!-- Google AdSense Code Placeholder -->
    <!-- <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_ADSENSE_ID" crossorigin="anonymous"></script> -->
    <style>
        :root {{
            --primary: #d32f2f;
            --dark: #121212;
            --light: #f8f9fa;
            --text: #222222;
        }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; 
            line-height: 1.6; 
            max-width: 850px; 
            margin: 0 auto; 
            padding: 0 15px;
            background: #f4f5f7; 
            color: var(--text); 
        }}
        header {{ 
            background: var(--dark);
            color: #fff;
            padding: 25px 20px; 
            margin-bottom: 25px; 
            border-bottom: 4px solid var(--primary);
            border-radius: 0 0 6px 6px;
        }}
        header h1 {{ 
            margin: 0; 
            font-size: 2.2rem; 
            letter-spacing: -0.5px;
            text-transform: uppercase;
        }}
        header h1 span {{ color: var(--primary); }}
        .tagline {{ font-size: 0.95rem; color: #ccc; margin-top: 5px; }}
        .content {{ 
            background: #fff; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
            margin-bottom: 25px; 
        }}
        .content h3 {{
            color: var(--dark);
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        .sources {{ 
            background: #fff; 
            padding: 20px 25px; 
            border-radius: 8px; 
            font-size: 0.9rem; 
            border-left: 4px solid var(--primary);
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        .sources ul {{ padding-left: 20px; }}
        .sources li {{ margin-bottom: 8px; }}
        footer {{ 
            margin-top: 40px; 
            margin-bottom: 20px;
            font-size: 0.85rem; 
            color: #666; 
            text-align: center; 
        }}
        a {{ color: #0056b3; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <header>
        <h1>Eye Witness <span>News</span></h1>
        <div class="tagline">Automated Global Insights & Regional Briefings</div>
    </header>

    <main class="content">
        {ai_content}
    </main>

    <section class="sources">
        <h3>Verified Sources & Direct Reporting</h3>
        <p>This round-up synthesizes real-time coverage from official feeds:</p>
        <ul>
            {sources_list_html}
        </ul>
    </section>

    <footer>
        <p>&copy; Eye Witness News. All Rights Reserved.</p>
        <p><a href="#">Privacy Policy</a> | <a href="#">Terms of Service</a> | <a href="#">About Us</a></p>
    </footer>
</body>
</html>
"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    print("Fetching news feeds...")
    news_items = fetch_latest_news()
    print("Generating Eye Witness News briefing via OpenAI...")
    ai_summary = generate_ai_roundup(news_items)
    print("Writing index.html...")
    build_index_html(ai_summary, news_items)
    print("Eye Witness News build complete!")
