"""Motor de correlação determinística entre relatórios SPI e AOI."""

from __future__ import annotations

from typing import IO

import pandas as pd


class SMTDeterministicEngine:
    """Correlaciona dados de SPI (impressão de pasta) e AOI (inspeção óptica)
    e aplica regras fixas de causa raiz sobre os desvios encontrados.
    """

    REQUIRED_SPI_COLUMNS = {"Panel_Barcode", "RefDes", "Volume(%)"}
    REQUIRED_AOI_COLUMNS = {"Panel_Barcode", "RefDes", "Defect_Type", "Result_AOI"}

    def load_spi(self, file: IO) -> pd.DataFrame:
        df = pd.read_csv(file, decimal=",")
        missing = self.REQUIRED_SPI_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Colunas ausentes no relatório SPI: {', '.join(sorted(missing))}")
        df["Volume(%)"] = pd.to_numeric(
            df["Volume(%)"].astype(str).str.replace(",", "."), errors="coerce"
        )
        return df.dropna(subset=["Volume(%)"])

    def load_aoi(self, file: IO) -> pd.DataFrame:
        df = pd.read_csv(file, decimal=",")
        missing = self.REQUIRED_AOI_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Colunas ausentes no relatório AOI: {', '.join(sorted(missing))}")
        return df

    def correlate(self, df_spi: pd.DataFrame, df_aoi: pd.DataFrame) -> pd.DataFrame:
        merged = pd.merge(df_spi, df_aoi, on=["Panel_Barcode", "RefDes"], how="inner")
        return merged[merged["Result_AOI"] != "PASS"]

    def diagnose(self, df_cruzado: pd.DataFrame) -> pd.DataFrame:
        if df_cruzado.empty:
            return pd.DataFrame(
                columns=["Placa", "Componente", "Volume SPI (%)", "Defeito AOI", "Causa Raiz", "Recomendação"]
            )
        registros = [self._classify(row) for _, row in df_cruzado.iterrows()]
        return pd.DataFrame(registros)

    def run(self, spi_file: IO, aoi_file: IO) -> pd.DataFrame:
        df_spi = self.load_spi(spi_file)
        df_aoi = self.load_aoi(aoi_file)
        df_cruzado = self.correlate(df_spi, df_aoi)
        return self.diagnose(df_cruzado)

    def _classify(self, row: pd.Series) -> dict:
        volume = float(row["Volume(%)"])
        defeito = row["Defect_Type"]

        # Limiares empíricos: abaixo de 50% a solda não sustenta o componente
        # (insuficiência de impressão); acima de 130% indica stencil/squeegee
        # depositando pasta em excesso.
        if volume < 50 and defeito in {"Missing", "Tombstone"}:
            causa = "Impressora (Pasta de Solda)"
            recomendacao = f"Volume insuficiente ({volume:.1f}%). Inspecionar stencil e raspador (squeegee)."
        elif volume > 130:
            causa = "Impressora (Pasta de Solda)"
            recomendacao = f"Volume excessivo ({volume:.1f}%). Verificar stencil entupido ou pressão do squeegee."
        elif volume > 90 and defeito == "Shift":
            causa = "Pick & Place"
            recomendacao = f"Deslocamento de componente sem excesso de pasta associado ({volume:.1f}%). Verificar bico de sucção (nozzle) e alinhamento do feeder."
        elif defeito in {"Bridge", "Solder Ball"} and volume > 90:
            causa = "Impressora (Pasta de Solda)"
            recomendacao = f"Excesso de pasta ({volume:.1f}%) favorecendo formação de pontes. Ajustar stencil/squeegee."
        else:
            causa = "Perfil Térmico / Refusão"
            recomendacao = "Volume de pasta dentro do padrão. Investigar o perfil térmico do forno de refusão."

        return {
            "Placa": row["Panel_Barcode"],
            "Componente": row["RefDes"],
            "Volume SPI (%)": round(volume, 1),
            "Defeito AOI": defeito,
            "Causa Raiz": causa,
            "Recomendação": recomendacao,
        }
