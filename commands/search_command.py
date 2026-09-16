"""
commands/search_command.py — Real-Time Web Search Engine Command with In-Message Button Scrolling
"""
import os
import math
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup

# In-memory search cache to make pagination instant
# Key: query_lower -> (timestamp, list_of_results)
SEARCH_CACHE = {}
CACHE_TTL = 300  # 5 minutes cache lifetime

def perform_web_search(query):
    """
    Performs real-time web search across search engine endpoints.
    Returns list of dicts: [{'title': str, 'link': str, 'snippet': str}]
    """
    query_clean = query.strip().lower()
    
    # Return cached results if available and fresh
    now = time.time()
    if query_clean in SEARCH_CACHE:
        cache_time, cached_results = SEARCH_CACHE[query_clean]
        if now - cache_time < CACHE_TTL:
            return cached_results

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    results = []

    # 1. Primary Engine: DuckDuckGo Lite (Real-time live web search)
    try:
        url = "https://lite.duckduckgo.com/lite/"
        resp = requests.post(url, data={"q": query}, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            trs = soup.find_all('tr')
            i = 0
            while i < len(trs):
                tr = trs[i]
                a = tr.find('a', class_='result-link')
                if a:
                    title = a.get_text(strip=True)
                    link = a.get('href', '')
                    snippet = ''
                    if i + 1 < len(trs):
                        td_snip = trs[i+1].find('td', class_='result-snippet')
                        if td_snip:
                            snippet = td_snip.get_text(strip=True)
                    if link and not link.startswith('https://duckduckgo.com/y.js'):
                        results.append({'title': title, 'link': link, 'snippet': snippet})
                i += 1
    except Exception as e:
        print(f"[SEARCH ENGINE] DDG Lite error: {e}")

    # 2. Fallback Engine: Google HTML Search
    if not results:
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for g in soup.find_all('div', class_='g'):
                    anchors = g.find_all('a')
                    h3 = g.find('h3')
                    if anchors and h3:
                        title = h3.get_text(strip=True)
                        link = anchors[0].get('href', '')
                        snip_div = g.find('div', class_='VwiC3b') or g.find('div', class_='st')
                        snippet = snip_div.get_text(strip=True) if snip_div else ''
                        if link.startswith('http'):
                            results.append({'title': title, 'link': link, 'snippet': snippet})
        except Exception as e:
            print(f"[SEARCH ENGINE] Google fallback error: {e}")

    # Cache non-empty search results
    if results:
        SEARCH_CACHE[query_clean] = (now, results)

    return results


def handle_search(bot, token, channel_id, args, state):
    """
    Real-time web search engine command with in-message scrolling/pagination buttons.

    Usage:
      .search python tutorial       -> Search live web (Page 1)
      .search python tutorial 2     -> Search live web (Page 2)
      .google elon musk             -> Alias using .google
      .find docker setup            -> Alias using .find
    """
    prefix = state.get("prefix", ".")
    
    query = ""
    page = 1

    if len(args) > 1:
        if len(args) > 2 and args[-1].isdigit():
            try:
                page = int(args[-1])
                query = " ".join(args[1:-1]).strip()
            except ValueError:
                query = " ".join(args[1:]).strip()
                page = 1
        elif len(args) == 2 and args[1].isdigit():
            page = int(args[1])
            query = ""
        else:
            query = " ".join(args[1:]).strip()
            page = 1

    # Guidance screen if no query provided
    if not query:
        lines = [
            "REAL-TIME WEB SEARCH ENGINE",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}search <query> [page]",
            "Examples:",
            f"  {prefix}search python tutorial",
            f"  {prefix}search how to install docker",
            f"  {prefix}search elon musk 2",
            f"  {prefix}google discord selfbot",
            "──────────────────────────────────────────",
            "Features: Real-Time Live Web Search + In-Msg Buttons"
        ]
        text_msg = (
            f"**[ REAL-TIME WEB SEARCH ENGINE ]**\n"
            f"Search the live web directly inside Discord text messages.\n\n"
            f"**Usage Examples:**\n"
            f"- `{prefix}search python tutorial` — Search live web for Python tutorials\n"
            f"- `{prefix}search how to install docker 2` — Search and turn to Page 2\n"
            f"- `{prefix}google elon musk` — Use `.google` or `.search` alias"
        )
        return lines, "WEB SEARCH ENGINE GUIDE", text_msg

    # Perform real-time live web search
    results = perform_web_search(query)
    
    total_results = len(results)
    per_page = 3  # 3 web search results per page for clean Discord rendering
    total_pages = max(1, math.ceil(total_results / per_page))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_items = results[start_idx:end_idx]

    # Glass Card Image lines
    lines = [
        f"Search: \"{query[:30]}\" | Web Results: {total_results}",
        f"Page: {page}/{total_pages} | Real-Time Web Engine Active",
        "──────────────────────────────────────────"
    ]

    if not page_items:
        lines.append(f"No web results found for query: '{query}'")
        lines.append("Try refining your search terms.")
    else:
        for idx, item in enumerate(page_items, start=start_idx + 1):
            title = item['title'][:45]
            link = item['link'][:45]
            lines.append(f"{idx}. {title}")
            lines.append(f"   Link: {link}")

    lines.append("──────────────────────────────────────────")
    lines.append(f"Nav: {prefix}search {query} <page>")

    # Build Interactive Discord Action Row Button Components for In-Message Scrolling
    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)
    query_slug = re.sub(r'[^a-zA-Z0-9_]', '_', query)[:15]

    components = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "style": 2,
                    "label": "◀ Prev",
                    "custom_id": f"search_{query_slug}_{prev_page}",
                    "disabled": page == 1
                },
                {
                    "type": 2,
                    "style": 1,
                    "label": f"Page {page}/{total_pages}",
                    "custom_id": f"search_{query_slug}_{page}"
                },
                {
                    "type": 2,
                    "style": 2,
                    "label": "Next ▶",
                    "custom_id": f"search_{query_slug}_{next_page}",
                    "disabled": page == total_pages
                },
                {
                    "type": 2,
                    "style": 3,
                    "label": "Refresh 🔄",
                    "custom_id": f"search_{query_slug}_{page}"
                }
            ]
        }
    ]

    card_title = f"WEB SEARCH: \"{query[:20].upper()}\" ({page}/{total_pages})"

    # Formatted Markdown Text Output
    text_lines = [
        f"🌐 **[ REAL-TIME WEB SEARCH — \"{query}\" ]**",
        f"Found **{total_results}** web results. Showing Page **{page}/{total_pages}**:\n"
    ]

    if not page_items:
        text_lines.append(f"No web results found for `{query}`.")
    else:
        for idx, item in enumerate(page_items, start=start_idx + 1):
            t = item['title']
            l = item['link']
            s = item['snippet'] if item['snippet'] else "No snippet preview available."
            text_lines.append(f"**{idx}. [{t}]({l})**")
            text_lines.append(f"> {s}")
            text_lines.append(f"🔗 `{l}`\n")

    text_lines.append(f"Use buttons below or type `{prefix}search {query} <page>` to turn pages.")
    text_msg = "\n".join(text_lines)

    return lines, card_title, text_msg, components
