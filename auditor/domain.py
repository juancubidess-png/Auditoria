"""Capa de dominio: objetos de valor y reporte."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActaArchivo:
    placa: str
    usuario: str
    ruta: str


@dataclass(frozen=True)
class AcuerdoArchivo:
    usuario: str
    ruta: str


@dataclass
class ReporteAuditoria:
    actas_faltantes: list = field(default_factory=list)
    acuerdos_faltantes: list = field(default_factory=list)

    def total_pendientes(self) -> int:
        return len(self.actas_faltantes) + len(self.acuerdos_faltantes)
