import hashlib
import sqlite3
# Importamos o DB_PATH e a função de validar do seu connection.py
from backend.database.connection import DB_PATH

def gerar_hash(senha):
    """
    Transforma a senha em um resumo criptográfico (Hash).
    Isso é padrão de segurança em ADS para evitar salvar senhas em texto puro.
    """
    return hashlib.sha256(senha.encode()).hexdigest()

def cadastrar_usuario(username, senha):
    """
    Lógica para inserir um novo usuário no banco de dados.
    """
    if not username or not senha:
        return False, "Usuário e senha são obrigatórios!"
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Geramos o hash da senha antes de salvar
        senha_criptografada = gerar_hash(senha)
        
        cursor.execute('INSERT INTO usuarios (username, senha) VALUES (?, ?)', 
                       (username, senha_criptografada))
        
        conn.commit()
        conn.close()
        return True, "Usuário cadastrado com sucesso! Agora você pode fazer login."
        
    except sqlite3.IntegrityError:
        # Esse erro acontece se o username já existir (devido ao UNIQUE no banco)
        return False, "Este nome de usuário já está em uso."
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"

def autenticar_usuario(username, senha):
    """
    Lógica para verificar se o usuário e senha estão corretos.
    """
    if not username or not senha:
        return False, "Preencha todos os campos!"

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Transformamos a senha digitada em hash para comparar com o que está no banco
        senha_hash = gerar_hash(senha)
        
        cursor.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', 
                       (username, senha_hash))
        
        user = cursor.fetchone()
        conn.close()

        if user:
            return True, "Login realizado com sucesso!"
        else:
            return False, "Usuário ou senha incorretos."
            
    except Exception as e:
        return False, f"Erro na autenticação: {str(e)}"