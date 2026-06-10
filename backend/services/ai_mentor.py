import os
from backend.services.analytics import buscar_dados_progresso

try:
    import google.generativeai as genai
    _GENAI_AVAILABLE = True
except ImportError:
    genai = None
    _GENAI_AVAILABLE = False

_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GENAI_API_KEY')
if _GENAI_AVAILABLE and _API_KEY:
    genai.configure(api_key=_API_KEY)
    model = genai.GenerativeModel('models/gemini-flash-lite-latest')
else:
    model = None


def _ia_disponivel():
    return _GENAI_AVAILABLE and model is not None


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
    if not _ia_disponivel():
        return []

    prompt = f"""
    Com base no texto fornecido, crie exatamente 3 flashcards no formato 'Pergunta | Resposta'.
    Cada flashcard deve ser uma linha separada.
    Mantenha conciso e relevante.

    Texto: {texto}

    Responda apenas com as 3 flashcards, nada mais.
    """

    try:
        response = model.generate_content(prompt)
        flashcards = response.text.strip().split('\n')
        return flashcards[:3]  # Garantir apenas 3
    except Exception:
        return []


def mentor_ia_resposta(mensagem_usuario):
    """Gera resposta do Mentor de Estudos Inteligente."""
    import json
    desempenho = obter_dados_desempenho()

    if isinstance(desempenho, str):
        dados_str = desempenho
    else:
        dados_str = ", ".join(
            [f"{mat}: {pct:.1f}%" for mat, pct in desempenho.items()])

    prompt = f"""
    Você é o Mentor de Estudos Inteligente do aplicativo StudyUp.
    Dados de desempenho do usuário: {dados_str}
    
    Sua resposta DEVE ser um objeto JSON contendo exatamente dois campos:
    1. "resposta": Uma mensagem de texto em Markdown. Nela, você deve:
       - Responder à mensagem do usuário.
       - Sugerir qual disciplina estudar hoje com base nos dados de desempenho fornecidos (priorizando menor percentual).
       - Se for o caso de o usuário colar um texto para estudar ou pedir flashcards explicitamente, explique na resposta que sugeriu alguns flashcards.
       - Manter um tom motivador e conciso.
    2. "flashcards": Um array de objetos JSON contendo sugestões de flashcards, ou um array vazio [] se o usuário não pediu e não há necessidade de criá-los. 
       Se o usuário colou um texto ou pediu flashcards explicitamente (ou você julgar altamente relevante para o tema da conversa), gere exatamente 3 flashcards relevantes.
       Cada flashcard no array deve ter a estrutura:
         {{"pergunta": "Pergunta concisa sobre o conteúdo", "resposta": "Resposta direta e objetiva"}}
    
    Exemplo de formato de saída esperado:
    {{
      "resposta": "Olá! Com base no seu desempenho, recomendo focar em... Aqui estão alguns flashcards para praticar.",
      "flashcards": [
        {{"pergunta": "O que é polimorfismo?", "resposta": "Capacidade de um objeto assumir diferentes formas."}},
        {{"pergunta": "Exemplo de polimorfismo?", "resposta": "Sobrescrita de métodos em subclasses."}},
        {{"pergunta": "Benefício principal?", "resposta": "Flexibilidade e reutilização de código."}}
      ]
    }}
    
    Mensagem do usuário: {mensagem_usuario}
    
    Responda APENAS com o objeto JSON estruturado.
    """

    if not _ia_disponivel():
        mock_flashcards = []
        msg_lower = mensagem_usuario.lower()
        if "flashcard" in msg_lower or "card" in msg_lower or len(mensagem_usuario) > 20:
            mock_flashcards = [
                {"pergunta": "Pergunta de Exemplo 1 (Demonstração)", "resposta": f"Resposta baseada em: {mensagem_usuario[:60]}..."},
                {"pergunta": "Pergunta de Exemplo 2 (Demonstração)", "resposta": "O banco de dados SQLite armazena tudo em um arquivo local único."},
                {"pergunta": "Pergunta de Exemplo 3 (Demonstração)", "resposta": "O Streamlit é um framework Python para web apps de dados."}
            ]
            msg_add = "\n\n*(Nota: O Mentor IA não está configurado. Exibindo flashcards de exemplo para demonstração)*"
        else:
            msg_add = ""

        if isinstance(desempenho, str):
            msg = "Mentor IA não está configurado. Cadastre seus estudos para usar o app normalmente." + msg_add
        else:
            materia_menor = min(desempenho, key=desempenho.get)
            msg = (f"Mentor IA não está configurado. Enquanto isso, priorize estudar {materia_menor} "
                   f"(desempenho atual: {desempenho[materia_menor]:.1f}%)." + msg_add)
        return json.dumps({
            "resposta": msg,
            "flashcards": mock_flashcards
        })

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return response.text.strip()
    except Exception:
        mock_flashcards = []
        msg_lower = mensagem_usuario.lower()
        if "flashcard" in msg_lower or "card" in msg_lower or len(mensagem_usuario) > 20:
            mock_flashcards = [
                {"pergunta": "Pergunta de Exemplo 1 (Demonstração)", "resposta": f"Resposta baseada em: {mensagem_usuario[:60]}..."},
                {"pergunta": "Pergunta de Exemplo 2 (Demonstração)", "resposta": "O banco de dados SQLite armazena tudo em um arquivo local único."},
                {"pergunta": "Pergunta de Exemplo 3 (Demonstração)", "resposta": "O Streamlit é um framework Python para web apps de dados."}
            ]
            msg_add = "\n\n*(Nota: O Mentor IA falhou. Exibindo flashcards de exemplo para demonstração)*"
        else:
            msg_add = ""

        if isinstance(desempenho, str):
            msg = "Mentor IA não está disponível no momento. Cadastre seus estudos para usar o app normalmente." + msg_add
        else:
            materia_menor = min(desempenho, key=desempenho.get)
            msg = (f"Mentor IA não respondeu. Enquanto isso, priorize estudar {materia_menor} "
                   f"(desempenho atual: {desempenho[materia_menor]:.1f}%)." + msg_add)
        return json.dumps({
            "resposta": msg,
            "flashcards": mock_flashcards
        })
