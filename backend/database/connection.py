import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

# --- CONFIGURAÇÃO DE CAMINHO DINÂMICO ---
# Isso garante que o banco de dados seja criado na mesma pasta deste arquivo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "studyup.db")

@contextmanager
def abrir_conexao():
    """Gerenciador de contexto para conexões do SQLite.
    Garante o fechamento da conexão mesmo em caso de erro, e executa commit/rollback.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _has_column(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row[1] == column_name for row in cursor.fetchall())


def init_db():
    """Inicializa o banco de dados e cria todas as tabelas necessárias."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()

        # 1. Tabela de Usuários (Nova para o sistema de login)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                pergunta_seguranca TEXT,
                resposta_seguranca TEXT,
                reset_token TEXT,
                reset_token_expiry TEXT
            )
        ''')

        # 2. Tabela de Disciplinas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disciplinas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nome TEXT NOT NULL UNIQUE,
                usuario_id INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # 3. Tabela de Tópicos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                disciplina_id INTEGER, 
                nome TEXT NOT NULL, 
                concluido BOOLEAN DEFAULT 0,
                usuario_id INTEGER,
                FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
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

        # 5b. Tabela de Progresso de Flashcards (Leitner SRS)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards_progresso (
                usuario_id INTEGER,
                flashcard_id INTEGER,
                caixa INTEGER DEFAULT 1,
                proxima_revisao TEXT,
                PRIMARY KEY (usuario_id, flashcard_id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (flashcard_id) REFERENCES flashcards (id)
            )
        ''')

        # Garantir colunas históricas na tabela sessoes
        try:
            cursor.execute('ALTER TABLE sessoes ADD COLUMN data_sessao TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe


        # 6. Tabela de Cronograma Semanal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cronograma (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina_id INTEGER,
                dia_semana INTEGER NOT NULL,
                usuario_id INTEGER,
                start_time TEXT,
                duration INTEGER DEFAULT 60,
                color TEXT DEFAULT '#4CAF50',
                FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # 7. Tabela de Compromissos Extras
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compromissos_extras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                dia_semana INTEGER NOT NULL,
                start_time TEXT,
                duration INTEGER DEFAULT 60,
                color TEXT DEFAULT '#FF9800',
                usuario_id INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # Ajustar tabelas antigas para suportar usuário e respostas de recuperação
        if _has_column(cursor, 'usuarios', 'email') is False:
            try:
                cursor.execute('ALTER TABLE usuarios ADD COLUMN email TEXT')
            except sqlite3.OperationalError:
                pass
        if _has_column(cursor, 'usuarios', 'pergunta_seguranca') is False:
            try:
                cursor.execute('ALTER TABLE usuarios ADD COLUMN pergunta_seguranca TEXT')
            except sqlite3.OperationalError:
                pass
        if _has_column(cursor, 'usuarios', 'resposta_seguranca') is False:
            try:
                cursor.execute('ALTER TABLE usuarios ADD COLUMN resposta_seguranca TEXT')
            except sqlite3.OperationalError:
                pass
        if _has_column(cursor, 'usuarios', 'reset_token') is False:
            try:
                cursor.execute('ALTER TABLE usuarios ADD COLUMN reset_token TEXT')
            except sqlite3.OperationalError:
                pass
        if _has_column(cursor, 'usuarios', 'reset_token_expiry') is False:
            try:
                cursor.execute('ALTER TABLE usuarios ADD COLUMN reset_token_expiry TEXT')
            except sqlite3.OperationalError:
                pass
        if _has_column(cursor, 'disciplinas', 'usuario_id') is False:
            try:
                cursor.execute('ALTER TABLE disciplinas ADD COLUMN usuario_id INTEGER')
            except sqlite3.OperationalError:
                pass
        if _has_column(cursor, 'topicos', 'usuario_id') is False:
            try:
                cursor.execute('ALTER TABLE topicos ADD COLUMN usuario_id INTEGER')
            except sqlite3.OperationalError:
                pass

        # Alterar tabela cronograma para adicionar novas colunas se não existirem
        try:
            cursor.execute('ALTER TABLE cronograma ADD COLUMN start_time TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe
        try:
            cursor.execute('ALTER TABLE cronograma ADD COLUMN duration INTEGER DEFAULT 60')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE cronograma ADD COLUMN color TEXT DEFAULT \'#4CAF50\'')
        except sqlite3.OperationalError:
            pass


# --- FUNÇÕES DE USUÁRIO ---

# --- FUNÇÕES DE USUÁRIO ---

def validar_login(username_or_email, senha_hash):
    """Verifica se as credenciais existem no banco."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM usuarios WHERE (username = ? OR email = ?) AND senha = ?',
            (username_or_email, username_or_email, senha_hash),
        )
        return cursor.fetchone()


def buscar_usuario_por_username_ou_email(username_or_email):
    """Busca um usuário no banco pelo username ou email com colunas explícitas."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, username, email, senha, pergunta_seguranca, resposta_seguranca, reset_token, reset_token_expiry FROM usuarios WHERE username = ? OR email = ?',
            (username_or_email, username_or_email),
        )
        return cursor.fetchone()



# --- FUNÇÕES DE DISCIPLINAS E TÓPICOS ---

def adicionar_disciplina(nome, usuario_id=None):
    try:
        with abrir_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO disciplinas (nome, usuario_id) VALUES (?, ?)',
                (nome, usuario_id),
            )
        return True
    except sqlite3.IntegrityError:
        return False

def listar_disciplinas(usuario_id=None):
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        if usuario_id is None:
            cursor.execute('SELECT * FROM disciplinas')
        else:
            cursor.execute(
                'SELECT * FROM disciplinas WHERE usuario_id IS NULL OR usuario_id = ?',
                (usuario_id,),
            )
        return cursor.fetchall()

def adicionar_topico(disciplina_id, nome_topico, usuario_id=None):
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO topicos (disciplina_id, nome, usuario_id) VALUES (?, ?, ?)',
            (disciplina_id, nome_topico, usuario_id),
        )

def listar_topicos_por_disciplina(disciplina_id, usuario_id=None):
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        if usuario_id is None:
            cursor.execute('SELECT * FROM topicos WHERE disciplina_id = ?', (disciplina_id,))
        else:
            cursor.execute(
                'SELECT * FROM topicos WHERE disciplina_id = ? AND (usuario_id IS NULL OR usuario_id = ?)',
                (disciplina_id, usuario_id),
            )
        return cursor.fetchall()


def atualizar_status_topico(topico_id, status: bool):
    """Marca um tópico como concluído (True) ou não concluído (False)."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE topicos SET concluido = ? WHERE id = ?', (1 if status else 0, topico_id))


def calcular_progresso_disciplina(disciplina_id, usuario_id=None):
    """Retorna a porcentagem de tópicos concluídos em uma disciplina."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        if usuario_id is None:
            cursor.execute('SELECT COUNT(*) FROM topicos WHERE disciplina_id = ?', (disciplina_id,))
        else:
            cursor.execute(
                'SELECT COUNT(*) FROM topicos WHERE disciplina_id = ? AND (usuario_id IS NULL OR usuario_id = ?)',
                (disciplina_id, usuario_id),
            )
        total = cursor.fetchone()[0] or 0

        if total == 0:
            return 0

        if usuario_id is None:
            cursor.execute('SELECT COUNT(*) FROM topicos WHERE disciplina_id = ? AND concluido = 1', (disciplina_id,))
        else:
            cursor.execute(
                'SELECT COUNT(*) FROM topicos WHERE disciplina_id = ? AND concluido = 1 AND (usuario_id IS NULL OR usuario_id = ?)',
                (disciplina_id, usuario_id),
            )
        concluido = cursor.fetchone()[0] or 0
        return round((concluido / total) * 100, 1)


def calcular_progresso_geral(usuario_id=None):
    """Retorna a porcentagem geral de tópicos concluídos para um usuário."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        if usuario_id is None:
            cursor.execute('SELECT COUNT(*) FROM topicos')
        else:
            cursor.execute(
                'SELECT COUNT(*) FROM topicos WHERE usuario_id IS NULL OR usuario_id = ?',
                (usuario_id,),
            )
        total = cursor.fetchone()[0] or 0

        if total == 0:
            return 0

        if usuario_id is None:
            cursor.execute('SELECT COUNT(*) FROM topicos WHERE concluido = 1')
        else:
            cursor.execute(
                'SELECT COUNT(*) FROM topicos WHERE concluido = 1 AND (usuario_id IS NULL OR usuario_id = ?)',
                (usuario_id,),
            )
        concluido = cursor.fetchone()[0] or 0
        return round((concluido / total) * 100, 1)



# --- FUNÇÕES DE DESEMPENHO E FLASHCARDS ---

def registrar_desempenho(topico_id, questoes, acertos):
    percentual = (acertos / questoes) * 100 if questoes > 0 else 0
    # Regra de negócio simples para revisão
    dias_revisao = 7 if percentual >= 75 else 1
    data_revisao = (datetime.now() + timedelta(days=dias_revisao)).date()
    
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessoes (topico_id, questoes_total, questoes_acerto, percentual, proxima_revisao, data_sessao) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (topico_id, questoes, acertos, percentual, data_revisao, datetime.now()))

def adicionar_flashcard(topico_id, pergunta, resposta):
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO flashcards (topico_id, pergunta, resposta) VALUES (?, ?, ?)', 
                       (topico_id, pergunta, resposta))

def listar_flashcards_por_topico(topico_id):
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM flashcards WHERE topico_id = ?', (topico_id,))
        return cursor.fetchall()


def salvar_progresso_flashcard(usuario_id, flashcard_id, acertou):
    """
    Atualiza o progresso do usuário no flashcard usando a lógica Leitner.
    caixa 1: 1 dia
    caixa 2: 3 dias
    caixa 3: 7 dias
    caixa 4: 14 dias
    caixa 5: 30 dias
    """
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        
        # Buscar progresso atual
        cursor.execute(
            'SELECT caixa FROM flashcards_progresso WHERE usuario_id = ? AND flashcard_id = ?',
            (usuario_id, flashcard_id)
        )
        row = cursor.fetchone()
        
        if row:
            caixa_atual = row[0]
            if acertou:
                nova_caixa = min(caixa_atual + 1, 5)
            else:
                nova_caixa = 1
        else:
            nova_caixa = 2 if acertou else 1
            
        # Definir intervalo
        intervalos = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
        dias = intervalos.get(nova_caixa, 1)
        proxima = (datetime.now() + timedelta(days=dias)).date().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO flashcards_progresso (usuario_id, flashcard_id, caixa, proxima_revisao)
            VALUES (?, ?, ?, ?)
        ''', (usuario_id, flashcard_id, nova_caixa, proxima))


def listar_flashcards_revisao(topico_id, usuario_id):
    """
    Retorna os flashcards que precisam ser revisados hoje ou são novos para o usuário.
    Retorna lista de tuplas: (id, topico_id, pergunta, resposta, caixa, proxima_revisao)
    """
    hoje = datetime.now().date().isoformat()
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT f.id, f.topico_id, f.pergunta, f.resposta, p.caixa, p.proxima_revisao
            FROM flashcards f
            LEFT JOIN flashcards_progresso p ON f.id = p.flashcard_id AND p.usuario_id = ?
            WHERE f.topico_id = ? AND (p.proxima_revisao IS NULL OR p.proxima_revisao <= ?)
        ''', (usuario_id, topico_id, hoje))
        return cursor.fetchall()


# --- FUNÇÕES DE CRONOGRAMA ---

def salvar_cronograma(disciplina_id, dia_semana, start_time=None, duration=60, color='#4CAF50', usuario_id=None):
    """
    Salva ou atualiza um cronograma para uma disciplina em um dia específico.
    dia_semana: 0=Segunda, 1=Terça, ..., 6=Domingo
    start_time: string no formato 'HH:MM'
    duration: duração em minutos
    color: cor em hexadecimal
    """
    try:
        with abrir_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cronograma (disciplina_id, dia_semana, start_time, duration, color, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (disciplina_id, dia_semana, start_time, duration, color, usuario_id))
        return True
    except Exception as e:
        print(f"Erro ao salvar cronograma: {e}")
        return False


def buscar_cronograma_usuario(usuario_id=None):
    """
    Retorna o cronograma de uma semana para um usuário.
    Retorna lista de tuplas: (id, disciplina_id, disciplina_nome, dia_semana, start_time, duration, color)
    """
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.disciplina_id, d.nome, c.dia_semana, c.start_time, c.duration, c.color
            FROM cronograma c
            JOIN disciplinas d ON c.disciplina_id = d.id
            WHERE c.usuario_id = ? OR c.usuario_id IS NULL
            ORDER BY c.dia_semana ASC, c.start_time ASC
        ''', (usuario_id,))
        return cursor.fetchall()


def obter_disciplinas_por_dia(dia_semana, usuario_id=None):
    """Retorna as disciplinas agendadas para um dia específico."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.id, c.disciplina_id, d.nome
            FROM cronograma c
            JOIN disciplinas d ON c.disciplina_id = d.id
            WHERE c.dia_semana = ? AND (c.usuario_id = ? OR c.usuario_id IS NULL)
        ''', (dia_semana, usuario_id))
        return cursor.fetchall()


def remover_cronograma(cronograma_id):
    """Remove um item do cronograma."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cronograma WHERE id = ?', (cronograma_id,))


def salvar_compromisso_extra(nome, dia_semana, start_time=None, duration=60, color='#FF9800', usuario_id=None):
    """
    Salva um compromisso extra.
    """
    try:
        with abrir_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO compromissos_extras (nome, dia_semana, start_time, duration, color, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, dia_semana, start_time, duration, color, usuario_id))
        return True
    except Exception as e:
        print(f"Erro ao salvar compromisso extra: {e}")
        return False


def buscar_compromissos_extras_usuario(usuario_id=None):
    """
    Retorna os compromissos extras de uma semana para um usuário.
    Retorna lista de tuplas: (id, nome, dia_semana, start_time, duration, color)
    """
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, nome, dia_semana, start_time, duration, color
            FROM compromissos_extras
            WHERE usuario_id = ? OR usuario_id IS NULL
            ORDER BY dia_semana ASC, start_time ASC
        ''', (usuario_id,))
        return cursor.fetchall()


def remover_compromisso_extra(compromisso_id):
    """Remove um compromisso extra."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM compromissos_extras WHERE id = ?', (compromisso_id,))


def foi_estudada_hoje(disciplina_id):
    """Verifica se uma disciplina foi estudada hoje."""
    hoje = datetime.now().date()
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM sessoes s
            JOIN topicos t ON s.topico_id = t.id
            WHERE t.disciplina_id = ? AND DATE(s.data_sessao) = ?
        ''', (disciplina_id, hoje))
        return cursor.fetchone()[0] > 0




def checar_conexao() -> bool:
    """Verifica se o banco de dados está acessível."""
    try:
        with abrir_conexao() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False



# Garante que o banco seja criado ao importar este arquivo pela primeira vez
init_db()