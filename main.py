"""Archiv principal de la app
import flet_console
sirve para un error asyncio de flet 
"""

from login import main
import flet as ft
import flet_console


if __name__ == "__main__":
    ft.app(
        target=main,assets_dir="assets")


flet_console.flet_console_error()
