# ⚡ Telegram Auto-Reaction Bot Service

An automated Telegram Channel Auto-Reaction Bot built in Python. Supports single or multi-bot setups to automatically add customizable emoji reactions to every new post published in your Telegram channels.

---

## ✨ Features

- ⚡ **Instant / Delayed Auto-Reactions**: Automatically reacts to any new channel post (text, photo, video, document, poll, etc.).
- 🤖 **Multi-Bot Support**: Add 1 or multiple bot tokens! If you add 3 bots as admins, every post gets 3 automatic reactions!
- 🎭 **Customizable Reaction Pools**: Pick from any allowed Telegram reaction emojis (`👍`, `❤️`, `🔥`, `🎉`, `🤩`, `👏`, `⚡`, `🥰`, `💯`, etc.).
- 🔀 **Random or Fixed Modes**: Randomly pick emojis per post or use fixed sets.
- 💬 **Telegram PM Admin Commands**: Control reactions, switch modes, and view stats directly inside Telegram PM.
- 💻 **Modern Web Dashboard**: Glassmorphism dark-mode UI at `http://localhost:5000` for live activity logs, stats, and real-time settings.

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

### 3️⃣ Configure `.env` or Web Dashboard
Open `.env` in this directory and paste your bot token:
```env
BOT_TOKENS=YOUR_BOT_TOKEN_HERE
```
*(If using multiple bots, separate tokens with commas)*.

### 4️⃣ Run the Service

You have 3 flexible ways to run:

#### Option A: Run Both Web Dashboard & Bot Script together (Recommended)
This starts both the Telegram bot reaction engine in the background and launches the web dashboard at `http://localhost:5000`:
```bash
python main.py
```
Open **`http://localhost:5000`** in your browser to view logs, monitor reactions, and configure settings live!

#### Option B: Run Script Only (Console Mode, No Web UI)
If you are running on a lightweight server or VPS and do not need the web dashboard:
```bash
python main.py --no-web
```

#### Option C: Run Web Dashboard Only
If you only want to access the Web UI dashboard:
```bash
python web.py
```
*(or `python main.py --web-only`)*

---

## 🛠 Admin Commands (In Telegram PM)

- `/start` or `/help` - View status and list of commands.
- `/status` - View total posts processed, reactions sent, uptime, and active bots.
- `/setemojis 👍 ❤️ 🔥 🎉 🤩 ⚡` - Update active emoji pool dynamically.
- `/mode random` or `/mode fixed` - Toggle between random selection or fixed emoji.
- `/test` - Send a test reaction.
