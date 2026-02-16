"""
UsuariosBuilder - Esquemas y operaciones SQL para usuarios
Contiene todas las definiciones de tablas y operaciones de la base de datos de usuarios
"""

import sqlite3
import json
from pathlib import Path


class UsuariosBuilder:
    """Constructor de base de datos de usuarios (integrado con ventas.db)"""
    
    DB_PATH = Path("./BASEDATOS/ventas.db")
    JSON_FILE = Path("Json files/users.json")
    
    # ==================== MÉTODOS ====================
    
    @classmethod
    def get_conexion(cls) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos"""
        cls.DB_PATH.parent.mkdir(exist_ok=True)
        return sqlite3.connect(str(cls.DB_PATH), check_same_thread=False)
    
    @classmethod
    def _leer_usuarios_json(cls) -> list:
        """Devuelve lista de dicts con 'nombre' + propiedades del JSON"""
        if not cls.JSON_FILE.exists():
            return []
        with cls.JSON_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        usuarios_raw = data.get("usuarios", {})
        lista = []
        for nombre, props in usuarios_raw.items():
            fila = {"nombre": nombre, **props}
            lista.append(fila)
        return lista
    
    @classmethod
    def _columnas_dinamicas(cls, dict_list: list) -> list:
        """Obtiene todas las keys únicas del JSON para crear columnas"""
        if not dict_list:
            return []
        keys = set()
        for d in dict_list:
            keys.update(d.keys())
        # Orden alfabético para consistencia
        return sorted(keys)
    
    @classmethod
    def _columna_existe(cls, cur, tabla: str, columna: str) -> bool:
        """Verifica si una columna existe en una tabla"""
        cur.execute(f"PRAGMA table_info({tabla})")
        return any(row[1] == columna for row in cur.fetchall())
    
    @classmethod
    def inicializar_bd(cls):
        """Inicializa la tabla de usuarios con columnas dinámicas desde JSON"""
        usuarios = cls._leer_usuarios_json()
        columnas = cls._columnas_dinamicas(usuarios)
        
        if not columnas:
            print("⚠️ No hay usuarios en el JSON")
            return
        
        con = cls.get_conexion()
        cur = con.cursor()
        
        # Crear tabla usuarios con columnas dinámicas
        cols_def = ", ".join([f"{col} TEXT" for col in columnas])
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS usuarios(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                {cols_def}
            )
        """)
        
        # Crear tabla auditoria (si no existe)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS auditoria(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT NOT NULL,
                usuario TEXT NOT NULL,
                tipo TEXT NOT NULL,
                descripcion TEXT,
                detalles TEXT
            )
        """)
        
        # Insertar o ignorar usuarios del JSON
        col_id = "nombre" if "nombre" in columnas else columnas[0]
        placeholders = ", ".join(["?"] * len(columnas))
        sql_insert = f"INSERT OR IGNORE INTO usuarios({','.join(columnas)}) VALUES({placeholders})"
        
        for u in usuarios:
            values = [u.get(col, "") for col in columnas]
            cur.execute(sql_insert, values)
        
        con.commit()
        con.close()
        print("✓ Base de datos de usuarios inicializada")
        print("✓ Tabla de auditoría creada")
    
    @classmethod
    def obtener_usuario(cls, nombre: str):
        """Obtiene un usuario específico de la base de datos"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            cur.execute("SELECT * FROM usuarios WHERE nombre = ?", (nombre,))
            usuario = cur.fetchone()
            con.close()
            return usuario
        except Exception as e:
            print(f"Error obteniendo usuario: {e}")
            return None
    
    @classmethod
    def obtener_todos_usuarios(cls):
        """Obtiene todos los usuarios de la base de datos"""
        try:
            con = cls.get_conexion()
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM usuarios ORDER BY nombre")
            usuarios = cur.fetchall()
            con.close()
            return usuarios
        except Exception as e:
            print(f"Error obteniendo usuarios: {e}")
            return []
    
    @classmethod
    def actualizar_usuario(cls, nombre_original: str, datos: dict):
        """Actualiza los datos de un usuario"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            
            # Construir query dinámico
            campos = []
            valores = []
            for key, value in datos.items():
                if key != "id":  # No actualizar el ID
                    campos.append(f"{key} = ?")
                    valores.append(value)
            
            valores.append(nombre_original)
            sql = f"UPDATE usuarios SET {', '.join(campos)} WHERE nombre = ?"
            
            cur.execute(sql, valores)
            con.commit()
            con.close()
            return True
        except Exception as e:
            print(f"Error actualizando usuario: {e}")
            return False
    
    @classmethod
    def crear_usuario(cls, datos: dict):
        """Crea un nuevo usuario en la base de datos"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            
            # Construir query dinámico
            columnas = list(datos.keys())
            valores = list(datos.values())
            placeholders = ", ".join(["?"] * len(columnas))
            
            sql = f"INSERT INTO usuarios ({', '.join(columnas)}) VALUES ({placeholders})"
            cur.execute(sql, valores)
            
            con.commit()
            con.close()
            return True
        except Exception as e:
            print(f"Error creando usuario: {e}")
            return False
    
    @classmethod
    def eliminar_usuario(cls, nombre: str):
        """Elimina un usuario de la base de datos"""
        try:
            con = cls.get_conexion()
            cur = con.cursor()
            cur.execute("DELETE FROM usuarios WHERE nombre = ?", (nombre,))
            con.commit()
            con.close()
            return True
        except Exception as e:
            print(f"Error eliminando usuario: {e}")
            return False
    
    @classmethod
    def verificar_credenciales(cls, nombre: str, password: str) -> bool:
        """Verifica las credenciales de un usuario"""
        try:
            con = cls.get_conexion()
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM usuarios WHERE nombre = ? AND password = ?",
                (nombre, password)
            )
            usuario = cur.fetchone()
            con.close()
            return usuario is not None
        except Exception as e:
            print(f"Error verificando credenciales: {e}")
            return False
