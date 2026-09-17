import os
import random
import string
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'amajg_secret_key_production_db_v3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

ADMIN_PRINCIPAL = 'cadastro.amajg@gmail.com'
DIRETORIA_USERS = {'cecilia', 'douglas', 'adrielle', 'mendes'}
SENHA_DIRETORIA = 'diretoria2026'
SENHA_ADMIN_PRINCIPAL = 'AMAJG2026*'

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True, nullable=False)
    nome = db.Column(db.String(120), nullable=False)
    cpf = db.Column(db.String(30), nullable=True)
    nascimento = db.Column(db.String(30), nullable=True)
    matricula = db.Column(db.String(50), nullable=True)
    instituicao = db.Column(db.String(150), nullable=False)
    curso = db.Column(db.String(150), nullable=True)
    periodo = db.Column(db.String(50), nullable=True)
    whatsapp = db.Column(db.String(30), nullable=True)
    email_voluntario = db.Column(db.String(120), nullable=True)
    photo = db.Column(db.String(200), default='default_user.png')
    data_cadastro = db.Column(db.String(50), nullable=True)
    validade = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(30), default='Ativo')
    cadastrado_por = db.Column(db.String(100), nullable=True)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def gerar_codigo_sequencial():
    count = Volunteer.query.count() + 1
    return f"AMAJG-{count:05d}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        temp_pass = session.get('temp_password')
        
        is_valid = False
        user_display = identifier
        
        if identifier == ADMIN_PRINCIPAL and (password == SENHA_ADMIN_PRINCIPAL or password == temp_pass):
            is_valid = True
            session['is_main_admin'] = True
        elif identifier in DIRETORIA_USERS and password == SENHA_DIRETORIA:
            is_valid = True
            session['is_main_admin'] = False

        if is_valid:
            session['admin_logged'] = True
            session['admin_user'] = user_display
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identificação ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('email', '').strip().lower()
        if identifier == ADMIN_PRINCIPAL or identifier in DIRETORIA_USERS:
            temp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            session['temp_password'] = temp_pass
            flash(f'Senha temporária gerada para {identifier}: {temp_pass}', 'info')
        else:
            flash('Usuário/E-mail não encontrado.', 'danger')
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
        cpf = request.form.get('cpf', '')
        raw_nasc = request.form.get('nascimento', '')
        nascimento = raw_nasc
        if '-' in raw_nasc:
            try:
                dt_obj = datetime.strptime(raw_nasc, '%Y-%m-%d')
                nascimento = dt_obj.strftime('%d/%m/%Y')
            except:
                pass
                
        matricula = request.form.get('matricula', '')
        instituicao = request.form.get('instituicao')
        curso = request.form.get('curso', '')
        periodo = request.form.get('periodo', '')
        whatsapp = request.form.get('whatsapp', '')
        email_voluntario = request.form.get('email_voluntario', '')
        
        codigo_sequencial = gerar_codigo_sequencial()
        
        photo_filename = 'default_user.png'
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                photo_filename = f"vol_{codigo_sequencial.replace('-', '')}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        now = datetime.now()
        validade_dt = now + timedelta(days=365)
        
        new_v = Volunteer(
            codigo=codigo_sequencial,
            nome=nome,
            cpf=cpf,
            nascimento=nascimento,
            matricula=matricula,
            instituicao=instituicao,
            curso=curso,
            periodo=periodo,
            whatsapp=whatsapp,
            email_voluntario=email_voluntario,
            photo=photo_filename,
            data_cadastro=now.strftime('%d/%m/%Y às %H:%M'),
            validade=validade_dt.strftime('%d/%m/%Y'),
            status='Ativo',
            cadastrado_por=session.get('admin_user', 'gestor')
        )
        db.session.add(new_v)
        db.session.commit()
        flash(f'Voluntário cadastrado com sucesso! Código: {codigo_sequencial}', 'success')
        return redirect(url_for('admin_dashboard'))

    volunteers_list = Volunteer.query.order_by(Volunteer.id.desc()).all()
    return render_template('admin.html', voluntariados=volunteers_list, is_main_admin=session.get('is_main_admin', False))

@app.route('/admin/edit/<int:vol_id>', methods=['GET', 'POST'])
def edit_volunteer(vol_id):
    if not session.get('admin_logged') or not session.get('is_main_admin'):
        flash('Apenas o administrador principal (cadastro.amajg@gmail.com) pode editar cadastros.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    vol = Volunteer.query.get_or_404(vol_id)
    if request.method == 'POST':
        vol.nome = request.form.get('nome')
        vol.cpf = request.form.get('cpf', '')
        raw_nasc = request.form.get('nascimento', '')
        if '-' in raw_nasc:
            try:
                dt_obj = datetime.strptime(raw_nasc, '%Y-%m-%d')
                vol.nascimento = dt_obj.strftime('%d/%m/%Y')
            except:
                pass
        else:
            if raw_nasc:
                vol.nascimento = raw_nasc
        vol.matricula = request.form.get('matricula', '')
        vol.instituicao = request.form.get('instituicao')
        vol.curso = request.form.get('curso', '')
        vol.periodo = request.form.get('periodo', '')
        vol.whatsapp = request.form.get('whatsapp', '')
        vol.email_voluntario = request.form.get('email_voluntario', '')
        vol.validade = request.form.get('validade', vol.validade)
        
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                photo_filename = f"vol_{vol.codigo.replace('-', '')}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
                vol.photo = photo_filename
                
        db.session.commit()
        flash('Cadastro atualizado com sucesso!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Converter data DD/MM/YYYY para YYYY-MM-DD para pré-preencher input date se houver
    nasc_input = vol.nascimento
    if vol.nascimento and '/' in vol.nascimento:
        try:
            dt_obj = datetime.strptime(vol.nascimento, '%d/%m/%Y')
            nasc_input = dt_obj.strftime('%Y-%m-%d')
        except:
            nasc_input = ''

    return render_template('edit_volunteer.html', vol=vol, nasc_input=nasc_input)

@app.route('/admin/delete/<int:vol_id>', methods=['POST'])
def delete_volunteer(vol_id):
    if not session.get('admin_logged') or not session.get('is_main_admin'):
        flash('Apenas o administrador principal (cadastro.amajg@gmail.com) pode excluir cadastros.', 'danger')
        return redirect(url_for('admin_dashboard'))
    vol = Volunteer.query.get_or_404(vol_id)
    db.session.delete(vol)
    db.session.commit()
    flash('Cadastro excluído com sucesso.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/public-query', methods=['GET', 'POST'])
def public_query():
    query_code = request.args.get('code', '').strip().upper()
    found_vol = None
    if request.method == 'POST':
        query_code = request.form.get('code', '').strip().upper()
    
    if query_code:
        found_vol = Volunteer.query.filter_by(codigo=query_code).first()
        
    return render_template('public_query.html', volunteer=found_vol, query_code=query_code)

@app.route('/card/<codigo>')
def view_card(codigo):
    vol = Volunteer.query.filter_by(codigo=codigo.upper()).first()
    if not vol:
        vol = Volunteer(
            codigo=codigo,
            nome='VOLUNTÁRIO DEMONSTRAÇÃO',
            cpf='000.000.000-00',
            nascimento='01/01/2000',
            matricula='2026001',
            instituicao='UNIVERSIDADE FEDERAL',
            curso='PEDAGOGIA',
            periodo='3º Período',
            photo='default_user.png',
            data_cadastro=datetime.now().strftime('%d/%m/%Y'),
            validade=(datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y'),
            status='Ativo'
        )
    return render_template('card.html', v=vol)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
