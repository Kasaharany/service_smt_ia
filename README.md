# Sistema de Análise de Causa Raiz para Defeitos em Linhas SMT (SPI & AOI)

Sistema desenvolvido para diagnóstico automatizado e rastreamento de defeitos no processo de manufatura de montagem em superfície (SMT). A solução integra e correlaciona dados de inspeção de pasta de solda (**SPI**) e inspeção óptica automatizada (**AOI**), reduzindo o tempo de análise de causa raiz e mitigando retrabalhos em ambiente de produção industrial.

---

## 🎯 Objetivo

Eliminar a análise manual reativa de falhas correlacionando desvios volumétricos/geométricos na impressão de solda (SPI) com os defeitos funcionais e estruturais detectados após o forno de refusão (AOI). O sistema gera diagnósticos determinísticos e reprodutíveis para ajustes imediatos na linha.

## ⚙️ Arquitetura e Funcionamento

1. **Ingestão de Dados:** Upload dos relatórios brutos de SPI e AOI (CSV), com validação de esquema (colunas obrigatórias) e normalização de tipos.
2. **Correlação Espacial & Paramétrica:** Mapeamento componente a componente por meio de identificadores de placa (`Panel_Barcode`) e referência de componente (`RefDes`), via junção relacional em memória.
3. **Mapeamento de Causa Raiz (Motor Determinístico):** Regras fixas e auditáveis que identificam se a falha no AOI (ex.: ponte, tombamento, deslocamento) decorreu de anomalias no SPI (ex.: volume excessivo, insuficiência de pasta) — sem depender de um modelo de IA generativa, garantindo reprodutibilidade e severidade classificada (Crítica/Alta/Média/Baixa).
4. **Assistência Técnica Contextual:** Chat opcional apoiado por IA generativa (Google Gemini), que analisa manuais técnicos (PDF) inteiramente em memória volátil — sem persistência em disco — e desacoplado da decisão de causa raiz.
5. **Visualização:** Dashboard Streamlit com métricas operacionais, gráfico de distribuição de causas por equipamento, tabela detalhada e exportação em CSV.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11+
* **Processamento e Análise de Dados:** Pandas
* **Interface / Dashboard:** Streamlit
* **Assistente Contextual (opcional):** Google Gemini API (`google-genai`)
* **Configuração:** `python-dotenv`

## 📁 Estrutura do Repositório

```text
├── app.py                  # Ponto de entrada da aplicação Streamlit
├── config/
│   ├── __init__.py
│   └── settings.py          # Variáveis de ambiente, limites de volume, contratos de colunas
├── core/
│   ├── __init__.py
│   ├── contracts.py          # Dataclasses: SPIDataRecord, AOIDataRecord, DiagnosticResult
│   ├── engine.py              # SMTDeterministicEngine: regras de causa raiz e correlação
│   └── ingestion.py           # Validação e carga dos relatórios SPI/AOI
├── services/
│   ├── __init__.py
│   └── llm_service.py         # TechnicalManualAssistant: consulta a manuais via Gemini
├── ui/
│   ├── __init__.py
│   ├── components.py          # Métricas, gráfico de distribuição e tabela de diagnóstico
│   └── views.py                # Abas: diagnóstico de linha, consulta a manuais, metodologia
├── data/                    # Dados brutos de SPI e AOI (ignorados pelo git)
├── .env.example             # Modelo de variáveis de ambiente (GEMINI_API_KEY)
├── requirements.txt          # Dependências do ambiente Python
└── README.md
```

## 🚀 Como Executar

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha GEMINI_API_KEY para habilitar o assistente de manuais
streamlit run app.py
```
