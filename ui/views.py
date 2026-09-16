"""Views (abas) da interface Streamlit."""

from __future__ import annotations

import streamlit as st
import PyPDF2

from core.engine import SMTDeterministicEngine

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - dependência opcional em runtime
    genai = None


def render_diagnostic_view(engine: SMTDeterministicEngine) -> None:
    """Aba de diagnóstico de linha: correlação determinística SPI × AOI."""
    st.markdown(
        "Submeta os relatórios da impressora (SPI) e da inspeção final (AOI) "
        "para isolar, por correlação determinística, a máquina responsável pelo defeito."
    )

    col_spi, col_aoi = st.columns(2)
    with col_spi:
        upload_spi = st.file_uploader("Carregar CSV da SPI", type=["csv"])
    with col_aoi:
        upload_aoi = st.file_uploader("Carregar CSV da AOI", type=["csv"])

    if upload_spi is None or upload_aoi is None:
        st.info("Carregue os dois relatórios para iniciar a análise.")
        return

    if not st.button("Executar Análise 🔎", type="primary"):
        return

    with st.spinner("Correlacionando dados de inspeção..."):
        try:
            relatorio_df = engine.run(upload_spi, upload_aoi)
        except ValueError as erro:
            st.error(f"Erro ao processar os relatórios: {erro}")
            return

    if relatorio_df.empty:
        st.success("Nenhuma anomalia crítica detetada neste lote.")
        return

    st.warning(f"{len(relatorio_df)} anomalia(s) encontrada(s). Consulte o diagnóstico abaixo.")
    st.dataframe(relatorio_df, use_container_width=True)

    csv = relatorio_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar relatório (CSV)",
        data=csv,
        file_name="diagnostico_causa_raiz.csv",
        mime="text/csv",
    )


def render_manual_assistant_view() -> None:
    """Aba de consulta a manuais: assistente técnico contextual apoiado por IA."""
    st.markdown(
        "🔒 **Área restrita à equipa de Engenharia.** Converse com o assistente "
        "ou carregue um manual técnico (PDF) para consulta contextual."
    )

    modelo = _get_modelo()
    if modelo is None:
        st.error("⚠️ Atenção: a chave GOOGLE_API_KEY não está configurada nos Secrets.")

    if "mensagens_chat" not in st.session_state:
        st.session_state.mensagens_chat = []

    ficheiro_manual = st.file_uploader("Carregar Base de Conhecimento (PDF)", type=["pdf"])
    contexto_pdf = ""
    if ficheiro_manual is not None:
        with st.spinner("A ler documento técnico..."):
            contexto_pdf = _extrair_texto_pdf(ficheiro_manual)
            st.success("Documento carregado na memória temporária.")

    st.divider()

    caixa_chat = st.container(height=400)
    with caixa_chat:
        for mensagem in st.session_state.mensagens_chat:
            with st.chat_message(mensagem["role"]):
                st.markdown(mensagem["content"])

    pergunta = st.chat_input("Diga 'oi' ou insira um código de erro para debug...")
    if not pergunta:
        return

    st.session_state.mensagens_chat.append({"role": "user", "content": pergunta})
    with caixa_chat:
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("A pensar..."):
                resposta = _gerar_resposta(modelo, contexto_pdf)
                st.markdown(resposta)
                st.session_state.mensagens_chat.append({"role": "assistant", "content": resposta})


def render_methodology_view() -> None:
    """Aba de arquitetura e metodologia do sistema."""
    st.markdown(
        """
### 🔬 Arquitetura & Metodologia

O sistema é dividido em dois motores independentes, cada um com um propósito distinto:

**1. Motor Determinístico de Correlação** (`core.engine.SMTDeterministicEngine`)
- Recebe os relatórios brutos de SPI (impressão de pasta de solda) e AOI (inspeção óptica).
- Correlaciona os dados por placa (`Panel_Barcode`) e componente (`RefDes`).
- Aplica regras fixas e auditáveis (limiares de volume × tipo de defeito) para apontar a
  causa raiz mais provável — sem depender de um modelo de IA generativa.
- Garante que o mesmo par de relatórios produza sempre o mesmo diagnóstico (reprodutibilidade).

**2. Assistente Técnico Contextual** (`ui.views.render_manual_assistant_view`)
- Camada opcional apoiada por IA generativa (Google Gemini) para consulta a manuais
  técnicos em PDF e apoio à engenharia em cenários não cobertos pelas regras determinísticas.
- Não participa da decisão de causa raiz do motor principal — é puramente consultiva.

Essa separação evita que respostas probabilísticas de um LLM influenciem o diagnóstico
de causa raiz, mantendo o núcleo do sistema rastreável, auditável e reproduzível.
        """
    )


def _get_modelo():
    if genai is None:
        return None
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        return genai.GenerativeModel("gemini-2.5-flash")
    except Exception:
        return None


def _extrair_texto_pdf(ficheiro_pdf) -> str:
    leitor = PyPDF2.PdfReader(ficheiro_pdf)
    texto = ""
    for pagina in leitor.pages:
        conteudo = pagina.extract_text()
        if conteudo:
            texto += conteudo + "\n"
    return texto


def _gerar_resposta(modelo, contexto_pdf: str) -> str:
    if modelo is None:
        return "Chave de API em falta. Configure GOOGLE_API_KEY nos Secrets do Streamlit."

    instrucoes = (
        "És um Engenheiro SMT Sênior. Se o técnico disser apenas 'oi', 'olá' ou um "
        "cumprimento, responde de forma natural e educada. Se for uma dúvida técnica, "
        "responde em tópicos curtos e diretos."
    )
    if contexto_pdf:
        instrucoes += f"\n\nBaseia-te NESTE MANUAL para responder: {contexto_pdf[:15000]}"

    historico = "\n".join(
        f"{msg['role']}: {msg['content']}" for msg in st.session_state.mensagens_chat[-5:]
    )
    prompt_final = f"{instrucoes}\n\nHistórico da conversa:\n{historico}\n\nResponde à última mensagem."

    try:
        resposta_ia = modelo.generate_content(prompt_final)
        return resposta_ia.text
    except Exception as erro:
        return f"Erro de comunicação com o servidor de IA: {erro}"
