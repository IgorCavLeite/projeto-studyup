"""
Componente UI para gerenciamento de cronograma de estudos
"""

import streamlit as st
from backend.services.cronograma import (
    DIAS_SEMANA,
    CORES_PADRAO,
    adicionar_disciplina_cronograma,
    remover_disciplina_cronograma,
    obter_cronograma_completo,
    calcular_progresso_dia,
    calcular_carga_horaria_semanal,
    adicionar_compromisso,
    remover_compromisso,
    validar_conflito_horario,
    obter_sugestoes_cronograma,
)
from backend.database.connection import (
    listar_disciplinas,
    foi_estudada_hoje,
    obter_disciplinas_por_dia,
)
from datetime import datetime


def renderizar_cartao_disciplina(nome, horario, duracao, cor, estudada=False, eh_hoje=False):
    """Renderiza um cartão de disciplina com informações visuais."""
    simbolo = "✅" if estudada else ("⏳" if eh_hoje else "📌")
    tempo_info = f" às {horario}" if horario else ""
    duracao_info = f" ({duracao}min)" if duracao else ""
    
    st.markdown(f"""
    <div style='background: {cor}; border: 2px solid #6C757D; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 8px;'>
        <p style='margin: 0; font-size: 0.75rem; font-weight: bold; color: #333;'>{simbolo} {nome}{tempo_info}{duracao_info}</p>
    </div>
    """, unsafe_allow_html=True)


def exibir_cronograma_semanal(usuario_id=None):
    """
    Exibe o cronograma completo da semana com todas as disciplinas e compromissos.
    """
    cronograma = obter_cronograma_completo(usuario_id)
    dia_semana_atual = datetime.now().weekday()
    
    st.subheader("📆 Sua Semana de Estudos")
    
    # Selector de modo de visualização
    col1, col2 = st.columns([1, 3])
    with col1:
        view_mode = st.radio("Modo:", ["Semanal", "Diário"], key="view_mode")
    with col2:
        if view_mode == "Diário":
            dias_semana_display = list(DIAS_SEMANA)
            dia_foco = st.selectbox("Dia:", dias_semana_display, index=dia_semana_atual, key="dia_foco_select")
            dia_foco_idx = DIAS_SEMANA.index(dia_foco)
        else:
            dia_foco_idx = None
    
    st.divider()
    
    # Mostrar metas do dia (se for diário e hoje)
    if view_mode == "Diário" and dia_foco_idx == dia_semana_atual:
        st.subheader("🎯 Metas de Hoje")
        objetivo = st.text_area("Objetivo do Dia:", key="objetivo_hoje", height=100)
        if st.button("💾 Salvar Meta", key="btn_salvar_meta"):
            st.session_state['meta_hoje'] = objetivo
            st.success("Meta salva!")
    
    st.divider()
    
    # Mostrar progresso do dia/dias
    if view_mode == "Diário":
        dias_ref = [dia_foco_idx]
    else:
        dias_ref = range(7)
    
    for idx, dia_idx in enumerate(dias_ref):
        if view_mode == "Semanal" and idx > 0:
            st.divider()
        
        progresso = calcular_progresso_dia(dia_idx, usuario_id)
        dia_nome = DIAS_SEMANA[dia_idx]
        eh_hoje = dia_idx == dia_semana_atual
        
        if eh_hoje:
            st.markdown(
                f"<div style='display: flex; justify-content: center; align-items: center; padding: 6px 12px; border-radius: 999px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin-bottom: 10px;'>",
                unsafe_allow_html=True)
            st.markdown(f"<span style='color: white; font-weight: 700;'>📍 {dia_nome} (Hoje)</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"### {dia_nome}", unsafe_allow_html=True)
        
        # Mostrar progresso
        if progresso['total'] > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Disciplinas", f"{progresso['estudadas']}/{progresso['total']}")
            with col2:
                st.metric("Progresso", f"{progresso['percentual']:.0f}%")
            with col3:
                st.progress(progresso['percentual'] / 100)
        else:
            st.info(f"Nenhuma disciplina agendada para {dia_nome}")
        
        # Exibir itens do cronograma
        if view_mode == "Semanal":
            # Grid de 7 colunas
            col = st.columns(1)[0]
        else:
            col = st.columns(1)[0]
        
        with col:
            items = cronograma[dia_idx]['disciplinas'] + cronograma[dia_idx]['compromissos']
            items.sort(key=lambda x: x.get('horario', '00:00') or '00:00')
            
            if not items:
                st.markdown(f"<p style='text-align: center; color: #999;'>Sem compromissos</p>", unsafe_allow_html=True)
            else:
                for item in items:
                    tipo = item.get('tipo', 'desconhecido')
                    if tipo == 'disciplina':
                        estudada = foi_estudada_hoje(item['disciplina_id']) if eh_hoje else False
                        renderizar_cartao_disciplina(
                            item['nome'],
                            item['horario'],
                            item['duracao'],
                            item['cor'],
                            estudada=estudada,
                            eh_hoje=eh_hoje
                        )
                        
                        # Botão de iniciar estudo
                        if eh_hoje and not estudada:
                            if st.button(f"▶️ Iniciar {item['nome']}", key=f"iniciar_{item['id']}"):
                                st.session_state['pagina'] = "Pomodoro"
                                st.session_state['disciplina_selecionada'] = item['nome']
                                st.session_state['auto_start_pomodoro'] = True
                                st.rerun()
                    else:
                        renderizar_cartao_disciplina(
                            f"📅 {item['nome']}",
                            item['horario'],
                            item['duracao'],
                            item['cor'],
                            estudada=False,
                            eh_hoje=False
                        )


def form_adicionar_disciplina_cronograma(usuario_id=None):
    """Formulário para adicionar uma disciplina ao cronograma."""
    st.subheader("➕ Adicionar Disciplina ao Cronograma")
    
    disciplinas = listar_disciplinas()
    if not disciplinas:
        st.warning("📚 Cadastre uma disciplina primeiro!")
        return False
    
    # Criar dicionário de disciplinas
    dict_disc = {d[1]: d[0] for d in disciplinas}
    
    # Inputs
    col1, col2 = st.columns(2)
    with col1:
        disc_selecionada = st.selectbox("Disciplina:", list(dict_disc.keys()), key="form_disc")
    with col2:
        dia_selecionado = st.selectbox("Dia da Semana:", DIAS_SEMANA, key="form_dia")
    
    col1, col2 = st.columns(2)
    with col1:
        time_slots = [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in [0, 30]]
        horario_selecionado = st.selectbox("Horário de Início:", time_slots, key="form_horario")
    with col2:
        duracao_selecionada = st.selectbox("Duração (min):", [30, 60, 90, 120], key="form_duracao")
    
    cores_lista = list(CORES_PADRAO.values())
    cores_labels = list(CORES_PADRAO.keys())
    cor_selecionada = st.selectbox("Cor:", cores_labels, key="form_cor")
    cor_hex = CORES_PADRAO[cor_selecionada]
    
    if st.button("✅ Adicionar ao Cronograma", key="btn_add_disc"):
        dia_idx = DIAS_SEMANA.index(dia_selecionado)
        disc_id = dict_disc[disc_selecionada]
        
        # Verificar conflito de horário
        tem_conflito, msg_conflito = validar_conflito_horario(dia_idx, horario_selecionado, duracao_selecionada, usuario_id)
        if tem_conflito:
            st.error(f"⚠️ {msg_conflito}")
            return False
        
        # Adicionar disciplina
        sucesso, mensagem, _ = adicionar_disciplina_cronograma(
            disc_id, dia_idx, horario_selecionado, duracao_selecionada, cor_hex, usuario_id
        )
        
        if sucesso:
            st.success(f"✅ {disc_selecionada} adicionada para {dia_selecionado} às {horario_selecionado}!")
            st.rerun()
        else:
            st.error(f"❌ Erro: {mensagem}")
        
        return sucesso
    
    return False


def form_gerenciar_disciplinas(usuario_id=None):
    """Formulário para remover disciplinas do cronograma."""
    st.subheader("🗑️ Remover Disciplinas")
    
    cronograma = obter_cronograma_completo(usuario_id)
    
    # Coletar todas as disciplinas
    todas_disciplinas = []
    for dia in range(7):
        todas_disciplinas.extend(cronograma[dia]['disciplinas'])
    
    if not todas_disciplinas:
        st.info("Nenhuma disciplina no cronograma.")
        return
    
    for item in todas_disciplinas:
        col1, col2 = st.columns([3, 1])
        with col1:
            dia_nome = DIAS_SEMANA[item['dia']]
            horario_info = f" às {item['horario']}" if item['horario'] else ""
            st.markdown(f"📍 **{item['nome']}** - {dia_nome}{horario_info}")
        with col2:
            if st.button("🗑️", key=f"remove_{item['id']}"):
                sucesso, msg = remover_disciplina_cronograma(item['id'])
                if sucesso:
                    st.success("Removido!")
                    st.rerun()
                else:
                    st.error(msg)


def form_adicionar_compromisso(usuario_id=None):
    """Formulário para adicionar um compromisso extra."""
    st.subheader("📅 Adicionar Compromisso Extra")
    
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome do Compromisso:", key="comp_nome", placeholder="Ex: Academia, Almoço")
    with col2:
        dia = st.selectbox("Dia da Semana:", DIAS_SEMANA, key="comp_dia")
    
    col1, col2 = st.columns(2)
    with col1:
        time_slots = [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in [0, 30]]
        horario = st.selectbox("Horário de Início:", time_slots, key="comp_horario")
    with col2:
        duracao = st.selectbox("Duração (min):", [30, 60, 90, 120], key="comp_duracao")
    
    cores_labels = list(CORES_PADRAO.keys())
    cor_label = st.selectbox("Cor:", cores_labels, key="comp_cor")
    cor_hex = CORES_PADRAO[cor_label]
    
    if st.button("✅ Adicionar Compromisso", key="btn_add_comp"):
        if not nome or len(nome.strip()) == 0:
            st.error("Por favor, digite um nome para o compromisso!")
            return False
        
        dia_idx = DIAS_SEMANA.index(dia)
        sucesso, msg = adicionar_compromisso(nome, dia_idx, horario, duracao, cor_hex, usuario_id)
        
        if sucesso:
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.error(f"❌ Erro: {msg}")
        
        return sucesso
    
    return False


def form_gerenciar_compromissos(usuario_id=None):
    """Formulário para remover compromissos extras."""
    st.subheader("🗑️ Remover Compromissos")
    
    cronograma = obter_cronograma_completo(usuario_id)
    
    # Coletar todos os compromissos
    todos_compromissos = []
    for dia in range(7):
        todos_compromissos.extend(cronograma[dia]['compromissos'])
    
    if not todos_compromissos:
        st.info("Nenhum compromisso extra.")
        return
    
    for item in todos_compromissos:
        col1, col2 = st.columns([3, 1])
        with col1:
            dia_nome = DIAS_SEMANA[item['dia']]
            horario_info = f" às {item['horario']}" if item['horario'] else ""
            st.markdown(f"📅 **{item['nome']}** - {dia_nome}{horario_info}")
        with col2:
            if st.button("🗑️", key=f"remove_comp_{item['id']}"):
                sucesso, msg = remover_compromisso(item['id'])
                if sucesso:
                    st.success("Removido!")
                    st.rerun()
                else:
                    st.error(msg)


def exibir_resumo_semanal(usuario_id=None):
    """Exibe um resumo das horas de estudo da semana."""
    st.subheader("📊 Resumo Semanal")
    
    carga = calcular_carga_horaria_semanal(usuario_id)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("⏱️ Total Semanal", f"{carga['total_horas']}h", f"{carga['total_minutos']}min")
    with col2:
        media_diaria = carga['total_horas'] / 7 if carga['total_horas'] > 0 else 0
        st.metric("📈 Média Diária", f"{media_diaria:.1f}h")
    
    st.divider()
    
    # Mostrar por dia
    st.write("**Carga horária por dia:**")
    for dia, minutos in carga['por_dia'].items():
        horas = minutos / 60
        st.progress(horas / 4, text=f"{dia}: {horas:.1f}h ({minutos}min)")


def sugerir_cronograma_automatico(usuario_id=None):
    """Sugere um cronograma automático com base nas disciplinas."""
    st.subheader("🤖 Sugerir Cronograma Automático")
    
    disciplinas = listar_disciplinas()
    if not disciplinas:
        st.warning("📚 Cadastre disciplinas primeiro!")
        return
    
    dict_disc = {d[1]: d[0] for d in disciplinas}
    
    col1, col2 = st.columns(2)
    with col1:
        disciplinas_selecionadas = st.multiselect(
            "Selecione as disciplinas:",
            list(dict_disc.keys()),
            key="sugestao_discs"
        )
    with col2:
        horas_por_dia = st.number_input("Horas por dia:", min_value=0.5, max_value=8.0, value=2.0, step=0.5, key="sugestao_horas")
    
    if st.button("💡 Gerar Sugestão", key="btn_sugestao"):
        if not disciplinas_selecionadas:
            st.warning("Selecione pelo menos uma disciplina!")
            return
        
        disc_ids = [dict_disc[d] for d in disciplinas_selecionadas]
        sugestoes = obter_sugestoes_cronograma(disc_ids, horas_por_dia)
        
        st.success("✅ Sugestão gerada!")
        
        if st.button("👍 Aceitar Sugestão", key="btn_aceitar_sugestao"):
            for sugestao in sugestoes:
                sucesso, _, _ = adicionar_disciplina_cronograma(
                    sugestao['disciplina_id'],
                    sugestao['dia_semana'],
                    sugestao['horario'],
                    sugestao['duracao'],
                    sugestao['cor'],
                    usuario_id
                )
            
            st.success("✅ Cronograma automático criado!")
            st.rerun()
        
        # Mostrar preview
        st.write("**Preview da sugestão:**")
        for sugestao in sugestoes:
            dia_nome = DIAS_SEMANA[sugestao['dia_semana']]
            # Encontrar nome da disciplina
            for d in disciplinas:
                if d[0] == sugestao['disciplina_id']:
                    nome_disc = d[1]
                    break
            
            st.info(f"📍 {nome_disc} - {dia_nome} às {sugestao['horario']} ({sugestao['duracao']}min)")
