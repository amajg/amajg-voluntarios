import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'amajg_secret_key_production'

# Armazenamento em memória simples para os voluntários (reinicia se o gunicorn reiniciar, ideal SQLite para persistência real)
volunteers_db = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # Aceita a senha padrão ou a última gerada em session se desejar
        valid_pass = session.get('temp_password', 'AMAJG2026*')
        if email == 'cadastro.amajg@gmail.com' and (password == 'AMAJG2026*' or password == valid_pass):
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
        email = request.form.get('email')
        if email == 'cadastro.amajg@gmail.com':
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
        
        # Gera código único para o voluntário
        codigo_unico = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        volunteers_db.append({
            'codigo': codigo_unico,
            'nome': nome,
            'instituicao': instituicao,
            'curso': curso,
            'periodo': periodo
        })
        flash('Voluntário cadastrado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin.html', voluntariados=volunteers_db)

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
            'codigo': codigo,
            'nome': 'VOLUNTÁRIO DEMONSTRAÇÃO',
            'instituicao': 'UNIVERSIDADE FEDERAL',
            'curso': 'PEDAGOGIA',
            'periodo': '3º Período'
        }
    return render_template('card.html', v=vol)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
