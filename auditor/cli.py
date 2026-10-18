"""Presentación: punto de entrada. Raíz de composición (inyección de dependencias)."""
import asyncio

from .config import ConfigError, Settings
from .nombres import TokenSubsetMatcher
from .parsers import ParserFactory
from .repositories import PostgresRegistroRepository
from .reporte import RichReporter
from .scanner import FileScanner
from .servicio import AuditService

PISTAS = {
    "password authentication failed": "Usuario o contraseña incorrectos. Revisa AIVEN_DB_PASSWORD.",
    "timeout expired": "El servidor no respondió en 10 s. Revisa internet/firewall y que el servicio Aiven esté encendido.",
    "could not translate host name": "No se resuelve el host. Revisa el host o tu conexión a internet.",
    "connection refused": "Host o puerto incorrectos, o el servicio está apagado.",
    "does not exist": "La base de datos o una tabla no existe. Ojo con la tilde en 'documentación_legal'.",
    "ssl": "Problema de SSL. Aiven exige sslmode=require.",
}


def _pista(error):
    msg = str(error).lower()
    return next((p for k, p in PISTAS.items() if k in msg), None)


def main(env=None, repo=None, console=None) -> int:
    """Ejecuta la auditoría. Devuelve 0 si termina bien y 1 si hay un error controlado."""
    reporter = RichReporter(console)
    try:
        cfg = Settings.from_env(env)
    except ConfigError as e:
        reporter.error("CONFIGURACIÓN", e)
        return 1

    repo = repo or PostgresRegistroRepository(cfg.dsn())
    servicio = AuditService(
        repo,
        FileScanner(ParserFactory.crear("acta"), cfg.ignorar),
        FileScanner(ParserFactory.crear("acuerdo"), cfg.ignorar),
        TokenSubsetMatcher(2),
    )
    reporter.info("Auditando: consulta a la BD y escaneo de directorios en paralelo...")
    try:
        reporte = asyncio.run(servicio.auditar(cfg.ruta_actas, cfg.ruta_acuerdos))
    except FileNotFoundError as e:
        reporter.error("RUTA NO ENCONTRADA", e, "Revisa la ruta o defínela con RUTA_ACTAS / RUTA_ACUERDOS.")
        return 1
    except Exception as e:  # errores de conexión o de consulta
        reporter.error("ERROR EN LA AUDITORÍA", e, _pista(e))
        return 1
    reporter.info("[green][OK] Auditoría completada.[/green]\n")
    reporter.mostrar(reporte)
    return 0
