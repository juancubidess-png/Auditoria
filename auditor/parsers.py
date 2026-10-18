"""Infraestructura: analizadores de nombres (Template Method) y fábrica (Factory)."""
import re
from abc import ABC, abstractmethod

from .domain import AcuerdoArchivo, ActaArchivo


class DocumentParser(ABC):
    @abstractmethod
    def patron(self) -> re.Pattern: ...

    @abstractmethod
    def construir(self, grupos, ruta): ...

    def parsear(self, nombre_archivo: str, ruta: str):
        """Método plantilla: aplica el patrón y delega la construcción."""
        m = self.patron().search(nombre_archivo)
        return self.construir(m.groups(), ruta) if m else None


class ActaParser(DocumentParser):
    _RE = re.compile(r"Acta\s+(?:de\s+)?Entrega\s*(?:-)?\s*([A-Za-z0-9]+)\s*-\s*([^-.]+)", re.I)

    def patron(self):
        return self._RE

    def construir(self, grupos, ruta):
        placa, usuario = grupos
        return ActaArchivo(placa.upper(), usuario.strip(), ruta)


class AcuerdoParser(DocumentParser):
    _RE = re.compile(r"Acuerdo\s+(?:de\s+)?Responsabilidad\s*(?:-)?\s*([^-.]+)", re.I)

    def patron(self):
        return self._RE

    def construir(self, grupos, ruta):
        return AcuerdoArchivo(grupos[0].strip(), ruta)


class ParserFactory:
    _registro = {"acta": ActaParser, "acuerdo": AcuerdoParser}

    @classmethod
    def crear(cls, tipo: str) -> DocumentParser:
        try:
            return cls._registro[tipo]()
        except KeyError:
            raise ValueError(f"Tipo de documento desconocido: {tipo}") from None
