import streamlit as st
from backend.recuperacao_senha import atualizar_senha


def exibir_recuperacao():
    st.markdown("### 🔑 Recuperar Acesso")

    with st.form("form_recovery"):
        usuario = st.text_input("Digite seu nome de usuário")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar = st.text_input("Confirme a Nova Senha", type="password")

        submit = st.form_submit_button("Redefinir Senha")

        if submit:
            if not usuario or not nova_senha:
                st.warning("Preencha todos os campos.")
            elif nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 4:
                st.error("A senha deve ter no mínimo 4 caracteres.")
            else:
                sucesso, mensagem = atualizar_senha(usuario, nova_senha)
                if sucesso:
                    st.success(mensagem)
                    st.info("Agora você pode voltar para a aba de Login.")
                else:
                    st.error(mensagem)
