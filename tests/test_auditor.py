import asyncio
import os
import tempfile

from auditor.domain import ActaArchivo, ReporteAuditoria
from auditor.nombres import TokenSubsetMatcher, tokens
from auditor.parsers import ActaParser, AcuerdoParser, ParserFactory
from auditor.repositories import InMemoryRegistroRepository
from auditor.scanner import FileScanner
from auditor.servicio import AuditService, IndiceNombres

M = TokenSubsetMatcher(2)


# ---- Parsers (Regex) ----
def test_acta_parser_valido():
    r = ActaParser().parsear("Acta Entrega - abc123 - Juan Perez.pdf", "/x")
    assert r == ActaArchivo("ABC123", "Juan Perez", "/x")


def test_acta_parser_con_de():
    assert ActaParser().parsear("Acta de Entrega - xy9 - Ana Lopez.pdf", "/x").placa == "XY9"


def test_acta_parser_invalido():
    assert ActaParser().parsear("Acta de Entrega.pdf", "/x") is None


def test_acuerdo_parser():
    r = AcuerdoParser().parsear("Acuerdo de Responsabilidad - Maria Gomez.pdf", "/y")
    assert r.usuario == "Maria Gomez"


def test_factory():
    assert isinstance(ParserFactory.crear("acta"), ActaParser)
    assert isinstance(ParserFactory.crear("acuerdo"), AcuerdoParser)
    try:
        ParserFactory.crear("otro")
        assert False
    except ValueError:
        pass


# ---- Strategy (matcher) ----
def test_matcher_subconjunto():
    assert M.coincide(tokens("Juan Perez"), tokens("Juan Carlos Perez Gomez"))


def test_matcher_dos_tokens_comunes():
    assert M.coincide(tokens("Juan Perez Ruiz"), tokens("Juan Perez Soto"))


def test_matcher_negativo():
    assert not M.coincide(tokens("Juan Perez"), tokens("Maria Gomez"))
    assert not M.coincide(tokens("Juan Ruiz"), tokens("Juan Soto"))   # solo 1 token común, sin inclusión
    assert not M.coincide(frozenset(), tokens("Juan"))


# ---- Índice hash ----
def test_indice_contiene():
    idx = IndiceNombres([tokens("Juan Carlos Perez"), tokens("Maria Gomez")], M)
    assert idx.contiene(tokens("Juan Perez"))
    assert not idx.contiene(tokens("Pedro Rojas"))


def test_indice_equivale_a_busqueda_secuencial():
    nombres = [tokens(n) for n in ["Ana Maria Lopez", "Luis Perez", "Juan Carlos Perez", "Sofia Rojas Diaz"]]
    idx = IndiceNombres(nombres, M)
    for q in ["Ana Lopez", "Luis", "Perez Juan", "Rojas", "Pedro Mora", "Diaz Sofia Rojas"]:
        t = tokens(q)
        assert idx.contiene(t) == any(M.coincide(t, n) for n in nombres)


# ---- Conciliación ----
def _servicio(actas=(), acuerdos=()):
    repo = InMemoryRegistroRepository(actas, acuerdos)
    return AuditService(repo, FileScanner(ActaParser()), FileScanner(AcuerdoParser()), M)


def test_conciliar_detecta_faltantes():
    s = _servicio()
    f_actas = [ActaParser().parsear("Acta Entrega - P1 - Juan Perez.pdf", "a"),
               ActaParser().parsear("Acta Entrega - P2 - Ana Lopez.pdf", "b")]
    f_acu = [AcuerdoParser().parsear("Acuerdo Responsabilidad - Juan Perez.pdf", "c"),
             AcuerdoParser().parsear("Acuerdo Responsabilidad - Pedro Rojas.pdf", "d")]
    rep = s.conciliar([("P1", "Juan Carlos Perez")], ["Juan Carlos Perez"], f_actas, f_acu)
    assert [a.placa for a in rep.actas_faltantes] == ["P2"]
    assert [a.usuario for a in rep.acuerdos_faltantes] == ["Pedro Rojas"]
    assert rep.total_pendientes() == 2


def test_reporte_vacio():
    assert ReporteAuditoria().total_pendientes() == 0


# ---- Escáner + auditoría asíncrona (integración con archivos temporales) ----
def _crear_arbol(base, nombres):
    for n in nombres:
        open(os.path.join(base, n), "w").close()


def test_scanner_ignora_y_filtra():
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "01. CONSOLIDADO"))
        _crear_arbol(d, ["Acta Entrega - P1 - Juan Perez.pdf", "otro.txt"])
        _crear_arbol(os.path.join(d, "01. CONSOLIDADO"), ["Acta Entrega - P9 - Ana Lopez.pdf"])
        res = FileScanner(ActaParser(), ignorar=("01. CONSOLIDADO",)).escanear(d)
        assert [r.placa for r in res] == ["P1"]


def test_scanner_ruta_inexistente():
    try:
        FileScanner(ActaParser()).escanear("/no/existe/xyz")
        assert False
    except FileNotFoundError:
        pass


def test_auditar_asincrono_extremo_a_extremo():
    with tempfile.TemporaryDirectory() as da, tempfile.TemporaryDirectory() as dc:
        _crear_arbol(da, ["Acta Entrega - P1 - Juan Perez.pdf", "Acta Entrega - P2 - Ana Lopez.pdf"])
        _crear_arbol(dc, ["Acuerdo Responsabilidad - Juan Perez.pdf", "Acuerdo Responsabilidad - Pedro Rojas.pdf"])
        s = _servicio([("P1", "Juan Carlos Perez")], ["Juan Carlos Perez"])
        rep = asyncio.run(s.auditar(da, dc))
        assert [a.placa for a in rep.actas_faltantes] == ["P2"]
        assert [a.usuario for a in rep.acuerdos_faltantes] == ["Pedro Rojas"]
