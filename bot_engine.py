import asyncio
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Any

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError, RetryAfter

import config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("AutoReactionBot")

# In-memory Global Stats and Logs
class BotState:
    def __init__(self):
        self.start_time = datetime.now()
        self.total_posts_processed = 0
        self.total_reactions_sent = 0
        self.recent_logs: List[Dict[str, Any]] = []
        self.bot_info: List[Dict[str, Any]] = []
        self.active_applications: List[Application] = []
        self.restart_requested = False  # Flag set by web UI to trigger hot-reload

state = BotState()

def log_event(level: str, message: str, details: Dict[str, Any] = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "level": level,
        "message": message,
        "details": details or {},
    }
    state.recent_logs.insert(0, entry)
    # Keep last 100 log entries
    if len(state.recent_logs) > 100:
        state.recent_logs.pop()
    logger.info(f"[{level}] {message}")

def pick_emoji() -> str:
    emojis = config.get_reaction_emojis()
    mode = config.get_reaction_mode()
    if not emojis:
        return "👍"
    if mode == "random":
        return random.choice(emojis)
    else:
        # fixed mode: returns first emoji
        return emojis[0]

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered whenever a new post is published in any channel the bot is in."""
    post = update.channel_post or update.edited_channel_post or update.message
    if not post:
        return

    chat = post.chat
    chat_id = chat.id
    chat_title = chat.title or chat.username or str(chat_id)
    message_id = post.message_id
    bot_name = context.bot.first_name or context.bot.username or "Bot"

    state.total_posts_processed += 1

    # Identify bot index among active bots
    bot_index = 0
    try:
        active_ids = [b["id"] for b in state.bot_info]
        if context.bot.id in active_ids:
            bot_index = active_ids.index(context.bot.id)
    except Exception:
        bot_index = 0

    min_d, max_d = config.get_delay_range()
    
    # Base delay configured by user (0 if min_d == 0 and max_d == 0)
    base_delay = random.uniform(min_d, max_d) if max_d > 0 else 0.0
    
    # Multi-bot staggering so multiple bots don't react at the exact same millisecond
    if max_d > 0:
        stagger = random.uniform(min_d, max_d) if min_d > 0 else random.uniform(0.5, max(1.0, max_d))
        total_delay = base_delay + (bot_index * stagger)
    else:
        # Instant mode: subtle 0.25s micro-stagger to avoid Telegram rate limits
        total_delay = bot_index * 0.25

    if total_delay > 0:
        log_event("INFO", f"Bot [{bot_name}] waiting {total_delay:.1f}s before reacting to post #{message_id} in [{chat_title}]")
        await asyncio.sleep(total_delay)

    emoji = pick_emoji()

    # Try up to 3 times with retry on rate limit
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await context.bot.set_message_reaction(
                chat_id=chat_id,
                message_id=message_id,
                reaction=emoji
            )
            state.total_reactions_sent += 1
            log_event("SUCCESS", f"Bot [{bot_name}] reacted {emoji} to post #{message_id} in [{chat_title}]", {
                "bot": bot_name,
                "chat": chat_title,
                "message_id": message_id,
                "emoji": emoji
            })
            return  # Success, exit
        except RetryAfter as e:
            # Telegram rate limit - wait and retry
            wait_time = e.retry_after + 0.5
            log_event("WARNING", f"Bot [{bot_name}] rate limited, retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
        except TelegramError as e:
            err_msg = str(e)
            log_event("WARNING", f"Bot [{bot_name}] failed to react with {emoji} in [{chat_title}]: {err_msg}")
            # If specified emoji failed (e.g. not allowed by channel), try fallback emoji
            if emoji != "\U0001f44d" and attempt == 0:
                emoji = "\U0001f44d"  # Switch to thumbs up for next retry
                continue
            break

# --- Admin Telegram PM Commands ---

def is_admin(user_id: int) -> bool:
    admin_id = config.get_admin_id()
    return admin_id == 0 or user_id == admin_id

async def check_admin_or_reply(update: Update) -> bool:
    user_id = update.effective_user.id
    if is_admin(user_id):
        return True
    admin_id = config.get_admin_id()
    await update.message.reply_text(
        f"⛔ **Access Denied**\n\n"
        f"Only the administrator can control this bot.\n"
        f"Your Telegram User ID is: `{user_id}`\n\n"
        f"*(Configured ADMIN_ID: `{admin_id}`)*",
        parse_mode="Markdown"
    )
    return False

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot_name = context.bot.first_name
    emojis = " ".join(config.get_reaction_emojis())
    mode = config.get_reaction_mode()
    min_d, max_d = config.get_delay_range()
    
    text = (
        f"🤖 **Auto-Reaction Bot Service**\n"
        f"Hello {user.first_name}! I am **{bot_name}**.\n\n"
        f"✨ **Status**: Active & Online!\n"
        f"🎭 **Current Emojis**: {emojis}\n"
        f"⚙️ **Reaction Mode**: `{mode}`\n"
        f"⏱ **Delay**: `{min_d}s - {max_d}s`\n\n"
        f"📌 **How to use me**:\n"
        f"1. Add me to your Telegram Channel.\n"
        f"2. Make me an **Admin** with permission to post or edit messages.\n"
        f"3. Whenever you post in the channel, I will automatically add reactions!\n\n"
        f"🛠 **Admin Management Commands**:\n"
        f"• `/status` — View statistics & current settings\n"
        f"• `/setemojis 😁 🔥 👍` — Change reaction emojis pool\n"
        f"• `/mode random` or `/mode fixed` — Switch reaction mode\n"
        f"• `/setdelay 0` or `/setdelay 1 3` — Set reaction delay\n"
        f"• `/bots` — View all configured bots\n"
        f"• `/addbot <TOKEN>` — Add a new bot token\n"
        f"• `/delbot <#>` — Remove a bot by number\n"
        f"• `/test` — Test a reaction in this chat\n"
        f"• `/myid` — View your Telegram User ID"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    admin_id = config.get_admin_id()
    status = "Authorized Admin" if is_admin(user_id) else "Unauthorized"
    await update.message.reply_text(
        f"🆔 **Your Telegram User ID**: `{user_id}`\n"
        f"🔐 **Status**: {status}\n\n"
        f"*(Set `ADMIN_ID={user_id}` in your environment variables to restrict control)*",
        parse_mode="Markdown"
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    uptime_secs = int((datetime.now() - state.start_time).total_seconds())
    hours, remainder = divmod(uptime_secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    emojis = " ".join(config.get_reaction_emojis())
    mode = config.get_reaction_mode()
    min_d, max_d = config.get_delay_range()
    active_bots_count = len(config.get_bot_tokens())

    text = (
        f"📊 **Auto-Reaction Service Stats**\n\n"
        f"🤖 **Active Bots**: `{active_bots_count}`\n"
        f"⏱ **Uptime**: `{uptime_str}`\n"
        f"📥 **Channel Posts Processed**: `{state.total_posts_processed}`\n"
        f"❤️ **Reactions Sent**: `{state.total_reactions_sent}`\n\n"
        f"⚙️ **Configuration**:\n"
        f"• **Mode**: `{mode}`\n"
        f"• **Emoji Pool**: {emojis}\n"
        f"• **Delay Range**: `{min_d}s - {max_d}s`\n"
        f"• **Admin ID**: `{config.get_admin_id()}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_setemojis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    args = context.args
    if not args:
        current = " ".join(config.get_reaction_emojis())
        await update.message.reply_text(
            f"🎭 **Current Emojis**: {current}\n\n"
            f"Usage: `/setemojis 😁` or `/setemojis 👍 ❤️ 🔥 🎉`",
            parse_mode="Markdown"
        )
        return

    new_emojis = " ".join(args)
    config.update_env("REACTION_EMOJIS", new_emojis)
    log_event("CONFIG", f"Updated reaction emojis to: {new_emojis}")
    await update.message.reply_text(f"✅ Reaction emojis updated to: {new_emojis}")

async def cmd_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    args = context.args
    if not args or args[0].lower() not in ["random", "fixed"]:
        current = config.get_reaction_mode()
        await update.message.reply_text(
            f"⚙️ **Current Mode**: `{current}`\n\n"
            f"Usage:\n"
            f"• `/mode random` — Randomly picks an emoji per post\n"
            f"• `/mode fixed` — Uses fixed first emoji",
            parse_mode="Markdown"
        )
        return

    new_mode = args[0].lower()
    config.update_env("REACTION_MODE", new_mode)
    log_event("CONFIG", f"Updated reaction mode to: {new_mode}")
    await update.message.reply_text(f"✅ Reaction mode updated to: `{new_mode}`", parse_mode="Markdown")

async def cmd_setdelay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    args = context.args
    if not args:
        min_d, max_d = config.get_delay_range()
        await update.message.reply_text(
            f"⏱ **Current Delay**: `{min_d}s - {max_d}s`\n\n"
            f"Usage:\n"
            f"• `/setdelay 0` — Instant reactions (no delay)\n"
            f"• `/setdelay 2` — Exact 2s delay\n"
            f"• `/setdelay 1 3` — Random delay between 1s and 3s",
            parse_mode="Markdown"
        )
        return

    try:
        min_val = float(args[0])
        max_val = float(args[1]) if len(args) > 1 else min_val
        if min_val < 0 or max_val < 0:
            await update.message.reply_text("❌ Delay cannot be negative.")
            return
        if min_val > max_val:
            min_val, max_val = max_val, min_val

        config.update_env("MIN_DELAY", str(min_val))
        config.update_env("MAX_DELAY", str(max_val))
        log_event("CONFIG", f"Updated delay to: {min_val}s - {max_val}s")
        await update.message.reply_text(f"✅ Reaction delay set to: `{min_val}s - {max_val}s`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ Invalid numbers. Example: `/setdelay 0` or `/setdelay 1 3`", parse_mode="Markdown")

async def cmd_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    tokens = config.get_bot_tokens()
    if not tokens:
        await update.message.reply_text("⚠️ No bots currently configured. Use `/addbot <TOKEN>` to add one.")
        return

    lines = [f"🤖 **Configured Bots ({len(tokens)})**:\n"]
    for i, t in enumerate(tokens, 1):
        bot_label = f"Bot #{i}"
        if i - 1 < len(state.bot_info):
            b = state.bot_info[i - 1]
            bot_label = f"@{b['username']} ({b['first_name']})"
        masked = t[:8] + "..." + t[-4:]
        lines.append(f"{i}. **{bot_label}**\n   Token: `{masked}`")

    lines.append("\nCommands:")
    lines.append("• `/addbot <TOKEN>` — Add a new bot token")
    lines.append("• `/delbot <NUMBER>` — Remove a bot by its list number")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_addbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: `/addbot <BOT_TOKEN_FROM_BOTFATHER>`", parse_mode="Markdown")
        return

    new_token = args[0].strip()
    existing = config.get_bot_tokens()
    if new_token in existing:
        await update.message.reply_text("⚠️ This bot token is already added.")
        return

    existing.append(new_token)
    config.update_env("BOT_TOKENS", ",".join(existing))
    state.restart_requested = True
    log_event("CONFIG", f"Added bot token via Telegram PM. Total: {len(existing)}")
    await update.message.reply_text(f"✅ Bot token added! Reloading bot instances... (Total: {len(existing)})")

async def cmd_delbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin_or_reply(update):
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: `/delbot <NUMBER>` (use `/bots` to view numbers)", parse_mode="Markdown")
        return

    target = args[0].strip()
    existing = config.get_bot_tokens()
    token_to_remove = None

    if target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(existing):
            token_to_remove = existing[idx]

    if not token_to_remove:
        for t in existing:
            if target in t:
                token_to_remove = t
                break

    if not token_to_remove:
        await update.message.reply_text("❌ Bot not found. Use `/bots` to see the list of active bots.")
        return

    existing.remove(token_to_remove)
    config.update_env("BOT_TOKENS", ",".join(existing))
    state.restart_requested = True
    log_event("CONFIG", f"Removed bot token via Telegram PM. Remaining: {len(existing)}")
    await update.message.reply_text(f"✅ Bot removed! Reloading bot instances... ({len(existing)} remaining)")

async def cmd_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    emoji = pick_emoji()
    try:
        await context.bot.set_message_reaction(
            chat_id=msg.chat_id,
            message_id=msg.message_id,
            reaction=emoji
        )
        await msg.reply_text(f"✅ Reaction test successful! Added {emoji}")
    except Exception as e:
        await msg.reply_text(f"❌ Reaction test failed: {e}")

async def build_bot_app(token: str) -> Application:
    """Initialize a single bot Application instance."""
    app = Application.builder().token(token).build()

    # Get Bot details
    try:
        bot_info = await app.bot.get_me()
        state.bot_info.append({
            "id": bot_info.id,
            "username": bot_info.username,
            "first_name": bot_info.first_name,
            "status": "Online"
        })
        log_event("INFO", f"Bot initialized: @{bot_info.username} ({bot_info.first_name})")
    except Exception as e:
        log_event("ERROR", f"Failed to connect bot token {token[:10]}... : {e}")

    # Register admin commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("settings", cmd_status))
    app.add_handler(CommandHandler("setemojis", cmd_setemojis))
    app.add_handler(CommandHandler("mode", cmd_mode))
    app.add_handler(CommandHandler("setdelay", cmd_setdelay))
    app.add_handler(CommandHandler("delay", cmd_setdelay))
    app.add_handler(CommandHandler("bots", cmd_bots))
    app.add_handler(CommandHandler("addbot", cmd_addbot))
    app.add_handler(CommandHandler("delbot", cmd_delbot))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("test", cmd_test))

    # Channel Post & Message Listener
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, handle_channel_post))

    return app

async def start_all_bots():
    """Start all configured bots concurrently."""
    tokens = config.get_bot_tokens()
    if not tokens:
        log_event("WARNING", "No BOT_TOKENS set in .env! Please add a bot token in .env or Web UI.")
        return

    log_event("INFO", f"Starting {len(tokens)} Telegram Bot(s)...")
    
    for token in tokens:
        try:
            app = await build_bot_app(token)
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                allowed_updates=["channel_post", "edited_channel_post", "message"],
                drop_pending_updates=True,
                poll_interval=0.0,
                timeout=5
            )
            state.active_applications.append(app)
            log_event("SUCCESS", f"Bot started successfully!")
        except Exception as e:
            log_event("ERROR", f"Failed to start bot with token {token[:10]}...: {e}")
            # Try to clean up the failed app
            try:
                await app.shutdown()
            except Exception:
                pass

    started = len(state.active_applications)
    if started > 0:
        log_event("SUCCESS", f"{started} bot(s) are running and listening for channel posts!")
    else:
        log_event("WARNING", "No bots could be started. Check your tokens.")

async def stop_all_bots():
    """Stop all running bots."""
    for app in state.active_applications:
        try:
            if app.updater:
                await app.updater.stop()
            await app.stop()
            await app.shutdown()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    state.active_applications.clear()
    state.bot_info.clear()
    # Brief delay to let Telegram API release the polling sessions
    await asyncio.sleep(2)
