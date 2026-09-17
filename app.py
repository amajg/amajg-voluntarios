import os
import random
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'amajg_secret_key_production'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Múltiplos administradores permitidos (E-mail: Senha)
admins_db = {
    'cadastro.amajg@gmail.com': 'AMAJG2026*',
    'secretaria': 'secretaria2026',
    'diretoria': 'diretoria2026'
}

# Armazenamento em memória (reinicia se o gunicorn reiniciar, ideal SQLite para persistência real)
volunteers_db = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        temp_pass = session.get('temp_password')
        if email in admins_db and (password == admins_db[email] or password == temp_pass):
            session['admin_logged'] = True
            session['admin_email'] = email
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('E-mail ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if email in admins_db:
            temp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            session['temp_password'] = temp_pass
            flash(f'Senha temporária gerada: {temp_pass}', 'info')
        else:
            flash('E-mail não encontrado.', 'danger')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if not session.get('admin_logged'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form.get('nome')
        instituicao = request.form.get('instituicao')
        curso = request.form.get('curso', '')
        periodo = request.form.get('periodo', '')
        
        codigo_unico = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Tratamento da Foto
        photo_filename = 'default_user.png'
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                photo_filename = f"vol_{codigo_unico}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        volunteers_db.append({
            'code': codigo_unico,
            'codigo': codigo_unico,
            'full_name': nome,
            'nome': nome,
            'institution': instituicao,
            'instituicao': instituicao,
            'curso': curso,
            'period': periodo,
            'periodo': periodo,
            'photo': photo_filename,
            'data_cadastro': datetime.now().strftime('%d/%m/%Y às %H:%M'),
            'cadastrado_por': session.get('admin_email', 'sistema')
        })
        flash(f'Voluntário cadastrado com sucesso! Código: {codigo_unico}', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin.html', voluntariados=volunteers_db, admins_count=len(admins_db))

@app.route('/public-query', methods=['GET', 'POST'])
def public_query():
    query_code = request.args.get('code', '')
    found_vol = None
    if request.method == 'POST':
        query_code = request.form.get('code', '').strip().upper()
    
    if query_code:
        found_vol = next((v for v in volunteers_db if v['codigo'] == query_code), None)
        
    return render_template('public_query.html', volunteer=found_vol, query_code=query_code)

@app.route('/card/<codigo>')
def view_card(codigo):
    vol = next((v for v in volunteers_db if v['codigo'] == codigo), None)
    if not vol:
        vol = {
            'code': codigo,
            'codigo': codigo,
            'full_name': 'VOLUNTÁRIO DEMONSTRAÇÃO',
            'nome': 'VOLUNTÁRIO DEMONSTRAÇÃO',
            'institution': 'UNIVERSIDADE FEDERAL',
            'instituicao': 'UNIVERSIDADE FEDERAL',
            'curso': 'PEDAGOGIA',
            'period': '3º Período',
            'periodo': '3º Período',
            'photo': 'default_user.png',
            'data_cadastro': '01/01/2026',
            'cadastrado_por': 'sistema'
        }
    return render_template('card.html', v=vol)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
