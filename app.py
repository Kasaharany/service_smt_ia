import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import json

# --- 1. Configuração da Interface Web ---
st.set_page_config(page_title="SMT Closed-Loop AI", page_icon="🏭", layout="wide")

# (Na Streamlit Cloud, deverá colocar a sua chave em "Settings > Secrets" em vez de a expor aqui)
# genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
# modelo = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. O Motor de Dados (Backend Blindado) ---
def processar_closed_loop(ficheiro_spi, ficheiro_aoi):
    # Proteção 1: Normalização de formatação regional (força a leitura da vírgula como decimal)
    df_spi = pd.read_csv(ficheiro_spi, decimal=',')
    df_aoi = pd.read_csv(ficheiro_aoi, decimal=',')
    
    # Garante de forma forçada que a coluna de Volume é sempre um número matemático
    if 'Volume(%)' in df_spi.columns:
        df_spi['Volume(%)'] = pd.to_numeric(df_spi['Volume(%)'].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Descarta linhas onde a conversão falhou (evitando que o sistema vá abaixo)
    df_spi = df_spi.dropna(subset=['Volume(%)'])
    
    # Cruzamento exato das placas e componentes
    df_cruzado = pd.merge(df_spi, df_aoi, on=['Panel_Barcode', 'RefDes'], how='inner')
    df_falhas_reais = df_cruzado[df_cruzado['Result_AOI'] != 'PASS']
    
    return df_falhas_reais

# --- 3. O Motor de Inteligência Artificial ---
def gerar_diagnostico_ia(df_cruzado):
    # Proteção 2: Contrato de Dados Rigoroso (JSON forçado)
    system_prompt = """
    You are a Senior SMT Process Engineer AI. 
    Analyze the merged SPI and AOI data to provide a root cause analysis.
    Return ONLY a valid JSON array of objects. Do not use markdown, do not say hello.
    Each object must have exactly two keys: "Component" and "Diagnosis".
    Example: [{"Component": "U1", "Diagnosis": "Root cause: Printer. Check stencil."}]
    
    Rules:
    1. If AOI defect is 'Missing' or 'Tombstone' AND SPI Volume < 50%, isolate root cause to Printer.
    2. If AOI defect is 'Shift' AND SPI Volume > 90%, isolate root cause to Pick & Place.
    """
    
    # Empacotar todos os dados com defeito num único pedido para poupar tokens
    dados_lista = []
    for index, linha in df_cruzado.iterrows():
        dados_lista.append(f"Component: {linha['RefDes']} | SPI Volume: {linha['Volume(%)']}% | AOI Defect: {linha['Defect_Type']}")
    
    prompt_final = f"{system_prompt}\n\nMachine Data to analyze:\n" + "\n".join(dados_lista)
    
    # Proteção 3: Sistema de Tentativas (Retry) para resiliência de rede
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            # --- CÓDIGO REAL DA API (Descomentar para a versão final de produção) ---
            # resposta = modelo.generate_content(
            #     prompt_final,
            #     generation_config=genai.GenerationConfig(response_mime_type="application/json")
            # )
            # diagnósticos_ia = json.loads(resposta.text)
            
            # --- SIMULAÇÃO LOCAL (Mantido para poder testar sem gastar chave de API) ---
            time.sleep(1.5) # Simula o atraso da internet
            diagnósticos_ia = []
            for index, linha in df_cruzado.iterrows():
                comp = linha['RefDes']
                vol = float(linha['Volume(%)'])
                defeito = linha['Defect_Type']
                
                if vol < 50 and defeito in ['Missing', 'Tombstone']:
                    diag = f"Root cause: Printer. Insufficient paste (Vol {vol}%). Inspect stencil apertures."
                elif vol > 90 and defeito == 'Shift':
                    diag = f"Root cause: Pick & Place. SPI nominal (Vol {vol}%). Verify nozzle vacuum."
                else:
                    diag = "Root cause: Printer/Reflow. Investigate parameters."
                diagnósticos_ia.append({"Component": comp, "Diagnosis": diag})
            # --- FIM DA SIMULAÇÃO ---

            # Organizar a tabela final bonita para o cliente
            relatorio_final = []
            for index, linha in df_cruzado.iterrows():
                comp = linha['RefDes']
                # Cruza o JSON da IA com a linha do Pandas
                texto_ia = next((item['Diagnosis'] for item in diagnósticos_ia if item['Component'] == comp), "Diagnosis error")
                
                relatorio_final.append({
                    'Componente': comp, 
                    'Volume SPI': f"{linha['Volume(%)']}%", 
                    'Defeito AOI': linha['Defect_Type'], 
                    'Diagnóstico do Especialista (IA)': texto_ia
                })
                
            return pd.DataFrame(relatorio_final)

        except Exception as erro_rede:
            if tentativa < tentativas - 1:
                time.sleep(2) # Espera 2 segundos silenciosamente e tenta de novo
                continue
            else:
                # Fallback se a API estiver em baixo (não destrói a aplicação)
                st.error("Falha de comunicação com o servidor de IA. A gerar relatório base.")
                return df_cruzado[['RefDes', 'Volume(%)', 'Defect_Type']]

# --- 4. Desenho do Ecrã (Frontend) ---
st.title("🏭 Assistente de Diagnóstico SMT (Closed-Loop)")
st.markdown("Submeta os relatórios da impressora (SPI) e da inspeção final (AOI) para encontrar a causa raiz das falhas de produção.")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Dados da SPI")
    upload_spi = st.file_uploader("Carregar ficheiro CSV da SPI", type=['csv'])

with col2:
    st.subheader("2. Dados da AOI")
    upload_aoi = st.file_uploader("Carregar ficheiro CSV da AOI", type=['csv'])

st.divider()

if upload_spi is not None and upload_aoi is not None:
    if st.button("Executar Análise Closed-Loop 🧠", type="primary"):
        
        with st.spinner("A cruzar dados e a processar inteligência artificial..."):
            df_anomalias = processar_closed_loop(upload_spi, upload_aoi)
            
            if not df_anomalias.empty:
                st.success("Dados cruzados com sucesso! A extrair diagnósticos...")
                relatorio_df = gerar_diagnostico_ia(df_anomalias)
                
                st.subheader("📋 Relatório de Ação para a Manutenção")
                # Exibição alargada e adaptativa no navegador
                st.dataframe(relatorio_df, use_container_width=True)
            else:
                st.info("Excelente! O lote cruzado não apresenta anomalias na inspeção final.")
else:
    st.warning("Por favor, carregue ambos os ficheiros (SPI e AOI) para iniciar o cruzamento.")
