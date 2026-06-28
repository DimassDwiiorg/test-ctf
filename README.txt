============================================================
PLATFORM BELAJAR CTF - FULL WEB APPLICATION (FLASK + SQLITE)
============================================================

Aplikasi ini dibuat lengkap dengan sistem autentikasi, database, 
dashboard user, tantangan CTF interaktif, serta Admin Page untuk 
memantau progres user.

STRUKTUR FILE:
├── app.py                 # Backend utama (Flask + SQLAlchemy)
└── templates/             # Folder template HTML website
    ├── base.html          # Layout dasar & styling CSS
    ├── login.html         # Halaman masuk
    ├── register.html      # Halaman daftar akun baru
    ├── dashboard.html     # Halaman belajar & input flag
    └── admin.html         # Halaman khusus Admin untuk cek skor

CARA MENJALANKANNYA:

1. Pastikan Anda sudah menginstal Python di komputer.
2. Buka Terminal / Command Prompt pada folder ini.
3. Instal library Flask & SQLAlchemy dengan perintah:
   pip install flask flask-sqlalchemy

4. Jalankan aplikasi web:
   python app.py

5. Buka browser Anda dan akses alamat berikut:
   http://127.0.0.1:5000

AKUN ADMIN DEFAULT:
- Username: admin
- Password: admin123
(Silakan gunakan akun ini untuk masuk ke Admin Panel)
