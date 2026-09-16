import streamlit as st
import pandas as pd

from config.settings import GEMINI_API_KEY
from core.engine import SMTDeterministicEngine
from core.ingestion import ingest_inspection_datasets
from services.llm_service import TechnicalManualAssistant
from ui.components import (
    render_diagnostic_table,
    render_distribution_chart,
    render_metrics_summary,
)


def render_diagnostic_view(engine: SMTDeterministicEngine) -> None:
    """Aba 1: Ingestão de relatórios e execução do motor determinístico."""
    st.subheader("Ingestão de Dados de Inspeção")
    st.write(
        "Carregue os relatórios de medição volumétrica (SPI) e detecção de defeitos pós-refusão (AOI)."
    )

    col1, col2 = st.columns(2)
    with col1:
        spi_file = st.file_uploader(
            "Relatório SPI (.csv)", type=["csv"], key="upload_spi"
        )
    with col2:
        aoi_file = st.file_uploader(
            "Relatório AOI (.csv)", type=["csv"], key="upload_aoi"
        )

    if spi_file and aoi_file:
        try:
            spi_df, aoi_df = ingest_inspection_datasets(spi_file, aoi_file)
            st.success(
                f"Arquivos validados: SPI ({len(spi_df)} registros) | AOI ({len(aoi_df)} defeitos)"
            )

            if st.button("Executar Diagnóstico de Causa Raiz", type="primary"):
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
                    label="Baixar Relatório de Diagnóstico (.csv)",
                    data=csv_data,
                    file_name="diagnostico_causa_raiz_smt.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"Falha na validação ou processamento dos dados: {str(e)}")
    else:
        st.info("Aguardando upload dos arquivos SPI e AOI em formato CSV.")


def render_manual_assistant_view() -> None:
    """Aba 2: Assistente técnico via LLM com memória volátil para manuais confidenciais."""
    st.subheader("Assistente Técnico de Processo (Memória Volátil)")
    st.write(
        "Consulte procedimentos de regulagem e manutenção em manuais PDF sem persistência em disco."
    )

    # Chave carregada de forma transparente via .env
    api_key = GEMINI_API_KEY

    if not api_key:
        st.error(
            "Chave de API do Gemini não encontrada. Defina a variável GEMINI_API_KEY no arquivo .env."
        )
        return

    pdf_file = st.file_uploader(
        "Manual de Manutenção / Operação (.pdf)", type=["pdf"], key="upload_pdf"
    )

    if pdf_file:
        user_query = st.text_area(
            "Descreva a falha ou informe o procedimento desejado:",
            placeholder="Ex: Qual o procedimento para limpeza e alinhamento do bocal da posicionadora?",
        )

        if st.button("Consultar Manual", type="primary"):
            if not user_query.strip():
                st.warning("Por favor, digite uma dúvida antes de consultar.")
                return

            with st.spinner("Analisando manual técnico..."):
                try:
                    assistant = TechnicalManualAssistant(api_key=api_key)
                    response_text = assistant.query_manual(pdf_file, user_query)
                    st.markdown("### Parecer do Manual Técnico:")
                    st.write(response_text)
                except Exception as e:
                    st.error(f"Erro na comunicação com a API: {str(e)}")
    else:
        st.info("Faça o upload do manual técnico em PDF para habilitar a consulta.")


def render_methodology_view() -> None:
    """Aba 3: Justificativa técnica e arquitetural para exibição à orientadora."""
    st.subheader("Fundamentação Arquitetural do Sistema")
    st.markdown("""
    ### Princípios de Engenharia de Software Adotados:
    * **Separação de Responsabilidades (SoC):** Cada módulo possui um domínio estrito (Ingestão, Motor de Inferência, Serviços de IA, Interface).
    * **Algoritmo Determinístico Linear $O(N + M)$:** O cruzamento das bases de dados é realizado em memória via índices relacionais com busca em tempo constante $O(1)$ por registro.
    * **Integridade Numérica Absoluta:** O cálculo e classificação de limites de solda são processados via código Python estruturado, evitando alucinações matemáticas frequentes em LLMs generativos.
    * **Privacidade Industrial e Efemeridade:** Documentos confidenciais são carregados exclusivamente na memória volátil (RAM) e transmitidos via túnel seguro para o modelo de contexto estendido, sem persistência em banco de dados.
    """)
