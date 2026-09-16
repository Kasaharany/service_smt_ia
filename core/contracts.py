from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SPIDataRecord:
    """Representa uma linha validada de inspeção de pasta de solda (SPI)."""
    panel_barcode: str
    ref_des: str
    volume_percent: float


@dataclass(frozen=True)
class AOIDataRecord:
    """Representa uma linha validada de defeito detectado na inspeção óptica (AOI)."""
    panel_barcode: str
    ref_des: str
    defect_type: str


@dataclass(frozen=True)
class DiagnosticResult:
    """Resultado formal do diagnóstico determinístico de causa raiz."""
    panel_barcode: str
    ref_des: str
    defect_type: str
    volume_percent: Optional[float]
    culprit_machine: str
    action_detail: str
    severity: str
