"""
ProveedoresBuilder - Esquemas y operaciones SQL para proveedores y compras
Contiene todas las definiciones de tablas y operaciones de la base de datos de proveedores
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime


class ProveedoresBuilder:
    """Constructor de base de datos de proveedores y compras"""
    
    DB_PATH = Path("./BASEDATOS/provedores.db")
    
    # ==================== ESQUEMAS SQL ====================
    
    SCHEMA_PROVEEDORES = """
        CREATE TABLE IF NOT EXISTS proveedores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            contacto    TEXT,
            telefono    TEXT,
            email       TEXT,
            direccion   TEXT,
            activo      INTEGER DEFAULT 1,
            creado_en   TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    SCHEMA_COMPRAS = """
        CREATE TABLE IF NOT EXISTS compras (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            folio         TEXT UNIQUE,
            fecha         TEXT NOT NULL,
            proveedor_id  INTEGER,
            total         REAL DEFAULT 0,
            estado        TEXT DEFAULT 'Pendiente',
            notas         TEXT,
            creado_en     TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        )
    """
    
    SCHEMA_DETALLE_COMPRAS = """
        CREATE TABLE IF NOT EXISTS detalle_compras (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            compra_id       INTEGER,
            producto        TEXT NOT NULL,
            cantidad        INTEGER DEFAULT 1,
            precio_unitario REAL DEFAULT 0,
            total           REAL DEFAULT 0,
            FOREIGN KEY (compra_id) REFERENCES compras(id)
        )
    """
    
    # ==================== MÉTODOS ====================
    
    @classmethod
    def get_conexion(cls) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos de proveedores"""
        os.makedirs(cls.DB_PATH.parent, exist_ok=True)
        conn = sqlite3.connect(str(cls.DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    @classmethod
    def inicializar_bd(cls):
        """Inicializa la base de datos con todas las tablas necesarias"""
        with cls.get_conexion() as conn:
            conn.execute(cls.SCHEMA_PROVEEDORES)
            conn.execute(cls.SCHEMA_COMPRAS)
            conn.execute(cls.SCHEMA_DETALLE_COMPRAS)
            conn.commit()
        print("✓ Base de datos de proveedores inicializada")
    
    @classmethod
    def obtener_proveedores_activos(cls):
        """Obtiene todos los proveedores activos"""
        try:
            with cls.get_conexion() as conn:
                cursor = conn.execute("""
                    SELECT * FROM proveedores 
                    WHERE activo = 1
                    ORDER BY nombre
                """)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo proveedores: {e}")
            return []
    
    @classmethod
    def generar_folio_compra(cls) -> str:
        """Genera un folio único para una nueva compra"""
        try:
            fecha = datetime.now().strftime("%Y%m%d")
            with cls.get_conexion() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total FROM compras 
                    WHERE folio LIKE ?
                """, (f"C{fecha}%",))
                total = cursor.fetchone()["total"]
                return f"C{fecha}{total + 1:04d}"
        except Exception as e:
            print(f"Error generando folio: {e}")
            return f"C{datetime.now().strftime('%Y%m%d')}0001"
    
    @classmethod
    def guardar_compra(cls, folio: str, fecha: str, proveedor_id: int, 
                      total: float, estado: str, notas: str, detalles: list):
        """Guarda una nueva compra con sus detalles"""
        try:
            with cls.get_conexion() as conn:
                # Insertar compra principal
                cursor = conn.execute("""
                    INSERT INTO compras (folio, fecha, proveedor_id, total, estado, notas)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (folio, fecha, proveedor_id, total, estado, notas))
                
                compra_id = cursor.lastrowid
                
                # Insertar detalles
                for detalle in detalles:
                    conn.execute("""
                        INSERT INTO detalle_compras 
                        (compra_id, producto, cantidad, precio_unitario, total)
                        VALUES (?, ?, ?, ?, ?)
                    """, (compra_id, detalle['producto'], detalle['cantidad'], 
                         detalle['precio_unitario'], detalle['total']))
                
                conn.commit()
            return True
        except Exception as e:
            print(f"Error guardando compra: {e}")
            return False
    
    @classmethod
    def obtener_compras(cls, filtro_estado: str = "Todos"):
        """Obtiene todas las compras con filtro opcional"""
        try:
            with cls.get_conexion() as conn:
                if filtro_estado == "Todos":
                    cursor = conn.execute("""
                        SELECT c.*, p.nombre as proveedor_nombre
                        FROM compras c
                        LEFT JOIN proveedores p ON c.proveedor_id = p.id
                        ORDER BY c.creado_en DESC
                    """)
                else:
                    cursor = conn.execute("""
                        SELECT c.*, p.nombre as proveedor_nombre
                        FROM compras c
                        LEFT JOIN proveedores p ON c.proveedor_id = p.id
                        WHERE c.estado = ?
                        ORDER BY c.creado_en DESC
                    """, (filtro_estado,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo compras: {e}")
            return []
    
    @classmethod
    def obtener_detalles_compra(cls, compra_id: int):
        """Obtiene los detalles de una compra específica"""
        try:
            with cls.get_conexion() as conn:
                cursor = conn.execute("""
                    SELECT * FROM detalle_compras 
                    WHERE compra_id = ?
                """, (compra_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo detalles de compra: {e}")
            return []
    
    @classmethod
    def actualizar_estado_compra(cls, compra_id: int, nuevo_estado: str):
        """Actualiza el estado de una compra"""
        try:
            with cls.get_conexion() as conn:
                conn.execute("""
                    UPDATE compras 
                    SET estado = ?
                    WHERE id = ?
                """, (nuevo_estado, compra_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error actualizando estado de compra: {e}")
            return False
