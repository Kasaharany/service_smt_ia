"""Views de autenticação: tela de login e painel de conta na sidebar."""

from __future__ import annotations

import streamlit as st

from services.auth_service import authenticate, change_password

_VISITOR_USER = {"username": "Visitante", "role": "visitor"}


def render_login_view() -> None:
    """Tela exibida enquanto não há usuário autenticado na sessão."""
    st.title("🏭 Sistema Especialista de Diagnóstico SMT")
    st.caption("Acesso restrito — faça login ou entre como visitante para conhecer o sistema.")

    col_login, col_visitor = st.columns([2, 1])

    with col_login:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", type="primary")

            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state["auth"] = user
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

    with col_visitor:
        st.subheader("👀 Visitante")
        st.caption("Acesso de demonstração, sem necessidade de login.")
        if st.button("Entrar como Visitante", width="stretch"):
            st.session_state["auth"] = dict(_VISITOR_USER)
            st.rerun()


def render_account_sidebar() -> None:
    """Bloco de conta exibido na sidebar quando há usuário autenticado."""
    auth = st.session_state.get("auth")
    if not auth:
        return

    role_label = "Administrador" if auth["role"] == "admin" else "Visitante"
    st.markdown(f"👤 **{auth['username']}**")
    st.caption(f"Perfil: {role_label}")

    if auth["role"] == "admin":
        with st.expander("🔑 Alterar senha"):
            with st.form("change_password_form"):
                current = st.text_input("Senha atual", type="password")
                new = st.text_input("Nova senha", type="password")
                confirm = st.text_input("Confirmar nova senha", type="password")
                submitted = st.form_submit_button("Atualizar senha")

                if submitted:
                    if not current or not new:
                        st.warning("Preencha todos os campos.")
                    elif new != confirm:
                        st.error("As senhas novas não coincidem.")
                    elif len(new) < 6:
                        st.error("A nova senha deve ter ao menos 6 caracteres.")
                    elif change_password(auth["username"], current, new):
                        st.success("Senha atualizada com sucesso.")
                    else:
                        st.error("Senha atual incorreta.")

    if st.button("🚪 Sair", width="stretch"):
        del st.session_state["auth"]
        st.rerun()
