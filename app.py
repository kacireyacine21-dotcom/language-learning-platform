#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
منصة تعلم اللغات
Language Learning Platform
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
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-2026')
DB_PATH = os.environ.get('DATABASE_PATH', 'database/languages.db')
DATABASE = DB_PATH

# ===================== Database Functions =====================

def get_db():
    """Get database connection"""
    try:
        # Ensure database directory exists
        db_dir = os.path.dirname(DATABASE)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        return db
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def close_db(db):
    """Close database connection"""
    if db is not None:
        try:
            db.close()
        except:
            pass

def init_db():
    """Initialize database with tables and sample data"""
    db = None
    try:
        db = get_db()
        cursor = db.cursor()

        # Create all tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS languages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                flag TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                order_num INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (language_id) REFERENCES languages(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                pronunciation TEXT,
                part_of_speech TEXT,
                example_sentence TEXT,
                category TEXT,
                difficulty TEXT DEFAULT 'beginner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (language_id) REFERENCES languages(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                question TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                options TEXT,
                explanation TEXT,
                difficulty TEXT DEFAULT 'beginner',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (language_id) REFERENCES languages(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (language_id) REFERENCES languages(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lesson_id INTEGER NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (lesson_id) REFERENCES lessons(id),
                UNIQUE(user_id, lesson_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exercise_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                is_correct BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                language_id INTEGER,
                score REAL,
                correct_answers INTEGER,
                total_questions INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (language_id) REFERENCES languages(id)
            )
        ''')

        db.commit()

        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM languages')
        if cursor.fetchone()[0] == 0:
            logger.info('Initializing database with sample data...')
            
            # Insert languages
            languages = [
                ('العربية', 'تعلم اللغة العربية الفصحى', '🇸🇦'),
                ('الإنجليزية', 'تعلم اللغة الإنجليزية', '🇺🇸'),
                ('الفرنسية', 'تعلم اللغة الفرنسية', '🇫🇷'),
                ('الألمانية', 'تعلم اللغة الألمانية', '🇩🇪'),
                ('الإسبانية', 'تعلم اللغة الإسبانية', '🇪🇸'),
                ('الإيطالية', 'تعلم اللغة الإيطالية', '🇮🇹'),
                ('الصينية', 'تعلم اللغة الصينية', '🇨🇳'),
                ('اليابانية', 'تعلم اللغة اليابانية', '🇯🇵'),
            ]

            for lang in languages:
                cursor.execute('INSERT INTO languages (name, description, flag) VALUES (?, ?, ?)', lang)

            db.commit()

            # Get language IDs
            cursor.execute('SELECT id FROM languages ORDER BY id')
            lang_ids = [row[0] for row in cursor.fetchall()]

            # Insert Lessons
            lessons_data = [
                (lang_ids[0], 'التحية والسلام', 'تعلم طرق التحية الأساسية والسلام', 1),
                (lang_ids[0], 'الأرقام 1-10', 'تعلم الأرقام من واحد إلى عشرة', 2),
                (lang_ids[0], 'أفراد العائلة', 'تعريف أفراد العائلة والعلاقات', 3),
                (lang_ids[0], 'الألوان الأساسية', 'أسماء الألوان الشهيرة', 4),
                (lang_ids[0], 'الحيوانات المألوفة', 'أسماء الحيوانات الشهيرة', 5),
                (lang_ids[1], 'Greetings and Farewells', 'Learn basic English greetings', 1),
                (lang_ids[1], 'Numbers 1-10', 'Learn to count from one to ten', 2),
                (lang_ids[1], 'Family Members', 'Learn family relationships', 3),
                (lang_ids[1], 'Basic Colors', 'Learn color names', 4),
                (lang_ids[1], 'Common Animals', 'Learn animal names', 5),
                (lang_ids[2], 'Salutations', 'Les salutations françaises de base', 1),
                (lang_ids[2], 'Les Nombres', 'Compter de un à dix', 2),
                (lang_ids[2], 'La Famille', 'Les membres de la famille', 3),
                (lang_ids[3], 'Grüße', 'Deutsche Grußformeln', 1),
                (lang_ids[3], 'Zahlen', 'Zahlen von eins bis zehn', 2),
                (lang_ids[3], 'Familie', 'Familienmitglieder', 3),
                (lang_ids[4], 'Saludos', 'Los saludos básicos', 1),
                (lang_ids[4], 'Números', 'Los números del uno al diez', 2),
                (lang_ids[4], 'Familia', 'Los miembros de la familia', 3),
                (lang_ids[5], 'Saluti', 'I saluti di base in italiano', 1),
                (lang_ids[5], 'Numeri', 'I numeri da uno a dieci', 2),
                (lang_ids[5], 'Famiglia', 'I membri della famiglia', 3),
                (lang_ids[6], '问候', 'Learn Chinese greetings', 1),
                (lang_ids[6], '数字', 'Learn numbers one to ten', 2),
                (lang_ids[7], 'あいさつ', 'Learn Japanese greetings', 1),
                (lang_ids[7], '数字', 'Learn numbers one to ten', 2),
            ]

            for lesson in lessons_data:
                cursor.execute('INSERT INTO lessons (language_id, title, content, order_num) VALUES (?, ?, ?, ?)', lesson)

            db.commit()

            # Insert Vocabulary
            vocab_data = [
                (lang_ids[0], 'مرحبا', 'Hello', 'marhaba', 'Greeting', 'مرحبا، كيف حالك؟', 'Greetings', 'beginner'),
                (lang_ids[0], 'صباح الخير', 'Good morning', 'sabah alkhayr', 'Phrase', 'صباح الخير يا صديقي', 'Greetings', 'beginner'),
                (lang_ids[0], 'شكرا', 'Thank you', 'shukran', 'Verb', 'شكرا لك على مساعدتك', 'Polite expressions', 'beginner'),
                (lang_ids[0], 'من فضلك', 'Please', 'min fadlak', 'Phrase', 'من فضلك ساعدني', 'Polite expressions', 'beginner'),
                (lang_ids[0], 'واحد', 'One', 'wahid', 'Number', 'عندي واحد قطة', 'Numbers', 'beginner'),
                (lang_ids[0], 'اثنين', 'Two', 'ithnayn', 'Number', 'لدي اثنين أخوة', 'Numbers', 'beginner'),
                (lang_ids[0], 'أب', 'Father', 'ab', 'Noun', 'والدي مهندس', 'Family', 'beginner'),
                (lang_ids[0], 'أم', 'Mother', 'um', 'Noun', 'والدتي معلمة', 'Family', 'beginner'),
                (lang_ids[0], 'أحمر', 'Red', 'ahmar', 'Adjective', 'البستان أحمر اللون', 'Colors', 'beginner'),
                (lang_ids[0], 'أزرق', 'Blue', 'azraq', 'Adjective', 'السماء زرقاء اللون', 'Colors', 'beginner'),
                (lang_ids[1], 'Hello', 'مرحبا', 'HEL-oh', 'Greeting', 'Hello, nice to meet you', 'Greetings', 'beginner'),
                (lang_ids[1], 'Thank you', 'شكرا', 'THANK you', 'Verb', 'Thank you very much', 'Polite', 'beginner'),
                (lang_ids[1], 'Please', 'من فضلك', 'PLEASE', 'Adverb', 'Please help me', 'Polite', 'beginner'),
                (lang_ids[1], 'One', 'واحد', 'WUN', 'Number', 'I have one brother', 'Numbers', 'beginner'),
                (lang_ids[1], 'Two', 'اثنين', 'TOO', 'Number', 'I have two cats', 'Numbers', 'beginner'),
                (lang_ids[1], 'Father', 'أب', 'FAH-ther', 'Noun', 'My father is a doctor', 'Family', 'beginner'),
                (lang_ids[1], 'Mother', 'أم', 'MUTH-er', 'Noun', 'My mother is a teacher', 'Family', 'beginner'),
                (lang_ids[1], 'Red', 'أحمر', 'RED', 'Adjective', 'The rose is red', 'Colors', 'beginner'),
                (lang_ids[1], 'Blue', 'أزرق', 'BLOO', 'Adjective', 'The sky is blue', 'Colors', 'beginner'),
                (lang_ids[1], 'Green', 'أخضر', 'GREEN', 'Adjective', 'The grass is green', 'Colors', 'beginner'),
            ]

            for vocab in vocab_data:
                cursor.execute('INSERT INTO vocabulary (language_id, word, translation, pronunciation, part_of_speech, example_sentence, category, difficulty) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', vocab)

            db.commit()

            # Insert Exercises
            exercises_data = [
                (lang_ids[0], 'تكوين جملة بسيطة', 'اختر الكلمات بالترتيب الصحيح', 'أنا | طالب | مجتهد', 'طالب|مجتهد|أنا', 'أنا طالب مجتهد', 'ترتيب الكلمات بشكل صحيح'),
                (lang_ids[0], 'إكمال الجملة', 'أكمل الجملة الناقصة', 'والدي _____', 'مهندس|معلم|دكتور', 'مهندس', 'اختر الكلمة الصحيحة'),
                (lang_ids[0], 'الترجمة', 'اختر الترجمة الصحيحة', 'How are you بالعربية', 'كيف حالك|من أنت|شكرا', 'كيف حالك', 'الترجمة من الإنجليزية للعربية'),
                (lang_ids[1], 'Simple Sentence', 'Arrange the words correctly', 'I | student | am | a', 'a|student|I|am', 'I am a student', 'Correct word order'),
                (lang_ids[1], 'Fill the Blank', 'Complete the sentence', 'My mother is a _____', 'teacher|doctor|engineer', 'teacher', 'Choose the correct word'),
                (lang_ids[1], 'Translation', 'Translate to English', 'أنا سعيد جداً', 'I am very happy|I am sad|I am tired', 'I am very happy', 'Translate from Arabic to English'),
            ]

            for ex in exercises_data:
                cursor.execute('INSERT INTO exercises (language_id, title, description, question, correct_answer, options, explanation) VALUES (?, ?, ?, ?, ?, ?, ?)', ex)

            db.commit()

            # Insert Quiz Questions
            quiz_data = [
                (lang_ids[0], 'كم عدد الأحرف الأبجدية العربية؟', '["28", "26", "30", "25"]', '28'),
                (lang_ids[0], 'ما هو الفعل الماضي من يكتب؟', '["كتب", "يكتب", "اكتب", "كاتب"]', 'كتب'),
                (lang_ids[1], 'How many letters in the English alphabet?', '["24", "26", "28", "30"]', '26'),
                (lang_ids[1], 'What is the past tense of write?', '["wrote", "write", "writes", "writing"]', 'wrote'),
                (lang_ids[1], 'Number 5 in English is?', '["One", "Three", "Five", "Ten"]', 'Five'),
                (lang_ids[1], 'What is red in Arabic?', '["أحمر", "أزرق", "أخضر", "أصفر"]', 'أحمر'),
            ]

            for quiz in quiz_data:
                cursor.execute('INSERT INTO quiz_questions (language_id, question, options, correct_answer) VALUES (?, ?, ?, ?)', quiz)

            db.commit()
            logger.info('✅ Database initialized successfully!')
            logger.info('✅ 8 Languages, 26 Lessons, Vocabulary, Exercises, and Quizzes added')

        close_db(db)
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        if db:
            close_db(db)
        raise

# ===================== Authentication Decorator =====================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            logger.warning('Token missing')
            return jsonify({'success': False, 'message': 'Token missing'}), 401
        
        try:
            token = token.split(' ')[1]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            logger.warning('Invalid token')
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        
        return f(current_user_id, *args, **kwargs)
    return decorated

# ===================== Routes - Static & Frontend =====================

@app.route('/')
def index():
    try:
        return send_from_directory('frontend', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading page'}), 500

@app.route('/<path:path>')
def static_files(path):
    """Serve static files from frontend folder"""
    try:
        return send_from_directory('frontend', path)
    except Exception as e:
        logger.error(f"Error serving {path}: {str(e)}")
        try:
            return send_from_directory('frontend', 'index.html')
        except:
            return jsonify({'success': False, 'message': 'File not found'}), 404

# ===================== Routes - Authentication =====================

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        logger.info('=== Register Request ===')
        logger.info(f'Data received: {data}')
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not all([name, email, password]):
            return jsonify({'success': False, 'message': 'يرجى ملء جميع الحقول'}), 400
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            logger.info('Password hashed successfully')
            cursor.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)', (name, email, hashed))
            db.commit()
            logger.info(f'✅ User registered successfully: {email}')
            close_db(db)
            return jsonify({'success': True, 'message': 'تم إنشاء الحساب بنجاح!'}), 201
        except sqlite3.IntegrityError:
            close_db(db)
            return jsonify({'success': False, 'message': 'البريد الإلكتروني مستخدم بالفعل'}), 400
    except Exception as e:
        logger.error(f'Register error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        logger.info('=== Login Request ===')
        logger.info(f'Login data: email={data.get("email")}')
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'البريد وكلمة المرور مطلوبان'}), 400
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        close_db(db)
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash']):
            return jsonify({'success': False, 'message': 'بريد أو كلمة مرور غير صحيحة'}), 401
        
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        logger.info(f'✅ Login successful: {email}')
        return jsonify({
            'success': True,
            'token': token,
            'user': {'id': user['id'], 'name': user['name'], 'email': user['email']}
        }), 200
    except Exception as e:
        logger.error(f'Login error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - Languages =====================

@app.route('/api/languages', methods=['GET'])
def get_languages():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT l.*, 
                   COUNT(DISTINCT les.id) as lesson_count,
                   COUNT(DISTINCT v.id) as vocab_count,
                   COUNT(DISTINCT e.id) as exercise_count
            FROM languages l
            LEFT JOIN lessons les ON l.id = les.language_id
            LEFT JOIN vocabulary v ON l.id = v.language_id
            LEFT JOIN exercises e ON l.id = e.language_id
            GROUP BY l.id
            ORDER BY l.id
        ''')
        languages = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': languages}), 200
    except Exception as e:
        logger.error(f'Get languages error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - Lessons =====================

@app.route('/api/lessons', methods=['GET'])
def get_lessons():
    try:
        language_id = request.args.get('language_id')
        db = get_db()
        cursor = db.cursor()
        
        if language_id:
            cursor.execute('SELECT * FROM lessons WHERE language_id = ? ORDER BY order_num', (language_id,))
        else:
            cursor.execute('SELECT * FROM lessons ORDER BY language_id, order_num')
        
        lessons = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': lessons}), 200
    except Exception as e:
        logger.error(f'Get lessons error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

@app.route('/api/lessons/<int:lesson_id>', methods=['GET'])
def get_lesson(lesson_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM lessons WHERE id = ?', (lesson_id,))
        lesson = cursor.fetchone()
        close_db(db)
        
        if not lesson:
            return jsonify({'success': False, 'message': 'الدرس غير موجود'}), 404
        
        return jsonify({'success': True, 'data': dict(lesson)}), 200
    except Exception as e:
        logger.error(f'Get lesson error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - Vocabulary =====================

@app.route('/api/vocabulary', methods=['GET'])
def get_vocabulary():
    try:
        language_id = request.args.get('language_id')
        category = request.args.get('category')
        db = get_db()
        cursor = db.cursor()
        
        if language_id and category:
            cursor.execute('SELECT * FROM vocabulary WHERE language_id = ? AND category = ?', (language_id, category))
        elif language_id:
            cursor.execute('SELECT * FROM vocabulary WHERE language_id = ?', (language_id,))
        else:
            cursor.execute('SELECT * FROM vocabulary')
        
        vocab = [dict(row) for row in cursor.fetchall()]
        close_db(db)
        return jsonify({'success': True, 'data': vocab}), 200
    except Exception as e:
        logger.error(f'Get vocabulary error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - Exercises =====================

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    try:
        language_id = request.args.get('language_id')
        db = get_db()
        cursor = db.cursor()
        
        if language_id:
            cursor.execute('SELECT * FROM exercises WHERE language_id = ?', (language_id,))
        else:
            cursor.execute('SELECT * FROM exercises')
        
        exercises = [dict(row) for row in cursor.fetchall()]
        
        # Parse options field
        for ex in exercises:
            if ex['options']:
                ex['options'] = ex['options'].split('|')
        
        close_db(db)
        return jsonify({'success': True, 'data': exercises}), 200
    except Exception as e:
        logger.error(f'Get exercises error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

@app.route('/api/exercises/submit', methods=['POST'])
@token_required
def submit_exercise(user_id):
    try:
        data = request.get_json()
        exercise_id = data.get('exercise_id')
        answer = data.get('answer')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM exercises WHERE id = ?', (exercise_id,))
        exercise = cursor.fetchone()
        
        if not exercise:
            close_db(db)
            return jsonify({'success': False, 'message': 'التمرين غير موجود'}), 404
        
        is_correct = answer.strip().lower() == exercise['correct_answer'].strip().lower()
        cursor.execute('INSERT INTO exercise_results (user_id, exercise_id, answer, is_correct) VALUES (?, ?, ?, ?)',
                      (user_id, exercise_id, answer, is_correct))
        db.commit()
        close_db(db)
        
        return jsonify({
            'success': True,
            'correct': is_correct,
            'correct_answer': exercise['correct_answer'],
            'explanation': exercise['explanation']
        }), 200
    except Exception as e:
        logger.error(f'Submit exercise error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - Quiz =====================

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    try:
        language_id = request.args.get('language_id')
        db = get_db()
        cursor = db.cursor()
        
        if language_id:
            cursor.execute('SELECT * FROM quiz_questions WHERE language_id = ?', (language_id,))
        else:
            cursor.execute('SELECT * FROM quiz_questions')
        
        questions = [dict(row) for row in cursor.fetchall()]
        
        # Parse options field
        for q in questions:
            try:
                q['options'] = json.loads(q['options'])
            except:
                q['options'] = q['options'].split('|') if '|' in q['options'] else [q['options']]
        
        close_db(db)
        return jsonify({'success': True, 'data': questions}), 200
    except Exception as e:
        logger.error(f'Get quiz error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

@app.route('/api/quiz/submit', methods=['POST'])
@token_required
def submit_quiz(user_id):
    try:
        data = request.get_json()
        language_id = data.get('language_id')
        answers = data.get('answers')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM quiz_questions WHERE language_id = ?', (language_id,))
        questions = [dict(row) for row in cursor.fetchall()]
        
        correct = 0
        for q in questions:
            if answers.get(str(q['id'])) == q['correct_answer']:
                correct += 1
        
        score = (correct / len(questions)) * 100 if questions else 0
        cursor.execute('INSERT INTO quiz_results (user_id, language_id, score, correct_answers, total_questions) VALUES (?, ?, ?, ?, ?)',
                      (user_id, language_id, score, correct, len(questions)))
        db.commit()
        close_db(db)
        
        return jsonify({
            'success': True,
            'score': score,
            'correct': correct,
            'total': len(questions)
        }), 200
    except Exception as e:
        logger.error(f'Submit quiz error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - User Profile =====================

@app.route('/api/user/profile', methods=['GET'])
@token_required
def user_profile(user_id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        cursor.execute('SELECT COUNT(*) as count FROM user_progress WHERE user_id = ? AND completed = TRUE', (user_id,))
        completed_lessons = cursor.fetchone()['count']
        
        cursor.execute('SELECT AVG(score) as avg_score FROM quiz_results WHERE user_id = ?', (user_id,))
        avg_score_row = cursor.fetchone()
        avg_score = avg_score_row['avg_score'] or 0
        
        close_db(db)
        
        return jsonify({
            'success': True,
            'data': {
                'user': dict(user) if user else {},
                'stats': {
                    'completed_lessons': completed_lessons,
                    'average_score': avg_score
                }
            }
        }), 200
    except Exception as e:
        logger.error(f'Get profile error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Routes - Progress =====================

@app.route('/api/progress', methods=['POST'])
@token_required
def update_progress(user_id):
    try:
        data = request.get_json()
        lesson_id = data.get('lesson_id')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute('INSERT OR REPLACE INTO user_progress (user_id, lesson_id, completed) VALUES (?, ?, TRUE)', (user_id, lesson_id))
        db.commit()
        close_db(db)
        return jsonify({'success': True, 'message': 'Progress updated'}), 200
    except Exception as e:
        logger.error(f'Update progress error: {str(e)}')
        return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500

# ===================== Error Handlers =====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    logger.error(f'Server error: {str(error)}')
    return jsonify({'success': False, 'message': 'Server error'}), 500

# ===================== Main =====================

if __name__ == '__main__':
    try:
        os.makedirs('database', exist_ok=True)
        os.makedirs('frontend', exist_ok=True)
        
        logger.info('Initializing database...')
        init_db()
        
        print('\n' + '='*60)
        print('🌍 منصة تعلم اللغات - Language Learning Platform')
        print('='*60)
        print('✅ Database initialized')
        
        # Get PORT from environment variable, default to 5000 for local development
        port = int(os.environ.get('PORT', 5000))
        debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
        
        print(f'🚀 Server is running on http://0.0.0.0:{port}')
        print('='*60)
        
        app.run(debug=debug_mode, host='0.0.0.0', port=port, use_reloader=False)
    except Exception as e:
        logger.error(f'Failed to start server: {str(e)}')
        print(f'❌ Error: {str(e)}')
        raise
