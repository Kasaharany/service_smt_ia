from typing import BinaryIO, Tuple, Union

import pandas as pd

from config.settings import REQUIRED_AOI_COLUMNS, REQUIRED_SPI_COLUMNS

# Caracteres que o Excel/LibreOffice interpretam como início de fórmula.
_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _neutralize_formula_injection(series: pd.Series) -> pd.Series:
    """Neutraliza CSV/Formula Injection (CWE-1236) prefixando com aspas simples
    qualquer valor que comece com um caractere interpretado como fórmula pelo
    Excel/LibreOffice. Protege relatórios exportados (`to_csv`) que incluem
    estes campos, vindos de um CSV de origem não totalmente confiável.
    """
    return series.apply(
        lambda value: f"'{value}" if value.startswith(_FORMULA_TRIGGER_CHARS) else value
    )


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
    df["Panel_Barcode"] = _neutralize_formula_injection(df["Panel_Barcode"].astype(str).str.strip())
    df["RefDes"] = _neutralize_formula_injection(df["RefDes"].astype(str).str.strip())

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

    df["Panel_Barcode"] = _neutralize_formula_injection(df["Panel_Barcode"].astype(str).str.strip())
    df["RefDes"] = _neutralize_formula_injection(df["RefDes"].astype(str).str.strip())
    df["Defect_Type"] = _neutralize_formula_injection(df["Defect_Type"].astype(str).str.strip())

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
