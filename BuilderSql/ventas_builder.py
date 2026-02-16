"""
VentasBuilder - Esquemas y operaciones SQL para ventas
Contiene todas las definiciones de tablas y operaciones de la base de datos de ventas
"""

import sqlite3
import datetime
from pathlib import Path


class VentasBuilder:
    """Constructor de base de datos de ventas"""
    
    DB_PATH = Path("./BASEDATOS/ventas.db")
    
    # ==================== ESQUEMAS SQL ====================
    
    SCHEMA_VENTAS = """
        CREATE TABLE IF NOT EXISTS ventas(
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            fecha   DATE,
            fecha_hora TEXT,
            total   REAL,
            tipo_venta TEXT DEFAULT 'Normal'
        )
    """
    
    SCHEMA_VENTAS_DETALLE = """
        CREATE TABLE IF NOT EXISTS ventas_detalle(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id    INTEGER,
            producto    TEXT,
            cantidad    INTEGER,
            precio_unit REAL,
            FOREIGN KEY(venta_id) REFERENCES ventas(id)
        )
    """
    
    SCHEMA_AUDITORIA = """
        CREATE TABLE IF NOT EXISTS auditoria(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_hora TEXT NOT NULL,
            usuario TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            detalles TEXT
        )
    """
    
    # ==================== MÉTODOS ====================
    
    @classmethod
    def get_conexion(cls) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos de ventas"""
        cls.DB_PATH.parent.mkdir(exist_ok=True)
        return sqlite3.connect(str(cls.DB_PATH), check_same_thread=False)
    
    @classmethod
    def inicializar_bd(cls):
        """Inicializa la base de datos con todas las tablas necesarias"""
        con = cls.get_conexion()
        cur = con.cursor()
        
        # Crear tablas
        cur.execute(cls.SCHEMA_VENTAS)
        cur.execute(cls.SCHEMA_VENTAS_DETALLE)
        cur.execute(cls.SCHEMA_AUDITORIA)
        
        # Verificar y agregar columna fecha_hora si no existe
        if not cls._columna_existe(cur, "ventas", "fecha_hora"):
            cur.execute("ALTER TABLE ventas ADD COLUMN fecha_hora TEXT")
        
        # Verificar y agregar columna tipo_venta si no existe
        if not cls._columna_existe(cur, "ventas", "tipo_venta"):
            cur.execute("ALTER TABLE ventas ADD COLUMN tipo_venta TEXT DEFAULT 'Normal'")
        
        con.commit()
        con.close()
        print("✓ Base de datos de ventas inicializada")
    
    @classmethod
    def _columna_existe(cls, cur, tabla: str, columna: str) -> bool:
        """Verifica si una columna existe en una tabla"""
        cur.execute(f"PRAGMA table_info({tabla})")
        return any(row[1] == columna for row in cur.fetchall())
    
    @classmethod
    def guardar_venta(cls, usuario: str, carrito: list[dict], tipo_venta: str = "Normal") -> bool:
        """Guarda una venta con sus detalles"""
        if not carrito:
            print("ERROR: Carrito vacío, no se puede guardar")
            return False
        
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            hoy = datetime.date.today()
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Calcular total
            total = 0.0
            for item in carrito:
                try:
                    precio = float(item["producto"]["precio"])
                    cantidad = int(item["cantidad"])
                    total += precio * cantidad
                except (KeyError, ValueError, TypeError) as e:
                    print(f"ERROR: Error calculando total para item: {e}")
                    con.close()
                    return False
            
            # Insertar venta principal
            cur.execute(
                "INSERT INTO ventas(usuario, fecha, fecha_hora, total, tipo_venta) VALUES(?,?,?,?,?)",
                (usuario, hoy, ahora, total, tipo_venta)
            )
            venta_id = cur.lastrowid
            print(f"DEBUG: Venta guardada con tipo_venta='{tipo_venta}'")
            
            # Insertar detalles de la venta
            for item in carrito:
                try:
                    p = item["producto"]
                    nombre_producto = p.get("nombre", "Producto sin nombre")
                    cantidad = int(item["cantidad"])
                    precio_unit = float(p.get("precio", 0))
                    
                    cur.execute(
                        "INSERT INTO ventas_detalle(venta_id, producto, cantidad, precio_unit) VALUES(?,?,?,?)",
                        (venta_id, nombre_producto, cantidad, precio_unit)
                    )
                except (KeyError, ValueError, TypeError) as e:
                    print(f"ERROR: Error insertando detalle de venta: {e}")
                    con.rollback()
                    con.close()
                    return False
            
            con.commit()
            con.close()
            print(f"✓ Venta guardada: ID {venta_id}, Total ${total:.2f}")
            return True
            
        except Exception as e:
            print(f"ERROR en guardar_venta: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def ventas_del_dia(cls, usuario: str) -> float:
        """Retorna el total de ventas del día para un usuario"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            hoy = datetime.date.today()
            cur.execute(
                "SELECT SUM(total) FROM ventas WHERE usuario=? AND fecha=?",
                (usuario, hoy)
            )
            total = cur.fetchone()[0] or 0.0
            con.close()
            return total
        except Exception as e:
            print(f"Error en ventas_del_dia: {e}")
            return 0.0
    
    @classmethod
    def ultimas_ventas(cls, usuario: str, limite: int = 10) -> list:
        """Retorna las últimas ventas de un usuario con formato (hora, producto, monto)"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            hoy = datetime.date.today()
            
            if limite == 0:  # Si es 0, obtener todas las ventas del día
                cur.execute("""
                    SELECT COALESCE(v.fecha_hora, v.fecha || ' 00:00:00') as fecha_hora,
                           GROUP_CONCAT(vd.producto, ', ') as productos,
                           v.total
                    FROM ventas v
                    LEFT JOIN ventas_detalle vd ON v.id = vd.venta_id
                    WHERE v.usuario = ? AND v.fecha = ?
                    GROUP BY v.id
                    ORDER BY v.id DESC
                """, (usuario, hoy))
            else:
                cur.execute("""
                    SELECT COALESCE(v.fecha_hora, v.fecha || ' 00:00:00') as fecha_hora,
                           GROUP_CONCAT(vd.producto, ', ') as productos,
                           v.total
                    FROM ventas v
                    LEFT JOIN ventas_detalle vd ON v.id = vd.venta_id
                    WHERE v.usuario = ?
                    GROUP BY v.id
                    ORDER BY v.id DESC
                    LIMIT ?
                """, (usuario, limite))
            
            rows = cur.fetchall()
            con.close()
            
            # Formatear los resultados
            resultados = []
            for row in rows:
                fecha_hora, productos, total = row
                
                # Extraer solo la hora (HH:MM)
                if fecha_hora:
                    try:
                        if ' ' in fecha_hora:
                            fecha_part, hora_part = fecha_hora.split(' ')
                            hora = hora_part[:5]  # Tomar solo HH:MM
                        else:
                            hora = "00:00"
                    except:
                        hora = "00:00"
                else:
                    hora = "00:00"
                
                # Limitar la lista de productos si es muy larga
                if productos and len(productos) > 30:
                    productos = productos[:27] + "..."
                elif not productos:
                    productos = "Varios productos"
                    
                resultados.append((hora, productos, total))
            
            return resultados
            
        except Exception as e:
            print(f"Error en ultimas_ventas: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @classmethod
    def registrar_auditoria(cls, usuario: str, tipo: str, descripcion: str, detalles: str = ""):
        """Registra una acción en la auditoría"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cur.execute(
                "INSERT INTO auditoria(fecha_hora, usuario, tipo, descripcion, detalles) VALUES(?,?,?,?,?)",
                (ahora, usuario, tipo, descripcion, detalles)
            )
            con.commit()
            con.close()
            return True
        except Exception as e:
            # Silenciar errores de auditoría para no afectar la operación principal
            # print(f"⚠️ Error registrando auditoría: {e}")
            return False
    
    @classmethod
    def obtener_auditoria(cls, limite: int = 100, usuario: str = None):
        """Obtiene registros de auditoría"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            
            if usuario:
                cur.execute("""
                    SELECT * FROM auditoria 
                    WHERE usuario = ?
                    ORDER BY id DESC 
                    LIMIT ?
                """, (usuario, limite))
            else:
                cur.execute("""
                    SELECT * FROM auditoria 
                    ORDER BY id DESC 
                    LIMIT ?
                """, (limite,))
            
            rows = cur.fetchall()
            con.close()
            return rows
        except Exception as e:
            print(f"Error obteniendo auditoría: {e}")
            return []
