"""
commands/music_command.py — YouTube Music Engine & Quality Selector using yt-dlp (Text-Based Commands)
"""
import os
import time
import math
import re
import subprocess
import json

# Per-user last music search cache: (channel_id, author_id) -> list of result dicts
LAST_MUSIC_SEARCH = {}

# Per-channel music queue: channel_id -> {'queue': [], 'current': None, 'status': 'idle'}
MUSIC_QUEUE = {}

QUALITY_SETTINGS = {
    "best": {"label": "Best / Lossless (320kbps)", "format": "bestaudio/best", "bitrate": "320k"},
    "320k": {"label": "320 kbps (Ultra High)", "format": "bestaudio/best", "bitrate": "320k"},
    "high": {"label": "High Quality (192kbps)", "format": "bestaudio[ext=m4a]/bestaudio/best", "bitrate": "192k"},
    "192k": {"label": "192 kbps (Standard High)", "format": "bestaudio/best", "bitrate": "192k"},
    "medium": {"label": "Medium Quality (128kbps)", "format": "bestaudio[abr<=160]/bestaudio/best", "bitrate": "128k"},
    "128k": {"label": "128 kbps (Standard)", "format": "bestaudio[abr<=160]/bestaudio/best", "bitrate": "128k"},
    "low": {"label": "Low Quality / Data Saver (64kbps)", "format": "worstaudio/bestaudio[abr<=96]/best", "bitrate": "64k"},
    "64k": {"label": "64 kbps (Low)", "format": "worstaudio/bestaudio[abr<=96]/best", "bitrate": "64k"}
}

def format_duration(seconds):
    if not seconds:
        return "N/A"
    try:
        sec = int(seconds)
        mins, s = divmod(sec, 60)
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            return f"{hrs}:{mins:02d}:{s:02d}"
        return f"{mins}:{s:02d}"
    except Exception:
        return "N/A"

def format_views(views):
    if not views:
        return "N/A"
    try:
        v = int(views)
        if v >= 1_000_000_000:
            return f"{v / 1_000_000_000:.1f}B"
        if v >= 1_000_000:
            return f"{v / 1_000_000:.1f}M"
        if v >= 1_000:
            return f"{v / 1_000:.1f}K"
        return str(v)
    except Exception:
        return "N/A"

def perform_yt_music_search(query, max_results=10):
    """
    Searches YouTube music tracks using yt-dlp.
    Returns list of track dicts: [{'title', 'uploader', 'duration', 'views', 'url', 'id'}]
    """
    results = []
    query_str = query.strip()
    search_term = query_str if query_str.startswith("http://") or query_str.startswith("https://") else f"ytsearch{max_results}:{query_str}"

    # Try importing yt_dlp library first
    try:
        import yt_dlp
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
            'default_search': 'ytsearch'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_term, download=False)
            if info:
                entries = info.get('entries', [info]) if 'entries' in info else [info]
                for entry in entries:
                    if not entry:
                        continue
                    video_id = entry.get('id', '')
                    title = entry.get('title', 'Unknown Track')
                    uploader = entry.get('uploader') or entry.get('channel') or 'Unknown Artist'
                    duration = entry.get('duration')
                    views = entry.get('view_count')
                    url = entry.get('webpage_url') or f"https://www.youtube.com/watch?v={video_id}"
                    results.append({
                        'id': video_id,
                        'title': title,
                        'uploader': uploader,
                        'duration': duration,
                        'duration_str': format_duration(duration),
                        'views': views,
                        'views_str': format_views(views),
                        'url': url
                    })
                if results:
                    return results
    except Exception as e:
        print(f"[MUSIC ENGINE] yt_dlp module search fallback: {e}")

    # Fallback to calling yt-dlp CLI via subprocess
    try:
        cmd = [
            "yt-dlp",
            "--dump-single-json",
            "--flat-playlist",
            "--default-search", "ytsearch",
            search_term
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0 and proc.stdout:
            data = json.loads(proc.stdout)
            entries = data.get('entries', [data]) if 'entries' in data else [data]
            for entry in entries:
                if not entry:
                    continue
                video_id = entry.get('id', '')
                title = entry.get('title', 'Unknown Track')
                uploader = entry.get('uploader') or entry.get('channel') or 'Unknown Artist'
                duration = entry.get('duration')
                views = entry.get('view_count')
                url = entry.get('webpage_url') or f"https://www.youtube.com/watch?v={video_id}"
                results.append({
                    'id': video_id,
                    'title': title,
                    'uploader': uploader,
                    'duration': duration,
                    'duration_str': format_duration(duration),
                    'views': views,
                    'views_str': format_views(views),
                    'url': url
                })
    except Exception as e:
        print(f"[MUSIC ENGINE] yt-dlp CLI search exception: {e}")

    return results

def extract_audio_info(url_or_query, quality="high"):
    """
    Extracts deep track metadata and direct audio format URLs using yt-dlp.
    """
    qual_config = QUALITY_SETTINGS.get(quality.lower(), QUALITY_SETTINGS["high"])
    fmt = qual_config["format"]

    search_target = url_or_query.strip()
    if not (search_target.startswith("http://") or search_target.startswith("https://")):
        search_target = f"ytsearch1:{search_target}"

    try:
        import yt_dlp
        ydl_opts = {
            'format': fmt,
            'quiet': True,
            'skip_download': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_target, download=False)
            if info:
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]
                
                audio_url = info.get('url', '')
                title = info.get('title', 'Unknown Track')
                uploader = info.get('uploader') or info.get('channel') or 'Unknown'
                duration = info.get('duration')
                views = info.get('view_count')
                webpage = info.get('webpage_url') or f"https://www.youtube.com/watch?v={info.get('id', '')}"
                abr = info.get('abr') or qual_config['bitrate']
                acodec = info.get('acodec') or 'aac/opus'
                ext = info.get('ext') or 'm4a'
                
                return {
                    'id': info.get('id', ''),
                    'title': title,
                    'uploader': uploader,
                    'duration': duration,
                    'duration_str': format_duration(duration),
                    'views': views,
                    'views_str': format_views(views),
                    'url': webpage,
                    'audio_url': audio_url,
                    'quality': quality,
                    'quality_label': qual_config['label'],
                    'bitrate': f"{abr}kbps" if isinstance(abr, (int, float)) else str(abr),
                    'acodec': acodec,
                    'ext': ext
                }
    except Exception as e:
        print(f"[MUSIC ENGINE] extract_audio_info module error: {e}")

    # Fallback via subprocess CLI
    try:
        cmd = [
            "yt-dlp",
            "-j",
            "-f", fmt,
            search_target
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode == 0 and proc.stdout:
            info = json.loads(proc.stdout)
            audio_url = info.get('url', '')
            title = info.get('title', 'Unknown Track')
            uploader = info.get('uploader') or info.get('channel') or 'Unknown'
            duration = info.get('duration')
            views = info.get('view_count')
            webpage = info.get('webpage_url') or f"https://www.youtube.com/watch?v={info.get('id', '')}"
            abr = info.get('abr') or qual_config['bitrate']
            acodec = info.get('acodec') or 'aac/opus'
            ext = info.get('ext') or 'm4a'

            return {
                'id': info.get('id', ''),
                'title': title,
                'uploader': uploader,
                'duration': duration,
                'duration_str': format_duration(duration),
                'views': views,
                'views_str': format_views(views),
                'url': webpage,
                'audio_url': audio_url,
                'quality': quality,
                'quality_label': qual_config['label'],
                'bitrate': f"{abr}kbps" if isinstance(abr, (int, float)) else str(abr),
                'acodec': acodec,
                'ext': ext
            }
    except Exception as e:
        print(f"[MUSIC ENGINE] extract_audio_info subprocess error: {e}")

    return None

# --- Text Command Handlers ---

def handle_music_search(bot, token, channel_id, args, state, author_id):
    """
    Text Command: .msearch <query> [page]
    Searches YouTube for tracks using yt-dlp and lists results for text-based selection.
    """
    prefix = state.get("prefix", ".")
    query = ""
    page = 1

    if len(args) > 1:
        if len(args) > 2 and args[-1].isdigit():
            page = int(args[-1])
            query = " ".join(args[1:-1]).strip()
        elif len(args) == 2 and args[1].isdigit():
            page = int(args[1])
            query = ""
        else:
            query = " ".join(args[1:]).strip()
            page = 1

    if not query:
        lines = [
            "YT-DLP MUSIC SEARCH ENGINE",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}msearch <song / artist query> [page]",
            f"Select: {prefix}mselect <1-10>",
            "Examples:",
            f"  {prefix}msearch lofi beats",
            f"  {prefix}msearch alan walker faded",
            f"  {prefix}mselect 1",
            "──────────────────────────────────────────",
            "Quality: Set quality via .mquality <best|high|medium|low>"
        ]
        text_msg = (
            f"**[ YT-DLP MUSIC SEARCH ENGINE ]**\n"
            f"Search YouTube music tracks directly using text commands.\n\n"
            f"**Usage:**\n"
            f"- `{prefix}msearch <song / artist query>` — Search YouTube music\n"
            f"- `{prefix}mselect <number>` — Select & play track from search results\n"
            f"- `{prefix}mquality <best|high|medium|low>` — Change audio quality setting"
        )
        return lines, "MUSIC SEARCH ENGINE GUIDE", text_msg

    results = perform_yt_music_search(query, max_results=10)
    if not results:
        lines = [
            f"Music Search: \"{query[:25]}\"",
            "──────────────────────────────────────────",
            "Status: NO MUSIC RESULTS FOUND",
            "Try adjusting your song name or artist query."
        ]
        text_msg = f"❌ No music tracks found on YouTube for `{query}`. Try refining your query."
        return lines, "MUSIC SEARCH FAILED", text_msg

    # Save to user's search session cache for .mselect command
    LAST_MUSIC_SEARCH[(channel_id, author_id)] = results

    total_results = len(results)
    per_page = 5
    total_pages = max(1, math.ceil(total_results / per_page))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_items = results[start_idx:end_idx]

    lines = [
        f"Search: \"{query[:25]}\" | Tracks: {total_results}",
        f"Page: {page}/{total_pages} | yt-dlp Music Engine",
        "──────────────────────────────────────────"
    ]
    for idx, item in enumerate(page_items, start=start_idx + 1):
        lines.append(f"{idx}. {item['title'][:38]}")
        lines.append(f"   By: {item['uploader'][:20]} | Dur: {item['duration_str']}")

    lines.append("──────────────────────────────────────────")
    lines.append(f"Select track: {prefix}mselect <1-{total_results}>")

    text_lines = [
        f"🎵 **[ YT-DLP MUSIC SEARCH — \"{query}\" ]**",
        f"Found **{total_results}** tracks on YouTube (Page **{page}/{total_pages}**):\n"
    ]
    for idx, item in enumerate(page_items, start=start_idx + 1):
        text_lines.append(
            f"**{idx}. [{item['title']}]({item['url']})**\n"
            f"> 👤 **Artist:** `{item['uploader']}` | ⏱️ **Duration:** `{item['duration_str']}` | 👁️ **Views:** `{item['views_str']}`"
        )

    text_lines.append(f"\n💡 **To Play a Track:** Type `{prefix}mselect <number>` (e.g. `{prefix}mselect 1`) or `{prefix}mplay <url>`.")
    text_msg = "\n".join(text_lines)

    return lines, f"MUSIC SEARCH: \"{query[:20].upper()}\"", text_msg

def handle_music_select(bot, token, channel_id, args, state, author_id):
    """
    Text Command: .mselect <number>
    Selects a track from the user's last .msearch results and queues/plays it.
    """
    prefix = state.get("prefix", ".")
    if len(args) < 2 or not args[1].isdigit():
        lines = [
            "MUSIC TRACK SELECTION",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}mselect <track_number>",
            "Example:",
            f"  {prefix}mselect 1",
            "──────────────────────────────────────────",
            f"Run {prefix}msearch <query> first to search songs."
        ]
        text_msg = f"⚠️ Please specify a track number to select. Usage: `{prefix}mselect <1-10>`"
        return lines, "MUSIC SELECT ERROR", text_msg

    idx = int(args[1]) - 1
    last_results = LAST_MUSIC_SEARCH.get((channel_id, author_id))
    if not last_results:
        lines = [
            "MUSIC SELECT EXPIRED",
            "──────────────────────────────────────────",
            "No active search session found.",
            f"Run {prefix}msearch <query> first to search tracks."
        ]
        text_msg = f"❌ No recent music search found. Please search for music first using `{prefix}msearch <query>`."
        return lines, "NO SEARCH SESSION", text_msg

    if idx < 0 or idx >= len(last_results):
        lines = [
            "INVALID TRACK NUMBER",
            "──────────────────────────────────────────",
            f"Selected track #{idx + 1} is out of range.",
            f"Valid range: 1 to {len(last_results)}"
        ]
        text_msg = f"⚠️ Invalid selection #{idx + 1}. Please choose a number between 1 and {len(last_results)}."
        return lines, "INVALID TRACK INDEX", text_msg

    selected = last_results[idx]
    # Play selected track using handle_music_play logic
    return handle_music_play(bot, token, channel_id, [prefix + "mplay", selected['url']], state, author_id)

def handle_music_play(bot, token, channel_id, args, state, author_id):
    """
    Text Command: .mplay <query or URL> / .play <query or URL>
    Fetches track info via yt-dlp, applies quality setting, and adds to queue.
    """
    prefix = state.get("prefix", ".")
    if len(args) < 2:
        lines = [
            "MUSIC PLAYER ENGINE",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}mplay <song name or YouTube URL>",
            "Examples:",
            f"  {prefix}mplay lofi hip hop beats",
            f"  {prefix}mplay https://youtu.be/dQw4w9WgXcQ",
            "──────────────────────────────────────────",
            f"Quality: {state.get('music_quality', 'high').upper()}"
        ]
        text_msg = (
            f"**[ MUSIC PLAYER ENGINE ]**\n"
            f"Syntax: `{prefix}mplay <song name or YouTube URL>`\n"
            f"Example: `{prefix}mplay faded alan walker` or `{prefix}play <link>`\n"
            f"Current Audio Quality: `{state.get('music_quality', 'high')}`"
        )
        return lines, "MUSIC PLAYER GUIDE", text_msg

    query = " ".join(args[1:]).strip()
    quality = state.get("music_quality", "high")

    track_info = extract_audio_info(query, quality=quality)
    if not track_info:
        lines = [
            f"Music Play: \"{query[:25]}\"",
            "──────────────────────────────────────────",
            "Status: FAILED TO EXTRACT AUDIO",
            "Verify URL or search terms and try again."
        ]
        text_msg = f"❌ Failed to extract audio for `{query}` using yt-dlp. Please check the song name or URL."
        return lines, "AUDIO EXTRACTION FAILED", text_msg

    # Manage Queue
    if channel_id not in MUSIC_QUEUE:
        MUSIC_QUEUE[channel_id] = {'queue': [], 'current': None, 'status': 'playing'}

    q_data = MUSIC_QUEUE[channel_id]
    q_data['queue'].append(track_info)

    pos = len(q_data['queue'])
    is_now_playing = (pos == 1 and q_data['current'] is None)

    if is_now_playing:
        q_data['current'] = q_data['queue'].pop(0)
        q_data['status'] = 'playing'

    current_track = q_data['current'] if is_now_playing else track_info

    lines = [
        f"🎵 {'NOW PLAYING' if is_now_playing else 'ADDED TO QUEUE'}",
        "──────────────────────────────────────────",
        f"Title: {current_track['title'][:35]}",
        f"Artist: {current_track['uploader'][:25]}",
        f"Duration: {current_track['duration_str']} | Bitrate: {current_track['bitrate']}",
        f"Quality: {current_track['quality_label']}",
        "──────────────────────────────────────────",
        f"Queue Pos: {'Now Playing (#1)' if is_now_playing else f'Position #{pos}'}"
    ]

    text_lines = [
        f"🎵 **[{'NOW PLAYING' if is_now_playing else 'ADDED TO QUEUE'}]**",
        f"**Track:** [{current_track['title']}]({current_track['url']})",
        f"> 👤 **Artist:** `{current_track['uploader']}`",
        f"> ⏱️ **Duration:** `{current_track['duration_str']}` | 👁️ **Views:** `{current_track['views_str']}`",
        f"> 🎚️ **Audio Quality:** `{current_track['quality_label']}` (`{current_track['bitrate']}`)",
        f"> 📁 **Codec/Format:** `{current_track['acodec']}` / `.{current_track['ext']}`",
    ]

    if current_track.get('audio_url'):
        text_lines.append(f"> 🔗 **Direct Stream URL:** [Click to Listen/Download Stream]({current_track['audio_url']})")

    if not is_now_playing:
        text_lines.append(f"\n📌 Queue Position: **#{pos}** | Use `{prefix}mqueue` to view the playlist.")
    else:
        text_lines.append(f"\n▶️ Playing live track. Type `{prefix}mstop` to stop or `{prefix}mqueue` for queue.")

    text_msg = "\n".join(text_lines)
    card_title = f"{'PLAYING' if is_now_playing else 'QUEUED'}: {current_track['title'][:20].upper()}"

    return lines, card_title, text_msg

def handle_music_quality(bot, token, channel_id, args, state, update_state_func):
    """
    Text Command: .mquality [best|320k|high|192k|medium|128k|low|64k]
    Views or sets preferred yt-dlp audio quality format.
    """
    prefix = state.get("prefix", ".")
    current_q = state.get("music_quality", "high").lower()

    if len(args) < 2:
        lines = [
            "AUDIO QUALITY CONFIGURATION",
            "──────────────────────────────────────────",
            f"Current Quality: {current_q.upper()}",
            "Available Quality Options:",
            "  1. best / 320k   - Lossless Ultra (320 kbps)",
            "  2. high / 192k   - High Quality (192 kbps) [Default]",
            "  3. medium / 128k - Standard Quality (128 kbps)",
            "  4. low / 64k     - Low / Data Saver (64 kbps)",
            "──────────────────────────────────────────",
            f"Set syntax: {prefix}mquality <option>"
        ]

        text_msg = (
            f"🎚️ **[ AUDIO QUALITY CONFIGURATION ]**\n"
            f"Current Quality Setting: `{current_q.upper()}` ({QUALITY_SETTINGS.get(current_q, {}).get('label', 'Default')})\n\n"
            f"**Available Quality Presets:**\n"
            f"• `best` or `320k` — 320kbps Lossless Ultra Quality\n"
            f"• `high` or `192k` — 192kbps High Quality *(Default)*\n"
            f"• `medium` or `128k` — 128kbps Standard Quality\n"
            f"• `low` or `64k` — 64kbps Low / Mobile Data Saver\n\n"
            f"*To change quality, type `{prefix}mquality <preset>` (e.g. `{prefix}mquality best`)*"
        )
        return lines, "AUDIO QUALITY SETTINGS", text_msg

    new_q = args[1].lower()
    if new_q not in QUALITY_SETTINGS:
        lines = [
            "INVALID QUALITY PRESET",
            "──────────────────────────────────────────",
            f"Unknown preset: '{new_q}'",
            "Valid Options: best, 320k, high, 192k, medium, 128k, low, 64k"
        ]
        text_msg = f"❌ Invalid quality preset `{new_q}`. Choose from: `best`, `320k`, `high`, `192k`, `medium`, `128k`, `low`, `64k`."
        return lines, "INVALID QUALITY PRESET", text_msg

    # Persist updated setting
    update_state_func(token, {"music_quality": new_q})
    q_info = QUALITY_SETTINGS[new_q]

    lines = [
        "AUDIO QUALITY UPDATED",
        "──────────────────────────────────────────",
        f"New Quality: {new_q.upper()}",
        f"Description: {q_info['label']}",
        f"Target Bitrate: {q_info['bitrate']}",
        "──────────────────────────────────────────",
        "Setting saved persistently to config."
    ]

    text_msg = (
        f"✅ **Audio Quality Updated to `{new_q.upper()}`!**\n"
        f"• **Label:** `{q_info['label']}`\n"
        f"• **Target Bitrate:** `{q_info['bitrate']}`\n"
        f"• *Future `{prefix}mplay` extractions will use this quality profile.*"
    )

    return lines, "QUALITY UPDATED", text_msg

def handle_music_info(bot, token, channel_id, args, state):
    """
    Text Command: .minfo <query or URL>
    Fetches detailed technical audio specs and qualities for a YouTube track using yt-dlp.
    """
    prefix = state.get("prefix", ".")
    if len(args) < 2:
        lines = [
            "TRACK MEDIA INFO EXAMINER",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}minfo <song name or URL>",
            "Example:",
            f"  {prefix}minfo https://youtu.be/dQw4w9WgXcQ",
            "──────────────────────────────────────────",
            "Shows exact codecs, bitrates & audio formats."
        ]
        text_msg = f"ℹ️ Please provide a song name or URL. Usage: `{prefix}minfo <query or URL>`"
        return lines, "MEDIA INFO GUIDE", text_msg

    query = " ".join(args[1:]).strip()
    quality = state.get("music_quality", "high")
    info = extract_audio_info(query, quality=quality)

    if not info:
        lines = [
            f"Media Info: \"{query[:25]}\"",
            "──────────────────────────────────────────",
            "Status: UNABLE TO INSPECT MEDIA",
            "Verify URL or query terms."
        ]
        text_msg = f"❌ Unable to retrieve media details for `{query}`."
        return lines, "MEDIA INSPECTION FAILED", text_msg

    lines = [
        f"TRACK INFO: {info['title'][:30]}",
        "──────────────────────────────────────────",
        f"Artist: {info['uploader'][:25]}",
        f"Duration: {info['duration_str']} | Views: {info['views_str']}",
        f"Codec: {info['acodec']} | Ext: .{info['ext']}",
        f"Bitrate: {info['bitrate']} | Profile: {info['quality_label']}",
        "──────────────────────────────────────────",
        f"URL: {info['url'][:40]}"
    ]

    text_msg = (
        f"🔍 **[ MEDIA TRACK TECHNICAL DETAILS ]**\n"
        f"• **Title:** [{info['title']}]({info['url']})\n"
        f"• **Artist/Channel:** `{info['uploader']}`\n"
        f"• **Duration:** `{info['duration_str']}`\n"
        f"• **View Count:** `{info['views_str']}`\n"
        f"• **Audio Codec:** `{info['acodec']}`\n"
        f"• **Audio Extension:** `.{info['ext']}`\n"
        f"• **Extracted Bitrate:** `{info['bitrate']}`\n"
        f"• **Active Profile:** `{info['quality_label']}`\n"
        f"• 🔗 **Direct Stream URL:** [Audio Link]({info['audio_url']})"
    )

    return lines, f"MEDIA INFO: {info['title'][:20].upper()}", text_msg

def handle_music_queue(bot, token, channel_id, args, state):
    """
    Text Command: .mqueue / .queue
    Displays the active music queue for the current channel.
    """
    prefix = state.get("prefix", ".")
    q_data = MUSIC_QUEUE.get(channel_id, {'queue': [], 'current': None, 'status': 'idle'})

    current = q_data.get('current')
    queue_list = q_data.get('queue', [])

    if not current and not queue_list:
        lines = [
            "MUSIC QUEUE — CHANNEL PLAYLIST",
            "──────────────────────────────────────────",
            "Status: QUEUE IS CURRENTLY EMPTY",
            f"Add music: {prefix}mplay <song name or url>",
            f"Search music: {prefix}msearch <query>"
        ]
        text_msg = f"🎵 **[ MUSIC QUEUE ]**\nThe music queue is currently empty.\nUse `{prefix}mplay <song name>` or `{prefix}msearch <query>` to add tracks!"
        return lines, "MUSIC QUEUE EMPTY", text_msg

    lines = [
        "MUSIC QUEUE — CHANNEL PLAYLIST",
        "──────────────────────────────────────────"
    ]

    if current:
        lines.append(f"▶ NOW PLAYING: {current['title'][:32]}")
        lines.append(f"  Artist: {current['uploader'][:20]} | Dur: {current['duration_str']}")
        lines.append("──────────────────────────────────────────")

    if queue_list:
        lines.append(f"UP NEXT ({len(queue_list)} track(s)):")
        for idx, track in enumerate(queue_list[:5], start=1):
            lines.append(f"{idx}. {track['title'][:35]} ({track['duration_str']})")
        if len(queue_list) > 5:
            lines.append(f"... and {len(queue_list) - 5} more tracks.")
    else:
        lines.append("Up Next: No remaining queued tracks.")

    lines.append("──────────────────────────────────────────")
    lines.append(f"Stop: {prefix}mstop | Skip: {prefix}skip")

    text_lines = [
        f"🎶 **[ MUSIC QUEUE & PLAYLIST ]**\n"
    ]
    if current:
        text_lines.append(
            f"▶️ **Now Playing:** [{current['title']}]({current['url']})\n"
            f"> 👤 Artist: `{current['uploader']}` | ⏱️ Duration: `{current['duration_str']}` | 🎚️ `{current['bitrate']}`\n"
        )
    if queue_list:
        text_lines.append(f"📋 **Up Next ({len(queue_list)} tracks):**")
        for idx, track in enumerate(queue_list[:10], start=1):
            text_lines.append(f"**{idx}.** [{track['title']}]({track['url']}) (`{track['duration_str']}`) by `{track['uploader']}`")
    else:
        text_lines.append("📋 **Up Next:** No queued tracks.")

    text_lines.append(f"\n💡 *Type `{prefix}mstop` to clear queue, `{prefix}skip` to skip track.*")
    text_msg = "\n".join(text_lines)

    return lines, "MUSIC QUEUE", text_msg

def handle_music_stop(bot, token, channel_id, state):
    """
    Text Command: .mstop / .stopmusic
    Clears current channel queue and resets playback state.
    """
    prefix = state.get("prefix", ".")
    if channel_id in MUSIC_QUEUE:
        del MUSIC_QUEUE[channel_id]

    lines = [
        "MUSIC ENGINE HALTED",
        "──────────────────────────────────────────",
        "Status: PLAYBACK STOPPED & QUEUE CLEARED",
        f"Play again: {prefix}mplay <song>"
    ]
    text_msg = f"⏹️ **Music Playback Halted!** Queue cleared and music engine reset for this channel."
    return lines, "MUSIC STOPPED", text_msg

def handle_music_skip(bot, token, channel_id, state):
    """
    Text Command: .skip
    Skips current playing song to the next song in the queue.
    """
    prefix = state.get("prefix", ".")
    q_data = MUSIC_QUEUE.get(channel_id)
    if not q_data or (not q_data.get('current') and not q_data.get('queue')):
        lines = [
            "SKIP TRACK",
            "──────────────────────────────────────────",
            "Status: NO ACTIVE TRACK TO SKIP"
        ]
        text_msg = f"⚠️ Nothing is currently playing to skip."
        return lines, "SKIP TRACK", text_msg

    old_track = q_data.get('current')
    if q_data.get('queue'):
        q_data['current'] = q_data['queue'].pop(0)
        new_track = q_data['current']
        lines = [
            "TRACK SKIPPED",
            "──────────────────────────────────────────",
            f"Skipped: {old_track['title'][:30] if old_track else 'Track'}",
            f"▶ Now Playing: {new_track['title'][:30]}"
        ]
        text_msg = f"⏭️ **Skipped track!** Now playing: **[{new_track['title']}]({new_track['url']})** (`{new_track['duration_str']}`)."
    else:
        q_data['current'] = None
        q_data['status'] = 'idle'
        lines = [
            "TRACK SKIPPED",
            "──────────────────────────────────────────",
            "Queue finished. No more tracks."
        ]
        text_msg = f"⏭️ **Skipped track!** Queue is now empty."

    return lines, "TRACK SKIPPED", text_msg

def handle_vcmusic(bot, token, channel_id, args, state):
    """
    Text Command: .vcmusic <query or URL>
    Voice channel audio stream extractor using yt-dlp.
    """
    prefix = state.get("prefix", ".")
    if len(args) < 2:
        lines = [
            "VOICE CHANNEL MUSIC STREAMER",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}vcmusic <song name or URL>",
            "Examples:",
            f"  {prefix}vcmusic lofi beats 24/7",
            f"  {prefix}vcmusic https://youtu.be/5qap5aO4i9A",
            "──────────────────────────────────────────",
            "Extracts raw voice channel Opus/AAC streams."
        ]
        text_msg = (
            f"🎙️ **[ VOICE CHANNEL MUSIC EXTRACTOR ]**\n"
            f"Syntax: `{prefix}vcmusic <song name or YouTube URL>`\n"
            f"Example: `{prefix}vcmusic lofi beats` or `{prefix}vcmusic <url>`\n"
            f"Extracts direct low-latency Opus/AAC voice streams via `yt-dlp`."
        )
        return lines, "VC MUSIC GUIDE", text_msg

    query = " ".join(args[1:]).strip()
    quality = state.get("music_quality", "high")
    info = extract_audio_info(query, quality=quality)

    if not info:
        lines = [
            f"VC Music: \"{query[:25]}\"",
            "──────────────────────────────────────────",
            "Status: STREAM EXTRACTION FAILED",
            "Verify URL or search terms."
        ]
        text_msg = f"❌ Unable to extract voice stream for `{query}`."
        return lines, "VC STREAM FAILED", text_msg

    lines = [
        f"🎙️ VC STREAM: {info['title'][:30]}",
        "──────────────────────────────────────────",
        f"Artist: {info['uploader'][:22]}",
        f"Duration: {info['duration_str']} | Bitrate: {info['bitrate']}",
        f"Codec: {info['acodec']} | Format: .{info['ext']}",
        "──────────────────────────────────────────",
        "Voice Channel Stream Ready!"
    ]

    text_msg = (
        f"🎙️ **[ VOICE CHANNEL AUDIO STREAM READY ]**\n"
        f"• **Title:** [{info['title']}]({info['url']})\n"
        f"• **Artist:** `{info['uploader']}`\n"
        f"• **Duration:** `{info['duration_str']}` | **Views:** `{info['views_str']}`\n"
        f"• **Voice Codec:** `{info['acodec']}` ({info['bitrate']})\n"
        f"• 🔊 **Direct Voice Stream Link:** [Listen Voice Audio Stream]({info['audio_url']})"
    )

    return lines, f"VC STREAM: {info['title'][:20].upper()}", text_msg

def handle_vcvideo(bot, token, channel_id, args, state):
    """
    Text Command: .vcvideo <query or URL>
    Voice video / stream format inspector using yt-dlp.
    """
    prefix = state.get("prefix", ".")
    if len(args) < 2:
        lines = [
            "VOICE VIDEO STREAM INSPECTOR",
            "──────────────────────────────────────────",
            f"Syntax: {prefix}vcvideo <query or URL>",
            "Examples:",
            f"  {prefix}vcvideo 4k nature relaxation",
            f"  {prefix}vcvideo https://youtu.be/dQw4w9WgXcQ",
            "──────────────────────────────────────────",
            "Inspects video/audio codecs for streaming."
        ]
        text_msg = (
            f"📹 **[ VOICE VIDEO STREAM INSPECTOR ]**\n"
            f"Syntax: `{prefix}vcvideo <query or YouTube URL>`\n"
            f"Inspects video stream resolutions, codecs, and direct media URLs via `yt-dlp`."
        )
        return lines, "VC VIDEO GUIDE", text_msg

    query = " ".join(args[1:]).strip()
    quality = state.get("music_quality", "high")
    info = extract_audio_info(query, quality=quality)

    if not info:
        lines = [
            f"VC Video: \"{query[:25]}\"",
            "──────────────────────────────────────────",
            "Status: VIDEO EXTRACTION FAILED"
        ]
        text_msg = f"❌ Unable to extract video stream info for `{query}`."
        return lines, "VC VIDEO FAILED", text_msg

    lines = [
        f"📹 VC VIDEO: {info['title'][:30]}",
        "──────────────────────────────────────────",
        f"Channel: {info['uploader'][:22]}",
        f"Duration: {info['duration_str']} | Views: {info['views_str']}",
        f"Audio Codec: {info['acodec']}",
        "──────────────────────────────────────────",
        "Video Stream Spec Ready!"
    ]

    text_msg = (
        f"📹 **[ VOICE VIDEO MEDIA INSPECTED ]**\n"
        f"• **Title:** [{info['title']}]({info['url']})\n"
        f"• **Channel:** `{info['uploader']}`\n"
        f"• **Duration:** `{info['duration_str']}` | **Views:** `{info['views_str']}`\n"
        f"• **Codec:** `{info['acodec']}` | **Profile:** `{info['quality_label']}`\n"
        f"• 🎬 **Direct Stream URL:** [Access Media Stream]({info['audio_url']})"
    )

    return lines, f"VC VIDEO: {info['title'][:20].upper()}", text_msg

