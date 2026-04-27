import sqlite3
import hashlib
import os

# Importar o caminho correto do banco de dados
from backend.database.connection import DB_PATH
from backend.services.auth import gerar_hash


def atualizar_senha(username, nova_senha):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verifica se o usuário existe
        cursor.execute(
            'SELECT id FROM usuarios WHERE username = ?', (username,))
        if not cursor.fetchone():
            conn.close()
            return False, "Usuário não encontrado."

        # Atualiza para a nova senha com hash
        senha_hash = gerar_hash(nova_senha)
        cursor.execute(
            'UPDATE usuarios SET senha = ? WHERE username = ?', (senha_hash, username))

        conn.commit()
        conn.close()
        return True, "Senha atualizada com sucesso!"
    except Exception as e:
        return False, f"Erro técnico: {str(e)}"
