import sys
from pathlib import Path

# Garante que os pacotes do projeto (core, services, ui, config) sejam
# importáveis a partir da raiz do repositório, independente de como o
# pytest é invocado.
sys.path.insert(0, str(Path(__file__).resolve().parent))
