import os
import random
import string
import base64
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'amajg_secret_key_production_db_v5'
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
    sexo = db.Column(db.String(30), nullable=True)
    estado_civil = db.Column(db.String(40), nullable=True)
    profissao = db.Column(db.String(100), nullable=True)
    doador_sangue = db.Column(db.String(10), nullable=True)
    doador_orgaos = db.Column(db.String(10), nullable=True)
    
    # Endereço
    cep = db.Column(db.String(20), nullable=True)
    rua = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(30), nullable=True)
    complemento = db.Column(db.String(100), nullable=True)
    referencia = db.Column(db.String(150), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    municipio = db.Column(db.String(100), nullable=True)
    
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
                
        sexo = request.form.get('sexo', '')
        estado_civil = request.form.get('estado_civil', '')
        profissao = request.form.get('profissao', '')
        doador_sangue = request.form.get('doador_sangue', 'Não')
        doador_orgaos = request.form.get('doador_orgaos', 'Não')
        
        cep = request.form.get('cep', '')
        rua = request.form.get('rua', '')
        numero = request.form.get('numero', '')
        complemento = request.form.get('complemento', '')
        referencia = request.form.get('referencia', '')
        bairro = request.form.get('bairro', '')
        municipio = request.form.get('municipio', '')
        
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
            sexo=sexo,
            estado_civil=estado_civil,
            profissao=profissao,
            doador_sangue=doador_sangue,
            doador_orgaos=doador_orgaos,
            cep=cep,
            rua=rua,
            numero=numero,
            complemento=complemento,
            referencia=referencia,
            bairro=bairro,
            municipio=municipio,
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

    search_query = request.args.get('q', '').strip()
    query_obj = Volunteer.query
    if search_query:
        term = f"%{search_query}%"
        query_obj = query_obj.filter(
            db.or_(
                Volunteer.nome.ilike(term),
                Volunteer.cpf.ilike(term),
                Volunteer.codigo.ilike(term)
            )
        )
    volunteers_list = query_obj.order_by(Volunteer.id.desc()).all()
    return render_template('admin.html', voluntariados=volunteers_list, is_main_admin=session.get('is_main_admin', False), search_query=search_query)

@app.route('/admin/backup-json')
def export_backup_json():
    if not session.get('admin_logged'):
        return redirect(url_for('login'))
    
    volunteers = Volunteer.query.all()
    data_list = []
    
    for v in volunteers:
        vol_dict = {
            'id': v.id,
            'codigo': v.codigo,
            'nome': v.nome,
            'cpf': v.cpf,
            'nascimento': v.nascimento,
            'sexo': v.sexo,
            'estado_civil': v.estado_civil,
            'profissao': v.profissao,
            'doador_sangue': v.doador_sangue,
            'doador_orgaos': v.doador_orgaos,
            'cep': v.cep,
            'rua': v.rua,
            'numero': v.numero,
            'complemento': v.complemento,
            'referencia': v.referencia,
            'bairro': v.bairro,
            'municipio': v.municipio,
            'matricula': v.matricula,
            'instituicao': v.instituicao,
            'curso': v.curso,
            'periodo': v.periodo,
            'whatsapp': v.whatsapp,
            'email_voluntario': v.email_voluntario,
            'photo_filename': v.photo,
            'photo_base64': None,
            'data_cadastro': v.data_cadastro,
            'validade': v.validade,
            'status': v.status,
            'cadastrado_por': v.cadastrado_por
        }
        
        if v.photo and v.photo != 'default_user.png':
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], v.photo)
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    vol_dict['photo_base64'] = base64.b64encode(f.read()).decode('utf-8')
                    
        data_list.append(vol_dict)
        
    backup_payload = {
        'sistema': 'AMAJG - Gestão de Voluntários',
        'data_backup': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_registros': len(data_list),
        'voluntarios': data_list
    }
    
    json_str = json.dumps(backup_payload, ensure_ascii=False, indent=4)
    filename = f"backup_amajg_voluntarios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return Response(
        json_str,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )

@app.route('/admin/toggle-status/<int:vol_id>', methods=['POST'])
def toggle_status(vol_id):
    if not session.get('admin_logged') or not session.get('is_main_admin'):
        flash('Apenas o administrador principal pode alterar o status.', 'danger')
        return redirect(url_for('admin_dashboard'))
    vol = Volunteer.query.get_or_404(vol_id)
    vol.status = 'Inativo' if vol.status == 'Ativo' else 'Ativo'
    db.session.commit()
    flash(f'Status do voluntário {vol.codigo} alterado para {vol.status}.', 'info')
    return redirect(url_for('admin_dashboard'))

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
                
        vol.sexo = request.form.get('sexo', '')
        vol.estado_civil = request.form.get('estado_civil', '')
        vol.profissao = request.form.get('profissao', '')
        vol.doador_sangue = request.form.get('doador_sangue', 'Não')
        vol.doador_orgaos = request.form.get('doador_orgaos', 'Não')
        
        vol.cep = request.form.get('cep', '')
        vol.rua = request.form.get('rua', '')
        vol.numero = request.form.get('numero', '')
        vol.complemento = request.form.get('complemento', '')
        vol.referencia = request.form.get('referencia', '')
        vol.bairro = request.form.get('bairro', '')
        vol.municipio = request.form.get('municipio', '')
        
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

```
