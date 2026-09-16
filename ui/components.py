import pandas as pd
import streamlit as st


def render_metrics_summary(results_df: pd.DataFrame, exec_time_ms: float) -> None:
    """Renderiza os cards de métricas operacionais principais."""
    col1, col2, col3, col4 = st.columns(4)

    total_defects = len(results_df)
    critical_count = len(results_df[results_df["Severidade"] == "Crítica"])
    stencil_count = len(
        results_df[results_df["Máquina Culpada"].str.contains("STENCIL", na=False)]
    )

    with col1:
        st.metric(
            label="Defeitos Analisados",
            value=f"{total_defects}",
            help="Total de registros correlacionados entre AOI e SPI",
        )
    with col2:
        st.metric(
            label="Falhas Críticas",
            value=f"{critical_count}",
            delta=f"{(critical_count / total_defects * 100):.1f}%" if total_defects > 0 else "0%",
            delta_color="inverse",
        )
    with col3:
        st.metric(
            label="Falhas de Impressão",
            value=f"{stencil_count}",
            help="Defeitos causados por sub ou sobredeposição de pasta",
        )
    with col4:
        st.metric(
            label="Latência do Algoritmo",
            value=f"{exec_time_ms:.2f} ms",
            delta="Determinístico",
        )


def render_distribution_chart(results_df: pd.DataFrame) -> None:
    """Renderiza o gráfico de distribuição de causas raiz por máquina."""
    st.markdown("#### Distribuição de Causas Raiz por Equipamento")
    machine_counts = results_df["Máquina Culpada"].value_counts()
    st.bar_chart(machine_counts)


def render_diagnostic_table(results_df: pd.DataFrame) -> None:
    """Exibe o DataFrame de diagnósticos com suporte a filtros e visualização limpa."""
    st.markdown("#### Detalhamento Técnico das Ocorrências")
    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True,
    )
