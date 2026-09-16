"""Simulação de integração direta com as máquinas de SPI e AOI da linha.

Em um ambiente de produção real, este módulo seria substituído por um
conector real (pasta de rede, FTP/SFTP ou protocolo industrial SECS/GEM)
que lê os relatórios exportados automaticamente pelas máquinas. Aqui, ele
gera um lote de amostra para fins de demonstração da interface, reutilizando
o mesmo caminho de validação (`core.ingestion`) usado no upload manual.
"""

from __future__ import annotations

import random
import string
from io import StringIO
from typing import Tuple

import pandas as pd

from core.ingestion import ingest_inspection_datasets

_DEFECT_TYPES = ["Missing", "Shift", "Tombstone", "Bridge"]


def _random_barcode() -> str:
    return "PNL-" + "".join(random.choices(string.digits, k=5))


def pull_from_spi_machine(n_boards: int = 3, components_per_board: int = 6) -> pd.DataFrame:
    """Simula a leitura do relatório de volume de pasta direto na máquina de SPI."""
    records = []
    for _ in range(n_boards):
        barcode = _random_barcode()
        for i in range(components_per_board):
            records.append({
                "Panel_Barcode": barcode,
                "RefDes": f"R{i + 1}",
                "Volume_Percent": round(random.uniform(20, 180), 1),
            })
    return pd.DataFrame(records)


def pull_from_aoi_machine(spi_df: pd.DataFrame, defect_rate: float = 0.4) -> pd.DataFrame:
    """Simula a leitura do relatório de defeitos direto na máquina de AOI,
    reaproveitando as mesmas placas/componentes inspecionados na SPI."""
    records = []
    for _, row in spi_df.iterrows():
        if random.random() < defect_rate:
            records.append({
                "Panel_Barcode": row["Panel_Barcode"],
                "RefDes": row["RefDes"],
                "Defect_Type": random.choice(_DEFECT_TYPES),
            })
    return pd.DataFrame(records, columns=["Panel_Barcode", "RefDes", "Defect_Type"])


def simulate_machine_integration() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Ponto de entrada único: simula a conexão direta às duas máquinas da
    linha e retorna os DataFrames já validados pelo pipeline de ingestão.
    """
    spi_df = pull_from_spi_machine()
    aoi_df = pull_from_aoi_machine(spi_df)

    spi_csv = StringIO(spi_df.to_csv(index=False))
    aoi_csv = StringIO(aoi_df.to_csv(index=False))
    return ingest_inspection_datasets(spi_csv, aoi_csv)
