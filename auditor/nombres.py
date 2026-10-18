"""Capa de dominio: tokenización y estrategia de coincidencia de nombres (Strategy)."""
import re
from abc import ABC, abstractmethod


def tokens(nombre):
    """Convierte un nombre en un conjunto de palabras en minúscula."""
    return frozenset(re.findall(r"\w+", (nombre or "").lower()))


class NameMatcher(ABC):
    @abstractmethod
    def coincide(self, a, b) -> bool: ...


class TokenSubsetMatcher(NameMatcher):
    """Coinciden si un conjunto contiene al otro o comparten al menos `minimo` tokens."""

    def __init__(self, minimo: int = 2):
        self._minimo = minimo

    def coincide(self, a, b) -> bool:
        return bool(a and b) and (a <= b or b <= a or len(a & b) >= self._minimo)
