import sqlite3, json, datetime
from pathlib import Path

DB_FOLDER = Path("BASEDATOS")
DB_FILE   = DB_FOLDER / "ventas.db"
JSON_FILE = Path("Json files/users.json")

DB_FOLDER.mkdir(exist_ok=True)

def get_conexion():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def _leer_usuarios_json():
    """Devuelve lista de dicts con 'nombre' + propiedades del JSON"""
    if not JSON_FILE.exists():
        return []
    with JSON_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    usuarios_raw = data.get("usuarios", {})
    lista = []
    for nombre, props in usuarios_raw.items():
        fila = {"nombre": nombre, **props}
        lista.append(fila)
    return lista

def _columnas_dinamicas(dict_list):
    """Obtiene todas las keys únicas del JSON para crear columnas"""
    if not dict_list:
        return []
    keys = set()
    for d in dict_list:
        keys.update(d.keys())
    # Orden alfabético para consistencia
    return sorted(keys)

def inicializar_bd():
    usuarios = _leer_usuarios_json()
    columnas = _columnas_dinamicas(usuarios)
    if not columnas:
        raise RuntimeError("No hay usuarios en el JSON")

    con = get_conexion()
    cur = con.cursor()

    # ------ Tabla usuarios (columnas dinámicas) ------
    cols_def = ", ".join([f"{col} TEXT" for col in columnas])
    cur.execute(f"CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY AUTOINCREMENT, {cols_def})")

    # Inserta o ignora según UNIQUE (usamos la columna 'nombre' como clave)
    # Si no existe 'nombre' usamos la primera columna
    col_id = "nombre" if "nombre" in columnas else columnas[0]
    placeholders = ", ".join(["?"] * len(columnas))
    sql_insert = f"INSERT OR IGNORE INTO usuarios({','.join(columnas)}) VALUES({placeholders})"
    for u in usuarios:
        values = [u.get(col, "") for col in columnas]
        cur.execute(sql_insert, values)

    # ------ Tablas de ventas (fijas) ------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ventas(
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            fecha   DATE,
            total   REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ventas_detalle(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id    INTEGER,
            producto    TEXT,
            cantidad    INTEGER,
            precio_unit REAL,
            FOREIGN KEY(venta_id) REFERENCES ventas(id)
        )
    """)
    con.commit()
    con.close()

# ---------- ventas ----------
def ventas_del_dia(usuario: str):
    """Retorna el total de ventas del día para un usuario"""
    try:
        con = get_conexion()
        cur = con.cursor()
        hoy = datetime.date.today()
        cur.execute("SELECT SUM(total) FROM ventas WHERE usuario=? AND fecha=?", (usuario, hoy))
        total = cur.fetchone()[0] or 0.0
        con.close()
        return total
    except Exception as e:
        print(f"Error en ventas_del_dia: {e}")
        return 0.0

def ultimas_ventas(usuario: str, limite=10):
    """Retorna las últimas ventas de un usuario con formato (hora, producto, monto)"""
    try:
        con = get_conexion()
        cur = con.cursor()
        
        if limite == 0:  # Si es 0, obtener todas las ventas del día
            cur.execute("""
                SELECT v.fecha || ' ' || time(v.id, 'unixepoch') as hora_completa,
                       GROUP_CONCAT(vd.producto, ', ') as productos,
                       v.total
                FROM ventas v
                LEFT JOIN ventas_detalle vd ON v.id = vd.venta_id
                WHERE v.usuario = ? AND v.fecha = date('now')
                GROUP BY v.id
                ORDER BY v.id DESC
            """, (usuario,))
        else:
            cur.execute("""
                SELECT v.fecha || ' ' || time(v.id, 'unixepoch') as hora_completa,
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
        
        # Formatear los resultados para que coincidan con lo que espera sala_empleados.py
        resultados = []
        for row in rows:
            hora_completa, productos, total = row
            
            # Extraer solo la hora (HH:MM)
            if hora_completa:
                try:
                    # Si la fecha incluye tiempo, extraer la parte de la hora
                    if ' ' in hora_completa:
                        fecha_part, hora_part = hora_completa.split(' ')
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

def guardar_venta(usuario: str, carrito: list[dict]):
    
    # Validar que el carrito no esté vacío
    if not carrito:
        print("ERROR db.py: Carrito vacío, no se puede guardar")
        return False
    
    try:
        con = get_conexion()
        cur = con.cursor()
        hoy = datetime.date.today()
        
        # Calcular total
        total = 0.0
        for item in carrito:
            try:
                precio = float(item["producto"]["precio"])
                cantidad = int(item["cantidad"])
                total += precio * cantidad
            except (KeyError, ValueError, TypeError) as e:
                print(f"ERROR db.py: Error calculando total para item: {e}")
                con.close()
                return False
        
        
        # Insertar venta principal
        cur.execute(
            "INSERT INTO ventas(usuario, fecha, total) VALUES(?,?,?)", 
            (usuario, hoy, total)
        )
        venta_id = cur.lastrowid

        
        # Insertar detalles de la venta
        items_insertados = 0
        for item in carrito:
            try:
                p = item["producto"]
                nombre_producto = p.get("nombre", "Producto sin nombre")
                cantidad = int(item["cantidad"])
                precio_unit = float(p["precio"])
                
                cur.execute(
                    "INSERT INTO ventas_detalle(venta_id, producto, cantidad, precio_unit) VALUES(?,?,?,?)",
                    (venta_id, nombre_producto, cantidad, precio_unit)
                )
                items_insertados += 1
                
                
            except (KeyError, ValueError, TypeError) as e:
                # Continuar con los demás items
                continue
        
        # Verificar que se insertaron todos los items
        if items_insertados != len(carrito):
            pass
        
        # Commit de la transacción
        con.commit()
        con.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"ERROR db.py: Error de SQLite al guardar venta: {e}")
        import traceback
        traceback.print_exc()
        try:
            con.close()
        except:
            pass
        return False
        
    except Exception as e:
        print(f"ERROR db.py: Error general al guardar venta: {e}")
        import traceback
        traceback.print_exc()
        try:
            con.close()
        except:
            pass
        return False

def obtener_detalle_venta(venta_id: int):
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
        return []

def total_ventas_periodo(usuario: str = None, fecha_inicio: str = None, fecha_fin: str = None):
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
        return 0.0