"""
commands/purge_commands.py — Direct Discord REST API Purge Handler for STORM GOD
"""
import time
import requests
from utils import get_self_id

def handle_purge(bot, token, channel_id, author_id, args, state):
    self_id = get_self_id(token) or author_id
    target = args[1].lower() if len(args) > 1 else "10"
    headers = {"Authorization": token, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    purged_count = 0

    if target == "all":
        target_chans = state.get("target_channel", "").split(",")
        channels_to_purge = [c.strip() for c in target_chans if c.strip()]
        if channel_id not in channels_to_purge:
            channels_to_purge.append(channel_id)
            
        for c_id in channels_to_purge:
            try:
                r = requests.get(f"https://discord.com/api/v9/channels/{c_id}/messages?limit=100", headers=headers, timeout=10)
                if r.status_code == 200:
                    messages = r.json()
                    for msg in messages:
                        if msg.get("author", {}).get("id") == self_id:
                            m_id = msg.get("id")
                            del_r = requests.delete(f"https://discord.com/api/v9/channels/{c_id}/messages/{m_id}", headers=headers, timeout=5)
                            if del_r.status_code in [200, 204]:
                                purged_count += 1
                                time.sleep(0.3)
            except Exception: pass
            
        lines = [
            f"Purged Target: ALL ({purged_count} messages)",
            "Status: MASS PURGE COMPLETE",
            "Channels Cleared: Across all allowed targets"
        ]
        text_msg = f"Purge Complete: Deleted **{purged_count}** messages across all allowed channels."
        return lines, "MASS PURGE", text_msg
    else:
        try:
            limit = min(int(target), 50)
        except ValueError:
            limit = 10
            
        try:
            r = requests.get(f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=100", headers=headers, timeout=10)
            if r.status_code == 200:
                messages = r.json()
                for msg in messages:
                    if msg.get("author", {}).get("id") == self_id:
                        m_id = msg.get("id")
                        del_r = requests.delete(f"https://discord.com/api/v9/channels/{channel_id}/messages/{m_id}", headers=headers, timeout=5)
                        if del_r.status_code in [200, 204]:
                            purged_count += 1
                            time.sleep(0.3)
                        if purged_count >= limit:
                            break
        except Exception: pass
        
        lines = [
            f"Purged Count: {purged_count} / {limit}",
            f"Channel ID: {channel_id}",
            "Status: LOCAL PURGE COMPLETE"
        ]
        text_msg = f"Purge Complete: Deleted **{purged_count}** of your sent messages in this channel."
        return lines, "CHANNEL PURGE", text_msg
