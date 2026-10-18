"""Pruebas de rendimiento y estrés. Uso: python -m bench.benchmark"""
import os, random, tempfile, time, tracemalloc
from auditor.nombres import TokenSubsetMatcher, tokens
from auditor.parsers import ActaParser
from auditor.scanner import FileScanner
from auditor.servicio import IndiceNombres

M = TokenSubsetMatcher(2)
random.seed(42)
NOM = [f"nombre{i}" for i in range(3000)]
APE = [f"apellido{i}" for i in range(3000)]


def nombre():
    return f"{random.choice(NOM)} {random.choice(NOM)} {random.choice(APE)} {random.choice(APE)}"


def secuencial(archivos, registros):          # lógica del prototipo v0: O(n·m)
    return [a for a in archivos if not any(M.coincide(a, r) for r in registros)]


def indexado(archivos, registros):            # índice hash por token
    idx = IndiceNombres(registros, M)
    return [a for a in archivos if not idx.contiene(a)]


def medir(f, *a):
    t = time.perf_counter(); r = f(*a); return r, time.perf_counter() - t


def comparativa(tamanos, repeticiones=5):
    print(f"{'n=m':>8} {'secuencial (s)':>16} {'indexado (s)':>14} {'mejora':>8} {'iguales':>8}")
    for n in tamanos:
        regs = [tokens(nombre()) for _ in range(n)]
        archs = [regs[i] if i % 2 == 0 else tokens(nombre()) for i in range(n)]
        ts, ti = [], []
        for _ in range(repeticiones):
            r1, a = medir(secuencial, archs, regs); r2, b = medir(indexado, archs, regs)
            ts.append(a); ti.append(b)
        ms, mi = sum(ts) / len(ts), sum(ti) / len(ti)
        print(f"{n:>8} {ms:>16.4f} {mi:>14.4f} {ms / mi:>7.1f}x {str(r1 == r2):>8}")


def indexado_grande(tamanos):
    print("\nSolo indexado (el secuencial es inviable):")
    for n in tamanos:
        regs = [tokens(nombre()) for _ in range(n)]
        archs = [regs[i] if i % 2 == 0 else tokens(nombre()) for i in range(n)]
        _, t = medir(indexado, archs, regs)
        print(f"{n:>8} {t:>10.4f} s")


def estres_escaneo(n):
    print(f"\nEstrés de escaneo con {n} archivos:")
    with tempfile.TemporaryDirectory() as d:
        for i in range(n):
            sub = os.path.join(d, f"c{i % 50}"); os.makedirs(sub, exist_ok=True)
            open(os.path.join(sub, f"Acta Entrega - P{i} - Usuario{i} Prueba.pdf"), "w").close()
        tracemalloc.start()
        t = time.perf_counter()
        total = sum(1 for _ in FileScanner(ActaParser()).iterar(d))   # generador: no acumula
        dt = time.perf_counter() - t
        _, pico = tracemalloc.get_traced_memory(); tracemalloc.stop()
        print(f"  archivos reconocidos: {total} | tiempo: {dt:.2f} s | memoria pico: {pico / 1e6:.2f} MB")


if __name__ == "__main__":
    comparativa([500, 1000, 2000, 4000, 10000], repeticiones=3)
    indexado_grande([10000, 50000, 100000])
    estres_escaneo(100000)
