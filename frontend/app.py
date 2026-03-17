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
    listar_flashcards_por_topico
)
from backend.services.analytics import buscar_dados_progresso, buscar_alertas_revisao
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
    
    st.sidebar.title("🚀 StudyUp")
    st.sidebar.markdown(f"**Bem-vindo, Estudante!**")
    
    opcao = st.sidebar.selectbox("Navegação:", 
        ["Dashboard", "Cadastrar Disciplina", "Cadastrar Tópico", "Pomodoro", "Flashcards"]
    )
    
    st.sidebar.divider()
    if st.sidebar.button("Sair do Sistema"):
        st.session_state['logado'] = False
        st.rerun()

    # --- PÁGINA: DASHBOARD ---
    if opcao == "Dashboard":
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
    elif opcao == "Cadastrar Disciplina":
        st.header("📚 Gerenciar Disciplinas")
        nova_disc = st.text_input("Nome da Disciplina (Ex: Direito Constitucional):")
        if st.button("Salvar"):
            if nova_disc and adicionar_disciplina(nova_disc):
                st.success("Disciplina cadastrada!")
            else:
                st.error("Erro ao cadastrar ou já existente.")

    # --- PÁGINA: CADASTRAR TÓPICO ---
    elif opcao == "Cadastrar Tópico":
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
    elif opcao == "Pomodoro":
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
    elif opcao == "Flashcards":
        st.header("🗂️ Flashcards")
        aba1, aba2 = st.tabs(["Criar", "Estudar"])
        
        with aba1:
            # Reutiliza lógica de seleção para cadastro de cards
            st.write("Crie novos cards para revisão rápida.")
            # ... (Lógica de cadastro similar ao tópico)
            
        with aba2:
            st.write("Revise seus conceitos salvos.")
            # ... (Lógica de exibição com expander)