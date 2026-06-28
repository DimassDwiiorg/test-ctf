import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, render_template_string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_ctf_key_change_me_in_production'
import os

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ctf_platform.db')

if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)


db = SQLAlchemy(app)

# Models[span_1](start_span)[span_1](end_span)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    solves = db.relationship('Solve', backref='user', lazy=True)

class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, default=100)
    flag = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), default='Easy/Medium')  # Pilihan: 'Easy/Medium' atau 'Hard+'
    solves = db.relationship('Solve', backref='challenge', lazy=True)

class Solve(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Initialize Database with Sample Data[span_2](start_span)[span_2](end_span)
def init_db():
    if not os.path.exists('instance/ctf_platform.db') and not os.path.exists('ctf_platform.db'):
        db.create_all()
        # Create Admin[span_3](start_span)[span_3](end_span)
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('shamod1703'), is_admin=True)
            db.session.add(admin)
        
        # Create Sample Challenges[span_4](start_span)[span_4](end_span)
        if not Challenge.query.first():
            challs = [
                Challenge(title="Sanity Check", category="Welcome", description="Selamat datang! Flag untuk tantangan ini adalah: CTF{w3lc0m3_t0_th3_g4m3}", flag="CTF{w3lc0m3_t0_th3_g4m3}", points=50, level='Easy/Medium'),
                Challenge(title="Inspector Gadget", category="Web Hacking", description="Coba periksa source code halaman web ini. Apakah kamu bisa menemukan sesuatu yang disembunyikan? (Hint: Lihat komentar di dashboard)", flag="CTF{h1dd3n_1n_h7ml_c0mm3n7}", points=100, level='Easy/Medium'),
                Challenge(title="Base Enigma", category="Cryptography", description="Pesan ini disandikan menggunakan Base64: Q1RGe2I0czY0X2RlYzBkM3JfMTNfMTV9", flag="CTF{b4s64_dec0d3r_13_15}", points=100, level='Easy/Medium'),
                Challenge(title="SSTI Nightmare", category="Web Hacking", description="Server ini memproses input nama secara ceroboh. Eksploitasi server lewat halaman /target_ssti untuk membaca file flag.txt!", flag="CTF{ssti_fl4sk_rce_unl0ck_2026}", points=500, level='Hard+')
            ]
            for c in challs:
                db.session.add(c)
        db.session.commit()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username sudah terdaftar!', 'danger')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash(f'Selamat datang kembali, {user.username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    challenges = Challenge.query.all()
    user_solves = [s.challenge_id for s in Solve.query.filter_by(user_id=session['user_id']).all()]
    
    # Hitung jumlah tantangan dasar (Easy/Medium) yang wajib diselesaikan
    easy_medium_ids = [c.id for c in Challenge.query.filter_by(level='Easy/Medium').all()]
    solved_easy_medium = [cid for cid in user_solves if cid in easy_medium_ids]
    
    # Status apakah Hard+ terbuka atau tidak
    hard_unlocked = len(solved_easy_medium) == len(easy_medium_ids)
    
    return render_template('dashboard.html', challenges=challenges, user_solves=user_solves, hard_unlocked=hard_unlocked)

# --- HALAMAN SCOREBOARD BARU ---
@app.route('/scoreboard')
def scoreboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    all_users = User.query.filter_by(is_admin=False).all()
    
    # Hitung total skor dinamis untuk setiap user berdasarkan tantangan yang diselesaikan
    leaderboard = []
    for user in all_users:
        total_score = sum([solve.challenge.points for solve in user.solves if solve.challenge])
        leaderboard.append({
            'username': user.username,
            'score': total_score,
            'solved_count': len(user.solves)
        })
    
    # Urutkan berdasarkan skor tertinggi
    leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)
    return render_template('scoreboard.html', leaderboard=leaderboard)

# --- HALAMAN LAB TARGET LEVEL HARD+ (SSTI) ---
@app.route('/target_ssti', methods=['GET', 'POST'])
def target_ssti():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Validasi ekstra: mencegah user bypass via URL langsung sebelum unlock
    user_solves = [s.challenge_id for s in Solve.query.filter_by(user_id=session['user_id']).all()]
    easy_medium_ids = [c.id for c in Challenge.query.filter_by(level='Easy/Medium').all()]
    if len([cid for cid in user_solves if cid in easy_medium_ids]) != len(easy_medium_ids):
        flash('Akses ditolak! Selesaikan level bawah terlebih dahulu.', 'danger')
        return redirect(url_for('dashboard'))

    result = ""
        if request.method == 'POST':
        name = request.form.get('name', '')
        
        # Proteksi tambahan agar pemain tidak mengintip rahasia server Vercel/database
        blacklist = ['config', 'environ', 'getenv', 'SECRET_KEY', 'DATABASE_URL']
        if any(bad in name for bad in blacklist):
            result = "<div class='alert alert-danger'>Payload terdeteksi berbahaya bagi server!</div>"
        else:
            template = f"<div class='alert alert-info'>Halo {name}, salam kenal dari server!</div>"
            try:
                result = render_template_string(template)
            except Exception as e:
                result = f"<div class='alert alert-danger'>Error: {str(e)}</div>"

            
    return render_template('ssti_challenge.html', result=result)

@app.route('/submit_flag/<int:challenge_id>', methods=['POST'])
def submit_flag(challenge_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    challenge = Challenge.query.get(challenge_id)
    submitted_flag = request.form['flag'].strip()
    
    already_solved = Solve.query.filter_by(user_id=session['user_id'], challenge_id=challenge_id).first()
    if already_solved:
        flash('Kamu sudah menyelesaikan tantangan ini!', 'info')
        return redirect(url_for('dashboard'))
        
    if submitted_flag == challenge.flag:
        solve = Solve(user_id=session['user_id'], challenge_id=challenge_id)
        db.session.add(solve)
        db.session.commit()
        flash(f'Luar biasa! Flag benar. +{challenge.points} poin!', 'success')
    else:
        flash('Flag salah! Coba lagi.', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Akses ditolak! Halaman ini khusus Admin.', 'danger')
        return redirect(url_for('dashboard'))
    all_solves = Solve.query.all()
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin.html', solves=all_solves, users=users)

@app.route('/logout')
def logout():
    session.clear()
    flash('Kamu telah logout.', 'info')
    return redirect(url_for('login'))


    # Hapus DB lama secara manual di Termux jika skema kolom level tidak terupdate otomatis
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
