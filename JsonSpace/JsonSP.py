# JsonDB.py
import json
import os
import shutil
import threading
import time
from typing import Any, Dict, List, Optional, Union

class JsonDB:
    """
    Base de datos local 100% en JSON.
    
    Permite guardar, leer, actualizar y eliminar datos de forma persistente.
    Soporta rutas anidadas (ej: "usuario.perfil.nombre"), respaldos automáticos,
    y operaciones seguras en entornos con hilos.
    
    Ejemplo básico:
        >>> db = JsonDB("mi_app.json")
        >>> db["usuario"] = "Carlos"
        >>> db.guardar("config.tema", "oscuro")
        >>> print(db.obtener("usuario"))
        Carlos
    """

    def __init__(
        self,
        ruta_archivo: str = "datos.json",
        crear_si_no_existe: bool = True,
        respaldos: bool = True,
        max_respaldos: int = 5
    ):
        """
        Inicializa la base de datos JSON.
        
        :param ruta_archivo: Ruta del archivo JSON donde se guardarán los datos.
        :param crear_si_no_existe: Si es True, crea el archivo si no existe.
        :param respaldos: Si es True, crea copias de seguridad antes de sobrescribir.
        :param max_respaldos: Número máximo de respaldos a mantener.
        
        Ejemplo:
            >>> db = JsonDB("config.json", respaldos=True, max_respaldos=3)
        """
        self.ruta_archivo = os.path.abspath(ruta_archivo)
        self.respaldos = respaldos
        self.max_respaldos = max_respaldos
        self._lock = threading.RLock()
        
        if crear_si_no_existe:
            self._crear_si_no_existe()

    def _crear_si_no_existe(self):
        """Crea el archivo con un objeto vacío {} si no existe."""
        if not os.path.exists(self.ruta_archivo):
            os.makedirs(os.path.dirname(self.ruta_archivo), exist_ok=True)
            self._escribir_datos({})

    def _leer_datos(self) -> dict:
        """Lee y devuelve el contenido del archivo JSON."""
        with self._lock:
            if not os.path.exists(self.ruta_archivo):
                return {}
            try:
                with open(self.ruta_archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                raise ValueError(f"El archivo '{self.ruta_archivo}' no contiene JSON válido.")

    def _escribir_datos(self, datos: dict):
        """Escribe un diccionario en el archivo JSON."""
        with self._lock:
            if self.respaldos and os.path.exists(self.ruta_archivo):
                self._crear_respaldo()
            
            with open(self.ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)

    def _crear_respaldo(self):
        """Crea una copia de seguridad del archivo actual."""
        backup_dir = self.ruta_archivo + ".backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = int(time.time())
        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.json")
        shutil.copy2(self.ruta_archivo, backup_path)

        backups = sorted(
            [f for f in os.listdir(backup_dir) if f.endswith('.json')],
            key=lambda x: int(x.split('_')[1].split('.')[0])
        )
        for old in backups[:-self.max_respaldos]:
            os.remove(os.path.join(backup_dir, old))

    def _obtener_valor_anidado(self, datos: dict, clave: str, separador: str = ".") -> Any:
        """Obtiene un valor usando claves anidadas como 'a.b.c'."""
        claves = clave.split(separador)
        for k in claves:
            if isinstance(datos, dict) and k in datos:
                datos = datos[k]
            else:
                return None
        return datos

    def _establecer_valor_anidado(self, datos: dict, clave: str, valor: Any, separador: str = "."):
        """Establece un valor en una ruta anidada como 'a.b.c'."""
        claves = clave.split(separador)
        for k in claves[:-1]:
            if k not in datos or not isinstance(datos[k], dict):
                datos[k] = {}
            datos = datos[k]
        datos[claves[-1]] = valor

    # ==============================
    # 🔹 MÉTODOS PRINCIPALES
    # ==============================

    def obtener(self, clave: str, valor_por_defecto: Any = None, separador: str = ".") -> Any:
        """
        Obtiene el valor asociado a una clave. Soporta rutas anidadas.
        
        :param clave: Clave a buscar (ej: "usuario.nombre").
        :param valor_por_defecto: Valor a devolver si la clave no existe.
        :param separador: Carácter usado para separar niveles (por defecto ".").
        :return: Valor encontrado o valor_por_defecto.
        
        Ejemplos:
            >>> db = JsonDB()
            >>> db.guardar("usuario.nombre", "Ana")
            >>> db.obtener("usuario.nombre")
            'Ana'
            >>> db.obtener("usuario.edad", 0)
            0
        """
        datos = self._leer_datos()
        valor = self._obtener_valor_anidado(datos, clave, separador)
        return valor if valor is not None else valor_por_defecto

    def guardar(self, clave: str, valor: Any, separador: str = "."):
        """
        Guarda o sobrescribe un valor en una clave. Crea la estructura anidada si no existe.
        
        :param clave: Clave donde guardar (ej: "config.tema").
        :param valor: Valor a guardar.
        :param separador: Carácter separador (por defecto ".").
        
        Ejemplos:
            >>> db = JsonDB()
            >>> db.guardar("app.nombre", "MiApp")
            >>> db.guardar("app.version", "1.0")
            # Resultado: {"app": {"nombre": "MiApp", "version": "1.0"}}
        """
        datos = self._leer_datos()
        self._establecer_valor_anidado(datos, clave, valor, separador)
        self._escribir_datos(datos)

    def agregar(self, clave: str, valor: Any, separador: str = "."):
        """
        Agrega un valor a una clave. Si la clave no existe, se crea como lista.
        Si ya existe y es una lista, se añade el valor.
        Si ya existe y es un diccionario, y el valor es dict, se fusiona.
        Si ya existe y es otro tipo, se convierte en lista [valor_antiguo, nuevo_valor].
        
        Ideal para acumular entradas de usuario:
            >>> value = input("Nombre: ")
            >>> db.agregar("usuarios", value)  # Se acumula en una lista
        
        Ejemplos:
            >>> db = JsonDB()
            >>> db.agregar("nombres", "Ana")
            >>> db.agregar("nombres", "Luis")
            # Resultado: {"nombres": ["Ana", "Luis"]}
            
            >>> db.agregar("config", {"tema": "oscuro"})
            >>> db.agregar("config", {"idioma": "es"})
            # Resultado: {"config": {"tema": "oscuro", "idioma": "es"}}
        """
        datos = self._leer_datos()
        valor_actual = self._obtener_valor_anidado(datos, clave, separador)
        
        if valor_actual is None:
            # La clave no existe: 
            # - Si el valor es un dict, guardar como dict
            # - Si no, guardar como lista con un elemento
            if isinstance(valor, dict):
                self._establecer_valor_anidado(datos, clave, valor, separador)
            else:
                self._establecer_valor_anidado(datos, clave, [valor], separador)
        elif isinstance(valor_actual, list):
            # Ya es una lista: añadir
            valor_actual.append(valor)
            self._establecer_valor_anidado(datos, clave, valor_actual, separador)
        elif isinstance(valor_actual, dict) and isinstance(valor, dict):
            # Fusionar diccionarios
            valor_actual.update(valor)
            self._establecer_valor_anidado(datos, clave, valor_actual, separador)
        else:
            # Caso mixto: convertir a lista
            nueva_lista = [valor_actual, valor]
            self._establecer_valor_anidado(datos, clave, nueva_lista, separador)
        
        self._escribir_datos(datos)

    def actualizar(self, clave: str, actualizaciones: dict, separador: str = "."):
        """
        Actualiza un objeto (diccionario) existente en la clave dada.
        
        :param clave: Clave del objeto a actualizar.
        :param actualizaciones: Diccionario con los campos a actualizar.
        :param separador: Carácter separador.
        :raises KeyError: Si la clave no existe.
        :raises TypeError: Si el valor no es un diccionario.
        
        Ejemplo:
            >>> db = JsonDB()
            >>> db.guardar("usuario", {"nombre": "Ana", "edad": 25})
            >>> db.actualizar("usuario", {"edad": 26, "ciudad": "Madrid"})
            # Resultado: {"usuario": {"nombre": "Ana", "edad": 26, "ciudad": "Madrid"}}
        """
        datos = self._leer_datos()
        valor_actual = self._obtener_valor_anidado(datos, clave, separador)
        if valor_actual is None:
            raise KeyError(f"La clave '{clave}' no existe.")
        if not isinstance(valor_actual, dict):
            raise TypeError(f"El valor en '{clave}' no es un diccionario.")
        
        valor_actual.update(actualizaciones)
        self._establecer_valor_anidado(datos, clave, valor_actual, separador)
        self._escribir_datos(datos)

    def eliminar(self, clave: str, separador: str = "."):
        """
        Elimina una clave y su valor.
        
        :param clave: Clave a eliminar.
        :param separador: Carácter separador.
        :raises KeyError: Si la clave no existe.
        
        Ejemplo:
            >>> db = JsonDB()
            >>> db["temp"] = "borrable"
            >>> db.eliminar("temp")
        """
        def _eliminar_recursivo(d, claves):
            if len(claves) == 1:
                if claves[0] in d:
                    del d[claves[0]]
                    return True
                return False
            if claves[0] in d and isinstance(d[claves[0]], dict):
                return _eliminar_recursivo(d[claves[0]], claves[1:])
            return False

        datos = self._leer_datos()
        claves = clave.split(separador)
        if _eliminar_recursivo(datos, claves):
            self._escribir_datos(datos)
        else:
            raise KeyError(f"La clave '{clave}' no existe.")

    def existe(self, clave: str, separador: str = ".") -> bool:
        """
        Verifica si una clave existe.
        
        Ejemplo:
            >>> db = JsonDB()
            >>> db["nombre"] = "Test"
            >>> db.existe("nombre")
            True
        """
        return self.obtener(clave, separador=separador) is not None

    def todas_las_claves(self, datos: dict = None, prefijo: str = "") -> List[str]:
        """
        Devuelve todas las claves en formato plano (con puntos).
        
        Ejemplo:
            >>> db = JsonDB()
            >>> db.guardar("a.b", 1)
            >>> db.guardar("a.c.d", 2)
            >>> db.todas_las_claves()
            ['a.b', 'a.c.d']
        """
        if datos is None:
            datos = self._leer_datos()
        claves = []
        for k, v in datos.items():
            clave_actual = f"{prefijo}.{k}" if prefijo else k
            if isinstance(v, dict):
                claves.extend(self.todas_las_claves(v, clave_actual))
            else:
                claves.append(clave_actual)
        return claves

    def todo(self) -> dict:
        """Devuelve todo el contenido como diccionario."""
        return self._leer_datos()

    def vaciar(self):
        """Elimina todos los datos (deja un objeto vacío {})."""
        self._escribir_datos({})

    # ==============================
    # 🔹 SOPORTE PARA DICCIONARIO
    # ==============================

    def __getitem__(self, clave: str):
        return self.obtener(clave)

    def __setitem__(self, clave: str, valor: Any):
        self.guardar(clave, valor)

    def __delitem__(self, clave: str):
        self.eliminar(clave)

    def __contains__(self, clave: str):
        return self.existe(clave)

    def __repr__(self):
        return f"<JsonDB ruta='{self.ruta_archivo}'>"