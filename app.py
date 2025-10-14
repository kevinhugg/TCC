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

#Função genérica para gerar pdf's
def gerar_pdf(template_htlm, dados, nome_arquivo):
    html_content = render_template_string(template_htlm, **dados)
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)

    if pisa_status.err:
        return "Erro na geração de PDF, 500"

    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"{nome_arquivo}.pdf",
        mimetype='application/pdf',
    )

@app.route(f'/gerar_pdf_<tipo_pdf>')
def gerar_pdf_tipo_pdf(tipo_pdf):
    filtro = request.args.get('filtro', '').strip().lower()
    data_emissao = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    dados = {"data_emissao": data_emissao}

    # Carrega apenas os dados correspondentes
    if tipo_pdf == "agentes":
        from firebase_functions import get_all_agents
        agentes = get_all_agents()
        if filtro:
            agentes = [a for a in agentes if filtro in a.get("nome", "").lower()]
        dados["agentes"] = agentes

    elif tipo_pdf == "ocorrencias":
        from firebase_functions import get_all_ocorrencias
        ocorrencias = get_all_ocorrencias()
        if filtro:
            ocorrencias = [o for o in ocorrencias if filtro in o.get("nomenclatura", "").lower()]
        dados["ocorrencias"] = ocorrencias


    elif tipo_pdf == "viaturas_danificadas":  # novo tipo de PDF

        from firebase_functions import get_all_damage_reports

        danos = get_all_damage_reports()

        # Filtra conforme o status e parte se houver

        status = request.args.get('status', 'all')

        parte = request.args.get('parte', 'all')

        if status != 'all':
            danos = [d for d in danos if d.get('status') == status]

        if parte != 'all':
            danos = [d for d in danos if d.get('parte') == parte]

        # Opcional: contar danos por veículo

        damage_counts = {}

        for d in danos:

            num_viatura = d.get('viatura')

            if num_viatura:
                damage_counts[num_viatura] = damage_counts.get(num_viatura, 0) + 1

        # Junta dados com veículos (se quiser)
        from firebase_functions import get_all_vehicles

        veiculos = get_all_vehicles()

        for v in veiculos:
            v['damage_count'] = damage_counts.get(v.get('numero'), 0)

        dados["danos"] = danos

        dados["veiculos"] = veiculos  # opcional se quiser mostrar info do veículo junto

        dados["data_emissao"] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    elif tipo_pdf == "servicos_gerais":
        from firebase_functions import get_all_services_with_agents
        servicos = get_all_services_with_agents()

        filtro = request.args.get("filtro", "").strip().lower()
        mes = request.args.get("mes", "todos")

        # Filtra pelo mês
        if mes != "todos":
            servicos = [
                s for s in servicos
                if s.get("data") and datetime.strptime(s["data"], "%Y-%m-%d").strftime("%Y/%m") == mes
            ]

        # Filtra pelo texto
        if filtro:
            filtro_normalizado = remover_acentos(filtro)
            servicos = [
                s for s in servicos
                if filtro_normalizado in remover_acentos(s.get("viatura", "")) or
                   filtro_normalizado in remover_acentos(s.get("nomenclatura", "")) or
                   filtro_normalizado in remover_acentos(s.get("responsavel", ""))
            ]

        dados["servicos"] = servicos
        dados["data_emissao"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    template_universal = """
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <style>
            body { font-family: DejaVu Sans; margin: 20px; color: #000; font-size: 14px; }
            h2 { text-align: center; font-size: 24px; margin-bottom: 20px; }
            .header-info { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 16px; }
            .section-title { font-size: 20px; margin-top: 30px; margin-bottom: 10px; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
            .item-card { border: 1px solid #000; border-radius: 5px; padding: 15px; margin-bottom: 20px; page-break-inside: avoid; }
            .item-card h3 { margin-top: 0; font-size: 18px; margin-bottom: 10px; }
            .item-table { width: 100%; border-collapse: collapse; font-size: 16px; }
            .item-table td { border: 1px solid #000; padding: 8px; }
            .item-table td.label { font-weight: bold; background-color: #f2f2f2; width: 30%; }
            .item-table td.value { width: 70%; }
            .footer { text-align: center; font-size: 12px; color: #666; margin-top: 30px; }
        </style>
    </head>
    <body>
        <h2>RELATÓRIO - SEMURB</h2>

        <div class="header-info">
            <strong>Data de emissão:</strong> {{ data_emissao }}
        </div>

        {% if agentes %}
        <div class="section-title">Agentes</div>
        <table class="item-table">
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Função</th>
                    <th>Equipe</th>
                    <th>Turno</th>
                    <th>Viatura</th>
                </tr>
            </thead>
            <tbody>
                {% for ag in agentes %}
                <tr>
                    <td>{{ ag.nome }}</td>
                    <td>{{ ag.funcao or "N/A" }}</td>
                    <td>{{ ag.equipe or "N/A" }}</td>
                    <td>{{ ag.turno or "N/A" }}</td>
                    <td>{{ ag.viatura or "N/A" }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        {% if ocorrencias %}
        <div class="section-title">Ocorrências</div>
        {% for oco in ocorrencias %}
        <div class="item-card">
            <h3>{{ oco.nomenclatura or "Ocorrência" }}</h3>
            <table class="item-table">
                {% if oco.data %}<tr><td class="label">Data</td><td class="value">{{ oco.data }}</td></tr>{% endif %}
                {% if oco.responsavel %}<tr><td class="label">Responsável</td><td class="value">{{ oco.responsavel }}</td></tr>{% endif %}
                {% if oco.viatura %}<tr><td class="label">Veículo</td><td class="value">{{ oco.viatura }}</td></tr>{% endif %}
                {% if oco.descricao %}<tr><td class="label">Descrição</td><td class="value">{{ oco.descricao }}</td></tr>{% endif %}
            </table>
        </div>
        {% endfor %}
        {% endif %}

        {% if danos %}
        <div class="section-title">Viaturas Danificadas</div>
        <table class="item-table">
            <thead>
                <tr>
                    <th>N° Viatura</th>
                    <th>Área Avariada</th>
                    <th>Descrição</th>
                    <th>Status</th>
                    <th>Data</th>
                </tr>
            </thead>
            <tbody>
                {% for d in danos %}
                <tr>
                    <td>{{ d.viatura }}</td>
                    <td>{{ d.parte }}</td>
                    <td>{{ d.descricao }}</td>
                    <td>{{ d.status }}</td>
                    <td>{{ d.data }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        {% if servicos %}
        <div class="section-title">Serviços</div>
        <table class="item-table">
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Responsável</th>
                    <th>Tipo</th>
                    <th>Veículo</th>
                </tr>
            </thead>
            <tbody>
                {% for s in servicos %}
                <tr>
                    <td>{{ s.data or "N/A" }}</td>
                    <td>{{ s.responsavel or "N/A" }}</td>
                    <td>{{ s.nomenclatura or "N/A" }}</td>
                    <td>{{ s.viatura or "N/A" }}</td>
                </tr>
        {% endfor %}
    </tbody>
</table>
{% endif %}


        <div class="footer">
            Relatório gerado automaticamente pelo Sistema SEMURB
        </div>
    </body>
    </html>
    """

    return gerar_pdf(template_universal, dados, f"relatorio_{tipo_pdf}")


if __name__ == '__main__':
    app.run(debug=True)