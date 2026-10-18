"""Infraestructura: configuración inmutable leída desde variables de entorno."""
import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    """Falta una variable obligatoria o es inválida."""


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_user: str
    db_password: str
    db_name: str
    db_port: int
    ruta_actas: Path
    ruta_acuerdos: Path
    ignorar: tuple

    @classmethod
    def from_env(cls, env=None) -> "Settings":
        env = os.environ if env is None else env
        password = env.get("AIVEN_DB_PASSWORD")
        if not password:
            raise ConfigError("Variable de entorno AIVEN_DB_PASSWORD no definida.")
        try:
            port = int(env.get("AIVEN_DB_PORT", "22070"))
        except ValueError:
            raise ConfigError("AIVEN_DB_PORT debe ser un número entero.") from None
        return cls(
            db_host=env.get("AIVEN_DB_HOST", "pg-140abf34-cun-c29c.a.aivencloud.com"),
            db_user=env.get("AIVEN_DB_USER", "avnadmin"),
            db_password=password,
            db_name=env.get("AIVEN_DB_NAME", "documentación_legal"),
            db_port=port,
            ruta_actas=Path(env.get("RUTA_ACTAS", "/home/thor/Documents/advanced_programming/02. ACTAS ENTREGA")),
            ruta_acuerdos=Path(env.get("RUTA_ACUERDOS", "/home/thor/Documents/advanced_programming/01. ACUERDOS RESPONSABILIDAD")),
            ignorar=("01. CONSOLIDADO", "02. ACTAS DE ENTREGA PERIFERICOS"),
        )

    def dsn(self) -> dict:
        return {
            "host": self.db_host, "user": self.db_user, "password": self.db_password,
            "dbname": self.db_name, "port": str(self.db_port),
            "sslmode": "require", "connect_timeout": "10",
        }
