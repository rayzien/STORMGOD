"""
commands/sticker_commands.py — Sticker Collection Manager for STORM GOD
Collect stickers from any server, browse collections, and send stickers anywhere.
"""
import os
import json
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STICKER_FILE = os.path.join(BASE_DIR, "sticker_collection.json")

def load_sticker_collection():
    if os.path.exists(STICKER_FILE):
        try:
            with open(STICKER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"servers": {}}

def save_sticker_collection(data):
    try:
        with open(STICKER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[STORMGOD STICKER] Save error: {e}")


def handle_add_sticker(bot, token, channel_id, args, guild_id):
    """
    .add sticker — Fetches all custom stickers from the current server
    and saves them to the local sticker collection.
    """
    if not guild_id:
        lines = [
            "STICKER COLLECTOR ERROR",
            "──────────────────────────────────────────",
            "Error: Must be used inside a server (guild).",
            "DMs do not have custom stickers."
        ]
        return lines, "STICKER ERROR", "This command must be used inside a server (not in DMs)."

    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        # Fetch guild info for name
        guild_r = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}", headers=headers, timeout=10)
        guild_name = "Unknown Server"
        if guild_r.status_code == 200:
            guild_name = guild_r.json().get("name", "Unknown Server")
        
        # Fetch stickers
        r = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/stickers", headers=headers, timeout=10)
        if r.status_code != 200:
            lines = [
                "STICKER FETCH FAILED",
                "──────────────────────────────────────────",
                f"Server: {guild_name}",
                f"HTTP Status: {r.status_code}",
                "Could not fetch stickers from this server."
            ]
            return lines, "FETCH FAILED", f"Failed to fetch stickers from **{guild_name}** (HTTP {r.status_code})."
        
        stickers_data = r.json()
        if not stickers_data:
            lines = [
                "NO STICKERS FOUND",
                "──────────────────────────────────────────",
                f"Server: {guild_name}",
                "This server has no custom stickers."
            ]
            return lines, "NO STICKERS", f"No custom stickers found in **{guild_name}**."
        
        # Save to collection
        collection = load_sticker_collection()
        sticker_entries = []
        for s in stickers_data:
            entry = {
                "name": s.get("name", "unknown"),
                "id": s.get("id", ""),
                "description": s.get("description", ""),
                "format_type": s.get("format_type", 1),
                "url": f"https://media.discordapp.net/stickers/{s.get('id')}.png?size=160"
            }
            # Lottie stickers use webp
            if s.get("format_type") == 3:
                entry["url"] = f"https://media.discordapp.net/stickers/{s.get('id')}.json"
            elif s.get("format_type") == 2:
                entry["url"] = f"https://media.discordapp.net/stickers/{s.get('id')}.png?size=160"
            sticker_entries.append(entry)
        
        collection["servers"][guild_id] = {
            "name": guild_name,
            "stickers": sticker_entries
        }
        save_sticker_collection(collection)
        
        lines = [
            "STICKER COLLECTION UPDATED",
            "──────────────────────────────────────────",
            f"Server: {guild_name}",
            f"Stickers Added: {len(sticker_entries)}",
            "──────────────────────────────────────────",
        ]
        # List first 8 sticker names
        for i, se in enumerate(sticker_entries[:8], 1):
            lines.append(f"  {i}. {se['name']}")
        if len(sticker_entries) > 8:
            lines.append(f"  ... and {len(sticker_entries) - 8} more")
        
        text_msg = (
            f"**[ STICKER COLLECTION UPDATED ]**\n"
            f"Server: **{guild_name}**\n"
            f"Stickers Collected: **{len(sticker_entries)}**\n\n"
            f"Use `.c` to view your full collection or `.sticker <name>` to send one."
        )
        return lines, "STICKERS COLLECTED", text_msg
        
    except Exception as e:
        lines = [
            "STICKER COLLECTOR ERROR",
            "──────────────────────────────────────────",
            f"Error: {str(e)[:50]}"
        ]
        return lines, "STICKER ERROR", f"Sticker collection failed: `{e}`"


def handle_sticker_collection(bot, token, channel_id, args):
    """
    .c [server_name] — View sticker collection. 
    If server_name provided, filter to that server.
    """
    collection = load_sticker_collection()
    servers = collection.get("servers", {})
    
    if not servers:
        lines = [
            "STICKER COLLECTION EMPTY",
            "──────────────────────────────────────────",
            "No stickers collected yet.",
            "Use .add sticker in a server to start collecting."
        ]
        return lines, "EMPTY COLLECTION", "No stickers collected yet. Use `.add sticker` in a server to start."

    # Filter by server name if provided
    filter_name = " ".join(args[1:]).strip().lower() if len(args) > 1 else ""
    
    if filter_name:
        matched = {gid: data for gid, data in servers.items() if filter_name in data.get("name", "").lower()}
    else:
        matched = servers
    
    if not matched:
        lines = [
            "NO MATCHING SERVER",
            "──────────────────────────────────────────",
            f"No collection found for: '{filter_name}'",
            "Use .c to see all servers."
        ]
        return lines, "NOT FOUND", f"No sticker collection found matching `{filter_name}`. Use `.c` to see all servers."
    
    lines = [
        "STICKER COLLECTION",
        "══════════════════════════════════════════",
    ]
    text_parts = ["**[ STICKER COLLECTION ]**\n"]
    
    total_stickers = 0
    for gid, data in matched.items():
        server_name = data.get("name", "Unknown")
        stickers = data.get("stickers", [])
        total_stickers += len(stickers)
        
        lines.append(f"Server: {server_name} ({len(stickers)} stickers)")
        lines.append("──────────────────────────────────────────")
        text_parts.append(f"**{server_name}** — `{len(stickers)}` stickers")
        
        for i, s in enumerate(stickers[:6], 1):
            lines.append(f"  {i}. {s['name']}")
        if len(stickers) > 6:
            lines.append(f"  ... +{len(stickers) - 6} more")
        lines.append("")
    
    lines.append(f"Total: {total_stickers} stickers across {len(matched)} server(s)")
    text_parts.append(f"\nTotal: **{total_stickers}** stickers across **{len(matched)}** server(s)")
    text_parts.append(f"Send one with `.sticker <name>`")
    
    return lines, "STICKER COLLECTION", "\n".join(text_parts)


def handle_send_sticker(bot, token, channel_id, args):
    """
    .sticker <name> — Sends a collected sticker by name as an image URL.
    """
    if len(args) < 2:
        lines = [
            "STICKER USAGE",
            "──────────────────────────────────────────",
            "Syntax: .sticker <name>",
            "Example: .sticker pepe",
            "Use .c to see your collection."
        ]
        return lines, "STICKER USAGE", "Usage: `.sticker <name>` — Send a sticker from your collection."

    search_name = " ".join(args[1:]).strip().lower()
    collection = load_sticker_collection()
    
    # Search across all servers
    for gid, data in collection.get("servers", {}).items():
        for s in data.get("stickers", []):
            if s["name"].lower() == search_name or search_name in s["name"].lower():
                # Send the sticker URL directly
                try:
                    bot.sendMessage(channel_id, s["url"])
                except Exception:
                    pass
                return None, None, None
    
    lines = [
        "STICKER NOT FOUND",
        "──────────────────────────────────────────",
        f"No sticker matching: '{search_name}'",
        "Use .c to view your collection."
    ]
    return lines, "NOT FOUND", f"No sticker named `{search_name}` found in your collection."
