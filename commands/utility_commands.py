"""
commands/utility_commands.py — AFK, Snipe, AutoReply, and Donation Text Commands for STORMGOD
"""
import os
import time
import json
from utils import read_config

# Snipe Cache: channel_id -> list of deleted message dicts [{author_name, author_id, content, time_str, timestamp}]
SNIPE_CACHE = {}

# AutoReply storage file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOREPLY_FILE = os.path.join(BASE_DIR, "autoreply.json")

def load_autoreplies():
    if os.path.exists(AUTOREPLY_FILE):
        try:
            with open(AUTOREPLY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"enabled": True, "triggers": {}}

def save_autoreplies(data):
    try:
        with open(AUTOREPLY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[STORMGOD AUTOREPLY] Error saving file: {e}")

# Global AutoReply Data
AUTOREPLY_DATA = load_autoreplies()

def record_deleted_message(channel_id, author_name, author_id, content):
    if not channel_id or not content:
        return
    if channel_id not in SNIPE_CACHE:
        SNIPE_CACHE[channel_id] = []

    time_str = time.strftime("%H:%M:%S")
    entry = {
        "author_name": author_name or "Unknown User",
        "author_id": str(author_id or ""),
        "content": content,
        "time_str": time_str,
        "timestamp": time.time()
    }

    SNIPE_CACHE[channel_id].insert(0, entry)
    if len(SNIPE_CACHE[channel_id]) > 20:
        SNIPE_CACHE[channel_id].pop()

# --- AFK COMMAND HANDLER ---

def handle_afk(bot, token, channel_id, args, state, update_state_func):
    """
    Text Command: .afk [on <msg> | off | status | message <msg>]
    Controls AFK auto-responder state and custom away message via chat.
    """
    prefix = state.get("prefix", ".")
    config = read_config()

    token1 = config.get("token", "")
    token2 = config.get("token2", "")
    afk_key = "afk_msg1" if token == token1 else ("afk_msg2" if token == token2 else "afk_msg1")

    current_afk_enabled = config.get("afk_enabled", "false") == "true"
    current_msg = config.get(afk_key, "") or "I am currently AFK / away from keyboard."

    if len(args) < 2:
        lines = [
            "AFK AUTO-RESPONDER MODULE",
            "──────────────────────────────────────────",
            f"Status: {'ENABLED (ONLINE)' if current_afk_enabled else 'DISABLED (OFFLINE)'}",
            f"Message: \"{current_msg[:35]}\"",
            "──────────────────────────────────────────",
            f"Turn ON: {prefix}afk on [message]",
            f"Turn OFF: {prefix}afk off"
        ]
        text_msg = (
            f"💤 **[ AFK AUTO-RESPONDER STATUS ]**\n"
            f"• **Status:** `{ 'ENABLED' if current_afk_enabled else 'DISABLED' }`\n"
            f"• **Current Away Message:** \"*{current_msg}*\"\n\n"
            f"**Usage Commands:**\n"
            f"- `{prefix}afk on [message]` — Enable AFK mode with optional message\n"
            f"- `{prefix}afk off` — Disable AFK mode\n"
            f"- `{prefix}afk msg <text>` — Set custom away message"
        )
        return lines, "AFK STATUS", text_msg

    subcmd = args[1].lower()

    if subcmd == "on":
        custom_msg = " ".join(args[2:]).strip() if len(args) > 2 else current_msg
        update_state_func(token, {"afk_enabled": "true", afk_key: custom_msg})

        lines = [
            "AFK MODE ACTIVATED",
            "──────────────────────────────────────────",
            "Status: ENABLED (ONLINE)",
            f"Away Msg: \"{custom_msg[:35]}\"",
            "──────────────────────────────────────────",
            f"Type {prefix}afk off to disable AFK."
        ]
        text_msg = f"💤 **AFK Mode Activated!** Auto-responder is **ON**.\n> Away Message: \"*{custom_msg}*\""
        return lines, "AFK ACTIVATED", text_msg

    elif subcmd in ["off", "disable", "stop"]:
        update_state_func(token, {"afk_enabled": "false"})

        lines = [
            "AFK MODE DEACTIVATED",
            "──────────────────────────────────────────",
            "Status: DISABLED",
            "Auto-responder halted."
        ]
        text_msg = f"🟢 **AFK Mode Deactivated.** Auto-responder turned OFF."
        return lines, "AFK DEACTIVATED", text_msg

    elif subcmd in ["msg", "message", "setmsg"]:
        if len(args) < 3:
            return handle_afk(bot, token, channel_id, [], state, update_state_func)
        new_msg = " ".join(args[2:]).strip()
        update_state_func(token, {afk_key: new_msg})

        lines = [
            "AFK MESSAGE UPDATED",
            "──────────────────────────────────────────",
            f"New Away Msg: \"{new_msg[:35]}\"",
            f"AFK Enabled: {current_afk_enabled}"
        ]
        text_msg = f"✅ **AFK Message Updated!**\n> New Away Message: \"*{new_msg}*\""
        return lines, "AFK MSG SAVED", text_msg

    return handle_afk(bot, token, channel_id, [], state, update_state_func)

# --- SNIPE COMMAND HANDLER ---

def handle_snipe(bot, token, channel_id, args, state, update_state_func=None):
    """
    Text Command: .snipe [index | on | off]
    Retrieves recently deleted messages in the current channel or toggles engine state.
    """
    prefix = state.get("prefix", ".")
    deleted_list = SNIPE_CACHE.get(channel_id, [])

    if len(args) > 1:
        sub = args[1].lower()
        if sub in ["on", "enable"] and update_state_func:
            update_state_func(token, {"snipe_enabled": "true"})
            lines = ["SNIPE ENGINE ACTIVATED", "──────────────────────────────────────────", "Status: ENABLED (ONLINE)"]
            return lines, "SNIPE ACTIVATED", f"🎯 **Snipe Module Enabled.** Message deletion tracking active."
        elif sub in ["off", "disable"] and update_state_func:
            update_state_func(token, {"snipe_enabled": "false"})
            lines = ["SNIPE ENGINE DEACTIVATED", "──────────────────────────────────────────", "Status: DISABLED"]
            return lines, "SNIPE DEACTIVATED", f"🛑 **Snipe Module Disabled.**"

    if not deleted_list:
        lines = [
            "MESSAGE SNIPER ENGINE",
            "──────────────────────────────────────────",
            "Status: NO DELETED MESSAGES CACHED",
            "Waiting for deleted message events."
        ]
        text_msg = f"🎯 **[ MESSAGE SNIPER ]**\nNo recently deleted messages found in this channel."
        return lines, "NO SNIPED MESSAGES", text_msg

    idx = 0
    if len(args) > 1 and args[1].isdigit():
        idx = max(0, int(args[1]) - 1)

    if idx >= len(deleted_list):
        idx = len(deleted_list) - 1

    entry = deleted_list[idx]

    lines = [
        f"🎯 SNIPED MESSAGE #{idx + 1}",
        "──────────────────────────────────────────",
        f"Author: {entry['author_name'][:25]}",
        f"Time: {entry['time_str']}",
        f"Content: {entry['content'][:40]}",
        "──────────────────────────────────────────",
        f"Total Cached Snipes: {len(deleted_list)}"
    ]

    text_msg = (
        f"🎯 **[ SNIPED DELETED MESSAGE #{idx + 1}/{len(deleted_list)} ]**\n"
        f"👤 **Author:** `{entry['author_name']}` (ID: `{entry['author_id']}`)\n"
        f"🕒 **Time:** `{entry['time_str']}`\n"
        f"💬 **Message Content:**\n> {entry['content']}\n\n"
        f"*Type `{prefix}snipe 2` for older sniped messages or `{prefix}snipe off` to disable.*"
    )

    return lines, f"SNIPED: {entry['author_name'].upper()}", text_msg


# --- AUTOREPLY COMMAND HANDLER ---

def handle_autoreply(bot, token, channel_id, args, state, update_state_func):
    """
    Text Command: .autoreply [add <trigger> = <response> | remove <trigger> | list | on | off]
    Manages keyword auto-replies.
    """
    prefix = state.get("prefix", ".")
    global AUTOREPLY_DATA

    if len(args) < 2:
        triggers = AUTOREPLY_DATA.get("triggers", {})
        is_on = AUTOREPLY_DATA.get("enabled", True)

        lines = [
            "KEYWORD AUTO-REPLY ENGINE",
            "──────────────────────────────────────────",
            f"Engine Status: {'ENABLED' if is_on else 'DISABLED'}",
            f"Active Triggers: {len(triggers)} keyword(s)",
            "──────────────────────────────────────────",
            f"Add: {prefix}autoreply add <kw> = <resp>",
            f"List: {prefix}autoreply list",
            f"Remove: {prefix}autoreply remove <kw>"
        ]

        text_lines = [
            f"🤖 **[ KEYWORD AUTO-REPLY ENGINE ]**",
            f"• **Engine Status:** `{ 'ENABLED' if is_on else 'DISABLED' }`",
            f"• **Total Active Triggers:** `{len(triggers)}` keyword(s)\n",
            f"**Usage Commands:**",
            f"- `{prefix}autoreply add <trigger> = <response>` — Add auto-reply",
            f"- `{prefix}autoreply list` — View all registered triggers",
            f"- `{prefix}autoreply remove <trigger>` — Delete a trigger",
            f"- `{prefix}autoreply on` / `{prefix}autoreply off` — Toggle auto-reply engine"
        ]

        return lines, "AUTOREPLY MANAGER", "\n".join(text_lines)

    subcmd = args[1].lower()

    if subcmd == "add":
        full_text = " ".join(args[2:]).strip()
        if "=" not in full_text:
            lines = ["INVALID SYNTAX", "──────────────────────────────────────────", f"Syntax: {prefix}autoreply add <trigger> = <response>"]
            text_msg = f"⚠️ Invalid syntax. Usage: `{prefix}autoreply add <trigger> = <response>` (e.g. `{prefix}autoreply add hello = Hey there!`)."
            return lines, "SYNTAX ERROR", text_msg

        trigger, response = [part.strip() for part in full_text.split("=", 1)]
        if not trigger or not response:
            lines = ["INVALID ENTRY", "──────────────────────────────────────────", "Trigger and response cannot be empty."]
            text_msg = f"⚠️ Trigger and response text cannot be empty."
            return lines, "ENTRY ERROR", text_msg

        AUTOREPLY_DATA["triggers"][trigger.lower()] = response
        save_autoreplies(AUTOREPLY_DATA)

        lines = [
            "AUTO-REPLY ADDED",
            "──────────────────────────────────────────",
            f"Trigger: \"{trigger[:25]}\"",
            f"Response: \"{response[:30]}\"",
            "──────────────────────────────────────────",
            "Saved successfully."
        ]
        text_msg = f"✅ **Auto-Reply Registered!**\n> 🔑 **Trigger:** `{trigger}`\n> 💬 **Response:** \"*{response}*\""
        return lines, "TRIGGER ADDED", text_msg

    elif subcmd in ["remove", "del", "delete"]:
        if len(args) < 3:
            lines = ["MISSING TRIGGER", "──────────────────────────────────────────", f"Syntax: {prefix}autoreply remove <trigger>"]
            text_msg = f"⚠️ Please specify the trigger to remove. Usage: `{prefix}autoreply remove <trigger>`"
            return lines, "MISSING PARAM", text_msg

        target = " ".join(args[2:]).strip().lower()
        if target in AUTOREPLY_DATA["triggers"]:
            del AUTOREPLY_DATA["triggers"][target]
            save_autoreplies(AUTOREPLY_DATA)
            lines = ["AUTO-REPLY REMOVED", "──────────────────────────────────────────", f"Removed trigger: '{target}'"]
            text_msg = f"🗑️ **Auto-Reply Removed!** Trigger `{target}` deleted."
            return lines, "TRIGGER REMOVED", text_msg
        else:
            lines = ["TRIGGER NOT FOUND", "──────────────────────────────────────────", f"No trigger matches: '{target}'"]
            text_msg = f"❌ Trigger `{target}` not found in auto-reply database."
            return lines, "NOT FOUND", text_msg

    elif subcmd in ["list", "show", "all"]:
        triggers = AUTOREPLY_DATA.get("triggers", {})
        if not triggers:
            lines = ["NO ACTIVE TRIGGERS", "──────────────────────────────────────────", f"Add trigger: {prefix}autoreply add <kw> = <resp>"]
            text_msg = f"ℹ️ No auto-reply triggers registered. Add one using `{prefix}autoreply add <trigger> = <response>`."
            return lines, "NO TRIGGERS", text_msg

        lines = [f"AUTO-REPLY TRIGGERS ({len(triggers)})", "──────────────────────────────────────────"]
        text_lines = [f"📋 **[ REGISTERED AUTO-REPLIES ({len(triggers)}) ]**\n"]

        for idx, (trig, resp) in enumerate(triggers.items(), start=1):
            lines.append(f"{idx}. '{trig}' -> '{resp[:25]}'")
            text_lines.append(f"**{idx}.** Trigger: `{trig}`\n> Response: \"*{resp}*\"")

        return lines, "AUTOREPLY LIST", "\n".join(text_lines)

    elif subcmd in ["on", "enable"]:
        AUTOREPLY_DATA["enabled"] = True
        save_autoreplies(AUTOREPLY_DATA)
        lines = ["AUTOREPLY ENGINE ON", "──────────────────────────────────────────", "Status: ENABLED"]
        text_msg = f"🟢 **Auto-Reply Engine Enabled.**"
        return lines, "AUTOREPLY ON", text_msg

    elif subcmd in ["off", "disable"]:
        AUTOREPLY_DATA["enabled"] = False
        save_autoreplies(AUTOREPLY_DATA)
        lines = ["AUTOREPLY ENGINE OFF", "──────────────────────────────────────────", "Status: DISABLED"]
        text_msg = f"🔴 **Auto-Reply Engine Disabled.**"
        return lines, "AUTOREPLY OFF", text_msg

    return handle_autoreply(bot, token, channel_id, [], state, update_state_func)

# --- DONATE COMMAND HANDLER ---

def handle_donate(prefix):
    """
    Text Command: .donate
    Displays developer support and donation channels.
    """
    lines = [
        "STORMGOD DEVELOPER DONATIONS",
        "──────────────────────────────────────────",
        "Developed by: rayzien",
        "Support tier: Lifetime Free & Open",
        "──────────────────────────────────────────",
        "Crypto USDT (TRC20): T...[Contact rayzien]",
        "PayPal / UPI: contact rayzien",
        "──────────────────────────────────────────",
        f"Check dashboard Premium for perks!"
    ]

    text_msg = (
        "❤️ **[ SUPPORT STORMGOD & DEVELOPER RAYZIEN ]**\n"
        "STORMGOD is actively maintained as a powerful selfbot framework!\n\n"
        "**Ways to Support Development:**\n"
        "• 🌟 **Star & Share:** Spread STORMGOD with friends\n"
        "• 💎 **Premium Membership:** Unlock multi-node priority capabilities\n"
        "• 🎁 **Direct Support / Tips:** Contact `rayzien` for official developer donation addresses\n\n"
        "*Thank you for supporting STORMGOD!*"
    )

    return lines, "SUPPORT & DONATIONS", text_msg
