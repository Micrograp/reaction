import asyncio
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import config
import bot_engine

# Ensure UTF-8 output encoding for console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Minimal zero-dependency HTTP health check listener for cloud platforms."""
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        # Suppress log spam in console
        pass

def start_health_server(port: int):
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"📡 Internal health check responding on port {port}")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Health check server note: {e}")

async def main():
    print("=" * 60)
    print("⚡ TELEGRAM AUTO-REACTION BOT SERVICE STARTING... ⚡")
    print("=" * 60)

    # Start health check server on port requested by Inject Cloud / cloud host
    port_str = os.getenv("PORT", "4005")
    try:
        port = int(port_str)
        t = threading.Thread(target=start_health_server, args=(port,), daemon=True)
        t.start()
    except ValueError:
        pass

    tokens = config.get_bot_tokens()
    if tokens:
        await bot_engine.start_all_bots()
    else:
        print("\n⚠️ WARNING: No BOT_TOKENS configured!")
        print("Please configure BOT_TOKENS in environment variables.\n")

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
