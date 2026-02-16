"""
ContratosBuilder - Esquemas y operaciones SQL para contratos de empleados
Contiene todas las definiciones de tablas y operaciones de la base de datos de contratos
"""

import sqlite3
from datetime import datetime
from pathlib import Path


class ContratosBuilder:
    """Constructor de base de datos de contratos de empleados"""
    
    DB_PATH = Path("./BASEDATOS/contratos.db")
    
    # ==================== MÉTODOS ====================
    
    @classmethod
    def get_conexion(cls) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos"""
        cls.DB_PATH.parent.mkdir(exist_ok=True)
        return sqlite3.connect(str(cls.DB_PATH), check_same_thread=False)
    
    @classmethod
    def inicializar_bd(cls):
        """Crea la tabla de contratos si no existe"""
        with cls.get_conexion() as conn:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contratos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_empleado TEXT NOT NULL,
                    puesto TEXT NOT NULL,
                    fecha_inicio TEXT NOT NULL,
                    salario REAL NOT NULL,
                    frecuencia_pago TEXT NOT NULL,
                    tipo_contrato TEXT NOT NULL,
                    estado TEXT NOT NULL DEFAULT 'Activo',
                    fecha_fin TEXT,
                    notas TEXT,
                    fecha_creacion TEXT NOT NULL,
                    fecha_modificacion TEXT
                )
            """)
            conn.commit()
            print("✅ Tabla 'contratos' inicializada")
    
    @classmethod
    def crear_contrato(cls, datos: dict) -> bool:
        """
        Crea un nuevo contrato de empleado
        Args:
            datos: dict con keys: nombre_empleado, puesto, fecha_inicio, salario,
                   frecuencia_pago, tipo_contrato, estado, fecha_fin, notas
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                fecha_actual = datetime.now().isoformat()
                
                cur.execute("""
                    INSERT INTO contratos (
                        nombre_empleado, puesto, fecha_inicio, salario,
                        frecuencia_pago, tipo_contrato, estado, fecha_fin,
                        notas, fecha_creacion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datos['nombre_empleado'],
                    datos['puesto'],
                    datos['fecha_inicio'],
                    datos['salario'],
                    datos['frecuencia_pago'],
                    datos['tipo_contrato'],
                    datos.get('estado', 'Activo'),
                    datos.get('fecha_fin'),
                    datos.get('notas', ''),
                    fecha_actual
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error al crear contrato: {e}")
            return False
    
    @classmethod
    def listar_contratos(cls, filtro_estado: str = None) -> list:
        """
        Lista todos los contratos o filtra por estado
        Args:
            filtro_estado: 'Activo', 'Finalizado', None para todos
        Returns:
            list: lista de dicts con los datos de los contratos
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                
                if filtro_estado:
                    cur.execute("""
                        SELECT id, nombre_empleado, puesto, fecha_inicio, salario,
                               frecuencia_pago, tipo_contrato, estado, fecha_fin,
                               notas, fecha_creacion, fecha_modificacion
                        FROM contratos
                        WHERE estado = ?
                        ORDER BY fecha_inicio DESC
                    """, (filtro_estado,))
                else:
                    cur.execute("""
                        SELECT id, nombre_empleado, puesto, fecha_inicio, salario,
                               frecuencia_pago, tipo_contrato, estado, fecha_fin,
                               notas, fecha_creacion, fecha_modificacion
                        FROM contratos
                        ORDER BY fecha_inicio DESC
                    """)
                
                columnas = [desc[0] for desc in cur.description]
                resultados = []
                for fila in cur.fetchall():
                    resultados.append(dict(zip(columnas, fila)))
                return resultados
        except Exception as e:
            print(f"❌ Error al listar contratos: {e}")
            return []
    
    @classmethod
    def obtener_contrato(cls, contrato_id: int) -> dict:
        """
        Obtiene un contrato por su ID
        Args:
            contrato_id: ID del contrato
        Returns:
            dict: datos del contrato o None
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id, nombre_empleado, puesto, fecha_inicio, salario,
                           frecuencia_pago, tipo_contrato, estado, fecha_fin,
                           notas, fecha_creacion, fecha_modificacion
                    FROM contratos
                    WHERE id = ?
                """, (contrato_id,))
                
                fila = cur.fetchone()
                if fila:
                    columnas = [desc[0] for desc in cur.description]
                    return dict(zip(columnas, fila))
                return None
        except Exception as e:
            print(f"❌ Error al obtener contrato: {e}")
            return None
    
    @classmethod
    def actualizar_contrato(cls, contrato_id: int, datos: dict) -> bool:
        """
        Actualiza un contrato existente
        Args:
            contrato_id: ID del contrato a actualizar
            datos: dict con los campos a actualizar
        Returns:
            bool: True si se actualizó exitosamente
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                fecha_actual = datetime.now().isoformat()
                
                cur.execute("""
                    UPDATE contratos SET
                        nombre_empleado = ?,
                        puesto = ?,
                        fecha_inicio = ?,
                        salario = ?,
                        frecuencia_pago = ?,
                        tipo_contrato = ?,
                        estado = ?,
                        fecha_fin = ?,
                        notas = ?,
                        fecha_modificacion = ?
                    WHERE id = ?
                """, (
                    datos['nombre_empleado'],
                    datos['puesto'],
                    datos['fecha_inicio'],
                    datos['salario'],
                    datos['frecuencia_pago'],
                    datos['tipo_contrato'],
                    datos['estado'],
                    datos.get('fecha_fin'),
                    datos.get('notas', ''),
                    fecha_actual,
                    contrato_id
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error al actualizar contrato: {e}")
            return False
    
    @classmethod
    def eliminar_contrato(cls, contrato_id: int) -> bool:
        """
        Elimina un contrato
        Args:
            contrato_id: ID del contrato a eliminar
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM contratos WHERE id = ?", (contrato_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error al eliminar contrato: {e}")
            return False
    
    @classmethod
    def buscar_contratos(cls, termino: str) -> list:
        """
        Busca contratos por nombre de empleado o puesto
        Args:
            termino: término de búsqueda
        Returns:
            list: lista de contratos que coinciden
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                termino_busqueda = f"%{termino}%"
                cur.execute("""
                    SELECT id, nombre_empleado, puesto, fecha_inicio, salario,
                           frecuencia_pago, tipo_contrato, estado, fecha_fin,
                           notas, fecha_creacion, fecha_modificacion
                    FROM contratos
                    WHERE nombre_empleado LIKE ? OR puesto LIKE ?
                    ORDER BY fecha_inicio DESC
                """, (termino_busqueda, termino_busqueda))
                
                columnas = [desc[0] for desc in cur.description]
                resultados = []
                for fila in cur.fetchall():
                    resultados.append(dict(zip(columnas, fila)))
                return resultados
        except Exception as e:
            print(f"❌ Error al buscar contratos: {e}")
            return []
    
    @classmethod
    def cambiar_estado_contrato(cls, contrato_id: int, nuevo_estado: str) -> bool:
        """
        Cambia el estado de un contrato
        Args:
            contrato_id: ID del contrato
            nuevo_estado: 'Activo' o 'Finalizado'
        Returns:
            bool: True si se cambió exitosamente
        """
        try:
            with cls.get_conexion() as conn:
                cur = conn.cursor()
                fecha_actual = datetime.now().isoformat()
                
                # Si se finaliza el contrato, agregar fecha de fin
                if nuevo_estado == 'Finalizado':
                    cur.execute("""
                        UPDATE contratos SET
                            estado = ?,
                            fecha_fin = ?,
                            fecha_modificacion = ?
                        WHERE id = ?
                    """, (nuevo_estado, fecha_actual, fecha_actual, contrato_id))
                else:
                    cur.execute("""
                        UPDATE contratos SET
                            estado = ?,
                            fecha_modificacion = ?
                        WHERE id = ?
                    """, (nuevo_estado, fecha_actual, contrato_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Error al cambiar estado: {e}")
            return False
