import hashlib
import os
import secrets
import smtplib
import ssl
import sqlite3
from datetime import datetime, timedelta
from email.message import EmailMessage

# Importamos o módulo de connection para ler DB_PATH dinamicamente
from backend.database import connection

def gerar_hash(senha):
    """
    Transforma a senha em um resumo criptográfico (Hash).
    Isso é padrão de segurança para evitar salvar senhas em texto puro.
    """
    return hashlib.sha256(senha.encode()).hexdigest()


def _montar_link_redefinicao(token):
    base_url = os.getenv("PASSWORD_RESET_BASE_URL", "http://localhost:8501")
    return f"{base_url.rstrip('/')}/?reset_token={token}"


def _enviar_email(destino, assunto, corpo):
    smtp_host = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    remetente = os.getenv("PASSWORD_RESET_FROM", smtp_user or "no-reply@studyup.local")

    # Se variáveis SMTP não configuradas, permitir um fallback de desenvolvimento.
    # Define PASSWORD_RESET_DEV_FALLBACK=1 para salvar o conteúdo do e-mail em disco
    # e permitir testes locais sem enviar e-mail real.
    if not smtp_host or not smtp_user or not smtp_password:
        dev_fallback = os.getenv("PASSWORD_RESET_DEV_FALLBACK", "1")
        if dev_fallback == "1":
            try:
                fallback_path = os.path.join(os.getcwd(), "tmp_last_reset_email.txt")
                with open(fallback_path, "w", encoding="utf-8") as f:
                    f.write(f"To: {destino}\nSubject: {assunto}\n\n{corpo}\n")
                return True, f"SMTP não configurado: link de redefinição salvo em {fallback_path}"
            except Exception as e:
                return False, f"Falha ao gravar arquivo de fallback: {e}"
        return False, "O servidor de e-mail não está configurado. Defina SMTP_SERVER, SMTP_USER e SMTP_PASSWORD."

    mensagem = EmailMessage()
    mensagem["Subject"] = assunto
    mensagem["From"] = remetente
    mensagem["To"] = destino
    mensagem.set_content(corpo)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_password)
            server.send_message(mensagem)
        return True, "E-mail enviado com sucesso."
    except Exception as e:
        return False, f"Erro ao enviar o e-mail: {str(e)}"


def cadastrar_usuario(username, senha, email, resposta_seguranca=None):
    """
    Lógica para inserir um novo usuário no banco de dados.
    """
    if not username or not senha or not email:
        return False, "Usuário, senha e e-mail são obrigatórios!"

    try:
        conn = sqlite3.connect(connection.DB_PATH)
        cursor = conn.cursor()

        senha_criptografada = gerar_hash(senha)
        resposta_criptografada = gerar_hash(resposta_seguranca) if resposta_seguranca else None

        cursor.execute(
            'INSERT INTO usuarios (username, email, senha, resposta_seguranca) VALUES (?, ?, ?, ?)',
            (username, email, senha_criptografada, resposta_criptografada),
        )

        conn.commit()
        conn.close()
        return True, "Usuário cadastrado com sucesso! Agora você pode fazer login."

    except sqlite3.IntegrityError:
        return False, "Este nome de usuário ou e-mail já está em uso."
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def autenticar_usuario(username_or_email, senha):
    """
    Lógica para verificar se o usuário e senha estão corretos.
    """
    if not username_or_email or not senha:
        return False, "Preencha todos os campos!", None
    try:
        senha_hash = gerar_hash(senha)
        user = connection.validar_login(username_or_email, senha_hash)

        if user:
            return True, "Login realizado com sucesso!", user[0]
        else:
            return False, "Usuário ou senha incorretos.", None

    except Exception as e:
        return False, f"Erro na autenticação: {str(e)}", None


def gerar_token_redefinicao():
    """Gera um token seguro para redefinição de senha."""
    return secrets.token_urlsafe(32)


def _salvar_token_redefinicao(usuario_id, token, expiry):
    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE usuarios SET reset_token = ?, reset_token_expiry = ? WHERE id = ?',
        (token, expiry.isoformat(), usuario_id),
    )
    conn.commit()
    conn.close()


def solicitar_link_redefinicao(email):
    if not email:
        return False, "Informe o e-mail para receber o link de recuperação."

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE email = ?', (email,))
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        return False, "E-mail não cadastrado."

    usuario_id = usuario[0]
    token = gerar_token_redefinicao()
    expiry = datetime.now() + timedelta(hours=1)
    _salvar_token_redefinicao(usuario_id, token, expiry)

    link = _montar_link_redefinicao(token)
    assunto = "Redefinição de senha - StudyUp"
    corpo = (
        f"Olá!\n\nRecebemos um pedido para redefinir sua senha."
        f"\n\nUse este link para criar uma nova senha:\n{link}"
        f"\n\nO link expira em 1 hora. Se você não solicitou essa ação, ignore esta mensagem."
    )

    sucesso, mensagem = _enviar_email(email, assunto, corpo)
    if not sucesso:
        return False, mensagem
    return True, "Link de recuperação enviado por e-mail. Verifique sua caixa de entrada."


def validar_token_redefinicao(token):
    if not token:
        return None

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, reset_token_expiry FROM usuarios WHERE reset_token = ?',
        (token,),
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return None

    usuario_id, expiry_text = usuario
    if expiry_text is None:
        return None

    try:
        expiry = datetime.fromisoformat(expiry_text)
    except ValueError:
        return None

    if datetime.now() > expiry:
        return None

    return usuario_id


def limpar_token_redefinicao(usuario_id):
    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE usuarios SET reset_token = NULL, reset_token_expiry = NULL WHERE id = ?',
        (usuario_id,),
    )
    conn.commit()
    conn.close()


def redefinir_senha_por_token(token, nova_senha):
    if not token or not nova_senha:
        return False, "Token e nova senha são obrigatórios."

    usuario_id = validar_token_redefinicao(token)
    if not usuario_id:
        return False, "Token inválido ou expirado."

    try:
        conn = sqlite3.connect(connection.DB_PATH)
        cursor = conn.cursor()
        nova_senha_hash = gerar_hash(nova_senha)
        cursor.execute(
            'UPDATE usuarios SET senha = ? WHERE id = ?',
            (nova_senha_hash, usuario_id),
        )
        conn.commit()
        conn.close()
        limpar_token_redefinicao(usuario_id)
        return True, "Senha redefinida com sucesso. Você pode fazer login com a nova senha."
    except Exception as e:
        return False, f"Erro ao redefinir senha: {str(e)}"


def redefinir_senha(username, resposta_seguranca, nova_senha):
    if not username or not resposta_seguranca or not nova_senha:
        return False, "Preencha todos os campos de recuperação."

    try:
        conn = sqlite3.connect(connection.DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, resposta_seguranca FROM usuarios WHERE username = ?',
            (username,),
        )
        usuario = cursor.fetchone()

        if not usuario:
            conn.close()
            return False, "Usuário não encontrado."

        usuario_id, resposta_hash = usuario
        if resposta_hash is None:
            conn.close()
            return False, "Este usuário não possui palavra-chave de recuperação cadastrada."

        if resposta_hash != gerar_hash(resposta_seguranca):
            conn.close()
            return False, "Resposta de recuperação incorreta."

        nova_senha_hash = gerar_hash(nova_senha)
        cursor.execute(
            'UPDATE usuarios SET senha = ? WHERE id = ?',
            (nova_senha_hash, usuario_id),
        )
        conn.commit()
        conn.close()
        return True, "Senha redefinida com sucesso. Você já pode fazer login com a nova senha."
    except Exception as e:
        return False, f"Erro ao redefinir senha: {str(e)}"
