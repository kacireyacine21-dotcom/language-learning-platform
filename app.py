#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
منصة تعلم اللغات - دروس النطق
Language Learning Platform - Pronunciation Lessons
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import os
import json
import logging
from datetime import datetime, timedelta
from functools import wraps

# Initialize Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')

# CORS Configuration
CORS(app, 
     resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}},
     supports_credentials=True)

# Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pronunciation-secret-key-2026')
DB_PATH = os.environ.get('DATABASE_PATH', 'database/languages.db')
DATABASE = DB_PATH

# ===================== Database Functions =====================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def close_db(db):
    if db is not None:
        try:
            db.close()
        except:
            pass

def init_db():
    """Initialize database with pronunciation lessons"""
    db = None
    try:
        db = get_db()
        cursor = db.cursor()

        # Create tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS languages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            description TEXT, flag TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT, language_id INTEGER NOT NULL,
            title TEXT NOT NULL, content TEXT, pronunciation TEXT, tips TEXT,
            order_num INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (language_id) REFERENCES languages(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT, language_id INTEGER NOT NULL,
            word TEXT NOT NULL, translation TEXT NOT NULL,
            pronunciation TEXT, audio_guide TEXT,
            part_of_speech TEXT, example TEXT, category TEXT,
            difficulty TEXT DEFAULT 'beginner',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (language_id) REFERENCES languages(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS pronunciation_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT, language_id INTEGER NOT NULL,
            title TEXT NOT NULL, word TEXT NOT NULL, correct_pronunciation TEXT,
            tips TEXT, difficulty TEXT DEFAULT 'beginner',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (language_id) REFERENCES languages(id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL, completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (lesson_id) REFERENCES lessons(id),
            UNIQUE(user_id, lesson_id))''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS pronunciation_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL, score REAL, feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (exercise_id) REFERENCES pronunciation_exercises(id))''')

        db.commit()

        # Check if data exists
        cursor.execute('SELECT COUNT(*) FROM languages')
        if cursor.fetchone()[0] == 0:
            logger.info('Initializing with pronunciation lessons...')
            
            # Languages
            langs = [
                ('العربية', 'تعلم نطق اللغة العربية الفصحى', '🇸🇦'),
                ('الإنجليزية', 'تعلم نطق الإنجليزية الصحيح', '🇺🇸'),
                ('الفرنسية', 'تعلم نطق الفرنسية', '🇫🇷'),
                ('الألمانية', 'تعلم نطق الألمانية', '🇩🇪'),
                ('الإسبانية', 'تعلم نطق الإسبانية', '🇪🇸'),
                ('الإيطالية', 'تعلم نطق الإيطالية', '🇮🇹'),
                ('الصينية', 'تعلم نطق الماندرين', '🇨🇳'),
                ('اليابانية', 'تعلم نطق اليابانية', '🇯🇵'),
            ]
            for lang in langs:
                cursor.execute('INSERT INTO languages (name, description, flag) VALUES (?, ?, ?)', lang)
            db.commit()

            cursor.execute('SELECT id FROM languages ORDER BY id')
            lang_ids = [row[0] for row in cursor.fetchall()]

            # Pronunciation Lessons
            lessons = [
                # Arabic
                (lang_ids[0], 'الحروف الهجائية العربية', 'تعلم نطق الحروف من ا إلى ي', 'al-huroof', 'ركز على مخارج الحروف من الحلق والشفتين', 1),
                (lang_ids[0], 'نطق الحركات (الفتحة والضمة والكسرة)', 'تعلم تأثير الحركات على نطق الكلمات', 'al-harakat', 'الحركات تغير نطق الكلمة كلياً', 2),
                (lang_ids[0], 'نطق الكلمات الشائعة', 'كلمات يومية مع نطق صحيح', 'kalimah-sha3ee', 'استمع للنطق عدة مرات قبل التكرار', 3),
                (lang_ids[0], 'تمييز الأصوات المتشابهة', 'الفرق بين الحروف المتقاربة مثل ض وظ', 'aswat-mutashabiha', 'استخدم مرآة لرؤية موضع اللسان', 4),
                (lang_ids[0], 'نطق الجمل البسيطة', 'جمل يومية مع نطق سليم', 'jumal-basita', 'لا تتسرع، انطق ببطء ووضوح أولاً', 5),
                
                # English
                (lang_ids[1], 'English Vowel Sounds', 'Learn the 5 vowel sounds: a, e, i, o, u', 'vowels', 'Each vowel has a short and long sound', 1),
                (lang_ids[1], 'Consonant Pronunciation', 'Master consonant sounds and combinations', 'consonants', 'Pay attention to voiced and unvoiced sounds', 2),
                (lang_ids[1], 'Common English Words', 'Pronunciation of frequently used words', 'common-words', 'Listen multiple times before repeating', 3),
                (lang_ids[1], 'Stress and Intonation', 'Word stress changes word meaning', 'stress', 'Practice with sentences for natural flow', 4),
                (lang_ids[1], 'Homophones Practice', 'Words that sound similar but differ in meaning', 'homophones', 'Context helps distinguish similar sounds', 5),
                
                # French
                (lang_ids[2], 'Les Voyelles Françaises', 'Les 12 sons de voyelles du français', 'voyelles', 'Le français a plus de voyelles que l\'anglais', 1),
                (lang_ids[2], 'Les Consonnes Difficiles', 'R français et autres consonnes', 'consonnes', 'Le R français se prononce à partir de la gorge', 2),
                (lang_ids[2], 'Accent Tonique et Rythme', 'La musicalité du français', 'rythme', 'Le français est une langue chantante', 3),
                (lang_ids[2], 'Mots Courants', 'Prononciation des mots du quotidien', 'mots', 'Écoutez la prononciation native', 4),
                (lang_ids[2], 'Liaison et Élision', 'Règles importantes du français', 'liaison', 'La liaison change la prononciation', 5),
                
                # German
                (lang_ids[3], 'Deutsche Vokale', 'Die 8 Vokale des Deutschen', 'vokale', 'Kurze und lange Vokale klingen unterschiedlich', 1),
                (lang_ids[3], 'Umlaute und Eszett', 'ä, ö, ü, ß Laute meistern', 'umlaute', 'Diese Laute existieren nicht in allen Sprachen', 2),
                (lang_ids[3], 'Konsonantenclusters', 'Schwierige Konsonantenkombinationen', 'konsonanten', 'Deutsch hat viele Konsonantengruppen', 3),
                (lang_ids[3], 'Häufige Deutsche Wörter', 'Alltagsvokabeln richtig aussprechen', 'worter', 'Das Deutsche hat klare Ausspracheregeln', 4),
                (lang_ids[3], 'Satzmelodie', 'Rhythmus und Betonung im Deutschen', 'melodie', 'Die Betonung liegt meist auf der ersten Silbe', 5),
                
                # Spanish
                (lang_ids[4], 'Las Vocales Españolas', 'Los 5 sonidos vocálicos del español', 'vocales', 'Las vocales españolas son más cortas que en inglés', 1),
                (lang_ids[4], 'La Consonante R', 'La R y RR españolas', 'erre', 'Práctica de roling R es importante', 2),
                (lang_ids[4], 'Sonidos Similares', 'B-V, LL-Y, C-Z diferencias', 'sonidos', 'El español tiene varios sonidos sibilantes', 3),
                (lang_ids[4], 'Palabras Cotidianas', 'Vocabulario de uso diario', 'palabras', 'Escucha hablantes nativos constantemente', 4),
                (lang_ids[4], 'Acentos Regionales', 'Variaciones de pronunciación española', 'acentos', 'Cada región de España tiene su acento', 5),
                
                # Italian
                (lang_ids[5], 'Le Vocali Italiane', 'I 5 suoni vocalici dell\'italiano', 'vocali', 'L\'italiano ha vocali chiare e distinte', 1),
                (lang_ids[5], 'Consonanti Doppie', 'La pronuncia delle consonanti doppie', 'doppie', 'Le doppie cambiano completamente il suono', 2),
                (lang_ids[5], 'Suoni c e g', 'Dolce vs duro: Ca, Ce, Ci, Co, Cu', 'suoni', 'La posizione della vocale cambia il suono', 3),
                (lang_ids[5], 'Parole Comuni', 'Pronuncia dei vocaboli quotidiani', 'parole', 'L\'italiano ha una pronuncia relativamente regolare', 4),
                (lang_ids[5], 'Ritmo e Intonazione', 'La musicalità dell\'italiano', 'ritmo', 'L\'italiano è una lingua musicale', 5),
                
                # Chinese
                (lang_ids[6], '普通话的四声', '四声声调系统', 'shengdiao', '声调错误会改变词义', 1),
                (lang_ids[6], '汉语辅音', '清浊音的区分', 'fuyin', '普通话有21个辅音', 2),
                (lang_ids[6], '汉语元音', '单元音和复元音', 'yuanyin', '发音时要注意嘴形', 3),
                (lang_ids[6], '常用汉字发音', '日常汉字的正确发音', 'hanzi', '多练习绕口令', 4),
                (lang_ids[6], '声调练习', '四声的辨别和训练', 'liaoshi', '听力是关键', 5),
                
                # Japanese
                (lang_ids[7], 'ひらがなの発音', 'ひらがな46音', 'hiragana', '日本語の基本は5つの母音', 1),
                (lang_ids[7], 'カタカナの発音', 'カタカナ46音', 'katakana', '外来語はカタカナで書く', 2),
                (lang_ids[7], '長音と短音', 'えいとおーの違い', 'chouon', '長音は意味を変える可能性', 3),
                (lang_ids[7], 'よく使う単語', '日常単語の正しい発音', 'tango', 'ネイティブの発音をよく聞く', 4),
                (lang_ids[7], 'アクセントと抑揚', '日本語のイントネーション', 'akusento', '標準日本語のアクセント位置', 5),
            ]
            for lesson in lessons:
                cursor.execute('''INSERT INTO lessons 
                    (language_id, title, content, pronunciation, tips, order_num) 
                    VALUES (?, ?, ?, ?, ?, ?)''', lesson)
            db.commit()

            # Vocabulary with pronunciation
            vocab = [
                # Arabic
                (lang_ids[0], 'السلام', 'Peace/Hello', 'as-salaam', 'تعريف شامل للتحية الإسلامية', 'Noun', 'السلام عليكم', 'Greetings', 'beginner'),
                (lang_ids[0], 'الشمس', 'The Sun', 'ash-shams', 'مد الشين من الفم', 'Noun', 'الشمس مضيئة', 'Nature', 'beginner'),
                (lang_ids[0], 'القمر', 'The Moon', 'al-qamar', 'نطق القاف من الحلق', 'Noun', 'القمر جميل', 'Nature', 'beginner'),
                
                # English
                (lang_ids[1], 'Beautiful', 'جميل', 'BYU-tuh-ful', 'Stress on first syllable', 'Adjective', 'She is beautiful', 'Adjectives', 'beginner'),
                (lang_ids[1], 'Pronunciation', 'النطق', 'pruh-nun-see-AY-shun', 'Stress on third syllable', 'Noun', 'Good pronunciation is important', 'Learning', 'beginner'),
                (lang_ids[1], 'Water', 'ماء', 'WAW-ter', 'American vs British', 'Noun', 'Drink water daily', 'Nouns', 'beginner'),
                
                # French
                (lang_ids[2], 'Bonjour', 'مرحبا', 'bon-ZHOOR', 'R français guttural', 'Noun', 'Bonjour, comment ça va?', 'Greetings', 'beginner'),
                (lang_ids[2], 'Merci', 'شكرا', 'mer-SEE', 'Final i not pronounced', 'Interjection', 'Merci beaucoup', 'Polite', 'beginner'),
                (lang_ids[2], 'S\'il vous plaît', 'من فضلك', 'see voo pleh', 'Liaison and elision', 'Phrase', 'S\'il vous plaît, aidez-moi', 'Polite', 'beginner'),
                
                # German
                (lang_ids[3], 'Guten Tag', 'يوم جيد', 'GOO-ten TAHG', 'T is pronounced clearly', 'Phrase', 'Guten Tag, Herr Schmidt', 'Greetings', 'beginner'),
                (lang_ids[3], 'Äpfel', 'تفاح', 'EHP-fel', 'Ä sounds like short e', 'Noun', 'Ich esse einen Äpfel', 'Nouns', 'beginner'),
                (lang_ids[3], 'Schön', 'جميل', 'shern', 'SCH makes sh sound', 'Adjective', 'Das ist sehr schön', 'Adjectives', 'beginner'),
            ]
            for v in vocab:
                cursor.execute('''INSERT INTO vocabulary 
                    (language_id, word, translation, pronunciation, audio_guide, part_of_speech, example, category, difficulty) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', v)
            db.commit()

            # Pronunciation exercises
            exercises = [
                (lang_ids[0], 'نطق الحرف ع', 'عين', 'AAA-ain (عين)', 'حرف ع ينطق من أعمق الحلق'),
                (lang_ids[0], 'نطق الحرف ق', 'قاف', 'QAF-qaf', 'حرف ق أعمق من حرف ك'),
                (lang_ids[1], 'TH sound practice', 'The', 'thuh', 'Tongue between teeth for "th"'),
                (lang_ids[1], 'R vs W', 'Red', 'red', 'Many learn wrong: "wed"'),
                (lang_ids[2], 'R guttural sound', 'Rare', 'RAHR', 'From back of throat'),
                (lang_ids[2], 'U vs OU', 'tu', 'too', 'French has many vowel sounds'),
            ]
            for ex in exercises:
                cursor.execute('''INSERT INTO pronunciation_exercises 
                    (language_id, title, word, correct_pronunciation, tips) 
                    VALUES (?, ?, ?, ?, ?)''', ex)
            db.commit()

            logger.info('✅ Pronunciation lessons database initialized!')
        
        close_db(db)
    except Exception as e:
        logger.error(f"DB init error: {str(e)}")
        if db:
            close_db(db)
        raise

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': 'Token missing'}), 401
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        return f(current_user_id, *args, **kwargs)
    return decorated

# Routes
@app.route('/')
def index():
    try:
        return send_from_directory('frontend', 'index.html')
    except:
        return jsonify({'success': False, 'message': 'Error'}), 500

@app.route('/<path:path>')
def static_files(path):
    try:
        return send_from_directory('frontend', path)
    except:
        try:
            return send_from_directory('frontend', 'index.html')
        except:
            return jsonify({'success': False}), 404

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        name, email, password = data.get('name'), data.get('email'), data.get('password')
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'Fill all fields'}), 400
        db = get_db()
        cursor = db.cursor()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)', (name, email, hashed))
        db.commit()
        close_db(db)
        logger.info(f'User registered: {email}')
        return jsonify({'success': True, 'message': 'تم إنشاء الحساب بنجاح!'}), 201
    except Exception as e:
        logger.error(f'Register error: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        email, password = data.get('email'), data.get('password')
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        close_db(db)
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        token = jwt.encode({'user_id': user['id'], 'exp': datetime.utcnow() + timedelta(days=7)}, 
                          app.config['SECRET_KEY'], algorithm='HS256')
        logger.info(f'Login successful: {email}')
        return jsonify({'success': True, 'token': token, 'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}}), 200
    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''SELECT l.*, COUNT(DISTINCT les.id) as lesson_count,
                         COUNT(DISTINCT v.id) as vocab_count, COUNT(DISTINCT e.id) as exercise_count
                         FROM languages l LEFT JOIN lessons les ON l.id = les.language_id
                         LEFT JOIN vocabulary v ON l.id = v.language_id
                         LEFT JOIN pronunciation_exercises e ON l.id = e.language_id
                         GROUP BY l.id ORDER BY l.id''')
        langs = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': langs}), 200
    except Exception as e:
        logger.error(f'Get languages error: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/lessons', methods=['GET'])
def get_lessons():
    try:
        lang_id = request.args.get('language_id')
        db = get_db()
        cursor = db.cursor()
        if lang_id:
            cursor.execute('SELECT * FROM lessons WHERE language_id = ? ORDER BY order_num', (lang_id,))
        else:
            cursor.execute('SELECT * FROM lessons ORDER BY language_id, order_num')
        lessons = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': lessons}), 200
    except Exception as e:
        logger.error(f'Get lessons error: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/vocabulary', methods=['GET'])
def get_vocabulary():
    try:
        lang_id = request.args.get('language_id')
        db = get_db()
        cursor = db.cursor()
        if lang_id:
            cursor.execute('SELECT * FROM vocabulary WHERE language_id = ?', (lang_id,))
        else:
            cursor.execute('SELECT * FROM vocabulary')
        vocab = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': vocab}), 200
    except Exception as e:
        logger.error(f'Get vocabulary error: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    try:
        lang_id = request.args.get('language_id')
        db = get_db()
        cursor = db.cursor()
        if lang_id:
            cursor.execute('SELECT * FROM pronunciation_exercises WHERE language_id = ?', (lang_id,))
        else:
            cursor.execute('SELECT * FROM pronunciation_exercises')
        exercises = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': exercises}), 200
    except Exception as e:
        logger.error(f'Get exercises error: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/exercises/submit', methods=['POST'])
@token_required
def submit_exercise(user_id):
    try:
        data = request.get_json()
        exercise_id = data.get('exercise_id')
        score = data.get('score', 100)
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM pronunciation_exercises WHERE id = ?', (exercise_id,))
        ex = cursor.fetchone()
        if not ex:
            close_db(db)
            return jsonify({'success': False}), 404
        cursor.execute('INSERT INTO pronunciation_scores (user_id, exercise_id, score) VALUES (?, ?, ?)',
                      (user_id, exercise_id, score))
        db.commit()
        close_db(db)
        return jsonify({'success': True, 'message': 'نتيجة تم حفظها بنجاح'}), 200
    except Exception as e:
        logger.error(f'Submit exercise error: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/user/profile', methods=['GET'])
@token_required
def user_profile(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        cursor.execute('SELECT COUNT(*) as count FROM user_progress WHERE user_id = ? AND completed = TRUE', (user_id,))
        completed = cursor.fetchone()['count']
        cursor.execute('SELECT AVG(score) as avg_score FROM pronunciation_scores WHERE user_id = ?', (user_id,))
        avg_score = cursor.fetchone()['avg_score'] or 0
        close_db(db)
        return jsonify({'success': True, 'data': {'user': dict(user) if user else {}, 
                       'stats': {'completed_lessons': completed, 'average_score': avg_score}}}), 200
    except Exception as e:
        logger.error(f'Profile error: {str(e)}')
        return jsonify({'success': False}), 500

@app.route('/api/progress', methods=['POST'])
@token_required
def update_progress(user_id):
    try:
        data = request.get_json()
        lesson_id = data.get('lesson_id')
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT OR REPLACE INTO user_progress (user_id, lesson_id, completed) VALUES (?, ?, TRUE)', 
                      (user_id, lesson_id))
        db.commit()
        close_db(db)
        return jsonify({'success': True}), 200
    except Exception as e:
        logger.error(f'Progress error: {str(e)}')
        return jsonify({'success': False}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False}), 404

if __name__ == '__main__':
    try:
        os.makedirs('database', exist_ok=True)
        os.makedirs('frontend', exist_ok=True)
        init_db()
        print('\n' + '='*60)
        print('🎤 منصة تعلم النطق - Pronunciation Learning Platform')
        print('='*60)
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV', 'development') == 'development'
        print(f'🚀 Running on http://0.0.0.0:{port}')
        print('='*60 + '\n')
        app.run(debug=debug, host='0.0.0.0', port=port, use_reloader=False)
    except Exception as e:
        logger.error(f'Server error: {str(e)}')
        raise
