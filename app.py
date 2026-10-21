import os
import json
import random
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'gomobile_super_secure_secret_key_2026')

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        g.user = cursor.fetchone()
        conn.close()

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Silakan masuk (login) atau daftar terlebih dahulu untuk mengakses fitur ini.", "info")
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view

def teacher_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Halaman portal pengajar khusus untuk akun guru. Silakan login terlebih dahulu.", "warning")
            return redirect(url_for('login', role='pengajar', next=request.url))
        if g.user['role'] != 'pengajar':
            flash("Akses ditolak: Akun Anda terdaftar sebagai Siswa. Portal ini khusus untuk Pengajar.", "danger")
            return redirect(url_for('index'))
        return view(**kwargs)
    return wrapped_view

# ========================================================
# 1. BERANDA (HOME)
# ========================================================
@app.route('/')
def index():
    conn = get_db()
    cursor = conn.cursor()

    # Get featured articles for Ruang Baca highlight
    cursor.execute("SELECT * FROM articles ORDER BY id DESC LIMIT 3")
    featured_articles = cursor.fetchall()

    conn.close()
    return render_template('index.html', featured_articles=featured_articles)

# ========================================================
# 2. AUTENTIKASI: LOGIN & REGISTRASI (SISWA & PENGAJAR)
# ========================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identity = request.form.get('identity', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'siswa').strip()

        if not identity or not password:
            flash("ID Pengguna / Email dan Kata Sandi wajib diisi.", "danger")
            return render_template('login.html')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE (username = ? OR email = ?)",
            (identity, identity)
        )
        user = cursor.fetchone()
        conn.close()

        if user is None:
            flash("Akun dengan ID/Email tersebut tidak ditemukan di database. Silakan daftar terlebih dahulu.", "danger")
            return render_template('login.html')

        if not check_password_hash(user['password_hash'], password):
            flash("Kata sandi yang Anda masukkan salah. Silakan coba lagi.", "danger")
            return render_template('login.html')

        # Store session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['user_name'] = user['full_name']
        session['role'] = user['role']

        flash(f"Selamat datang kembali, {user['full_name']}! Anda masuk sebagai {user['role'].capitalize()}.", "success")

        # Redirect based on role or next url
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)

        if user['role'] == 'pengajar':
            return redirect(url_for('teacher_dashboard'))
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        school = request.form.get('school', '').strip()
        role = request.form.get('role', 'siswa').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not full_name or not username or not email or not password:
            flash("Semua field wajib diisi.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Kata sandi minimal 6 karakter.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Konfirmasi kata sandi tidak cocok.", "danger")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()

        # Check existing username or email
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("Username atau Email sudah terdaftar di database. Silakan gunakan yang lain atau langsung login.", "danger")
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        cursor.execute('''
        INSERT INTO users (username, email, password_hash, full_name, role, phone, school)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, full_name, role, phone, school))
        conn.commit()
        conn.close()

        flash("Pendaftaran berhasil disimpan ke database! Silakan masuk dengan ID dan password baru Anda.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Anda telah berhasil keluar dari akun GoMobile.", "info")
    return redirect(url_for('index'))

# ========================================================
# 3. RUANG BELAJAR (LATIHAN SOAL KELAS 10, 11, 12 SMA)
# ========================================================
@app.route('/ruang-belajar')
def ruang_belajar():
    conn = get_db()
    cursor = conn.cursor()

    # Count questions per grade
    cursor.execute("SELECT COUNT(*) FROM questions WHERE grade = 10")
    count_10 = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions WHERE grade = 11")
    count_11 = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions WHERE grade = 12")
    count_12 = cursor.fetchone()[0]

    # Fetch recent results if logged in
    recent_results = []
    if g.user:
        cursor.execute('''
        SELECT * FROM quiz_results
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 5
        ''', (g.user['id'],))
        recent_results = cursor.fetchall()

    conn.close()
    return render_template(
        'ruang_belajar.html',
        count_10=count_10,
        count_11=count_11,
        count_12=count_12,
        recent_results=recent_results
    )

@app.route('/ruang-belajar/kelas/<int:grade>')
def paket_soal(grade):
    if grade not in [10, 11, 12]:
        flash("Jenjang kelas tidak valid. Pilih Kelas 10, 11, atau 12 SMA.", "warning")
        return redirect(url_for('ruang_belajar'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE grade = ? ORDER BY id ASC", (grade,))
    questions = cursor.fetchall()
    conn.close()

    if not questions:
        flash(f"Belum ada soal latihan untuk Kelas {grade} SMA.", "info")
        return redirect(url_for('ruang_belajar'))

    return render_template('paket_soal.html', grade=grade, questions=questions)

@app.route('/ruang-belajar/submit', methods=['POST'])
def submit_quiz():
    grade = int(request.form.get('grade', 10))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE grade = ? ORDER BY id ASC", (grade,))
    questions = cursor.fetchall()

    total_questions = len(questions)
    correct_count = 0
    wrong_count = 0
    detailed_answers = []

    for q in questions:
        user_choice = request.form.get(f'answer_{q["id"]}', '').strip().upper()
        is_correct = (user_choice == q['correct_option'])

        if is_correct:
            correct_count += 1
        else:
            wrong_count += 1

        # Map choice letter to text
        option_map = {
            'A': q['option_a'],
            'B': q['option_b'],
            'C': q['option_c'],
            'D': q['option_d'],
            'E': q['option_e']
        }

        detailed_answers.append({
            'question_id': q['id'],
            'subject': q['subject'],
            'question_text': q['question_text'],
            'user_answer': user_choice or 'Tidak Dijawab',
            'user_answer_text': option_map.get(user_choice, '-'),
            'correct_option': q['correct_option'],
            'correct_option_text': option_map.get(q['correct_option'], '-'),
            'is_correct': is_correct,
            'explanation': q['explanation']
        })

    score = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0
    user_id = g.user['id'] if g.user else 1 # fallback guest

    # Save to database
    cursor.execute('''
    INSERT INTO quiz_results (user_id, grade, total_questions, correct_answers, wrong_answers, score, answers_json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, grade, total_questions, correct_count, wrong_count, score, json.dumps(detailed_answers)))
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()

    flash(f"Latihan selesai! Anda menjawab {correct_count} Benar dan {wrong_count} Salah.", "success")
    return redirect(url_for('quiz_result', result_id=result_id))

@app.route('/ruang-belajar/hasil/<int:result_id>')
def quiz_result(result_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quiz_results WHERE id = ?", (result_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        flash("Hasil latihan tidak ditemukan.", "danger")
        return redirect(url_for('ruang_belajar'))

    review_items = json.loads(result['answers_json']) if result['answers_json'] else []
    return render_template('quiz_result.html', result=result, review_items=review_items)

# ========================================================
# 4. RUANG BACA (ARTIKEL HITS, SEJARAH & TIPS UTBK)
# ========================================================
@app.route('/ruang-baca')
def ruang_baca():
    category = request.args.get('kat', 'semua')
    query = request.args.get('q', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    sql = "SELECT * FROM articles WHERE 1=1"
    params = []

    if category != 'semua' and category:
        sql += " AND category = ?"
        params.append(category)

    if query:
        sql += " AND (title LIKE ? OR summary LIKE ? OR content LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

    sql += " ORDER BY id DESC"
    cursor.execute(sql, params)
    articles = cursor.fetchall()
    conn.close()

    return render_template(
        'ruang_baca.html',
        articles=articles,
        current_cat=category,
        search_query=query
    )

@app.route('/ruang-baca/<int:article_id>')
def artikel_detail(article_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Increment view count
    cursor.execute("UPDATE articles SET views = views + 1 WHERE id = ?", (article_id,))
    conn.commit()

    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    conn.close()

    if not article:
        flash("Artikel tidak ditemukan di Ruang Baca.", "danger")
        return redirect(url_for('ruang_baca'))

    return render_template('artikel_detail.html', article=article)

# ========================================================
# 5. PAKET BERBAYAR & CHECKOUT QRIS
# (Rp 800.000, Rp 700.000, Rp 500.000)
# ========================================================
@app.route('/paket-berbayar')
def paket_berbayar():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packages ORDER BY price DESC")
    raw_packages = cursor.fetchall()
    conn.close()

    packages = []
    for p in raw_packages:
        pkg_dict = dict(p)
        pkg_dict['features'] = json.loads(p['features_json'])
        pkg_dict['modules'] = json.loads(p['modules_json'])
        packages.append(pkg_dict)

    return render_template('paket_berbayar.html', packages=packages)

@app.route('/checkout')
def checkout():
    paket_id = request.args.get('paket_id', 1, type=int)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packages WHERE id = ?", (paket_id,))
    selected_package = cursor.fetchone()
    conn.close()

    if not selected_package:
        flash("Paket yang Anda pilih tidak ditemukan.", "danger")
        return redirect(url_for('paket_berbayar'))

    current_user_dict = dict(g.user) if g.user else None
    return render_template(
        'checkout.html',
        selected_package=selected_package,
        current_user=current_user_dict
    )

@app.route('/checkout/process', methods=['POST'])
def process_checkout():
    package_id = request.form.get('package_id', type=int)
    proof_note = request.form.get('proof_note', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM packages WHERE id = ?", (package_id,))
    package = cursor.fetchone()
    if not package:
        conn.close()
        flash("Paket belajar tidak valid.", "danger")
        return redirect(url_for('paket_berbayar'))

    # If user is already logged in
    if g.user:
        user_id = g.user['id']
        buyer_name = g.user['full_name']
        buyer_email = g.user['email']
        buyer_phone = g.user['phone'] or '08123456789'
        buyer_school = g.user['school'] or 'SMA'
    else:
        # Register new student account immediately
        buyer_name = request.form.get('buyer_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        buyer_email = request.form.get('buyer_email', '').strip().lower()
        buyer_phone = request.form.get('buyer_phone', '').strip()
        buyer_school = request.form.get('buyer_school', '').strip()

        if not buyer_name or not username or not password or not buyer_email:
            conn.close()
            flash("Semua data pendaftaran akun wajib diisi untuk registrasi paket.", "danger")
            return redirect(url_for('checkout', paket_id=package_id))

        # Check existing user
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, buyer_email))
        existing = cursor.fetchone()
        if existing:
            user_id = existing['id']
        else:
            password_hash = generate_password_hash(password)
            cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, phone, school)
            VALUES (?, ?, ?, ?, 'siswa', ?, ?)
            ''', (username, buyer_email, password_hash, buyer_name, buyer_phone, buyer_school))
            conn.commit()
            user_id = cursor.lastrowid

        # Log them in automatically
        session['user_id'] = user_id
        session['username'] = username
        session['user_name'] = buyer_name
        session['role'] = 'siswa'

    # Generate Order Code (e.g., GM-20261014-8921)
    rand_code = random.randint(1000, 9999)
    date_str = datetime.now().strftime("%Y%m%d")
    order_code = f"GM-{date_str}-{rand_code}"

    cursor.execute('''
    INSERT INTO orders (order_code, user_id, buyer_name, buyer_email, buyer_phone, buyer_school, package_id, package_title, amount, payment_method, payment_status, proof_note, paid_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'QRIS', 'paid', ?, CURRENT_TIMESTAMP)
    ''', (order_code, user_id, buyer_name, buyer_email, buyer_phone, buyer_school, package['id'], package['title'], package['price'], proof_note))
    conn.commit()
    conn.close()

    flash(f"Pembayaran QRIS untuk {package['title']} berhasil dikonfirmasi!", "success")
    return redirect(url_for('order_success', order_code=order_code))

@app.route('/checkout/success/<order_code>')
def order_success(order_code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        flash("Pesanan tidak ditemukan.", "danger")
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM packages WHERE id = ?", (order['package_id'],))
    package = cursor.fetchone()
    conn.close()

    return render_template('order_success.html', order=order, package=package)

@app.route('/materi-premium/<slug>')
@login_required
def materi_premium(slug):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packages WHERE slug = ?", (slug,))
    package_row = cursor.fetchone()
    conn.close()

    if not package_row:
        flash("Materi paket premium tidak ditemukan.", "danger")
        return redirect(url_for('paket_berbayar'))

    package = dict(package_row)
    package['modules'] = json.loads(package_row['modules_json'])
    return render_template('materi_premium.html', package=package)

# ========================================================
# 6. APLIKASI UNTUK PENGAJAR (VERSI LAPTOP)
# ========================================================
@app.route('/pengajar')
@teacher_required
def teacher_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'siswa'")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    # Recent student activity
    cursor.execute('''
    SELECT qr.*, u.full_name as student_name
    FROM quiz_results qr
    LEFT JOIN users u ON qr.user_id = u.id
    ORDER BY qr.id DESC LIMIT 6
    ''')
    recent_quiz_results = cursor.fetchall()
    conn.close()

    return render_template(
        'teacher/dashboard.html',
        total_students=total_students,
        total_questions=total_questions,
        total_articles=total_articles,
        total_orders=total_orders,
        recent_quiz_results=recent_quiz_results
    )

@app.route('/pengajar/bank-soal')
@teacher_required
def teacher_bank_soal():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions ORDER BY grade ASC, id DESC")
    questions = cursor.fetchall()
    conn.close()
    return render_template('teacher/bank_soal.html', questions=questions)

@app.route('/pengajar/bank-soal/tambah', methods=['POST'])
@teacher_required
def add_question():
    grade = int(request.form.get('grade', 10))
    subject = request.form.get('subject', '').strip()
    question_text = request.form.get('question_text', '').strip()
    option_a = request.form.get('option_a', '').strip()
    option_b = request.form.get('option_b', '').strip()
    option_c = request.form.get('option_c', '').strip()
    option_d = request.form.get('option_d', '').strip()
    option_e = request.form.get('option_e', '').strip()
    correct_option = request.form.get('correct_option', 'A').strip().upper()
    explanation = request.form.get('explanation', '').strip()

    if not subject or not question_text or not option_a:
        flash("Form soal belum lengkap.", "danger")
        return redirect(url_for('teacher_bank_soal'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO questions (grade, subject, question_text, option_a, option_b, option_c, option_d, option_e, correct_option, explanation, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (grade, subject, question_text, option_a, option_b, option_c, option_d, option_e, correct_option, explanation, g.user['id']))
    conn.commit()
    conn.close()

    flash(f"Soal baru untuk Kelas {grade} SMA ({subject}) berhasil ditambahkan ke database!", "success")
    return redirect(url_for('teacher_bank_soal'))

@app.route('/pengajar/bank-soal/hapus/<int:q_id>', methods=['POST'])
@teacher_required
def delete_question(q_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM questions WHERE id = ?", (q_id,))
    conn.commit()
    conn.close()

    flash("Soal berhasil dihapus dari database.", "info")
    return redirect(url_for('teacher_bank_soal'))

@app.route('/pengajar/artikel')
@teacher_required
def teacher_articles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY id DESC")
    articles = cursor.fetchall()
    conn.close()
    return render_template('teacher/kelola_artikel.html', articles=articles)

@app.route('/pengajar/artikel/tambah', methods=['POST'])
@teacher_required
def add_article():
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'hits').strip()
    badge = request.form.get('badge', '').strip()
    summary = request.form.get('summary', '').strip()
    content = request.form.get('content', '').strip()
    author = request.form.get('author', g.user['full_name']).strip()
    read_time = request.form.get('read_time', '5 menit').strip()

    if not title or not summary or not content:
        flash("Form artikel belum lengkap.", "danger")
        return redirect(url_for('teacher_articles'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO articles (title, category, summary, content, author, read_time, badge)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, category, summary, content, author, read_time, badge))
    conn.commit()
    conn.close()

    flash(f"Artikel '{title}' berhasil dipublikasikan ke Ruang Baca!", "success")
    return redirect(url_for('teacher_articles'))

@app.route('/pengajar/artikel/hapus/<int:art_id>', methods=['POST'])
@teacher_required
def delete_article(art_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id = ?", (art_id,))
    conn.commit()
    conn.close()

    flash("Artikel berhasil dihapus dari Ruang Baca.", "info")
    return redirect(url_for('teacher_articles'))

@app.route('/pengajar/verifikasi-bayar')
@teacher_required
def teacher_verifikasi_bayar():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    conn.close()
    return render_template('teacher/verifikasi_bayar.html', orders=orders)

@app.route('/pengajar/verifikasi-bayar/<int:order_id>', methods=['POST'])
@teacher_required
def verify_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET payment_status = 'verified' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()

    flash("Pembayaran QRIS siswa telah diverifikasi. Akses materi aktif!", "success")
    return redirect(url_for('teacher_verifikasi_bayar'))

@app.route('/pengajar/nilai-siswa')
@teacher_required
def teacher_nilai_siswa():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT qr.*, u.full_name as student_name, u.school, u.email
    FROM quiz_results qr
    LEFT JOIN users u ON qr.user_id = u.id
    ORDER BY qr.id DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return render_template('teacher/nilai_siswa.html', results=results)

if __name__ == '__main__':
    init_db()
    print("=======================================================")
    print("GoMobile Web Application & Teacher Portal is running!")
    print("Akses aplikasi di http://127.0.0.1:5000")
    print("=======================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
