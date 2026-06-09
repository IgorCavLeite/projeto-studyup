import sqlite3
from datetime import datetime, timedelta

from backend.database import connection


def test_register_and_auth(tmp_path):
    db = tmp_path / "test_auth.db"
    connection.DB_PATH = str(db)
    connection.init_db()

    from backend.services.auth import (
        cadastrar_usuario,
        autenticar_usuario,
        gerar_token_redefinicao,
        redefinir_senha_por_token,
    )

    ok, msg = cadastrar_usuario("u1", "pass", "u1@example.com")
    assert ok, msg
    ok2, msg2 = cadastrar_usuario("u2", "pass2", "u2@example.com")
    assert ok2, msg2

    sucesso, mensagem, usuario_id = autenticar_usuario("u1", "pass")
    assert sucesso is True
    assert usuario_id is not None

    sucesso2, mensagem2, usuario_id2 = autenticar_usuario("u2", "pass2")
    assert sucesso2 is True
    assert usuario_id2 is not None
    assert usuario_id != usuario_id2

    assert connection.adicionar_disciplina("Disciplina U1", usuario_id)
    assert connection.adicionar_disciplina("Disciplina U2", usuario_id2)

    disciplinas_u1 = connection.listar_disciplinas(usuario_id)
    disciplinas_u2 = connection.listar_disciplinas(usuario_id2)

    assert any(d[1] == "Disciplina U1" for d in disciplinas_u1)
    assert not any(d[1] == "Disciplina U2" for d in disciplinas_u1)
    assert any(d[1] == "Disciplina U2" for d in disciplinas_u2)

    token = gerar_token_redefinicao()
    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE usuarios SET reset_token = ?, reset_token_expiry = ? WHERE id = ?',
        (token, (datetime.now() + timedelta(hours=1)).isoformat(), usuario_id),
    )
    conn.commit()
    conn.close()

    sucesso, mensagem = redefinir_senha_por_token(token, "newpass")
    assert sucesso, mensagem

    sucesso, mensagem, _ = autenticar_usuario("u1", "newpass")
    assert sucesso is True

    sucesso_old, _, _ = autenticar_usuario("u1", "pass")
    assert sucesso_old is False
