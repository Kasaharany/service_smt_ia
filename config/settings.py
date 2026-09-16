import os
from pathlib import Path

from dotenv import load_dotenv

# Localiza o arquivo .env na raiz do projeto com caminho absoluto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

# Limites operacionais de processo SMT para pasta de solda (volume percentual)
MIN_SOLDER_VOLUME_PERCENT: float = 50.0   # Abaixo disso: subdeposição severa (Stencil Printer)
MAX_SOLDER_VOLUME_PERCENT: float = 150.0  # Acima disso: sobredeposição severa (Risco de curto)

# Configurações do modelo de linguagem (Gemini)
DEFAULT_GEMINI_MODEL: str = "gemini-3.6-flash"
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Contratos de colunas obrigatórias nos arquivos de inspeção
REQUIRED_SPI_COLUMNS: set = {
    "Panel_Barcode",
    "RefDes",
    "Volume_Percent"
}

REQUIRED_AOI_COLUMNS: set = {
    "Panel_Barcode",
    "RefDes",
    "Defect_Type"
}
