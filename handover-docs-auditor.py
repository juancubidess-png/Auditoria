import csv
import os
import re
import psycopg2 
from pathlib import Path
from collections import defaultdict

# Importaciones de Rich para darle formato visual
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

# conexion  a Bases de datos postgres 
DB_CONFIG = {
    'host': 'pg-140abf34-cun-c29c.a.aivencloud.com',
    'user': 'avnadmin',
    'password': '',
    'dbname': 'documentación_legal',  
    'port': '5432' 
}

# rutas al repositorio 

RUTA_ACTAS = r"h:/02. INVENTARIO HELPDESK Y ACTAS/01. INVENTARIO MOVIIRED/01. ACTAS DE ENTREGA MOVII & MOVIIRED"
RUTA_ACUERDOS = r"h:/02. INVENTARIO HELPDESK Y ACTAS/01. INVENTARIO MOVIIRED/02. ACUERDO DE RESPONSABILIDAD MOVII & MOVIIRED/ACUERDOS EQUIPOS"

