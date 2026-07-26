import os
import datetime
import feedparser
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# RSS Feeds
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
            for entry in feed.entries[:2]:
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
    You are the Senior Editor for 'Eye Witness News'. 
    Below are top news items collected today:
    {prompt_content}

    Task:
    Write a sleek, modern news briefing formatted into standard HTML tags only.
    Structure requirement:
    1. A single primary <div class="hero-story"> featuring an <h2> headline, a <p> summary, and a <div> highlighting the main takeaway.
    2. A <div class="grid-container"> containing 3 distinct <article class="card"> blocks for secondary developments (Regional, International, Tech/Biz). Each card needs an <h3> header and a <p> brief summary.

    Keep the tone factual, fast-paced, and engaging. Do not include markdown code block formatting like ```html.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

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

    <!-- Google AdSense Placeholder (Replace ca-pub-YOUR_ADSENSE_ID once approved) -->
    <!-- <script async src="[https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_ADSENSE_ID](https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_ADSENSE_ID)" crossorigin="anonymous"></script> -->

    <style>
        :root {{
            --primary: #d32f2f;
            --primary-dark: #b71c1c;
            --dark: #0f172a;
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
        }}

        /* Header & Navigation */
        .top-bar {{
            background: var(--dark);
            color: var(--text-muted);
            font-size: 0.8rem;
            padding: 8px 0;
            border-bottom: 1px solid #1e293b;
        }}
        .top-bar-inner {{
            max-width: 1100px;
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
            font-weight: 600;
        }}
        .pulse {{
            width: 8px;
            height: 8px;
            background-color: #4ade80;
            border-radius: 50%;
            animation: pulse-animation 1.5s infinite;
        }}
        @keyframes pulse-animation {{
            0% {{ box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }}
            70% {{ box-shadow: 0 0 0 8px rgba(74, 222, 128, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }}
        }}

        header {{
            background: #ffffff;
            border-bottom: 3px solid var(--primary);
            padding: 25px 0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .header-inner {{
            max-width: 1100px;
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
        .tagline {{ font-size: 0.85rem; color: var(--text-muted); font-weight: 500; margin-top: -4px; }}

        /* Main Container */
        .container {{
            max-width: 1100px;
            margin: 30px auto;
            padding: 0 20px;
        }}

        /* Hero Story Card */
        .hero-story {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 35px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
            position: relative;
            overflow: hidden;
        }}
        .hero-story::before {{
            content: "FEATURED BRIEFING";
            position: absolute;
            top: 0;
            left: 0;
            background: var(--primary);
            color: #fff;
            font-size: 0.7rem;
            font-weight: 800;
            padding: 4px 12px;
            border-bottom-right-radius: 8px;
            letter-spacing: 1px;
        }}
        .hero-story h2 {{
            font-size: 1.8rem;
            color: var(--dark);
            margin-top: 10px;
            margin-bottom: 15px;
            line-height: 1.3;
        }}
        .hero-story p {{ font-size: 1.05rem; color: var(--text-main); margin-bottom: 15px; }}

        /* Ad Banners Placeholder */
        .ad-banner {{
            background: #e2e8f0;
            border: 1px dashed #94a3b8;
            border-radius: 8px;
            text-align: center;
            padding: 15px;
            margin: 25px 0;
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 600;
        }}

        /* Card Grid Layout */
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 35px;
        }}
        .card {{
            background: var(--card-bg);
            padding: 25px;
            border-radius: 10px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.08);
        }}
