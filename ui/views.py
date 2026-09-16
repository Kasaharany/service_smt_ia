import streamlit as st

from config.settings import GEMINI_API_KEY
from core.engine import SMTDeterministicEngine
from core.ingestion import ingest_inspection_datasets
from services.history_service import generate_historical_diagnostics
from services.llm_service import TechnicalManualAssistant
from services.machine_integration import simulate_machine_integration
from ui.components import (
    render_diagnostic_table,
    render_distribution_chart,
    render_history_severity_chart,
    render_history_summary,
    render_history_trend_chart,
    render_metrics_summary,
)


def render_diagnostic_view(engine: SMTDeterministicEngine) -> None:
    """Aba 1: Ingestão de relatórios e execução do motor determinístico."""
    st.subheader("📊 Ingestão de Dados de Inspeção")
    st.write(
        "Carregue os relatórios de medição volumétrica (SPI) e detecção de defeitos pós-refusão (AOI), "
        "ou integre diretamente com as máquinas da linha."
    )

    col_connect, col_clear = st.columns([3, 1])
    with col_connect:
        if st.button(
            "🔌 Conectar às Máquinas (SPI + AOI)",
            type="secondary",
            help="Simula a integração direta com as máquinas de SPI e AOI da linha de produção.",
        ):
            with st.spinner("Estabelecendo conexão com as máquinas da linha..."):
                spi_df, aoi_df = simulate_machine_integration()
            st.session_state["integration_spi_df"] = spi_df
            st.session_state["integration_aoi_df"] = aoi_df
            st.success(
                f"Integração concluída: SPI ({len(spi_df)} registros) | AOI ({len(aoi_df)} defeitos) recebidos das máquinas."
            )
    with col_clear:
        if "integration_spi_df" in st.session_state and st.button("🔄 Limpar integração"):
            st.session_state.pop("integration_spi_df", None)
            st.session_state.pop("integration_aoi_df", None)
            st.rerun()

    st.caption(
        "🔧 Modo demonstração — em produção, este botão se conectaria via pasta de rede/SFTP "
        "ou protocolo industrial (SECS/GEM) diretamente às máquinas físicas."
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        spi_file = st.file_uploader(
            "Relatório SPI (.csv)", type=["csv"], key="upload_spi"
        )
    with col2:
        aoi_file = st.file_uploader(
            "Relatório AOI (.csv)", type=["csv"], key="upload_aoi"
        )

    spi_df = aoi_df = None
    source_label = None

    try:
        if spi_file and aoi_file:
            spi_df, aoi_df = ingest_inspection_datasets(spi_file, aoi_file)
            source_label = "upload manual"
        elif "integration_spi_df" in st.session_state:
            spi_df = st.session_state["integration_spi_df"]
            aoi_df = st.session_state["integration_aoi_df"]
            source_label = "integração direta (simulada)"
    except Exception as e:
        st.error(f"Falha na validação ou processamento dos dados: {str(e)}")
        return

    if spi_df is None or aoi_df is None:
        st.info(
            "Aguardando upload dos arquivos SPI e AOI, ou clique em \"Conectar às Máquinas\" "
            "para simular a integração direta."
        )
        return

    st.success(
        f"Fonte dos dados: **{source_label}** — SPI ({len(spi_df)} registros) | AOI ({len(aoi_df)} defeitos)"
    )

    if st.button("⚙️ Executar Diagnóstico de Causa Raiz", type="primary"):
        with st.spinner("Correlacionando bases de dados..."):
            results_df, exec_time = engine.run_diagnostics(spi_df, aoi_df)

        st.markdown("---")
        render_metrics_summary(results_df, exec_time)
        st.markdown("---")

        col_chart, col_empty = st.columns([2, 1])
        with col_chart:
            render_distribution_chart(results_df)

        render_diagnostic_table(results_df)

        # Exportação do relatório gerado
        csv_data = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar Relatório de Diagnóstico (.csv)",
            data=csv_data,
            file_name="diagnostico_causa_raiz_smt.csv",
            mime="text/csv",
        )


def render_manual_assistant_view() -> None:
    """Aba 2: Assistente técnico via LLM com memória volátil para manuais confidenciais."""
    st.subheader("🤖 Assistente Técnico de Processo (Memória Volátil)")
    st.write(
        "Consulte procedimentos de regulagem e manutenção em um ou mais manuais PDF, "
        "sem persistência em disco."
    )

    # Chave carregada de forma transparente via .env
    api_key = GEMINI_API_KEY

    if not api_key:
        st.error(
            "Chave de API do Gemini não encontrada. Defina a variável GEMINI_API_KEY no arquivo .env."
        )
        return

    pdf_files = st.file_uploader(
        "Manuais de Manutenção / Operação (.pdf)",
        type=["pdf"],
        key="upload_pdf",
        accept_multiple_files=True,
    )

    if pdf_files:
        st.caption(
            f"📎 {len(pdf_files)} manual(is) carregado(s): "
            + ", ".join(f.name for f in pdf_files)
        )
        user_query = st.text_area(
            "Descreva a falha ou informe o procedimento desejado:",
            placeholder="Ex: Qual o procedimento para limpeza e alinhamento do bocal da posicionadora?",
        )

        if st.button("🔍 Consultar Manuais", type="primary"):
            if not user_query.strip():
                st.warning("Por favor, digite uma dúvida antes de consultar.")
                return

            with st.spinner("Analisando manuais técnicos..."):
                try:
                    assistant = TechnicalManualAssistant(api_key=api_key)
                    response_text = assistant.query_manual(pdf_files, user_query)
                    st.markdown("### Parecer Técnico:")
                    st.write(response_text)
                except Exception as e:
                    st.error(f"Erro na comunicação com a API: {str(e)}")
    else:
        st.info("Faça o upload de um ou mais manuais técnicos em PDF para habilitar a consulta.")


def render_history_view(engine: SMTDeterministicEngine) -> None:
    """Aba 4: Histórico de diagnósticos, como se as máquinas estivessem
    permanentemente conectadas ao sistema."""
    st.subheader("📈 Histórico de Diagnósticos")
    st.write(
        "Visão de tendência de defeitos ao longo do tempo, simulando como o sistema "
        "acompanharia a produção caso estivesse permanentemente conectado às máquinas da linha."
    )
    st.caption(
        "🔧 Modo demonstração — os dados abaixo são gerados sinteticamente para representar "
        "o histórico que existiria com a integração contínua às máquinas de SPI e AOI."
    )

    days = st.slider("Período (dias)", min_value=7, max_value=30, value=14, step=1)

    if st.button("🔄 Gerar Histórico Simulado", type="primary") or "history_df" not in st.session_state:
        with st.spinner("Consolidando histórico de produção..."):
            st.session_state["history_df"] = generate_historical_diagnostics(engine, days=days)

    history_df = st.session_state["history_df"]

    if history_df.empty:
        st.info("Nenhum defeito simulado no período selecionado. Clique em \"Gerar Histórico Simulado\" novamente.")
        return

    st.markdown("---")
    render_history_summary(history_df)
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        render_history_trend_chart(history_df)
    with col2:
        render_distribution_chart(history_df)

    render_history_severity_chart(history_df)

    with st.expander("📋 Ver ocorrências detalhadas do período"):
        render_diagnostic_table(history_df)


def render_methodology_view() -> None:
    """Aba 3: Justificativa técnica e arquitetural para exibição à orientadora."""
    st.subheader("🏗️ Fundamentação Arquitetural do Sistema")
    st.markdown("""
    ### Princípios de Engenharia de Software Adotados:
    * **Separação de Responsabilidades (SoC):** Cada módulo possui um domínio estrito (Ingestão, Motor de Inferência, Serviços de IA, Interface).
    * **Algoritmo Determinístico Linear $O(N + M)$:** O cruzamento das bases de dados é realizado em memória via índices relacionais com busca em tempo constante $O(1)$ por registro.
    * **Integridade Numérica Absoluta:** O cálculo e classificação de limites de solda são processados via código Python estruturado, evitando alucinações matemáticas frequentes em LLMs generativos.
    * **Privacidade Industrial e Efemeridade:** Documentos confidenciais são carregados exclusivamente na memória volátil (RAM) e transmitidos via túnel seguro para o modelo de contexto estendido, sem persistência em banco de dados.
    * **Integração com Máquinas (Demonstração):** O botão "Conectar às Máquinas" simula, para fins didáticos, a leitura automática dos relatórios de SPI e AOI. Em produção, o mesmo contrato de dados (`core.ingestion`) seria alimentado por um conector real (pasta de rede/SFTP ou protocolo SECS/GEM), sem alterar o motor de diagnóstico.
    * **Histórico e Tendência (Demonstração):** A aba de Histórico simula uma série temporal de produção, aplicando o mesmo motor determinístico dia a dia. Em produção, essa série viria de um repositório real de diagnósticos já executados, sem alterar as regras de causa raiz nem a lógica de agregação.
    """)
