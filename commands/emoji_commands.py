"""
commands/emoji_commands.py — Emoji Manager for STORM GOD (No-Nitro Emoji Support)
Type an emoji name and it sends the emoji as an image URL — works without Nitro.
"""
import requests

# In-memory emoji cache: guild_id -> [{name, id, animated, url}]
EMOJI_CACHE = {}

def _fetch_guild_emojis(token, guild_id):
    """Fetch all custom emojis from a guild via Discord API."""
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/emojis", headers=headers, timeout=10)
        if r.status_code == 200:
            emojis = []
            for e in r.json():
                ext = "gif" if e.get("animated") else "png"
                emojis.append({
                    "name": e.get("name", ""),
                    "id": e.get("id", ""),
                    "animated": e.get("animated", False),
                    "url": f"https://cdn.discordapp.com/emojis/{e.get('id')}.{ext}?size=96",
                    "guild_id": guild_id
                })
            return emojis
    except Exception:
        pass
    return []

def _get_user_guilds(token):
    """Fetch all guilds the user is in."""
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get("https://discord.com/api/v9/users/@me/guilds", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def _build_full_cache(token):
    """Build/refresh the full emoji cache across all guilds."""
    global EMOJI_CACHE
    guilds = _get_user_guilds(token)
    for g in guilds:
        gid = g.get("id")
        if gid and gid not in EMOJI_CACHE:
            EMOJI_CACHE[gid] = _fetch_guild_emojis(token, gid)

def _search_all_emojis(token, query):
    """Search for an emoji by name across all cached guilds."""
    _build_full_cache(token)
    query_lower = query.lower()
    
    # Exact match first
    for gid, emojis in EMOJI_CACHE.items():
        for e in emojis:
            if e["name"].lower() == query_lower:
                return e
    
    # Partial match
    for gid, emojis in EMOJI_CACHE.items():
        for e in emojis:
            if query_lower in e["name"].lower():
                return e
    
    return None


def handle_emoji_send(bot, token, channel_id, args, guild_id=None):
    """
    .e <emoji_name> or .e <number> — Find and send a custom emoji as image URL (no Nitro needed).
    """
    if len(args) < 2:
        lines = [
            "EMOJI MANAGER",
            "──────────────────────────────────────────",
            "Syntax: .e <emoji_name> OR .e <number>",
            "Example: .e pepe | .e 5",
            "Lists: .efind (current server) | .elist | .esearch <query>"
        ]
        return lines, "EMOJI USAGE", "Usage: `.e <emoji_name>` or `.e <number>` — Send any custom emoji without Nitro."

    query = " ".join(args[1:]).strip()
    
    # Check if user passed a number for the current server
    if query.isdigit() and guild_id:
        idx = int(query)
        if guild_id not in EMOJI_CACHE:
            EMOJI_CACHE[guild_id] = _fetch_guild_emojis(token, guild_id)
        
        emojis = EMOJI_CACHE.get(guild_id, [])
        if 1 <= idx <= len(emojis):
            emoji = emojis[idx - 1]
            try:
                bot.sendMessage(channel_id, emoji["url"])
            except Exception:
                pass
            return None, None, None

    emoji = _search_all_emojis(token, query)
    
    if emoji:
        try:
            bot.sendMessage(channel_id, emoji["url"])
        except Exception:
            pass
        return None, None, None
    else:
        lines = [
            "EMOJI NOT FOUND",
            "──────────────────────────────────────────",
            f"No emoji matching: '{query}'",
            "Try .efind to see server emojis, .esearch <name> or .elist"
        ]
        return lines, "EMOJI NOT FOUND", f"No emoji matching `{query}` found. Try `.efind` for current server list."

def handle_emoji_find(bot, token, channel_id, args, guild_id):
    """
    .efind [number] — Show emojis from current server, depicted with indices, or send by index.
    """
    if not guild_id:
        return ["ERROR", "──────────────────────────────────────────", "You can only use .efind in a server."], "ERROR", "You must be in a server to use this command."

    if guild_id not in EMOJI_CACHE:
        EMOJI_CACHE[guild_id] = _fetch_guild_emojis(token, guild_id)
    
    emojis = EMOJI_CACHE.get(guild_id, [])
    
    if not emojis:
        return ["NO EMOJIS", "──────────────────────────────────────────", "This server has no custom emojis."], "NO EMOJIS", "This server has no custom emojis."

    # If the user passed a number, act like .e <number>
    if len(args) > 1 and args[1].isdigit():
        return handle_emoji_send(bot, token, channel_id, args, guild_id)
        
    lines = [
        f"SERVER EMOJIS  —  Total: {len(emojis)}",
        "══════════════════════════════════════════",
    ]
    
    text_parts = [f"**[ CURRENT SERVER EMOJIS — {len(emojis)} total ]**\n"]
    
    # We list them all, maybe grouped if there are many, but Discord limits to 50 normal + 50 animated, max 100-250 usually.
    # Text output will fit in a single embed easily if formatted well.
    for i, e in enumerate(emojis, start=1):
        anim_tag = " [GIF]" if e["animated"] else ""
        lines.append(f"  {i}. :{e['name']}:{anim_tag}")
        text_parts.append(f"`{i}.` **:{e['name']}:**{anim_tag}")
    
    lines.append("──────────────────────────────────────────")
    lines.append("Usage: .e <number> or .efind <number> to send")
    text_parts.append("\n*Usage: `.e <number>` or `.efind <number>` to send an emoji!*")
    
    # If the text is too long for one embed field, it will get truncated, but for 50-100 emojis it's usually fine.
    # If it's over 4000 chars, it might error, so we truncate just in case.
    full_text = "\n".join(text_parts)
    if len(full_text) > 4000:
        full_text = full_text[:3900] + "\n... (List truncated. Search by name instead!)"
        
    return lines, "SERVER EMOJIS", full_text


def handle_emoji_list(bot, token, channel_id, args):
    """
    .elist [page] — List all available custom emojis across all joined servers.
    """
    _build_full_cache(token)
    
    all_emojis = []
    guild_names = {}
    
    # Get guild names
    guilds = _get_user_guilds(token)
    for g in guilds:
        guild_names[g.get("id")] = g.get("name", "Unknown")
    
    for gid, emojis in EMOJI_CACHE.items():
        for e in emojis:
            e["server_name"] = guild_names.get(gid, "Unknown")
            all_emojis.append(e)
    
    if not all_emojis:
        lines = [
            "NO CUSTOM EMOJIS FOUND",
            "──────────────────────────────────────────",
            "No custom emojis available across your servers."
        ]
        return lines, "NO EMOJIS", "No custom emojis found across any of your joined servers."

    # Pagination
    page = 1
    if len(args) > 1 and args[1].isdigit():
        page = max(1, int(args[1]))
    
    per_page = 15
    total_pages = max(1, (len(all_emojis) + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    end = start + per_page
    page_emojis = all_emojis[start:end]
    
    lines = [
        f"EMOJI LIBRARY  —  PAGE {page}/{total_pages}",
        f"Total: {len(all_emojis)} emojis across {len(EMOJI_CACHE)} servers",
        "══════════════════════════════════════════",
    ]
    
    text_parts = [f"**[ EMOJI LIBRARY — Page {page}/{total_pages} ]**\n"]
    
    for i, e in enumerate(page_emojis, start + 1):
        anim_tag = " [GIF]" if e["animated"] else ""
        lines.append(f"  {i}. :{e['name']}:{anim_tag} — {e.get('server_name', '?')}")
        text_parts.append(f"`{i}.` **:{e['name']}:**{anim_tag} — *{e.get('server_name', '?')}*")
    
    lines.append("──────────────────────────────────────────")
    lines.append(f"Page {page}/{total_pages} | .elist {page+1} for next")
    text_parts.append(f"\nPage {page}/{total_pages} | `.elist {page+1}` for next | `.e <name>` to send")
    
    return lines, "EMOJI LIBRARY", "\n".join(text_parts)


def handle_emoji_search(bot, token, channel_id, args):
    """
    .esearch <query> — Fuzzy search for emojis by name fragment.
    """
    if len(args) < 2:
        lines = [
            "EMOJI SEARCH USAGE",
            "──────────────────────────────────────────",
            "Syntax: .esearch <partial_name>",
            "Example: .esearch pep"
        ]
        return lines, "SEARCH USAGE", "Usage: `.esearch <partial_name>` — Search for emojis by name."

    query = " ".join(args[1:]).strip().lower()
    _build_full_cache(token)
    
    # Get guild names
    guilds = _get_user_guilds(token)
    guild_names = {g.get("id"): g.get("name", "Unknown") for g in guilds}
    
    results = []
    for gid, emojis in EMOJI_CACHE.items():
        for e in emojis:
            if query in e["name"].lower():
                e["server_name"] = guild_names.get(gid, "Unknown")
                results.append(e)
    
    if not results:
        lines = [
            "NO RESULTS",
            "──────────────────────────────────────────",
            f"No emojis matching: '{query}'",
        ]
        return lines, "SEARCH EMPTY", f"No emojis matching `{query}` found."
    
    lines = [
        f"EMOJI SEARCH: '{query}'  ({len(results)} results)",
        "══════════════════════════════════════════",
    ]
    text_parts = [f"**[ EMOJI SEARCH: '{query}' — {len(results)} results ]**\n"]
    
    for i, e in enumerate(results[:15], 1):
        anim_tag = " [GIF]" if e["animated"] else ""
        lines.append(f"  {i}. :{e['name']}:{anim_tag} — {e.get('server_name', '?')}")
        text_parts.append(f"`{i}.` **:{e['name']}:**{anim_tag} — *{e.get('server_name', '?')}*")
    
    if len(results) > 15:
        lines.append(f"  ... +{len(results) - 15} more results")
    
    text_parts.append(f"\nUse `.e <name>` to send any emoji.")
    
    return lines, "EMOJI SEARCH", "\n".join(text_parts)
