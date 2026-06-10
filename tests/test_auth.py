import sqlite3
from datetime import datetime, timedelta
import hashlib

from backend.database import connection
from backend.services.auth import (
    cadastrar_usuario,
    autenticar_usuario,
    gerar_token_redefinicao,
    redefinir_senha_por_token,
    redefinir_senha,
    verificar_hash
)

def test_register_and_auth_pbkdf2(tmp_path):
    db = tmp_path / "test_auth_pbkdf2.db"
    connection.DB_PATH = str(db)
    connection.init_db()

    # 1. Cadastrar usuário e verificar que foi salvo com PBKDF2
    ok, msg = cadastrar_usuario("testuser", "mysecurepassword", "test@example.com", "mysecretanswer")
    assert ok, msg

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT senha, resposta_seguranca FROM usuarios WHERE username = 'testuser'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    senha_hash, resposta_hash = row
    assert senha_hash.startswith("pbkdf2_sha256$")
    assert resposta_hash.startswith("pbkdf2_sha256$")

    # 2. Autenticar com a senha correta
    sucesso, mensagem, usuario_id = autenticar_usuario("testuser", "mysecurepassword")
    assert sucesso
    assert usuario_id is not None

    # Autenticar com a senha incorreta
    sucesso_err, mensagem_err, usuario_id_err = autenticar_usuario("testuser", "wrongpassword")
    assert not sucesso_err
    assert usuario_id_err is None


def test_legacy_password_migration(tmp_path):
    db = tmp_path / "test_auth_migration.db"
    connection.DB_PATH = str(db)
    connection.init_db()

    # 1. Inserir manualmente um usuário com hash legado (SHA-256 simples)
    username = "legacyuser"
    senha_legada = "legacy_pass"
    resposta_legada = "legacy_answer"
    
    hash_senha_legada = hashlib.sha256(senha_legada.encode()).hexdigest()
    hash_resposta_legada = hashlib.sha256(resposta_legada.encode()).hexdigest()

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (username, email, senha, resposta_seguranca) VALUES (?, ?, ?, ?)",
        (username, "legacy@example.com", hash_senha_legada, hash_resposta_legada)
    )
    conn.commit()
    conn.close()

    # 2. Fazer login: deve validar a senha legada e migrá-la automaticamente para PBKDF2
    sucesso, mensagem, usuario_id = autenticar_usuario(username, senha_legada)
    assert sucesso, mensagem
    assert usuario_id is not None

    # Verificar se o hash foi migrado para PBKDF2 no banco
    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT senha, resposta_seguranca FROM usuarios WHERE id = ?", (usuario_id,))
    senha_hash, resposta_hash = cursor.fetchone()
    conn.close()

    assert senha_hash.startswith("pbkdf2_sha256$")
    # A resposta_seguranca ainda não foi migrada porque o login só migra a senha
    assert resposta_hash == hash_resposta_legada

    # 3. Fazer login novamente (agora validando contra o novo PBKDF2)
    sucesso_novo, mensagem_novo, usuario_id_novo = autenticar_usuario(username, senha_legada)
    assert sucesso_novo
    assert usuario_id_novo == usuario_id


def test_legacy_security_question_migration_and_recovery(tmp_path):
    db = tmp_path / "test_auth_recovery.db"
    connection.DB_PATH = str(db)
    connection.init_db()

    username = "recoveryuser"
    senha_legada = "recovery_pass"
    resposta_legada = "recovery_answer"
    
    hash_senha_legada = hashlib.sha256(senha_legada.encode()).hexdigest()
    hash_resposta_legada = hashlib.sha256(resposta_legada.encode()).hexdigest()

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (username, email, senha, resposta_seguranca) VALUES (?, ?, ?, ?)",
        (username, "recovery@example.com", hash_senha_legada, hash_resposta_legada)
    )
    conn.commit()
    conn.close()

    # 1. Recuperar senha: deve aceitar a resposta legada, migrá-la para PBKDF2 e salvar a nova senha em PBKDF2
    nova_senha = "new_secure_pass"
    sucesso, mensagem = redefinir_senha(username, resposta_legada, nova_senha)
    assert sucesso, mensagem

    # 2. Verificar banco de dados: ambos devem ser PBKDF2 agora
    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT senha, resposta_seguranca FROM usuarios WHERE username = ?", (username,))
    senha_hash, resposta_hash = cursor.fetchone()
    conn.close()

    assert senha_hash.startswith("pbkdf2_sha256$")
    assert resposta_hash.startswith("pbkdf2_sha256$")

    # 3. Autenticar com a nova senha
    sucesso_login, _, _ = autenticar_usuario(username, nova_senha)
    assert sucesso_login
