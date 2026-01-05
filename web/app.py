from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime, timedelta

from bot.database import get_db, Chat, Message, User, Pattern, Statistic
from bot.config import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app)

@app.route('/')
def index():
    """Главная страница"""
    with get_db() as db:
        chats = db.query(Chat).order_by(Chat.created_at.desc()).limit(10).all()
        total_messages = db.query(Message).count()
        total_users = db.query(User).count()
        
    return render_template('index.html', 
                         chats=chats,
                         total_messages=total_messages,
                         total_users=total_users)

@app.route('/api/statistics/<chat_id>')
def get_statistics(chat_id):
    """API для получения статистики"""
    with get_db() as db:
        chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Базовая статистика
        stats = {
            'chat_id': chat.chat_id,
            'title': chat.title,
            'personality_level': chat.personality_level,
            'total_messages': db.query(Message).filter(Message.chat_id == chat.id).count(),
            'active_users': db.query(User).join(Message).filter(Message.chat_id == chat.id).distinct().count(),
            'patterns_count': db.query(Pattern).filter(Pattern.chat_id == chat.id).count(),
        }
        
        # Статистика по дням
        week_ago = datetime.now() - timedelta(days=7)
        daily_stats = db.query(Statistic).filter(
            Statistic.chat_id == chat.id,
            Statistic.date >= week_ago
        ).all()
        
        stats['daily'] = [{
            'date': s.date.strftime('%Y-%m-%d'),
            'messages': s.total_messages,
            'responses': s.bot_responses,
            'response_rate': s.bot_responses / s.total_messages if s.total_messages > 0 else 0
        } for s in daily_stats]
        
        return jsonify(stats)

@app.route('/api/patterns/<chat_id>')
def get_patterns(chat_id):
    """API для получения паттернов"""
    with get_db() as db:
        chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        patterns = db.query(Pattern).filter(
            Pattern.chat_id == chat.id
        ).order_by(Pattern.frequency.desc()).limit(50).all()
        
        result = [{
            'text': p.pattern_text,
            'type': p.pattern_type,
            'frequency': p.frequency,
            'last_used': p.last_used.strftime('%Y-%m-%d %H:%M') if p.last_used else None
        } for p in patterns]
        
        return jsonify(result)

@app.route('/api/export/<chat_id>')
def export_personality(chat_id):
    """Экспорт личности чата"""
    with get_db() as db:
        chat = db.query(Chat).filter(Chat.chat_id == chat_id).first()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Собираем данные для экспорта
        export_data = {
            'chat_info': {
                'id': chat.chat_id,
                'title': chat.title,
                'personality_level': chat.personality_level,
                'created_at': chat.created_at.isoformat()
            },
            'patterns': [],
            'top_phrases': []
        }
        
        # Топ паттерны
        patterns = db.query(Pattern).filter(
            Pattern.chat_id == chat.id
        ).order_by(Pattern.frequency.desc()).limit(100).all()
        
        export_data['patterns'] = [{
            'text': p.pattern_text,
            'type': p.pattern_type,
            'frequency': p.frequency
        } for p in patterns]
        
        # Топ фразы
        messages = db.query(Message).filter(
            Message.chat_id == chat.id,
            Message.text.isnot(None)
        ).order_by(Message.timestamp.desc()).limit(500).all()
        
        # Анализ фраз (упрощенный)
        from collections import Counter
        all_texts = [m.text for m in messages if m.text]
        word_freq = Counter(" ".join(all_texts).split())
        
        export_data['word_frequency'] = dict(word_freq.most_common(50))
        
        return jsonify(export_data)

if __name__ == "__main__":
    app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=True)