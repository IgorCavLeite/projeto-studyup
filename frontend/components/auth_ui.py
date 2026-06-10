import streamlit as st
from backend.services.auth import (
    autenticar_usuario,
    cadastrar_usuario,
    solicitar_link_redefinicao,
    redefinir_senha_por_token,
)

def desenhar_tela_login():
    st.title("🚀 StudyUp - Área de Acesso")
    
    tab_login, tab_recuperacao, tab_cadastro = st.tabs([
        "Entrar", "Esqueci Minha Senha", "Criar Nova Conta"
    ])

    with tab_login:
        with st.form("form_login"):
            usuario = st.text_input("Usuário ou E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                sucesso, mensagem, usuario_id = autenticar_usuario(usuario, senha)
                if sucesso:
                    st.session_state['logado'] = True
                    st.session_state['usuario'] = usuario
                    st.session_state['usuario_id'] = usuario_id
                    st.rerun()
                else:
                    st.error(mensagem)

    with tab_recuperacao:
        st.subheader("Solicitar link de recuperação")
        with st.form("form_solicitar_link"):
            email_recuperacao = st.text_input("E-mail cadastrado")
            if st.form_submit_button("Enviar link por e-mail"):
                sucesso, mensagem = solicitar_link_redefinicao(email_recuperacao)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)

        st.divider()
        st.subheader("Redefinir senha com token")
        try:
            token_param = st.query_params.get("reset_token", "")
        except Exception:
            # Compatibilidade com versões do Streamlit que não expõem
            # `st.query_params` — apenas não pré-preenche o token.
            token_param = ""
        with st.form("form_redefinir_token"):
            token_recuperacao = st.text_input(
                "Token de recuperação",
                value=token_param or "",
            )
            nova_senha_recuperacao = st.text_input("Nova senha", type="password")
            confirmar_nova_senha = st.text_input(
                "Confirme a nova senha", type="password"
            )
            if st.form_submit_button("Redefinir senha"):
                if nova_senha_recuperacao != confirmar_nova_senha:
                    st.error("As senhas não conferem!")
                else:
                    sucesso, mensagem = redefinir_senha_por_token(
                        token_recuperacao,
                        nova_senha_recuperacao,
                    )
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)

    with tab_cadastro:
        st.subheader("Crie sua conta de estudante")
        with st.form("form_cadastro"):
            novo_usuario = st.text_input("Escolha um Nome de Usuário")
            novo_email = st.text_input("E-mail")
            nova_senha = st.text_input("Defina uma Senha", type="password")
            confirmar_senha = st.text_input("Confirme a Senha", type="password")
            
            if st.form_submit_button("Finalizar Cadastro"):
                if nova_senha != confirmar_senha:
                    st.error("As senhas não conferem!")
                elif len(nova_senha) < 4:
                    st.warning("A senha deve ter pelo menos 4 caracteres por segurança.")
                else:
                    sucesso, mensagem = cadastrar_usuario(
                        novo_usuario, nova_senha, novo_email
                    )
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)