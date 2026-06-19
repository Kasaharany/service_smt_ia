# 🏭 SMT Closed-Loop AI Diagnostics
An automated micro-SaaS designed for the Surface Mount Technology (SMT) industry to perform root-cause analysis on production failures by correlating SPI (Solder Paste Inspection) and AOI (Automated Optical Inspection) data.

## 🚀 The Problem it Solves
Process engineers waste hours manually cross-referencing false calls and defects from inspection machinery (like Koh Young, Omron, etc.). This tool automates the process using an LLM-powered engine.

## ⚙️ How it Works
1. **Data Ingestion:** Upload raw CSV logs from both SPI and AOI.
2. **Mathematical Correlation:** The system uses Pandas to perfectly match Panel Barcodes and Reference Designators.
3. **AI Root-Cause Isolation:** Using Google's Gemini API, the tool mathematically separates Printer issues (e.g., stencil clogging) from Pick & Place issues (e.g., nozzle vacuum failure).
4. **Actionable Output:** Delivers a clear, English-based maintenance instruction matrix.

## 🛠️ Tech Stack
- **Backend:** Python, Pandas
- **AI Engine:** Google Gemini Pro API
- **Frontend/Deployment:** Streamlit Community Cloud
