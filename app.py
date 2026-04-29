#!/usr/bin/env python3
"""
Vulnerable Support Ticket System - Flask Edition
Intentionally insecure for educational purposes.
DO NOT USE IN PRODUCTION.
"""

import os
import sqlite3
import subprocess
import sys
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')  # Not secret in this lab

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE', os.path.join(BASE_DIR, 'tickets.db'))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
PORT = int(os.environ.get('PORT', 5000))
DEBUG_MODE = os.environ.get('FLASK_DEBUG', '1') == '1'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure required directories exist
db_dir = os.path.dirname(DATABASE)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- Database Helpers ----------
def get_db():
    """Return a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and default admin user."""
    with get_db() as conn:
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            '''
        )
        # Insert default admin (plaintext password)
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)',
            ('admin', 'password'),
        )
    print('Database initialized. Admin: admin / password')


def list_uploaded_files():
    """Return only regular files from the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


# ---------- Authentication Decorator ----------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            flash('Please log in first.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


# ---------- Routes ----------
@app.route('/')
def index():
    """Public ticket submission page."""
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit_ticket():
    """Process ticket submission. VULNERABLE: No sanitization."""
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']

    with get_db() as conn:
        conn.execute(
            'INSERT INTO tickets (name, email, subject, message) VALUES (?, ?, ?, ?)',
            (name, email, subject, message),
        )
    flash('Ticket submitted successfully!', 'success')
    return redirect(url_for('index'))


# ---------- Admin Authentication ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_db() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?',
                (username, password),
            ).fetchone()

        if user:
            session['admin'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid credentials.', 'danger')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))


# ---------- Admin Panel ----------
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


@app.route('/admin/tickets')
@admin_required
def admin_tickets():
    """Display all tickets. VULNERABLE: message is not escaped -> XSS."""
    with get_db() as conn:
        tickets = conn.execute('SELECT * FROM tickets ORDER BY created_at DESC').fetchall()
    return render_template('admin_tickets.html', tickets=tickets)


@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload():
    """File manager: upload and list files. VULNERABLE: no extension check."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part.', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f'File "{filename}" uploaded successfully.', 'success')
        return redirect(url_for('admin_upload'))

    return render_template('admin_upload.html', files=list_uploaded_files())


@app.route('/uploads/<filename>')
@admin_required
def uploaded_file(filename):
    """Serve uploaded files (including potentially malicious ones)."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin/execute/<filename>', methods=['POST'])
@admin_required
def execute_script(filename):
    """Execute an uploaded Python script with a command parameter. RCE VULNERABILITY."""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        flash('File not found.', 'danger')
        return redirect(url_for('admin_upload'))

    cmd = request.form.get('cmd', 'whoami')
    try:
        # VULNERABILITY: Executing user-controlled file with user input
        result = subprocess.run(
            [sys.executable, filepath, cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout + result.stderr
        return render_template(
            'admin_upload.html',
            files=list_uploaded_files(),
            exec_output=output,
            exec_filename=filename,
        )
    except subprocess.TimeoutExpired:
        flash('Execution timed out.', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin_upload'))


# ---------- Run ----------
if __name__ == '__main__':
    # Initialize DB if not exists
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=DEBUG_MODE, host='0.0.0.0', port=PORT)
