from typing import BinaryIO, Tuple, Union
import pandas as pd

from config.settings import REQUIRED_AOI_COLUMNS, REQUIRED_SPI_COLUMNS


def validate_and_load_spi_data(
    file_source: Union[str, BinaryIO]
) -> pd.DataFrame:
    """
    Realiza a leitura e validação do esquema de dados da SPI.
    Garante presença de colunas obrigatórias e coerência de tipos numéricos.
    """
    # Garante leitura do início caso venha de stream do Streamlit
    if hasattr(file_source, "seek"):
        file_source.seek(0)

    df = pd.read_csv(file_source)
    df.columns = df.columns.str.strip()

    missing_cols = REQUIRED_SPI_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Relatório SPI inválido. Colunas ausentes: {sorted(list(missing_cols))}"
        )

    df["Volume_Percent"] = pd.to_numeric(df["Volume_Percent"], errors="coerce")
    df["Panel_Barcode"] = df["Panel_Barcode"].astype(str).str.strip()
    df["RefDes"] = df["RefDes"].astype(str).str.strip()

    return df


def validate_and_load_aoi_data(
    file_source: Union[str, BinaryIO]
) -> pd.DataFrame:
    """
    Realiza a leitura e validação do esquema de dados da AOI.
    Normaliza os identificadores de painel, componente e classificação do defeito.
    """
    if hasattr(file_source, "seek"):
        file_source.seek(0)

    df = pd.read_csv(file_source)
    df.columns = df.columns.str.strip()

    missing_cols = REQUIRED_AOI_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Relatório AOI inválido. Colunas ausentes: {sorted(list(missing_cols))}"
        )

    df["Panel_Barcode"] = df["Panel_Barcode"].astype(str).str.strip()
    df["RefDes"] = df["RefDes"].astype(str).str.strip()
    df["Defect_Type"] = df["Defect_Type"].astype(str).str.strip()

    return df


def ingest_inspection_datasets(
    spi_source: Union[str, BinaryIO],
    aoi_source: Union[str, BinaryIO]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ponto de entrada único para carga e validação dos relatórios combinados.
    """
    spi_df = validate_and_load_spi_data(spi_source)
    aoi_df = validate_and_load_aoi_data(aoi_source)
    return spi_df, aoi_df
