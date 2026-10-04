import os
import re
import sys
from collections import defaultdict
from contextlib import closing
from pathlib import Path

import psycopg2
from rich.console import Console
from rich.table import Table

console = Console()

# --- Configuración -----------------------------------------------------------
password = os.getenv("AIVEN_DB_PASSWORD")
if not password:
    sys.exit("Variable de entorno AIVEN_DB_PASSWORD no definida.")

DB_CONFIG = {
    "host": "pg-140abf34-cun-c29c.a.aivencloud.com",
    "user": "avnadmin",
    "password": password,
    "dbname": "documentación_legal",
    "port": "22070",
    "sslmode": "require",
    "connect_timeout": "10",
}

RUTA_ACTAS = os.getenv("RUTA_ACTAS", "/ruta/a/actas")
RUTA_ACUERDOS = os.getenv("RUTA_ACUERDOS", "/ruta/a/acuerdos")
IGNORAR = ("01. CONSOLIDADO", "02. ACTAS DE ENTREGA PERIFERICOS")

REGEX_ACTA = re.compile(r"Acta\s+(?:de\s+)?Entrega\s*(?:-)?\s*([A-Za-z0-9]+)\s*-\s*([^-.]+)", re.I)
REGEX_ACUERDO = re.compile(r"Acuerdo\s+(?:de\s+)?Responsabilidad\s*(?:-)?\s*([^-.]+)", re.I)


# --- Nombres -----------------------------------------------------------------
def tokens(nombre):
    return set(re.findall(r"\w+", (nombre or "").lower()))


def mismo_nombre(a, b):
    return bool(a and b) and (a <= b or b <= a or len(a & b) >= 2)


# --- Base de datos -----------------------------------------------------------
def cargar_bd():
    with closing(psycopg2.connect(**DB_CONFIG)) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT UPPER(TRIM(e.placa_equipo)), u.nombre_completo
            FROM actas_entrega a
            JOIN equipos  e ON a.id_equipo  = e.id_equipo
            JOIN usuarios u ON a.id_usuario = u.id_usuario
        """)
        actas = defaultdict(list)
        for placa, usuario in cur.fetchall():
            actas[placa].append(tokens(usuario))

        cur.execute("""
            SELECT u.nombre_completo
            FROM acuerdos_responsabilidad ar
            JOIN usuarios u ON ar.id_usuario = u.id_usuario
        """)
        acuerdos = [tokens(r[0]) for r in cur.fetchall()]
    return actas, acuerdos


# --- Archivos ----------------------------------------------------------------
def archivos(ruta, regex, ignorar=()):
    """Genera (grupos_del_regex, ruta_archivo) por cada archivo que cumpla el patrón."""
    for f in Path(ruta).rglob("*.*"):
        m = regex.search(f.name)
        if m and not any(i in str(f) for i in ignorar):
            yield m.groups(), str(f)


# --- Reporte -----------------------------------------------------------------
def tabla(titulo, columnas, filas):
    if not filas:
        return console.print(f"[green][OK] {titulo}: todo registrado en BD.[/green]\n")
    t = Table(title=f"[yellow]{titulo} ({len(filas)})[/yellow]", show_lines=True)
    for c in columnas:
        t.add_column(c)
    for fila in sorted(filas):
        t.add_row(*fila)
    console.print(t, "\n")


def main():
    try:
        actas_db, acuerdos_db = cargar_bd()
    except psycopg2.Error as e:
        sys.exit(f"Error de base de datos: {e}")

    actas = [
        (placa.upper(), usuario.strip(), ruta)
        for (placa, usuario), ruta in archivos(RUTA_ACTAS, REGEX_ACTA, IGNORAR)
        if not any(mismo_nombre(tokens(usuario), t) for t in actas_db.get(placa.upper(), []))
    ]
    acuerdos = [
        (usuario.strip(), ruta)
        for (usuario,), ruta in archivos(RUTA_ACUERDOS, REGEX_ACUERDO)
        if not any(mismo_nombre(tokens(usuario), t) for t in acuerdos_db)
    ]

    tabla("ACTAS NO REGISTRADAS", ["Placa", "Usuario", "Ruta"], actas)
    tabla("ACUERDOS NO REGISTRADOS", ["Usuario", "Ruta"], acuerdos)


if __name__ == "__main__":
    main()