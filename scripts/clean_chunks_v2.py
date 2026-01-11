#!/usr/bin/env python3
"""
Script de Limpieza y Consolidación de Chunks RAG - Versión 2
=============================================================
Mejoras sobre v1:
- Reparación inteligente de capítulos "GENERAL"
- Filtrado estricto de requisitos (sin headers)
- Control de integridad (sin truncamientos)
- Formateo mejorado de párrafos

Autor: Claude Code
Fecha: 2024-01-10
"""

import json
import re
from typing import List, Dict, Any
from pathlib import Path


class ChunkCleanerV2:
    """Limpia y consolida chunks RAG fragmentados con validaciones estrictas."""

    def __init__(self):
        self.continuation_patterns = [
            r'\(continuaci[oó]n\)',
            r'continuaci[oó]n',
            r'viene de',
            r'\(cont\.',
            r'\(sigue\)'
        ]

        # Mapeo de keywords a capítulos
        self.chapter_keywords = {
            "CAPITULO IV: FACTURACIÓN Y LIQUIDACIÓN": [
                'facturación', 'facturacion', 'liquidación', 'liquidacion',
                'débito', 'debito', 'refacturación', 'refacturacion',
                'iva', 'factura', 'detalle de facturación', 'troquel',
                'kairos', 'cedim'
            ],
            "CAPITULO II: ACCESO Y AUTORIZACIONES": [
                'admisión', 'admision', 'psicología', 'psicologia',
                'turnos', 'salud mental', 'autorización', 'autorizacion',
                'gestión de autorizaciones', 'portal de prestadores',
                'validación', 'validacion', 'ambulatoria', 'ambulatorio'
            ],
            "CAPITULO III: GESTIÓN DE INTERNACIONES": [
                'prórroga', 'prorroga', 'internación', 'internacion',
                'traslado', 'traslados', 'derivación', 'derivacion',
                'censo diario', 'egreso', 'denuncia de internación',
                'historia clínica', 'cirugía programada', 'internado'
            ]
        }

    def infer_chapter(self, texto: str, seccion: str) -> str:
        """Infiere el capítulo basándose en el contenido del texto."""
        texto_lower = (texto + " " + seccion).lower()

        # Contar matches por capítulo
        scores = {}
        for chapter, keywords in self.chapter_keywords.items():
            score = sum(1 for kw in keywords if kw in texto_lower)
            if score > 0:
                scores[chapter] = score

        # Retornar el capítulo con mayor score
        if scores:
            return max(scores, key=scores.get)

        # Default: CAPITULO I si no hay match
        return "CAPITULO I: ACUERDO DE COBERTURA"

    def is_continuation(self, texto: str) -> bool:
        """Detecta si un chunk es continuación de otro."""
        texto_lower = texto.lower()
        return any(re.search(pattern, texto_lower) for pattern in self.continuation_patterns)

    def is_empty_header(self, chunk: Dict) -> bool:
        """Detecta si un chunk es solo un título vacío."""
        texto = chunk.get('texto', '').strip()

        # Títulos típicos: CAPITULO II, INTRODUCCION, etc.
        if len(texto) < 100 and re.match(r'^[A-ZÁÉÍÓÚ\s]+\d*$', texto.upper()):
            return True

        # Chunk con solo título de capítulo/sección
        if texto.upper().startswith(('CAPITULO', 'ANEXO', 'INTRODUCCION')):
            # Si tiene menos de 2 líneas, es solo un header
            if texto.count('\n') < 2:
                return True

        return False

    def extract_contacts(self, texto: str) -> List[Dict[str, str]]:
        """Extrae emails y teléfonos del texto."""
        contactos = []

        # Regex para emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', texto)
        for email in set(emails):  # Eliminar duplicados
            contactos.append({"tipo": "email", "valor": email})

        # Regex para teléfonos (argentinos)
        phones = re.findall(r'\b(?:0810-\d{3}-\d{4}|\d{4}-\d{4}|\d{2}-\d{1}-\d{3}-\d{4}|\d{2}-\d{4}-\d{4})\b', texto)
        for phone in set(phones):  # Eliminar duplicados
            contactos.append({"tipo": "telefono", "valor": phone})

        return contactos

    def extract_requirements(self, texto: str) -> List[str]:
        """Extrae requisitos y documentación obligatoria (FILTRADO ESTRICTO)."""
        requisitos = []
        texto_lower = texto.lower()

        # Patrones de requisitos
        req_keywords = [
            'requisito', 'obligatorio', 'debe presentar', 'documentación requerida',
            'orden médica', 'autorización', 'credencial', 'dni', 'documento de identidad',
            'deberá presentar', 'deberá adjuntar', 'debe adjuntar'
        ]

        for keyword in req_keywords:
            if keyword in texto_lower:
                # Buscar la oración que contiene el keyword
                sentences = re.split(r'[.!?\n]', texto)
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 10:
                        req = sentence.strip()

                        # FILTRADO ESTRICTO: Rechazar headers y títulos
                        if req.startswith('#'):
                            continue
                        if req.endswith(':'):
                            continue
                        if re.match(r'^[A-ZÁÉÍÓÚÑ\s]+$', req):  # Todo en mayúsculas
                            continue
                        if len(req) > 200:  # Muy largo, probablemente no es un requisito
                            continue

                        requisitos.append(req)

        return list(set(requisitos))[:5]  # Max 5, sin duplicados

    def extract_alerts(self, texto: str) -> List[str]:
        """Extrae alertas, restricciones y causas de débitos."""
        alertas = []
        texto_lower = texto.lower()

        # Patrones de alerta
        alert_keywords = [
            'débito', 'debito', 'restricción', 'no se aceptará',
            'será pasible', 'causa de rechazo', 'no será reconocido',
            'motivo de débito', 'no refacturable', 'prohibido',
            'no se acepta', 'falta de'
        ]

        for keyword in alert_keywords:
            if keyword in texto_lower:
                sentences = re.split(r'[.!?\n]', texto)
                for sentence in sentences:
                    if keyword in sentence.lower() and len(sentence.strip()) > 10:
                        alert = sentence.strip()

                        # Filtrar títulos
                        if alert.startswith('#') or alert.endswith(':'):
                            continue
                        if len(alert) > 250:
                            continue

                        alertas.append(alert)

        return list(set(alertas))[:5]

    def extract_plans(self, texto: str) -> List[str]:
        """Extrae planes mencionados (ASI 350P/400/450 -> lista individual)."""
        planes = set()

        # Buscar patrones como "Asi 350P / 400 / 450"
        plan_pattern = r'(?:Asi|ASI)\s*(\d{3}[A-Z]?(?:\s*/\s*\d{3}[A-Z]?)*)'
        matches = re.findall(plan_pattern, texto, re.IGNORECASE)

        for match in matches:
            # Dividir "350P / 400 / 450" en planes individuales
            parts = re.split(r'\s*/\s*', match)
            for part in parts:
                planes.add(f"ASI {part.strip()}")

        # Buscar planes específicos comunes
        common_plans = ['Blanco', 'Exclusive', 'Evolution']
        for plan in common_plans:
            if re.search(rf'\b{plan}\b', texto, re.IGNORECASE):
                planes.add(plan)

        return sorted(list(planes))

    def fix_table(self, texto: str) -> Dict[str, Any]:
        """Valida y corrige formato de tablas Markdown."""
        lines = texto.split('\n')
        table_lines = [l for l in lines if '|' in l]

        if not table_lines:
            return {"valid": True, "texto": texto}

        # Contar pipes en la primera línea de tabla
        expected_pipes = table_lines[0].count('|')

        errors = []
        fixed_lines = []

        for i, line in enumerate(lines):
            if '|' not in line:
                fixed_lines.append(line)
                continue

            # Remover saltos de línea internos
            cleaned = line.replace('\\n', ' / ').replace('\r', '')

            # Verificar número de pipes
            pipe_count = cleaned.count('|')
            if pipe_count != expected_pipes:
                errors.append(f"Línea {i+1}: esperados {expected_pipes} pipes, encontrados {pipe_count}")
                # Intentar arreglar agregando pipes faltantes
                if pipe_count < expected_pipes:
                    cleaned += ' |' * (expected_pipes - pipe_count)

            fixed_lines.append(cleaned)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "texto": '\n'.join(fixed_lines)
        }

    def improve_paragraph_formatting(self, texto: str) -> str:
        """Mejora el formateo de párrafos para mejor legibilidad."""
        # No aplicar a tablas
        if '|' in texto and '---' in texto:
            return texto

        # Separar párrafos con doble salto de línea
        # Pero mantener listas y estructuras existentes
        lines = texto.split('\n')
        formatted = []
        prev_was_empty = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Preservar líneas vacías existentes
            if not stripped:
                if not prev_was_empty:
                    formatted.append('')
                    prev_was_empty = True
                continue

            # Preservar formato Markdown (headers, listas)
            if stripped.startswith(('#', '-', '*', '1.', '2.', '3.')):
                formatted.append(line)
                prev_was_empty = False
                continue

            # Agregar línea normal
            formatted.append(line)
            prev_was_empty = False

            # Agregar salto de línea después de oraciones completas
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                # Si la siguiente línea no está vacía y no es lista/header
                if next_line and not next_line.startswith(('#', '-', '*', '1.', '2.', '3.')):
                    # Si la línea actual termina en punto
                    if stripped.endswith(('.', ':', ')')):
                        formatted.append('')

        return '\n'.join(formatted)

    def merge_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Fusiona chunks fragmentados en bloques lógicos."""
        merged = []
        buffer = None

        for i, chunk in enumerate(chunks):
            # Saltar headers vacíos
            if self.is_empty_header(chunk):
                # Guardar el capítulo para aplicarlo al próximo chunk
                if buffer is None:
                    buffer = {
                        "capitulo": chunk.get("capitulo", chunk.get("seccion", "GENERAL")),
                        "texto_acumulado": ""
                    }
                continue

            # Detectar continuación
            is_cont = self.is_continuation(chunk.get('texto', ''))
            same_section = (
                buffer and
                chunk.get('seccion') == buffer.get('seccion_anterior')
            )

            if is_cont or same_section:
                # Fusionar con buffer
                if buffer:
                    buffer['texto_acumulado'] += "\n\n" + chunk.get('texto', '')
                else:
                    # No hay buffer, crear uno
                    buffer = {
                        "capitulo": chunk.get("capitulo", "GENERAL"),
                        "seccion": chunk.get("seccion", "GENERAL"),
                        "texto_acumulado": chunk.get('texto', ''),
                        "seccion_anterior": chunk.get("seccion")
                    }
            else:
                # Guardar buffer anterior si existe
                if buffer and buffer.get('texto_acumulado') and len(buffer['texto_acumulado'].strip()) > 50:
                    merged.append(self._create_clean_chunk(buffer, chunk))
                elif buffer and buffer.get('texto_acumulado'):
                    # Chunk muy corto, fusionar con el siguiente
                    print(f"⚠️  Chunk muy corto detectado, fusionando...")
                    buffer['texto_acumulado'] += "\n\n" + chunk.get('texto', '')
                    buffer['seccion'] = chunk.get('seccion', buffer.get('seccion', 'GENERAL'))
                    continue

                # Iniciar nuevo buffer
                buffer = {
                    "obra_social": chunk.get("obra_social", "ASI"),
                    "archivo": chunk.get("archivo", "unknown.docx"),
                    "capitulo": chunk.get("capitulo", "GENERAL"),
                    "seccion": chunk.get("seccion", "GENERAL"),
                    "texto_acumulado": chunk.get('texto', ''),
                    "tipo": chunk.get("tipo", "docx-texto"),
                    "es_tabla": chunk.get("es_tabla", False),
                    "seccion_anterior": chunk.get("seccion"),
                    "moneda": chunk.get("moneda", "ARS")
                }

        # Guardar último buffer (CONTROL DE INTEGRIDAD)
        if buffer and buffer.get('texto_acumulado') and len(buffer['texto_acumulado'].strip()) > 50:
            merged.append(self._create_clean_chunk(buffer, {}))
        elif buffer and buffer.get('texto_acumulado'):
            # Último chunk muy corto, agregar al anterior
            if merged:
                print(f"⚠️  Último chunk muy corto, fusionando con el anterior...")
                merged[-1]['texto'] += "\n\n" + buffer['texto_acumulado']
            else:
                # No hay chunks previos, guardarlo de todas formas
                merged.append(self._create_clean_chunk(buffer, {}))

        return merged

    def _create_clean_chunk(self, buffer: Dict, reference_chunk: Dict) -> Dict:
        """Crea un chunk limpio y enriquecido."""
        texto = buffer['texto_acumulado'].strip()

        # Limpiar texto de marcas de continuación
        for pattern in self.continuation_patterns:
            texto = re.sub(pattern, '', texto, flags=re.IGNORECASE)

        # Limpiar múltiples saltos de línea (máximo 2)
        texto = re.sub(r'\n{3,}', '\n\n', texto)

        # Corregir tablas si es necesario
        if buffer.get('es_tabla'):
            table_result = self.fix_table(texto)
            texto = table_result['texto']
            if not table_result['valid']:
                print(f"⚠️  Advertencia en tabla: {table_result.get('errors', [])}")
        else:
            # Mejorar formateo de párrafos (solo para no-tablas)
            texto = self.improve_paragraph_formatting(texto)

        # Extraer metadata
        contactos = self.extract_contacts(texto)
        requisitos = self.extract_requirements(texto)
        alertas = self.extract_alerts(texto)
        planes = self.extract_plans(texto)

        # Detectar temas clave
        temas_keywords = [
            'autorización', 'facturación', 'internación', 'ambulatorio',
            'coseguro', 'prestación', 'guardia', 'cirugía', 'módulo',
            'liquidación', 'débito', 'refacturación'
        ]
        temas = [kw for kw in temas_keywords if kw in texto.lower()]

        # Inferir capítulo si es "GENERAL"
        capitulo = buffer.get("capitulo", "GENERAL")
        if capitulo == "GENERAL" or "GENERAL" in capitulo.upper():
            capitulo = self.infer_chapter(texto, buffer.get("seccion", ""))
            print(f"✓ Capítulo inferido: {capitulo[:50]}...")

        # Construir chunk limpio
        clean_chunk = {
            "obra_social": buffer.get("obra_social", "ASI"),
            "archivo": buffer.get("archivo", "unknown.docx"),
            "capitulo": capitulo,
            "seccion": buffer.get("seccion", "GENERAL"),
            "texto": texto,
            "tipo": buffer.get("tipo", "docx-texto"),
            "es_tabla": buffer.get("es_tabla", False),
            "metadata": {
                "temas_clave": temas,
                "planes": planes,
                "contactos": contactos,
                "requisitos": requisitos,
                "alertas": alertas
            }
        }

        # Agregar moneda si existe
        if buffer.get("moneda"):
            clean_chunk["moneda"] = buffer["moneda"]

        return clean_chunk

    def validate_output(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Valida la calidad del output."""
        stats = {
            "total_chunks": len(chunks),
            "chunks_con_tablas": 0,
            "chunks_sin_texto": 0,
            "chunks_con_contactos": 0,
            "chunks_con_alertas": 0,
            "chunks_con_requisitos": 0,
            "chunks_con_general": 0,
            "obras_sociales": set(),
            "capitulos": set(),
            "longitud_promedio": 0,
            "longitud_min": float('inf'),
            "longitud_max": 0
        }

        longitudes = []

        for chunk in chunks:
            texto_len = len(chunk.get("texto", ""))
            longitudes.append(texto_len)

            if texto_len < stats["longitud_min"]:
                stats["longitud_min"] = texto_len
            if texto_len > stats["longitud_max"]:
                stats["longitud_max"] = texto_len

            if chunk.get("es_tabla"):
                stats["chunks_con_tablas"] += 1

            if not chunk.get("texto", "").strip():
                stats["chunks_sin_texto"] += 1

            if chunk.get("metadata", {}).get("contactos"):
                stats["chunks_con_contactos"] += 1

            if chunk.get("metadata", {}).get("alertas"):
                stats["chunks_con_alertas"] += 1

            if chunk.get("metadata", {}).get("requisitos"):
                stats["chunks_con_requisitos"] += 1

            capitulo = chunk.get("capitulo", "")
            if "GENERAL" in capitulo.upper():
                stats["chunks_con_general"] += 1

            stats["obras_sociales"].add(chunk.get("obra_social", "UNKNOWN"))
            stats["capitulos"].add(capitulo)

        stats["longitud_promedio"] = sum(longitudes) // len(longitudes) if longitudes else 0
        stats["obras_sociales"] = sorted(list(stats["obras_sociales"]))
        stats["capitulos"] = sorted(list(stats["capitulos"]))

        return stats

    def clean_file(self, input_path: str, output_path: str = None) -> Dict[str, Any]:
        """Limpia un archivo JSON de chunks."""
        print(f"📂 Leyendo: {input_path}")

        with open(input_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        print(f"📊 Chunks originales: {len(chunks)}")

        # Procesar
        print("🔧 Fusionando y limpiando chunks...")
        merged = self.merge_chunks(chunks)

        print(f"✅ Chunks consolidados: {len(merged)}")

        # Validar
        stats = self.validate_output(merged)

        # Guardar
        if output_path is None:
            output_path = input_path.replace('.json', '_cleaned_v2.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        print(f"💾 Guardado en: {output_path}")
        print(f"\n📈 Estadísticas:")
        print(f"   - Obras Sociales: {', '.join(stats['obras_sociales'])}")
        print(f"   - Capítulos únicos: {len(stats['capitulos'])}")
        print(f"   - Chunks con tablas: {stats['chunks_con_tablas']}")
        print(f"   - Chunks con contactos: {stats['chunks_con_contactos']}")
        print(f"   - Chunks con alertas: {stats['chunks_con_alertas']}")
        print(f"   - Chunks con requisitos: {stats['chunks_con_requisitos']}")
        print(f"   - Longitud promedio: {stats['longitud_promedio']} caracteres")
        print(f"   - Longitud mín/máx: {stats['longitud_min']} / {stats['longitud_max']}")

        if stats['chunks_con_general'] > 0:
            print(f"   ⚠️  Chunks con GENERAL: {stats['chunks_con_general']}")

        if stats['chunks_sin_texto'] > 0:
            print(f"   ⚠️  Chunks sin texto: {stats['chunks_sin_texto']}")

        return stats


def main():
    """Función principal."""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python clean_chunks_v2.py <archivo_input.json> [archivo_output.json]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    cleaner = ChunkCleanerV2()
    cleaner.clean_file(input_file, output_file)


if __name__ == "__main__":
    main()
