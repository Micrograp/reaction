import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Standard Telegram reaction emojis supported by Bot API
ALLOWED_EMOJIS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱",
    "🤬", "😢", "🎉", "🤩", "🤮", "💩", "🙏", "👌", "🕊", "🤡",
    "🥱", "🥴", "😍", "🐳", "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡",
    "🍌", "🏆", "🍾", "🍓", "🍾", "🗿", "🎈"
]

def get_bot_tokens() -> list[str]:
    raw = os.getenv("BOT_TOKENS", "").strip()
    if not raw or raw == "YOUR_BOT_TOKEN_HERE":
        return []
    
    # Step 1: Split by common separators (comma, semicolon, whitespace, newline)
    chunks = [t.strip() for t in re.split(r'[,;\s\n]+', raw) if t.strip()]
    
    # Step 2: For any chunk that looks like concatenated tokens (multiple colons),
    # split at boundaries where a new bot token starts (7+ digits followed by colon)
    tokens = []
    for chunk in chunks:
        if chunk.count(':') > 1:
            # Split at zero-width positions before a new bot token (not preceded by a digit)
            parts = re.split(r'(?<!\d)(?=\d{7,}:)', chunk)
            tokens.extend([p for p in parts if p.strip()])
        else:
            tokens.append(chunk)
    
    # Step 3: Validate each token looks like a bot token (digits:characters)
    valid_tokens = [t for t in tokens if re.match(r'^\d+:[A-Za-z0-9_\-]+$', t)]
    
    # Deduplicate while preserving order
    seen = set()
    unique_tokens = []
    for t in valid_tokens:
        if t not in seen:
            seen.add(t)
            unique_tokens.append(t)
    return unique_tokens

def get_admin_id() -> int:
    try:
        return int(os.getenv("ADMIN_ID", "0"))
    except ValueError:
        return 0

def get_reaction_emojis() -> list[str]:
    raw = os.getenv("REACTION_EMOJIS", "👍 ❤️ 🔥 🎉 🤩 👏 ⚡").strip()
    # Find all emojis or split by space
    emojis = [e.strip() for e in raw.split() if e.strip()]
    return emojis if emojis else ["👍", "❤️", "🔥"]

def get_reaction_mode() -> str:
    mode = os.getenv("REACTION_MODE", "random").strip().lower()
    return mode if mode in ["random", "fixed"] else "random"

def get_delay_range() -> tuple[float, float]:
    try:
        min_d = float(os.getenv("MIN_DELAY", "0.5"))
        max_d = float(os.getenv("MAX_DELAY", "2.0"))
        return max(0.0, min_d), max(min_d, max_d)
    except ValueError:
        return 0.5, 2.0

def update_env(key: str, value: str):
    """Update a key in the .env file and in current os.environ."""
    os.environ[key] = value
    if not ENV_PATH.exists():
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")
        return

    content = ENV_PATH.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    if pattern.search(content):
        new_content = pattern.sub(f"{key}={value}", content)
    else:
        new_content = content + f"\n{key}={value}\n"
    
    ENV_PATH.write_text(new_content, encoding="utf-8")
