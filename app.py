#Precisa baixar o Flask antes de iniciar esses:

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import random
import string
import datetime # Para controlar a expiração do código

from dash_app import create_dash_app

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
    if matricula == 'admin' and senha == 'gusmao':
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

if __name__ == '__main__':
    app.run(debug=True)