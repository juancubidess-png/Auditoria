import io
import os
import tempfile

from rich.console import Console

from auditor import cli
from auditor.config import ConfigError, Settings
from auditor.domain import AcuerdoArchivo, ActaArchivo, ReporteAuditoria
from auditor.repositories import InMemoryRegistroRepository
from auditor.reporte import RichReporter


def _console():
    buf = io.StringIO()
    return Console(file=buf, width=200, force_terminal=False, color_system=None), buf


# ---- Settings ----
def test_settings_desde_entorno():
    s = Settings.from_env({"AIVEN_DB_PASSWORD": "x", "AIVEN_DB_PORT": "5432", "RUTA_ACTAS": "/tmp/a"})
    assert s.db_password == "x" and s.db_port == 5432 and str(s.ruta_actas) == "/tmp/a"
    assert s.dsn()["sslmode"] == "require" and s.dsn()["port"] == "5432"


def test_settings_sin_password():
    try:
        Settings.from_env({})
        assert False
    except ConfigError:
        pass


def test_settings_puerto_invalido():
    try:
        Settings.from_env({"AIVEN_DB_PASSWORD": "x", "AIVEN_DB_PORT": "abc"})
        assert False
    except ConfigError:
        pass


def test_settings_usa_os_environ_por_defecto():
    os.environ["AIVEN_DB_PASSWORD"] = "temporal"
    try:
        assert Settings.from_env().db_password == "temporal"
    finally:
        del os.environ["AIVEN_DB_PASSWORD"]


# ---- RichReporter ----
def test_reporter_muestra_tablas():
    c, buf = _console()
    r = ReporteAuditoria([ActaArchivo("P2", "Ana Lopez", "/ruta/larga/Acta Entrega - P2 - Ana Lopez.pdf")], [AcuerdoArchivo("Pedro Rojas", "/ruta/larga/Acuerdo Responsabilidad - Pedro Rojas.pdf")])
    RichReporter(c).mostrar(r)
    out = buf.getvalue()
    assert "ACTAS NO REGISTRADAS (1)" in out and "Ana Lopez" in out
    assert "ACUERDOS NO REGISTRADOS (1)" in out and "Pedro Rojas" in out
    assert "Total pendientes: 2" in out


def test_reporter_todo_registrado():
    c, buf = _console()
    RichReporter(c).mostrar(ReporteAuditoria())
    assert "todo registrado en BD" in buf.getvalue()


def test_reporter_error_con_pista():
    c, buf = _console()
    RichReporter(c).error("TITULO", "detalle", "una pista")
    assert "TITULO" in buf.getvalue() and "Pista:" in buf.getvalue()


# ---- CLI de extremo a extremo (repositorio en memoria, sin base de datos) ----
def _arbol(base, nombres):
    for n in nombres:
        open(os.path.join(base, n), "w").close()


def test_cli_ok():
    c, buf = _console()
    with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as dc:
        _arbol(da, ["Acta Entrega - P1 - Juan Perez.pdf", "Acta Entrega - P2 - Ana Lopez.pdf"])
        _arbol(dc, ["Acuerdo Responsabilidad - Pedro Rojas.pdf"])
        repo = InMemoryRegistroRepository([("P1", "Juan Carlos Perez")], ["Juan Carlos Perez"])
        env = {"AIVEN_DB_PASSWORD": "x", "RUTA_ACTAS": da, "RUTA_ACUERDOS": dc}
        assert cli.main(env=env, repo=repo, console=c) == 0
    out = buf.getvalue()
    assert "Ana Lopez" in out and "Pedro Rojas" in out and "Total pendientes: 2" in out


def test_cli_sin_configuracion():
    c, buf = _console()
    assert cli.main(env={}, console=c) == 1
    assert "CONFIGURACIÓN" in buf.getvalue()


def test_cli_ruta_inexistente():
    c, buf = _console()
    env = {"AIVEN_DB_PASSWORD": "x", "RUTA_ACTAS": "/no/existe/a", "RUTA_ACUERDOS": "/no/existe/b"}
    assert cli.main(env=env, repo=InMemoryRegistroRepository(), console=c) == 1
    assert "RUTA NO ENCONTRADA" in buf.getvalue()


class _RepoQueFalla(InMemoryRegistroRepository):
    def obtener_actas(self):
        raise RuntimeError("password authentication failed for user")


def test_cli_error_de_conexion_con_pista():
    c, buf = _console()
    with tempfile.TemporaryDirectory() as d:
        env = {"AIVEN_DB_PASSWORD": "x", "RUTA_ACTAS": d, "RUTA_ACUERDOS": d}
        assert cli.main(env=env, repo=_RepoQueFalla(), console=c) == 1
    assert "Usuario o contraseña incorrectos" in buf.getvalue()
