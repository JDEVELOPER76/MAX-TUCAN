"""oculta el error al salir de una pantalla construida en flet 
solo la oculta no la repara pero igual no es nada grabe"""

import sys

def flet_console_error():
    """Parche para ocultar un error 
    al cerrar una pestana de flet """
    def _hook(unraisable):
        msg = str(unraisable.exc_value)
        if "Event loop is closed" in msg or "StreamWriter.__del__" in msg:
            return  # Ignora este error silenciosamente
        sys.__stderr__.write(f"Ignored unraisable exception: {msg}\n")

    sys.unraisablehook = _hook



