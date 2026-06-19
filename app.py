import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import json
import PyPDF2

# --- 1. Configuração da Interface Web ---
st.set_page_config(page_title="SMT Closed-Loop AI", page_icon="🏭", layout="wide")

# (Na Streamlit Cloud, deverá colocar a sua chave em "Settings > Secrets")
# genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
# modelo = genai.GenerativeModel('gemini-1.5-flash')

# Inicializar a memória do Chat (Para não esquecer a conversa ao atualizar o ecrã)
if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

# --- 2. Funções do Backend (Blindadas) ---
def processar_closed_loop(ficheiro_spi, ficheiro_aoi):
    df_spi = pd.read_csv(ficheiro_spi, decimal=',')
    df_aoi = pd.read_csv(ficheiro_aoi, decimal=',')
    if 'Volume(%)' in df_spi.columns:
        df_spi['Volume(%)'] = pd.to_numeric(df_spi['Volume(%)'].astype(str).str.replace(',', '.'), errors='coerce')
    df_spi = df_spi.dropna(subset=['Volume(%)'])
    df_cruzado = pd.merge(df_spi, df_aoi, on=['Panel_Barcode', 'RefDes'], how='inner')
    return df_cruzado[df_cruzado['Result_AOI'] != 'PASS']

def gerar_diagnostico_ia(df_cruzado):
    time.sleep(1.5) # Simulação (substituir pela chamada real da API no futuro)
    relatorio_final = []
    for index, linha in df_cruzado.iterrows():
        comp = linha['RefDes']
        vol = float(linha['Volume(%)'])
        defeito = linha['Defect_Type']
        
        if vol < 50 and defeito in ['Missing', 'Tombstone']:
            diag = f"Printer Issue (Vol {vol}%). Inspect stencil."
        elif vol > 90 and defeito == 'Shift':
            diag = f"Pick & Place Issue (Vol {vol}%). Verify nozzle."
        else:
            diag = "Investigate thermal profile."
            
        relatorio_final.append({
            'Componente': comp, 
            'Volume SPI': f"{vol}%", 
            'Defeito AOI': defeito, 
            'Diagnóstico': diag
        })
    return pd.DataFrame(relatorio_final)

def extrair_texto_pdf(ficheiro_pdf):
    leitor = PyPDF2.PdfReader(ficheiro_pdf)
    texto = ""
    for pagina in leitor.pages:
        if pagina.extract_text():
            texto += pagina.extract_text() + "\n"
    return texto

# --- 3. Desenho do Ecrã (Frontend com Abas) ---
st.title("🏭 Assistente de Diagnóstico SMT (Closed-Loop)")

# Criar as abas principais de navegação
aba1, aba2 = st.tabs(["📊 1. Análise Closed-Loop", "💬 2. Assistente de Manutenção Especialista"])

# ==========================================
# ABA 1: CRUZAMENTO DE DADOS (O que já tínhamos)
# ==========================================
with aba1:
    st.markdown("Submeta os relatórios da impressora (SPI) e da inspeção final (AOI) para isolar a máquina com defeito.")
    col1, col2 = st.columns(2)
    with col1:
        upload_spi = st.file_uploader("Carregar CSV da SPI", type=['csv'])
    with col2:
        upload_aoi = st.file_uploader("Carregar CSV da AOI", type=['csv'])

    if upload_spi is not None and upload_aoi is not None:
        if st.button("Executar Análise 🧠", type="primary"):
            with st.spinner("A processar os dados de inspeção..."):
                df_anomalias = processar_closed_loop(upload_spi, upload_aoi)
                if not df_anomalias.empty:
                    st.success("Causa raiz encontrada! Consulte a tabela e utilize a Aba 2 para saber como reparar.")
                    relatorio_df = gerar_diagnostico_ia(df_anomalias)
                    st.dataframe(relatorio_df, use_container_width=True)
                else:
                    st.info("Nenhuma anomalia crítica detetada neste lote.")

# ==========================================
# ABA 2: CHAT COM INTELIGÊNCIA ARTIFICIAL (Manuais da Fábrica)
# ==========================================
with aba2:
    st.markdown("Carregue o manual da máquina (PDF) ou registos de engenharia. A IA irá basear-se neles para guiar a sua manutenção.")
    
    # Upload do Manual
    ficheiro_manual = st.file_uploader("Carregar Base de Conhecimento (PDF)", type=['pdf'])
    contexto_pdf = ""
    
    if ficheiro_manual is not None:
        with st.spinner("A ler o manual da máquina..."):
            contexto_pdf = extrair_texto_pdf(ficheiro_manual)
            st.success(f"O manual '{ficheiro_manual.name}' foi memorizado. Pode fazer a sua pergunta.")
    
    st.divider()

    # Desenhar o histórico do chat no ecrã
    for mensagem in st.session_state.mensagens_chat:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

    # A caixa onde o técnico escreve a pergunta
    pergunta = st.chat_input("Ex: Qual é o procedimento para ajustar a pressão do rodo?")

    if pergunta:
        # Mostra a pergunta do técnico
        st.session_state.mensagens_chat.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)

        # Lógica de resposta da IA
        with st.chat_message("assistant"):
            with st.spinner("A consultar o manual e a formular resposta..."):
                
                # --- CÓDIGO DA API REAL (Descomentar futuramente) ---
                # prompt_rag = f"És um engenheiro SMT. Usa este manual para responder: {contexto_pdf[:15000]}\n\nPergunta: {pergunta}"
                # resposta = modelo.generate_content(prompt_rag).text
                
                # --- SIMULAÇÃO (Para testar o visual da aplicação) ---
                time.sleep(1)
                if ficheiro_manual:
                    resposta = f"A analisar o manual carregado: Com base no protocolo padrão de manutenção SMT, recomendo parar a linha S01 imediatamente e verificar a calibração física, conforme o capítulo 4 da documentação técnica."
                else:
                    resposta = "Não carregou nenhum manual específico, mas baseado nos padrões globais da indústria SMT, recomendo que acione a equipa de engenharia para calibrar os parâmetros de offset."
                
                st.markdown(resposta)
                # Guarda a resposta na memória
                st.session_state.mensagens_chat.append({"role": "assistant", "content": resposta})
