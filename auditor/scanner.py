"""Infraestructura: escáner de directorios (entrega los archivos de a uno, con generador)."""
from pathlib import Path

from .parsers import DocumentParser


class FileScanner:
    def __init__(self, parser: DocumentParser, ignorar=()):
        self._parser = parser
        self._ignorar = tuple(ignorar)

    def iterar(self, ruta):
        if not Path(ruta).is_dir():
            raise FileNotFoundError(f"Ruta no encontrada: {ruta}")
        for f in Path(ruta).rglob("*.*"):
            if any(i in str(f) for i in self._ignorar):
                continue
            doc = self._parser.parsear(f.name, str(f))
            if doc is not None:
                yield doc

    def escanear(self, ruta) -> list:
        return list(self.iterar(ruta))
