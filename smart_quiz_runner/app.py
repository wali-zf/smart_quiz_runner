import sqlite3
import os
import webbrowser 
import csv 
import random 
from datetime import datetime 
from io import StringIO 
from threading import Timer 
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_quiz_app'

# Configure Uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists('database.db'):
        conn = get_db_connection()
        with open('schema.sql') as f:
            conn.executescript(f.read())
        conn.close()
        print("Database initialized!")

def check_schema_updates():
    """Automatically adds new columns for the upgrade."""
    conn = get_db_connection()
    
    # Quiz Table Updates
    quiz_cols = {
        'time_limit': 'INTEGER DEFAULT 0',
        'strict_mode': 'INTEGER DEFAULT 0',
        'deadline': 'TEXT',
        'passing_score': 'INTEGER DEFAULT 0',
        'max_attempts': 'INTEGER DEFAULT 0'
    }
    for col, dtype in quiz_cols.items():
        try:
            conn.execute(f'SELECT {col} FROM quizzes LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute(f'ALTER TABLE quizzes ADD COLUMN {col} {dtype}')

    # User Table Updates (Profile)
    user_cols = {
        'full_name': 'TEXT',
        'profile_image': 'TEXT'
    }
    for col, dtype in user_cols.items():
        try:
            conn.execute(f'SELECT {col} FROM users LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute(f'ALTER TABLE users ADD COLUMN {col} {dtype}')

    # Question Table Updates (Images & Types)
    q_cols = {
        'question_type': "TEXT DEFAULT 'mcq'", # mcq, true_false, text
        'image_path': 'TEXT'
    }
    for col, dtype in q_cols.items():
        try:
            conn.execute(f'SELECT {col} FROM questions LIMIT 1')
        except sqlite3.OperationalError:
            conn.execute(f'ALTER TABLE questions ADD COLUMN {col} {dtype}')
    
    conn.commit()
    conn.close()

# --- Auth & Profile ---

@app.route('/')
def home():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name'] if user['full_name'] else user['username']
            session['profile_image'] = user['profile_image']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (request.form['username'], request.form['password'], request.form['role']))
            conn.commit()
            conn.close()
            flash('Account created! Please login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username taken.')
            conn.close()
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if request.method == 'POST':
        # 1. Update Basic Info
        full_name = request.form.get('full_name')
        if full_name:
            conn.execute('UPDATE users SET full_name = ? WHERE id = ?', (full_name, session['user_id']))
            session['full_name'] = full_name # Update session

        # 2. Handle Image Upload
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                conn.execute('UPDATE users SET profile_image = ? WHERE id = ?', (filename, session['user_id']))
                session['profile_image'] = filename

        # 3. Update Password
        if request.form.get('new_password'):
            current_pass = request.form.get('current_password')
            user = conn.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],)).fetchone()
            if user['password'] == current_pass:
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (request.form['new_password'], session['user_id']))
                flash('Profile and password updated!')
            else:
                flash('Incorrect current password. Other changes saved.')
        else:
            flash('Profile updated!')
        
        conn.commit()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Quiz Logic ---

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    search = request.args.get('q', '')
    conn = get_db_connection()
    
    query = '''SELECT q.*, u.username as creator_name FROM quizzes q JOIN users u ON q.creator_id = u.id'''
    params = []
    
    if session['role'] == 'teacher':
        query += ' WHERE q.creator_id = ?'
        params.append(session['user_id'])
        if search: 
            query += ' AND q.title LIKE ?'
            params.append(f'%{search}%')
    elif search:
        query += ' WHERE q.title LIKE ?'
        params.append(f'%{search}%')
        
    quizzes = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('dashboard.html', quizzes=quizzes, search_query=search)

@app.route('/create_quiz', methods=('GET', 'POST'))
def create_quiz():
    if session.get('role') != 'teacher': return redirect(url_for('dashboard'))
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('''INSERT INTO quizzes (title, creator_id, time_limit, strict_mode, deadline, passing_score, max_attempts) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (request.form['title'], session['user_id'], request.form.get('time_limit',0), 
                      1 if request.form.get('strict_mode') else 0, request.form.get('deadline'), 
                      request.form.get('passing_score',0), request.form.get('max_attempts',0)))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('create_quiz.html')

@app.route('/edit_quiz/<int:quiz_id>', methods=('GET', 'POST'))
def edit_quiz(quiz_id):
    if session.get('role') != 'teacher': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    if request.method == 'POST':
        conn.execute('''UPDATE quizzes SET title=?, time_limit=?, strict_mode=?, deadline=?, passing_score=?, max_attempts=? WHERE id=?''',
                     (request.form['title'], request.form.get('time_limit',0), 1 if request.form.get('strict_mode') else 0,
                      request.form.get('deadline'), request.form.get('passing_score',0), request.form.get('max_attempts',0), quiz_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    quiz = conn.execute('SELECT * FROM quizzes WHERE id=?', (quiz_id,)).fetchone()
    conn.close()
    return render_template('edit_quiz.html', quiz=quiz)

@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    if session.get('role') != 'teacher': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    conn.execute('DELETE FROM questions WHERE quiz_id=?', (quiz_id,))
    conn.execute('DELETE FROM results WHERE quiz_id=?', (quiz_id,))
    conn.execute('DELETE FROM quizzes WHERE id=?', (quiz_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

# --- Advanced Question Management ---

@app.route('/quiz/<int:quiz_id>/questions', methods=('GET', 'POST'))
def manage_questions(quiz_id):
    if session.get('role') != 'teacher': return redirect(url_for('dashboard'))
    conn = get_db_connection()

    if request.method == 'POST':
        q_type = request.form['question_type']
        q_text = request.form['question_text']
        
        # Handle Image
        image_path = None
        if 'question_image' in request.files:
            file = request.files['question_image']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"q_{quiz_id}_{datetime.now().timestamp()}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename

        # Handle Options based on Type
        options = ""
        correct_answer = ""

        if q_type == 'mcq':
            # Collect non-empty options
            opts = [request.form.get(f'option{i}') for i in range(1, 5)]
            opts = [o for o in opts if o and o.strip()] # Remove empty
            options = "|".join(opts)
            
            # Map "Option A/B/C/D" to real value
            sel = request.form.get('correct_answer_mcq')
            idx_map = {'Option A':0, 'Option B':1, 'Option C':2, 'Option D':3}
            if sel in idx_map and idx_map[sel] < len(opts):
                correct_answer = opts[idx_map[sel]]
            else:
                correct_answer = opts[0] if opts else ""

        elif q_type == 'true_false':
            options = "True|False"
            correct_answer = request.form.get('correct_answer_tf')

        elif q_type == 'text':
            options = "" # No options for text input
            correct_answer = request.form.get('correct_answer_text')

        conn.execute('''INSERT INTO questions (quiz_id, question_text, options, correct_answer, question_type, image_path) 
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (quiz_id, q_text, options, correct_answer, q_type, image_path))
        conn.commit()
        flash('Question added!')

    quiz = conn.execute('SELECT * FROM quizzes WHERE id=?', (quiz_id,)).fetchone()
    questions = conn.execute('SELECT * FROM questions WHERE quiz_id=?', (quiz_id,)).fetchall()
    conn.close()
    return render_template('add_questions.html', quiz=quiz, questions=questions)

@app.route('/delete_question/<int:question_id>', methods=['POST'])
def delete_question(question_id):
    conn = get_db_connection()
    q = conn.execute('SELECT quiz_id FROM questions WHERE id=?', (question_id,)).fetchone()
    if q and session.get('role') == 'teacher':
        conn.execute('DELETE FROM questions WHERE id=?', (question_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('manage_questions', quiz_id=q['quiz_id']))

# --- Taking Quiz (Updated for Types) ---

@app.route('/take_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id=?', (quiz_id,)).fetchone()
    
    # Checks (Deadline, Attempts)
    if quiz['deadline'] and datetime.now().strftime('%Y-%m-%dT%H:%M') > quiz['deadline']:
        conn.close(); flash('Quiz Expired'); return redirect(url_for('dashboard'))
    if quiz['max_attempts'] > 0:
        used = conn.execute('SELECT COUNT(*) FROM results WHERE quiz_id=? AND user_id=?', (quiz_id, session['user_id'])).fetchone()[0]
        if request.method == 'GET' and used >= quiz['max_attempts']:
            conn.close(); flash('Max attempts reached'); return redirect(url_for('dashboard'))

    if request.method == 'POST':
        score = 0
        questions = conn.execute('SELECT * FROM questions WHERE quiz_id=?', (quiz_id,)).fetchall()
        feedback = []
        
        for q in questions:
            user_ans = request.form.get(str(q['id']), '').strip()
            correct_ans = q['correct_answer']
            is_correct = False
            
            # Smart Grading
            if q['question_type'] == 'text':
                # Case insensitive comparison for text answers
                if user_ans.lower() == correct_ans.lower():
                    is_correct = True
            else:
                # Exact match for MCQ/TF
                if user_ans == correct_ans:
                    is_correct = True
            
            if is_correct: score += 1
            feedback.append({'question': q['question_text'], 'user_answer': user_ans, 'correct_answer': correct_ans, 'is_correct': is_correct})
            
        pct = round((score/len(questions)*100),1) if questions else 0
        conn.execute('INSERT INTO results (user_id, quiz_id, score) VALUES (?, ?, ?)', (session['user_id'], quiz_id, score))
        conn.commit()
        conn.close()
        return render_template('result.html', score=score, total=len(questions), feedback=feedback, percentage=pct, pass_mark=quiz['passing_score'])

    questions_db = conn.execute('SELECT * FROM questions WHERE quiz_id=?', (quiz_id,)).fetchall()
    conn.close()
    
    questions = []
    for q in questions_db:
        d = dict(q)
        if d['options']:
            opts = d['options'].split('|')
            if d['question_type'] == 'mcq': random.shuffle(opts) # Only shuffle MCQs
            d['options_list'] = opts
        questions.append(d)
    random.shuffle(questions)
    
    return render_template('take_quiz.html', quiz=quiz, questions=questions)

# --- Reporting ---
@app.route('/quiz/<int:quiz_id>/results')
def view_results(quiz_id):
    if session.get('role') != 'teacher': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    quiz = conn.execute('SELECT * FROM quizzes WHERE id=?', (quiz_id,)).fetchone()
    results = conn.execute('''SELECT u.full_name, u.username, r.score, r.timestamp FROM results r JOIN users u ON r.user_id=u.id WHERE r.quiz_id=? ORDER BY r.score DESC''', (quiz_id,)).fetchall()
    conn.close()
    
    count = len(results)
    avg = round(sum(r['score'] for r in results)/count, 2) if count else 0
    high = max([r['score'] for r in results]) if count else 0
    return render_template('quiz_results.html', quiz=quiz, results=results, total_attempts=count, avg_score=avg, highest_score=high)

@app.route('/export_results/<int:quiz_id>')
def export_results(quiz_id):
    if session.get('role') != 'teacher': return redirect(url_for('dashboard'))
    conn = get_db_connection()
    results = conn.execute('''SELECT u.full_name, u.username, r.score, r.timestamp FROM results r JOIN users u ON r.user_id=u.id WHERE r.quiz_id=?''', (quiz_id,)).fetchall()
    conn.close()
    si = StringIO(); cw = csv.writer(si)
    cw.writerow(['Name', 'Username', 'Score', 'Date']); [cw.writerow([r['full_name'] or r['username'], r['username'], r['score'], r['timestamp']]) for r in results]
    return make_response(si.getvalue(), {'Content-Disposition': f'attachment; filename=results_{quiz_id}.csv', 'Content-type': 'text/csv'})

@app.route('/my_results')
def student_history():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    history = conn.execute('SELECT q.title, r.score, r.timestamp FROM results r JOIN quizzes q ON r.quiz_id=q.id WHERE r.user_id=? ORDER BY r.timestamp DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('student_history.html', history=history)

if __name__ == '__main__':
    init_db()
    check_schema_updates()
    Timer(1, lambda: webbrowser.open_new('http://127.0.0.1:5000/')).start()
    app.run(debug=True)