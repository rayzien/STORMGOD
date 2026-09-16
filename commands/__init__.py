"""
commands/__init__.py — Central Command Router & Dispatcher for STORM GOD
"""
import os
from utils import send_image_to_discord
from image_renderer import generate_glass_card, generate_help_card

from .help_command import get_help_manifest, handle_unknown_command
from .core_commands import (
    handle_ping, handle_status, handle_prefix, handle_say, handle_cid, handle_uid
)
from .catcher_commands import handle_dark, handle_cooldown, handle_stop
from .prompt_commands import handle_prompt_action
from .premium_commands import handle_premium
from .purge_commands import handle_purge
from .history_command import handle_history
from .channel_commands import handle_allow, handle_block
from .music_command import (
    handle_music_search, handle_music_select, handle_music_play,
    handle_music_quality, handle_music_info, handle_music_queue,
    handle_music_stop, handle_music_skip, handle_vcmusic, handle_vcvideo
)
from .utility_commands import handle_afk, handle_snipe, handle_autoreply, handle_donate
from .sticker_commands import handle_add_sticker, handle_sticker_collection, handle_send_sticker
from .emoji_commands import handle_emoji_send, handle_emoji_list, handle_emoji_search

def dispatch_command(cmd, args, content, prefix, state, token, channel_id, author_id, author_name, bot, update_state_func, guild_id=None):
    cmd = cmd.lower()

    # ── HELP ──
    if cmd == "help":
        query = args[1] if len(args) > 1 else None
        return get_help_manifest(prefix, query)

    # ── CORE ──
    elif cmd == "ping":
        return handle_ping(bot, token, channel_id, state)

    elif cmd == "status":
        return handle_status(bot, token, channel_id, state)

    elif cmd in ["history", "hist", "logs", "loots"]:
        return handle_history(bot, token, channel_id, args, state)

    elif cmd == "allow":
        return handle_allow(bot, token, channel_id, args, state, update_state_func)

    elif cmd == "block":
        return handle_block(bot, token, channel_id, args, state, update_state_func)

    elif cmd == "prefix":
        return handle_prefix(bot, token, channel_id, state, args, update_state_func)

    elif cmd == "say":
        return handle_say(bot, token, channel_id, content, prefix, args)

    elif cmd == "cid":
        return handle_cid(bot, token, channel_id)

    elif cmd == "uid":
        return handle_uid(bot, token, channel_id, author_id, args, prefix)

    # ── AUTOMATION ──
    elif cmd == "dark":
        return handle_dark(bot, token, channel_id, state, update_state_func)

    elif cmd == "cooldown":
        return handle_cooldown(bot, token, channel_id, prefix)

    elif cmd == "stop":
        return handle_stop(bot, token, channel_id, update_state_func, prefix)

    elif cmd in ["purge", "purgeall"]:
        return handle_purge(bot, token, channel_id, author_id, args, state)

    elif cmd in ["yes", "accept"]:
        return handle_prompt_action("yes", bot, channel_id, prefix)

    elif cmd in ["no", "disagree"]:
        return handle_prompt_action("no", bot, channel_id, prefix)

    elif cmd == "premium":
        return handle_premium(prefix)

    # ── AFK ──
    elif cmd in ["afk", "away"]:
        return handle_afk(bot, token, channel_id, args, state, update_state_func)

    # ── SNIPE ──
    elif cmd in ["snipe", "snip"]:
        if len(args) > 1 and args[1].lower() in ["on", "enable"]:
            return handle_snipe(bot, token, channel_id, args, state, update_state_func)
        if not state.get("snipe_enabled", True):
            lines = ["SNIPE MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF", f"Enable: {prefix}snipe on"]
            return lines, "SNIPE DISABLED", f"Snipe module is currently disabled. Type `{prefix}snipe on` or toggle ON in dashboard settings."
        return handle_snipe(bot, token, channel_id, args, state, update_state_func)

    # ── AUTOREPLY ──
    elif cmd in ["autoreply", "ar", "autoresponder"]:
        return handle_autoreply(bot, token, channel_id, args, state, update_state_func)

    # ── DONATE ──
    elif cmd in ["donate", "donations", "tip", "support"]:
        return handle_donate(prefix)

    # ── STICKER MANAGER ──
    elif cmd == "add" and len(args) > 1 and args[1].lower() == "sticker":
        return handle_add_sticker(bot, token, channel_id, args, guild_id)

    elif cmd == "c":
        return handle_sticker_collection(bot, token, channel_id, args)

    elif cmd == "sticker":
        return handle_send_sticker(bot, token, channel_id, args)

    # ── EMOJI MANAGER ──
    elif cmd == "e":
        return handle_emoji_send(bot, token, channel_id, args, guild_id)

    elif cmd == "efind":
        from .emoji_commands import handle_emoji_find
        return handle_emoji_find(bot, token, channel_id, args, guild_id)

    elif cmd in ["elist", "emojis"]:
        return handle_emoji_list(bot, token, channel_id, args)

    elif cmd == "esearch":
        return handle_emoji_search(bot, token, channel_id, args)

    # ── MUSIC & VC ──
    elif cmd in ["msearch", "searchmusic"]:
        if not state.get("music_enabled", True):
            lines = ["MUSIC MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF"]
            return lines, "MUSIC DISABLED", "Music module is currently disabled in settings."
        return handle_music_search(bot, token, channel_id, args, state, author_id)

    elif cmd == "mselect":
        if not state.get("music_enabled", True):
            lines = ["MUSIC MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF"]
            return lines, "MUSIC DISABLED", "Music module is currently disabled in settings."
        return handle_music_select(bot, token, channel_id, args, state, author_id)

    elif cmd in ["mplay", "play", "music"]:
        if not state.get("music_enabled", True):
            lines = ["MUSIC MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF"]
            return lines, "MUSIC DISABLED", "Music player module is currently disabled in settings."
        return handle_music_play(bot, token, channel_id, args, state, author_id)

    elif cmd in ["vcmusic", "vcaudio"]:
        if not state.get("vcmusic_enabled", True):
            lines = ["VC MUSIC MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF"]
            return lines, "VC MUSIC DISABLED", "Voice channel music module is currently disabled in settings."
        return handle_vcmusic(bot, token, channel_id, args, state)

    elif cmd in ["vcvideo", "vcstream"]:
        if not state.get("vcmusic_enabled", True):
            lines = ["VC VIDEO MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF"]
            return lines, "VC VIDEO DISABLED", "Voice channel video module is currently disabled in settings."
        return handle_vcvideo(bot, token, channel_id, args, state)

    elif cmd in ["mquality", "quality"]:
        return handle_music_quality(bot, token, channel_id, args, state, update_state_func)

    elif cmd == "minfo":
        if not state.get("music_enabled", True):
            lines = ["MUSIC MODULE DISABLED", "──────────────────────────────────────────", "Status: MODULE IS OFF"]
            return lines, "MUSIC DISABLED", "Music module is currently disabled in settings."
        return handle_music_info(bot, token, channel_id, args, state)

    elif cmd in ["mqueue", "queue"]:
        return handle_music_queue(bot, token, channel_id, args, state)

    elif cmd in ["mstop", "stopmusic"]:
        return handle_music_stop(bot, token, channel_id, state)

    elif cmd in ["skip", "mskip"]:
        return handle_music_skip(bot, token, channel_id, state)

    return handle_unknown_command(cmd, prefix)



def execute(content, prefix, state, token, channel_id, author_id, author_name, bot, update_state_func, guild_id=None):
    args = content[len(prefix):].split()
    if not args:
        return

    cmd = args[0]
    res = dispatch_command(
        cmd, args, content, prefix, state, token, channel_id, author_id, author_name, bot, update_state_func, guild_id=guild_id
    )
    
    components = None
    auto_delete_delay = 0
    if res is None:
        return
    if len(res) == 5:
        lines, card_title, text_msg, components, auto_delete_delay = res
    elif len(res) == 4:
        lines, card_title, text_msg, components = res
    elif len(res) == 3:
        lines, card_title, text_msg = res
    else:
        return

    if lines is None and card_title is None and text_msg is None:
        return

    if lines and card_title:
        try:
            # Use specialized help renderer for help commands
            if card_title in ["STORM GOD HELP CENTER"] or "COMMAND CENTER" in (card_title or ""):
                file_path = generate_help_card(card_title, lines)
            else:
                file_path = generate_glass_card(card_title, lines)
            sent = send_image_to_discord(token, channel_id, file_path, content="", components=components, auto_delete_delay=auto_delete_delay)
            if not sent and text_msg:
                bot.sendMessage(channel_id, text_msg)
        except Exception as e:
            print(f"[STORMGOD COMMANDS] Execution error: {e}")
            if text_msg:
                try:
                    bot.sendMessage(channel_id, text_msg)
                except Exception:
                    pass
    elif text_msg:
        try:
            bot.sendMessage(channel_id, text_msg)
        except Exception as e:
            print(f"[STORMGOD COMMANDS] Text send error: {e}")
