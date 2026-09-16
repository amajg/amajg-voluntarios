import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'amajg_secret_key_cloudflare'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email == 'cadastro.amajg@gmail.com' and password == 'AMAJG2026*':
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

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged'):
        return redirect(url_for('login'))
    return render_template('admin.html', volunteers=[])

@app.route('/public-query', methods=['GET', 'POST'])
def public_query():
    query_code = request.args.get('code', '')
    if request.method == 'POST':
        query_code = request.form.get('code', '').strip()
    return render_template('public_query.html', volunteer=None, query_code=query_code)

@app.route('/card/<codepath>')
def card_view(codepath):
    v = {
        'code': codepath,
        'full_name': 'VOLUNTÁRIO DEMONSTRAÇÃO',
        'institution': 'UNIVERSIDADE FEDERAL',
        'registration': '20261050',
        'course': 'PEDAGOGIA',
        'period': '3º Período',
        'valid_until': '31/12/2026',
        'photo': 'default_user.png'
    }
    return render_template('card.html', v=v)
    app.run(debug=True, host='0.0.0.0', port=5000)
async def on_fetch(request, env, ctx):
    return await app.handle_async(request)