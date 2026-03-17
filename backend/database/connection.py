import sqlite3
import os
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DE CAMINHO DINÂMICO ---
# Isso garante que o banco de dados seja criado na mesma pasta deste arquivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "studyup.db")

def init_db():
    """Inicializa o banco de dados e cria todas as tabelas necessárias."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tabela de Usuários (Nova para o sistema de login)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    # 2. Tabela de Disciplinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # 3. Tabela de Tópicos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            disciplina_id INTEGER, 
            nome TEXT NOT NULL, 
            concluido BOOLEAN DEFAULT 0,
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id)
        )
    ''')

    # 4. Tabela de Sessões de Estudo/Desempenho
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            topico_id INTEGER, 
            questoes_total INTEGER, 
            questoes_acerto INTEGER, 
            percentual REAL,
            proxima_revisao DATE,
            data_sessao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topico_id) REFERENCES topicos (id)
        )
    ''')

    # 5. Tabela de Flashcards
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topico_id INTEGER,
            pergunta TEXT NOT NULL,
            resposta TEXT NOT NULL,
            FOREIGN KEY (topico_id) REFERENCES topicos (id)
        )
    ''')

    # 6. Tabela de Cronograma Semanal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cronograma (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina_id INTEGER,
            dia_semana INTEGER NOT NULL,
            usuario_id INTEGER,
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            UNIQUE (disciplina_id, dia_semana)
        )
    ''')

    conn.commit()
    conn.close()

# --- FUNÇÕES DE USUÁRIO ---

def validar_login(username, senha_hash):
    """Verifica se as credenciais existem no banco."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (username, senha_hash))
    user = cursor.fetchone()
    conn.close()
    return user

# --- FUNÇÕES DE DISCIPLINAS E TÓPICOS ---

def adicionar_disciplina(nome):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO disciplinas (nome) VALUES (?)', (nome,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def listar_disciplinas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM disciplinas')
    dados = cursor.fetchall()
    conn.close()
    return dados

def adicionar_topico(disciplina_id, nome_topico):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO topicos (disciplina_id, nome) VALUES (?, ?)', (disciplina_id, nome_topico))
    conn.commit()
    conn.close()

def listar_topicos_por_disciplina(disciplina_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM topicos WHERE disciplina_id = ?', (disciplina_id,))
    dados = cursor.fetchall()
    conn.close()
    return dados


def atualizar_status_topico(topico_id, status: bool):
    """Marca um tópico como concluído (True) ou não concluído (False)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE topicos SET concluido = ? WHERE id = ?', (1 if status else 0, topico_id))
    conn.commit()
    conn.close()


def calcular_progresso_disciplina(disciplina_id):
    """Retorna a porcentagem de tópicos concluídos em uma disciplina."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM topicos WHERE disciplina_id = ?', (disciplina_id,))
    total = cursor.fetchone()[0] or 0

    if total == 0:
        conn.close()
        return 0

    cursor.execute('SELECT COUNT(*) FROM topicos WHERE disciplina_id = ? AND concluido = 1', (disciplina_id,))
    concluido = cursor.fetchone()[0] or 0
    conn.close()
    return round((concluido / total) * 100, 1)


def calcular_progresso_geral():
    """Retorna a porcentagem geral de tópicos concluídos em todo o sistema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM topicos')
    total = cursor.fetchone()[0] or 0

    if total == 0:
        conn.close()
        return 0

    cursor.execute('SELECT COUNT(*) FROM topicos WHERE concluido = 1')
    concluido = cursor.fetchone()[0] or 0
    conn.close()
    return round((concluido / total) * 100, 1)


# --- FUNÇÕES DE DESEMPENHO E FLASHCARDS ---

def registrar_desempenho(topico_id, questoes, acertos):
    percentual = (acertos / questoes) * 100 if questoes > 0 else 0
    # Regra de negócio simples para revisão
    dias_revisao = 7 if percentual >= 75 else 1
    data_revisao = (datetime.now() + timedelta(days=dias_revisao)).date()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessoes (topico_id, questoes_total, questoes_acerto, percentual, proxima_revisao) 
        VALUES (?, ?, ?, ?, ?)
    ''', (topico_id, questoes, acertos, percentual, data_revisao))
    conn.commit()
    conn.close()

def adicionar_flashcard(topico_id, pergunta, resposta):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO flashcards (topico_id, pergunta, resposta) VALUES (?, ?, ?)', 
                   (topico_id, pergunta, resposta))
    conn.commit()
    conn.close()

def listar_flashcards_por_topico(topico_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM flashcards WHERE topico_id = ?', (topico_id,))
    dados = cursor.fetchall()
    conn.close()
    return dados


# --- FUNÇÕES DE CRONOGRAMA ---

def salvar_cronograma(disciplina_id, dia_semana, usuario_id=None):
    """
    Salva ou atualiza um cronograma para uma disciplina em um dia específico.
    dia_semana: 0=Segunda, 1=Terça, ..., 6=Domingo
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO cronograma (disciplina_id, dia_semana, usuario_id)
            VALUES (?, ?, ?)
        ''', (disciplina_id, dia_semana, usuario_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar cronograma: {e}")
        return False


def buscar_cronograma_usuario(usuario_id=None):
    """
    Retorna o cronograma de uma semana para um usuário.
    Retorna lista de tuplas: (disciplina_id, disciplina_nome, dia_semana)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.disciplina_id, d.nome, c.dia_semana
        FROM cronograma c
        JOIN disciplinas d ON c.disciplina_id = d.id
        WHERE c.usuario_id = ? OR c.usuario_id IS NULL
        ORDER BY c.dia_semana ASC
    ''', (usuario_id,))
    dados = cursor.fetchall()
    conn.close()
    return dados


def obter_disciplinas_por_dia(dia_semana, usuario_id=None):
    """Retorna as disciplinas agendadas para um dia específico."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.id, c.disciplina_id, d.nome
        FROM cronograma c
        JOIN disciplinas d ON c.disciplina_id = d.id
        WHERE c.dia_semana = ? AND (c.usuario_id = ? OR c.usuario_id IS NULL)
    ''', (dia_semana, usuario_id))
    dados = cursor.fetchall()
    conn.close()
    return dados


def remover_cronograma(cronograma_id):
    """Remove um item do cronograma."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cronograma WHERE id = ?', (cronograma_id,))
    conn.commit()
    conn.close()


def foi_estudada_hoje(disciplina_id):
    """Verifica se uma disciplina foi estudada hoje."""
    hoje = datetime.now().date()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM sessoes s
        JOIN topicos t ON s.topico_id = t.id
        WHERE t.disciplina_id = ? AND DATE(s.data_sessao) = ?
    ''', (disciplina_id, hoje))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0




def checar_conexao() -> bool:
    """Verifica se o banco de dados está acessível."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


# Garante que o banco seja criado ao importar este arquivo pela primeira vez
init_db()