"""Capa de aplicación: índice hash de nombres y servicio de auditoría."""
import asyncio
from collections import defaultdict

from .domain import ReporteAuditoria
from .nombres import NameMatcher, tokens


class IndiceNombres:
    """Índice invertido token -> posiciones. Construcción O(m·k); consulta O(k·b) esperado."""

    def __init__(self, nombres, matcher: NameMatcher):
        self._nombres = list(nombres)
        self._matcher = matcher
        self._por_token = defaultdict(list)
        for i, ts in enumerate(self._nombres):
            for t in ts:
                self._por_token[t].append(i)

    def contiene(self, consulta) -> bool:
        candidatos = set()
        for t in consulta:
            candidatos.update(self._por_token.get(t, ()))
        return any(self._matcher.coincide(consulta, self._nombres[i]) for i in candidatos)


class AuditService:
    def __init__(self, repo, esc_actas, esc_acuerdos, matcher: NameMatcher):
        self._repo, self._esc_actas, self._esc_acuerdos, self._matcher = repo, esc_actas, esc_acuerdos, matcher

    async def auditar(self, ruta_actas, ruta_acuerdos) -> ReporteAuditoria:
        actas_db, acuerdos_db, f_actas, f_acuerdos = await asyncio.gather(
            asyncio.to_thread(self._repo.obtener_actas),
            asyncio.to_thread(self._repo.obtener_acuerdos),
            asyncio.to_thread(self._esc_actas.escanear, ruta_actas),
            asyncio.to_thread(self._esc_acuerdos.escanear, ruta_acuerdos),
        )
        return self.conciliar(actas_db, acuerdos_db, f_actas, f_acuerdos)

    def conciliar(self, actas_db, acuerdos_db, f_actas, f_acuerdos) -> ReporteAuditoria:
        por_placa = defaultdict(list)
        for placa, usuario in actas_db:
            por_placa[placa.strip().upper()].append(tokens(usuario))
        indice = IndiceNombres([tokens(u) for u in acuerdos_db], self._matcher)
        reporte = ReporteAuditoria()
        for a in f_actas:
            ts = tokens(a.usuario)
            if not any(self._matcher.coincide(ts, t) for t in por_placa.get(a.placa, [])):
                reporte.actas_faltantes.append(a)
        for ac in f_acuerdos:
            if not indice.contiene(tokens(ac.usuario)):
                reporte.acuerdos_faltantes.append(ac)
        return reporte
