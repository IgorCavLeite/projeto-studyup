from datetime import datetime
import pandas as pd
from backend.database.connection import abrir_conexao

def buscar_dados_progresso():
    # Buscando da tabela 'sessoes'
    query = '''
        SELECT d.nome as Disciplina, s.percentual
        FROM sessoes s
        JOIN topicos t ON s.topico_id = t.id
        JOIN disciplinas d ON t.disciplina_id = d.id
    '''
    with abrir_conexao() as conn:
        df = pd.read_sql_query(query, conn)
    return df


def obter_questoes_resolvidas_hoje():
    """Retorna o total de questões respondidas nas sessões de hoje (fuso horário local)."""
    hoje = datetime.now().date().isoformat()
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(questoes_total), 0)
            FROM sessoes
            WHERE DATE(data_sessao) = ?
        """, (hoje,))
        total = cursor.fetchone()[0]
    return int(total)


def buscar_alertas_revisao():
    """Busca tópicos que precisam de revisão hoje ou estão atrasados (fuso horário local)."""
    hoje = datetime.now().date().isoformat()
    query = '''
        SELECT d.nome as Disciplina, t.nome as Topico, s.proxima_revisao
        FROM sessoes s
        JOIN topicos t ON s.topico_id = t.id
        JOIN disciplinas d ON t.disciplina_id = d.id
        WHERE s.proxima_revisao <= ?
        ORDER BY s.proxima_revisao ASC
    '''
    with abrir_conexao() as conn:
        df = pd.read_sql_query(query, conn, params=(hoje,))
    return df


