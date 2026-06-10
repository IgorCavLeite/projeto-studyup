import sqlite3
from datetime import datetime, timedelta

from backend.database import connection


def test_leitner_srs_logic(tmp_path):
    # Configurar BD temporário
    db = tmp_path / "test_flashcards.db"
    connection.DB_PATH = str(db)
    connection.init_db()

    usuario_id = 1
    topico_id = 1

    # 1. Adicionar flashcards para teste
    connection.adicionar_flashcard(topico_id, "Pergunta 1", "Resposta 1")
    connection.adicionar_flashcard(topico_id, "Pergunta 2", "Resposta 2")

    # 2. Inicialmente, todos os cartões do tópico devem ser retornados para revisão
    due_cards = connection.listar_flashcards_revisao(topico_id, usuario_id)
    assert len(due_cards) == 2
    # Formato do retorno: (id, topico_id, pergunta, resposta, caixa, proxima_revisao)
    assert due_cards[0][2] == "Pergunta 1"
    assert due_cards[0][4] is None  # Sem caixa inicial

    fc1_id = due_cards[0][0]
    fc2_id = due_cards[1][0]

    # 3. Marcar fc1 como "Acertei" (caixa = 2, próxima revisão = hoje + 3 dias)
    connection.salvar_progresso_flashcard(usuario_id, fc1_id, True)

    # Verificar caixa e data de revisão no progresso
    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT caixa, proxima_revisao FROM flashcards_progresso WHERE usuario_id = ? AND flashcard_id = ?', (usuario_id, fc1_id))
    prog = cursor.fetchone()
    conn.close()
    assert prog is not None
    assert prog[0] == 2  # Caixa 2
    
    hoje = datetime.now().date()
    proxima_esperada = (hoje + timedelta(days=3)).isoformat()
    assert prog[1] == proxima_esperada

    # 4. Listar revisões novamente: apenas fc2 deve vir (já que fc1 foi programado para daqui a 3 dias)
    due_cards = connection.listar_flashcards_revisao(topico_id, usuario_id)
    assert len(due_cards) == 1
    assert due_cards[0][0] == fc2_id

    # 5. Marcar fc1 como "Errei" (reseta para caixa = 1, próxima revisão = hoje + 1 dia)
    connection.salvar_progresso_flashcard(usuario_id, fc1_id, False)

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT caixa, proxima_revisao FROM flashcards_progresso WHERE usuario_id = ? AND flashcard_id = ?', (usuario_id, fc1_id))
    prog = cursor.fetchone()
    conn.close()
    assert prog[0] == 1  # Reseta para caixa 1
    proxima_esperada_erro = (hoje + timedelta(days=1)).isoformat()
    assert prog[1] == proxima_esperada_erro
