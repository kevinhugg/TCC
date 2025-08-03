#Precisa baixar o Flask antes de iniciar esses:

from flask import Flask, render_template, request, redirect, url_for, flash, session, render_template_string, make_response, send_file
from flask_mail import Mail, Message
import random
import string
from datetime import datetime
import unicodedata

from xhtml2pdf import pisa
import io
import os
import base64

from xhtml2pdf.default import DEFAULT_FONT
DEFAULT_FONT['DejaVuSans'] = '/caminho/para/DejaVuSans.ttf'

from dash_app import create_dash_app
from data.dados import *

app = Flask(__name__)

#dash_app = create_dash_app(app)
#import sys
#sys.modules['dash_instance'] = dash_app

#Para isso aqui, precisa do Banco de Dados também, então depois que o Miguel tiver terminado, eu conecto tudo aqui

app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com' 
app.config['MAIL_PASSWORD'] = 'sua_senha_do_app' 
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com' 
app.secret_key = 'semurb' 

mail = Mail(app)

#integração do Dash
dash_app = create_dash_app(app)

# Rota para index.html (sua página de login)
@app.route('/')
def pagina_login():
    return render_template('login/index.html')

#Rota para o forms de login
@app.route('/login', methods=['POST'])
def info_login():
    if request.method == 'POST':
        matricula = request.form['matricula'] 
        senha = request.form['senha']      

#Aqui precisa do Banco de Dados, então é tudo hipotético
    if matricula == '2' and senha == '2':
        session['usuario_logado'] = True
        flash('Login realizado com sucesso!', 'success')
        return redirect('/dashboard/')
    else:
        flash('Matrícula ou senha inválidos', 'danger')
        return redirect(url_for('pagina_login'))

#Rota para metodoRecSenha.html
@app.route('/rec-senha')
def metodoRecSenha():
    return render_template('login/metodoRecSenha.html')

@app.route('/enviar-codigo', methods=['POST'])
def enviar_codigo():
    email = request.form['email']
    codigo = ''.join(random.choices(string.digits, k=6))

    session['reset_code'] = codigo
    session['reset_email'] = email
    session['reset_code_expiry'] = datetime.datetime.now() + datetime.timedelta(minutes=10)

    try:
        msg = Message("Código de Recuperação de Senha",
                      recipients=[email])
        msg.body = f"Seu código de recuperação de senha é: {codigo}\nEste código é válido por 10 minutos."
        mail.send(msg)
        flash('Um código de recuperação foi enviado para o seu e-mail.', 'info')
        return redirect(url_for('pagina_codigo'))
    
    except Exception as e:
        flash(f'Erro ao enviar e-mail: {e}', 'danger')
        print(f"Erro ao enviar e-mail: {e}")
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
    
    #Aqui ele olha se tem uma conta já
    if 'reset_code' not in session or 'reset_code_expiry' not in session:
        flash('Sua sessão de recuperação expirou ou é inválida. Por favor, solicite um novo código.', 'danger')
        return redirect(url_for('metodoRecSenha'))

    #Aqui é para ver se o código expirou
    if datetime.datetime.now() > session['reset_code_expiry']:
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
        return redirect(url_for('red_senha')) # Próxima etapa
    else:
        flash('Código inválido. Tente novamente.', 'danger')
        return redirect(url_for('pagina_codigo')) # Volta para a página de código
    


# Rota para a página de redefinição de senha
@app.route('/redefinir-senha')
def red_senha():
    
    if 'reset_email' not in session:
        flash('Acesso inválido à página de redefinição de senha.', 'danger')
        return redirect(url_for('pagina_login'))
    return render_template('login/redefinirSenha.html')

##LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('pagina_login'))

@app.before_request
def proteger_rotas():
    #se for para a rota de /dashboard ele so deixa usar se estiver logado
    if request.path.startswith('/dashboard') and not session.get('usuario_logado'):
        return redirect(url_for('pagina_login'))

#PDF'S
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
        imagem = imagem_embed,
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

    if filtro:
        filtrados = [a for a in agents if filtro in a['nome'].lower() or filtro in a['func_mes'].lower() or filtro in a['cargo_at'].lower()]
    else:
        filtrados = agents

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
            <h1>Lista de Agentes</h1>
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Cargo</th>
                        <th>Função</th>
                        <th>Viatura</th>
                    </tr>
                </thead>
                <tbody>
                    {% for ag in agents %}
                    <tr>
                        <td>{{ ag.nome }}</td>
                        <td>{{ ag.cargo_at }}</td>
                        <td>{{ ag.func_mes }}</td>
                        <td>{{ ag.viatura_mes }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body> 
    </html>
    """

    rendered_html = render_template_string(html_content, agents=filtrados)

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(rendered_html.encode('utf-8')), dest=pdf_buffer)
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, as_attachment=True, download_name='agentes.pdf', mimetype='application/pdf')

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

@app.route("/gerar_pdf_servicos_gerais")
def gerar_pdf_servicos_gerais():
    filtro = request.args.get('filtro', '').strip()
    if filtro.lower() == 'none':
        filtro = ''
    mes = request.args.get('mes', 'todos').strip()

    filtro_acento = remover_acentos(filtro) if filtro else ''

    if mes != 'todos' and mes:
        try:
            dt = datetime.strptime(mes, "%Y/%m")
            mes = dt.strftime("%Y/%m")  # força formato correto (ex: "2025/07")
        except Exception:
            mes = 'todos'

    def corresponde(item):
        match_filtro = True
        if filtro_acento:
            viatura_norm = remover_acentos(item.get('viatura', '').lower())
            responsavel = next((a['nome'] for a in agents if a.get('viatura_mes') == item.get('viatura')), '')
            responsavel_norm = remover_acentos(responsavel.lower())
            match_filtro = filtro_acento in viatura_norm or filtro_acento in responsavel_norm

        match_mes = True
        if mes != 'todos' and mes:
            try:
                item_mes = datetime.strptime(item['data'], '%Y-%m-%d').strftime('%Y/%m')
                print(f"Comparando meses: item_mes={item_mes} com filtro mes={mes}")  # DEBUG
                match_mes = (item_mes == mes)
            except Exception:
                match_mes = False

        return match_filtro and match_mes

    servicos = [o for o in Ocur_Vehicles if o.get('class') == 'serviço']
    filtrados = [o for o in servicos if corresponde(o)]

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
            <h1>Serviços Registrados</h1>
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Responsável</th>
                        <th>Tipo</th>
                        <th>Veículo</th>
                    </tr>
                </thead>
                <tbody>
    """

    for serv in filtrados:
        responsavel = next(
            (a['nome'] for a in agents if a.get('viatura_mes') == serv.get('viatura')),
            'Desconhecido'
        )
        html_content += f"""
            <tr>
                <td>{serv.get('data', '')}</td>
                <td>{responsavel}</td>
                <td>{serv.get('nomenclatura', '')}</td>
                <td>{serv.get('viatura', '')}</td>
            </tr>
        """

    html_content += """
                </tbody>
            </table>
        </body>
    </html>
    """

    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)
    if pisa_status.err:
        return "Erro ao gerar PDF", 500
    pdf_buffer.seek(0)

    nome_arquivo = f'servicos_de={filtro or "todos"}_data={mes}.pdf'

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype='application/pdf'
    )

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

if __name__ == '__main__':
    app.run(debug=True)