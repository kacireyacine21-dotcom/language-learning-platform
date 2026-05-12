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
    # Ensure database directory exists
    db_dir = os.path.dirname(DATABASE)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except:
            pass
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

            # Pronunciation Lessons - Simplified for beginners
            lessons = [
                # Arabic - Simple lessons for beginners
                (lang_ids[0], 'الحرف الأول: ا', '''درسنا اليوم: تعلم الحرف الأول من اللغة العربية

🔊 الحرف: ا (ألف)
📝 النطق: "آ" أو "ا"
💬 مثال: أنا (انا)

➡️ طريقة النطق:
افتح فمك قليلاً وقول "آآآ" ببطء
هذا الحرف يشبه حرف A في الإنجليزية

✅ تطبيق سريع:
قول: آ آ آ (3 مرات ببطء)
الآن: أنا (انا)''', 'alef', 'لا تتسرع، تعلم ببطء وتكرار', 1),
                
                (lang_ids[0], 'الحرف الثاني: ب', '''درسنا اليوم: تعلم الحرف الثاني

🔊 الحرف: ب
📝 النطق: "ب" - مثل حرف B في الإنجليزية
💬 أمثلة:
- باب (baab) = door
- بيت (bait) = house
- بنت (bint) = girl

➡️ طريقة النطق:
أغلق شفتيك وقول "ب" - ستسمع صوت الشفاه
الآن افتح وقول "با" أو "بي" أو "بو"

✅ تطبيق:
قول: بااا (3 مرات)
الآن: باب - بيت - بنت''', 'ba', 'تركيز على النطق من الشفتين', 2),

                (lang_ids[0], 'الكلمات الأساسية', '''درسنا اليوم: كلمات مهمة جداً للمحادثة

📚 الكلمات الأساسية:

1️⃣ مرحبا (Marhaba) = Hello
2️⃣ شكراً (Shukran) = Thank you
3️⃣ من فضلك (Min fadlak) = Please
4️⃣ عفواً (Afwan) = You're welcome
5️⃣ نعم (Aywa) = Yes
6️⃣ لا (La) = No

➡️ تطبيق:
قول كل كلمة 5 مرات ببطء
ثم حاول نطقها بدون قراءة

💡 نصيحة:
هذه الكلمات ستساعدك في أي محادثة!''', 'asaseya', 'استخدم هذه الكلمات يومياً', 3),

                (lang_ids[0], 'الأرقام من 1 إلى 10', '''درسنا اليوم: الأرقام الأساسية

🔢 الأرقام:

1 = واحد (wahid)
2 = اثنان (ithnan)
3 = ثلاثة (talata)
4 = أربعة (arbaa)
5 = خمسة (hamsa)
6 = ستة (sitta)
7 = سبعة (sabaa)
8 = ثمانية (tamaniya)
9 = تسعة (tisaa)
10 = عشرة (ashara)

➡️ تطبيق:
قول الأرقام من 1 إلى 10 ببطء
كرر 3 مرات

💡 الفائدة:
ستحتاج هذه الأرقام دائماً!''', 'arqam', 'استخدم أصابعك للعد أثناء النطق', 4),

                (lang_ids[0], 'الجملة الأولى', '''درسنا اليوم: نطق جملة كاملة

📝 الجملة:
السلام عليكم ورحمة الله وبركاته

📢 النطق:
As-Salaam Alaikum wa Rahmatullahi wa Barakatuh

➡️ شرح بسيط:
- السلام عليكم = السلام والسلامة عليك
- ورحمة الله = ورحمة من الله
- وبركاته = وبركات الله

🎯 معنى كامل:
"السلام عليكم" = "الله يحميك"

✅ تطبيق:
قول الجملة ببطء 5 مرات
ثم بسرعة عادية

💡 استخدام:
هذه أشهر تحية في العالم العربي!''', 'salam', 'لا تخف من الكلمات الطويلة', 5),

                # English - Simple lessons for beginners
                (lang_ids[1], 'الدرس الأول: Hello', '''درسنا اليوم: تحية شهيرة

🔊 الكلمة: Hello
📝 النطق: "هالو" أو "هيلو"
💬 المعنى: مرحبا

➡️ طريقة النطق:
قول: "ه" ثم "آ" ثم "لو"
Hel-lo (قسمها إلى جزأين)

✅ أمثلة:
- Hello! How are you? = مرحبا! كيف حالك؟
- Hello, my name is... = مرحبا، اسمي هو...

تطبيق: قول "Hello" 5 مرات''', 'hello', 'ابدأ بالكلمات البسيطة', 1),

                (lang_ids[1], 'الدرس الثاني: Thank You', '''درسنا اليوم: كلمة الشكر

🔊 الكلمة: Thank You
📝 النطق: "ثانك يو"
💬 المعنى: شكراً لك

➡️ طريقة النطق:
- Thank = ثانك (صوت ث + ا + ن + ك)
- You = يو (ي + و)

✅ أمثلة:
- Thank you! = شكراً لك!
- Thank you very much = شكراً جزيلاً

تطبيق: قول "Thank You" 5 مرات''', 'thankyou', 'الشكر مهم في أي لغة', 2),

                (lang_ids[1], 'الأرقام 1-10', '''درسنا اليوم: الأرقام الإنجليزية

🔢 الأرقام:
1 = One (ون)
2 = Two (تو)
3 = Three (ثري)
4 = Four (فور)
5 = Five (فايف)
6 = Six (سكس)
7 = Seven (سيفن)
8 = Eight (ايت)
9 = Nine (ناين)
10 = Ten (تن)

➡️ تطبيق سريع:
قول الأرقام من 1 إلى 10 ببطء

✅ نصيحة:
الأرقام أساسية في أي لغة!''', 'numbers', 'استخدم أصابعك للعد', 3),

                (lang_ids[1], 'الألوان الأساسية', '''درسنا اليوم: الألوان

🎨 الألوان:
- Red (رد) = أحمر
- Blue (بلو) = أزرق
- Green (جرين) = أخضر
- Yellow (يلو) = أصفر
- Black (بلاك) = أسود
- White (وايت) = أبيض

➡️ تطبيق:
- This is red = هذا أحمر
- I like blue = أحب الأزرق

✅ تطبيق سريع:
قول كل لون مع اللون الذي تراه حولك''', 'colors', 'تعلم أثناء النظر إلى الأشياء', 4),

                (lang_ids[1], 'أشهر الكلمات', '''درسنا اليوم: كلمات يومية

📚 كلمات مهمة:
- Yes = نعم (يس)
- No = لا (نو)
- Please = من فضلك (بليز)
- Sorry = آسف (سوري)
- OK = حسناً (أوكي)
- Good = جيد (جود)
- Help = ساعد (هيلب)

➡️ تطبيق:
جرب هذه الكلمات مع أصدقاء
استخدمها في جمل بسيطة

✅ مثال:
"Please, can you help?" = من فضلك، هل تستطيع مساعدتي؟''', 'daily', 'تعلم كلمة واحدة كل يوم', 5),

                # French - Simple lessons
                (lang_ids[2], 'الدرس الأول: Bonjour', '''درسنا اليوم: التحية الفرنسية

🔊 الكلمة: Bonjour
📝 النطق: "بونجور"
💬 المعنى: مرحبا / صباح الخير

➡️ طريقة النطق:
- Bon = "بون" (مثل كلمة Good)
- Jour = "جور" (مثل كلمة day)

✅ أمثلة:
- Bonjour! Ça va? = مرحبا! كيف حالك؟
- Bonjour, je m'appelle = مرحبا، اسمي

تطبيق: قول "Bonjour" 5 مرات''', 'bonjour', 'الفرنسية لغة جميلة', 1),

                (lang_ids[2], 'الدرس الثاني: Merci', '''درسنا اليوم: كلمة الشكر

🔊 الكلمة: Merci
📝 النطق: "ميرسي"
💬 المعنى: شكراً

➡️ طريقة النطق:
- Mer = "مير"
- Ci = "سي"

✅ أمثلة:
- Merci! = شكراً!
- Merci beaucoup = شكراً جزيلاً

تطبيق: قول "Merci" 5 مرات''', 'merci', 'كلمة سهلة وجميلة', 2),

                (lang_ids[2], 'الأرقام الفرنسية', '''درسنا اليوم: الأرقام

🔢 الأرقام:
1 = Un (أون)
2 = Deux (دو)
3 = Trois (تروا)
4 = Quatre (كاتر)
5 = Cinq (سان)
6 = Six (سيس)
7 = Sept (سيت)
8 = Huit (وايت)
9 = Neuf (نوف)
10 = Dix (ديس)

تطبيق: قول الأرقام ببطء''', 'nombres', 'الأرقام الفرنسية سهلة', 3),

                (lang_ids[2], 'كلمات يومية', '''درسنا اليوم: كلمات مهمة

📚 كلمات:
- Oui = نعم (وي)
- Non = لا (نون)
- S\'il vous plaît = من فضلك (سيل فو بليه)
- De rien = عفواً (د ريان)
- Excusez-moi = اعذرني (إكسكوزي موا)

✅ تطبيق سريع:
استخدم هذه الكلمات في محادثة''', 'mots', 'الفرنسية لغة أدب', 4),

                (lang_ids[2], 'الألوان', '''درسنا اليوم: الألوان الفرنسية

🎨 الألوان:
- Rouge = أحمر (روج)
- Bleu = أزرق (بلو)
- Vert = أخضر (فير)
- Jaune = أصفر (جون)
- Noir = أسود (نوار)
- Blanc = أبيض (بلان)

تطبيق: قول كل لون مع الأشياء حولك''', 'couleurs', 'الألوان جميلة باللغة', 5),

                # German - Simple lessons
                (lang_ids[3], 'الدرس الأول: Hallo', '''درسنا اليوم: التحية

🔊 الكلمة: Hallo
📝 النطق: "هالو"
💬 المعنى: مرحبا

➡️ طريقة النطق:
- Ha = "ها"
- llo = "لو"

✅ أمثلة:
- Hallo! Wie geht\'s? = مرحبا! كيف حالك؟

تطبيق: قول "Hallo" 5 مرات''', 'hallo', 'الألمانية لغة قوية', 1),

                (lang_ids[3], 'الدرس الثاني: Danke', '''درسنا اليوم: الشكر

🔊 الكلمة: Danke
📝 النطق: "دانكه"
💬 المعنى: شكراً

➡️ طريقة النطق:
- Dan = "دان"
- ke = "كه"

تطبيق: قول "Danke" 5 مرات''', 'danke', 'كلمة سهلة', 2),

                (lang_ids[3], 'الأرقام', '''درسنا اليوم: الأرقام الألمانية

🔢 الأرقام:
1 = Eins (آينس)
2 = Zwei (تسفاي)
3 = Drei (درآي)
4 = Vier (فير)
5 = Fünf (فونف)

تطبيق: قول الأرقام ببطء''', 'zahlen', 'تعلم الأرقام أولاً', 3),

                (lang_ids[3], 'كلمات يومية', '''درسنا اليوم: كلمات مهمة

📚 كلمات:
- Ja = نعم (يا)
- Nein = لا (نآين)
- Bitte = من فضلك (بيته)
- Guten Morgen = صباح الخير (جوتن مورجن)

تطبيق: استخدم هذه الكلمات''', 'worter', 'الألمانية سهلة بالممارسة', 4),

                (lang_ids[3], 'الألوان', '''درسنا اليوم: الألوان الألمانية

🎨 الألوان:
- Rot = أحمر (روت)
- Blau = أزرق (بلاو)
- Grün = أخضر (جرون)
- Gelb = أصفر (جيلب)
- Schwarz = أسود (شفارتس)
- Weiß = أبيض (فآيس)

تطبيق: قول الألوان مع الأشياء''', 'farben', 'الألمانية جميلة', 5),

                # Spanish - Simple lessons
                (lang_ids[4], 'الدرس الأول: Hola', '''درسنا اليوم: التحية

🔊 الكلمة: Hola
📝 النطق: "أولا"
💬 المعنى: مرحبا

➡️ طريقة النطق:
- Ho = "أو"
- la = "لا"

تطبيق: قول "Hola" 5 مرات''', 'hola', 'الإسبانية ممتعة', 1),

                (lang_ids[4], 'الدرس الثاني: Gracias', '''درسنا اليوم: الشكر

🔊 الكلمة: Gracias
📝 النطق: "جراسياس"
💬 المعنى: شكراً

تطبيق: قول "Gracias" 5 مرات''', 'gracias', 'كلمة مهمة', 2),

                (lang_ids[4], 'الأرقام', '''درسنا اليوم: الأرقام الإسبانية

🔢 الأرقام:
1 = Uno (أونو)
2 = Dos (دوس)
3 = Tres (تريس)
4 = Cuatro (كواترو)
5 = Cinco (سينكو)

تطبيق: قول الأرقام ببطء''', 'numeros', 'الإسبانية سهلة', 3),

                (lang_ids[4], 'كلمات يومية', '''درسنا اليوم: كلمات مهمة

📚 كلمات:
- Sí = نعم (سي)
- No = لا (نو)
- Por favor = من فضلك (بور فافور)
- De nada = عفواً (دي نادا)

تطبيق: استخدم الكلمات''', 'palabras', 'الإسبانية حول العالم', 4),

                (lang_ids[4], 'الألوان', '''درسنا اليوم: الألوان الإسبانية

🎨 الألوان:
- Rojo = أحمر (روخو)
- Azul = أزرق (أثول)
- Verde = أخضر (فيردي)
- Amarillo = أصفر (أماريلو)
- Negro = أسود (نيجرو)
- Blanco = أبيض (بلانكو)

تطبيق: قول الألوان مع الأشياء''', 'colores', 'الإسبانية جميلة', 5),

                # Italian - Simple lessons
                (lang_ids[5], 'الدرس الأول: Ciao', '''درسنا اليوم: التحية

🔊 الكلمة: Ciao
📝 النطق: "تشاو"
💬 المعنى: مرحبا / وداعاً

تطبيق: قول "Ciao" 5 مرات''', 'ciao', 'الإيطالية لغة الحب', 1),

                (lang_ids[5], 'الدرس الثاني: Grazie', '''درسنا اليوم: الشكر

🔊 الكلمة: Grazie
📝 النطق: "جراتسيه"
💬 المعنى: شكراً

تطبيق: قول "Grazie" 5 مرات''', 'grazie', 'كلمة جميلة', 2),

                (lang_ids[5], 'الأرقام', '''درسنا اليوم: الأرقام الإيطالية

🔢 الأرقام:
1 = Uno (أونو)
2 = Due (دويه)
3 = Tre (تري)
4 = Quattro (كوترو)
5 = Cinque (تشينكوي)

تطبيق: قول الأرقام''', 'numeri', 'الإيطالية سهلة', 3),

                (lang_ids[5], 'كلمات يومية', '''درسنا اليوم: كلمات مهمة

📚 كلمات:
- Sì = نعم (سي)
- No = لا (نو)
- Per favore = من فضلك (بير فافوري)
- Prego = عفواً (بريجو)

تطبيق: استخدم الكلمات''', 'parole', 'الإيطالية رومانسية', 4),

                (lang_ids[5], 'الألوان', '''درسنا اليوم: الألوان الإيطالية

🎨 الألوان:
- Rosso = أحمر (روسو)
- Blu = أزرق (بلو)
- Verde = أخضر (فيردي)
- Giallo = أصفر (جيالو)
- Nero = أسود (نيرو)
- Bianco = أبيض (بيانكو)

تطبيق: قول الألوان''', 'colori', 'الإيطالية جميلة', 5),

                # Chinese - Simple lessons
                (lang_ids[6], 'الدرس الأول: 你好', '''درسنا اليوم: التحية الصينية

🔊 الكلمة: 你好 (Nǐ hǎo)
📝 النطق: "نيا هاو"
💬 المعنى: مرحبا / صباح الخير

تطبيق: قول "Ni hao" 5 مرات''', 'nihao', 'الصينية جميلة', 1),

                (lang_ids[6], 'الدرس الثاني: 谢谢', '''درسنا اليوم: الشكر

🔊 الكلمة: 谢谢 (Xièxiè)
📝 النطق: "شيه شيه"
💬 المعنى: شكراً

تطبيق: قول "Xièxiè" 5 مرات''', 'xiexie', 'كلمة مهمة', 2),

                (lang_ids[6], 'الأرقام', '''درسنا اليوم: الأرقام الصينية

🔢 الأرقام:
1 = 一 (Yī) = ي
2 = 二 (Èr) = آر
3 = 三 (Sān) = سان
4 = 四 (Sì) = سو
5 = 五 (Wǔ) = وو

تطبيق: قول الأرقام''', 'shushu', 'الصينية سهلة', 3),

                (lang_ids[6], 'كلمات يومية', '''درسنا اليوم: كلمات مهمة

📚 كلمات:
- 是的 (Shì de) = نعم
- 不是 (Búshi) = لا
- 对不起 (Duìbúqǐ) = آسف
- 没关系 (Méi guānxi) = لا مشكلة

تطبيق: استخدم الكلمات''', 'ciyu', 'الصينية مثيرة', 4),

                (lang_ids[6], 'الألوان', '''درسنا اليوم: الألوان الصينية

🎨 الألوان:
- 红 (Hóng) = أحمر
- 蓝 (Lán) = أزرق
- 绿 (Lǜ) = أخضر
- 黄 (Huáng) = أصفر
- 黑 (Hēi) = أسود
- 白 (Báis) = أبيض

تطبيق: قول الألوان''', 'yanse', 'الصينية فريدة', 5),

                # Japanese - Simple lessons
                (lang_ids[7], 'الدرس الأول: こんにちは', '''درسنا اليوم: التحية اليابانية

🔊 الكلمة: こんにちは (Konnichiha)
📝 النطق: "كون نيتشي وا"
💬 المعنى: مرحبا / مساء الخير

تطبيق: قول "Konnichiha" 5 مرات''', 'konnichiha', 'اليابانية جميلة', 1),

                (lang_ids[7], 'الدرس الثاني: ありがとう', '''درسنا اليوم: الشكر

🔊 الكلمة: ありがとう (Arigatou)
📝 النطق: "أري جاتو"
💬 المعنى: شكراً

تطبيق: قول "Arigatou" 5 مرات''', 'arigatou', 'كلمة محترمة', 2),

                (lang_ids[7], 'الأرقام', '''درسنا اليوم: الأرقام اليابانية

🔢 الأرقام:
1 = 一 (Ichi) = إتشي
2 = 二 (Ni) = نيي
3 = 三 (San) = سان
4 = 四 (Shi) = شي
5 = 五 (Go) = جو

تطبيق: قول الأرقام''', 'suuji', 'اليابانية سهلة', 3),

                (lang_ids[7], 'كلمات يومية', '''درسنا اليوم: كلمات مهمة

📚 كلمات:
- はい (Hai) = نعم
- いいえ (Iie) = لا
- すみません (Sumimasen) = اعذرني
- 大丈夫 (Daijoubu) = لا مشكلة

تطبيق: استخدم الكلمات''', 'kotoba', 'اليابانية أدب', 4),

                (lang_ids[7], 'الألوان', '''درسنا اليوم: الألوان اليابانية

🎨 الألوان:
- 赤 (Aka) = أحمر
- 青 (Ao) = أزرق
- 緑 (Midori) = أخضر
- 黄色 (Kiiro) = أصفر
- 黒 (Kuro) = أسود
- 白 (Shiro) = أبيض

تطبيق: قول الألوان''', 'iro', 'اليابانية فريدة', 5),
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
        token = jwt.encode({'user_id': user['id'], 'exp': datetime.now() + timedelta(days=7)}, 
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
        try:
            cursor.execute('''SELECT l.*, COUNT(DISTINCT les.id) as lesson_count,
                             COUNT(DISTINCT v.id) as vocab_count, COUNT(DISTINCT e.id) as exercise_count
                             FROM languages l LEFT JOIN lessons les ON l.id = les.language_id
                             LEFT JOIN vocabulary v ON l.id = v.language_id
                             LEFT JOIN pronunciation_exercises e ON l.id = e.language_id
                             GROUP BY l.id ORDER BY l.id''')
            langs = [dict(row) for row in cursor.fetchall()]
            close_db(db)
            if not langs:
                logger.warning('No languages found - reinitializing database')
                init_db()
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
        except Exception as inner_e:
            logger.error(f'Query error: {str(inner_e)}')
            close_db(db)
            init_db()
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
        return jsonify({'success': False, 'message': str(e), 'data': []}), 500

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

@app.route('/api/lessons/<int:id>', methods=['GET'])
def get_lesson(id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM lessons WHERE id = ?', (id,))
        lesson = cursor.fetchone()
        close_db(db)
        if not lesson:
            return jsonify({'success': False, 'message': 'Lesson not found'}), 404
        return jsonify({'success': True, 'data': dict(lesson)}), 200
    except Exception as e:
        logger.error(f'Get lesson error: {str(e)}')
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
