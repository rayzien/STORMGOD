"""
commands/channel_commands.py — Channel Authorization (.allow / .block) Handler for STORM GOD
"""
from utils import read_config, write_config

def handle_allow(bot, token, channel_id, args, state, update_state_func):
    target = args[1].strip() if len(args) > 1 else str(channel_id)
    config = read_config()
    
    current_chans_raw = state.get("target_channel") or config.get("target_channel", "")
    chans = [c.strip() for c in current_chans_raw.split(",") if c.strip()]
    
    if target not in chans:
        chans.append(target)
        new_chans_str = ", ".join(chans)
        
        update_state_func(token, {"target_channel": new_chans_str})
        write_config({"target_channel": new_chans_str})
        
        lines = [
            f"Allowed Channel: {target}",
            f"Active Target Channels: {len(chans)}",
            "Status: ALLOWED & SECURED"
        ]
        text_msg = f"Channel Allowed! Added `{target}` to active listening targets."
        return lines, "CHANNEL ALLOWED", text_msg
    else:
        lines = [
            f"Channel ID: {target}",
            "Status: ALREADY ALLOWED",
            f"Active Targets: {len(chans)}"
        ]
        text_msg = f"Channel `{target}` is already allowed and monitored."
        return lines, "CHANNEL PERMISSION", text_msg


def handle_block(bot, token, channel_id, args, state, update_state_func):
    target = args[1].strip() if len(args) > 1 else str(channel_id)
    config = read_config()
    
    current_chans_raw = state.get("target_channel") or config.get("target_channel", "")
    chans = [c.strip() for c in current_chans_raw.split(",") if c.strip()]
    
    if target in chans:
        chans.remove(target)
        new_chans_str = ", ".join(chans)
        
        update_state_func(token, {"target_channel": new_chans_str})
        write_config({"target_channel": new_chans_str})
        
        lines = [
            f"Blocked Channel: {target}",
            f"Remaining Active Targets: {len(chans)}",
            "Status: BLOCKED & HALTED"
        ]
        text_msg = f"Channel Blocked! Removed `{target}` from listening targets."
        return lines, "CHANNEL BLOCKED", text_msg
    else:
        lines = [
            f"Channel ID: {target}",
            "Status: NOT IN ALLOWED LIST",
            f"Remaining Targets: {len(chans)}"
        ]
        text_msg = f"Channel `{target}` is not in the active allowed targets list."
        return lines, "CHANNEL PERMISSION", text_msg
