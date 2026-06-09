import sys
import os

# Adiciona a pasta raiz ao sistema de caminhos do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.components.auth_ui import desenhar_tela_login
from frontend.components.cronograma_ui import (
    exibir_cronograma_semanal,
    form_adicionar_disciplina_cronograma,
    form_gerenciar_disciplinas,
    form_adicionar_compromisso,
    form_gerenciar_compromissos,
    exibir_resumo_semanal,
    sugerir_cronograma_automatico,
)
from frontend.components.pomodoro_ui import render_pomodoro_page
from backend.services.ai_mentor import mentor_ia_resposta
from backend.services.pomodoro import formatar_tempo
from backend.services.analytics import (
    buscar_dados_progresso,
    buscar_alertas_revisao,
    obter_questoes_resolvidas_hoje,
)
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
    salvar_compromisso_extra,
    buscar_compromissos_extras_usuario,
    remover_compromisso_extra,
    foi_estudada_hoje,
)
import random
from datetime import datetime, timedelta
import time
import plotly.express as px
import streamlit as st


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

DIAS_SEMANA = ["Segunda", "Terça", "Quarta",
               "Quinta", "Sexta", "Sábado", "Domingo"]
DIAS_MAP = {dia: idx for idx, dia in enumerate(DIAS_SEMANA)}


def obter_frase_motivacional():
    """Retorna uma frase motivacional aleatória."""
    return random.choice(FRASES_MOTIVACIONAIS)


def obter_numero_dia_semana():
    """Retorna o dia da semana atual (0=Segunda, 6=Domingo)."""
    return datetime.now().weekday()


# --- IMPORTAÇÕES DO FRONTEND ---
# 1. Configuracão inicial da página
st.set_page_config(page_title="StudyUp - Pro", layout="wide", page_icon="🚀")

# 2. Carregar CSS customizado (Mãozinha no cursor)
try:
    with open("frontend/assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback caso o arquivo não seja encontrado
    st.markdown(
        """<style>div[data-baseweb="select"], button { cursor: pointer !important; }</style>""", unsafe_allow_html=True)

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
        st.session_state['pagina'] = "Cronograma"

    if 'usuario' not in st.session_state:
        st.session_state['usuario'] = "Estudante"
    if 'usuario_id' not in st.session_state:
        st.session_state['usuario_id'] = None

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
    if st.sidebar.button("🤖 Mentor IA", key="nav_mentor_ia"):
        st.session_state['pagina'] = "Mentor IA"

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
    st.sidebar.markdown(
        f"**Banco:** {status_emoji} {'Conectado' if db_ok else 'Offline'}")

    st.sidebar.divider()
    if st.sidebar.button("🚪 Sair", key="nav_logout"):
        st.session_state['logado'] = False
        st.session_state.pop('usuario', None)
        st.session_state.pop('usuario_id', None)
        st.rerun()

    st.sidebar.markdown("### v1.0.0")

    # --- PÁGINA: DASHBOARD ---
    if st.session_state['pagina'] == "Dashboard":
        st.header("📊 Painel de Desempenho")

        progresso_total = calcular_progresso_geral(st.session_state.get('usuario_id'))
        st.metric("Progresso total do edital", f"{progresso_total}%")

        df_progresso = buscar_dados_progresso()

        if df_progresso.empty:
            st.warning("Ainda não há dados. Registre uma sessão de estudos!")
        else:
            # Agregar dados por disciplina e calcular percentual médio
            df_agg = df_progresso.groupby('Disciplina')[
                'percentual'].mean().reset_index()
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
                df_revisao_filtrado = df_revisao[[
                    'Disciplina', 'Topico']].drop_duplicates()
                st.dataframe(df_revisao_filtrado,
                             use_container_width=True, hide_index=True)
            else:
                st.dataframe(df_revisao, use_container_width=True)
        else:
            st.success("Tudo em dia!")

    # --- PÁGINA: CADASTRAR DISCIPLINA ---
    elif st.session_state['pagina'] == "Cadastrar Disciplina":
        st.header("📚 Gerenciar Disciplinas")
        nova_disc = st.text_input(
            "Nome da Disciplina (Ex: Direito Constitucional):")
        if st.button("Salvar"):
            if nova_disc and adicionar_disciplina(nova_disc, st.session_state.get('usuario_id')):
                st.success("Disciplina cadastrada!")
            else:
                st.error("Erro ao cadastrar ou já existente.")

    # --- PÁGINA: CADASTRAR TÓPICO ---
    elif st.session_state['pagina'] == "Cadastrar Tópico":
        st.header("📝 Cadastrar Conteúdo")
        disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
        if not disciplinas:
            st.warning("Cadastre uma disciplina primeiro!")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            escolha = st.selectbox(
                "Selecione a Disciplina:", list(dict_disc.keys()))
            nome_topico = st.text_input("Nome do Tópico (Ex: Artigo 5º):")
            if st.button("Salvar Tópico"):
                adicionar_topico(dict_disc[escolha], nome_topico, st.session_state.get('usuario_id'))
                st.success("Tópico adicionado!")

    # --- PÁGINA: MEUS ESTUDOS ---
    elif st.session_state['pagina'] == "Meus Estudos":
        st.header("📚 Meus Estudos")
        disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
        if not disciplinas:
            st.warning("Cadastre uma disciplina primeiro!")
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            escolha = st.selectbox(
                "Selecione a Disciplina:", list(dict_disc.keys()))
            disciplina_id = dict_disc[escolha]

            progresso = calcular_progresso_disciplina(disciplina_id, st.session_state.get('usuario_id'))
            st.markdown(f"**Progresso em {escolha}:** {progresso}%")
            st.progress(progresso / 100)

            topicos = listar_topicos_por_disciplina(disciplina_id, st.session_state.get('usuario_id'))
            if not topicos:
                st.info(
                    "Cadastre tópicos para esta disciplina para acompanhar o progresso.")
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
        disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
        disciplina_padrao = st.session_state.get('disciplina_selecionada', None)
        auto_start = st.session_state.pop('auto_start_pomodoro', False)
        render_pomodoro_page(
            disciplinas,
            lambda disciplina_id: listar_topicos_por_disciplina(disciplina_id, st.session_state.get('usuario_id')),
            registrar_desempenho,
            disciplina_padrao=disciplina_padrao,
            auto_start=auto_start,
        )

    # --- PÁGINA: FLASHCARDS ---
    elif st.session_state['pagina'] == "Flashcards":
        st.header("🗂️ Flashcards")
        aba1, aba2 = st.tabs(["Criar", "Estudar"])

        with aba1:
            st.write("Crie novos cards para revisão rápida.")
            disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
            if not disciplinas:
                st.warning(
                    "Cadastre uma disciplina primeiro para poder criar flashcards.")
            else:
                dict_disc = {d[1]: d[0] for d in disciplinas}
                esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()))
                topicos = listar_topicos_por_disciplina(dict_disc[esc_disc], st.session_state.get('usuario_id'))

                if not topicos:
                    st.info(
                        "Cadastre um tópico para esta disciplina antes de criar flashcards.")
                else:
                    dict_topicos = {t[2]: t[0] for t in topicos}
                    esc_topico = st.selectbox(
                        "Tópico:", list(dict_topicos.keys()))

                    pergunta = st.text_area("Pergunta:")
                    resposta = st.text_area("Resposta:")
                    if st.button("Salvar Flashcard"):
                        if pergunta.strip() and resposta.strip():
                            adicionar_flashcard(
                                dict_topicos[esc_topico], pergunta.strip(), resposta.strip())
                            st.success("Flashcard salvo com sucesso!")
                        else:
                            st.error(
                                "Pergunta e resposta não podem ficar vazias.")

        with aba2:
            st.write("Revise seus conceitos salvos.")
            disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
            if not disciplinas:
                st.warning(
                    "Cadastre uma disciplina primeiro para acessar seus flashcards.")
            else:
                dict_disc = {d[1]: d[0] for d in disciplinas}
                esc_disc = st.selectbox("Disciplina:", list(
                    dict_disc.keys()), key="flash_disc")
                topicos = listar_topicos_por_disciplina(dict_disc[esc_disc], st.session_state.get('usuario_id'))

                if not topicos:
                    st.info(
                        "Cadastre um tópico para esta disciplina antes de adicionar flashcards.")
                else:
                    dict_topicos = {t[2]: t[0] for t in topicos}
                    esc_topico = st.selectbox("Tópico:", list(
                        dict_topicos.keys()), key="flash_top")
                    flashcards = listar_flashcards_por_topico(
                        dict_topicos[esc_topico])

                    if not flashcards:
                        st.info(
                            "Nenhum flashcard criado ainda. Vá para a aba 'Criar' para adicionar.")
                    else:
                        for fc in flashcards:
                            # fc: (id, topico_id, pergunta, resposta)
                            with st.expander(fc[2]):
                                st.write(f"**Resposta:** {fc[3]}")

    # --- PÁGINA: MENTOR IA ---
    elif st.session_state['pagina'] == "Mentor IA":
        st.header("🤖 Mentor de Estudos Inteligente")

        st.markdown(
            "Converse com seu mentor IA para obter sugestões de estudo e criar flashcards!")

        # Área de chat
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []

        # Exibir histórico
        for msg in st.session_state['chat_history']:
            if msg['role'] == 'user':
                st.markdown(f"**Você:** {msg['content']}")
            else:
                st.markdown(f"**Mentor IA:** {msg['content']}")

        # Input do usuário
        user_input = st.text_area(
            "Digite sua mensagem ou cole um texto para criar flashcards:", height=100)

        if st.button("Enviar"):
            if user_input.strip():
                # Adicionar mensagem do usuário ao histórico
                st.session_state['chat_history'].append(
                    {'role': 'user', 'content': user_input})

                # Gerar resposta da IA
                resposta = mentor_ia_resposta(user_input)

                # Adicionar resposta ao histórico
                st.session_state['chat_history'].append(
                    {'role': 'assistant', 'content': resposta})

                st.rerun()
            else:
                st.warning("Digite uma mensagem antes de enviar.")

    # --- PÁGINA: CRONOGRAMA ---
    elif st.session_state['pagina'] == "Cronograma":
        # --- FRASE MOTIVACIONAL ---
        frase = obter_frase_motivacional()
        st.markdown(
            f"<div style='text-align: center; font-size: 1.3rem; color: #FF6B6B; font-weight: bold; margin-bottom: 20px;'>{frase}</div>", unsafe_allow_html=True)

        # --- DATA E PROGRESSO ---
        hoje = datetime.now()
        data_formatada = hoje.strftime("%A, %d de %B de %Y").replace("Monday", "Segunda").replace("Tuesday", "Terça").replace(
            "Wednesday", "Quarta").replace("Thursday", "Quinta").replace("Friday", "Sexta").replace("Saturday", "Sábado").replace("Sunday", "Domingo")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"### 📅 Hoje: {data_formatada}")

        with col2, col3:
            pass

        st.divider()

        # --- VERIFICAR SE HÁ CRONOGRAMA ---
        usuario_id = st.session_state.get('usuario_id')
        cronograma = buscar_cronograma_usuario(usuario_id)

        if not cronograma:
            st.markdown(
                "<div style='text-align: center; padding: 40px;'>", unsafe_allow_html=True)
            st.markdown("### 📭 Seu Cronograma está Vazio!")
            st.markdown(
                "Crie um cronograma personalizado para organizar seus estudos.", unsafe_allow_html=True)

            if st.button("⚙️ Configurar meu Primeiro Cronograma", key="setup_cronograma"):
                st.session_state['pagina'] = "Configurar Cronograma"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # --- GRID SEMANAL ---
            st.subheader("📆 Sua Semana de Estudos")

            dia_semana_atual = obter_numero_dia_semana()

            col1, col2 = st.columns([1,3])
            with col1:
                view_mode = st.radio("Modo:", ["Semanal", "Diário"], key="view_mode")
            with col2:
                if view_mode == "Diário":
                    dia_foco = st.selectbox("Dia:", DIAS_SEMANA, index=dia_semana_atual, key="dia_foco")
                    dia_foco_idx = DIAS_MAP.get(dia_foco, dia_semana_atual)
                else:
                    dia_foco_idx = None

            st.divider()

            # Metas do dia
            if view_mode == "Diário" and dia_foco_idx == dia_semana_atual:
                st.subheader("🎯 Metas de Hoje")
                objetivo = st.text_area("Objetivo do Dia:", key="objetivo_hoje", height=100)
                if st.button("💾 Salvar Meta"):
                    # Save to session or db, for now session
                    st.session_state['meta_hoje'] = objetivo
                    st.success("Meta salva!")

            st.divider()

            # Agrupar disciplinas e compromissos por dia
            cronograma_por_dia = {i: [] for i in range(7)}
            compromissos_por_dia = {i: [] for i in range(7)}
            for item in cronograma:
                # item: (id, disciplina_id, disciplina_nome, dia_semana, start_time, duration, color)
                dia = int(item[3]) if item[3] is not None else 0
                cronograma_por_dia[dia].append(item)
            compromissos = buscar_compromissos_extras_usuario(usuario_id)
            for item in compromissos:
                # item: (id, nome, dia_semana, start_time, duration, color)
                dia = int(item[2]) if item[2] is not None else 0
                compromissos_por_dia[dia].append(item)

            # Calcular progresso diário
            dia_ref = dia_foco_idx if view_mode == "Diário" else dia_semana_atual
            disciplinas_ref = cronograma_por_dia[dia_ref]
            estudadas_ref = sum(1 for item in disciplinas_ref if foi_estudada_hoje(item[1]))
            total_ref = len(disciplinas_ref)

            if total_ref > 0:
                progresso_ref = (estudadas_ref / total_ref) * 100
                dia_nome_ref = DIAS_SEMANA[dia_ref]
                st.metric(f"📊 Progresso de {dia_nome_ref}",
                          f"{estudadas_ref}/{total_ref}", f"{int(progresso_ref)}%")
                st.progress(progresso_ref / 100)
            else:
                st.info(f"Nenhuma disciplina agendada para {DIAS_SEMANA[dia_ref] if view_mode == 'Diário' else 'hoje'}.")

            st.divider()

            # Grid
            if view_mode == "Semanal":
                colunas = st.columns(7)
                dias_a_mostrar = range(7)
            else:
                colunas = st.columns(1)
                dias_a_mostrar = [dia_foco_idx]

            for idx, dia_idx in enumerate(dias_a_mostrar):
                with colunas[idx]:
                    dia_nome = DIAS_SEMANA[dia_idx]
                    eh_hoje = dia_idx == dia_semana_atual

                    # Destaque visual para hoje
                    if eh_hoje:
                        st.markdown(
                            f"<div style='display: flex; justify-content: center; align-items: center; padding: 6px 12px; border-radius: 999px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin-bottom: 10px;'>", unsafe_allow_html=True)
                        st.markdown(
                            f"<span style='color: white; font-weight: 700;'>📍 Hoje</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<h4 style='text-align: center; margin-top: 0; margin-bottom: 4px;'>{dia_nome}</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f"<h4 style='text-align: center; margin-top: 0;'>{dia_nome}</h4>", unsafe_allow_html=True)

                    disciplinas_dia = cronograma_por_dia[dia_idx]
                    compromissos_dia = compromissos_por_dia[dia_idx]

                    all_items = []
                    for item in disciplinas_dia:
                        all_items.append(('disciplina', item))
                    for item in compromissos_dia:
                        all_items.append(('compromisso', item))

                    # Sort by start_time
                    all_items.sort(key=lambda x: x[1][4] if x[0] == 'disciplina' else x[1][3] or '00:00')

                    if not all_items:
                        st.markdown(
                            f"<p style='text-align: center; color: #999;'>-</p>", unsafe_allow_html=True)
                    else:
                        for tipo, item in all_items:
                            if tipo == 'disciplina':
                                cronograma_id, disc_id, disc_nome, _, start_time, duration, color = item
                                estudada = foi_estudada_hoje(disc_id) if eh_hoje else False
                                simbolo = "✅" if estudada else ("⏳" if eh_hoje else "📌")
                                nome = disc_nome
                                bg_color = color or "#E9ECEF"
                            else:
                                comp_id, nome, _, start_time, duration, color = item
                                simbolo = "📅"
                                bg_color = color or "#FF9800"
                                estudada = False

                            time_info = f" ({start_time})" if start_time else ""
                            st.markdown(f"""
                            <div style='background: {bg_color}; border: 2px solid #6C757D; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 8px;'>
                                <p style='margin: 0; font-size: 0.75rem; font-weight: bold; color: #333;'>{simbolo} {nome}{time_info}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            # Botão de ação para disciplinas hoje
                            if tipo == 'disciplina' and eh_hoje and not estudada:
                                if st.button(f"▶️ Iniciar", key=f"iniciar_{cronograma_id}"):
                                    st.session_state['pagina'] = "Pomodoro"
                                    st.session_state['disciplina_selecionada'] = disc_nome
                                    st.session_state['auto_start_pomodoro'] = True
                                    st.rerun()

            st.divider()

            # --- SEÇÃO DE CONFIGURAÇÃO DO CRONOGRAMA ---
            st.subheader("⚙️ Gerenciar Cronograma")

            with st.expander("🔧 Adicionar ou Remover Disciplinas"):
                tab1, tab2 = st.tabs(["Adicionar", "Remover"])

                with tab1:
                    st.write("Escolha uma disciplina, dia, horário e duração:")
                    disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
                    if not disciplinas:
                        st.warning("Cadastre uma disciplina primeiro!")
                    else:
                        dict_disc = {d[1]: d[0] for d in disciplinas}
                        esc_disc = st.selectbox("Disciplina:", list(
                            dict_disc.keys()), key="crono_disc")
                        esc_dia = st.selectbox(
                            "Dia da Semana:", DIAS_SEMANA, key="crono_dia")
                        time_slots = [f"{h:02d}:{m:02d}" for h in range(6,23) for m in [0,30]]
                        esc_time = st.selectbox("Horário de Início:", time_slots, key="crono_time")
                        esc_duration = st.selectbox("Duração (min):", [30,60,90,120], key="crono_duration")
                        color_options = ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0']
                        esc_color = st.selectbox("Cor:", color_options, key="crono_color")

                        if st.button("✅ Adicionar ao Cronograma"):
                            dia_idx = DIAS_MAP.get(esc_dia, 0)
                            if salvar_cronograma(dict_disc[esc_disc], dia_idx, esc_time, esc_duration, esc_color):
                                st.success(
                                    f"✅ {esc_disc} adicionada para {esc_dia} às {esc_time}!")
                                st.rerun()
                            else:
                                st.error("Erro ao adicionar.")

                with tab2:
                    st.write("Remova disciplinas do seu cronograma:")
                    if not cronograma:
                        st.info("Nenhuma disciplina no cronograma.")
                    else:
                        # Mostrar cronograma para remover
                        for item in cronograma:
                            cron_id, disc_id, disc_nome, dia_sem, start_time, duration, color = item
                            time_info = f" às {start_time}" if start_time else ""
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(
                                    f"📍 **{disc_nome}** - {DIAS_SEMANA[dia_sem]}{time_info}")
                            with col2:
                                if st.button("🗑️", key=f"remove_disc_{cron_id}"):
                                    remover_cronograma(cron_id)
                                    st.success("Disciplina removida!")
                                    st.rerun()

            st.divider()

            # --- COMPROMISSOS EXTRAS ---
            with st.expander("📅 Gerenciar Compromissos Extras"):
                tab1, tab2 = st.tabs(["Adicionar", "Remover"])

                with tab1:
                    st.write("Adicione compromissos extras (ex: academia, almoço):")
                    nome_comp = st.text_input("Nome do Compromisso:", key="comp_nome")
                    esc_dia_comp = st.selectbox("Dia da Semana:", DIAS_SEMANA, key="comp_dia")
                    time_slots = [f"{h:02d}:{m:02d}" for h in range(6,23) for m in [0,30]]
                    esc_time_comp = st.selectbox("Horário de Início:", time_slots, key="comp_time")
                    esc_duration_comp = st.selectbox("Duração (min):", [30,60,90,120], key="comp_duration")
                    color_options = ['#FF9800', '#4CAF50', '#2196F3', '#E91E63', '#9C27B0']
                    esc_color_comp = st.selectbox("Cor:", color_options, key="comp_color")

                    if st.button("✅ Adicionar Compromisso"):
                        dia_idx = DIAS_MAP.get(esc_dia_comp, 0)
                        if salvar_compromisso_extra(nome_comp, dia_idx, esc_time_comp, esc_duration_comp, esc_color_comp):
                            st.success(f"✅ {nome_comp} adicionado!")
                            st.rerun()
                        else:
                            st.error("Erro ao adicionar.")

                with tab2:
                    st.write("Remova compromissos extras:")
                    if not compromissos:
                        st.info("Nenhum compromisso extra.")
                    else:
                        for item in compromissos:
                            comp_id, nome, dia_sem, start_time, duration, color = item
                            time_info = f" às {start_time}" if start_time else ""
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"📅 **{nome}** - {DIAS_SEMANA[dia_sem]}{time_info}")
                            with col2:
                                if st.button("🗑️", key=f"remove_comp_{comp_id}"):
                                    remover_compromisso_extra(comp_id)
                                    st.success("Compromisso removido!")
                                    st.rerun()

    # --- PÁGINA: CONFIGURAR CRONOGRAMA ---
    elif st.session_state['pagina'] == "Configurar Cronograma":
        st.header("⚙️ Configurar Cronograma")

        st.write("Adicione suas disciplinas ao cronograma semanal.")

        disciplinas = listar_disciplinas(st.session_state.get('usuario_id'))
        if not disciplinas:
            st.warning("Cadastre uma disciplina primeiro!")
            if st.button("📚 Ir para Disciplinas"):
                st.session_state['pagina'] = "Cadastrar Disciplina"
                st.rerun()
        else:
            dict_disc = {d[1]: d[0] for d in disciplinas}
            esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()), key="setup_disc")
            esc_dia = st.selectbox("Dia da Semana:", DIAS_SEMANA, key="setup_dia")
            time_slots = [f"{h:02d}:{m:02d}" for h in range(6,23) for m in [0,30]]
            esc_time = st.selectbox("Horário de Início:", time_slots, key="setup_time")
            esc_duration = st.selectbox("Duração (min):", [30,60,90,120], key="setup_duration")
            color_options = ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0']
            esc_color = st.selectbox("Cor:", color_options, key="setup_color")

            if st.button("✅ Adicionar ao Cronograma"):
                dia_idx = DIAS_MAP.get(esc_dia, 0)
                if salvar_cronograma(dict_disc[esc_disc], dia_idx, esc_time, esc_duration, esc_color):
                    st.success(f"✅ {esc_disc} adicionada para {esc_dia} às {esc_time}!")
                    st.rerun()
                else:
                    st.error("Erro ao adicionar.")

        st.divider()
        if st.button("🔙 Voltar ao Cronograma"):
            st.session_state['pagina'] = "Cronograma"
            st.rerun()
