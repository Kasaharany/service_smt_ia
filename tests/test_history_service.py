import random

from core.engine import SMTDeterministicEngine
from services.history_service import generate_historical_diagnostics


def test_generate_historical_diagnostics_covers_requested_period():
    random.seed(7)
    engine = SMTDeterministicEngine()

    history_df = generate_historical_diagnostics(engine, days=10)

    assert not history_df.empty
    assert "Data" in history_df.columns
    assert history_df["Data"].nunique() <= 10
    assert set(history_df["Severidade"]).issubset({"Crítica", "Alta", "Média", "Baixa"})
