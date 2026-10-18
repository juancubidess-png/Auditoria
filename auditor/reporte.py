"""Presentación: salida de consola con Rich."""
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from .domain import ReporteAuditoria


class RichReporter:
    def __init__(self, console=None):
        self._c = console or Console()

    def info(self, texto: str) -> None:
        self._c.print(texto)

    def error(self, titulo: str, detalle, pista=None) -> None:
        self._c.print(f"[bold red][{titulo}][/bold red] {escape(str(detalle).strip())}")
        if pista:
            self._c.print(f"[yellow]Pista:[/yellow] {pista}")

    def _tabla(self, titulo, columnas, filas) -> None:
        if not filas:
            self._c.print(f"[green][OK] {titulo}: todo registrado en BD.[/green]\n")
            return
        t = Table(title=f"[yellow]{titulo} ({len(filas)})[/yellow]", show_lines=True)
        for c in columnas:
            t.add_column(c)
        for fila in sorted(filas):
            t.add_row(*map(escape, fila))
        self._c.print(t, "\n")

    def mostrar(self, r: ReporteAuditoria) -> None:
        self._tabla("ACTAS NO REGISTRADAS", ["Placa", "Usuario", "Ruta"],
                    [(a.placa, a.usuario, a.ruta) for a in r.actas_faltantes])
        self._tabla("ACUERDOS NO REGISTRADOS", ["Usuario", "Ruta"],
                    [(a.usuario, a.ruta) for a in r.acuerdos_faltantes])
        self._c.print(f"Total pendientes: {r.total_pendientes()}")
