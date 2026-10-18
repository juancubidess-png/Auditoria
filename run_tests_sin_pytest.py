"""Ejecutor mínimo (solo para entornos sin pytest). En su equipo use: pytest -v"""
import importlib, sys
sys.path.insert(0, ".")
ok = 0
for mod in ("tests.test_auditor", "tests.test_presentacion"):
    m = importlib.import_module(mod)
    for n in sorted(x for x in dir(m) if x.startswith("test_")):
        getattr(m, n)(); ok += 1; print("PASSED", n)
print(f"{ok} pruebas aprobadas")
