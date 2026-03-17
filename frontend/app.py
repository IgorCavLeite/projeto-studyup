import sys
import os

# Adiciona a pasta raiz ao sistema de caminhos do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

import streamlit as st
import plotly.express as px
import time

# --- IMPORTAÇÕES DO BACKEND ---
from backend.database.connection import (
    listar_disciplinas,
    adicionar_disciplina,
    adicionar_topico,
    listar_topicos_por_disciplina,
    registrar_desempenho,
    adicionar_flashcard,
    listar_flashcards_por_topico,
    checar_conexao,
)
from backend.services.analytics import (
    buscar_dados_progresso,
    buscar_alertas_revisao,
    obter_questoes_resolvidas_hoje,
)
from backend.services.pomodoro import formatar_tempo

# --- IMPORTAÇÕES DO FRONTEND ---
from frontend.components.auth_ui import desenhar_tela_login

# 1. Configuração inicial da página
st.set_page_config(page_title="StudyUp - Pro", layout="wide", page_icon="🚀")

# 2. Carregar CSS customizado (Mãozinha no cursor)
try:
    with open("frontend/assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback caso o arquivo não seja encontrado
    st.markdown("""<style>div[data-baseweb="select"], button { cursor: pointer !important; }</style>""", unsafe_allow_html=True)

# 3. Gerenciamento de Estado de Login
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# --- FLUXO DE TELAS ---

if not st.session_state['logado']:
    # Chama a tela de login/cadastro que isolamos
    desenhar_tela_login()
else:
    # --- ÁREA LOGADA DO SISTEMA ---
    
    # --- SIDEBAR (NAVEGAÇÃO) ---
    if 'pagina' not in st.session_state:
        st.session_state['pagina'] = "Dashboard"

    if 'usuario' not in st.session_state:
        st.session_state['usuario'] = "Estudante"

    st.sidebar.markdown("### 👤 Perfil")
    st.sidebar.markdown(
        f"<div style='display:flex; align-items:center; gap:8px;'>"
        f"<span style='font-size:1.6rem;'>🧑‍🎓</span>"
        f"<span style='font-weight:600;'>{st.session_state['usuario']}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # Menu Agrupado
    st.sidebar.markdown("#### 📊 Geral")
    if st.sidebar.button("🏠 Dashboard", key="nav_dashboard"):
        st.session_state['pagina'] = "Dashboard"

    st.sidebar.markdown("#### 📚 Gestão")
    if st.sidebar.button("📘 Disciplinas", key="nav_disciplinas"):
        st.session_state['pagina'] = "Cadastrar Disciplina"
    if st.sidebar.button("📝 Tópicos", key="nav_topicos"):
        st.session_state['pagina'] = "Cadastrar Tópico"

    st.sidebar.markdown("#### ⏱️ Estudo Ativo")
    if st.sidebar.button("⏳ Pomodoro", key="nav_pomodoro"):
        st.session_state['pagina'] = "Pomodoro"
    if st.sidebar.button("🗂️ Flashcards", key="nav_flashcards"):
        st.session_state['pagina'] = "Flashcards"

    st.sidebar.markdown("#### ⚙️ Configurações")
    if st.sidebar.button("👤 Perfil do Usuário", key="nav_perfil"):
        st.session_state['pagina'] = "Perfil"
    if st.sidebar.button("⚙️ Opções do Sistema", key="nav_sistema"):
        st.session_state['pagina'] = "Configurações"

    # Mini estatística
    try:
        questoes_hoje = obter_questoes_resolvidas_hoje()
    except Exception:
        questoes_hoje = 0
    st.sidebar.metric("🧠 Questões hoje", questoes_hoje)

    # Status do banco
    db_ok = checar_conexao()
    status_emoji = "🟢" if db_ok else "🔴"
    st.sidebar.markdown(f"**Banco:** {status_emoji} {'Conectado' if db_ok else 'Offline'}")

    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair", key="nav_logout"):
        st.session_state['logado'] = False
        st.rerun()

    st.sidebar.markdown("### v1.0.0")

    # --- PÁGINA: DASHBOARD ---
    if st.session_state['pagina'] == "Dashboard":
        st.header("📊 Painel de Desempenho")
        df_progresso = buscar_dados_progresso()
        
        if df_progresso.empty:
            st.warning("Ainda não há dados. Registre uma sessão de estudos!")
        else:
            fig = px.bar(df_progresso, x='Disciplina', y='percentual', 
                         color='percentual', color_continuous_scale='RdYlGn', range_y=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🔔 Revisões Pendentes")
        df_revisao = buscar_alertas_revisao()
        st.dataframe(df_revisao, use_container_width=True) if not df_revisao.empty else st.success("Tudo em dia!")

    # --- PÁGINA: CADASTRAR DISCIPLINA ---
    elif st.session_state['pagina'] == "Cadastrar Disciplina":
        st.header("📚 Gerenciar Disciplinas")
        nova_disc = st.text_input("Nome da Disciplina (Ex: Direito Constitucional):")
        if st.button("Salvar"):
            if nova_disc and adicionar_disciplina(nova_disc):
                st.success("Disciplina cadastrada!")
            else:
                st.error("Erro ao cadastrar ou já existente.")

    # --- PÁGINA: CADASTRAR TÓPICO ---
    elif st.session_state['pagina'] == "Cadastrar Tópico":
        st.header("📝 Cadastrar Conteúdo")
        disciplinas = listar_disciplinas()
        if not disciplinas:
            st.warning("Cadastre uma disciplina primeiro!")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            escolha = st.selectbox("Selecione a Disciplina:", list(dict_disc.keys()))
            nome_topico = st.text_input("Nome do Tópico (Ex: Artigo 5º):")
            if st.button("Salvar Tópico"):
                adicionar_topico(dict_disc[escolha], nome_topico)
                st.success("Tópico adicionado!")

    # --- PÁGINA: POMODORO ---
    elif st.session_state['pagina'] == "Pomodoro":
        st.header("⏳ Timer Pomodoro")
        disciplinas = listar_disciplinas()
        if not disciplinas:
            st.info("Configure disciplinas e tópicos primeiro.")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()))
            topicos = listar_topicos_por_disciplina(dict_disc[esc_disc])
            
            if topicos:
                dict_topicos = {t[2]: t[0] for t in topicos}
                esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()))
                
                if st.button("Iniciar Foco (25min)"):
                    tempo = 25 * 60
                    prog = st.progress(0)
                    txt = st.empty()
                    for s in range(tempo, -1, -1):
                        txt.subheader(f"Restante: {formatar_tempo(s)}")
                        prog.progress((tempo - s) / tempo)
                        time.sleep(1)
                    st.success("Fim do ciclo! Registre seu desempenho abaixo.")

                with st.form("desempenho"):
                    q = st.number_input("Questões Feitas", min_value=0)
                    a = st.number_input("Acertos", min_value=0)
                    if st.form_submit_button("Registrar"):
                        registrar_desempenho(dict_topicos[esc_topico], q, a)
                        st.success("Dados salvos!")

    # --- PÁGINA: FLASHCARDS ---
    elif st.session_state['pagina'] == "Flashcards":
        st.header("🗂️ Flashcards")
        aba1, aba2 = st.tabs(["Criar", "Estudar"])
        
        with aba1:
            st.write("Crie novos cards para revisão rápida.")
            disciplinas = listar_disciplinas()
            if not disciplinas:
                st.warning("Cadastre uma disciplina primeiro para poder criar flashcards.")
            else:
                dict_disc = {d[1]: d[0] for d in disciplinas}
                esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()))
                topicos = listar_topicos_por_disciplina(dict_disc[esc_disc])

                if not topicos:
                    st.info("Cadastre um tópico para esta disciplina antes de criar flashcards.")
                else:
                    dict_topicos = {t[2]: t[0] for t in topicos}
                    esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()))

                    pergunta = st.text_area("Pergunta:")
                    resposta = st.text_area("Resposta:")
                    if st.button("Salvar Flashcard"):
                        if pergunta.strip() and resposta.strip():
                            adicionar_flashcard(dict_topicos[esc_topico], pergunta.strip(), resposta.strip())
                            st.success("Flashcard salvo com sucesso!")
                        else:
                            st.error("Pergunta e resposta não podem ficar vazias.")

        with aba2:
            st.write("Revise seus conceitos salvos.")
            disciplinas = listar_disciplinas()
            if not disciplinas:
                st.warning("Cadastre uma disciplina primeiro para acessar seus flashcards.")
            else:
                dict_disc = {d[1]: d[0] for d in disciplinas}
                esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()), key="flash_disc")
                topicos = listar_topicos_por_disciplina(dict_disc[esc_disc])

                if not topicos:
                    st.info("Cadastre um tópico para esta disciplina antes de adicionar flashcards.")
                else:
                    dict_topicos = {t[2]: t[0] for t in topicos}
                    esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()), key="flash_top")
                    flashcards = listar_flashcards_por_topico(dict_topicos[esc_topico])

                    if not flashcards:
                        st.info("Nenhum flashcard criado ainda. Vá para a aba 'Criar' para adicionar.")
                    else:
                        for fc in flashcards:
                            # fc: (id, topico_id, pergunta, resposta)
                            with st.expander(fc[2]):
                                st.write(f"**Resposta:** {fc[3]}")
