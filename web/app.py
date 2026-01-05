from flask import Flask, jsonify, render_template
from flask_cors import CORS
import os
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = Flask(__name__)
CORS(app)

# Получение URL базы данных
def get_db_url():
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url

def get_db_connection():
    """Получение соединения с БД"""
    try:
        conn = psycopg2.connect(get_db_url(), sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    """Главная страница с healthcheck"""
    try:
        # Проверка подключения к БД
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM messages")
                result = cur.fetchone()
                message_count = result[0] if result else 0
            conn.close()
            
            return render_template('index.html', 
                                 status='healthy',
                                 message_count=message_count,
                                 timestamp=datetime.now().isoformat())
        else:
            return render_template('index.html', 
                                 status='database_error',
                                 message_count=0,
                                 timestamp=datetime.now().isoformat())
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/health')
def health():
    """API healthcheck для Railway"""
    try:
        # Проверка БД
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                db_ok = cur.fetchone() is not None
            conn.close()
        else:
            db_ok = False
        
        return jsonify({
            "status": "healthy" if db_ok else "degraded",
            "database": "connected" if db_ok else "disconnected",
            "timestamp": datetime.now().isoformat(),
            "service": "chat-clone-bot"
        }), 200 if db_ok else 503
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/stats')
def stats():
    """Статистика"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Общая статистика
            cur.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT chat_id) as total_chats,
                    COUNT(DISTINCT user_id) as total_users,
                    MAX(created_at) as last_message
                FROM messages
            """)
            stats = cur.fetchone()
            
            # Активность по дням
            cur.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as messages
                FROM messages 
                WHERE created_at > CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            daily_stats = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            "statistics": stats,
            "daily_activity": daily_stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/messages')
def get_messages():
    """Получение последних сообщений"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database not available"}), 503
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id, chat_id, user_id, text, created_at
                FROM messages 
                ORDER BY created_at DESC 
                LIMIT 50
            """)
            messages = cur.fetchall()
        
        conn.close()
        
        return jsonify({
            "messages": messages,
            "count": len(messages)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)