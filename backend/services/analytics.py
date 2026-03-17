import sqlite3
import pandas as pd

DB_PATH = "data/studyup.db"

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

def buscar_alertas_revisao():
    """Busca tópicos que precisam de revisão hoje ou estão atrasados."""
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