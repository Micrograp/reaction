import asyncio
import threading
import sys
import time
import signal

# Ensure UTF-8 output encoding for Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import bot_engine
import web

def start_flask_thread(port):
    """Run Flask Web Server in a separate daemon thread."""
    bot_engine.log_event("INFO", f"Starting Web Dashboard at http://localhost:{port}")
    web.run_web_server(port=port)

async def main():
    print("=" * 60)
    print("⚡ TELEGRAM AUTO-REACTION BOT SERVICE STARTING... ⚡")
    print("=" * 60)

    no_web = "--no-web" in sys.argv
    web_only = "--web-only" in sys.argv

    # Start Flask Web Dashboard thread unless --no-web is passed
    if not no_web:
        web_port = int(config.os.getenv("PORT", config.os.getenv("WEB_PORT", "5000")))
        web_thread = threading.Thread(target=start_flask_thread, args=(web_port,), daemon=True)
        web_thread.start()

    # Initial bot startup unless --web-only is passed
    if not web_only:
        tokens = config.get_bot_tokens()
        if tokens:
            await bot_engine.start_all_bots()
        else:
            print("\n WARNING: No BOT_TOKENS found in .env file!")
            print(" Please open http://localhost:5000 in your browser or edit .env to add your Telegram Bot Token.\n")
    else:
        print("\n Running in WEB-ONLY mode (bots disabled).")
        print(f" Dashboard is live at http://localhost:{config.os.getenv('PORT', config.os.getenv('WEB_PORT', '5000'))}\n")

    # Main loop: watch for restart signals from the web dashboard
    try:
        while True:
            if bot_engine.state.restart_requested:
                bot_engine.state.restart_requested = False
                print("\n Reloading bot instances with new tokens...")

                # Stop all currently running bots
                await bot_engine.stop_all_bots()

                # Re-read tokens from env (updated by web UI) and start fresh
                new_tokens = config.get_bot_tokens()
                if new_tokens:
                    await bot_engine.start_all_bots()
                else:
                    bot_engine.log_event("WARNING", "No tokens configured after reload.")

            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n Shutting down Telegram Auto-Reaction Bot Service...")
        await bot_engine.stop_all_bots()
        print(" Service stopped cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
