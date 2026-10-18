"""Infraestructura: Repository (abstracto, en memoria y PostgreSQL)."""
from abc import ABC, abstractmethod

SQL_ACTAS = """
    SELECT UPPER(TRIM(e.placa_equipo)), u.nombre_completo
    FROM actas_entrega a
    JOIN equipos  e ON a.id_equipo  = e.id_equipo
    JOIN usuarios u ON a.id_usuario = u.id_usuario
"""
SQL_ACUERDOS = """
    SELECT u.nombre_completo
    FROM acuerdos_responsabilidad ar
    JOIN usuarios u ON ar.id_usuario = u.id_usuario
"""


class RegistroRepository(ABC):
    @abstractmethod
    def obtener_actas(self) -> list: ...      # [(placa, usuario)]

    @abstractmethod
    def obtener_acuerdos(self) -> list: ...   # [usuario]


class InMemoryRegistroRepository(RegistroRepository):
    def __init__(self, actas=(), acuerdos=()):
        self._actas = list(actas)
        self._acuerdos = list(acuerdos)

    def obtener_actas(self):
        return list(self._actas)

    def obtener_acuerdos(self):
        return list(self._acuerdos)


class PostgresRegistroRepository(RegistroRepository):  # pragma: no cover (requiere BD real)
    def __init__(self, dsn: dict):
        self._dsn = dsn

    def _consultar(self, sql):
        import psycopg2  # importación diferida: las pruebas no la necesitan
        conn = psycopg2.connect(**self._dsn)
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchall()
        finally:
            conn.close()

    def obtener_actas(self):
        return self._consultar(SQL_ACTAS)

    def obtener_acuerdos(self):
        return [r[0] for r in self._consultar(SQL_ACUERDOS)]
