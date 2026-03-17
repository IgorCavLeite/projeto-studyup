import streamlit as st

def desenhar_tela_login():
    """
    Função que renderiza a interface de autenticação.
    Requisitos: E-mail/User, Senha oculta, Botão Login, Cadastro e Recuperação.
    """
    st.markdown("### 🔐 Acesso ao StudyUp")
    
    with st.form("form_auth"):
        usuario = st.text_input("E-mail ou Username")
        senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar")

        if btn_entrar:
            # Critério de aceite: validar se estão vazios
            if not usuario or not senha:
                st.error("Preencha todos os campos!")
            else:
                # Simulação de verificação (a ser integrada ao DB)
                if usuario == "admin" and senha == "123":
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

    # Links de navegação solicitados
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Esqueci minha senha"):
            st.info("Fluxo de recuperação iniciado...")
    with col2:
        if st.button("Não tem conta? Cadastre-se"):
            st.info("Redirecionando para Cadastro...")