import os
import time
from dotenv import load_dotenv
from utils import is_authorized, read_config, send_image_to_discord
from image_renderer import generate_glass_card

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "STORM GOD")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_node_state(token=None):
    config = read_config()
    token_idx = 1
    if token and token == config.get("token2"):
        token_idx = 2
        
    chan_key = "target_channel" if token_idx == 1 else f"target_channel{token_idx}"
    
    return {
        "prefix": config.get("prefix", "."),
        "farm_enabled": config.get("farm_enabled", "true") == "true",
        "target_channel": config.get(chan_key, ""),
        "listener_id": config.get("listener_id", "self"),
        "music_enabled": config.get("music_enabled", "true") == "true",
        "music_quality": config.get("music_quality", "high"),
        "snipe_enabled": config.get("snipe_enabled", "true") == "true",
        "autoreply_enabled": config.get("autoreply_enabled", "true") == "true",
        "vcmusic_enabled": config.get("vcmusic_enabled", "true") == "true",
        "afk_enabled": config.get("afk_enabled", "false") == "true",
        "token": config.get("token", ""),
    }

def update_node_state(token, data):
    config = read_config()
    key_map = {
        "farm_enabled": lambda v: "true" if v else "false",
        "music_enabled": lambda v: "true" if v else "false",
        "snipe_enabled": lambda v: "true" if v else "false",
        "autoreply_enabled": lambda v: "true" if v else "false",
        "vcmusic_enabled": lambda v: "true" if v else "false",
        "afk_enabled": lambda v: "true" if v else "false",
        "prefix": str,
        "target_channel": str,
        "listener_id": str,
    }
    for k, v in data.items():
        if k in key_map:
            config[k] = key_map[k](v)
        else:
            config[k] = str(v)
    
    config_path = os.path.join(BASE_DIR, "config.txt")
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            for key, val in config.items():
                f.write(f"{key}={val}\n")
    except Exception as e:
        print(f"[{PROJECT_NAME}] Config write error: {e}")


import commands
from commands.utility_commands import record_deleted_message, AUTOREPLY_DATA

RECENT_MESSAGES_CACHE = {} # message_id -> {author_name, author_id, channel_id, content}

def on_message_delete(resp, bot, token):
    if resp.event.message_deleted:
        try:
            msg_data = resp.parsed.auto()
            msg_id = msg_data.get("id")
            channel_id = msg_data.get("channel_id")

            cached = RECENT_MESSAGES_CACHE.get(msg_id)
            if cached:
                record_deleted_message(
                    channel_id=cached["channel_id"],
                    author_name=cached["author_name"],
                    author_id=cached["author_id"],
                    content=cached["content"]
                )
            elif msg_data.get("content"):
                record_deleted_message(
                    channel_id=channel_id,
                    author_name=msg_data.get("author", {}).get("username", "Unknown User"),
                    author_id=msg_data.get("author", {}).get("id", ""),
                    content=msg_data.get("content")
                )
        except Exception:
            pass

def on_message(resp, bot, token):
    if resp.event.message:
        msg = resp.parsed.auto()
        author = msg.get("author", {})
        author_id = author.get("id")
        author_name = author.get("username", "Unknown")
        channel_id = msg.get("channel_id")
        guild_id = msg.get("guild_id")
        content = msg.get("content", "").strip()
        msg_id = msg.get("id")

        if msg_id and content:
            RECENT_MESSAGES_CACHE[msg_id] = {
                "author_name": author_name,
                "author_id": author_id,
                "channel_id": channel_id,
                "content": content
            }
            if len(RECENT_MESSAGES_CACHE) > 500:
                RECENT_MESSAGES_CACHE.pop(next(iter(RECENT_MESSAGES_CACHE)))
        
        config = read_config()
        if config.get("afk_enabled", "false") == "true" and not guild_id:
            try:
                bot_id = bot.gateway.session.user.get('id')
                if bot_id and author_id != bot_id:
                    token1 = config.get("token", "")
                    token2 = config.get("token2", "")
                    afk_msg = ""
                    if token == token1: afk_msg = config.get("afk_msg1", "")
                    elif token == token2: afk_msg = config.get("afk_msg2", "")
                    
                    if afk_msg:
                        global AFK_COOLDOWNS
                        if 'AFK_COOLDOWNS' not in globals():
                            AFK_COOLDOWNS = {}
                        last_afk = AFK_COOLDOWNS.get(author_id, 0)
                        if time.time() - last_afk > 300:
                            bot.sendMessage(channel_id, afk_msg)
                            AFK_COOLDOWNS[author_id] = time.time()
                            from web_server import add_log
                            add_log(f"[{bot_id[:5]}...] AFK auto-responded to DM from {author_name}")
            except Exception: pass
        
        state = get_node_state(token)
        prefix = state.get("prefix", ".")

        if not content.startswith(prefix):
            # Check AutoReply Triggers
            try:
                bot_id = bot.gateway.session.user.get('id')
                if author_id != bot_id and AUTOREPLY_DATA.get("enabled", True):
                    triggers = AUTOREPLY_DATA.get("triggers", {})
                    content_lower = content.lower()
                    for trig, reply_text in triggers.items():
                        if trig in content_lower:
                            bot.sendMessage(channel_id, reply_text)
                            from web_server import add_log
                            add_log(f"AutoReply triggered for '{trig}' in channel {channel_id}")
                            break
            except Exception:
                pass
            return

        if not is_authorized(author_id, token):
            return

        from web_server import add_log
        add_log(f"CMD: '{content}' by {author_name}")

        commands.execute(
            content=content,
            prefix=prefix,
            state=state,
            token=token,
            channel_id=channel_id,
            author_id=author_id,
            author_name=author_name,
            bot=bot,
            update_state_func=update_node_state,
            guild_id=guild_id
        )

def setup(bot, token=None):
    bot.gateway.command({"function": lambda resp: on_message(resp, bot, token), "name": "MESSAGE_CREATE"})
    bot.gateway.command({"function": lambda resp: on_message_delete(resp, bot, token), "name": "MESSAGE_DELETE"})

