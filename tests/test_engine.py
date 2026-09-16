import pandas as pd
import pytest

from core.engine import SMTDeterministicEngine


@pytest.fixture
def engine() -> SMTDeterministicEngine:
    return SMTDeterministicEngine(min_vol=50.0, max_vol=150.0)


class TestEvaluateRootCause:
    def test_missing_spi_measurement_is_not_identified(self, engine):
        machine, detail, severity = engine.evaluate_root_cause("Bridge", None)
        assert machine == "NÃO IDENTIFICADO"
        assert severity == "Alta"

    def test_nan_volume_is_not_identified(self, engine):
        machine, _, severity = engine.evaluate_root_cause("Bridge", float("nan"))
        assert machine == "NÃO IDENTIFICADO"
        assert severity == "Alta"

    def test_severe_underdeposition_blames_printer(self, engine):
        machine, detail, severity = engine.evaluate_root_cause("Missing", 30.0)
        assert machine == "IMPRESSORA DE PASTA (STENCIL PRINTER)"
        assert severity == "Crítica"
        assert "30.0%" in detail

    def test_severe_overdeposition_blames_printer(self, engine):
        machine, detail, severity = engine.evaluate_root_cause("Bridge", 175.0)
        assert machine == "IMPRESSORA DE PASTA (STENCIL PRINTER)"
        assert severity == "Crítica"
        assert "175.0%" in detail

    def test_volume_exactly_at_min_threshold_is_not_underdeposition(self, engine):
        # limiar é exclusivo (`<`), então o valor igual ao mínimo é aceitável
        machine, _, _ = engine.evaluate_root_cause("Bridge", 50.0)
        assert machine != "IMPRESSORA DE PASTA (STENCIL PRINTER)"

    def test_volume_exactly_at_max_threshold_is_not_overdeposition(self, engine):
        machine, _, _ = engine.evaluate_root_cause("Bridge", 150.0)
        assert machine != "IMPRESSORA DE PASTA (STENCIL PRINTER)"

    @pytest.mark.parametrize("defect", ["missing", "Ausente", "AUSÊNCIA"])
    def test_missing_component_within_nominal_range_blames_pick_and_place(self, engine, defect):
        machine, _, severity = engine.evaluate_root_cause(defect, 90.0)
        assert machine == "POSICIONADORA (PICK & PLACE)"
        assert severity == "Média"

    @pytest.mark.parametrize("defect", ["shift", "Deslocamento", "desalinhado"])
    def test_shift_within_nominal_range_blames_pick_and_place(self, engine, defect):
        machine, _, severity = engine.evaluate_root_cause(defect, 90.0)
        assert machine == "POSICIONADORA (PICK & PLACE)"
        assert severity == "Média"

    @pytest.mark.parametrize("defect", ["tombstone", "Tombamento", "levantado"])
    def test_tombstone_within_nominal_range_blames_oven_or_placement(self, engine, defect):
        machine, _, severity = engine.evaluate_root_cause(defect, 90.0)
        assert machine == "FORNO DE REFUSÃO / POSICIONADORA"
        assert severity == "Alta"

    @pytest.mark.parametrize("defect", ["bridge", "Curto", "curto-circuito"])
    def test_bridge_within_nominal_range_blames_oven(self, engine, defect):
        machine, _, severity = engine.evaluate_root_cause(defect, 90.0)
        assert machine == "FORNO DE REFUSÃO"
        assert severity == "Alta"

    def test_unknown_defect_within_nominal_range_falls_back_to_process_review(self, engine):
        machine, _, severity = engine.evaluate_root_cause("Voiding", 90.0)
        assert machine == "AVALIAÇÃO DE PROCESSO"
        assert severity == "Baixa"


class TestRunDiagnostics:
    def test_matched_defect_produces_formatted_row(self, engine):
        spi_df = pd.DataFrame([
            {"Panel_Barcode": "P1", "RefDes": "R1", "Volume_Percent": 30.0},
        ])
        aoi_df = pd.DataFrame([
            {"Panel_Barcode": "P1", "RefDes": "R1", "Defect_Type": "Missing"},
        ])

        results_df, exec_ms = engine.run_diagnostics(spi_df, aoi_df)

        assert len(results_df) == 1
        row = results_df.iloc[0]
        assert row["Volume SPI (%)"] == "30.0%"
        assert row["Máquina Culpada"] == "IMPRESSORA DE PASTA (STENCIL PRINTER)"
        assert row["Severidade"] == "Crítica"
        assert exec_ms >= 0

    def test_aoi_defect_without_spi_match_is_not_identified(self, engine):
        spi_df = pd.DataFrame([
            {"Panel_Barcode": "P1", "RefDes": "R1", "Volume_Percent": 90.0},
        ])
        aoi_df = pd.DataFrame([
            {"Panel_Barcode": "P1", "RefDes": "R2", "Defect_Type": "Bridge"},
        ])

        results_df, _ = engine.run_diagnostics(spi_df, aoi_df)

        assert len(results_df) == 1
        row = results_df.iloc[0]
        assert row["Volume SPI (%)"] == "N/A"
        assert row["Máquina Culpada"] == "NÃO IDENTIFICADO"

    def test_no_defects_produces_empty_report(self, engine):
        spi_df = pd.DataFrame([
            {"Panel_Barcode": "P1", "RefDes": "R1", "Volume_Percent": 90.0},
        ])
        aoi_df = pd.DataFrame(columns=["Panel_Barcode", "RefDes", "Defect_Type"])

        results_df, _ = engine.run_diagnostics(spi_df, aoi_df)

        assert results_df.empty
