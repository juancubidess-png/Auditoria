import csv
import os
import re
import psycopg2
from pathlib import Path
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


#============================================
# 1. Leer la contraseña
#============================================
db_password = os.getenv('AIVEN_DB_PASSWORD')

#=====================================================
# 2. Validar que la variable de entorno no esté vacía
#=====================================================
if not db_password:
    console.print("[bold red][CRÍTICO][/bold red] Variable de entorno 'AIVEN_DB_PASSWORD' no definida. Ejecución abortada.")
    exit(1)

#=====================================================
# 3. Configuración de BD 
#=====================================================
DB_CONFIG = {
    'host': 'pg-140abf34-cun-c29c.a.aivencloud.com',
    'user': 'avnadmin',
    'password': db_password,
    'dbname': 'documentación_legal',
    'port': '22070',
    'sslmode': 'require',
    'connect_timeout': '10' 
}

#=====================================================
# 4. Prueba de Conexión
#=====================================================
try:
    console.print("Estableciendo conexión con Aiven PostgreSQL...")
    conexion = psycopg2.connect(**DB_CONFIG)
    console.print("[bold green][OK] Conexión establecida correctamente.[/bold green]")
    conexion.close()
except psycopg2.Error as db_error:
    console.print("[bold red][FALLO DE CONEXIÓN][/bold red] El servidor de base de datos devolvió el siguiente error:")
    console.print(f"[white]{db_error}[/white]")
    exit(1)
except Exception as e:
    console.print("[bold red][ERROR DEL SISTEMA][/bold red] La ejecución fue interrumpida por la siguiente excepción:")
    console.print(f"[white]{e}[/white]")
    exit(1)

# ================================================================================================================
# 3. Regex y Normalización
# ================================================================================================================
REGEX_ACTA = re.compile(r"Acta\s+(?:de\s+)?Entrega\s*(?:-)?\s*([A-Za-z0-9]+)\s*-\s*([^-.]+)", re.IGNORECASE)
REGEX_ACUERDO = re.compile(r"Acuerdo\s+(?:de\s+)?Responsabilidad\s*(?:-)?\s*([^-.]+)", re.IGNORECASE)

def tokenizar_nombre(nombre_raw):
    if not nombre_raw or str(nombre_raw).strip() in ["", "-", "N/A"]: return set()
    return set(re.findall(r'\w+', str(nombre_raw).lower()))

def buscar_match_flexible(tokens_a, tokens_b):
    if not tokens_a or not tokens_b: return False
    return tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a) or len(tokens_a.intersection(tokens_b)) >= 2