from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from googletrans import Translator
import pinyin
import pandas as pd
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
translator = Translator()

# Загрузка данных из файлов
def load_word_dict_from_xlsx(file_path):
    df = pd.read_excel(file_path)
    if 'char' not in df.columns or 'pinyin' not in df.columns or 'translation' not in df.columns or 'hsk_level' not in df.columns:
        raise ValueError("Required columns are missing in the new xlsx file")
    word_dict = {row['char']: list(row['char']) for _, row in df.iterrows()}
    pinyin_dict = {row['char']: re.sub(r'[\[\]]', '', row['pinyin']).strip() for _, row in df.iterrows()}
    translation_dict = {row['char']: row['translation'].strip().lower() for _, row in df.iterrows()}
    hsk_dict = {row['char']: row['hsk_level'] for _, row in df.iterrows()}
    return word_dict, pinyin_dict, translation_dict, hsk_dict

word_dict, pinyin_dict, translation_dict, hsk_dict = load_word_dict_from_xlsx('new_hsk_chars.xlsx')

def find_words(known_chars):
    """Находит слова, содержащие все иероглифы из известного набора и не показывать уже известные слова"""
    return [word for word, chars in word_dict.items() if all(char in known_chars for char in chars) and word not in known_chars]

def translate_word(word):
    """Переводит слово на русский язык"""
    translation = translator.translate(word, src='zh-cn', dest='ru')
    return translation.text

def get_pinyin(word):
    """Возвращает пиньинь для китайского слова"""
    return pinyin.get(word, format='strip', delimiter=' ')

def clean_chars_input(chars):
    """Очищает и нормализует вводимые иероглифы (удаляет пробелы и запятые)"""
    return re.findall(r'\S', chars)  # Разделяет строку по символам, игнорируя пробелы и запятые

def get_hsk_level_for_char(char, words):
    """Возвращает уровень HSK для символа на основе слов, содержащих этот символ"""
    max_hsk_level = 0
    for word in words:
        if char in word_dict.get(word, []):
            hsk_level = hsk_dict.get(word, '0')
            try:
                level = int(hsk_level)
                if level > max_hsk_level:
                    max_hsk_level = level
            except ValueError:
                pass
    return str(max_hsk_level) if max_hsk_level > 0 else 'Unknown'

@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        known_chars = conn.execute('SELECT char FROM known_chars WHERE user_id = ?', (user_id,)).fetchall()
        conn.close()
        known_chars = [char['char'] for char in known_chars]
        
        # Преобразование списка символов в строку без начальной запятой
        known_chars_str = ', '.join(known_chars) if known_chars else 'No known characters'
        
        return render_template('index.html', known_chars_str=known_chars_str)
    return render_template('index.html', known_chars_str='No known characters')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if username and password:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful. Please log in.')
        except sqlite3.IntegrityError:
            flash('User with this username already exists.')
        conn.close()
    else:
        flash('Please fill in both fields.')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username and password:
        conn = get_db_connection()
        user = conn.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            flash(f'Welcome, {username}!')
        else:
            flash('Invalid username or password.')
        conn.close()
    else:
        flash('Please fill in both fields.')
    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/add_chars', methods=['POST'])
def add_chars():
    if 'user_id' in session:
        user_id = session['user_id']
        chars = request.form['chars']
        if chars:
            chars_list = clean_chars_input(chars)
            conn = get_db_connection()
            
            added_chars = []
            for char in chars_list:
                existing_char = conn.execute('SELECT 1 FROM known_chars WHERE user_id = ? AND char = ?', (user_id, char)).fetchone()
                if not existing_char:
                    conn.execute('INSERT INTO known_chars (user_id, char) VALUES (?, ?)', (user_id, char))
                    added_chars.append(char)
            
            conn.commit()
            conn.close()
            if added_chars:
                flash(f'Characters added: {", ".join(added_chars)}.')
            else:
                flash('No new characters added.')
        else:
            flash('Please enter characters or text.')
    return redirect(url_for('index'))

@app.route('/remove_chars', methods=['POST'])
def remove_chars():
    if 'user_id' in session:
        user_id = session['user_id']
        chars = request.form['chars']
        if chars:
            chars_list = clean_chars_input(chars)
            conn = get_db_connection()
            
            known_chars = conn.execute('SELECT char FROM known_chars WHERE user_id = ?', (user_id,)).fetchall()
            known_chars_set = set(char['char'] for char in known_chars)
            
            removed_chars = []
            for char in chars_list:
                if char in known_chars_set:
                    conn.execute('DELETE FROM known_chars WHERE user_id = ? AND char = ?', (user_id, char))
                    removed_chars.append(char)
            
            conn.commit()
            conn.close()
            if removed_chars:
                flash(f'Characters removed: {", ".join(removed_chars)}.')
            else:
                flash('No characters removed.')
        else:
            flash('Please enter characters or text.')
    return redirect(url_for('index'))

@app.route('/known_chars')
def known_chars_view():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        known_chars = conn.execute('SELECT char FROM known_chars WHERE user_id = ? ORDER BY rowid DESC', (user_id,)).fetchall()
        conn.close()
        known_chars = [char['char'] for char in known_chars]

        # Получаем все слова для проверки
        words = list(word_dict.keys())
        
        hsk_levels = {char: get_hsk_level_for_char(char, words) for char in known_chars}

        # Нумерация начинается с 1
        known_chars_list = list(enumerate(known_chars, start=1))

        return render_template('known_chars.html', known_chars=known_chars_list, hsk_levels=hsk_levels)
    return redirect(url_for('index'))

@app.route('/find_words')
def find_words_view():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        known_chars = conn.execute('SELECT char FROM known_chars WHERE user_id = ?', (user_id,)).fetchall()
        conn.close()
        known_chars = [char['char'] for char in known_chars]
        words = find_words(known_chars)

        # Получение параметра сортировки из URL
        hsk_level = request.args.get('hsk_level', None)  # Новый параметр для пользовательской сортировки

        translations = {word: translation_dict.get(word, '') for word in words} if words else {}
        pinyins = {word: pinyin_dict.get(word, '').replace(' ', '') for word in words} if words else {}
        hsk_levels = {word: hsk_dict.get(word, 'Unknown') for word in words} if words else {}

        # Функция для получения уровня HSK как целого числа
        def get_hsk_level(word):
            level = hsk_levels.get(word, '0')  # Получаем уровень HSK, значение по умолчанию '0'
            # Приводим level к строке перед вызовом isdigit(), затем конвертируем в int
            return int(level) if str(level).isdigit() else 0

        # Обработка сортировки по уровню HSK
        if hsk_level:
            words_sorted = [word for word in words if get_hsk_level(word) == int(hsk_level)]
        else:
            words_sorted = sorted(words, key=get_hsk_level)  # По умолчанию сортировка по уровню HSK

        # Обновляем словари с учетом сортировки
        translations = {word: translations[word] for word in words_sorted}
        pinyins = {word: pinyins[word] for word in words_sorted}
        hsk_levels = {word: hsk_levels[word] for word in words_sorted}

        return render_template('find_words.html', translations=translations, pinyins=pinyins, hsk_levels=hsk_levels)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
