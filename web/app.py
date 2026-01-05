from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS
from sqlalchemy.orm import Session
import os

from bot.database import get_db, Chat, Message
from bot.config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY or os.urandom(24)
CORS(app)

# Healthcheck endpoint ДОЛЖЕН БЫТЬ ПЕРВЫМ
@app.route('/')
def healthcheck():
    """Простой healthcheck для Railway"""
    try:
        # Проверка подключения к БД
        with get_db() as db:
            db.execute("SELECT 1")
        return jsonify({"status": "healthy", "service": "chat-clone-bot"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Панель управления"""
    try:
        with get_db() as db:
            chats = db.query(Chat).order_by(Chat.created_at.desc()).limit(10).all()
            total_messages = db.query(Message).count()
            
        return render_template('index.html', 
                             chats=chats,
                             total_messages=total_messages)
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

# Остальные маршруты...
@app.route('/api/health')
def api_health():
    """API healthcheck"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "chat-clone-bot-api"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)