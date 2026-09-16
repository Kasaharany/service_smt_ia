import pandas as pd
import plotly.express as px
import streamlit as st

_TEAL = "#00C2A8"
_SEVERITY_CHART_COLORS = {
    "Crítica": "#FF4B4B",
    "Alta": "#FFA721",
    "Média": "#FFD600",
    "Baixa": "#6C7086",
}
_PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=10, b=10),
    transition_duration=400,
    font_color="#FAFAFA",
)


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
    st.markdown("#### 🏭 Distribuição de Causas Raiz por Equipamento")
    machine_counts = (
        results_df["Máquina Culpada"].value_counts().reset_index()
    )
    machine_counts.columns = ["Máquina", "Ocorrências"]

    fig = px.bar(
        machine_counts,
        x="Máquina",
        y="Ocorrências",
        text="Ocorrências",
        color_discrete_sequence=[_TEAL],
    )
    fig.update_traces(
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Ocorrências: %{y}<extra></extra>",
    )
    fig.update_layout(**_PLOTLY_LAYOUT, showlegend=False)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


_SEVERITY_COLORS = {
    "Crítica": "background-color: rgba(255, 75, 75, 0.18)",
    "Alta": "background-color: rgba(255, 167, 33, 0.18)",
    "Média": "background-color: rgba(255, 214, 0, 0.14)",
    "Baixa": "background-color: rgba(49, 51, 79, 0.10)",
}


_SHORT_MACHINE_NAMES = {
    "IMPRESSORA DE PASTA (STENCIL PRINTER)": "Impressora",
    "POSICIONADORA (PICK & PLACE)": "Pick & Place",
    "FORNO DE REFUSÃO / POSICIONADORA": "Forno/Posic.",
    "FORNO DE REFUSÃO": "Forno",
    "AVALIAÇÃO DE PROCESSO": "Processo",
    "NÃO IDENTIFICADO": "N/ident.",
}


def render_history_summary(history_df: pd.DataFrame) -> None:
    """Renderiza os cards de KPI do histórico de produção simulado."""
    col1, col2, col3, col4 = st.columns(4)

    total_defects = len(history_df)
    days_covered = history_df["Data"].nunique()
    avg_per_day = total_defects / days_covered if days_covered else 0
    critical_pct = (
        (history_df["Severidade"] == "Crítica").mean() * 100 if total_defects > 0 else 0
    )
    top_cause_raw = (
        history_df["Máquina Culpada"].value_counts().idxmax() if total_defects > 0 else "N/A"
    )
    top_cause = _SHORT_MACHINE_NAMES.get(top_cause_raw, top_cause_raw)

    with col1:
        st.metric("Defeitos no Período", f"{total_defects}", help=f"Acumulado em {days_covered} dia(s)")
    with col2:
        st.metric("Média por Dia", f"{avg_per_day:.1f}")
    with col3:
        st.metric("Taxa Crítica", f"{critical_pct:.1f}%", delta_color="inverse")
    with col4:
        st.metric("Causa Mais Frequente", top_cause, help=top_cause_raw)


def render_history_trend_chart(history_df: pd.DataFrame) -> None:
    """Renderiza a tendência diária de defeitos detectados no período."""
    st.markdown("#### 📈 Tendência de Defeitos ao Longo do Tempo")
    daily_counts = history_df.groupby("Data").size().reset_index(name="Defeitos")

    fig = px.area(
        daily_counts,
        x="Data",
        y="Defeitos",
        markers=True,
        color_discrete_sequence=[_TEAL],
    )
    fig.update_traces(
        line_shape="spline",
        line_width=3,
        fillgradient=dict(
            type="vertical",
            colorscale=[[0, "rgba(0,194,168,0)"], [1, "rgba(0,194,168,0.35)"]],
        ),
        hovertemplate="<b>%{x|%d/%m}</b><br>Defeitos: %{y}<extra></extra>",
    )
    fig.update_layout(**_PLOTLY_LAYOUT)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def render_history_severity_chart(history_df: pd.DataFrame) -> None:
    """Renderiza a evolução diária de defeitos segmentada por severidade."""
    st.markdown("#### 🚦 Severidade por Dia")
    pivot = (
        history_df.pivot_table(index="Data", columns="Severidade", aggfunc="size", fill_value=0)
        .reset_index()
        .melt(id_vars="Data", var_name="Severidade", value_name="Ocorrências")
    )

    fig = px.bar(
        pivot,
        x="Data",
        y="Ocorrências",
        color="Severidade",
        color_discrete_map=_SEVERITY_CHART_COLORS,
        category_orders={"Severidade": ["Crítica", "Alta", "Média", "Baixa"]},
    )
    fig.update_traces(
        marker_line_width=0,
        hovertemplate="<b>%{x|%d/%m}</b><br>%{fullData.name}: %{y}<extra></extra>",
    )
    fig.update_layout(**_PLOTLY_LAYOUT, legend_title_text="", barmode="stack")
    st.plotly_chart(fig, width="stretch", theme=None, config={"displayModeBar": False})


def render_diagnostic_table(results_df: pd.DataFrame) -> None:
    """Exibe o DataFrame de diagnósticos com destaque de cor por severidade."""
    st.markdown("#### 📋 Detalhamento Técnico das Ocorrências")

    def _highlight_row(row: pd.Series) -> list:
        style = _SEVERITY_COLORS.get(row.get("Severidade"), "")
        return [style] * len(row)

    styled_df = results_df.style.apply(_highlight_row, axis=1)
    st.dataframe(
        styled_df,
        width="stretch",
        hide_index=True,
    )
