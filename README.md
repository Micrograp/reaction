# ⚡ Telegram Auto-Reaction Bot Service

An automated Telegram Channel Auto-Reaction Bot built in Python. Supports single or multi-bot setups to automatically add customizable emoji reactions to every new post published in your Telegram channels.

---

## ✨ Features

- ⚡ **Instant / Delayed Auto-Reactions**: Automatically reacts to any new channel post (text, photo, video, document, poll, etc.).
- 🤖 **Multi-Bot Support**: Add 1 or multiple bot tokens! If you add 3 bots as admins, every post gets 3 automatic reactions with natural staggering!
- 🎭 **Customizable Reaction Pools**: Pick from any allowed Telegram reaction emojis (`👍`, `❤️`, `🔥`, `🎉`, `🤩`, `👏`, `⚡`, `🥰`, `💯`, etc.).
- 🔀 **Random or Fixed Modes**: Randomly pick emojis per post or use fixed sets.
- 💬 **Full Telegram Admin Controls**: Configure everything directly from Telegram private chat (PM) — no website or port needed!

---

## 🛠 Admin Telegram Commands

You can control all aspects of the bot directly in a private chat with any of your bots:

| Command | Description | Example |
| :--- | :--- | :--- |
| `/status` | View service statistics, uptime, and current settings | `/status` |
| `/setemojis` | Set allowed reaction emojis pool | `/setemojis 😁 🔥 👍 ❤️` |
| `/mode` | Switch reaction mode (`random` or `fixed`) | `/mode random` |
| `/setdelay` | Set delay range in seconds (`0` for instant) | `/setdelay 0` or `/setdelay 1 3` |
| `/bots` | List all active bots with usernames | `/bots` |
| `/addbot` | Add a new bot token and hot-reload | `/addbot 123456:ABC-DEF...` |
| `/delbot` | Remove a bot by its list number | `/delbot 2` |
| `/test` | Test if the bot can add a reaction | `/test` |
| `/myid` | View your Telegram numeric user ID | `/myid` |
| `/help` | View help and command list | `/help` |

---

## 🚀 Quick Setup & Usage

### 1️⃣ Get your Bot Token(s) from Telegram
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to create your bot.
3. Copy the **HTTP API Token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 2️⃣ Add Bot to your Telegram Channel
1. Open your Telegram Channel.
2. Go to **Channel Settings** ➡️ **Administrators** ➡️ **Add Admin**.
3. Search for your bot username and add it as an **Admin**.
4. Make sure the bot has permission to **Post Messages** or **Edit Messages**.

### 3️⃣ Configure Environment Variables
Set your variables in `.env` (or in your cloud hosting dashboard):
```env
BOT_TOKENS=YOUR_BOT_TOKEN_HERE
ADMIN_ID=YOUR_TELEGRAM_USER_ID
REACTION_EMOJIS=😁
REACTION_MODE=random
MIN_DELAY=0
MAX_DELAY=0
```

### 4️⃣ Run the Service
```bash
python main.py
```
Or run with Docker:
```bash
docker compose up -d
```
