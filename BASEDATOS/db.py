"""
BASEDATOS/db.py - Módulo centralizado de acceso a bases de datos
Utiliza los builders de BuilderSql para operaciones SQL

Este módulo sirve como capa de compatibilidad para el código existente,
delegando todas las operaciones SQL a los builders correspondientes en BuilderSql/
"""

import sqlite3
import json
import datetime
from pathlib import Path

# Importar builders de SQL
from BuilderSql import VentasBuilder, UsuariosBuilder, ContratosBuilder

DB_FOLDER = Path("BASEDATOS")
DB_FILE   = DB_FOLDER / "ventas.db"
JSON_FILE = Path("Json files/users.json")

DB_FOLDER.mkdir(exist_ok=True)

def get_conexion():
    """Retorna una conexión a la base de datos de ventas"""
    return VentasBuilder.get_conexion()

# ==================== FUNCIONES DE USUARIOS ====================

def _leer_usuarios_json():
    """Devuelve lista de dicts con 'nombre' + propiedades del JSON"""
    return UsuariosBuilder._leer_usuarios_json()

def _columnas_dinamicas(dict_list):
    """Obtiene todas las keys únicas del JSON para crear columnas"""
    return UsuariosBuilder._columnas_dinamicas(dict_list)

def _columna_existe(cur, tabla, columna):
    """Verifica si una columna existe en una tabla"""
    return UsuariosBuilder._columna_existe(cur, tabla, columna)

def inicializar_bd():
    """Inicializa todas las bases de datos del sistema"""
    print("🔧 Inicializando bases de datos...")
    
    # Inicializar tabla de usuarios
    UsuariosBuilder.inicializar_bd()
    
    # Inicializar tablas de ventas y auditoría
    VentasBuilder.inicializar_bd()
    
    # Inicializar tabla de contratos
    ContratosBuilder.inicializar_bd()
    
    print("✅ Todas las bases de datos inicializadas correctamente")

# ==================== FUNCIONES DE VENTAS ====================

def ventas_del_dia(usuario: str):
    """Retorna el total de ventas del día para un usuario"""
    return VentasBuilder.ventas_del_dia(usuario)

def ultimas_ventas(usuario: str, limite=10):
    """Retorna las últimas ventas de un usuario con formato (hora, producto, monto)"""
    return VentasBuilder.ultimas_ventas(usuario, limite)

def guardar_venta(usuario: str, carrito: list[dict], tipo_venta: str = "Normal"):
    """Guarda una venta con sus detalles"""
    return VentasBuilder.guardar_venta(usuario, carrito, tipo_venta)

def obtener_detalle_venta(venta_id: int):
    """Obtiene los detalles de una venta específica"""
    try:
        con = get_conexion()
        cur = con.cursor()
        cur.execute("""
            SELECT producto, cantidad, precio_unit
            FROM ventas_detalle
            WHERE venta_id = ?
            ORDER BY id
        """, (venta_id,))
        rows = cur.fetchall()
        con.close()
        return rows
    except Exception as e:
        print(f"Error obteniendo detalle de venta: {e}")
        return []

def total_ventas_periodo(usuario: str = None, fecha_inicio: str = None, fecha_fin: str = None):
    """Calcula el total de ventas en un período"""
    try:
        con = get_conexion()
        cur = con.cursor()
        
        query = "SELECT SUM(total) FROM ventas WHERE 1=1"
        params = []
        
        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)
        
        if fecha_inicio:
            query += " AND fecha >= ?"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND fecha <= ?"
            params.append(fecha_fin)
        
        cur.execute(query, params)
        total = cur.fetchone()[0] or 0.0
        con.close()
        return total
        
    except Exception as e:
        print(f"Error calculando total de período: {e}")
        return 0.0

# ==================== FUNCIONES DE AUDITORÍA ====================

def registrar_auditoria(usuario: str, tipo: str, descripcion: str, detalles: str = ""):
    """Registra una acción en la auditoría"""
    return VentasBuilder.registrar_auditoria(usuario, tipo, descripcion, detalles)

def obtener_auditoria(usuario: str = None, tipo: str = None, fecha_inicio: str = None, fecha_fin: str = None, limite: int = 1000):
    """Obtiene registros de auditoría con filtros opcionales"""
    try:
        con = get_conexion()
        cur = con.cursor()
        
        query = "SELECT * FROM auditoria WHERE 1=1"
        params = []
        
        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)
        
        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)
        
        if fecha_inicio:
            query += " AND fecha_hora >= ?"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND fecha_hora <= ?"
            params.append(fecha_fin)
        
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limite)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        con.close()
        return rows
        
    except Exception as e:
        print(f"Error obteniendo auditoría: {e}")
        return []

def obtener_estadisticas_auditoria():
    """Obtiene estadísticas generales de auditoría"""
    try:
        con = get_conexion()
        cur = con.cursor()
        
        # Total de registros
        total = cur.execute("SELECT COUNT(*) as count FROM auditoria").fetchone()[0]
        
        # Por tipo
        por_tipo = {}
        cur.execute("SELECT tipo, COUNT(*) as count FROM auditoria GROUP BY tipo ORDER BY count DESC")
        for row in cur.fetchall():
            por_tipo[row[0]] = row[1]
        
        # Por usuario
        por_usuario = {}
        cur.execute("SELECT usuario, COUNT(*) as count FROM auditoria GROUP BY usuario ORDER BY count DESC LIMIT 10")
        for row in cur.fetchall():
            por_usuario[row[0]] = row[1]
        
        con.close()
        
        return {
            "total": total,
            "por_tipo": por_tipo,
            "por_usuario": por_usuario
        }
        
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return {"total": 0, "por_tipo": {}, "por_usuario": {}}

def eliminar_registros_auditoria(fecha_inicio: str = None, fecha_fin: str = None, tipo: str = None, usuario: str = None):
    """Elimina registros de auditoría con filtros opcionales"""
    try:
        con = get_conexion()
        cur = con.cursor()
        
        query = "DELETE FROM auditoria WHERE 1=1"
        params = []
        
        if fecha_inicio:
            query += " AND fecha_hora >= ?"
            params.append(fecha_inicio)
        
        if fecha_fin:
            query += " AND fecha_hora <= ?"
            params.append(fecha_fin)
        
        if tipo:
            query += " AND tipo = ?"
            params.append(tipo)
        
        if usuario:
            query += " AND usuario = ?"
            params.append(usuario)
        
        cur.execute(query, params)
        eliminados = cur.rowcount
        con.commit()
        con.close()
        
        return eliminados
        
    except Exception as e:
        print(f"Error eliminando registros: {e}")
        return 0

def exportar_auditoria_pdf(registros: list, ruta_archivo: str):
    """
    Exporta registros de auditoría a un archivo PDF
    
    Args:
        registros: Lista de tuplas con los registros de auditoría
        ruta_archivo: Ruta completa donde se guardará el PDF
    
    Returns:
        bool: True si se exportó correctamente, False en caso contrario
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(ruta_archivo, pagesize=A4)
        elementos = []
        
        # Estilos
        estilos = getSampleStyleSheet()
        titulo_estilo = ParagraphStyle(
            'CustomTitle',
            parent=estilos['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=30,
            alignment=1  # Centrado
        )
        
        # Título
        elementos.append(Paragraph("Reporte de Auditoría del Sistema", titulo_estilo))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Información del reporte
        info_estilo = estilos['Normal']
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        elementos.append(Paragraph(f"<b>Fecha de generación:</b> {fecha_actual}", info_estilo))
        elementos.append(Paragraph(f"<b>Total de registros:</b> {len(registros)}", info_estilo))
        elementos.append(Spacer(1, 0.3*inch))
        
        # Preparar datos para la tabla
        datos = [['Fecha/Hora', 'Usuario', 'Tipo', 'Descripción']]
        
        for reg in registros:
            # reg = (id, fecha_hora, usuario, tipo, descripcion, detalles)
            fila = [
                reg[1][:16] if reg[1] else '',  # Fecha/Hora (acortado)
                reg[2] if reg[2] else '',  # Usuario
                reg[3].upper() if reg[3] else '',  # Tipo
                (reg[4][:40] + '...') if reg[4] and len(reg[4]) > 40 else (reg[4] if reg[4] else '')  # Descripción
            ]
            datos.append(fila)
        
        # Crear tabla
        tabla = Table(datos, colWidths=[2*inch, 1.5*inch, 1.2*inch, 2.8*inch])
        
        # Estilo de la tabla
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')])
        ]))
        
        elementos.append(tabla)
        
        # Construir PDF
        doc.build(elementos)
        
        return True
        
    except Exception as e:
        print(f"Error al exportar auditoría a PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
