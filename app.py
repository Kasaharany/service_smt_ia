import streamlit as st

from config.settings import GEMINI_API_KEY
from core.engine import SMTDeterministicEngine
from ui.theme import inject_custom_theme
from ui.views import (
    render_diagnostic_view,
    render_history_view,
    render_manual_assistant_view,
    render_methodology_view,
)


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🏭 Painel do Sistema")
        st.caption("Diagnóstico de Causa Raiz SMT")
        st.divider()

        ia_status = "🟢 Online" if GEMINI_API_KEY else "🔴 Offline"
        st.metric("Assistente de IA", ia_status)
        st.metric("Motor Determinístico", "🟢 Ativo")
        if not GEMINI_API_KEY:
            st.caption("⚠️ Configure `GEMINI_API_KEY` no `.env` para habilitar a consulta a manuais.")

        st.divider()
        st.markdown("### Navegação")
        st.caption("📊 **Diagnóstico de Linha** — correlação SPI × AOI e integração com as máquinas.")
        st.caption("📈 **Histórico** — tendência de defeitos ao longo do tempo.")
        st.caption("📖 **Consulta a Manuais** — assistente técnico com base em PDFs.")
        st.caption("🔬 **Arquitetura & Metodologia** — fundamentação técnica do sistema.")

        st.divider()
        st.caption("v1.0 · Motor determinístico + IA contextual")


def main() -> None:
    st.set_page_config(
        page_title="Sistema de Diagnóstico SMT",
        page_icon="🏭",
        layout="wide",
        # "auto": expandida em telas grandes, recolhida automaticamente em
        # telas pequenas (celular/tablet) — evita a sidebar cobrir o conteúdo.
        initial_sidebar_state="auto",
    )
    inject_custom_theme()

    _render_sidebar()

    st.title("🏭 Sistema Especialista de Diagnóstico SMT")
    st.caption(
        "Diagnóstico de Causa Raiz por Correlação Determinística SPI-AOI e Assistência Técnica Contextual"
    )

    # Instancia o motor de inferência determinístico
    engine = SMTDeterministicEngine()

    # Divisão das abas principais
    tab_diagnostics, tab_history, tab_manuals, tab_arch = st.tabs([
        "📊 Diagnóstico de Linha",
        "📈 Histórico",
        "📖 Consulta a Manuais",
        "🔬 Arquitetura & Metodologia",
    ])

    with tab_diagnostics:
        render_diagnostic_view(engine)

    with tab_history:
        render_history_view(engine)

    with tab_manuals:
        render_manual_assistant_view()

    with tab_arch:
        render_methodology_view()


if __name__ == "__main__":
    main()
