import time
import streamlit as st
from backend.services.pomodoro import formatar_tempo

DEFAULT_POMODORO = 20
DEFAULT_PAUSA_CURTA = 5
DEFAULT_PAUSA_LONGA = 15

MODES = {
    "Pomodoro": {
        "label": "Foco",
        "emoji": "🔥",
        "default": DEFAULT_POMODORO,
        "description": "Tempo de concentração para estudar com foco total.",
    },
    "Pausa Curta": {
        "label": "Descanso Curto",
        "emoji": "☕",
        "default": DEFAULT_PAUSA_CURTA,
        "description": "Pausa rápida para recarregar a energia.",
    },
    "Pausa Longa": {
        "label": "Descanso Longo",
        "emoji": "🌿",
        "default": DEFAULT_PAUSA_LONGA,
        "description": "Pausa maior para relaxar profundamente.",
    },
}


def _render_pomodoro_banner(mode_name: str, duration: int):
    mode_info = MODES.get(mode_name, MODES["Pomodoro"])
    st.markdown(
        f"""
        <div class='pomodoro-card'>
            <div class='pomodoro-header'>
                <div>
                    <h2>{mode_info['emoji']} {mode_info['label']}</h2>
                    <p>{mode_info['description']}</p>
                </div>
                <div class='pomodoro-meta'>
                    <span>{duration} min</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _executar_timer(duracao_minutos: int, modo_atual: str):
    duracao_segundos = duracao_minutos * 60
    progresso = st.progress(0)
    contador = st.empty()

    for tempo in range(duracao_segundos, -1, -1):
        contador.markdown(
            f"<div class='pomodoro-countdown'>{formatar_tempo(tempo)}</div>", unsafe_allow_html=True
        )
        progresso.progress((duracao_segundos - tempo) / duracao_segundos)
        time.sleep(1)

    st.balloons()
    st.success(f"🎉 Ciclo de {modo_atual} concluído!")


def _obter_proximo_modo(ciclos_pomodoro:int):
    if ciclos_pomodoro > 0 and ciclos_pomodoro % 4 == 0:
        return "Pausa Longa"
    return "Pausa Curta"


def _executar_sequencia(modo: str, tempo_foco: int, pausa_curta: int, pausa_longa: int, ciclos_pomodoro: int):
    if modo == "Pomodoro":
        _executar_timer(tempo_foco, modo)
        ciclos_pomodoro += 1
        proximo = _obter_proximo_modo(ciclos_pomodoro)
        st.info(f"Agora iniciando automaticamente {proximo.lower()}.")
        if proximo == "Pausa Curta":
            _executar_timer(pausa_curta, proximo)
        else:
            _executar_timer(pausa_longa, proximo)
        st.success("🟢 Pausa concluída! Volte ao Pomodoro quando estiver pronto.")
    else:
        duracao = pausa_curta if modo == "Pausa Curta" else pausa_longa
        _executar_timer(duracao, modo)
        st.success("🟢 Pausa concluída! Agora volte ao Pomodoro.")
    return ciclos_pomodoro


def render_pomodoro_page(
    disciplinas,
    listar_topicos_func,
    registrar_desempenho_func,
    disciplina_padrao=None,
    auto_start=False,
):
    st.header("⏳ Timer Pomodoro")
    if not disciplinas:
        st.info("Cadastre disciplinas e tópicos antes de usar o Pomodoro.")
        return

    dict_disc = {d[1]: d[0] for d in disciplinas}
    indice_padrao = 0
    if disciplina_padrao and disciplina_padrao in dict_disc:
        indice_padrao = list(dict_disc.keys()).index(disciplina_padrao)

    esc_disc = st.selectbox("Disciplina:", list(dict_disc.keys()), index=indice_padrao)
    if disciplina_padrao:
        st.session_state.pop('disciplina_selecionada', None)

    topicos = listar_topicos_func(dict_disc[esc_disc])
    if not topicos:
        st.warning("Cadastre um tópico para esta disciplina antes de iniciar o Pomodoro.")
        return

    dict_topicos = {t[2]: t[0] for t in topicos}
    esc_topico = st.selectbox("Tópico:", list(dict_topicos.keys()))

    if "pomodoro_mode" not in st.session_state:
        st.session_state["pomodoro_mode"] = "Pomodoro"
    if "pomodoro_cycles" not in st.session_state:
        st.session_state["pomodoro_cycles"] = 0

    st.markdown("---")
    st.subheader("Modos de Timer")
    modo = st.radio(
        "Escolha um modo:",
        list(MODES.keys()),
        index=list(MODES.keys()).index(st.session_state["pomodoro_mode"]),
        horizontal=True,
    )
    st.session_state["pomodoro_mode"] = modo

    col1, col2, col3 = st.columns(3)
    with col1:
        tempo_foco = st.number_input(
            "Pomodoro (min)", min_value=5, max_value=90, value=st.session_state.get('pomodoro_foco', DEFAULT_POMODORO), step=1, key="pomodoro_foco"
        )
    with col2:
        pausa_curta = st.number_input(
            "Pausa Curta (min)", min_value=1, max_value=30, value=st.session_state.get('pomodoro_pausa_curta', DEFAULT_PAUSA_CURTA), step=1, key="pomodoro_pausa_curta"
        )
    with col3:
        pausa_longa = st.number_input(
            "Pausa Longa (min)", min_value=5, max_value=60, value=st.session_state.get('pomodoro_pausa_longa', DEFAULT_PAUSA_LONGA), step=1, key="pomodoro_pausa_longa"
        )

    st.write(f"**Pomodoros concluídos:** {st.session_state['pomodoro_cycles']} (a cada 4, próxima é pausa longa)")

    outros_valores = {
        "Pomodoro": tempo_foco,
        "Pausa Curta": pausa_curta,
        "Pausa Longa": pausa_longa,
    }
    duracao_selecionada = outros_valores.get(modo, DEFAULT_POMODORO)
    _render_pomodoro_banner(modo, duracao_selecionada)

    if auto_start and not st.session_state.get("pomodoro_auto_start_executed", False):
        st.session_state["pomodoro_auto_start_executed"] = True
        st.session_state["pomodoro_cycles"] = _executar_sequencia(
            "Pomodoro",
            tempo_foco,
            pausa_curta,
            pausa_longa,
            st.session_state["pomodoro_cycles"],
        )
        st.session_state["pomodoro_mode"] = "Pomodoro"
        st.rerun()

    iniciar_chave = f"iniciar_{modo.replace(' ', '_').lower()}"
    if st.button("▶️ Iniciar Ciclo", key=iniciar_chave):
        st.session_state["pomodoro_cycles"] = _executar_sequencia(
            modo,
            tempo_foco,
            pausa_curta,
            pausa_longa,
            st.session_state["pomodoro_cycles"],
        )
        st.session_state["pomodoro_mode"] = "Pomodoro"
        st.rerun()

    st.markdown("---")
    with st.expander("📈 Registrar Desempenho após o ciclo"):
        q = st.number_input("Questões Feitas:", min_value=0, key="pomodoro_questoes")
        a = st.number_input("Acertos:", min_value=0, key="pomodoro_acertos")
        if st.button("💾 Registrar Desempenho", key="btn_registrar_desempenho"):
            registrar_desempenho_func(dict_topicos[esc_topico], q, a)
            st.success("Dados de desempenho registrados com sucesso!")
