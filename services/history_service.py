"""Simulação de histórico de diagnósticos, como se o sistema estivesse
permanentemente conectado às máquinas de SPI e AOI da linha.

Reaproveita os mesmos geradores de dados sintéticos usados na integração
sob demanda (`services.machine_integration`), aplicando-os retroativamente
a uma janela de dias para compor uma série temporal de produção e permitir
a análise de tendência de causa raiz ao longo do tempo.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from core.engine import SMTDeterministicEngine
from services.machine_integration import pull_from_aoi_machine, pull_from_spi_machine


def generate_historical_diagnostics(
    engine: SMTDeterministicEngine, days: int = 14
) -> pd.DataFrame:
    """Gera `days` dias de produção sintética e executa o motor determinístico
    em cada lote, retornando o histórico consolidado com uma coluna `Data`.
    """
    daily_reports = []
    today = date.today()

    for offset in range(days):
        report_date = today - timedelta(days=days - 1 - offset)

        spi_df = pull_from_spi_machine()
        aoi_df = pull_from_aoi_machine(spi_df)

        results_df, _ = engine.run_diagnostics(spi_df, aoi_df)
        if results_df.empty:
            continue

        results_df.insert(0, "Data", pd.Timestamp(report_date))
        daily_reports.append(results_df)

    if not daily_reports:
        return pd.DataFrame()

    return pd.concat(daily_reports, ignore_index=True)
