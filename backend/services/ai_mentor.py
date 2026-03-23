import google.generativeai as genai
import os
from backend.services.analytics import buscar_dados_progresso

# Configurar a API do Gemini
genai.configure(api_key="AIzaSyBIzfGK-l1NyMdE-c1HKxv3OSPE2RUDO40")

# Modelo a ser usado
model = genai.GenerativeModel('models/gemini-flash-lite-latest')


def obter_dados_desempenho():
    """Obtém os dados de desempenho do usuário."""
    df = buscar_dados_progresso()
    if df.empty:
        return "Nenhum dado de desempenho disponível."

    # Agregar por disciplina
    desempenho = df.groupby('Disciplina')['percentual'].mean().to_dict()
    return desempenho


def sugerir_topico_estudo():
    """Sugere um tópico para estudo baseado no menor desempenho."""
    desempenho = obter_dados_desempenho()
    if isinstance(desempenho, str):
        return "Comece estudando qualquer matéria disponível."

    # Encontrar a matéria com menor desempenho
    materia_menor = min(desempenho, key=desempenho.get)
    return f"Priorize estudar {materia_menor} (desempenho atual: {desempenho[materia_menor]:.1f}%)."


def criar_flashcards(texto):
    """Cria 3 flashcards a partir de um texto colado."""
    prompt = f"""
    Com base no texto fornecido, crie exatamente 3 flashcards no formato 'Pergunta | Resposta'.
    Cada flashcard deve ser uma linha separada.
    Mantenha conciso e relevante.

    Texto: {texto}

    Responda apenas com as 3 flashcards, nada mais.
    """

    response = model.generate_content(prompt)
    flashcards = response.text.strip().split('\n')
    return flashcards[:3]  # Garantir apenas 3


def mentor_ia_resposta(mensagem_usuario):
    """Gera resposta do Mentor de Estudos Inteligente."""
    desempenho = obter_dados_desempenho()

    if isinstance(desempenho, str):
        dados_str = desempenho
    else:
        dados_str = ", ".join(
            [f"{mat}: {pct:.1f}%" for mat, pct in desempenho.items()])

    prompt = f"""
    Atue como um Mentor de Estudos Inteligente para o projeto StudyUp.
    Dados de desempenho do usuário: {dados_str}
    
    Seu objetivo é:
    - Sugerir qual tópico estudar hoje priorizando as matérias com menor desempenho.
    - Se o usuário colar um texto, criar 3 flashcards no formato 'Pergunta | Resposta'.
    - Manter um tom motivador e conciso.
    - Responda sempre em Markdown para facilitar a leitura no Streamlit.
    
    Mensagem do usuário: {mensagem_usuario}
    """

    response = model.generate_content(prompt)
    return response.text.strip()
