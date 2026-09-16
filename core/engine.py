import time
from typing import Dict, List, Tuple
import pandas as pd

from config.settings import (
    MAX_SOLDER_VOLUME_PERCENT,
    MIN_SOLDER_VOLUME_PERCENT,
)
from core.contracts import DiagnosticResult


class SMTDeterministicEngine:
    """
    Motor determinístico de diagnóstico de causa raiz.
    Executa correlação relacional entre medições de pasta (SPI) e defeitos ópticos (AOI).
    """

    def __init__(
        self,
        min_vol: float = MIN_SOLDER_VOLUME_PERCENT,
        max_vol: float = MAX_SOLDER_VOLUME_PERCENT,
    ):
        self.min_vol = min_vol
        self.max_vol = max_vol

    def evaluate_root_cause(
        self, defect_type: str, volume_percent: float | None
    ) -> Tuple[str, str, str]:
        """
        Aplica as regras formais do sistema especialista.
        Retorna uma tupla: (Máquina Culpada, Detalhamento Técnico, Severidade).
        """
        defect_clean = str(defect_type).strip().lower()

        if volume_percent is None or pd.isna(volume_percent):
            return (
                "NÃO IDENTIFICADO",
                "Sem registro de inspeção correspondente na base SPI.",
                "Alta",
            )

        # Regra 1: Subdeposição severa de pasta
        if volume_percent < self.min_vol:
            return (
                "IMPRESSORA DE PASTA (STENCIL PRINTER)",
                (
                    f"Subdeposição crítica ({volume_percent:.1f}%). "
                    "Causa: entupimento de abertura de estêncil ou pressão insuficiente de rodo."
                ),
                "Crítica",
            )

        # Regra 2: Sobredeposição severa de pasta
        if volume_percent > self.max_vol:
            return (
                "IMPRESSORA DE PASTA (STENCIL PRINTER)",
                (
                    f"Sobredeposição crítica ({volume_percent:.1f}%). "
                    "Causa: vazamento de pasta sob o estêncil ou snap-off inadequado. Risco de curto."
                ),
                "Crítica",
            )

        # Regra 3: Volume dentro da janela nominal -> falha mecânica ou térmica posterior
        if defect_clean in ["missing", "ausente", "ausência"]:
            return (
                "POSICIONADORA (PICK & PLACE)",
                (
                    f"Volume de pasta conforme ({volume_percent:.1f}%). "
                    "Causa: falha de sucção no bocal, alimentação de fita ou perda de peça no transporte."
                ),
                "Média",
            )

        if defect_clean in ["shift", "deslocamento", "desalinhado"]:
            return (
                "POSICIONADORA (PICK & PLACE)",
                (
                    f"Volume de pasta conforme ({volume_percent:.1f}%). "
                    "Causa: calibração de visão óptica do cabeçote ou desaceleração mecânica inadequada."
                ),
                "Média",
            )

        if defect_clean in ["tombstone", "tombamento", "levantado"]:
            return (
                "FORNO DE REFUSÃO / POSICIONADORA",
                (
                    f"Volume de pasta aceitável ({volume_percent:.1f}%). "
                    "Causa: desbalanceamento no perfil térmico das zonas de refluxo ou assimetria mecânica de pad."
                ),
                "Alta",
            )

        if defect_clean in ["bridge", "curto", "curto-circuito"]:
            return (
                "FORNO DE REFUSÃO",
                (
                    f"Volume nominal aceitável ({volume_percent:.1f}%). "
                    "Causa: rampa de aquecimento excessiva provocando esparramamento acelerado de fluxo."
                ),
                "Alta",
            )

        return (
            "AVALIAÇÃO DE PROCESSO",
            f"Volume medido ({volume_percent:.1f}%). Padrão de defeito não coberto por regras estáticas.",
            "Baixa",
        )

    def run_diagnostics(
        self, spi_df: pd.DataFrame, aoi_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, float]:
        """
        Executa a correlação relacional em memória e retorna o DataFrame de diagnósticos
        junto com o tempo total de processamento em milissegundos.
        """
        start_time = time.perf_counter()

        # Junção relacional à esquerda via chave composta
        merged_df = pd.merge(
            aoi_df,
            spi_df[["Panel_Barcode", "RefDes", "Volume_Percent"]],
            on=["Panel_Barcode", "RefDes"],
            how="left",
        )

        results: List[Dict] = []
        for _, row in merged_df.iterrows():
            barcode = row["Panel_Barcode"]
            ref_des = row["RefDes"]
            defect = row["Defect_Type"]
            vol = row["Volume_Percent"]

            machine, detail, severity = self.evaluate_root_cause(defect, vol)

            result_obj = DiagnosticResult(
                panel_barcode=barcode,
                ref_des=ref_des,
                defect_type=defect,
                volume_percent=vol if pd.notna(vol) else None,
                culprit_machine=machine,
                action_detail=detail,
                severity=severity,
            )

            results.append({
                "Código de Barras": result_obj.panel_barcode,
                "Posição (RefDes)": result_obj.ref_des,
                "Defeito na AOI": result_obj.defect_type,
                "Volume SPI (%)": f"{result_obj.volume_percent:.1f}%" if result_obj.volume_percent is not None else "N/A",
                "Máquina Culpada": result_obj.culprit_machine,
                "Diagnóstico Técnico": result_obj.action_detail,
                "Severidade": result_obj.severity,
            })

        execution_time_ms = (time.perf_counter() - start_time) * 1000
        output_df = pd.DataFrame(results)

        return output_df, execution_time_ms
