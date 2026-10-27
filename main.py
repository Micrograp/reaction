import asyncio
import sys
import config
import bot_engine

# Ensure UTF-8 output encoding for console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def main():
    print("=" * 60)
    print("⚡ TELEGRAM AUTO-REACTION BOT SERVICE STARTING... ⚡")
    print("=" * 60)

    tokens = config.get_bot_tokens()
    if tokens:
        await bot_engine.start_all_bots()
    else:
        print("\n⚠️ WARNING: No BOT_TOKENS configured!")
        print("Please configure BOT_TOKENS in environment variables or via Telegram.\n")

    # Main loop: keep service alive and handle hot-reload requests from Telegram commands
    try:
        while True:
            if bot_engine.state.restart_requested:
                bot_engine.state.restart_requested = False
                print("\n🔄 Hot-reloading bot instances...")
                await bot_engine.stop_all_bots()

                new_tokens = config.get_bot_tokens()
                if new_tokens:
                    await bot_engine.start_all_bots()
                else:
                    bot_engine.log_event("WARNING", "No tokens configured after reload.")

            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nShutting down Telegram Auto-Reaction Bot Service...")
        await bot_engine.stop_all_bots()
        print("Service stopped cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
