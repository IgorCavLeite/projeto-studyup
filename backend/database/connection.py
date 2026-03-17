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

# Garante que o banco seja criado ao importar este arquivo pela primeira vez
init_db()