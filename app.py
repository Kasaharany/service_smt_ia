import streamlit as st

from core.engine import SMTDeterministicEngine
from ui.views import (
    render_diagnostic_view,
    render_manual_assistant_view,
    render_methodology_view,
)


def main() -> None:
    st.set_page_config(
        page_title="Sistema de Diagnóstico SMT",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("🏭 SMT Expert Diagnostic System")
    st.caption(
        "Diagnóstico de Causa Raiz por Correlação Determinística SPI-AOI e Assistência Técnica Contextual"
    )

    # Instancia o motor de inferência determinístico
    engine = SMTDeterministicEngine()

    # Divisão das abas principais
    tab_diagnostics, tab_manuals, tab_arch = st.tabs([
        "📊 Diagnóstico de Linha",
        "📖 Consulta a Manuais",
        "🔬 Arquitetura & Metodologia",
    ])

    with tab_diagnostics:
        render_diagnostic_view(engine)

    with tab_manuals:
        render_manual_assistant_view()

    with tab_arch:
        render_methodology_view()


if __name__ == "__main__":
    main()
