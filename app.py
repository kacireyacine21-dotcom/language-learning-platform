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

            # Pronunciation Lessons
            lessons = [
                # Arabic
                (lang_ids[0], 'الحروف الهجائية العربية', '''تعلم نطق جميع الحروف العربية 28:
ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي
كل حرف له مخرج محدد من الفم. الحروف الحلقية (ا، ه، ح، خ، ع، غ) تنطق من الحلق.
الحروف الشفوية (ب، ف، م) تنطق من الشفاه. مهم تركيز على مخارج الحروف.''', 'al-huroof', 'ركز على مخارج الحروف من الحلق والشفتين', 1),
                (lang_ids[0], 'نطق الحركات (الفتحة والضمة والكسرة)', '''الحركات الثلاث الأساسية:
1. الفتحة (َ): تفتح الفم قليلاً - مثال: كتاب (ka-taab)
2. الضمة (ُ): تدور الشفاه - مثال: كتب (ku-tub)
3. الكسرة (ِ): تُسحب الشفاه للخلف - مثال: كتب (ki-tab)
الحركات تغير معنى الكلمة تماماً! درّب أذنك على الفرق.''', 'al-harakat', 'الحركات تغير نطق الكلمة كلياً', 2),
                (lang_ids[0], 'نطق الكلمات الشائعة', '''كلمات يومية مهمة:
- السلام عليكم (as-salaam alaikum) - التحية
- صباح الخير (sabah al-khair) - صباح الخير
- مساء الخير (masaa al-khair) - مساء الخير
- شكراً (shukran) - شكراً
- من فضلك (min fadlak) - من فضلك
- عفواً (afwan) - عفواً
استمع للنطق الصحيح عدة مرات قبل التكرار.''', 'kalimah-sha3ee', 'استمع للنطق عدة مرات قبل التكرار', 3),
                (lang_ids[0], 'تمييز الأصوات المتشابهة', '''الحروف المتشابهة في النطق:
- ض (emphatic D) vs د (light D)
- ظ (emphatic Z) vs ز (light Z)
- ط (emphatic T) vs ت (light T)
- ص (emphatic S) vs س (light S)
الحروف الأولى تُنطق بضغط على الحنك. الحروف الثانية ألطف.
مثال: ضرس vs درس - لاحظ الفرق في النطق.''', 'aswat-mutashabiha', 'استخدم مرآة لرؤية موضع اللسان', 4),
                (lang_ids[0], 'نطق الجمل البسيطة', '''جمل يومية بسيطة:
- أنا أسمي محمد (ana ismi Muhammad) - اسمي محمد
- كيف حالك؟ (kayf haluk?) - كيف حالك؟
- أنا بخير (ana bi-khair) - أنا بخير
- هذا جميل (haza jameel) - هذا جميل
- شنو أخبارك؟ (shnu akhbarak?) - كيف أخبارك؟
انطق ببطء ووضوح أولاً. الهدف هو الوضوح قبل السرعة.''', 'jumal-basita', 'لا تتسرع، انطق ببطء ووضوح أولاً', 5),
                
                # English
                (lang_ids[1], 'English Vowel Sounds', '''Learn the 5 main vowel sounds:
/æ/ as in CAT - open mouth, short sound
/ɛ/ as in BED - relax mouth, medium sound
/ɪ/ as in SIT - smile slightly, short sound
/ɑ:/ as in FATHER - open mouth wide, long sound
/ʊ/ as in BOOK - round lips, short sound
Vowels are the most important for clear English. Practice each sound 10 times.''', 'vowels', 'Each vowel has a short and long sound', 1),
                (lang_ids[1], 'Consonant Pronunciation', '''Master basic consonants:
VOICED: b, d, g, v, z, j - Your throat vibrates
UNVOICED: p, t, k, f, s, ch - No vibration in throat
Practice pairs: P-B, T-D, K-G
Put your hand on throat to feel vibration.
Example: PACK vs BAG - hear the difference?''', 'consonants', 'Pay attention to voiced and unvoiced sounds', 2),
                (lang_ids[1], 'Common English Words', '''Practice these 10 words:
1. HELLO (hə-LOH) - stress on 2nd syllable
2. WATER (WAH-tur) - T becomes D sound
3. QUESTION (KWES-chun) - Q-sound is KW
4. PRONUNCIATION (pruh-nun-see-AY-shun) - stress on 3rd
5. IMPORTANT (im-POR-tunt) - stress on 2nd
6. BEAUTIFUL (BEW-ti-ful) - 3 syllables
7. DIFFERENT (DIF-runt) - R is flapped
8. EXAMPLE (ig-ZAM-pul) - G sounds like Z
Listen to native speakers and repeat!''', 'common-words', 'Listen multiple times before repeating', 3),
                (lang_ids[1], 'Stress and Intonation', '''Word stress changes meaning:
PRESENT (noun) vs pre-SENT (verb)
RE-cord (noun) vs re-CORD (verb)
CON-test (noun) vs con-TEST (verb)

Sentence intonation:
Statement: "You are here." - falls at end
Question: "You are here?" - rises at end
Practice using sentences for natural flow.''', 'stress', 'Practice with sentences for natural flow', 4),
                (lang_ids[1], 'Homophones Practice', '''Words that sound the same, different meaning:
- THEIR vs THERE vs THEY'RE
- WRITE vs RIGHT
- WEAR vs WHERE
- BREAK vs BRAKE
- FLOUR vs FLOWER
Context helps you understand which word is used.
Example: "Their book is over there" - different words, same sound!''', 'homophones', 'Context helps distinguish similar sounds', 5),
                
                # French
                (lang_ids[2], 'Les Voyelles Françaises', '''Les 6 voyelles de base du français:
/a/ comme dans CAT - bouche ouverte
/e/ comme dans CAFÉ - sourire un peu
/i/ comme dans CHEMISE - sourire beaucoup
/o/ comme dans BEAU - lèvres arrondies
/u/ comme dans VOUS - lèvres très arrondies
/ə/ comme dans LE - neutre
Les voyelles françaises sont très différentes de l'anglais. Pronunciez avec les lèvres arrondies.''', 'voyelles', 'Le français a plus de voyelles que l\'anglais', 1),
                (lang_ids[2], 'Les Consonnes Difficiles', '''Le R français est le plus difficile:
R FRANÇAIS: Son guttural du fond de la gorge - comme PARIS
R ANGLAIS: Son de la langue - comme RED
Autres consonnes difficiles:
- TH n'existe pas en français
- W se prononce V - WASHINGTON = VASHINGTON
- GN se prononce NY - MONTAGNE = mon-TAH-nyuh
Pratiquez le R en gargarisant!''', 'consonnes', 'Le R français se prononce à partir de la gorge', 2),
                (lang_ids[2], 'Accent Tonique et Rythme', '''Le français est une langue chantante:
- Pas d'accent tonique fort comme l'anglais
- Rythme syllabique régulier
- Les mots s'enchaînent ensemble
Exemple: "Je suis français" = JUH-SWEE-FRAN-SAY
La musique du français vient de:
- Intonation montante et descendante
- Liaisons entre les mots
- Absence de pauses fortes
Écoutez des chansons françaises pour apprendre le rythme!''', 'rythme', 'Le français est une langue chantante', 3),
                (lang_ids[2], 'Mots Courants', '''Mots du quotidien avec prononciation:
- BONJOUR (bon-ZHOOR) - Bonjour
- MERCI (mair-SEE) - Merci
- OUI (wee) - Oui
- NON (non) - Non
- S'IL VOUS PLAÎT (see-voo-PLEH) - S'il vous plaît
- EAU (oh) - Eau
- PAIN (pan) - Pain
- VIN (van) - Vin
Écoutez la prononciation native 5 fois avant de répéter.''', 'mots', 'Écoutez la prononciation native', 4),
                (lang_ids[2], 'Liaison et Élision', '''Les liaisons sont essentielles:
Quand on prononce ensemble:
- Les enfants (lez-ON-fon) - liaison Z
- Vous avez (vooz-A-vay) - liaison Z
- Nous arrivons (noo-Z-a-ree-VON) - liaison Z
L'élision (supprimer le son):
- Le pomme → L'pomme (l'est pas dit)
- La heure → L'heure (la devient l')
Ces règles rendent le français fluide et musical!''', 'liaison', 'La liaison change la prononciation', 5),
                
                # German
                (lang_ids[3], 'Deutsche Vokale', '''Les 8 voyelles allemandes:
COURTES: /a/, /ɛ/, /ɪ/, /ɔ/, /ʊ/
LONGUES: /a:/, /e:/, /i:/, /o:/, /u:/
Exemple:
- BITTE (court I) vs BIETE (long I)
- STADT (court A) vs STAAT (long A)
Les voyelles longues prennent environ 2 fois plus longtemps.
Essayez de sentir la différence en parlant lentement.''', 'vokale', 'Kurze und lange Vokale klingen unterschiedlich', 1),
                (lang_ids[3], 'Umlaute und Eszett', '''Les sons spéciaux allemands:
Ä - comme dans SCHÄFER (le A avec deux points)
Ö - comme dans KÖLN (le O avec deux points)  
Ü - comme dans MÜNCHEN (le U avec deux points)
ß (Eszett) - son S long et fort
Ces sons n'existent pas dans beaucoup de langues.
Pratiquez chaque son 10 fois pour bien les prononcer.''', 'umlaute', 'Diese Laute existieren nicht in allen Sprachen', 2),
                (lang_ids[3], 'Konsonantenclusters', '''L'allemand a beaucoup de consonnes ensemble:
- SCHRANK (sh-consonant cluster) - shRank
- STRASSE (st consonant cluster) - stRah-seh
- SCHWARZ (sw consonant cluster) - shVarts
- SPRINGEN (sp consonant cluster) - shpRING-en
Ces groupes de consonnes sont difficiles!
Pratiquez chaque cluster lentement, puis plus vite.''', 'konsonanten', 'Deutsch hat viele Konsonantengruppen', 3),
                (lang_ids[3], 'Häufige Deutsche Wörter', '''10 mots allemands communs:
1. GUTEN TAG (GOO-ten tahg) - Bonjour
2. DANKE (DAHN-kuh) - Merci
3. BITTE (BIT-uh) - S'il vous plaît
4. JA (yah) - Oui
5. NEIN (nine) - Non
6. WASSER (VAH-ser) - Eau
7. BROT (broht) - Pain
8. BIER (beer) - Bière
9. STADT (shtaht) - Ville
10. HAUS (hows) - Maison
L'allemand a des règles de prononciation claires!''', 'worter', 'Das Deutsche hat klare Ausspracheregeln', 4),
                (lang_ids[3], 'Satzmelodie', '''La mélodie des phrases allemandes:
L'accent tonique est généralement sur la PREMIÈRE syllabe:
- MÜN-chen (Munich)
- HAM-burg (Hambourg)
- BER-lin (Berlin)
- DEUTSCH (allemand)
Mais pas toujours pour les mots composés!
La prononciation claire et précise est très importante en allemand.''', 'melodie', 'Die Betonung liegt meist auf der ersten Silbe', 5),
                
                # Spanish
                (lang_ids[4], 'Las Vocales Españolas', '''Los 5 sonidos vocálicos del español:
/a/ como en CASA - boca abierta
/e/ como en MESA - boca medio abierta
/i/ como en SILLA - boca cerrada, sonriendo
/o/ como en SOLO - labios redondeados
/u/ como en TUNA - labios muy redondeados
Las vocales españolas son más cortas que en inglés.
Practica cada una 5 veces seguidas.''', 'vocales', 'Las vocales españolas son más cortas que en inglés', 1),
                (lang_ids[4], 'La Consonante R', '''El sonido R es importante en español:
R SUAVE: UNA VEZ (perro, pero) - one tap of the tongue
RR FUERTE: DOS O MÁS VECES (perro, sierra) - rolled R
EJEMPLO:
- PERO (peh-RO) - pero (but)
- PERRO (peh-RRO) - perro (dog)
- CORO (KO-ro) - coro (choir)
- CORRO (KO-rrro) - corro (run)
¡La práctica hace al maestro! Intenta rodar la R.''', 'erre', 'Práctica de rolling R es importante', 2),
                (lang_ids[4], 'Sonidos Similares', '''Pares de sonidos difíciles:
- B y V: En español moderno suenan igual - VINO, BINO (mismo sonido)
- LL y Y: En muchas regiones suenan igual - LLAMAR, YAMAR
- C (antes de E, I) y Z: Sonido TH - CENA, ZONA
- G (antes de E, I) y J: Sonido gutural - GENTE, JEFE
El español tiene varios sonidos que varían por región.
Escucha hablantes de diferentes regiones hispanohablantes.''', 'sonidos', 'El español tiene varios sonidos sibilantes', 3),
                (lang_ids[4], 'Palabras Cotidianas', '''10 palabras españolas importantes:
1. HOLA (OH-la) - Hola
2. GRACIAS (GRAH-see-as) - Gracias
3. POR FAVOR (por fa-VOR) - Por favor
4. SÍ (see) - Sí
5. NO (no) - No
6. AGUA (AH-gwa) - Agua
7. PAN (pan) - Pan
8. VINO (VEE-no) - Vino
9. BUENAS NOCHES (BWEH-nas NOH-ches) - Buenas noches
10. ¿CÓMO ESTÁS? (KO-mo es-TAS) - ¿Cómo estás?
Escucha constantemente a hablantes nativos.''', 'palabras', 'Escucha hablantes nativos constantemente', 4),
                (lang_ids[4], 'Acentos Regionales', '''Variaciones de pronunciación española:
ESPAÑA (Madrid):
- C antes de E, I suena como TH
- LL suena como SH

MÉXICO:
- Pronunciación más clara
- R menos rolada que en otros lugares

ARGENTINA:
- LL suena como SH
- Acento italiano por la migración

COLOMBIA:
- Pronunciación muy clara
- Ritmo más pausado
Cada región tiene su encanto. ¡Aprende a reconocer los acentos!''', 'acentos', 'Cada región de España tiene su acento', 5),
                
                # Italian
                (lang_ids[5], 'Le Vocali Italiane', '''I 5 suoni vocalici dell'italiano:
/a/ come in CASA - bocca aperta
/e/ come in BELLO - bocca semi-aperta, tono medio
/i/ come in VINO - bocca chiusa, sorridendo
/o/ come in BOLO - labbra arrotondate, tono medio
/u/ come in LUNA - labbra molto arrotondate
L'italiano ha vocali chiare e distinte.
Pronuncia ogni suono con chiarezza, non veloce.''', 'vocali', 'L\'italiano ha vocali chiare e distinte', 1),
                (lang_ids[5], 'Consonanti Doppie', '''Le consonanti doppie cambiano completamente il suono:
MELA (MEH-la) - apple - consonante singola
MELLA (MEL-la) - dent - consonante doppia
CARO (KAH-ro) - dear - consonante singola  
CARRO (KAR-ro) - car - consonante doppia
Le doppie si pronunciano tenendo il suono più a lungo.
Ascolta la differenza: è molto importante!''', 'doppie', 'Le doppie cambiano completamente il suono', 2),
                (lang_ids[5], 'Suoni c e g', '''CA, CO, CU = suono K duro
- CALDO (KAL-do) - caldo
- CORPO (KOR-po) - corpo
- CURVA (KUR-va) - curva

CE, CI = suono CH dolce
- CENA (CHEN-a) - cena
- CIAO (CHOW) - ciao

GA, GO, GU = suono G duro
- GATTO (GAT-to) - gatto
- GORDO (GOR-do) - gordo

GE, GI = suono J
- GENTE (JEN-te) - gente
- GIRO (JEE-ro) - giro
La posizione della vocale cambia completamente il suono!''', 'suoni', 'La posizione della vocale cambia il suono', 3),
                (lang_ids[5], 'Parole Comuni', '''10 parole italiane comuni:
1. CIAO (CHOW) - Ciao
2. GRAZIE (GRAH-tsee-eh) - Grazie
3. PREGO (PREH-go) - Prego
4. SÌ (see) - Sì
5. NO (no) - No
6. ACQUA (AH-kwa) - Acqua
7. PANE (PAH-neh) - Pane
8. VINO (VEE-no) - Vino
9. BUONGIORNO (bwon-JOR-no) - Buongiorno
10. BUONASERA (bwoh-na-SEH-ra) - Buonasera
L'italiano ha una pronuncia relativamente regolare!''', 'parole', 'L\'italiano ha una pronuncia relativamente regolare', 4),
                (lang_ids[5], 'Ritmo e Intonazione', '''L'italiano è una lingua musicale con ritmo particolare:
FRASI LUNGHE: "Mi piacerebbe andare al cinema stasera"
- Pronuncia in modo fluido, non veloce
- L'intonazione sale e scende dolcemente
ESCLAMAZIONI:
- BRAVO! (BRAH-vo) - esclamazione positiva
- ACCIDENTI! (ah-chee-DEN-tee) - esclamazione negativa
- BELLISSIMO! (bel-LIS-see-mo) - bellissimo
L'italiano è una lingua musicale - ascolta cantanti italiani!''', 'ritmo', 'L\'italiano è una lingua musicale', 5),
                
                # Chinese
                (lang_ids[6], '普通话的四声', '''汉语中有四个声调:
第一声 (高平) ⎯ mā - 妈 (mamma)
第二声 (上升) ⟋ má - 麻 (hemp)
第三声 (低凹) ⌢ mǎ - 马 (horse)
第四声 (下降) ⌞ mà - 骂 (scold)

同一个音节，四声不同，意思完全不同！
练习: 妈、麻、马、骂 - 听听有什么不同
声调错误会改变词义，所以声调很重要!''', 'shengdiao', '声调错误会改变词义', 1),
                (lang_ids[6], '汉语辅音', '''普通话有21个辅音，分为清浊音:
清音 (不用声带): p, t, k, q, c, ch, f, s, sh, x
浊音 (用声带): b, d, g, j, z, zh, r
鼻音: m, n, ng
流音: l, w, y

例子:
- P音: 拍 (pāi) - 拍照
- B音: 百 (bǎi) - 百年
- T音: 太 (tài) - 太好
- D音: 大 (dà) - 大门
请把手放在喉咙上感受清浊音的区别!''', 'fuyin', '普通话有21个辅音', 2),
                (lang_ids[6], '汉语元音', '''汉语中的元音和复元音:
单元音:
- a (啊) - 张大嘴巴
- e (呃) - 嘴巴放松
- i (伊) - 嘴角上扬
- o (哦) - 嘴唇圆形
- u (乌) - 嘴唇突出
- ü (鱼) - 嘴唇圆形+舌头靠前

复元音:
- ai (爱) - a+i
- ei (诶) - e+i
- ao (凹) - a+o
- ou (欧) - o+u
- ia (呀) - i+a
- ie (耶) - i+e
发音时要注意嘴形的变化!''', 'yuanyin', '发音时要注意嘴形', 3),
                (lang_ids[6], '常用汉字发音', '''10个常用中文词汇:
1. 你好 (nǐ hǎo) - 你好
2. 谢谢 (xièxiè) - 谢谢
3. 对不起 (duìbúqǐ) - 对不起
4. 没关系 (méi guānxì) - 没关系
5. 是 (shì) - 是
6. 不是 (búshì) - 不是
7. 水 (shuǐ) - 水
8. 米饭 (mǐfàn) - 米饭
9. 谢谢 (xièxiè) - 谢谢
10. 再见 (zàijiàn) - 再见
多练习绕口令来提高发音!''', 'hanzi', '多练习绕口令', 4),
                (lang_ids[6], '声调练习', '''四声辨别训练:
妈 - 麻 - 马 - 骂 (都是ma的不同音)
区别:
- 妈 (mā) 妈妈 - mother (高声)
- 麻 (má) 亚麻布 - linen (上升)
- 马 (mǎ) 骑马 - horse (低凹)
- 骂 (mà) 骂人 - scold (下降)

练习方法:
1. 先听原声
2. 跟着念3次
3. 自己独立念
4. 对比原声
听力是学习普通话的关键!''', 'liaoshi', '听力是关键', 5),
                
                # Japanese
                (lang_ids[7], 'ひらがなの発音', '''ひらがなの基本46音:
あ行 (a,i,u,e,o) - あいうえお
か行 (ka,ki,ku,ke,ko) - かきくけこ
さ行 (sa,si,su,se,so) - さしすせそ
た行 (ta,ti,tu,te,to) - たちつてと
な行 (na,ni,nu,ne,no) - なにぬねの
は行 (ha,hi,hu,he,ho) - はひふへほ
ま行 (ma,mi,mu,me,mo) - まみむめも
や行 (ya,yu,yo) - やゆよ
ら行 (ra,ri,ru,re,ro) - らりるれろ
わ行 (wa,o,n) - わをん

日本語の基本は5つの母音 (a,i,u,e,o) です!''', 'hiragana', '日本語の基本は5つの母音', 1),
                (lang_ids[7], 'カタカナの発音', '''カタカナも46音で、ひらがなと同じ:
あ → ア
か → カ
さ → サ
外来語はカタカナで書きます:
- コンピュータ (konpyūta) - computer
- インターネット (intānetto) - internet
- ビジネス (bijinesu) - business
- テレビ (terebi) - television
- ラジオ (rajio) - radio

カタカナは特に外国語や新しい言葉に使います!''', 'katakana', '外来語はカタカナで書く', 2),
                (lang_ids[7], '長音と短音', '''日本語での長短音の違い:
えい vs おー:
- SEMPAI (せんぱい) - senior (えい)
- SENSEI (せんせい) - teacher (えい)
- OKAASAN (おかあさん) - mother (ああ)
- ONEESAN (おねえさん) - older sister (ええ)

長音は意味を変える可能性があります:
- ここ (koko) - here
- こうこう (koukoo) - high school
発音と意味の関係をしっかり理解しましょう!''', 'chouon', '長音は意味を変える可能性', 3),
                (lang_ids[7], 'よく使う単語', '''10個の日本語日常用語:
1. こんにちは (konnichiha) - こんにちは
2. ありがとう (arigatou) - ありがとう
3. すみません (sumimasen) - すみません
4. はい (hai) - はい
5. いいえ (iie) - いいえ
6. 水 (mizu) - 水
7. ご飯 (gohan) - ご飯
8. お酒 (osake) - お酒
9. さようなら (sayounara) - さようなら
10. おやすみなさい (oyasuminasai) - おやすみなさい
ネイティブの発音をよく聞く練習が大事です!''', 'tango', 'ネイティブの発音をよく聞く', 4),
                (lang_ids[7], 'アクセントと抑揚', '''標準日本語 (東京方言) のアクセント:
日本語は英語ほど強いアクセントがありません。
むしろ音の高さが変わります:

例:
- 橋 (はし) - bridge - 高い-低い
- 箸 (はし) - chopsticks - 低い-高い
- 雨 (あめ) - rain - 高い-低い
- 飴 (あめ) - candy - 低い-高い

東京方言の特徴:
- 最後の音が低くなることが多い
- 音の流れが重要
標準日本語のアクセント位置をしっかり覚えましょう!''', 'akusento', '標準日本語のアクセント位置', 5),
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
