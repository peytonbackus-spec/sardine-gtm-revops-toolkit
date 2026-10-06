import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

vault = os.path.expanduser("~/GTM 2nd Brain")
research_dir = os.path.join(vault, "30_Resources/Research")
os.makedirs(research_dir, exist_ok=True)

date_str = datetime.now().strftime("%Y-%m-%d")
file_path = os.path.join(research_dir, f"GTM_Research_{date_str}.md")

# Add or remove RSS Feeds here
FEEDS = {
    "Sales Hacker": "https://www.saleshacker.com/feed/",
    "OpenView Insights": "https://openviewpartners.com/feed/",
    "SaaStr": "https://www.saastr.com/feed/",
    "HubSpot Marketing Blog": "https://blog.hubspot.com/marketing/rss.xml",
    "TechCrunch Enterprise": "https://techcrunch.com/category/enterprise/feed/"
}

def fetch_feed_items(url, max_items=3):
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            root = ET.fromstring(response.read())
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item")[:max_items]:
                    title = item.findtext("title", "No Title").strip()
                    link = item.findtext("link", "").strip()
                    items.append({"title": title, "link": link})
    except Exception as e:
        items.append({"title": f"Feed currently unavailable: {str(e)}", "link": ""})
    return items

feed_sections = []
for name, url in FEEDS.items():
    articles = fetch_feed_items(url)
    sec = f"### {name}\n"
    for a in articles:
        title = a["title"]
        link = a["link"]
        if link:
            sec += f"- [{title}]({link})\n"
        else:
            sec += f"- {title}\n"
    feed_sections.append(sec)

all_feeds = "\n".join(feed_sections)
now_str = datetime.now().strftime("%H:%M:%S EDT")

content = f"""---
type: resource
category: research
tags:
  - gtm
  - revops
  - research
date: {date_str}
status: automated
---

# GTM & RevOps Automated Intelligence Digest - {date_str}

## Live RSS Feed Ingestion

{all_feeds}

## Strategic Takeaways
* Live RSS ingestion active for expanded RevOps feeds.
* Last updated at {now_str}.
"""

with open(file_path, "w") as f:
    f.write(content)

print(f"Updated gtm_researcher.py and regenerated {file_path}")
