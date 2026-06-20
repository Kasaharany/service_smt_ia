import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import json
import PyPDF2

# --- 1. Configuração da Interface Web ---
st.set_page_config(page_title="SMT Closed-Loop AI", page_icon="🏭", layout="wide")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelo = genai.GenerativeModel('gemini-1.5-flash')
    ia_pronta = True
except Exception:
    ia_pronta = False

if "mensagens_chat" not in st.session_state:
    st.session_state.mensagens_chat = []

# --- 2. Funções do Backend ---
def processar_closed_loop(ficheiro_spi, ficheiro_aoi):
    df_spi = pd.read_csv(ficheiro_spi, decimal=',')
    df_aoi = pd.read_csv(ficheiro_aoi, decimal=',')
    if 'Volume(%)' in df_spi.columns:
        df_spi['Volume(%)'] = pd.to_numeric(df_spi['Volume(%)'].astype(str).str.replace(',', '.'), errors='coerce')
    df_spi = df_spi.dropna(subset=['Volume(%)'])
    df_cruzado = pd.merge(df_spi, df_aoi, on=['Panel_Barcode', 'RefDes'], how='inner')
    return df_cruzado[df_cruzado['Result_AOI'] != 'PASS']

def gerar_diagnostico_ia(df_cruzado):
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

# --- 3. Desenho do Ecrã ---
st.title("🏭 Assistente de Diagnóstico SMT (Closed-Loop)")

aba1, aba2 = st.tabs(["📊 1. Análise Closed-Loop", "💬 2. Portal do Técnico (Base de Conhecimento)"])

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
                    st.success("Causa raiz encontrada! Consulte a tabela.")
                    relatorio_df = gerar_diagnostico_ia(df_anomalias)
                    st.dataframe(relatorio_df, use_container_width=True)
                else:
                    st.info("Nenhuma anomalia crítica detetada neste lote.")

with aba2:
    st.markdown("🔒 **Área restrita à equipa de Engenharia.** Converse com a IA ou carregue um manual para debug.")
    
    if not ia_pronta:
        st.error("⚠️ Atenção: A chave da API não está configurada nos Secrets.")
    
    ficheiro_manual = st.file_uploader("Carregar Base de Conhecimento (PDF)", type=['pdf'])
    contexto_pdf = ""
    
    if ficheiro_manual is not None:
        with st.spinner("A ler documento técnico..."):
            contexto_pdf = extrair_texto_pdf(ficheiro_manual)
            st.success("Documento carregado na memória temporária.")
    
    st.divider()

    caixa_chat = st.container(height=400)
    
    with caixa_chat:
        for mensagem in st.session_state.mensagens_chat:
            with st.chat_message(mensagem["role"]):
                st.markdown(mensagem["content"])

    pergunta = st.chat_input("Diga 'oi' ou insira um código de erro para debug...")

    if pergunta:
        st.session_state.mensagens_chat.append({"role": "user", "content": pergunta})
        with caixa_chat:
            with st.chat_message("user"):
                st.markdown(pergunta)

            with st.chat_message("assistant"):
                with st.spinner("A pensar..."):
                    if ia_pronta:
                        try:
                            instrucoes = "És um Engenheiro SMT Sênior. Se o técnico disser apenas 'oi', 'olá' ou um cumprimento, responde de forma natural e educada. Se for uma dúvida técnica, responde em tópicos curtos e diretos."
                            
                            if ficheiro_manual:
                                instrucoes += f"\n\nBaseia-te NESTE MANUAL para responder: {contexto_pdf[:15000]}"
                            
                            historico = ""
                            for msg in st.session_state.mensagens_chat[-5:]:
                                historico += f"{msg['role']}: {msg['content']}\n"
                            
                            prompt_final = f"{instrucoes}\n\nHistórico da conversa:\n{historico}\n\nResponde à última mensagem."
                            
                            resposta_ia = modelo.generate_content(prompt_final)
                            resposta = resposta_ia.text
                            
                        except Exception as e:
                            resposta = f"Erro de comunicação com o servidor de IA: {e}"
                    else:
                        resposta = "Chave de API em falta. Vá aos Secrets do Streamlit."
                    
                    st.markdown(resposta)
                    st.session_state.mensagens_chat.append({"role": "assistant", "content": resposta})
