# GoMobile - Aplikasi Bimbingan Belajar Siswa & Portal Pengajar

GoMobile adalah platform web bimbingan belajar (les) interaktif yang ramah pengguna di ponsel (**mobile-friendly**) dan dilengkapi antarmuka khusus layar lebar (**versi laptop**) untuk pengajar/guru.

---

## 🚀 Fitur Unggulan Sesuai Permintaan

1. **Autentikasi Siswa & Pengajar (Database SQLite)**:
   - Registrasi dan Login mandiri untuk **Siswa** dan **Pengajar**.
   - Identitas (Username, Email, Nama Lengkap, No. HP, Asal Sekolah) dan Password tersimpan aman di database dengan enkripsi hash.
   - Akun bawaan siap uji:
     - **Pengajar:** ID `guru_budi` | Password: `guru123`
     - **Siswa:** ID `siswa_ahmad` | Password: `siswa123`

2. **Tata Letak Beranda (Header Navbar)**:
   - **Pojok Kiri:** Nama dan Brand **"GoMobile"**.
   - **Di Bagian Tengah:** Navigasi **"Ruang Belajar"**.
   - **Di Samping Ruang Belajar:** Navigasi **"Ruang Baca"**.
   - Navigasi bawah khusus HP (Bottom Bar) untuk kemudahan navigasi satu jempol.

3. **Ruang Belajar (Latihan Soal Basic SMA Kelas 10, 11, 12)**:
   - Halaman paket latihan dipisah per jenjang:
     - **Kelas 10 SMA:** Persamaan nilai mutlak, GLBB mekanika, konfigurasi elektron, sel prokariotik, teks LHO.
     - **Kelas 11 SMA:** Barisan deret aritmetika, termodinamika energi, pH asam-basa, sistem ekskresi, English grammar.
     - **Kelas 12 SMA:** Limit aljabar kalkulus, gaya Lorentz magnetik, sel Volta, silogisme penalaran, kaidah PUEBI.
   - Pengerjaan kuis step-by-step dengan kartu pilihan jawaban interaktif (A, B, C, D, E).
   - **Halaman Akhir Evaluasi:** Menampilkan rincian **Jumlah Jawaban Benar**, **Jumlah Jawaban Salah**, Skor Akhir (0-100), serta pembahasan lengkap tiap butir soal.

4. **Ruang Baca (Literasi & Pembahasan)**:
   - **Hits Pendidikan:** Transformasi Kurikulum Merdeka & Peran AI dalam Pembelajaran Modern.
   - **Sejarah & Pahlawan Pendidikan:** Ki Hajar Dewantara (Taman Siswa & filosofi Tut Wuri Handayani), R.A. Kartini, dan Dewi Sartika (Sakola Kautamaan Istri).
   - **Pembahasan TKA, UTBK & SNBT:** Panduan lengkap subtes TPS, literasi membaca, penalaran matematika, dan strategi menaklukkan soal HOTS TKA.

5. **Paket Belajar Berbayar (TKA, SNBT, UTBK)**:
   - **Paket Master UTBK-SNBT + TKA All-in-One:** **Rp 800.000,00**
   - **Paket Intensif Sukses SNBT PTN:** **Rp 700.000,00**
   - **Paket Kilat TKA SMA & Ujian Mandiri:** **Rp 500.000,00**

6. **Sistem Pembayaran Eksklusif QRIS**:
   - Begitu tombol paket diklik, siswa langsung diarahkan ke halaman registrasi dan pembayaran.
   - Tampilan barcode standar **QRIS Nasional** (mendukung BCA, Mandiri, BRI, BNI, GoPay, OVO, DANA, ShopeePay).
   - Simulasi konfirmasi pembayaran instan dan aktivasi materi premium.

7. **Aplikasi Pengajar (Versi Laptop)**:
   - Dashboard analitik: Total siswa terdaftar, total bank soal, total artikel, dan riwayat pesanan QRIS.
   - **Kelola Bank Soal:** Tambah soal baru untuk kelas 10, 11, 12 beserta kunci & pembahasannya.
   - **Kelola Ruang Baca:** Menulis dan mempublikasikan artikel edukasi baru.
   - **Verifikasi Pesanan QRIS:** Memvalidasi pembayaran siswa.
   - **Pantau Nilai Siswa:** Rekap skor latihan siswa, jumlah benar dan salah per paket.

---

## 🛠️ Cara Menjalankan Aplikasi Secara Lokal

1. Buka PowerShell atau Terminal di direktori proyek:
   ```powershell
   cd C:\Users\fajri\Desktop\GoMobile
   ```

2. Pasang dependensi:
   ```powershell
   pip install -r requirements.txt
   ```

3. Jalankan server Flask:
   ```powershell
   python app.py
   ```

4. Buka browser Anda:
   - Akses Web Siswa & Pengajar di: [http://127.0.0.1:5000](http://127.0.0.1:5000)

5. Menjalankan Tes Otomatis:
   ```powershell
   python test_app.py
   ```

---

## 🌐 Panduan Deployment ke Netlify (Production Ready)

Proyek ini telah dikonfigurasi secara lengkap untuk deployment ke Netlify menggunakan **Netlify Functions (Serverless Python)** dan **Netlify Edge CDN**:

1. **Konfigurasi Otomatis (`netlify.toml`)**:
   - `command = "python prepare_deploy.py"`: Menyiapkan aset statis ke direktori `public/static` agar disajikan langsung dengan performa maksimal melalui Netlify Edge CDN.
   - `functions = "netlify/functions"`: Menangani seluruh routing dinamis Flask (autentikasi session, latihan soal, pembelian paket QRIS, portal pengajar) melalui serverless function.
   - `included_files = ["templates/**", "gomobile.db"]`: Memastikan file template Jinja2 dan seed database disertakan di dalam serverless runtime package.

2. **Langkah Hubungkan ke Netlify**:
   - Buka dashboard [Netlify](https://app.netlify.com).
   - Klik **"Add new site"** -> **"Import an existing project"**.
   - Pilih **GitHub** dan pilih repository: `GoMobile-project/GoMobile`.
   - Netlify akan mendeteksi `netlify.toml` secara otomatis:
     - **Build command:** `python prepare_deploy.py`
     - **Publish directory:** `public`
     - **Functions directory:** `netlify/functions`
   - Klik **Deploy GoMobile**.

3. **Variabel Lingkungan (Environment Variables) Opsional di Netlify**:
   - `SECRET_KEY`: Kunci rahasia untuk enkripsi session Flask.
   - `PYTHON_VERSION`: `3.11` (sudah otomatis dikonfigurasi).

