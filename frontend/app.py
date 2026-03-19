import sys
import os

# Adiciona a pasta raiz ao sistema de caminhos do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import plotly.express as px
import time
from datetime import datetime, timedelta
import random


def _atualizar_topico_callback(topico_id: int):
    """Callback do Streamlit para atualizar o status de conclusão de um tópico."""
    chave = f"topico_{topico_id}"
    status = st.session_state.get(chave, False)
    atualizar_status_topico(topico_id, status)


# --- DADOS MOTIVACIONAIS ---
FRASES_MOTIVACIONAIS = [
    "A constância vence o talento! 💪",
    "Todo expert um dia foi iniciante. 🚀",
    "O hábito é a chave do sucesso. 🔑",
    "Aprenda um pouco cada dia, eis o segredo. 📚",
    "Disciplina: a ponte entre a intenção e o resultado. 🌉",
    "O conhecimento é poder! ⚡",
    "Pequenos passos levam a grandes conquistas. 👣",
    "Sua dedicação de hoje será sua vantagem amanhã. ⭐",
    "Foco, força e fé! ✨",
    "O estudo é o investimento mais rentável. 💎",
]

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def obter_frase_motivacional():
    """Retorna uma frase motivacional aleatória."""
    return random.choice(FRASES_MOTIVACIONAIS)


def obter_numero_dia_semana():
    """Retorna o dia da semana atual (0=Segunda, 6=Domingo)."""
    return datetime.now().weekday()



from backend.database.connection import (
    listar_disciplinas,
    adicionar_disciplina,
    adicionar_topico,
    listar_topicos_por_disciplina,
    atualizar_status_topico,
    calcular_progresso_disciplina,
    calcular_progresso_geral,
    registrar_desempenho,
    adicionar_flashcard,
    listar_flashcards_por_topico,
    checar_conexao,
    salvar_cronograma,
    buscar_cronograma_usuario,
    obter_disciplinas_por_dia,
    remover_cronograma,
    foi_estudada_hoje,
)
from backend.services.analytics import (
    buscar_dados_progresso,
    buscar_alertas_revisao,
    obter_questoes_resolvidas_hoje,
)
from backend.services.pomodoro import formatar_tempo

# --- IMPORTAÇÕES DO FRONTEND ---
from frontend.components.auth_ui import desenhar_tela_login

# 1. Configuracão inicial da página
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
    if st.sidebar.button("📅 Cronograma", key="nav_cronograma"):
        st.session_state['pagina'] = "Cronograma"

    st.sidebar.markdown("#### 📚 Gestão")
    if st.sidebar.button("📘 Disciplinas", key="nav_disciplinas"):
        st.session_state['pagina'] = "Cadastrar Disciplina"
    if st.sidebar.button("📝 Tópicos", key="nav_topicos"):
        st.session_state['pagina'] = "Cadastrar Tópico"
    if st.sidebar.button("📖 Meus Estudos", key="nav_meus_estudos"):
        st.session_state['pagina'] = "Meus Estudos"

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

        progresso_total = calcular_progresso_geral()
        st.metric("Progresso total do edital", f"{progresso_total}%")

        df_progresso = buscar_dados_progresso()
        
        if df_progresso.empty:
            st.warning("Ainda não há dados. Registre uma sessão de estudos!")
        else:
            # Agregar dados por disciplina e calcular percentual médio
            df_agg = df_progresso.groupby('Disciplina')['percentual'].mean().reset_index()
            fig = px.bar(df_agg, x='Disciplina', y='percentual', 
                         color='percentual', color_continuous_scale='RdYlGn', range_y=[0, 100],
                         labels={'percentual': 'Progresso (%)'})
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🔔 Revisões Pendentes")
        df_revisao = buscar_alertas_revisao()
        if not df_revisao.empty:
            # Exibir apenas as colunas necessárias
            if 'Disciplina' in df_revisao.columns and 'Topico' in df_revisao.columns:
                df_revisao_filtrado = df_revisao[['Disciplina', 'Topico']].drop_duplicates()
                st.dataframe(df_revisao_filtrado, use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_revisao, use_container_width=True)
        else:
            st.success("Tudo em dia!")

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

    # --- PÁGINA: MEUS ESTUDOS ---
    elif st.session_state['pagina'] == "Meus Estudos":
        st.header("📚 Meus Estudos")
        disciplinas = listar_disciplinas()
        if not disciplinas:
            st.warning("Cadastre uma disciplina primeiro!")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            escolha = st.selectbox("Selecione a Disciplina:", list(dict_disc.keys()))
            disciplina_id = dict_disc[escolha]

            progresso = calcular_progresso_disciplina(disciplina_id)
            st.markdown(f"**Progresso em {escolha}:** {progresso}%")
            st.progress(progresso / 100)

            topicos = listar_topicos_por_disciplina(disciplina_id)
            if not topicos:
                st.info("Cadastre tópicos para esta disciplina para acompanhar o progresso.")
            else:
                for tp in topicos:
                    tp_id, _, tp_nome, tp_concluido = tp
                    label = f"✅ {tp_nome}" if tp_concluido else tp_nome
                    st.checkbox(label,
                                value=bool(tp_concluido),
                                key=f"topico_{tp_id}",
                                on_change=_atualizar_topico_callback,
                                args=(tp_id,))

    # --- PÁGINA: POMODORO ---
    elif st.session_state['pagina'] == "Pomodoro":
        st.header("⏳ Timer Pomodoro")
        disciplinas = listar_disciplinas()
        if not disciplinas:
            st.info("Configure disciplinas e tópicos primeiro.")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            
            # Pré-selecionar disciplina se vindo do Cronograma
            disciplina_padrao = st.session_state.get('disciplina_selecionada', None)
            indice_padrao = 0
            if disciplina_padrao and disciplina_padrao in dict_disc:
                indice_padrao = list(dict_disc.keys()).index(disciplina_padrao)
            
            esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()), index=indice_padrao)
            
            # Limpar a seleção após usar
            if disciplina_padrao:
                del st.session_state['disciplina_selecionada']
            
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

    # --- PÁGINA: CRONOGRAMA ---
    elif st.session_state['pagina'] == "Cronograma":
        # --- FRASE MOTIVACIONAL ---
        frase = obter_frase_motivacional()
        st.markdown(f"<div style='text-align: center; font-size: 1.3rem; color: #FF6B6B; font-weight: bold; margin-bottom: 20px;'>{frase}</div>", unsafe_allow_html=True)
        
        # --- DATA E PROGRESSO ---
        hoje = datetime.now()
        data_formatada = hoje.strftime("%A, %d de %B de %Y").replace("Monday", "Segunda").replace("Tuesday", "Terça").replace("Wednesday", "Quarta").replace("Thursday", "Quinta").replace("Friday", "Sexta").replace("Saturday", "Sábado").replace("Sunday", "Domingo")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### 📅 Hoje: {data_formatada}")
        
        with col2, col3:
            pass
        
        st.divider()
        
        # --- VERIFICAR SE HÁ CRONOGRAMA ---
        cronograma = buscar_cronograma_usuario()
        
        if not cronograma:
            st.markdown("<div style='text-align: center; padding: 40px;'>", unsafe_allow_html=True)
            st.markdown("### 📭 Seu Cronograma está Vazio!")
            st.markdown("Crie um cronograma personalizado para organizar seus estudos.", unsafe_allow_html=True)
            
            if st.button("⚙️ Configurar meu Primeiro Cronograma", key="setup_cronograma"):
                st.session_state['pagina'] = "Configurar Cronograma"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # --- GRID SEMANAL ---
            st.subheader("📆 Sua Semana de Estudos")
            
            # Agrupar disciplinas por dia
            cronograma_por_dia = {i: [] for i in range(7)}
            for item in cronograma:
                # item: (id, disciplina_id, disciplina_nome, dia_semana)
                dia = item[3]
                cronograma_por_dia[dia].append(item)
            
            # Calcular progresso diário
            dia_semana_atual = obter_numero_dia_semana()
            disciplinas_hoje = cronograma_por_dia[dia_semana_atual]
            estudadas_hoje = sum(1 for disc_id, _, _, _ in [(item[1], item[2], item[3], item[0]) for item in disciplinas_hoje] if foi_estudada_hoje(disc_id))
            total_hoje = len(disciplinas_hoje)
            
            if total_hoje > 0:
                progresso_hoje = (estudadas_hoje / total_hoje) * 100
                st.metric("📊 Progresso de Hoje", f"{estudadas_hoje}/{total_hoje}", f"{int(progresso_hoje)}%")
                st.progress(progresso_hoje / 100)
            else:
                st.info("Nenhuma disciplina agendada para hoje.")
            
            st.divider()
            
            # Grid de 7 colunas
            colunas = st.columns(7)
            
            for dia_idx, coluna in enumerate(colunas):
                with coluna:
                    dia_nome = DIAS_SEMANA[dia_idx]
                    eh_hoje = dia_idx == dia_semana_atual
                    
                    # Destaque visual para hoje
                    if eh_hoje:
                        st.markdown(f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; text-align: center;'>", unsafe_allow_html=True)
                        st.markdown(f"<h4 style='color: white; margin: 0;'>📍 {dia_nome}</h4>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h4 style='text-align: center; margin-top: 0;'>{dia_nome}</h4>", unsafe_allow_html=True)
                    
                    disciplinas_dia = cronograma_por_dia[dia_idx]
                    
                    if not disciplinas_dia:
                        st.markdown(f"<p style='text-align: center; color: #999;'>-</p>", unsafe_allow_html=True)
                    else:
                        for item in disciplinas_dia:
                            cronograma_id, disc_id, disc_nome, _ = item
                            estudada = foi_estudada_hoje(disc_id) if eh_hoje else False
                            
                            # Card com cor baseada no status
                            if estudada:
                                cor_bg = "#D4EDDA"
                                cor_borda = "#28A745"
                                simbolo = "✅"
                            elif eh_hoje:
                                cor_bg = "#FFF3CD"
                                cor_borda = "#FF6B6B"
                                simbolo = "⏳"
                            else:
                                cor_bg = "#E9ECEF"
                                cor_borda = "#6C757D"
                                simbolo = "📌"
                            
                            st.markdown(f"""
                            <div style='background: {cor_bg}; border: 2px solid {cor_borda}; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 8px;'>
                                <p style='margin: 0; font-size: 0.75rem; font-weight: bold; color: #333;'>{simbolo} {disc_nome}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Botão de ação rápida para hoje
                            if eh_hoje and not estudada:
                                if st.button(f"▶️ Iniciar", key=f"iniciar_{cronograma_id}"):
                                    st.session_state['pagina'] = "Pomodoro"
                                    st.session_state['disciplina_selecionada'] = disc_nome
                                    st.rerun()
            
            st.divider()
            
            # --- SEÇÃO DE CONFIGURAÇÃO DO CRONOGRAMA ---
            st.subheader("⚙️ Gerenciar Cronograma")
            
            with st.expander("🔧 Adicionar ou Remover Disciplinas"):
                tab1, tab2 = st.tabs(["Adicionar", "Remover"])
                
                with tab1:
                    st.write("Escolha uma disciplina e o dia da semana:")
                    disciplinas = listar_disciplinas()
                    if not disciplinas:
                        st.warning("Cadastre uma disciplina primeiro!")
                    else:
                        dict_disc = {d[1]: d[0] for d in disciplinas}
                        esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()), key="crono_disc")
                        esc_dia = st.selectbox("Dia da Semana:", DIAS_SEMANA, key="crono_dia")
                        
                        if st.button("✅ Adicionar ao Cronograma"):
                            dia_idx = DIAS_SEMANA.index(esc_dia)
                            if salvar_cronograma(dict_disc[esc_disc], dia_idx):
                                st.success(f"✅ {esc_disc} adicionada para {esc_dia}!")
                                st.rerun()
                            else:
                                st.error("Esta disciplina já está agendada para este dia.")
                
                with tab2:
                    st.write("Remova disciplinas do seu cronograma:")
                    if not cronograma:
                        st.info("Nenhuma disciplina no cronograma.")
                    else:
                        # Mostrar cronograma para remover
                        for item in cronograma:
                            cron_id, disc_id, disc_nome, dia_sem = item
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"📍 **{disc_nome}** - {DIAS_SEMANA[dia_sem]}")
                            with col2:
                                if st.button("🗑️", key=f"remove_{cron_id}"):
                                    remover_cronograma(cron_id)
                                    st.success("Disciplina removida!")
                                    st.rerun()
