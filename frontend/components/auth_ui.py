import streamlit as st
from backend.services.auth import autenticar_usuario, cadastrar_usuario

def desenhar_tela_login():
    st.title("🚀 StudyUp - Área de Acesso")
    
    # Criando abas para não poluir a tela
    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Nova Conta"])

    with tab_login:
        with st.form("form_login"):
            usuario = st.text_input("Usuário ou E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                sucesso, mensagem = autenticar_usuario(usuario, senha)
                if sucesso:
                    st.session_state['logado'] = True
                    st.rerun()
                else:
                    st.error(mensagem)

    with tab_cadastro:
        st.subheader("Crie sua conta de estudante")
        with st.form("form_cadastro"):
            novo_usuario = st.text_input("Escolha um Nome de Usuário")
            nova_senha = st.text_input("Defina uma Senha", type="password")
            confirmar_senha = st.text_input("Confirme a Senha", type="password")
            
            if st.form_submit_button("Finalizar Cadastro"):
                if nova_senha != confirmar_senha:
                    st.error("As senhas não conferem!")
                elif len(nova_senha) < 4:
                    st.warning("A senha deve ter pelo menos 4 caracteres por segurança.")
                else:
                    sucesso, mensagem = cadastrar_usuario(novo_usuario, nova_senha)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)