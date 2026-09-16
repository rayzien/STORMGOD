"""
premium_commands.py — Premium info command (.premium) for STORM GOD
"""

def handle_premium(prefix):
    lines = [
        "STORMGOD PREMIUM EDITION:",
        "- Multi-account concurrent automation",
        "- Instant Captcha Alert Notifications",
        "- Advanced Credits tracking & analytics",
        "- Priority support and automatic updates",
        f"Usage: Visit dashboard Premium tab or type {prefix}premium"
    ]
    text_msg = (
        "**[ STORMGOD PREMIUM EDITION ]**\n"
        "- Multi-account concurrent automation\n"
        "- Instant Captcha Alert Notifications\n"
        "- Advanced Credits tracking & analytics\n"
        "- Priority support and automatic updates\n\n"
        "Check out the Premium tab on your dashboard for upgrade details!"
    )
    return lines, "Premium Tier Info", text_msg
