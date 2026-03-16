import plotly.express as px
from logic.analytics import buscar_dados_progresso, buscar_alertas_revisao
import streamlit as st
import time
from database.connection import (
    adicionar_disciplina, 
    listar_disciplinas, 
    adicionar_topico, 
    listar_topicos_por_disciplina,
    registrar_desempenho,
    adicionar_flashcard,       
    listar_flashcards_por_topico
)
from logic.pomodoro import formatar_tempo

import streamlit as st
from login import desenhar_tela_login  # 1. Importa o seu arquivo

# 2. Verifica se o usuário já logou
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

# 3. Se não logou, mostra sua tela e para a execução do resto
if not st.session_state['logado']:
    desenhar_tela_login()
    st.stop() 

# --- A partir daqui começa o código original do projeto ---
st.title("🚀 StudyUp - Gerenciador de Estudos")


st.set_page_config(page_title="StudyUp", layout="wide")

# CSS para forçar o cursor de mãozinha
st.markdown("""
    <style>
    div[data-baseweb="select"], button, .stSelectbox { cursor: pointer !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 StudyUp - Gerenciador de Estudos")

# --- MENU LATERAL ---
st.sidebar.header("Menu de Navegação")
opcao = st.sidebar.selectbox("Ir para:", ["Dashboard", "Cadastrar Disciplina", "Cadastrar Tópico", "Pomodoro", "Flashcards"])

# --- PÁGINA: DASHBOARD ---
if opcao == "Dashboard":
    st.header("📊 Painel de Desempenho")
    
    # 1. Gráfico de Desempenho
    df_progresso = buscar_dados_progresso()
    
    if df_progresso.empty:
        st.warning("Ainda não há dados suficientes. Realize uma sessão de Pomodoro e registre seus acertos!")
    else:
        st.subheader("Percentual Médio de Acertos por Disciplina")
        # Criando o gráfico com Plotly
        fig = px.bar(
            df_progresso, 
            x='Disciplina', 
            y='percentual',
            color='percentual',
            color_continuous_scale='RdYlGn', # Vermelho para baixo, Verde para alto
            range_y=[0, 100],
            text_auto='.1f'
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 2. Alertas de Revisão
    st.subheader("🔔 Tópicos para Revisar Hoje")
    df_revisao = buscar_alertas_revisao()
    
    if df_revisao.empty:
        st.success("Tudo em dia! Nenhuma revisão pendente para hoje.")
    else:
        st.dataframe(df_revisao, use_container_width=True)

# --- PÁGINA: CADASTRAR DISCIPLINA ---
elif opcao == "Cadastrar Disciplina":
    st.header("📚 Gerenciar Disciplinas")
    nova_disc = st.text_input("Nome da Disciplina:")
    if st.button("Salvar Disciplina"):
        if nova_disc:
            if adicionar_disciplina(nova_disc):
                st.success("Disciplina adicionada!")
            else:
                st.error("Erro ou já cadastrada.")
    
    st.divider()
    for d in listar_disciplinas():
        st.write(f"- {d[1]}")

# --- PÁGINA: CADASTRAR TÓPICO ---
elif opcao == "Cadastrar Tópico":
    st.header("📝 Cadastrar Conteúdo")
    disciplinas = listar_disciplinas()
    if not disciplinas:
        st.warning("Cadastre uma disciplina primeiro!")
    else:
        dict_disc = {d[1]: d[0] for d in disciplinas}
        escolha = st.selectbox("Selecione a Disciplina:", list(dict_disc.keys()))
        nome_topico = st.text_input("Nome do Tópico:")
        if st.button("Salvar Tópico"):
            if nome_topico:
                adicionar_topico(dict_disc[escolha], nome_topico)
                st.success(f"Tópico adicionado!")

# --- PÁGINA: POMODORO ---
elif opcao == "Pomodoro":
    st.header("⏳ Timer Pomodoro")
    disciplinas = listar_disciplinas()
    if not disciplinas:
        st.info("Cadastre disciplina e tópico antes.")
    else:
        dict_disc = {d[1]: d[0] for d in disciplinas}
        esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()))
        topicos = listar_topicos_por_disciplina(dict_disc[esc_disc])
        
        if not topicos:
            st.warning("Cadastre tópicos para esta disciplina.")
        else:
            dict_topicos = {t[2]: t[0] for t in topicos}
            esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()))
            
            if st.button("Iniciar 25min"):
                tempo = 25 * 60
                prog = st.progress(0)
                txt = st.empty()
                for s in range(tempo, -1, -1):
                    txt.subheader(f"Restante: {formatar_tempo(s)}")
                    prog.progress((tempo - s) / tempo)
                    time.sleep(1)
                st.success("Sessão Finalizada!")
                st.balloons()

            st.divider()
            st.subheader("📊 Registrar Desempenho")
            with st.form("form_desempenho"):
                col1, col2 = st.columns(2)
                q = col1.number_input("Questões", min_value=0, step=1)
                a = col2.number_input("Acertos", min_value=0, step=1)
                if st.form_submit_button("Salvar"):
                    if q > 0:
                        registrar_desempenho(dict_topicos[esc_topico], q, a)
                        st.success("Salvo com sucesso!")

elif opcao == "Flashcards":
    st.header("🗂️ Flashcards - Revisão Rápida")
    
    aba_cadastrar, aba_estudar = st.tabs(["🆕 Cadastrar Cards", "🧠 Estudar"])

    with aba_cadastrar:
        disciplinas = listar_disciplinas()
        if not disciplinas:
            st.warning("Cadastre uma disciplina primeiro.")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            esc_disc = st.selectbox("Disciplina do Card:", list(dict_disc.keys()), key="fc_disc")
            topicos = listar_topicos_por_disciplina(dict_disc[esc_disc])
            
            if not topicos:
                st.warning("Cadastre um tópico para esta disciplina.")
            else:
                dict_topicos = {t[2]: t[0] for t in topicos}
                esc_topico = st.selectbox("Tópico do Card:", list(dict_topicos.keys()), key="fc_top")
                
                pergunta = st.text_area("Pergunta (Frente):")
                resposta = st.text_area("Resposta (Verso):")
                
                if st.button("Salvar Flashcard"):
                    if pergunta and resposta:
                        adicionar_flashcard(dict_topicos[esc_topico], pergunta, resposta)
                        st.success("Card salvo com sucesso!")

    with aba_estudar:
        # Lógica simples de exibição
        st.subheader("Selecione o que revisar:")
        # Repetir a seleção de disciplina/tópico aqui para filtrar
        # ... (pode usar os mesmos seletores acima com chaves/keys diferentes)
        
        # Exemplo de exibição do card
        cards = listar_flashcards_por_topico(dict_topicos[esc_topico]) if topicos else []
        
        for card in cards:
            with st.expander(f"❓ {card[2]}"):
                st.write(f"💡 **Resposta:** {card[3]}")