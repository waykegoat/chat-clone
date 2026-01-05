import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter, defaultdict
from datetime import datetime
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from bot.database import Pattern, Message
from bot.utils import clean_text

class PatternLearner:
    def __init__(self):
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass
        
        self.stop_words = set(stopwords.words('russian') + stopwords.words('english'))
        self.learned_patterns = defaultdict(list)
        
    def analyze_message(self, text: str, chat_id: int, user_id: int, db: Session):
        """Анализ сообщения для извлечения паттернов"""
        if not text:
            return
        
        cleaned = clean_text(text)
        
        # Токенизация
        tokens = word_tokenize(cleaned, language='russian')
        
        # Удаление стоп-слов
        filtered_tokens = [word.lower() for word in tokens 
                          if word.lower() not in self.stop_words and len(word) > 2]
        
        # Извлечение n-грамм
        unigrams = filtered_tokens
        bigrams = [' '.join(filtered_tokens[i:i+2]) for i in range(len(filtered_tokens)-1)]
        trigrams = [' '.join(filtered_tokens[i:i+3]) for i in range(len(filtered_tokens)-2)]
        
        # Сохранение паттернов
        self._save_patterns(unigrams, 'word', chat_id, user_id, db)
        self._save_patterns(bigrams, 'bigram', chat_id, user_id, db)
        self._save_patterns(trigrams, 'trigram', chat_id, user_id, db)
        
        # Извлечение часто повторяющихся фраз
        if len(cleaned) > 10 and len(cleaned) < 100:
            self._check_for_phrases(cleaned, chat_id, user_id, db)
    
    def _save_patterns(self, items: List[str], pattern_type: str, 
                       chat_id: int, user_id: int, db: Session):
        """Сохранение паттернов в базу"""
        counter = Counter(items)
        
        for item, count in counter.items():
            if count >= 2:  # Сохраняем только повторяющиеся паттерны
                pattern = db.query(Pattern).filter(
                    Pattern.chat_id == chat_id,
                    Pattern.pattern_text == item,
                    Pattern.pattern_type == pattern_type
                ).first()
                
                if pattern:
                    pattern.frequency += count
                    pattern.last_used = datetime.now()
                else:
                    pattern = Pattern(
                        chat_id=chat_id,
                        user_id=user_id,
                        pattern_text=item,
                        pattern_type=pattern_type,
                        frequency=count,
                        last_used=datetime.now()
                    )
                    db.add(pattern)
        
        db.commit()
    
    def _check_for_phrases(self, text: str, chat_id: int, user_id: int, db: Session):
        """Проверка на часто повторяющиеся фразы"""
        # Здесь можно добавить логику для обнаружения мемов и часто используемых фраз
        pass