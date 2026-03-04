import sqlite3
import os  # <--- ESSA LINHA É A QUE ESTÁ FALTANDO
from datetime import datetime, timedelta

DB_PATH = "data/studyup.db"

def init_db():
    if not os.path.exists('data'):
        os.makedirs('data')
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor() # A definição do cursor acontece aqui dentro

    cursor.execute('CREATE TABLE IF NOT EXISTS disciplinas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            disciplina_id INTEGER, 
            nome TEXT NOT NULL, 
            concluido BOOLEAN DEFAULT 0,
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id)
        )
    ''')

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

    # --- NOVA TABELA DE FLASHCARDS ---
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

# --- FUNÇÕES DE FLASHCARDS ---

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

# --- MANTENHA AS OUTRAS FUNÇÕES ABAIXO (adicionar_disciplina, registrar_desempenho, etc.) ---

def adicionar_disciplina(nome):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO disciplinas (nome) VALUES (?)', (nome,))
        conn.commit()
        conn.close()
        return True
    except:
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

def registrar_desempenho(topico_id, questoes, acertos):
    percentual = (acertos / questoes) * 100 if questoes > 0 else 0
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

init_db()