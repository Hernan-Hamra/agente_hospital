"""
Motor de consultas SQL para Escenario 2.

Sin LLM - Solo lookup + formateo.
"""
import sqlite3
from typing import Dict, Optional, List
from dataclasses import dataclass

from .normalizer import NormalizedQuery


@dataclass
class QueryResult:
    """Resultado de una consulta."""
    success: bool
    respuesta: str
    data: Optional[Dict] = None
    error: Optional[str] = None


class QueryEngine:
    """
    Motor de consultas estructuradas.

    Flujo:
    1. Recibe NormalizedQuery
    2. Ejecuta SQL según tipo_ingreso
    3. Formatea respuesta
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def query(self, normalized: NormalizedQuery) -> QueryResult:
        """
        Ejecuta una consulta normalizada.

        Args:
            normalized: Query normalizada con obra_social y tipo_ingreso

        Returns:
            QueryResult con respuesta formateada
        """
        # Validar query
        if not normalized.is_valid:
            return self._missing_info_response(normalized)

        # Verificar restricciones temporales
        restriccion = self._check_restricciones(
            normalized.obra_social,
            normalized.tipo_ingreso
        )

        # Obtener requisitos
        requisitos = self._get_requisitos(
            normalized.obra_social,
            normalized.tipo_ingreso
        )

        if not requisitos:
            return QueryResult(
                success=False,
                respuesta=f"No tengo información de {normalized.tipo_ingreso} para {normalized.obra_social}.",
                error="not_found"
            )

        # Formatear respuesta según tipo
        respuesta = self._format_response(requisitos, normalized)

        # Agregar alerta de restricción si existe
        if restriccion:
            respuesta = f"⛔ ATENCIÓN: {restriccion['mensaje']}\n\n{respuesta}"

        return QueryResult(
            success=True,
            respuesta=respuesta,
            data=dict(requisitos)
        )

    def _check_restricciones(self, obra_social: str, tipo_ingreso: str) -> Optional[Dict]:
        """Verifica si hay restricciones activas para esta obra social y tipo."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT r.*, os.nombre as obra_social_nombre
            FROM restricciones r
            JOIN obras_sociales os ON r.obra_social_id = os.id
            WHERE os.codigo = ?
              AND r.activa = 1
              AND (r.fecha_fin IS NULL OR r.fecha_fin >= date('now'))
              AND r.fecha_inicio <= date('now')
        """, (obra_social,))

        restricciones = cursor.fetchall()

        for rest in restricciones:
            # Verificar si este tipo está bloqueado
            tipos_bloqueados = rest['tipos_bloqueados']
            tipos_permitidos = rest['tipos_permitidos']

            if tipos_bloqueados:
                bloqueados = [t.strip() for t in tipos_bloqueados.split(',')]
                if tipo_ingreso in bloqueados:
                    return dict(rest)

            if tipos_permitidos:
                permitidos = [t.strip() for t in tipos_permitidos.split(',')]
                if tipo_ingreso not in permitidos:
                    return dict(rest)

        return None

    def _get_requisitos(self, obra_social: str, tipo_ingreso: str) -> Optional[sqlite3.Row]:
        """Obtiene requisitos de la DB."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT r.*, os.nombre as obra_social_nombre, os.telefono, os.email, os.portal
            FROM requisitos r
            JOIN obras_sociales os ON r.obra_social_id = os.id
            WHERE os.codigo = ? AND r.tipo_ingreso = ?
        """, (obra_social, tipo_ingreso))

        return cursor.fetchone()

    def _missing_info_response(self, normalized: NormalizedQuery) -> QueryResult:
        """Genera respuesta cuando falta información."""
        missing = []

        if not normalized.obra_social:
            missing.append("obra social (ej: ENSALUD, ASI, IOSFA)")

        if not normalized.tipo_ingreso:
            missing.append("tipo de ingreso (ambulatorio, internación, guardia, traslados)")

        return QueryResult(
            success=False,
            respuesta=f"Para ayudarte necesito que me indiques: {', '.join(missing)}",
            error="missing_info"
        )

    def _format_response(self, req: sqlite3.Row, normalized: NormalizedQuery) -> str:
        """Formatea la respuesta según el tipo de ingreso."""
        tipo = normalized.tipo_ingreso

        if tipo == "ambulatorio":
            return self._format_ambulatorio(req)
        elif tipo == "internacion":
            return self._format_internacion(req)
        elif tipo == "guardia":
            return self._format_guardia(req)
        elif tipo == "traslados":
            return self._format_traslados(req)
        else:
            return self._format_generico(req)

    def _format_ambulatorio(self, req: sqlite3.Row) -> str:
        """Formato para ingreso ambulatorio."""
        lines = [f"📋 INGRESO AMBULATORIO - {req['obra_social_nombre']}"]
        lines.append("")

        if req['documentacion']:
            lines.append(f"📄 Documentación: {req['documentacion']}")

        if req['validador_link']:
            lines.append(f"🔗 Portal: {req['validador_link']}")

        if req['validador_telefono']:
            lines.append(f"📞 Teléfono: {req['validador_telefono']}")

        if req['coseguro_aplica']:
            lines.append(f"💰 Coseguro: Según plan (consultar valores)")
        else:
            lines.append(f"💰 Coseguro: NO aplica")

        if req['notas']:
            lines.append(f"\n⚠️ {req['notas']}")

        return "\n".join(lines)

    def _format_internacion(self, req: sqlite3.Row) -> str:
        """Formato para internación."""
        lines = [f"🏥 INTERNACIÓN - {req['obra_social_nombre']}"]
        lines.append("")

        if req['documentacion']:
            lines.append(f"📄 Documentación: {req['documentacion']}")

        if req['mail_denuncia']:
            lines.append(f"📧 Mail denuncia: {req['mail_denuncia']}")

        if req['plazo_denuncia']:
            lines.append(f"⏰ Plazo: {req['plazo_denuncia']}")

        if req['validador_link']:
            lines.append(f"🔗 Portal: {req['validador_link']}")

        if req['validador_telefono']:
            lines.append(f"📞 Teléfono: {req['validador_telefono']}")

        if req['notas']:
            lines.append(f"\n⚠️ {req['notas']}")

        return "\n".join(lines)

    def _format_guardia(self, req: sqlite3.Row) -> str:
        """Formato para guardia."""
        lines = [f"🚨 GUARDIA - {req['obra_social_nombre']}"]
        lines.append("")

        if req['documentacion']:
            lines.append(f"📄 Documentación: {req['documentacion']}")

        if req['validador_link']:
            lines.append(f"🔗 Portal: {req['validador_link']}")

        if req['validador_telefono']:
            lines.append(f"📞 Teléfono: {req['validador_telefono']}")

        # Guardia generalmente no tiene coseguro
        lines.append(f"💰 Coseguro: EXENTO")

        if req['notas']:
            lines.append(f"\n⚠️ {req['notas']}")

        return "\n".join(lines)

    def _format_traslados(self, req: sqlite3.Row) -> str:
        """Formato para traslados."""
        lines = [f"🚑 TRASLADOS - {req['obra_social_nombre']}"]
        lines.append("")

        if req['documentacion']:
            lines.append(f"📄 Documentación: {req['documentacion']}")

        if req['validador_telefono']:
            lines.append(f"📞 Teléfono: {req['validador_telefono']}")

        if req['validador_email']:
            lines.append(f"📧 Email: {req['validador_email']}")

        if req['notas']:
            lines.append(f"\n⚠️ {req['notas']}")

        return "\n".join(lines)

    def _format_generico(self, req: sqlite3.Row) -> str:
        """Formato genérico."""
        lines = [f"📋 {req['tipo_ingreso'].upper()} - {req['obra_social_nombre']}"]
        lines.append("")

        for key in ['documentacion', 'validador_link', 'validador_telefono', 'mail_denuncia', 'notas']:
            if req[key]:
                lines.append(f"• {key}: {req[key]}")

        return "\n".join(lines)

    def query_coseguros(self, obra_social: str, plan: str = None) -> QueryResult:
        """
        Consulta coseguros de una obra social.

        Args:
            obra_social: Código de obra social
            plan: Nombre del plan (opcional)

        Returns:
            QueryResult con valores de coseguros
        """
        cursor = self.conn.cursor()

        if plan:
            cursor.execute("""
                SELECT c.*, os.nombre as obra_social_nombre
                FROM coseguros c
                JOIN obras_sociales os ON c.obra_social_id = os.id
                WHERE os.codigo = ? AND c.plan = ?
            """, (obra_social, plan))
        else:
            cursor.execute("""
                SELECT c.*, os.nombre as obra_social_nombre
                FROM coseguros c
                JOIN obras_sociales os ON c.obra_social_id = os.id
                WHERE os.codigo = ?
                ORDER BY c.plan, c.prestacion
            """, (obra_social,))

        rows = cursor.fetchall()

        if not rows:
            return QueryResult(
                success=False,
                respuesta=f"No tengo información de coseguros para {obra_social}.",
                error="not_found"
            )

        # Formatear
        lines = [f"💰 COSEGUROS - {rows[0]['obra_social_nombre']}"]
        lines.append("")

        current_plan = None
        for row in rows:
            if row['plan'] != current_plan:
                current_plan = row['plan']
                lines.append(f"\n📌 {current_plan}:")

            if row['aplica']:
                lines.append(f"  • {row['prestacion']}: ${row['valor']}")
            else:
                lines.append(f"  • {row['prestacion']}: EXENTO")

        if rows[0]['exentos']:
            lines.append(f"\n⚠️ Exentos: {rows[0]['exentos']}")

        return QueryResult(
            success=True,
            respuesta="\n".join(lines),
            data=[dict(r) for r in rows]
        )

    def add_restriccion(
        self,
        obra_social: str,
        tipo_restriccion: str,
        mensaje: str,
        tipos_bloqueados: str = None,
        tipos_permitidos: str = None,
        fecha_fin: str = None
    ) -> bool:
        """
        Agrega una restricción temporal a una obra social.

        Args:
            obra_social: Código de la obra social
            tipo_restriccion: 'falta_pago', 'convenio_suspendido', etc.
            mensaje: Mensaje a mostrar al usuario
            tipos_bloqueados: Tipos de ingreso bloqueados (coma separado)
            tipos_permitidos: Tipos de ingreso permitidos (coma separado)
            fecha_fin: Fecha de fin de restricción (YYYY-MM-DD) o None si indefinido

        Returns:
            True si se agregó correctamente
        """
        cursor = self.conn.cursor()

        # Obtener ID de obra social
        cursor.execute("SELECT id FROM obras_sociales WHERE codigo = ?", (obra_social,))
        result = cursor.fetchone()
        if not result:
            return False

        os_id = result[0]

        cursor.execute("""
            INSERT INTO restricciones
            (obra_social_id, tipo_restriccion, mensaje, tipos_bloqueados, tipos_permitidos, fecha_inicio, fecha_fin)
            VALUES (?, ?, ?, ?, ?, date('now'), ?)
        """, (os_id, tipo_restriccion, mensaje, tipos_bloqueados, tipos_permitidos, fecha_fin))

        self.conn.commit()
        return True

    def remove_restriccion(self, obra_social: str, tipo_restriccion: str = None) -> int:
        """
        Desactiva restricciones de una obra social.

        Args:
            obra_social: Código de la obra social
            tipo_restriccion: Tipo específico o None para todas

        Returns:
            Número de restricciones desactivadas
        """
        cursor = self.conn.cursor()

        if tipo_restriccion:
            cursor.execute("""
                UPDATE restricciones SET activa = 0
                WHERE obra_social_id = (SELECT id FROM obras_sociales WHERE codigo = ?)
                  AND tipo_restriccion = ?
                  AND activa = 1
            """, (obra_social, tipo_restriccion))
        else:
            cursor.execute("""
                UPDATE restricciones SET activa = 0
                WHERE obra_social_id = (SELECT id FROM obras_sociales WHERE codigo = ?)
                  AND activa = 1
            """, (obra_social,))

        self.conn.commit()
        return cursor.rowcount

    def list_restricciones(self, obra_social: str = None) -> List[Dict]:
        """Lista restricciones activas."""
        cursor = self.conn.cursor()

        if obra_social:
            cursor.execute("""
                SELECT r.*, os.codigo as obra_social_codigo, os.nombre as obra_social_nombre
                FROM restricciones r
                JOIN obras_sociales os ON r.obra_social_id = os.id
                WHERE os.codigo = ? AND r.activa = 1
            """, (obra_social,))
        else:
            cursor.execute("""
                SELECT r.*, os.codigo as obra_social_codigo, os.nombre as obra_social_nombre
                FROM restricciones r
                JOIN obras_sociales os ON r.obra_social_id = os.id
                WHERE r.activa = 1
            """)

        return [dict(r) for r in cursor.fetchall()]
