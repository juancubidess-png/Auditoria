import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2
from rich.console import Console
from rich.markup import escape
from rich.table import Table

console = Console()


def fallar(titulo, detalle, pista=None):
    """Muestra un error claro y termina el programa."""
    console.print(f"[bold red][{titulo}][/bold red] {escape(str(detalle).strip())}")
    if pista:
        console.print(f"[yellow]Pista:[/yellow] {pista}")
    sys.exit(1)


# --- Configuración -----------------------------------------------------------
password = os.getenv("AIVEN_DB_PASSWORD")
if not password:
    fallar("CONFIGURACIÓN", "Variable de entorno AIVEN_DB_PASSWORD no definida.")

DB_CONFIG = {
    "host": "pg-140abf34-cun-c29c.a.aivencloud.com",
    "user": "avnadmin",
    "password": password,
    "dbname": "documentación_legal",
    "port": "22070",
    "sslmode": "require",
    "connect_timeout": "10",
}

RUTA_ACTAS = os.getenv("RUTA_ACTAS", "/home/thor/Documents/advanced_programming/02. ACTAS ENTREGA")
RUTA_ACUERDOS = os.getenv("RUTA_ACUERDOS", "/home/thor/Documents/advanced_programming/01. ACUERDOS RESPONSABILIDAD")
IGNORAR = ("01. CONSOLIDADO", "02. ACTAS DE ENTREGA PERIFERICOS")

REGEX_ACTA = re.compile(r"Acta\s+(?:de\s+)?Entrega\s*(?:-)?\s*([A-Za-z0-9]+)\s*-\s*([^-.]+)", re.I)
REGEX_ACUERDO = re.compile(r"Acuerdo\s+(?:de\s+)?Responsabilidad\s*(?:-)?\s*([^-.]+)", re.I)

PISTAS = {
    "password authentication failed": "Usuario o contraseña incorrectos. Revisa AIVEN_DB_PASSWORD.",
    "timeout expired": "El servidor no respondió en 10 s. Revisa internet/firewall y que el servicio Aiven esté encendido.",
    "could not translate host name": "No se resuelve el host. Revisa el host o tu conexión a internet.",
    "connection refused": "Host o puerto incorrectos, o el servicio está apagado.",
    "does not exist": "La base de datos no existe. Ojo con la tilde en 'documentación_legal'.",
    "ssl": "Problema de SSL. Aiven exige sslmode=require.",
}


# --- Nombres -----------------------------------------------------------------
def tokens(nombre):
    return set(re.findall(r"\w+", (nombre or "").lower()))


def mismo_nombre(a, b):
    return bool(a and b) and (a <= b or b <= a or len(a & b) >= 2)


# --- Base de datos -----------------------------------------------------------
def conectar():
    console.print("Conectando a Aiven PostgreSQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        pista = next((p for k, p in PISTAS.items() if k in str(e).lower()), None)
        fallar("FALLO DE CONEXIÓN", e, pista)
    console.print("[green][OK] Conexión establecida.[/green]")
    return conn


def cargar_bd(conn):
    with conn.cursor() as cur:
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

    total_actas = sum(map(len, actas.values()))
    console.print(f"[green][OK] Datos cargados:[/green] {total_actas} actas y {len(acuerdos)} acuerdos en BD.\n")
    return actas, acuerdos


# --- Archivos ----------------------------------------------------------------
def archivos(ruta, regex, ignorar=()):
    """Genera (grupos_del_regex, ruta_archivo) por cada archivo que cumpla el patrón."""
    if not Path(ruta).is_dir():
        fallar("RUTA NO ENCONTRADA", ruta, "Revisa la ruta o defínela con RUTA_ACTAS / RUTA_ACUERDOS.")
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
        t.add_row(*map(escape, fila))
    console.print(t, "\n")


def main():
    conn = conectar()
    try:
        actas_db, acuerdos_db = cargar_bd(conn)
    except psycopg2.Error as e:
        fallar("ERROR EN CONSULTA", e, "Revisa que las tablas y columnas existan con esos nombres.")
    finally:
        conn.close()

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