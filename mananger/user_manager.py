# user_manager.py
from JsonSpace.JsonSP import JsonDB   # <- your JsonDB wrapper
from typing import List, Dict, Any
import os

# ---------- file paths ----------
ADMIN_FILE = "./Json files/admin.json"
USERS_FILE = "./Json files/users.json"

# ---------- DB instances ----------
ADMIN_DB = JsonDB(ADMIN_FILE)
USERS_DB = JsonDB(USERS_FILE)

# ---------- helpers ----------
def _key(username: str) -> str:
    """Nested key inside 'usuarios' container."""
    return f"usuarios.{username}"

def _ensure_default_admin():
    """
    Creates admin/admin the very first time the app starts.
    Idempotent: does nothing if the account already exists.
    """
    if not ADMIN_DB.existe(_key("admin")):
        ADMIN_DB.guardar(_key("admin"), {
            "password": "admin",
            "rol": "Admin",
            "estado": "Activo",
            "tipo": "admin"
        })

os.makedirs(os.path.dirname(ADMIN_FILE) or ".", exist_ok=True)
os.makedirs(os.path.dirname(USERS_FILE) or ".", exist_ok=True)

# 2. create default admin if missing
_ensure_default_admin()

# ---------- CRUD API ----------
def crear_usuario(username: str,
                  password: str,
                  rol: str = "Empleado",
                  estado: str = "Activo",
                  tipo: str = "empleado") -> None:
    """Save user in the correct JSON file."""
    if tipo == "admin":
        ADMIN_DB.guardar(_key(username), {
            "password": password,
            "rol": rol,
            "estado": estado,
            "tipo": tipo
        })
    else:
        USERS_DB.guardar(_key(username), {
            "password": password,
            "rol": rol,
            "estado": estado,
            "tipo": tipo
        })

def listar_todos() -> List[Dict[str, Any]]:
    """Flat list with every user (admins + employees)."""
    usuarios = []
    
    # Obtener usuarios de admin.json
    admins = ADMIN_DB.obtener("usuarios") or {}
    for username, data in admins.items():
        usuarios.append({
            "usuario": username,
            "password": data.get("password", ""),
            "rol": data.get("rol", ""),
            "estado": data.get("estado", ""),
            "tipo": data.get("tipo", "admin")
        })
    
    # Obtener usuarios de users.json
    empls = USERS_DB.obtener("usuarios") or {}
    for username, data in empls.items():
        usuarios.append({
            "usuario": username,
            "password": data.get("password", ""),
            "rol": data.get("rol", ""),
            "estado": data.get("estado", ""),
            "tipo": data.get("tipo", "empleado")
        })
    
    return usuarios

def usuario_existe(username: str) -> bool:
    return ADMIN_DB.existe(_key(username)) or USERS_DB.existe(_key(username))

def actualizar_usuario(username: str, cambios: dict):
    """Actualiza cualquier campo de un usuario existente."""
    if ADMIN_DB.existe(_key(username)):
        ADMIN_DB.actualizar(_key(username), cambios)
    elif USERS_DB.existe(_key(username)):
        USERS_DB.actualizar(_key(username), cambios)
    else:
        raise KeyError("Usuario no encontrado")

def eliminar_usuario(username: str):
    """Borra el usuario del archivo que corresponda."""
    if ADMIN_DB.existe(_key(username)):
        ADMIN_DB.eliminar(_key(username))
    elif USERS_DB.existe(_key(username)):
        USERS_DB.eliminar(_key(username))
    else:
        raise KeyError("Usuario no encontrado")