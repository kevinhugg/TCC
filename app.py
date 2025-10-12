from flask import Flask, render_template, request, redirect, url_for, flash, session, render_template_string, \
    make_response, send_file
from flask_mail import Mail, Message
import random
import string
from datetime import datetime, timedelta, timezone
import unicodedata

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email.utils

from xhtml2pdf import pisa
import io
import os
import base64

from xhtml2pdf.default import DEFAULT_FONT

DEFAULT_FONT['DejaVuSans'] = '/caminho/para/DejaVuSans.ttf'

from dash_app import create_dash_app

from firebase_functions import (
    sign_in_user, create_user, add_adm,
    get_all_vehicles, get_vehicle_by_number, get_damage_reports_by_vehicle,
    get_all_damage_reports, get_damage_by_id, delete_damage_by_id,
    get_agent_by_doc_id, get_all_agents, get_unassigned_agents,
    get_history_by_agent, get_occurrences_and_services_by_vehicle,
    get_all_occurrences_and_services, get_agents_by_vehicle,
    add_occurrence_or_service, add_vehicle, delete_agent, delete_vehicle,
    update_agent_by_doc_id, update_vehicle,
    replace_vehicle_image, replace_agent_image, clear_agent_assignment,
    get_occurrence_or_service_by_id,
    reset_password, get_admin_by_uid
)

from data.dados import *

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'grupo.kolom@gmail.com'
app.config['MAIL_PASSWORD'] = 'xfju vcgm ylkm hzgt'
app.config['MAIL_DEFAULT_SENDER'] = 'grupo.kolom@gmail.com'
app.secret_key = 'semurb'

mail = Mail(app)

# integração do Dash
dash_app = create_dash_app(app)


# Rota para index.html (sua página de login)
@app.route('/')
def pagina_login():
    return render_template('login/index.html')


# Rota para o forms de login
@app.route('/login', methods=['POST'])
def info_login():
    """
    Processa o formulário de login.
    Usa a função sign_in_user para autenticar com o Firebase.
    """
    if request.method == 'POST':
        # O campo de matrícula foi substituído por e-mail no HTML
        email = request.form['email']
        senha = request.form['senha']

        # Chama a função de login do Firebase
        user_data, error_message = sign_in_user(email, senha)

        if user_data:
            # Login bem-sucedido
            session['usuario_logado'] = True
            session['user_id'] = user_data.get('localId')  # Armazena o UID do usuário na sessão
            session['id_token'] = user_data.get('idToken')  # Token para futuras requisições autenticadas
            flash('Login realizado com sucesso!', 'success')
            return redirect('/dashboard/')  # Idealmente, redirecionar para um painel
        else:
            # Falha no login
            # A mensagem de erro específica de sign_in_user será exibida
            flash(error_message, 'danger')
            return redirect(url_for('pagina_login'))


# =============================================
# ROTAS ADMINISTRATIVAS COM FIREBASE AUTH
# =============================================

# Rota para página de login administrativo
@app.route('/admin_login_page')
def admin_login_page():
    return render_template('login/admin_login.html')

# Rota para processar login administrativo com Firebase Auth
@app.route('/admin_login', methods=['POST'])
def admin_login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    try:
        # Tenta fazer login no Firebase Authentication
        user_data, error_message = sign_in_user(email, senha)
        
        if user_data:
            # Login bem-sucedido no Authentication
            user_uid = user_data.get('localId')
            
            # Verifica se este usuário é um administrador
            admin_user = get_admin_by_uid(user_uid)
            
            if admin_user:
                # É um administrador - permite acesso
                session['admin_logged_in'] = True
                session['admin_email'] = email
                session['admin_nome'] = admin_user.get('nome', 'Administrador')
                session['admin_uid'] = user_uid
                flash('Login administrativo realizado com sucesso!', 'success')
                return redirect(url_for('pagina_registro'))
            else:
                # Login bem-sucedido mas não é administrador
                flash('Acesso negado. Você não tem permissões administrativas.', 'error')
                return redirect(url_for('admin_login_page'))
        else:
            # Falha no login
            flash(error_message, 'error')
            return redirect(url_for('admin_login_page'))
            
    except Exception as e:
        print(f"❌ Erro no login administrativo: {e}")
        flash('Erro interno no servidor.', 'error')
        return redirect(url_for('admin_login_page'))

# Rota para página de registro (protegida)
@app.route('/pagina_registro')
def pagina_registro():
    # Verifica se o administrador está logado
    if not session.get('admin_logged_in'):
        flash('Acesso negado. Faça login como administrador primeiro.', 'error')
        return redirect(url_for('admin_login_page'))
    
    return render_template('login/register.html')

# Rota para criar novo agente (protegida)
@app.route('/create_adm', methods=['POST'])
def create_adm_route():
    """
    Processa o formulário de registro de novo agente.
    """
    # Verifica se o administrador está logado
    if not session.get('admin_logged_in'):
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin_login_page'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        matricula = request.form['matricula']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']

        # Validação básica
        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('pagina_registro'))

        # Tenta criar o usuário no Firebase Authentication
        user = create_user(email, senha)

        if user == "EMAIL_EXISTS":
            flash('Este e-mail já está cadastrado.', 'danger')
            return redirect(url_for('pagina_registro'))
        elif user == "WEAK_PASSWORD":
            flash('A senha é muito fraca. Use pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('pagina_registro'))
        elif user is None:
            flash('Ocorreu um erro ao criar o usuário.', 'danger')
            return redirect(url_for('pagina_registro'))

        # Se o usuário foi criado com sucesso no Auth, adicione os dados ao Firestore
        adm_data = {
            "nome": nome,
            "email": email,
            "matricula": matricula,
            "uid": user.uid,
            "cargo_at": "",
            "func_mes": "",
            "viatura_mes": "",
            "tipo": "agente",
            "data_criacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Adiciona o agente no Firestore
        from firebase_functions import add_agent
        agent_id = add_agent(adm_data)

        if agent_id:
            flash('Agente registrado com sucesso!', 'success')
            return redirect(url_for('pagina_registro'))
        else:
            flash('Erro ao salvar os dados do agente no banco de dados.', 'danger')
            return redirect(url_for('pagina_registro'))

# Rota para logout administrativo
@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_email', None)
    session.pop('admin_nome', None)
    session.pop('admin_uid', None)
    flash('Logout administrativo realizado com sucesso!', 'success')
    return redirect(url_for('admin_login_page'))


# Rota para metodoRecSenha.html
@app.route('/rec-senha')
def metodoRecSenha():
    return render_template('login/metodoRecSenha.html')


@app.route('/enviar-codigo', methods=['POST'])
def enviar_codigo():
    email_destino = request.form['email']
    codigo = ''.join(random.choices(string.digits, k=6))

    session['reset_code'] = codigo
    session['reset_email'] = email_destino
    session['reset_code_expiry'] = datetime.now(timezone.utc) + timedelta(minutes=10)

    try:
        print(f" Tentando enviar código para: {email_destino}")
        
        smtp_server = "smtp.gmail.com"
        port = 587
        sender_email = "kevinmar704@gmail.com"
        sender_password = "xfju vcgm ylkm hzgt" 

        # ✅ CORREÇÃO: Remover caracteres não-ASCII do email
        email_limpo = ''.join(char for char in email_destino if ord(char) < 128)
        print(f"📧 Email limpo: {email_limpo}")
        
        # ✅ CORREÇÃO: Especificar encoding UTF-8 explicitamente
        mensagem = MIMEMultipart("alternative")
        mensagem["Subject"] = "Código de Recuperação de Senha - SEMURB"
        mensagem["From"] = sender_email
        mensagem["To"] = email_limpo
        mensagem["Date"] = email.utils.formatdate(localtime=True)
        
        # Texto simples sem caracteres especiais
        texto = f"""
        SEMURB - Secretaria Municipal de Urbanismo
        
        Seu codigo de recuperacao de senha e: {codigo}
        
        Este codigo e valido por 10 minutos.
        
        Se voce nao solicitou este codigo, ignore este email.
        
        Atenciosamente,
        Equipe SEMURB
        """
        
        # ✅ CORREÇÃO: Especificar charset UTF-8
        parte_texto = MIMEText(texto, "plain", "utf-8")
        mensagem.attach(parte_texto)
        
        print(" Conectando ao servidor SMTP...")
        
        # Envia o email
        servidor = smtplib.SMTP(smtp_server, port)
        servidor.set_debuglevel(1) 
        servidor.ehlo()
        servidor.starttls()
        servidor.ehlo()
        servidor.login(sender_email, sender_password)
        
        # ✅ CORREÇÃO: Codificar a mensagem para UTF-8 antes de enviar
        mensagem_utf8 = mensagem.as_string().encode('utf-8')
        servidor.sendmail(sender_email, email_limpo, mensagem_utf8)
        servidor.quit()
        
        print(" Email enviado com sucesso via SMTP!")
        
        flash('Um código de recuperação foi enviado para o seu e-mail.', 'success')
        return redirect(url_for('pagina_codigo'))
        
    except smtplib.SMTPException as e:
        print(f"❌ ERRO SMTP: {e}")
        flash('Erro ao enviar e-mail. Verifique sua conexão e tente novamente.', 'danger')
        return redirect(url_for('metodoRecSenha'))
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        print("Traceback completo:")
        print(traceback.format_exc())
        flash('Erro ao enviar e-mail. Tente novamente.', 'danger')
        return redirect(url_for('metodoRecSenha'))


# Rota para a página de inserção do código
@app.route('/codigo')
def pagina_codigo():
    if 'reset_email' not in session:
        flash('Por favor, solicite um código primeiro.', 'warning')
        return redirect(url_for('metodoRecSenha'))
    return render_template('login/codigo.html')


# Rota para validar o código
@app.route('/validar-codigo', methods=['POST'])
def validar_codigo():
    codigo_digitado = request.form['codigo']

    # Aqui ele olha se tem uma conta já
    if 'reset_code' not in session or 'reset_code_expiry' not in session:
        flash('Sua sessão de recuperação expirou ou é inválida. Por favor, solicite um novo código.', 'danger')
        return redirect(url_for('metodoRecSenha'))

    # Aqui é para ver se o código expirou
    if datetime.now(timezone.utc) > session['reset_code_expiry']:
        session.pop('reset_code', None)
        session.pop('reset_email', None)
        session.pop('reset_code_expiry', None)
        flash('O código expirou. Por favor, solicite um novo.', 'danger')
        return redirect(url_for('metodoRecSenha'))

    # Ver se o código está certo
    if codigo_digitado == session['reset_code']:
        # Código válido! Redirecionar para a página de redefinir senha
        flash('Código verificado com sucesso! Agora você pode redefinir sua senha.', 'success')
        # Limpar o código da sessão, mas manter o e-mail para a próxima etapa (redefinição)
        session.pop('reset_code', None)
        session.pop('reset_code_expiry', None)
        return redirect(url_for('red_senha'))  # Próxima etapa
    else:
        flash('Código inválido. Tente novamente.', 'danger')
        return redirect(url_for('pagina_codigo'))  # Volta para a página de código


# Rota para a página de redefinição de senha
@app.route('/redefinir-senha')
def red_senha():
    if 'reset_email' not in session:
        flash('Acesso inválido à página de redefinição de senha.', 'danger')
        return redirect(url_for('pagina_login'))
    return render_template('login/redefinirSenha.html')


@app.route('/redefinir-senha-final', methods=['POST'])
def redefinir_senha_final():
    if 'reset_email' not in session:
        flash('Sua sessão de redefinição de senha expirou.', 'danger')
        return redirect(url_for('pagina_login'))

    nova_senha = request.form['nova_senha']
    confirmar_senha = request.form['confirmar_senha']

    if nova_senha != confirmar_senha:
        flash('As senhas não coincidem.', 'danger')
        return redirect(url_for('red_senha'))

    email = session['reset_email']
    success, message = reset_password(email, nova_senha)

    if success:
        flash('Senha redefinida com sucesso! Você já pode fazer o login.', 'success')
        session.pop('reset_email', None)  # Limpa a sessão
        return redirect(url_for('pagina_login'))
    else:
        flash(f'Erro ao redefinir a senha: {message}', 'danger')
        return redirect(url_for('red_senha'))


##LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('pagina_login'))


@app.before_request
def proteger_rotas():
    # se for para a rota de /dashboard ele so deixa usar se estiver logado
    if request.path.startswith('/dashboard') and not session.get('usuario_logado'):
        return redirect(url_for('pagina_login'))


# PDF'S
def remover_acentos(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn').lower()


@app.route('/pdf_viaturas_Danificadas')
def gerar_pdf_viaturas():
    status = request.args.get('status', 'all')

    if status == 'all':
        dados_filtrados = damVehicles
    else:
        dados_filtrados = [d for d in damVehicles if d['status'] == status]

    html_template = '''
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
        </head>
        <body>
            <h2 style="text-align: center"> Tabela de Viaturas Danificadas - Status: {{ status|capitalize }}</h2>
            <table>
                <thead>
                    <tr>
                        <th>N°</th>
                        <th>Descrição</th>
                        <th>Status</th>
                        <th>Data</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in damVehicles %}
                    <tr>
                        <td>{{ item.viatura }}</td>
                        <td>{{ item.descricao }}</td>
                        <td>{{ item.status }}</td>
                        <td>{{ item.data }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body>
    </html>
    '''

    html_content = render_template_string(html_template, damVehicles=dados_filtrados, status=status)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500

    pdf_buffer.seek(0)
    return make_response(pdf_buffer.read(), {
        'content-Type': 'application/pdf',
        'content-Disposition': 'attachment; filename="viaturas_danificadas.pdf"'
    })


@app.route(f'/pdf_detalhes_viatura_<numero>')
def gerar_pdf_viatura_detalhes(numero):
    status = request.args.get('status', 'todos')

    viatura_info = next((v for v in viaturas if v['numero'] == numero), None)

    imagem_path = os.path.join(app.root_path, 'static', 'assets', 'img', os.path.basename(viatura_info['imagem']))
    with open(imagem_path, 'rb') as img_file:
        imagem_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        imagem_embed = f"data:image/png;base64,{imagem_base64}"

    if not viatura_info:
        return "Viatura não encontrada.", 404

    ocorrencias_do_ve = [o for o in Ocur_Vehicles if o['viatura'] == numero]
    if status != 'todos':
        status_formatado = status.replace('/', '-')
        ocorrencias_do_ve = [
            o for o in ocorrencias_do_ve
            if o['data'].startswith(status_formatado)
        ]

    mes_selecionado = status if status == 'todos' else datetime.strptime(status, '%Y/%m').strftime('%B/%Y').capitalize()

    html_template = '''
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
                .img-final {
                    display: block;
                    margin-left: 26rem;
                    margin-right: auto;
                    margin-top: auto;
                    margin-bottom: auto;
                    width: 150px;
                    height: auto;
                }
            </style>
        </head>
        <body>
            <h2 class="title"> Relatório da Viatura - {{ numero }}</h2>
            <h3 class="section-title">Mes: {{ mes }}</h3>

            <h3 class="tittle">Última foto da viatura<h3/>
            <img src="{{ imagem }}" class="img-final">

            <h3 class="tittle">Informações da viatura<h3/>
            <table>
                <thead>
                    <tr>
                        <th class="thead-infos">N°</th>
                        <th class="thead-infos">Placa</th>
                        <th class="thead-infos">Tipo</th>
                        <th class="thead-infos">Avaria</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="table-infos">{{ info.numero }}</td>
                        <td class="table-infos">{{ info.placa }}</td>
                        <td class="table-infos">{{ info.veiculo }}</td>
                        <td class="table-infos">{{ 'sim' if info.avariada else 'Não' }}</td>
                    </tr>
                </tbody>
            </table>

            <h3 class="tittle">Ocorrências</h3>
            {% if ocorrencias%}
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Tipo</th>
                        <th>Descrição</th>
                    </tr>
                </thead>
                <tbody>
                    {% for oco in ocorrencias %}
                    <tr>
                        <td>{{ oco.data }}</td>
                        <td>{{ oco.nomenclatura }}</td>
                        <td>{{ oco.descricao }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align:center;">Nenhuma ocorrência registrada para este periodo.<p>
            {% endif %}
        </body>
    </html>
    '''

    html_content = render_template_string(
        html_template,
        info=viatura_info,
        numero=numero,
        mes=mes_selecionado,
        ocorrencias=ocorrencias_do_ve,
        imagem=imagem_embed,
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500

    pdf_buffer.seek(0)
    return make_response(pdf_buffer.read(), {
        'content-Type': 'application/pdf',
        'content-Disposition': f'attachment; filename="Relatorio_Viatura_{numero}.pdf"'
    })


@app.route("/gerar_pdf_agentes")
def gerar_pdf_agentes():
    filtro = request.args.get('filtro', '').lower()

    # Buscar agentes do Firebase em vez de usar dados mock
    try:
        from firebase_functions import get_all_agents
        agents = get_all_agents()
    except Exception as e:
        print(f"❌ Erro ao buscar agentes do Firebase: {e}")
        return "Erro ao carregar dados dos agentes", 500

    # Aplicar filtro se existir
    if filtro:
        agents_filtrados = [a for a in agents if
                           filtro in a.get('nome', '').lower() or
                           filtro in a.get('funcao', '').lower() or
                           filtro in a.get('patente', '').lower() or
                           filtro in a.get('equipe', '').lower() or
                           filtro in a.get('viatura', '').lower()]
    else:
        agents_filtrados = agents

    # Preparar dados para o PDF
    dados_agentes = []
    for agent in agents_filtrados:
        dados_agentes.append({
            'nome': agent.get('nome', 'N/A'),
            'matricula': agent.get('matricula', 'N/A'),
            'idade': agent.get('idade', 'N/A'),
            'patente': agent.get('patente', 'N/A').capitalize() if agent.get('patente') else 'N/A',
            'funcao': agent.get('funcao', 'N/A').capitalize() if agent.get('funcao') else 'N/A',
            'equipe': agent.get('equipe', 'N/A').capitalize() if agent.get('equipe') else 'N/A',
            'viatura': agent.get('viatura', 'N/A'),
            'turno': agent.get('turno', 'N/A').capitalize() if agent.get('turno') else 'N/A'
        })

    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
                .header-info {
                    margin-bottom: 20px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }
                .filtro-info {
                    background-color: #e7f3ff;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>RELATÓRIO DE AGENTES - SEMURB</h2>
            </div>
            
            <div class="header-info">
                <strong>Data de emissão:</strong> {{ data_emissao }}<br>
                <strong>Total de agentes:</strong> {{ total_agentes }}
            </div>
            
            {% if filtro %}
            <div class="filtro-info">
                <strong>Filtro aplicado:</strong> {{ filtro }}
            </div>
            {% endif %}
            
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Matrícula</th>
                        <th>Idade</th>
                        <th>Patente</th>
                        <th>Função</th>
                        <th>Equipe</th>
                        <th>Veículo</th>
                        <th>Turno</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ag in agentes %}
                    <tr>
                        <td>{{ ag.nome }}</td>
                        <td>{{ ag.matricula }}</td>
                        <td>{{ ag.idade }}</td>
                        <td>{{ ag.patente }}</td>
                        <td>{{ ag.funcao }}</td>
                        <td>{{ ag.equipe }}</td>
                        <td>{{ ag.viatura }}</td>
                        <td>{{ ag.turno }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div style="margin-top: 30px; text-align: center; color: #666; font-size: 12px;">
                Relatório gerado automaticamente pelo Sistema SEMURB
            </div>
        </body>
    </html>
    """

    # Preparar dados para o template
    data_emissao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    total_agentes = len(dados_agentes)

    rendered_html = render_template_string(
        html_content, 
        agentes=dados_agentes,
        data_emissao=data_emissao,
        total_agentes=total_agentes,
        filtro=filtro if filtro else None
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    
    if pisa_status.err:
        print(f"❌ Erro ao gerar PDF: {pisa_status.err}")
        return "Erro ao gerar PDF", 500
    
    pdf_buffer.seek(0)

    # Nome do arquivo com base no filtro
    nome_filtro = f"filtro_{filtro}" if filtro else "todos"
    nome_arquivo = f'agentes_{nome_filtro}_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )


@app.route("/gerar_pdf_agentes_ocorrencias")
def gerar_pdf_agentes_oco():
    agente_id = request.args.get('filtro', '')
    mes = request.args.get('status', '').strip()

    agente = next((a for a in agents if a['id'] == agente_id), None)
    if not agente:
        return "Agente não encontrado", 404

    numero_viatura = agente.get('viatura_mes', '')
    ocorrencias = [o for o in Ocur_Vehicles if o['viatura'] == numero_viatura]

    if mes != 'todos' and mes:
        ocorrencias = [
            o for o in ocorrencias
            if datetime.strptime(o['data'], "%Y-%m-%d").strftime('%Y/%m') == mes
        ]

    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
        </head>
        <body>
            <h2 class="tittle"> Relatório do Agente - {{ info.nome }}</h2>
            <h3 class="tittle">Mes: {{ mes }}</h3>

            <h3 class="tittle">Informações do Agente<h3/>
            <table>
                <thead>
                    <tr>
                        <th class="thead-infos">Nome</th>
                        <th class="thead-infos">Cargo</th>
                        <th class="thead-infos">Função</th>
                        <th class="thead-infos">Viatura(Mês)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="table-infos">{{ info.nome }}</td>
                        <td class="table-infos">{{ info.cargo_at }}</td>
                        <td class="table-infos">{{ info.func_mes }}</td>
                        <td class="table-infos">{{ info.viatura_mes }}</td>
                    </tr>
                </tbody>
            </table>

            <h3 class="tittle">Ocorrências</h3>
            {% if ocorrencias%}
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Descrição</th>
                    </tr>
                </thead>
                <tbody>
                    {% for oco in ocorrencias %}
                    <tr>
                        <td>{{ oco.data }}</td>
                        <td>{{ oco.descricao }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align:center;">Nenhuma ocorrência registrada para este periodo.<p>
            {% endif %}
        </body>
    </html>
    '''
    """

    rendered_html = render_template_string(
        html_content,
        info=agente,
        id=agente['id'],
        mes=mes,
        ocorrencias=ocorrencias
    )

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name='detalhes_agente.pdf', mimetype='application/pdf')



@app.route(f'/pdf_detalhes_ocorrencia_<ocorrencia_id>')
def gerar_pdf_detalhes_ocorrencia(ocorrencia_id):
    ocorrencia_info = next((o for o in Ocur_Vehicles if o['id'] == ocorrencia_id), None)
    if not ocorrencia_info:
        return "Ocorrência não encontrada.", 404

    numero = ocorrencia_info['viatura']
    responsavel = next((r['nome'] for r in agents if r['viatura_mes'] == numero), None)

    nome_oco = ocorrencia_info['nomenclatura']

    if not ocorrencia_info:
        return "Ocorrência não encontrada.", 404

    html_template = '''
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
        </head>
        <body>
            <h2 class="title">Relatório - {{ info['nomenclatura'] }}</h2>

            {% if info %}
                <h3 class="section-title">Responsável e Viatura</h3>
                <table>
                    <tbody>
                        <tr>
                            <th>Motorista responsável</th>
                            <td>{{ responsavel }}</td>
                        </tr>
                        <tr>
                            <th>Viatura responsável</th>
                            <td>{{ info.get('viatura', 'Não informado') }}</td>
                        </tr>
                    </tbody>
                </table>

                <h3 class="section-title">Informações da Ocorrência</h3>
                <table>
                    <tbody>
                        <tr>
                            <th>Tipo</th>
                            <td>{{ info['nomenclatura'] }}</td>
                        </tr>
                        <tr>
                            <th>Endereço</th>
                            <td>{{ info.get('endereco', 'Não informado') }}</td>
                        </tr>
                        <tr>
                            <th>Descrição</th>
                            <td>{{ info.get('descricao', 'Não informada') }}</td>
                        </tr>
                        <tr>
                            <th>Data</th>
                            <td>{{ info.get('data', 'Não informada') }}</td>
                        </tr>
                    </tbody>
                </table>

                <h3 class="section-title">Informações para Contato</h3>
                <table>
                    <tbody>
                        <tr>
                            <th>Nome para contato</th>
                            <td>{{ info.get('n_cidadao', 'Não informado') }}</td>
                        </tr>
                        <tr>
                            <th>Contato</th>
                            <td>{{ info.get('contato', 'Não informado') }}</td>
                        </tr>
                    </tbody>
                </table>
            {% else %}
                <p style="text-align:center;">Nenhuma ocorrência encontrada.</p>
            {% endif %}
        </body>
    </html>
    '''

    html_content = render_template_string(
        html_template,
        info=ocorrencia_info,
        numero=numero,
        responsavel=responsavel
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500

    pdf_buffer.seek(0)
    return make_response(pdf_buffer.read(), {
        'content-Type': 'application/pdf',
        'content-Disposition': f'attachment; filename="Relatorio_ocorrencia_{nome_oco}.pdf"'
    })

@app.route("/gerar_pdf_ocorrencias")
def gerar_pdf_ocorrencias():
    print(f"🔍 PDF OCORRÊNCIAS - Chamada recebida")
    print(f"📋 Parâmetros: filtro={request.args.get('filtro')}, mes={request.args.get('mes')}")
    
    filtro = request.args.get('filtro', '').strip()
    if filtro.lower() == 'none':
        filtro = ''
    mes = request.args.get('mes', 'todos').strip()

    print(f"📊 Processando: filtro='{filtro}', mes='{mes}'")
    
    # ... resto do código permanece igual ...

    filtro_acento = remover_acentos(filtro) if filtro else ''

    if mes != 'todos' and mes:
        try:
            dt = datetime.strptime(mes, "%Y/%m")
            mes = dt.strftime("%Y/%m")
        except Exception:
            mes = 'todos'

    # Busca ocorrências do Firebase
    from firebase_functions import get_all_occurrences
    todas_ocorrencias = get_all_occurrences()

    def corresponde(item):
        match_filtro = True
        if filtro_acento:
            viatura_norm = remover_acentos(item.get('viatura', '').lower())
            responsavel_norm = remover_acentos(item.get('responsavel', '').lower())
            tipo_norm = remover_acentos(item.get('tipo_ocorrencia', '').lower())
            match_filtro = (filtro_acento in viatura_norm or 
                          filtro_acento in responsavel_norm or 
                          filtro_acento in tipo_norm)

        match_mes = True
        if mes != 'todos' and mes:
            try:
                item_mes = datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m')
                match_mes = (item_mes == mes)
            except Exception:
                match_mes = False

        return match_filtro and match_mes

    ocorrencias_filtradas = [o for o in todas_ocorrencias if corresponde(o)]

    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
        </head>
        <body>
            <h1>Ocorrências Registradas</h1>
            <p><strong>Filtro:</strong> {{ filtro_display }}</p>
            <p><strong>Mês:</strong> {{ mes_display }}</p>
            <p><strong>Total de ocorrências:</strong> {{ total }}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Responsável</th>
                        <th>Tipo</th>
                        <th>Veículo</th>
                        <th>Descrição</th>
                    </tr>
                </thead>
                <tbody>
    """

    for ocor in ocorrencias_filtradas:
        html_content += f"""
            <tr>
                <td>{ocor.get('data', '')} {ocor.get('horario', '')}</td>
                <td>{ocor.get('responsavel', '')}</td>
                <td>{ocor.get('tipo_ocorrencia', '')}</td>
                <td>{ocor.get('viatura', '')}</td>
                <td>{ocor.get('descricao', '')}</td>
            </tr>
        """

    html_content += """
                </tbody>
            </table>
        </body>
    </html>
    """

    # Preparar displays para o template
    filtro_display = filtro if filtro else "Todos"
    mes_display = "Todos os meses" if mes == 'todos' else datetime.strptime(mes, "%Y/%m").strftime("%B/%Y").capitalize()
    
    rendered_html = render_template_string(
        html_content, 
        filtro_display=filtro_display,
        mes_display=mes_display,
        total=len(ocorrencias_filtradas)
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500
    pdf_buffer.seek(0)

    nome_arquivo = f'ocorrencias_filtro={filtro or "todos"}_mes={mes}.pdf'

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )


@app.route("/gerar_pdf_ocorrencia_detalhes")
def gerar_pdf_ocorrencia_detalhes():
    ocorrencia_id = request.args.get('id', '')
    
    if not ocorrencia_id:
        return "ID da ocorrência não fornecido", 400

    # Busca a ocorrência do Firebase
    from firebase_functions import get_occurrence_by_id
    ocorrencia = get_occurrence_by_id(ocorrencia_id)
    
    if not ocorrencia:
        return "Ocorrência não encontrada", 404

    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                    width: 30%;
                }
                .info-table {
                    width: 100%;
                    margin-bottom: 2rem;
                }
            </style>
        </head>
        <body>
            <h2>Detalhes da Ocorrência</h2>
            
            <table class="info-table">
                <tbody>
                    <tr>
                        <th>Data e Hora</th>
                        <td>{{ ocorrencia.data }} {{ ocorrencia.horario }}</td>
                    </tr>
                    <tr>
                        <th>Tipo de Ocorrência</th>
                        <td>{{ ocorrencia.tipo_ocorrencia }}</td>
                    </tr>
                    <tr>
                        <th>Responsável</th>
                        <td>{{ ocorrencia.responsavel }}</td>
                    </tr>
                    <tr>
                        <th>Veículo</th>
                        <td>{{ ocorrencia.viatura }}</td>
                    </tr>
                </tbody>
            </table>

            <table class="info-table">
                <tbody>
                    <tr>
                        <th>Descrição</th>
                        <td>{{ ocorrencia.descricao }}</td>
                    </tr>
                    {% if ocorrencia.endereco %}
                    <tr>
                        <th>Endereço</th>
                        <td>{{ ocorrencia.endereco }}</td>
                    </tr>
                    {% endif %}
                    {% if ocorrencia.nome %}
                    <tr>
                        <th>Cidadão Atendido</th>
                        <td>{{ ocorrencia.nome }}</td>
                    </tr>
                    {% endif %}
                    {% if ocorrencia.contato %}
                    <tr>
                        <th>Contato</th>
                        <td>{{ ocorrencia.contato }}</td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>

            {% if ocorrencia.fotoUrl %}
            <div style="text-align: center; margin-top: 2rem;">
                <p><strong>Foto da Ocorrência:</strong></p>
                <img src="{{ ocorrencia.fotoUrl }}" style="max-width: 400px; max-height: 300px;" alt="Foto da Ocorrência">
            </div>
            {% endif %}
        </body>
    </html>
    """

    rendered_html = render_template_string(html_content, ocorrencia=ocorrencia)

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500
    pdf_buffer.seek(0)

    # Cria um nome amigável para o arquivo
    data_formatada = ocorrencia.get('data', '').replace('-', '')
    tipo_limpo = ocorrencia.get('tipo_ocorrencia', 'ocorrencia').replace(' ', '_').lower()
    nome_arquivo = f'ocorrencia_{data_formatada}_{tipo_limpo}.pdf'

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )

@app.route("/gerar_pdf_servicos_gerais")
def gerar_pdf_servicos_gerais():
    print(f"🔍 PDF SERVIÇOS GERAIS - Chamada recebida")
    print(f"📋 Parâmetros: filtro={request.args.get('filtro')}, mes={request.args.get('mes')}")
    
    filtro = request.args.get('filtro', '').strip()
    if filtro.lower() == 'none':
        filtro = ''
    mes = request.args.get('mes', 'todos').strip()

    print(f"📊 Processando: filtro='{filtro}', mes='{mes}'")
    
    filtro_acento = remover_acentos(filtro) if filtro else ''

    if mes != 'todos' and mes:
        try:
            dt = datetime.strptime(mes, "%Y/%m")
            mes = dt.strftime("%Y/%m")
        except Exception:
            mes = 'todos'

    # Busca serviços do Firebase
    from firebase_functions import get_all_services_with_agents
    todos_servicos = get_all_services_with_agents()

    def corresponde(item):
        match_filtro = True
        if filtro_acento:
            viatura_norm = remover_acentos(item.get('viatura', '').lower())
            responsavel_norm = remover_acentos(item.get('responsavel', '').lower())
            tipo_norm = remover_acentos(item.get('nomenclatura', '').lower())
            match_filtro = (filtro_acento in viatura_norm or 
                          filtro_acento in responsavel_norm or 
                          filtro_acento in tipo_norm)

        match_mes = True
        if mes != 'todos' and mes:
            try:
                item_mes = datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m')
                match_mes = (item_mes == mes)
            except Exception:
                match_mes = False

        return match_filtro and match_mes

    servicos_filtrados = [s for s in todos_servicos if corresponde(s)]

    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                }
                .header-info {
                    margin-bottom: 20px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }
                .filtro-info {
                    background-color: #e7f3ff;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>RELATÓRIO DE SERVIÇOS - SEMURB</h2>
            </div>
            
            <div class="header-info">
                <strong>Data de emissão:</strong> {{ data_emissao }}<br>
                <strong>Total de serviços:</strong> {{ total_servicos }}
            </div>
            
            {% if filtro %}
            <div class="filtro-info">
                <strong>Filtro aplicado:</strong> {{ filtro }}
            </div>
            {% endif %}
            
            {% if mes != 'todos' %}
            <div class="filtro-info">
                <strong>Mês selecionado:</strong> {{ mes_display }}
            </div>
            {% endif %}
            
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Horário</th>
                        <th>Responsável</th>
                        <th>Tipo de Serviço</th>
                        <th>Veículo</th>
                        <th>Descrição</th>
                        <th>Endereço</th>
                    </tr>
                </thead>
                <tbody>
                    {% for serv in servicos %}
                    <tr>
                        <td>{{ serv.data }}</td>
                        <td>{{ serv.horario }}</td>
                        <td>{{ serv.responsavel }}</td>
                        <td>{{ serv.nomenclatura }}</td>
                        <td>{{ serv.viatura }}</td>
                        <td>{{ serv.descricao }}</td>
                        <td>{{ serv.endereco }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            {% if not servicos %}
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3>Nenhum serviço encontrado para os critérios selecionados</h3>
            </div>
            {% endif %}
            
            <div style="margin-top: 30px; text-align: center; color: #666; font-size: 12px;">
                Relatório gerado automaticamente pelo Sistema SEMURB
            </div>
        </body>
    </html>
    """

    # Preparar displays para o template
    filtro_display = filtro if filtro else "Todos"
    mes_display = "Todos os meses" if mes == 'todos' else datetime.strptime(mes, "%Y/%m").strftime("%B/%Y").capitalize()
    data_emissao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    rendered_html = render_template_string(
        html_content, 
        servicos=servicos_filtrados,
        filtro=filtro_display,
        mes_display=mes_display,
        data_emissao=data_emissao,
        total_servicos=len(servicos_filtrados)
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        print(f"❌ Erro ao gerar PDF: {pisa_status.err}")
        return "Erro ao gerar PDF", 500
    pdf_buffer.seek(0)

    nome_arquivo = f'servicos_gerais_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )


@app.route("/gerar_pdf_servico_detalhes")
def gerar_pdf_servico_detalhes():
    service_id = request.args.get('id', '')
    
    if not service_id:
        return "ID do serviço não fornecido", 400

    # Busca o serviço do Firebase
    from firebase_functions import get_service_by_id, get_agents_by_vehicle
    servico = get_service_by_id(service_id)
    
    if not servico:
        return "Serviço não encontrado", 404

    # Busca agentes do veículo
    vehicle_number = servico.get('viatura')
    agentes_veiculo = get_agents_by_vehicle(vehicle_number) if vehicle_number else []

    # Encontra motorista e outros agentes
    motorista = next((a for a in agentes_veiculo if a.get('funcao', '').lower() == 'motorista'), None)
    outros_agentes = [a for a in agentes_veiculo if a != motorista]

    html_content = """
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <style>
                 body {
                    font-family: DejaVu Sans;
                    margin: 20px;
                }
                h2 {
                    text-align: center;
                    margin-bottom: 2rem;
                    font-size: 2rem;
                }
                h3.section-title {
                    margin-top: 2rem;
                    margin-bottom: 0.5rem;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 4px;
                    font-size: 1.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 2rem;
                    font-size: 1.2rem;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                    vertical-align: top;
                }
                th {
                    background-color: #f2f2f2;
                    width: 30%;
                }
                .info-table {
                    width: 100%;
                    margin-bottom: 2rem;
                }
                .agents-table {
                    width: 100%;
                    margin-top: 1rem;
                }
                .agent-photo {
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    object-fit: cover;
                }
            </style>
        </head>
        <body>
            <h2>Detalhes do Serviço</h2>
            
            <table class="info-table">
                <tbody>
                    <tr>
                        <th>Data e Hora</th>
                        <td>{{ servico.data }} {{ servico.horario }}</td>
                    </tr>
                    <tr>
                        <th>Tipo de Serviço</th>
                        <td>{{ servico.nomenclatura }}</td>
                    </tr>
                    <tr>
                        <th>Responsável</th>
                        <td>{{ servico.responsavel }}</td>
                    </tr>
                    <tr>
                        <th>Veículo</th>
                        <td>{{ servico.viatura }}</td>
                    </tr>
                </tbody>
            </table>

            <table class="info-table">
                <tbody>
                    <tr>
                        <th>Descrição</th>
                        <td>{{ servico.descricao }}</td>
                    </tr>
                    {% if servico.endereco %}
                    <tr>
                        <th>Endereço</th>
                        <td>{{ servico.endereco }}</td>
                    </tr>
                    {% endif %}
                    {% if servico.local %}
                    <tr>
                        <th>Local</th>
                        <td>{{ servico.local }}</td>
                    </tr>
                    {% endif %}
                    {% if servico.observacoes %}
                    <tr>
                        <th>Observações</th>
                        <td>{{ servico.observacoes }}</td>
                    </tr>
                    {% endif %}
                    {% if servico.qtd_items %}
                    <tr>
                        <th>Quantidade de Itens</th>
                        <td>{{ servico.qtd_items }}</td>
                    </tr>
                    {% endif %}
                </tbody>
            </table>

            {% if servico.fotoUrl %}
            <div style="text-align: center; margin-top: 2rem;">
                <p><strong>Foto do Serviço:</strong></p>
                <img src="{{ servico.fotoUrl }}" style="max-width: 400px; max-height: 300px;" alt="Foto do Serviço">
            </div>
            {% endif }

            <!-- Seção da Equipe -->
            <h3 class="section-title">Equipe Responsável</h3>
            
            {% if motorista or outros_agentes %}
            <table class="agents-table">
                <thead>
                    <tr>
                        <th>Foto</th>
                        <th>Nome</th>
                        <th>Função</th>
                        <th>Turno</th>
                    </tr>
                </thead>
                <tbody>
                    {% if motorista %}
                    <tr>
                        <td>
                            {% if motorista.foto_agnt %}
                            <img src="{{ motorista.foto_agnt }}" class="agent-photo" alt="{{ motorista.nome }}">
                            {% else %}
                            <div style="width: 50px; height: 50px; background: #ccc; border-radius: 50%;"></div>
                            {% endif %}
                        </td>
                        <td><strong>{{ motorista.nome }}</strong></td>
                        <td>{{ motorista.funcao|capitalize }}</td>
                        <td>{{ motorista.turno|capitalize }}</td>
                    </tr>
                    {% endif %}
                    
                    {% for agente in outros_agentes %}
                    <tr>
                        <td>
                            {% if agente.foto_agnt %}
                            <img src="{{ agente.foto_agnt }}" class="agent-photo" alt="{{ agente.nome }}">
                            {% else %}
                            <div style="width: 50px; height: 50px; background: #ccc; border-radius: 50%;"></div>
                            {% endif %}
                        </td>
                        <td>{{ agente.nome }}</td>
                        <td>{{ agente.funcao|capitalize }}</td>
                        <td>{{ agente.turno|capitalize }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="text-align: center; color: #666; padding: 20px;">
                Nenhum agente atribuído a este veículo
            </p>
            {% endif %}

            <div style="margin-top: 30px; text-align: center; color: #666; font-size: 12px;">
                Relatório gerado automaticamente pelo Sistema SEMURB - {{ data_emissao }}
            </div>
        </body>
    </html>
    """

    data_emissao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    rendered_html = render_template_string(
        html_content, 
        servico=servico,
        motorista=motorista,
        outros_agentes=outros_agentes,
        data_emissao=data_emissao
    )

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500
    pdf_buffer.seek(0)

    # Cria um nome amigável para o arquivo
    data_formatada = servico.get('data', '').replace('-', '')
    tipo_limpo = servico.get('nomenclatura', 'servico').replace(' ', '_').lower()
    nome_arquivo = f'servico_{data_formatada}_{tipo_limpo}.pdf'

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )



if __name__ == '__main__':
    app.run(debug=True)