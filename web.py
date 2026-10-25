import os
import functools
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

import config
import bot_engine

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY", "reaction-bot-secret-key-2026")

# Disable default werkzeug logging spam for clear terminal output
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"status": "error", "message": "Unauthorized. Please log in."}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return redirect(url_for("admin"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("admin"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        valid_user, valid_pwd = config.get_admin_credentials()
        
        if username == valid_user and password == valid_pwd:
            session["logged_in"] = True
            session["username"] = username
            bot_engine.log_event("AUTH", f"Admin user '{username}' logged in successfully.")
            return redirect(url_for("admin"))
        else:
            error = "Invalid username or password. Please try again."
            bot_engine.log_event("WARNING", f"Failed login attempt for username '{username}'")

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin():
    return render_template("index.html")

@app.route("/api/stats")
@login_required
def api_stats():
    uptime_secs = int((datetime.now() - bot_engine.state.start_time).total_seconds())
    hours, remainder = divmod(uptime_secs, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

    min_delay, max_delay = config.get_delay_range()

    return jsonify({
        "uptime": uptime_str,
        "active_bots": len(bot_engine.state.bot_info),
        "posts_processed": bot_engine.state.total_posts_processed,
        "reactions_sent": bot_engine.state.total_reactions_sent,
        "tokens": config.get_bot_tokens(),
        "mode": config.get_reaction_mode(),
        "emojis": config.get_reaction_emojis(),
        "min_delay": min_delay,
        "max_delay": max_delay,
        "bot_details": bot_engine.state.bot_info
    })

@app.route("/api/logs")
@login_required
def api_logs():
    return jsonify(bot_engine.state.recent_logs)

@app.route("/api/config", methods=["POST"])
@login_required
def api_config():
    data = request.json or {}
    mode = data.get("mode")
    emojis = data.get("emojis")
    min_d = data.get("min_delay")
    max_d = data.get("max_delay")

    if mode:
        config.update_env("REACTION_MODE", mode)
    if emojis:
        config.update_env("REACTION_EMOJIS", emojis)
    if min_d is not None:
        config.update_env("MIN_DELAY", str(min_d))
    if max_d is not None:
        config.update_env("MAX_DELAY", str(max_d))

    bot_engine.log_event("CONFIG", "Configuration updated via Web Dashboard")
    return jsonify({"status": "success", "message": "Settings saved successfully!"})

@app.route("/api/add_token", methods=["POST"])
@login_required
def api_add_token():
    data = request.json or {}
    new_token = data.get("token", "").strip()

    if not new_token:
        return jsonify({"status": "error", "message": "No token provided."})

    # Get existing tokens and add the new one
    existing = config.get_bot_tokens()
    if new_token in existing:
        return jsonify({"status": "error", "message": "This token is already added!"})

    existing.append(new_token)
    tokens_str = ",".join(existing)
    config.update_env("BOT_TOKENS", tokens_str)

    bot_engine.log_event("CONFIG", f"Added new bot token (Total: {len(existing)})")
    bot_engine.state.restart_requested = True

    return jsonify({
        "status": "success",
        "message": f"Bot token added! Starting bot... ({len(existing)} total)",
        "count": len(existing)
    })

@app.route("/api/remove_token", methods=["POST"])
@login_required
def api_remove_token():
    data = request.json or {}
    token_to_remove = data.get("token", "").strip()

    if not token_to_remove:
        return jsonify({"status": "error", "message": "No token provided."})

    existing = config.get_bot_tokens()
    if token_to_remove not in existing:
        return jsonify({"status": "error", "message": "Token not found."})

    existing.remove(token_to_remove)
    tokens_str = ",".join(existing) if existing else ""
    config.update_env("BOT_TOKENS", tokens_str)

    bot_engine.log_event("CONFIG", f"Removed bot token (Remaining: {len(existing)})")
    bot_engine.state.restart_requested = True

    return jsonify({
        "status": "success",
        "message": f"Bot removed. {len(existing)} bot(s) remaining.",
        "count": len(existing)
    })

@app.route("/api/save_tokens", methods=["POST"])
@login_required
def api_save_tokens():
    data = request.json or {}
    raw_tokens = data.get("tokens", "").strip()

    tokens_list = [t.strip() for t in raw_tokens.replace("\n", ",").split(",") if t.strip()]
    tokens_str = ",".join(tokens_list)

    config.update_env("BOT_TOKENS", tokens_str)
    bot_engine.log_event("CONFIG", f"Updated bot tokens (Count: {len(tokens_list)})")
    bot_engine.state.restart_requested = True

    return jsonify({
        "status": "success",
        "message": f"Saved {len(tokens_list)} token(s)! Restarting bot engine...",
        "count": len(tokens_list)
    })

def run_web_server(port=5000):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("WEB_PORT", "5000")))
    print(f"Starting Web Dashboard at http://localhost:{port}")
    run_web_server(port=port)
