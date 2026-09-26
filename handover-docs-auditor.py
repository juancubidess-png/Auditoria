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