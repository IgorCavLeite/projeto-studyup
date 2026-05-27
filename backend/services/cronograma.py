"""
Serviço de Cronograma de Estudos
Gerencia cronogramas semanais com disciplinas e compromissos extras.
"""

import sqlite3
from datetime import datetime, timedelta
from backend.database.connection import (
    DB_PATH,
    salvar_cronograma,
    remover_cronograma,
    buscar_cronograma_usuario,
    obter_disciplinas_por_dia,
    salvar_compromisso_extra,
    remover_compromisso_extra,
    buscar_compromissos_extras_usuario,
    foi_estudada_hoje,
)

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
CORES_PADRAO = {
    'verde': '#4CAF50',
    'azul': '#2196F3',
    'laranja': '#FF9800',
    'rosa': '#E91E63',
    'roxo': '#9C27B0',
    'vermelho': '#F44336',
}


def validar_dia_semana(dia):
    """Valida se o dia da semana é válido (0-6)."""
    return 0 <= dia <= 6


def validar_horario(horario):
    """Valida se o horário está no formato HH:MM."""
    try:
        hora, minuto = horario.split(':')
        hora = int(hora)
        minuto = int(minuto)
        return 0 <= hora <= 23 and 0 <= minuto <= 59
    except:
        return False


def validar_duracao(duracao):
    """Valida se a duração é válida (em minutos)."""
    return isinstance(duracao, int) and duracao > 0 and duracao <= 480  # Máx 8 horas


def adicionar_disciplina_cronograma(disciplina_id, dia_semana, start_time, duration=60, color='#4CAF50', usuario_id=None):
    """
    Adiciona uma disciplina ao cronograma com validação.
    
    Args:
        disciplina_id: ID da disciplina
        dia_semana: 0-6 (Segunda-Domingo)
        start_time: Horário em formato 'HH:MM'
        duration: Duração em minutos
        color: Cor em hexadecimal
        usuario_id: ID do usuário (opcional)
    
    Returns:
        (sucesso: bool, mensagem: str, cronograma_id: int ou None)
    """
    # Validações
    if not validar_dia_semana(dia_semana):
        return False, "Dia da semana inválido (0-6)", None
    
    if not validar_horario(start_time):
        return False, "Horário inválido. Use formato HH:MM", None
    
    if not validar_duracao(duration):
        return False, "Duração inválida (1-480 minutos)", None
    
    if not (color.startswith('#') and len(color) == 7):
        return False, "Cor inválida. Use formato hexadecimal #RRGGBB", None
    
    try:
        if salvar_cronograma(disciplina_id, dia_semana, start_time, duration, color, usuario_id):
            return True, "Disciplina adicionada ao cronograma com sucesso!", None
        else:
            return False, "Erro ao salvar cronograma", None
    except Exception as e:
        return False, f"Erro: {str(e)}", None


def remover_disciplina_cronograma(cronograma_id):
    """
    Remove uma disciplina do cronograma.
    
    Args:
        cronograma_id: ID do item do cronograma
    
    Returns:
        (sucesso: bool, mensagem: str)
    """
    try:
        remover_cronograma(cronograma_id)
        return True, "Disciplina removida do cronograma"
    except Exception as e:
        return False, f"Erro ao remover: {str(e)}"


def obter_cronograma_completo(usuario_id=None):
    """
    Retorna o cronograma completo organizado por dia.
    
    Args:
        usuario_id: ID do usuário (opcional)
    
    Returns:
        dict com estrutura: {dia: [items]}
    """
    cronograma_raw = buscar_cronograma_usuario(usuario_id)
    compromissos = buscar_compromissos_extras_usuario(usuario_id)
    
    cronograma_por_dia = {i: {'disciplinas': [], 'compromissos': []} for i in range(7)}
    
    for item in cronograma_raw:
        dia = int(item[3]) if item[3] is not None else 0
        cronograma_por_dia[dia]['disciplinas'].append({
            'id': item[0],
            'disciplina_id': item[1],
            'nome': item[2],
            'dia': dia,
            'horario': item[4],
            'duracao': item[5],
            'cor': item[6],
            'tipo': 'disciplina'
        })
    
    for item in compromissos:
        dia = int(item[2]) if item[2] is not None else 0
        cronograma_por_dia[dia]['compromissos'].append({
            'id': item[0],
            'nome': item[1],
            'dia': dia,
            'horario': item[3],
            'duracao': item[4],
            'cor': item[5],
            'tipo': 'compromisso'
        })
    
    return cronograma_por_dia


def calcular_progresso_dia(dia_semana, usuario_id=None):
    """
    Calcula o progresso de estudo do dia.
    
    Args:
        dia_semana: 0-6
        usuario_id: ID do usuário (opcional)
    
    Returns:
        dict com: {'total': int, 'estudadas': int, 'percentual': float}
    """
    disciplinas = obter_disciplinas_por_dia(dia_semana, usuario_id)
    total = len(disciplinas)
    
    if total == 0:
        return {'total': 0, 'estudadas': 0, 'percentual': 0.0}
    
    estudadas = sum(1 for _, disc_id, _ in disciplinas if foi_estudada_hoje(disc_id))
    percentual = (estudadas / total) * 100 if total > 0 else 0
    
    return {
        'total': total,
        'estudadas': estudadas,
        'percentual': round(percentual, 1)
    }


def calcular_carga_horaria_semanal(usuario_id=None):
    """
    Calcula a carga horária total semanal de estudos.
    
    Returns:
        dict com: {'total_minutos': int, 'total_horas': float, 'por_dia': dict}
    """
    cronograma = buscar_cronograma_usuario(usuario_id)
    
    total_minutos = 0
    por_dia = {i: 0 for i in range(7)}
    
    for item in cronograma:
        dia = int(item[3]) if item[3] is not None else 0
        duracao = item[5] if item[5] is not None else 0
        total_minutos += duracao
        por_dia[dia] += duracao
    
    total_horas = round(total_minutos / 60, 1)
    
    return {
        'total_minutos': total_minutos,
        'total_horas': total_horas,
        'por_dia': {DIAS_SEMANA[i]: por_dia[i] for i in range(7)}
    }


def adicionar_compromisso(nome, dia_semana, start_time, duration=60, color='#FF9800', usuario_id=None):
    """
    Adiciona um compromisso extra ao cronograma.
    
    Args:
        nome: Nome do compromisso
        dia_semana: 0-6
        start_time: Horário em formato 'HH:MM'
        duration: Duração em minutos
        color: Cor em hexadecimal
        usuario_id: ID do usuário (opcional)
    
    Returns:
        (sucesso: bool, mensagem: str)
    """
    if not nome or len(nome.strip()) == 0:
        return False, "Nome do compromisso não pode estar vazio"
    
    if not validar_dia_semana(dia_semana):
        return False, "Dia da semana inválido (0-6)"
    
    if not validar_horario(start_time):
        return False, "Horário inválido. Use formato HH:MM"
    
    if not validar_duracao(duration):
        return False, "Duração inválida (1-480 minutos)"
    
    try:
        if salvar_compromisso_extra(nome, dia_semana, start_time, duration, color, usuario_id):
            return True, f"Compromisso '{nome}' adicionado com sucesso!"
        else:
            return False, "Erro ao salvar compromisso"
    except Exception as e:
        return False, f"Erro: {str(e)}"


def remover_compromisso(compromisso_id):
    """
    Remove um compromisso extra.
    
    Returns:
        (sucesso: bool, mensagem: str)
    """
    try:
        remover_compromisso_extra(compromisso_id)
        return True, "Compromisso removido"
    except Exception as e:
        return False, f"Erro ao remover: {str(e)}"


def obter_sugestoes_cronograma(disciplinas_ids, horas_por_dia=2):
    """
    Gera sugestões automáticas de cronograma com base em disciplinas.
    
    Args:
        disciplinas_ids: Lista de IDs de disciplinas
        horas_por_dia: Horas recomendadas por dia
    
    Returns:
        list de dicts com sugestões de cronograma
    """
    if not disciplinas_ids:
        return []
    
    sugestoes = []
    dias_disponiveis = 5  # Segunda a Sexta
    disciplinas_por_dia = (len(disciplinas_ids) / dias_disponiveis)
    
    horario_inicio = 14  # 14:00
    minuto_inicio = 0
    
    for idx, disc_id in enumerate(disciplinas_ids):
        dia = idx % dias_disponiveis  # Distribuir entre seg-sex
        horario = f"{horario_inicio:02d}:{minuto_inicio:02d}"
        
        sugestoes.append({
            'disciplina_id': disc_id,
            'dia_semana': dia,
            'horario': horario,
            'duracao': int(horas_por_dia * 60),
            'cor': list(CORES_PADRAO.values())[idx % len(CORES_PADRAO)]
        })
        
        horario_inicio += 1
        if horario_inicio >= 22:
            horario_inicio = 14
            minuto_inicio = 0
    
    return sugestoes


def validar_conflito_horario(dia_semana, start_time, duration, usuario_id=None, excluir_id=None):
    """
    Verifica se há conflito de horário no cronograma.
    
    Returns:
        (tem_conflito: bool, mensagem: str)
    """
    try:
        cronograma = buscar_cronograma_usuario(usuario_id)
        
        def tempo_para_minutos(hora_str):
            h, m = map(int, hora_str.split(':'))
            return h * 60 + m
        
        novo_inicio = tempo_para_minutos(start_time)
        novo_fim = novo_inicio + duration
        
        for item in cronograma:
            if excluir_id and item[0] == excluir_id:
                continue
            
            if item[3] == dia_semana and item[4]:  # Mesmo dia
                existente_inicio = tempo_para_minutos(item[4])
                existente_fim = existente_inicio + (item[5] or 60)
                
                # Verificar sobreposição
                if not (novo_fim <= existente_inicio or novo_inicio >= existente_fim):
                    return True, f"Conflito de horário! Há outro compromisso de {item[4]}"
        
        return False, ""
    except Exception as e:
        return False, f"Erro ao verificar conflito: {str(e)}"
