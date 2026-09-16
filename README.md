# Sistema de Análise de Causa Raiz para Defeitos em Linhas SMT (SPI & AOI)

Sistema desenvolvido para diagnóstico automatizado e rastreamento de defeitos no processo de manufatura de montagem em superfície (SMT). A solução integra e correlaciona dados de inspeção de pasta de solda (**SPI**) e inspeção óptica automatizada (**AOI**), reduzindo o tempo de análise de causa raiz e mitigando retrabalhos em ambiente de produção industrial.

---

## 🎯 Objetivo

Eliminar a análise manual reativa de falhas correlacionando desvios volumétricos/geométricos na impressão de solda (SPI) com os defeitos funcionais e estruturais detectados após o forno de refusão (AOI). O sistema gera diagnósticos determinísticos e reprodutíveis para ajustes imediatos na linha.

## ⚙️ Arquitetura e Funcionamento

1. **Ingestão de Dados:** Upload dos relatórios brutos de SPI e AOI (CSV).
2. **Correlação Espacial & Paramétrica:** Mapeamento componente a componente por meio de identificadores de placa (`Panel_Barcode`) e referência de componente (`RefDes`).
3. **Mapeamento de Causa Raiz (Motor Determinístico):** Regras fixas e auditáveis que identificam se a falha no AOI (ex.: ponte, tombamento, deslocamento) decorreu de anomalias no SPI (ex.: volume excessivo, insuficiência de pasta) — sem depender de um modelo de IA generativa, garantindo reprodutibilidade.
4. **Assistência Técnica Contextual:** Chat opcional apoiado por IA generativa (Google Gemini) para consulta a manuais técnicos (PDF), desacoplado da decisão de causa raiz.
5. **Visualização:** Dashboard Streamlit com relatórios estruturados e exportação em CSV para tomada de decisão rápida da engenharia de processos.

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.11+
* **Processamento e Análise de Dados:** Pandas
* **Interface / Dashboard:** Streamlit
* **Assistente Contextual (opcional):** Google Gemini API, PyPDF2

## 📁 Estrutura do Repositório

```text
├── app.py                # Ponto de entrada da aplicação Streamlit
├── core/
│   ├── __init__.py
│   └── engine.py          # SMTDeterministicEngine: ingestão, correlação e regras de causa raiz
├── ui/
│   ├── __init__.py
│   └── views.py            # Abas: diagnóstico de linha, consulta a manuais, metodologia
├── data/                  # Dados brutos de SPI e AOI (ignorados pelo git)
├── requirements.txt        # Dependências do ambiente Python
└── README.md
```

## 🚀 Como Executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para habilitar o assistente técnico contextual, configure a chave `GOOGLE_API_KEY` nos Secrets do Streamlit.
