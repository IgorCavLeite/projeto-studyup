import sqlite3
from datetime import datetime, timedelta

from backend.database import connection
from backend.services import analytics


def test_analytics_timezone_and_filters(tmp_path):
    # 1. Configurar banco temporário
    db = tmp_path / "test_analytics.db"
    connection.DB_PATH = str(db)
    analytics.DB_PATH = str(db)
    connection.init_db()

    # 2. Cadastrar uma disciplina e um tópico de teste
    usuario_id = 1
    connection.adicionar_disciplina("Python", usuario_id)
    disciplinas = connection.listar_disciplinas(usuario_id)
    disc_id = disciplinas[0][0]

    connection.adicionar_topico(disc_id, "Variáveis", usuario_id)
    topicos = connection.listar_topicos_por_disciplina(disc_id, usuario_id)
    top_id = topicos[0][0]

    # 3. Inserir sessões com diferentes datas/horários
    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)
    amanha = hoje + timedelta(days=1)

    conn = sqlite3.connect(connection.DB_PATH)
    cursor = conn.cursor()

    # Sessão 1: Hoje (questoes_total = 10, proxima_revisao = amanhã)
    cursor.execute('''
        INSERT INTO sessoes (topico_id, questoes_total, questoes_acerto, percentual, proxima_revisao, data_sessao) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (top_id, 10, 8, 80.0, amanha.date().isoformat(), hoje))

    # Sessão 2: Ontem (questoes_total = 5, proxima_revisao = hoje)
    cursor.execute('''
        INSERT INTO sessoes (topico_id, questoes_total, questoes_acerto, percentual, proxima_revisao, data_sessao) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (top_id, 5, 4, 80.0, hoje.date().isoformat(), ontem))

    # Sessão 3: Amanhã (questoes_total = 15, proxima_revisao = daqui a 3 dias)
    cursor.execute('''
        INSERT INTO sessoes (topico_id, questoes_total, questoes_acerto, percentual, proxima_revisao, data_sessao) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (top_id, 15, 12, 80.0, (hoje + timedelta(days=3)).date().isoformat(), amanha))

    conn.commit()
    conn.close()

    # 4. Validar obter_questoes_resolvidas_hoje()
    # Deve contar apenas as questões feitas na data local de hoje (Sessão 1 = 10 questões)
    # Sessão 2 (ontem) e Sessão 3 (amanhã) devem ser ignoradas.
    questoes_hoje = analytics.obter_questoes_resolvidas_hoje()
    assert questoes_hoje == 10

    # 5. Validar buscar_alertas_revisao()
    # Devem vir apenas os tópicos com proxima_revisao <= hoje (Sessão 2 = hoje, ou seja, <= hoje)
    # A Sessão 1 (amanhã) e Sessão 3 (daqui a 3 dias) devem ser ignoradas.
    alertas = analytics.buscar_alertas_revisao()
    assert len(alertas) == 1
    assert alertas.iloc[0]['Disciplina'] == "Python"
    assert alertas.iloc[0]['Topico'] == "Variáveis"
    assert alertas.iloc[0]['proxima_revisao'] == hoje.date().isoformat()
