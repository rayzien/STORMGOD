"""
catcher_commands.py — STORM GOD Farm control commands (.dark, .cooldown, .stop)
"""

def handle_dark(bot, token, channel_id, state, update_state_func):
    prefix = state.get("prefix", ".")
    new_val = not state.get('farm_enabled', True)
    update_state_func(token, {"farm_enabled": new_val})
    status_str = "ENGAGED" if new_val else "HALTED / OFFLINE"
    lines = [
        f"STORMGOD Farm Status: {status_str}",
        f"Action: State saved in config.txt",
        f"Usage Hint: Type {prefix}dark again to toggle ON/OFF."
    ]
    text_msg = (
        f"**STORMGOD Farm Toggled!** Engine is now **{status_str}**.\n"
        f"Usage: Type `{prefix}dark` anytime to toggle ON or OFF."
    )
    return lines, "Module Toggled", text_msg

def handle_cooldown(bot, token, channel_id, prefix):
    lines = [
        "Mode: STORM GOD AUTO FARM",
        "Rate Limit Cooldown: Active",
        "Status: PROTECTION SYSTEM ACTIVE",
        f"Usage Hint: Use {prefix}dark to pause or resume farming."
    ]
    text_msg = (
        f"**Cooldown Status:** Engine spawn detection | Anti-ban protection active.\n"
        f"Usage: Type `{prefix}dark` to pause or resume farming."
    )
    return lines, "Failsafe Monitor", text_msg

def handle_stop(bot, token, channel_id, update_state_func, prefix):
    update_state_func(token, {"farm_enabled": False})
    lines = [
        "STORMGOD Farm status: OFF",
        "Failsafe: ENGAGED",
        "System: EMERGENCY HALT COMPLETE",
        f"Usage Hint: Type {prefix}dark to re-enable farming."
    ]
    text_msg = (
        f"**EMERGENCY HALT!** STORMGOD Farm disabled immediately.\n"
        f"Usage: Type `{prefix}dark` when ready to resume."
    )
    return lines, "Emergency Halt", text_msg
