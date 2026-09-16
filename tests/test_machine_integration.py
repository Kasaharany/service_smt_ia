import random

from services.machine_integration import simulate_machine_integration


def test_simulate_machine_integration_returns_validated_dataframes():
    random.seed(42)

    spi_df, aoi_df = simulate_machine_integration()

    assert list(spi_df.columns) == ["Panel_Barcode", "RefDes", "Volume_Percent"]
    assert list(aoi_df.columns) == ["Panel_Barcode", "RefDes", "Defect_Type"]
    assert len(spi_df) > 0
    # todo componente defeituoso na AOI deve existir também na SPI simulada
    assert set(aoi_df["Panel_Barcode"]).issubset(set(spi_df["Panel_Barcode"]))
