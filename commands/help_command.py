"""
help_command.py — Full Help System for STORM GOD
Renders premium help image with ALL commands and interactive navigation buttons.
"""

COMMANDS_DOC = {
    "core": {
        "title": "CORE MODULES",
        "tag": "[CORE]",
        "icon": "◈",
        "description": "Essential system utilities & channel controls",
        "commands": {
            "help": ("Display command list, submenus, or detailed usage.", ".help [category | command]"),
            "ping": ("Check node connection latency and gateway health.", ".ping"),
            "status": ("View STORM GOD engine status and credits.", ".status"),
            "history": ("View paginated event history log entries.", ".history [page]"),
            "allow": ("Enable bot listening and commands in a channel.", ".allow [channel_id]"),
            "block": ("Disable bot listening and commands in a channel.", ".block [channel_id]"),
            "purge": ("Delete sent messages in channel or across servers.", ".purge [count | all]"),
            "prefix": ("Change system command prefix.", ".prefix [char]"),
            "say": ("Send a custom message to the current channel.", ".say [text]"),
            "cid": ("Display the current channel ID.", ".cid"),
            "uid": ("Get user ID of yourself or a mentioned user.", ".uid [@user]")
        }
    },
    "farm": {
        "title": "AUTOMATION MODULES",
        "tag": "[AUTO]",
        "icon": "⚡",
        "description": "Automation & failsafe controls",
        "commands": {
            "dark": ("Toggle STORM GOD automation engine (ON/OFF).", ".dark"),
            "cooldown": ("Display active rate-limit & cooldown status.", ".cooldown"),
            "stop": ("Emergency halt automation engine.", ".stop")
        }
    },
    "prompts": {
        "title": "PROMPT MODULES",
        "tag": "[PROMPTS]",
        "icon": "❓",
        "description": "Interactive confirmation prompts",
        "commands": {
            "yes / accept": ("Confirm active system verification prompt.", ".yes OR .accept"),
            "no / disagree": ("Cancel active prompt.", ".no OR .disagree")
        }
    },
    "premium": {
        "title": "PREMIUM MODULES",
        "tag": "[PREMIUM]",
        "icon": "★",
        "description": "Exclusive upgrades & enterprise capabilities",
        "commands": {
            "premium": ("List all available premium features and license info.", ".premium")
        }
    },
    "music": {
        "title": "YT-DLP MUSIC SYSTEM",
        "tag": "[MUSIC]",
        "icon": "♫",
        "description": "YouTube music search, player & voice channel stream controls",
        "commands": {
            "msearch": ("Search YouTube music tracks via yt-dlp.", ".msearch <song / artist>"),
            "mselect": ("Select and queue a track from search results.", ".mselect <track_number>"),
            "mplay / play": ("Extract and queue YouTube audio track.", ".mplay <song name or URL>"),
            "vcmusic": ("Extract direct voice channel audio stream.", ".vcmusic <song name or URL>"),
            "vcvideo": ("Inspect voice video stream codecs & resolutions.", ".vcvideo <query or URL>"),
            "mquality": ("View or change audio extraction quality.", ".mquality [best|high|medium|low]"),
            "minfo": ("Inspect track technical specs & codecs.", ".minfo <song name or URL>"),
            "mqueue": ("Display active playlist and queued tracks.", ".mqueue"),
            "mstop": ("Halt music engine and clear channel queue.", ".mstop"),
            "skip": ("Skip currently playing track.", ".skip")
        }
    },
    "utility": {
        "title": "UTILITY & AUTOMATION",
        "tag": "[UTILITY]",
        "icon": "⚙",
        "description": "AFK auto-responder, snipe, keyword auto-reply & donation portal",
        "commands": {
            "afk": ("Toggle AFK mode or set away message.", ".afk [on <msg> | off | status]"),
            "snipe": ("Retrieve the last deleted message in current channel.", ".snipe [index]"),
            "autoreply": ("Manage keyword auto-responder triggers.", ".autoreply [add <kw> = <resp> | list | remove]"),
            "donate": ("View STORM GOD developer support & donation info.", ".donate")
        }
    },
    "sticker": {
        "title": "STICKER MANAGER",
        "tag": "[STICKER]",
        "icon": "🎨",
        "description": "Collect & send server stickers anywhere",
        "commands": {
            "add sticker": ("Collect all stickers from current server.", ".add sticker"),
            "c": ("View sticker collection by server.", ".c [server_name]"),
            "sticker": ("Send a collected sticker by name.", ".sticker <name>")
        }
    },
    "emoji": {
        "title": "EMOJI MANAGER",
        "tag": "[EMOJI]",
        "icon": "😎",
        "description": "Use custom emojis without Nitro — send as image links",
        "commands": {
            "e": ("Send a custom emoji as image URL (no Nitro).", ".e <emoji_name> OR .e <number>"),
            "efind": ("Show all emojis from current server (numbered).", ".efind [number]"),
            "elist": ("List all custom emojis across your servers.", ".elist [page]"),
            "esearch": ("Search emojis by name fragment.", ".esearch <query>")
        }
    }
}

COMMAND_SUGGESTIONS = {
    "farm": "dark",
    "on": "dark",
    "off": "dark",
    "start": "dark",
    "cmds": "help",
    "menu": "help",
    "helpp": "help",
    "info": "status",
    "hist": "history",
    "loots": "history",
    "clear": "purge",
    "del": "purge",
    "delete": "purge",
    "purgeall": "purge",
    "channel": "cid",
    "user": "uid",
    "buy": "premium",
    "upgrade": "premium",
    "song": "mplay",
    "audio": "mplay",
    "m": "mplay",
    "searchm": "msearch",
    "vc": "vcmusic",
    "video": "vcvideo",
    "away": "afk",
    "snip": "snipe",
    "ar": "autoreply",
    "autoresponder": "autoreply",
    "tip": "donate",
    "emoji": "e",
    "emote": "e",
    "stickers": "c",
    "collection": "c"
}


def get_help_manifest(prefix, query=None):
    """
    Generates the full help system.
    - No query: Returns overview with ALL categories + navigation buttons
    - With query: Returns detailed category view
    """
    prefix = prefix or "."
    query = query.strip().lower() if query else ""

    # Category-specific help
    if query in COMMANDS_DOC:
        cat_data = COMMANDS_DOC[query]
        lines = [
            f"{cat_data['icon']}  {cat_data['title']}",
            f"    {cat_data['description']}",
            "══════════════════════════════════════════"
        ]
        text_lines = [
            f"**{cat_data['icon']} {cat_data['title']}** — *{cat_data['description']}*",
            "```"
        ]
        
        for cmd_name, (desc, usage) in cat_data["commands"].items():
            lines.append(f"  {prefix}{cmd_name.split()[0]}")
            lines.append(f"    {desc}")
            lines.append(f"    Usage: {usage.replace('.', prefix)}")
            lines.append("")
            text_lines.append(f"{usage.replace('.', prefix)} — {desc}")
            
        text_lines.append("```")
        
        # Back button
        components = [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "style": 2,
                        "label": "◀ Back to Help",
                        "custom_id": "help_back"
                    }
                ]
            }
        ]
        
        return lines, cat_data["title"], "\n".join(text_lines), components

    # Main help overview — show ALL categories with command counts
    categories = list(COMMANDS_DOC.keys())
    total_commands = sum(len(cat["commands"]) for cat in COMMANDS_DOC.values())
    
    lines = [
        "STORM GOD — COMMAND CENTER",
        f"    {total_commands} commands across {len(categories)} modules",
        "══════════════════════════════════════════",
        ""
    ]
    
    for cat_key in categories:
        cat = COMMANDS_DOC[cat_key]
        cmd_count = len(cat["commands"])
        lines.append(f"{cat['icon']}  {cat['title']}  [{cmd_count} cmds]")
        lines.append(f"    {cat['description']}")
        # Show first 3 command names inline
        cmd_names = list(cat["commands"].keys())[:3]
        preview = " | ".join(f"{prefix}{c.split()[0]}" for c in cmd_names)
        if len(cat["commands"]) > 3:
            preview += f" +{len(cat['commands']) - 3} more"
        lines.append(f"    {preview}")
        lines.append("")
    
    lines.append("══════════════════════════════════════════")
    lines.append(f"Type {prefix}help <category> for detailed usage")
    lines.append("github.com/rayzien/stormgod")

    text_msg = f"**[ STORM GOD — COMMAND CENTER ]**\n"
    for cat_key in categories:
        cat = COMMANDS_DOC[cat_key]
        text_msg += f"• {cat['icon']} **{cat['title']}**: `{prefix}help {cat_key}`\n"
    text_msg += f"\n*{total_commands} commands — Use `{prefix}help <category>` for details.*"

    # Navigation buttons for each category
    button_rows = []
    row = []
    styles = [1, 1, 1, 1, 3, 3, 4, 4]  # Varied button colors
    for i, cat_key in enumerate(categories):
        cat = COMMANDS_DOC[cat_key]
        row.append({
            "type": 2,
            "style": styles[i % len(styles)],
            "label": cat["title"][:20],
            "custom_id": f"help_{cat_key}"
        })
        if len(row) >= 4:
            button_rows.append({"type": 1, "components": row})
            row = []
    if row:
        button_rows.append({"type": 1, "components": row})
    
    return lines, "STORM GOD HELP CENTER", text_msg, button_rows


def handle_unknown_command(cmd, prefix):
    suggestion = COMMAND_SUGGESTIONS.get(cmd)
    lines = [
        f"Unknown Command: '{cmd}'",
        f"Suggested Alternative: {prefix}{suggestion}" if suggestion else f"Type {prefix}help to see available commands.",
        f"Status: COMMAND UNRESOLVED"
    ]
    if suggestion:
        text_msg = f"Unknown command `{prefix}{cmd}`. Did you mean `{prefix}{suggestion}`? Type `{prefix}help` for all commands."
    else:
        text_msg = f"Unknown command `{prefix}{cmd}`. Type `{prefix}help` to view all available commands."
    return lines, "Command Not Found", text_msg
