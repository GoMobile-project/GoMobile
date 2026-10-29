import unittest
import json
from app import app
from database import init_db, get_db

class GoMobileTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()

    def test_01_homepage_layout(self):
        """Test Homepage elements: GoMobile brand, Ruang Belajar, Ruang Baca, Paid Packages"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        # Check branding and navigation
        self.assertIn('GoMobile', html)
        self.assertIn('Ruang Belajar', html)
        self.assertIn('Ruang Baca', html)
        self.assertIn('Paket Berbayar', html)
        # Check SMA grades teaser
        self.assertIn('Kelas 10 SMA', html)
        self.assertIn('Kelas 11 SMA', html)
        self.assertIn('Kelas 12 SMA', html)
        # Check prices
        self.assertIn('800.000', html)
        self.assertIn('700.000', html)
        self.assertIn('500.000', html)

    def test_02_registration_and_login(self):
        """Test User registration and login into database"""
        # Register new student
        res_reg = self.client.post('/register', data={
            'full_name': 'Test Siswa Baru',
            'username': 'test_siswa_99',
            'email': 'siswa99@test.com',
            'phone': '081299998888',
            'school': 'SMAN 5 Test',
            'role': 'siswa',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        # Login with registered account
        res_login = self.client.post('/login', data={
            'identity': 'test_siswa_99',
            'password': 'password123',
            'role': 'siswa'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)
        self.assertIn('Test Siswa Baru', res_login.data.decode('utf-8'))

    def test_03_ruang_belajar_grades_and_quiz_submission(self):
        """Test Ruang Belajar separate grade pages and correct/wrong score calculation"""
        # Check Ruang Belajar index
        res_hub = self.client.get('/ruang-belajar')
        self.assertEqual(res_hub.status_code, 200)

        # Check Kelas 10 page
        res_k10 = self.client.get('/ruang-belajar/kelas/10')
        self.assertEqual(res_k10.status_code, 200)
        self.assertIn('Kelas 10 SMA', res_k10.data.decode('utf-8'))

        # Check Kelas 11 page
        res_k11 = self.client.get('/ruang-belajar/kelas/11')
        self.assertEqual(res_k11.status_code, 200)
        self.assertIn('Kelas 11 SMA', res_k11.data.decode('utf-8'))

        # Check Kelas 12 page
        res_k12 = self.client.get('/ruang-belajar/kelas/12')
        self.assertEqual(res_k12.status_code, 200)
        self.assertIn('Kelas 12 SMA', res_k12.data.decode('utf-8'))

        # Submit quiz answers for Kelas 10 (simulate 4 correct, 1 wrong)
        # Fetch question IDs for grade 10
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, correct_option FROM questions WHERE grade = 10 ORDER BY id ASC")
        q_list = cursor.fetchall()
        conn.close()

        form_data = {'grade': 10}
        for idx, q in enumerate(q_list):
            if idx == 0:
                # Answer wrong
                form_data[f'answer_{q["id"]}'] = 'E' if q['correct_option'] != 'E' else 'D'
            else:
                # Answer correct
                form_data[f'answer_{q["id"]}'] = q['correct_option']

        res_submit = self.client.post('/ruang-belajar/submit', data=form_data, follow_redirects=True)
        self.assertEqual(res_submit.status_code, 200)
        result_html = res_submit.data.decode('utf-8')
        
        # Verify Benar / Salah is reported on the result page
        self.assertIn('Benar', result_html)
        self.assertIn('Salah', result_html)
        self.assertIn('Kunci Pembahasan', result_html)

    def test_04_ruang_baca_articles(self):
        """Test Ruang Baca filters and article reading view"""
        # View Ruang Baca
        res_baca = self.client.get('/ruang-baca')
        self.assertEqual(res_baca.status_code, 200)
        html = res_baca.data.decode('utf-8')
        self.assertIn('Hits Pendidikan', html)
        self.assertIn('Pahlawan &amp; Sejarah', html)
        self.assertIn('Pembahasan TKA', html)

        # View single article
        res_art = self.client.get('/ruang-baca/1')
        self.assertEqual(res_art.status_code, 200)
        self.assertIn('Kembali ke Ruang Baca', res_art.data.decode('utf-8'))

    def test_05_paid_packages_and_qris_checkout(self):
        """Test Paid packages (Rp 800.000, 700.000, 500.000) and QRIS payment process"""
        res_pkg = self.client.get('/paket-berbayar')
        self.assertEqual(res_pkg.status_code, 200)
        html = res_pkg.data.decode('utf-8')
        self.assertIn('800.000', html)
        self.assertIn('700.000', html)
        self.assertIn('500.000', html)

        # Checkout page for Paket 1 (Rp 800.000)
        res_checkout = self.client.get('/checkout?paket_id=1')
        self.assertEqual(res_checkout.status_code, 200)
        checkout_html = res_checkout.data.decode('utf-8')
        self.assertIn('QRIS', checkout_html)
        self.assertIn('800.000', checkout_html)

        # Process checkout and registration
        res_process = self.client.post('/checkout/process', data={
            'package_id': 1,
            'buyer_name': 'Budi Siswa QRIS',
            'username': 'budi_qris_siswa',
            'buyer_email': 'budiqris@test.com',
            'buyer_phone': '081234567899',
            'buyer_school': 'SMAN 1 Jaya',
            'password': 'password123',
            'proof_note': 'Pembayaran QRIS melalui m-BCA'
        }, follow_redirects=True)
        self.assertEqual(res_process.status_code, 200)
        success_html = res_process.data.decode('utf-8')
        self.assertIn('Pembayaran Berhasil', success_html)
        self.assertIn('QRIS Nasional', success_html)

    def test_06_teacher_laptop_portal(self):
        """Test Laptop version of Teacher App: Dashboard, Bank Soal, and Student Monitoring"""
        # Login as pre-seeded teacher with unique password
        res_login = self.client.post('/login', data={
            'identity': 'guru_budi',
            'password': 'budi_mat123',
            'role': 'pengajar'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)

        # Teacher Dashboard
        res_dash = self.client.get('/pengajar')
        self.assertEqual(res_dash.status_code, 200)
        dash_html = res_dash.data.decode('utf-8')
        self.assertIn('Aplikasi Pengajar GoMobile', dash_html)
        self.assertIn('Kelola Bank Soal', dash_html)

        # Add new question in Bank Soal
        res_add_q = self.client.post('/pengajar/bank-soal/tambah', data={
            'grade': 10,
            'subject': 'Fisika Eksperimen',
            'question_text': 'Berapakah nilai percepatan gravitasi standar bumi g?',
            'option_a': '9.8 m/s²',
            'option_b': '5.0 m/s²',
            'option_c': '15 m/s²',
            'option_d': '20 m/s²',
            'option_e': '1.0 m/s²',
            'correct_option': 'A',
            'explanation': 'Nilai standar percepatan gravitasi bumi rata-rata adalah 9.8 m/s².'
        }, follow_redirects=True)
        self.assertEqual(res_add_q.status_code, 200)
        self.assertIn('Fisika Eksperimen', res_add_q.data.decode('utf-8'))

        # Check Student Scores page
        res_scores = self.client.get('/pengajar/nilai-siswa')
        self.assertEqual(res_scores.status_code, 200)

        # Check QRIS Orders Verification page
        res_orders = self.client.get('/pengajar/verifikasi-bayar')
        self.assertEqual(res_orders.status_code, 200)

    def test_07_modul_katalog_and_all_12_subjects(self):
        """Test 12 subject modules catalog and individual chapter reader"""
        res_cat = self.client.get('/modul-belajar')
        self.assertEqual(res_cat.status_code, 200)
        cat_html = res_cat.data.decode('utf-8')
        
        # Verify 12 subjects are present in catalog
        subjects = [
            'Sosiologi', 'Matematika Tingkat Lanjut', 'Bahasa Indonesia Tingkat Lanjut',
            'Bahasa Inggris Tingkat Lanjut', 'Pelajaran Kewirausahaan', 'IPA Terpadu',
            'Pendidikan Pancasila dan Kewarganegaraan', 'IPS Terpadu', 'Sejarah &amp; Antropologi',
            'Bahasa Arab', 'Bahasa Jepang', 'Bahasa Mandarin'
        ]
        for sub in subjects:
            self.assertIn(sub, cat_html)

        # Test viewing detail page of Sosiologi
        res_sos = self.client.get('/modul-belajar/sosiologi')
        self.assertEqual(res_sos.status_code, 200)
        self.assertIn('Sosiologi', res_sos.data.decode('utf-8'))
        self.assertIn('Simulasi CAT', res_sos.data.decode('utf-8'))

    def test_08_simulation_25_questions_quiz_and_submit(self):
        """Test 25 questions simulation page, live clock markup, and score evaluation"""
        # View simulation page for IPA Terpadu
        res_quiz = self.client.get('/modul-belajar/ipa-terpadu/simulasi')
        self.assertEqual(res_quiz.status_code, 200)
        quiz_html = res_quiz.data.decode('utf-8')
        
        # Verify real-time clock container is present
        self.assertIn('liveClockTime', quiz_html)
        self.assertIn('liveClockDate', quiz_html)
        self.assertIn('elapsedTimer', quiz_html)
        self.assertIn('25 Soal', quiz_html)

        # Submit answers (all A)
        form_data = {}
        for qid in range(1, 26):
            form_data[f'answer_{qid}'] = 'A'

        res_submit = self.client.post('/modul-belajar/ipa-terpadu/simulasi/submit', data=form_data, follow_redirects=True)
        self.assertEqual(res_submit.status_code, 200)
        sub_html = res_submit.data.decode('utf-8')
        self.assertIn('Hasil Evaluasi', sub_html)
        self.assertIn('Skor Akhir CAT', sub_html)
        self.assertIn('Pembahasan Detail 25 Butir Soal', sub_html)

    def test_09_premium_user_bank_soal_30_questions(self):
        """Test that premium user gets 30 questions per subject in Bank Soal Kelas 12"""
        # Login as premium student Ahmad
        res_login = self.client.post('/login', data={
            'identity': 'siswa_ahmad',
            'password': 'ahmad_pass123',
            'role': 'siswa'
        }, follow_redirects=True)
        self.assertEqual(res_login.status_code, 200)

        # Check Bank Soal Kelas 12
        res_k12 = self.client.get('/ruang-belajar/kelas/12')
        self.assertEqual(res_k12.status_code, 200)
        k12_html = res_k12.data.decode('utf-8')
        
        # Verify premium badge and 30 questions available
        self.assertIn('Premium (30 Soal / Mapel)', k12_html)
        self.assertIn('liveClockTime', k12_html)

    def test_10_unique_passwords_for_all_users(self):
        """Test each demo user has distinct password and can login"""
        accounts = [
            ('siswa_zahra', 'zahra_pass456', 'siswa'),
            ('siswa_dimas', 'dimas_pass789', 'siswa'),
            ('siswa_nayla', 'nayla_pass321', 'siswa'),
            ('guru_siti', 'siti_fis456', 'pengajar'),
            ('guru_andi', 'andi_tps789', 'pengajar')
        ]
        for username, password, role in accounts:
            res = self.client.post('/login', data={
                'identity': username,
                'password': password,
                'role': role
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn('/logout', res.data.decode('utf-8'))
            self.client.get('/logout')

if __name__ == '__main__':
    unittest.main()
