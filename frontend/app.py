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
    listar_flashcards_revisao,
    salvar_progresso_flashcard,
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
                    tp_id, _, tp_nome, tp_concluido = tp[:4]
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
            usuario_id = st.session_state.get('usuario_id')
            disciplinas = listar_disciplinas(usuario_id)
            if not disciplinas:
                st.warning(
                    "Cadastre uma disciplina primeiro para acessar seus flashcards.")
            else:
                dict_disc = {d[1]: d[0] for d in disciplinas}
                esc_disc = st.selectbox("Disciplina:", list(
                    dict_disc.keys()), key="flash_disc")
                topicos = listar_topicos_por_disciplina(dict_disc[esc_disc], usuario_id)

                if not topicos:
                    st.info(
                        "Cadastre um tópico para esta disciplina antes de adicionar flashcards.")
                else:
                    dict_topicos = {t[2]: t[0] for t in topicos}
                    esc_topico = st.selectbox("Tópico:", list(
                        dict_topicos.keys()), key="flash_top")
                    
                    # Resetar estado do SRS caso mude disciplina/tópico
                    chave_atual = (esc_disc, esc_topico)
                    if st.session_state.get('srs_key') != chave_atual:
                        st.session_state['srs_key'] = chave_atual
                        st.session_state['srs_card_idx'] = 0
                        st.session_state['srs_show_answer'] = False

                    # Seleção de modo de estudo
                    modo_estudo = st.radio(
                        "Modo de Estudo:",
                        ["Praticar (Repetição Espaçada)", "Navegar por Todos"],
                        key="modo_estudo_flashcard"
                    )

                    st.write("---")

                    if modo_estudo == "Praticar (Repetição Espaçada)":
                        # Listar flashcards vencidos
                        flashcards_revisao = listar_flashcards_revisao(dict_topicos[esc_topico], usuario_id)
                        
                        if not flashcards_revisao:
                            st.success("🎉 Todos os flashcards deste tópico estão em dia!")
                        else:
                            idx = st.session_state.get('srs_card_idx', 0)
                            
                            if idx >= len(flashcards_revisao):
                                st.success("🎉 Você concluiu a sessão de estudos para este tópico!")
                                if st.button("🔄 Estudar Novamente"):
                                    st.session_state['srs_card_idx'] = 0
                                    st.session_state['srs_show_answer'] = False
                                    st.rerun()
                            else:
                                fc = flashcards_revisao[idx]
                                # fc: (id, topico_id, pergunta, resposta, caixa, proxima_revisao)
                                
                                st.markdown(f"**Cartão {idx + 1} de {len(flashcards_revisao)}** (Caixa: {fc[4] or 1})")
                                
                                # Render da pergunta
                                st.markdown(f"""
                                <div style='background: #f0f2f6; border-left: 5px solid #2196F3; padding: 15px; border-radius: 5px; margin-bottom: 15px;'>
                                    <h5 style='margin: 0; color: #333;'>P: {fc[2]}</h5>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if not st.session_state.get('srs_show_answer', False):
                                    if st.button("👁️ Mostrar Resposta"):
                                        st.session_state['srs_show_answer'] = True
                                        st.rerun()
                                else:
                                    # Render da resposta
                                    st.markdown(f"""
                                    <div style='background: #e8f5e9; border-left: 5px solid #4CAF50; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
                                        <h5 style='margin: 0; color: #2e7d32;'>R: {fc[3]}</h5>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("🔴 Errei / Difícil", key=f"btn_err_{fc[0]}", use_container_width=True):
                                            salvar_progresso_flashcard(usuario_id, fc[0], False)
                                            st.session_state['srs_card_idx'] = idx + 1
                                            st.session_state['srs_show_answer'] = False
                                            st.rerun()
                                    with col2:
                                        if st.button("🟢 Acertei / Fácil", key=f"btn_acert_{fc[0]}", use_container_width=True):
                                            salvar_progresso_flashcard(usuario_id, fc[0], True)
                                            st.session_state['srs_card_idx'] = idx + 1
                                            st.session_state['srs_show_answer'] = False
                                            st.rerun()
                                            
                    else:
                        flashcards = listar_flashcards_por_topico(dict_topicos[esc_topico])
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
        for idx, msg in enumerate(st.session_state['chat_history']):
            if msg['role'] == 'user':
                st.markdown(f"**Você:** {msg['content']}")
            else:
                st.markdown(f"**Mentor IA:** {msg['content']}")
                
                # Se tiver flashcards sugeridos
                flashcards = msg.get('flashcards', [])
                if flashcards:
                    st.write("")
                    salvos = msg.get('salvos', False)
                    if salvos:
                        st.success("✅ Flashcards salvos com sucesso no seu banco de dados!")
                    else:
                        with st.expander("💡 Flashcards Sugeridos - Clique para Salvar", expanded=True):
                            for i, fc in enumerate(flashcards):
                                st.markdown(f"**Card {i+1}:**")
                                st.markdown(f"- **P:** {fc['pergunta']}")
                                st.markdown(f"- **R:** {fc['resposta']}")
                            
                            st.write("---")
                            usuario_id = st.session_state.get('usuario_id')
                            disciplinas = listar_disciplinas(usuario_id)
                            if disciplinas:
                                dict_disc = {d[1]: d[0] for d in disciplinas}
                                key_disc = f"disc_sug_{idx}"
                                esc_disc = st.selectbox("Salvar na Disciplina:", list(dict_disc.keys()), key=key_disc)
                                
                                topicos = listar_topicos_por_disciplina(dict_disc[esc_disc], usuario_id)
                                if topicos:
                                    dict_topicos = {t[2]: t[0] for t in topicos}
                                    key_top = f"top_sug_{idx}"
                                    esc_topico = st.selectbox("Salvar no Tópico:", list(dict_topicos.keys()), key=key_top)
                                    
                                    if st.button("💾 Adicionar estes Flashcards", key=f"btn_save_sug_{idx}"):
                                        for fc in flashcards:
                                            adicionar_flashcard(dict_topicos[esc_topico], fc['pergunta'], fc['resposta'])
                                        st.session_state['chat_history'][idx]['salvos'] = True
                                        st.success("Flashcards adicionados com sucesso!")
                                        st.rerun()
                                else:
                                    st.warning("Cadastre um tópico para esta disciplina para salvar os flashcards.")
                            else:
                                st.warning("Cadastre uma disciplina primeiro para salvar os flashcards.")

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

                # Fazer o parse do JSON
                import json
                try:
                    dados_ia = json.loads(resposta)
                    texto_resposta = dados_ia.get("resposta", "")
                    flashcards_sugeridos = dados_ia.get("flashcards", [])
                except Exception:
                    texto_resposta = resposta
                    flashcards_sugeridos = []

                # Adicionar resposta ao histórico
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': texto_resposta,
                    'flashcards': flashcards_sugeridos,
                    'salvos': False
                })
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

        st.markdown(f"### 📅 Hoje: {data_formatada}")
        st.divider()

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
            exibir_cronograma_semanal(usuario_id)
            
            st.divider()
            exibir_resumo_semanal(usuario_id)
            
            st.divider()
            st.subheader("⚙️ Gerenciar Cronograma")
            
            with st.expander("🔧 Adicionar ou Remover Disciplinas"):
                tab1, tab2 = st.tabs(["Adicionar", "Remover"])
                with tab1:
                    form_adicionar_disciplina_cronograma(usuario_id)
                with tab2:
                    form_gerenciar_disciplinas(usuario_id)
            
            with st.expander("📅 Gerenciar Compromissos Extras"):
                tab1, tab2 = st.tabs(["Adicionar", "Remover"])
                with tab1:
                    form_adicionar_compromisso(usuario_id)
                with tab2:
                    form_gerenciar_compromissos(usuario_id)
            
            with st.expander("🤖 Sugestões Automáticas"):
                sugerir_cronograma_automatico(usuario_id)

    # --- PÁGINA: CONFIGURAR CRONOGRAMA ---
    elif st.session_state['pagina'] == "Configurar Cronograma":
        st.header("⚙️ Configurar Cronograma")
        st.write("Adicione suas disciplinas ao cronograma semanal.")
        usuario_id = st.session_state.get('usuario_id')
        form_adicionar_disciplina_cronograma(usuario_id)

        st.divider()
        if st.button("🔙 Voltar ao Cronograma"):
            st.session_state['pagina'] = "Cronograma"
            st.rerun()

    # --- PÁGINA: PERFIL ---
    elif st.session_state['pagina'] == "Perfil":
        from backend.services.auth import gerar_hash
        st.header("👤 Perfil do Usuário")
        usuario_id = st.session_state.get('usuario_id')
        
        # Obter dados do usuário
        from backend.database.connection import abrir_conexao
        with abrir_conexao() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username, email, pergunta_seguranca FROM usuarios WHERE id = ?", (usuario_id,))
            user_data = cursor.fetchone()
        
        if user_data:
            username, email, pergunta = user_data
            st.write(f"**Nome de Usuário:** {username}")
            st.write(f"**E-mail:** {email or 'Não cadastrado'}")
            st.write(f"**Pergunta de Segurança:** {pergunta or 'Não cadastrada'}")
            
            st.divider()
            st.subheader("Alterar Configurações de Recuperação")
            with st.form("form_perfil_update"):
                novo_email = st.text_input("Alterar E-mail:", value=email or "")
                nova_pergunta = st.text_input("Pergunta de Segurança:", value=pergunta or "", placeholder="Ex: Nome do seu primeiro mascote?")
                nova_resposta = st.text_input("Resposta da Pergunta (Deixe em branco para manter a atual):", type="password")
                
                if st.form_submit_button("Salvar Alterações"):
                    if not novo_email:
                        st.error("O e-mail é obrigatório.")
                    else:
                        from backend.database.connection import abrir_conexao
                        try:
                            with abrir_conexao() as conn:
                                cursor = conn.cursor()
                                if nova_resposta:
                                    cursor.execute(
                                        "UPDATE usuarios SET email = ?, pergunta_seguranca = ?, resposta_seguranca = ? WHERE id = ?",
                                        (novo_email, nova_pergunta, gerar_hash(nova_resposta), usuario_id)
                                    )
                                else:
                                    cursor.execute(
                                        "UPDATE usuarios SET email = ?, pergunta_seguranca = ? WHERE id = ?",
                                        (novo_email, nova_pergunta, usuario_id)
                                    )
                            st.success("Perfil atualizado com sucesso!")
                            st.rerun()

                        except sqlite3.IntegrityError:
                            st.error("Este e-mail já está em uso por outro usuário.")
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

    # --- PÁGINA: CONFIGURAÇÕES ---
    elif st.session_state['pagina'] == "Configurações":
        st.header("⚙️ Opções do Sistema")
        
        st.subheader("Configurações do Pomodoro Padrão")
        if 'pomodoro_foco' not in st.session_state:
            st.session_state['pomodoro_foco'] = 20
        if 'pomodoro_pausa_curta' not in st.session_state:
            st.session_state['pomodoro_pausa_curta'] = 5
        if 'pomodoro_pausa_longa' not in st.session_state:
            st.session_state['pomodoro_pausa_longa'] = 15
            
        with st.form("form_config_pomodoro"):
            foco = st.number_input("Tempo de Foco padrão (min):", min_value=5, max_value=90, value=st.session_state['pomodoro_foco'])
            pausa_c = st.number_input("Pausa Curta padrão (min):", min_value=1, max_value=30, value=st.session_state['pomodoro_pausa_curta'])
            pausa_l = st.number_input("Pausa Longa padrão (min):", min_value=5, max_value=60, value=st.session_state['pomodoro_pausa_longa'])
            
            if st.form_submit_button("Salvar Preferências"):
                st.session_state['pomodoro_foco'] = foco
                st.session_state['pomodoro_pausa_curta'] = pausa_c
                st.session_state['pomodoro_pausa_longa'] = pausa_l
                st.success("Configurações do Pomodoro atualizadas!")
                st.rerun()

        st.divider()
        if st.button("🔙 Voltar ao Cronograma"):
            st.session_state['pagina'] = "Cronograma"
            st.rerun()
