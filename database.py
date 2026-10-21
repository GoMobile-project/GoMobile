import sqlite3
import json
import os
import shutil
from werkzeug.security import generate_password_hash

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), 'gomobile.db')

def get_db_path():
    """Return the database path, handling serverless /tmp environments gracefully."""
    if os.environ.get('GOMOBILE_DB_PATH'):
        return os.environ['GOMOBILE_DB_PATH']

    # In serverless environments (Netlify Functions, AWS Lambda), the deployment root is read-only.
    # We use /tmp to allow read-write database operations during function runtime.
    is_serverless = bool(
        os.environ.get('NETLIFY') or
        os.environ.get('AWS_LAMBDA_FUNCTION_NAME') or
        os.environ.get('LAMBDA_TASK_ROOT')
    )
    if is_serverless:
        tmp_dir = '/tmp'
        tmp_db = os.path.join(tmp_dir, 'gomobile.db')
        if not os.path.exists(tmp_db) and os.path.exists(DEFAULT_DB_PATH):
            try:
                shutil.copyfile(DEFAULT_DB_PATH, tmp_db)
            except Exception as e:
                print(f"Notice: copying initial database to /tmp failed ({e})")
        return tmp_db

    return DEFAULT_DB_PATH

def get_db():
    db_path = get_db_path()
    needs_init = not os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    if needs_init:
        _init_db_tables_and_seeds(conn)
    return conn

def init_db():
    conn = get_db()
    _init_db_tables_and_seeds(conn)
    conn.close()

def _init_db_tables_and_seeds(conn):
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'siswa', -- 'siswa' or 'pengajar'
        phone TEXT,
        school TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create questions table (Ruang Belajar)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grade INTEGER NOT NULL, -- 10, 11, or 12
        subject TEXT NOT NULL,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        option_e TEXT NOT NULL,
        correct_option TEXT NOT NULL, -- 'A', 'B', 'C', 'D', 'E'
        explanation TEXT NOT NULL,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create quiz_results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        grade INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        wrong_answers INTEGER NOT NULL,
        score REAL NOT NULL,
        answers_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create articles table (Ruang Baca)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL, -- 'hits', 'pahlawan_sejarah', 'utbk_snbt_tka'
        summary TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        read_time TEXT DEFAULT '5 menit',
        views INTEGER DEFAULT 0,
        badge TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create packages table (Paket Berbayar)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        price INTEGER NOT NULL,
        price_display TEXT NOT NULL,
        badge TEXT,
        tagline TEXT NOT NULL,
        description TEXT NOT NULL,
        features_json TEXT NOT NULL,
        modules_json TEXT NOT NULL
    )
    ''')

    # Create orders table (QRIS Registration & Payment)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE NOT NULL,
        user_id INTEGER,
        buyer_name TEXT NOT NULL,
        buyer_email TEXT NOT NULL,
        buyer_phone TEXT NOT NULL,
        buyer_school TEXT,
        package_id INTEGER NOT NULL,
        package_title TEXT NOT NULL,
        amount INTEGER NOT NULL,
        payment_method TEXT DEFAULT 'QRIS',
        payment_status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'verified'
        qris_ref TEXT,
        proof_note TEXT,
        paid_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (package_id) REFERENCES packages(id)
    )
    ''')

    conn.commit()

    # Seed Initial Data if empty
    seed_users(conn)
    seed_questions(conn)
    seed_articles(conn)
    seed_packages(conn)
    conn.commit()

def seed_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Pre-seed 1 Teacher and 1 Student for immediate testing and demonstration
        users_data = [
            (
                'guru_budi',
                'guru@gomobile.id',
                generate_password_hash('guru123'),
                'Budi Prasetyo, S.Pd., M.Si.',
                'pengajar',
                '081234567890',
                'SMA Negeri 1 Edukasi GoMobile'
            ),
            (
                'siswa_ahmad',
                'siswa@gomobile.id',
                generate_password_hash('siswa123'),
                'Ahmad Rizky Pratama',
                'siswa',
                '089876543210',
                'SMA Nusantara Cendekia'
            )
        ]
        cursor.executemany('''
        INSERT INTO users (username, email, password_hash, full_name, role, phone, school)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', users_data)
        conn.commit()

def seed_questions(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        questions_data = [
            # ================= KELAS 10 SMA =================
            (
                10,
                'Matematika',
                'Jika nilai mutlak |2x - 5| = 7, maka nilai-nilai x yang memenuhi persamaan tersebut adalah...',
                'x = 6 atau x = -1',
                'x = 5 atau x = -2',
                'x = 7 atau x = -3',
                'x = 4 atau x = 1',
                'x = 3 atau x = -5',
                'A',
                'Pembahasan: |2x - 5| = 7 memiliki dua kemungkinan:\n1) 2x - 5 = 7 => 2x = 12 => x = 6\n2) 2x - 5 = -7 => 2x = -2 => x = -1.\nJadi nilai x adalah x = 6 atau x = -1.',
                1
            ),
            (
                10,
                'Fisika',
                'Sebuah mobil bergerak lurus dengan percepatan konstan 2 m/s². Jika kecepatan awal mobil adalah 10 m/s, berapakah kecepatan mobil setelah bergerak selama 5 detik?',
                '15 m/s',
                '20 m/s',
                '25 m/s',
                '30 m/s',
                '18 m/s',
                'B',
                'Pembahasan: Rumus GLBB untuk kecepatan akhir vt = v0 + (a x t). Diketahui v0 = 10 m/s, a = 2 m/s², t = 5 s. Maka vt = 10 + (2 x 5) = 10 + 10 = 20 m/s.',
                1
            ),
            (
                10,
                'Kimia',
                'Nomor atom unsur Klorin (Cl) adalah 17. Konfigurasi elektron unsur Klorin menurut kulit utama (Bohr) adalah...',
                '2, 8, 8',
                '2, 8, 7',
                '2, 7, 8',
                '2, 8, 6, 1',
                '2, 10, 5',
                'B',
                'Pembahasan: Jumlah elektron Cl = 17. Pengisian kulit: Kulit K = 2 elektron, Kulit L = 8 elektron, Kulit M = 7 elektron (2 + 8 + 7 = 17).',
                1
            ),
            (
                10,
                'Biologi',
                'Ciri utama yang membedakan sel prokariotik dari sel eukariotik adalah keberadaan...',
                'Dinding sel',
                'Membran inti sel (karioteka)',
                'Ribosom',
                'Sitoplasma',
                'Materi genetik (DNA/RNA)',
                'B',
                'Pembahasan: Sel prokariotik (seperti bakteri) belum memiliki membran inti sel (karioteka), sehingga materi genetik tersebar di nukleoid. Sel eukariotik memiliki membran inti.',
                1
            ),
            (
                10,
                'Bahasa Indonesia',
                'Teks yang memuat penjelasan tentang suatu objek atau fenomena alam/sosial secara objektif berdasarkan fakta yang ditemukan dari hasil pengamatan disebut...',
                'Teks Eksplanasi',
                'Teks Negosiasi',
                'Teks Laporan Hasil Observasi (LHO)',
                'Teks Anekdot',
                'Teks Eksposisi',
                'C',
                'Pembahasan: Teks LHO (Laporan Hasil Observasi) disusun berdasarkan data faktual hasil pengamatan langsung pada suatu objek atau fenomena.',
                1
            ),

            # ================= KELAS 11 SMA =================
            (
                11,
                'Matematika',
                'Diketahui suku ke-3 suatu barisan aritmetika adalah 11 dan suku ke-7 adalah 23. Berapakah suku pertama (a) dan beda (b) barisan tersebut?',
                'a = 5 dan b = 3',
                'a = 3 dan b = 4',
                'a = 2 dan b = 5',
                'a = 5 dan b = 4',
                'a = 4 dan b = 3',
                'A',
                'Pembahasan: Un = a + (n-1)b.\nU3 = a + 2b = 11\nU7 = a + 6b = 23\nKurangkan: 4b = 12 => b = 3.\nSubstitusi: a + 2(3) = 11 => a + 6 = 11 => a = 5.',
                1
            ),
            (
                11,
                'Fisika',
                'Hukum Termodinamika I pada hakikatnya merupakan penerapan dari hukum...',
                'Kekekalan Momentum',
                'Kekekalan Energi',
                'Kekekalan Massa',
                'Gravitasi Newton',
                'Entropi Maksimum',
                'B',
                'Pembahasan: Hukum I Termodinamika (ΔU = Q - W) menyatakan bahwa energi tidak dapat diciptakan maupun dimusnahkan, hanya dapat berubah bentuk, yang merupakan Hukum Kekekalan Energi.',
                1
            ),
            (
                11,
                'Kimia',
                'Larutan asam asetat CH3COOH 0,1 M memiliki derajat ionisasi α = 0,01. Berapakah nilai pH larutan tersebut?',
                'pH = 1',
                'pH = 2',
                'pH = 3',
                'pH = 4',
                'pH = 5',
                'C',
                'Pembahasan: [H+] = M x α = 0,1 x 0,01 = 10^-3 M. pH = -log[H+] = -log(10^-3) = 3.',
                1
            ),
            (
                11,
                'Biologi',
                'Bagian nefron ginjal yang berfungsi utama dalam proses filtrasi darah untuk menghasilkan urine primer adalah...',
                'Glomerulus dan Kapsula Bowman',
                'Tubulus Kontortus Proksimal',
                'Lengkung Henle',
                'Tubulus Kontortus Distal',
                'Tubulus Kolektivus',
                'A',
                'Pembahasan: Filtrasi darah terjadi di badan malpighi (Glomerulus dan Kapsula Bowman) dan menghasilkan urine primer.',
                1
            ),
            (
                11,
                'Bahasa Inggris',
                'If she _____ harder yesterday, she would have passed the scholarship selection exam.',
                'studied',
                'had studied',
                'has studied',
                'was studying',
                'would study',
                'B',
                'Pembahasan: Conditional sentence type 3: If + Past Perfect (had + V3), would have + V3. Bentuk yang tepat adalah "had studied".',
                1
            ),

            # ================= KELAS 12 SMA =================
            (
                12,
                'Matematika',
                'Nilai dari lim (x -> 3) [(x² - 9) / (x - 3)] adalah...',
                '0',
                '3',
                '6',
                '9',
                'Tak terhingga',
                'C',
                'Pembahasan: Faktorkan pembilang: (x² - 9) = (x - 3)(x + 3). Maka lim (x -> 3) [(x - 3)(x + 3) / (x - 3)] = lim (x -> 3) (x + 3) = 3 + 3 = 6.',
                1
            ),
            (
                12,
                'Fisika',
                'Kawat penghantar berarus listrik 5 A berada dalam medan magnet homogen 0,4 Tesla tegak lurus terhadap arah kawat. Jika panjang kawat 2 meter, gaya Lorentz yang dialami kawat adalah...',
                '2 N',
                '4 N',
                '6 N',
                '8 N',
                '10 N',
                'B',
                'Pembahasan: Rumus gaya Lorentz F = B x I x L x sin(θ). Karena tegak lurus, sin(90°) = 1. F = 0,4 T x 5 A x 2 m x 1 = 4 Newton.',
                1
            ),
            (
                12,
                'Kimia',
                'Pada sel Volta, reaksi oksidasi selalu terjadi pada elektroda...',
                'Anoda bermuatan negatif',
                'Katoda bermuatan positif',
                'Anoda bermuatan positif',
                'Katoda bermuatan negatif',
                'Jembatan garam',
                'A',
                'Pembahasan: Ingat rumus praktis AnOx & KatRed (Anoda Oksidasi, Katoda Reduksi). Pada sel Volta, Anoda bermuatan negatif dan Katoda bermuatan positif.',
                1
            ),
            (
                12,
                'Penalaran UTBK/SNBT',
                'Semua siswa yang lolos seleksi beasiswa memiliki sertifikat prestasi. Beberapa siswa kelas 12 memiliki sertifikat prestasi. Kesimpulan yang tepat adalah...',
                'Semua siswa kelas 12 lolos seleksi beasiswa',
                'Beberapa siswa kelas 12 yang memiliki sertifikat prestasi lolos seleksi beasiswa',
                'Tidak ada siswa kelas 12 yang lolos beasiswa',
                'Semua siswa yang berprestasi adalah siswa kelas 12',
                'Siswa yang tidak berprestasi pasti bukan siswa kelas 12',
                'B',
                'Pembahasan: Silogisme partikular. Karena hanya sebagian siswa kelas 12 yang memiliki sertifikat prestasi, maka kemungkinan ada sebagian siswa kelas 12 yang memenuhi syarat lolos beasiswa.',
                1
            ),
            (
                12,
                'Literasi Bahasa Indonesia',
                'Manakah kalimat berikut yang menggunakan tanda baca dan ejaan yang baku sesuai dengan Pedoman Umum Ejaan Bahasa Indonesia (PUEBI)?',
                'Ibu membeli sayur, beras dan minyak dipasar.',
                'Surat ini ditandatangani oleh Dr. Ahmad, M.Pd.',
                'Ia tidak masuk sekolah karena sakit; tetapi tetap mengirim tugas.',
                'Dimanakah letak perpustakaan daerah kota Bandung?',
                'Kita memerlukan perlengkapan belajar: pena, pensil, dan penghapus.',
                'B',
                'Pembahasan: Pilihan B menggunakan penulisan gelar dan tanda koma yang baku secara tepat. Pilihan A kurang koma sebelum "dan", C salah tanda titik koma, D seharusnya "Di manakah", E titik dua tidak tepat setelah kata kerja.',
                1
            )
        ]
        cursor.executemany('''
        INSERT INTO questions (grade, subject, question_text, option_a, option_b, option_c, option_d, option_e, correct_option, explanation, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', questions_data)
        conn.commit()

def seed_articles(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles")
    if cursor.fetchone()[0] == 0:
        articles_data = [
            (
                "Transformasi Kurikulum Merdeka & Peran AI dalam Ruang Belajar Siswa Abad 21",
                "hits",
                "Membahas bagaimana integrasi teknologi kecerdasan buatan dan Kurikulum Merdeka mengubah paradigma bimbingan belajar siswa di seluruh nusantara.",
                """Perkembangan teknologi kecerdasan buatan (Artificial Intelligence) dan perombakan kurikulum pendidikan nasional menghadirkan era baru bagi dunia pendidikan Indonesia. Kini, pembelajaran tidak lagi terpaku pada hafalan satu arah di dalam kelas konvensional, melainkan beralih menuju pembelajaran yang berpusat pada siswa (student-centered learning).

Pendidikan Berbasis Minat dan Bakat:
Kurikulum Merdeka memberikan keleluasaan bagi siswa SMA untuk mendalami mata pelajaran pilihan sesuai cita-cita jurusan perguruan tinggi mereka. Melalui platform belajar fleksibel seperti GoMobile, siswa dapat menyesuaikan ritme belajar secara mandiri, menguji pemahaman lewat bank soal bertahap, serta mendapatkan umpan balik instan atas hasil latihan mereka.

Kolaborasi Guru dan Teknologi:
Teknologi bukan hadir untuk menggantikan peran pendidik, melainkan menjadi asisten terbaik bagi para guru. Guru dapat memantau grafik pemahaman siswa, mengidentifikasi materi yang belum dikuasai (misalnya konsep kalkulus atau hukum termodinamika), dan memberikan bimbingan tertarget yang lebih berdampak tinggi.""",
                "Tim Edukasi GoMobile",
                "4 menit",
                1280,
                "Trending Hits"
            ),
            (
                "Ki Hajar Dewantara: Warisan Filosofi 'Ing Ngarso Sung Tulodo' dan Hari Pendidikan Nasional",
                "pahlawan_sejarah",
                "Menelusuri jejak perjuangan Raden Mas Soewardi Soeryaningrat dalam meruntuhkan monopoli pendidikan kolonial Belanda untuk melahirkan Taman Siswa.",
                """Ki Hajar Dewantara (lahir dengan nama Raden Mas Soewardi Soeryaningrat pada 2 Mei 1889) adalah pahlawan nasional yang diakui sebagai Bapak Pendidikan Nasional Republik Indonesia. Tanggal kelahirannya setiap tahun diperingati sebagai Hari Pendidikan Nasional (Hardiknas).

Tiga Pilar Filosofi Pendidikan:
Ajaran Ki Hajar Dewantara yang abadi dan menjadi pedoman utama sistem pendidikan Indonesia berbunyi:
1. "Ing ngarso sung tulodo" - Di depan menjadi teladan bagi para murid.
2. "Ing madyo mangun karso" - Di tengah membangun kemauan, semangat, dan inisiatif.
3. "Tut wuri handayani" - Di belakang memberikan dorongan moril dan kepercayaan.

Menolak Diskriminasi Pendidikan Kolonial:
Pada masa penjajahan Belanda, pendidikan hanya dinikmati oleh anak-anak bangsawan dan keturunan Eropa. Ki Hajar Dewantara dengan gagah berani mendirikan Perguruan Nasional Taman Siswa pada tahun 1922 di Yogyakarta. Tujuannya adalah memberikan hak belajar yang setara bagi seluruh kaum pribumi jelata. Semangat inilah yang menjadi fondasi berdirinya GoMobile: meratakan akses ilmu pengetahuan berkualitas untuk setiap generasi muda di Indonesia.""",
                "Dr. Hendra Wijaya",
                "6 menit",
                2450,
                "Pahlawan Pendidikan"
            ),
            (
                "Raden Ajeng Kartini & Dewi Sartika: Pelopor Emansipasi Pendidikan Wanita Indonesia",
                "pahlawan_sejarah",
                "Kisah perjuangan dua srikandi pendidikan tanah air yang mendobrak feodalisme agar perempuan Indonesia berhak mengenyam bangku sekolah.",
                """Perjalanan pendidikan di Indonesia tak lepas dari perjuangan gigih para srikandi bangsa. R.A. Kartini di Jepara dan Dewi Sartika di Bandung menjadi dua tonggak utama emansipasi intelektual wanita nusantara.

R.A. Kartini dan 'Habis Gelap Terbitlah Terang':
Melalui surat-suratnya yang terkumpul dalam buku 'Door Duisternis tot Licht', Kartini mencurahkan impiannya agar perempuan dapat mandiri, berilmu pengetahuan, dan terbebas dari kurungan tradisi pingitan yang membelenggu. Kartini mendirikan sekolah kecil di pendopo kabupaten untuk mengajari para gadis membaca, menulis, dan menjahit.

Dewi Sartika dan Sakola Kautamaan Istri:
Jika Kartini terkenal dengan pemikiran tertulisnya, Dewi Sartika adalah penggerak praktis yang mendirikan sekolah wanita pertama di Hindia Belanda pada tahun 1904 di Bandung. Sekolah ini berkembang pesat ke berbagai pelosok Jawa Barat, membuktikan bahwa perempuan berdaya adalah pilar kemajuan sebuah bangsa. Nilai perjuangan ini membakar semangat para pelajar masa kini untuk tidak pernah menyia-nyiakan kesempatan belajar.""",
                "Siti Nurhaliza, M.Pd.",
                "5 menit",
                1890,
                "Sejarah Nasional"
            ),
            (
                "Panduan Super Lengkap UTBK-SNBT: Bedah Subtes TPS, Literasi Bahasa & Penalaran Matematika",
                "utbk_snbt_tka",
                "Kupas tuntas format terbaru seleksi nasional berbasis tes (SNBT), bobot penilaian Item Response Theory (IRT), dan strategi manajemen waktu.",
                """Ujian Tulis Berbasis Komputer - Seleksi Nasional Berdasarkan Tes (UTBK-SNBT) merupakan gerbang utama seleksi masuk Perguruan Tinggi Negeri (PTN) idaman di Indonesia. Memahami peta soal dan manajemen waktu adalah kunci utama meraih skor di atas 700.

Subtes Utama UTBK-SNBT:
1. Tes Potensi Skolastik (TPS):
   - Penalaran Umum (PU): Logika induktif, deduktif, dan kuantitatif.
   - Pengetahuan dan Pemahaman Umum (PPU): Pemahaman konteks bacaan dan kebahasaan.
   - Kemampuan Memahami Bacaan dan Menulis (KBM): Kaidah ejaan, kalimat efektif, koherensi paragraf.
   - Pengetahuan Kuantitatif (PK): Aljabar dasar, aritmetika, geometri, dan probabilitas.

2. Literasi dalam Bahasa Indonesia dan Bahasa Inggris:
   - Menguji kemampuan menganalisis argumen teks panjang, infografis, dan sudut pandang penulis.

3. Penalaran Matematika:
   - Pemecahan masalah dunia nyata dengan pemodelan matematis.

Strategi Lolos PTN Impian:
- Kenali Sistem IRT: Kerjakan semua soal karena tidak ada sistem minus. Soal yang jarang dijawab benar oleh peserta lain akan bernilai bobot lebih tinggi.
- Latihan Tryout Rutin: Ikuti paket belajar tryout berkala di GoMobile untuk membiasakan ritme 1 soal per 60 detik.""",
                "Master Coach UTBK GoMobile",
                "7 menit",
                3420,
                "Strategi SNBT"
            ),
            (
                "Strategi Tembus TKA (Tes Kemampuan Akademik) Saintek & Soshum dengan Skor Maksimal",
                "utbk_snbt_tka",
                "Metode penguasaan konsep esensial Fisika, Kimia, Biologi, Matematika IPA, serta Sosiologi, Geografi, Ekonomi, dan Sejarah.",
                """Tes Kemampuan Akademik (TKA) mengukur penguasaan materi pelajaran secara mendalam untuk memvalidasi kesiapan calon mahasiswa di bidang studi yang dipilih.

Karakteristik Soal TKA:
Soal TKA tidak sekadar menghafal rumus, melainkan soal bertipe HOTS (Higher Order Thinking Skills). Siswa diuji kemampuan analisis grafik, interpretasi eksperimen laboratorium, dan penerapan prinsip saintifik dalam skenario nyata.

Langkah Efektif Membedah Soal TKA:
1. Pemetaan Materi Esensial: Prioritaskan bab-bab yang setiap tahun konsisten keluar, seperti Stoikiometri & Ikatan Kimia, Dinamika Partikel & Gelombang dalam Fisika, serta Sistem Organ pada Biologi.
2. Rangkuman Konsep Satu Lembar (Mind Map): Hubungkan konsep yang saling bertautan daripada menghafal rumus secara terisolasi.
3. Drill Soal Berjenjang: Mulai dari paket dasar kelas 10-12 sebelum beralih ke paket komprehensif berbayar GoMobile.""",
                "Bambang Setiawan, M.Sc.",
                "5 menit",
                2100,
                "Bedah TKA"
            )
        ]
        cursor.executemany('''
        INSERT INTO articles (title, category, summary, content, author, read_time, views, badge)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', articles_data)
        conn.commit()

def seed_packages(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM packages")
    if cursor.fetchone()[0] == 0:
        packages_data = [
            (
                "paket-master-utbk-tka",
                "Paket Master UTBK-SNBT + TKA All-in-One",
                800000,
                "Rp 800.000,00",
                "Paling Lengkap & Populer",
                "Solusi komprehensif all-in-one lolos PTN Klaster 1 & Jurusan Favorit (Kedokteran, STEI, FSRD, FH, FEB).",
                "Akses tanpa batas ke seluruh modul UTBK-SNBT (TPS, Literasi, Penalaran Matematika) ditambah bank materi TKA Saintek & Soshum mendalam. Dilengkapi 30x Tryout CAT sistem IRT, video pembahasan interaktif, serta sesi mentoring bimbingan belajar dengan pengajar spesialis GoMobile.",
                json.dumps([
                    "30x Tryout CAT Online Berstandar BPPP & Sistem IRT",
                    "Akses Seluruh Modul Materi UTBK-SNBT & TKA Lengkap",
                    "Pembahasan Video & Teks Step-by-Step",
                    "Grup Diskusi & Mentoring Privat dengan Pengajar",
                    "Prediksi Peluang Lolos Jurusan PTN Berbasis Skor",
                    "Sertifikat Kelulusan Tryout & Analisis Kelemahan Subtes",
                    "Akses Materi Aktif Selama 1 Tahun Penuh"
                ]),
                json.dumps([
                    {"title": "Modul 1: Kupas Tuntas TPS (Penalaran Umum, PPU, KBM, PK)", "lessons": 16, "hours": "24 Jam"},
                    {"title": "Modul 2: Penguasaan Literasi Bahasa Indonesia & Inggris", "lessons": 12, "hours": "18 Jam"},
                    {"title": "Modul 3: Penalaran Matematika Konseptual & Soal HOTS", "lessons": 14, "hours": "20 Jam"},
                    {"title": "Modul 4: Penguasaan Komprehensif TKA Saintek / Soshum", "lessons": 20, "hours": "30 Jam"},
                    {"title": "Modul 5: Simulasi Tryout CAT IRT Nasional (30 Paket)", "lessons": 30, "hours": "60 Jam"}
                ])
            ),
            (
                "paket-intensif-snbt",
                "Paket Intensif Sukses SNBT PTN",
                700000,
                "Rp 700.000,00",
                "Pilihan Favorit Siswa",
                "Fokus maksimal menembus batas passing grade UTBK-SNBT jalur tes nasional.",
                "Program akselerasi belajar terstruktur yang menitikberatkan pada TPS, Literasi Bahasa Indonesia, Literasi Bahasa Inggris, dan Penalaran Matematika. Termasuk 20x Tryout CAT sistem ranking nasional dan bank soal latihan prediktif.",
                json.dumps([
                    "20x Tryout CAT Online Sistem IRT Real-time",
                    "Modul Belajar Lengkap Khusus Materi UTBK-SNBT",
                    "Rangkuman Rumus Cepat & Teknik Eliminasi Jawaban",
                    "Kunci Jawaban & Pembahasan Mendalam",
                    "Webinar Bulanan Strategi Memilih Prodi PTN",
                    "Akses Materi Aktif Selama 6 Bulan"
                ]),
                json.dumps([
                    {"title": "Modul 1: Strategi Kilat Penalaran Umum & Logika", "lessons": 10, "hours": "15 Jam"},
                    {"title": "Modul 2: Trik Membaca Cepat Literasi Teks Panjang", "lessons": 10, "hours": "15 Jam"},
                    {"title": "Modul 3: Penalaran Matematika Praktis & Efisien", "lessons": 12, "hours": "18 Jam"},
                    {"title": "Modul 4: 20 Paket Simulasi Tryout SNBT CAT", "lessons": 20, "hours": "40 Jam"}
                ])
            ),
            (
                "paket-kilat-tka-sma",
                "Paket Kilat TKA SMA & Ujian Mandiri",
                500000,
                "Rp 500.000,00",
                "Hemat & Tertarget",
                "Penguasaan materi esensial TKA Saintek/Soshum untuk Ujian Mandiri PTN & Prestasi SMA.",
                "Rangkuman materi pelajaran kurikulum SMA kelas 10, 11, dan 12 yang disaring khusus untuk kebutuhan ujian kemampuan akademik dan ujian mandiri PTN (SIMAK UI, UTUL UGM, SMUP Unpad, dll).",
                json.dumps([
                    "10x Tryout CAT TKA Berbobot Standar Mandiri PTN",
                    "Bank Soal TKA Terpilih (Saintek / Soshum)",
                    "Pembahasan Soal TKA dengan Analisis Konsep Dasar",
                    "Ringkasan Materi Esensial Format PDF & Interaktif",
                    "Akses Materi Aktif Selama 4 Bulan"
                ]),
                json.dumps([
                    {"title": "Modul 1: Bedah Soal Esensial Matematika Lanjut", "lessons": 8, "hours": "12 Jam"},
                    {"title": "Modul 2: Konsep Inti Sains Terpadu / Sosial Humaniora", "lessons": 12, "hours": "18 Jam"},
                    {"title": "Modul 3: 10 Paket Simulasi Tryout TKA", "lessons": 10, "hours": "20 Jam"}
                ])
            )
        ]
        cursor.executemany('''
        INSERT INTO packages (slug, title, price, price_display, badge, tagline, description, features_json, modules_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', packages_data)
        conn.commit()

if __name__ == '__main__':
    init_db()
    print("GoMobile SQLite Database initialized and seeded successfully at:", DB_PATH)
