import sqlite3
import pandas as pd
from backend.database.connection import DB_PATH

def buscar_dados_progresso():
    conn = sqlite3.connect(DB_PATH)
    # Buscando da tabela 'sessoes'
    query = '''
        SELECT d.nome as Disciplina, s.percentual
        FROM sessoes s
        JOIN topicos t ON s.topico_id = t.id
        JOIN disciplinas d ON t.disciplina_id = d.id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def obter_questoes_resolvidas_hoje():
    """Retorna o total de questões respondidas nas sessões de hoje."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(questoes_total), 0)
        FROM sessoes
        WHERE DATE(data_sessao) = DATE('now')
    """)
    total = cursor.fetchone()[0]
    conn.close()
    return int(total)
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT d.nome as Disciplina, t.nome as Topico, s.proxima_revisao
        FROM sessoes s
        JOIN topicos t ON s.topico_id = t.id
        JOIN disciplinas d ON t.disciplina_id = d.id
        WHERE s.proxima_revisao <= DATE('now')
        ORDER BY s.proxima_revisao ASC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df   