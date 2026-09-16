import streamlit as st

# CSS estático definido pelo próprio aplicativo (nunca contém texto vindo do
# usuário, de um CSV carregado ou da resposta da IA) — seguro usar
# unsafe_allow_html aqui, ao contrário de conteúdo gerado dinamicamente.
_CUSTOM_CSS = """
<style>
/* Botões: feedback tátil ao passar o mouse e ao clicar */
div.stButton > button, div.stDownloadButton > button {
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0, 194, 168, 0.35);
}
div.stButton > button:active, div.stDownloadButton > button:active {
    transform: translateY(0) scale(0.97);
    box-shadow: 0 1px 4px rgba(0, 194, 168, 0.25);
}

/* Cards de métrica com leve elevação ao passar o mouse */
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    transition: transform 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    background-color: rgba(0, 194, 168, 0.08);
    box-shadow: 0 6px 16px rgba(0, 194, 168, 0.15);
}

/* Abas: transição suave de cor ao trocar */
button[data-baseweb="tab"] {
    transition: color 0.2s ease;
}

/* Fade-in suave do conteúdo principal a cada rerun/troca de aba */
div.block-container {
    animation: fadeIn 0.4s ease;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Scrollbar customizada, alinhada à cor de destaque do tema */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: rgba(0, 194, 168, 0.4); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 194, 168, 0.7); }

/* Sidebar: transição suave ao expandir/colapsar */
section[data-testid="stSidebar"] {
    transition: width 0.2s ease, margin-left 0.2s ease;
}

/* Mobile: sidebar não deve ultrapassar a largura útil da tela */
@media (max-width: 640px) {
    section[data-testid="stSidebar"] {
        width: 85vw !important;
        min-width: 85vw !important;
    }
}
</style>
"""


def inject_custom_theme() -> None:
    """Aplica animações e ajustes visuais globais definidos por este app.

    Conteúdo 100% estático (sem interpolação de dados do usuário/IA) —
    diferente do texto exibido no assistente técnico, que nunca usa
    `unsafe_allow_html`.
    """
    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)
