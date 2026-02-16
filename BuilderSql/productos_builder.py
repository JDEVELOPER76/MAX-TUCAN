"""
ProductosBuilder - Esquemas y operaciones SQL para productos
Contiene todas las definiciones de tablas y operaciones de la base de datos de productos
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime


class ProductosBuilder:
    """Constructor de base de datos de productos"""
    
    DB_PATH = Path("./BASEDATOS/productos.db")
    
    # ==================== ESQUEMAS SQL ====================
    
    SCHEMA_PRODUCTOS = """
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            
            -- Precios y tipos de venta
            precio_compra REAL DEFAULT 0,
            precio_venta_normal REAL DEFAULT 0,
            precio_venta_mayoreo REAL DEFAULT 0,
            precio_venta_promocion REAL DEFAULT 0,
            
            -- Stocks
            stock_actual INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 0,
            stock_maximo INTEGER DEFAULT 0,
            
            -- Configuración de tipos de venta
            venta_normal_activa INTEGER DEFAULT 1,
            venta_mayoreo_activa INTEGER DEFAULT 0,
            venta_promocion_activa INTEGER DEFAULT 0,
            minimo_mayoreo INTEGER DEFAULT 10,
            fecha_inicio_promocion TEXT,
            fecha_fin_promocion TEXT,
            
            -- IVA personalizado
            iva_porcentaje REAL DEFAULT 16.0,
            
            -- Imágenes y multimedia
            imagen_path TEXT,
            especificaciones_json TEXT,
            
            -- Estado
            activo INTEGER DEFAULT 1,
            destacado INTEGER DEFAULT 0,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
            actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    SCHEMA_HISTORIAL_PRECIOS = """
        CREATE TABLE IF NOT EXISTS historial_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            tipo_precio TEXT,
            precio_anterior REAL,
            precio_nuevo REAL,
            fecha_cambio TEXT DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT DEFAULT 'Sistema',
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """
    
    # ==================== MÉTODOS ====================
    
    @classmethod
    def get_conexion(cls) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos de productos"""
        os.makedirs(cls.DB_PATH.parent, exist_ok=True)
        conn = sqlite3.connect(str(cls.DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    @classmethod
    def inicializar_bd(cls):
        """Inicializa la base de datos con todas las tablas necesarias"""
        with cls.get_conexion() as conn:
            conn.execute(cls.SCHEMA_PRODUCTOS)
            conn.execute(cls.SCHEMA_HISTORIAL_PRECIOS)
            conn.commit()
        print("✓ Base de datos de productos inicializada")
    
    @classmethod
    def registrar_cambio_precio(cls, producto_id: int, tipo_precio: str, 
                                precio_anterior: float, precio_nuevo: float, 
                                usuario: str = "Sistema"):
        """Registra un cambio de precio en el historial"""
        try:
            with cls.get_conexion() as conn:
                conn.execute("""
                    INSERT INTO historial_precios 
                    (producto_id, tipo_precio, precio_anterior, precio_nuevo, usuario)
                    VALUES (?, ?, ?, ?, ?)
                """, (producto_id, tipo_precio, precio_anterior, precio_nuevo, usuario))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error registrando cambio de precio: {e}")
            return False
    
    @classmethod
    def producto_existe(cls, codigo_barras: str) -> bool:
        """Verifica si existe un producto con el código de barras dado"""
        try:
            with cls.get_conexion() as conn:
                cur = conn.execute(
                    "SELECT id FROM productos WHERE codigo_barras = ?",
                    (codigo_barras,)
                )
                return cur.fetchone() is not None
        except Exception as e:
            print(f"Error verificando existencia de producto: {e}")
            return False
    
    @classmethod
    def obtener_productos_activos(cls, limite: int = 0):
        """Obtiene todos los productos activos"""
        try:
            with cls.get_conexion() as conn:
                if limite > 0:
                    cursor = conn.execute("""
                        SELECT * FROM productos 
                        WHERE activo = 1 AND stock_actual > 0
                        ORDER BY nombre
                        LIMIT ?
                    """, (limite,))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM productos 
                        WHERE activo = 1 AND stock_actual > 0
                        ORDER BY nombre
                    """)
                return cursor.fetchall()
        except Exception as e:
            print(f"Error obteniendo productos activos: {e}")
            return []
    
    @classmethod
    def actualizar_stock(cls, producto_id: int, cantidad: int):
        """Actualiza el stock de un producto"""
        try:
            with cls.get_conexion() as conn:
                conn.execute("""
                    UPDATE productos 
                    SET stock_actual = stock_actual - ?,
                        actualizado_en = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (cantidad, producto_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error actualizando stock: {e}")
            return False
    
    @classmethod
    def obtener_estadisticas(cls):
        """Obtiene estadísticas de productos"""
        try:
            with cls.get_conexion() as conn:
                total = conn.execute(
                    "SELECT COUNT(*) as count FROM productos WHERE activo = 1"
                ).fetchone()["count"]
                
                bajo_stock = conn.execute("""
                    SELECT COUNT(*) as count FROM productos 
                    WHERE stock_actual <= stock_minimo AND activo = 1
                """).fetchone()["count"]
                
                destacados = conn.execute("""
                    SELECT COUNT(*) as count FROM productos 
                    WHERE destacado = 1 AND activo = 1
                """).fetchone()["count"]
                
                hoy = datetime.now().strftime("%Y-%m-%d")
                nuevos_hoy = conn.execute("""
                    SELECT COUNT(*) as count FROM productos 
                    WHERE DATE(creado_en) = ? AND activo = 1
                """, (hoy,)).fetchone()["count"]
                
                return {
                    "total": total,
                    "bajo_stock": bajo_stock,
                    "destacados": destacados,
                    "nuevos_hoy": nuevos_hoy
                }
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {
                "total": 0,
                "bajo_stock": 0,
                "destacados": 0,
                "nuevos_hoy": 0
            }
