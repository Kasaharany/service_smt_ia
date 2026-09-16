from io import StringIO

import pandas as pd
import pytest

from core.ingestion import (
    ingest_inspection_datasets,
    validate_and_load_aoi_data,
    validate_and_load_spi_data,
)


class TestValidateAndLoadSpiData:
    def test_valid_csv_loads_and_normalizes_types(self):
        csv = StringIO("Panel_Barcode,RefDes,Volume_Percent\n  P1 , R1 ,85.5\n")
        df = validate_and_load_spi_data(csv)

        assert df.loc[0, "Panel_Barcode"] == "P1"
        assert df.loc[0, "RefDes"] == "R1"
        assert df.loc[0, "Volume_Percent"] == 85.5

    def test_missing_required_column_raises(self):
        csv = StringIO("Panel_Barcode,RefDes\nP1,R1\n")
        with pytest.raises(ValueError, match="Colunas ausentes"):
            validate_and_load_spi_data(csv)

    def test_non_numeric_volume_is_coerced_to_nan(self):
        csv = StringIO("Panel_Barcode,RefDes,Volume_Percent\nP1,R1,not-a-number\n")
        df = validate_and_load_spi_data(csv)

        assert pd.isna(df.loc[0, "Volume_Percent"])

    def test_formula_prefixed_barcode_is_neutralized(self):
        csv = StringIO('Panel_Barcode,RefDes,Volume_Percent\n=HYPERLINK("http://evil"),R1,50\n')
        df = validate_and_load_spi_data(csv)

        assert df.loc[0, "Panel_Barcode"].startswith("'=")

    @pytest.mark.parametrize("trigger", ["=cmd", "+1+1", "-1+1", "@SUM(1)"])
    def test_all_formula_trigger_characters_are_neutralized(self, trigger):
        csv = StringIO(f"Panel_Barcode,RefDes,Volume_Percent\n{trigger},R1,50\n")
        df = validate_and_load_spi_data(csv)

        assert df.loc[0, "Panel_Barcode"] == f"'{trigger}"

    def test_normal_barcode_is_left_untouched(self):
        csv = StringIO("Panel_Barcode,RefDes,Volume_Percent\nPNL-12345,R1,50\n")
        df = validate_and_load_spi_data(csv)

        assert df.loc[0, "Panel_Barcode"] == "PNL-12345"


class TestValidateAndLoadAoiData:
    def test_valid_csv_loads_and_normalizes_types(self):
        csv = StringIO("Panel_Barcode,RefDes,Defect_Type\n P1 , R1 , Bridge \n")
        df = validate_and_load_aoi_data(csv)

        assert df.loc[0, "Panel_Barcode"] == "P1"
        assert df.loc[0, "RefDes"] == "R1"
        assert df.loc[0, "Defect_Type"] == "Bridge"

    def test_missing_required_column_raises(self):
        csv = StringIO("Panel_Barcode,RefDes\nP1,R1\n")
        with pytest.raises(ValueError, match="Colunas ausentes"):
            validate_and_load_aoi_data(csv)

    def test_formula_prefixed_defect_type_is_neutralized(self):
        csv = StringIO("Panel_Barcode,RefDes,Defect_Type\nP1,R1,=cmd|'/c calc'\n")
        df = validate_and_load_aoi_data(csv)

        assert df.loc[0, "Defect_Type"].startswith("'=")


class TestIngestInspectionDatasets:
    def test_returns_both_validated_dataframes(self):
        spi_csv = StringIO("Panel_Barcode,RefDes,Volume_Percent\nP1,R1,50\n")
        aoi_csv = StringIO("Panel_Barcode,RefDes,Defect_Type\nP1,R1,Bridge\n")

        spi_df, aoi_df = ingest_inspection_datasets(spi_csv, aoi_csv)

        assert len(spi_df) == 1
        assert len(aoi_df) == 1
