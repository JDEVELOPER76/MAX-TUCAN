# login.py — versión final sin contenedor blanco y pantalla completa
import flet as ft
from mananger.user_manager import ADMIN_DB, USERS_DB
from admin_panels.admin_panel import AdminPanel
import time
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # ruta temporalmientras corre el .exe
    except AttributeError:
        base_path = os.path.abspath(".")  # modo script normal
    return os.path.join(base_path, relative_path)


class LoginApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self._setup_page()
        self.setup_ui()

    # ---------- CONFIG PÁGINA ----------
    def _setup_page(self):
        self.page.title = "TUCAN MAX"
        self.page.window.icon = resource_path("assets/tucan.ico") 
        self.page.window.maximized = True
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.WHITE
        self.page.padding = 0
        self.page.spacing = 0
        self.page.auto_scroll = False
        self.page.scroll = None
        self.page.window.bgcolor = ft.Colors.WHITE

        # 🔹 Modo pantalla completa (funciona en app de escritorio)
        self.page.window.maximized = True

        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # ---------- ELEMENTOS ----------
        self.progress_ring = ft.ProgressRing(width=25, height=25, stroke_width=3, visible=False)

        self.entrada_user = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.BLUE_400,
            text_size=16,
            width=300
        )

        self.entrada_contraseña = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border=ft.InputBorder.UNDERLINE,
            border_color=ft.Colors.BLUE_400,
            text_size=16,
            width=300
        )

        self.mensaje_login = ft.Text("", size=14, text_align=ft.TextAlign.CENTER)

        self.boton_login = ft.ElevatedButton(
            content=ft.Row([
                self.progress_ring,
                ft.Text("Ingresar al Sistema", size=16, weight=ft.FontWeight.W_500),
            ], alignment=ft.MainAxisAlignment.CENTER),
            on_click=self.validar_login,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                padding=20,
            ),
            width=250,
        )

    # ---------- UI ----------
    def setup_ui(self):
        logo_section = ft.Column([
            ft.Image(
                src=resource_path("assets/tucan.jpg"),
                width=350,
                height=350,
                fit=ft.ImageFit.COVER,
                border_radius=10,
            ),
            ft.Container(height=30),
            ft.Text("TUCAN MAX", size=36, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            ft.Text("TUS VENTAS MAS ORGANIZADAS", size=18, color=ft.Colors.BLACK),
        ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        login_form = ft.Column([
            ft.Text("Iniciar Sesión", size=30, weight=ft.FontWeight.W_700, color=ft.Colors.BLACK),
            ft.Container(height=50),
            self.entrada_user,
            ft.Container(height=40),
            self.entrada_contraseña,
            ft.Container(height=50),
            ft.Container(content=self.boton_login, alignment=ft.alignment.center),
            ft.Container(height=20),
            self.mensaje_login,
        ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 🔹 Fila central con logo y formulario, todo expandido
        main_content = ft.Row(
            [
                ft.Container(logo_section, alignment=ft.alignment.center, expand=True),
                ft.Container(login_form, alignment=ft.alignment.center, expand=True),
            ],
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 🔹 Fondo degradado (ocupa toda la pantalla)
        root = ft.Container(
            content=main_content,
            expand=True,
            padding=0,
            margin=0,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    ft.Colors.BLUE_700,
                    ft.Colors.CYAN_200,
                    ft.Colors.TEAL_100,
                ],
            ),
        )

        self.page.clean()
        self.page.add(root)

    # ---------- LOGIN ----------
# ---------- LOGIN ----------
    def obtener_usuario(self, nombre_usuario):
        return (ADMIN_DB.obtener(f"usuarios.{nombre_usuario}") or
                USERS_DB.obtener(f"usuarios.{nombre_usuario}"))

    def validar_login(self, e):
        self.progress_ring.visible = True
        self.boton_login.disabled = True
        self.page.update()
        time.sleep(0.4)

        usuario = self.entrada_user.value.strip() if self.entrada_user.value else ""
        contraseña = self.entrada_contraseña.value if self.entrada_contraseña.value else ""

        if not usuario or not contraseña:
            self.entrada_user.error_text = "Usuario requerido" if not usuario else ""
            self.entrada_contraseña.error_text = "Contraseña requerida" if not contraseña else ""
            self._reset_loading()
            return

        time.sleep(0.4)
        self.entrada_user.error_text = ""
        self.entrada_contraseña.error_text = ""

        # 1) ¿es admin?
        admin_data = ADMIN_DB.obtener(f"usuarios.{usuario}")
        if admin_data and admin_data.get("password") == contraseña:
            self.mensaje_login.value = ""
            self.page.update()
            self.navegar_a_admin()
            return

        # 2) ¿es empleado?
        emp_data = USERS_DB.obtener(f"usuarios.{usuario}")
        if emp_data and emp_data.get("password") == contraseña:
            self.mensaje_login.value = ""
            self.page.update()
            self.navegar_a_empleado()
            return

        # 3) credenciales inválidas
        self.entrada_user.error_text = "Usuario o contraseña incorrecta"
        self.entrada_contraseña.error_text = "Usuario o contraseña incorrecta"
        self._reset_loading()

    def navegar_a_admin(self):
        self.page.clean()
        AdminPanel(self.page)
        self.page.update()

    def navegar_a_empleado(self):
        self.page.clean()
        from empleados.sala_empleados import SalaEmpleados
        # le pasamos el usuario que acaba de hacer login
        usuario = self.entrada_user.value.strip()
        SalaEmpleados(self.page, usuario)
        self.page.update()
        # ---------- HELPERS ----------
    def _reset_loading(self):
        self.progress_ring.visible = False
        self.boton_login.disabled = False
        self.page.update()



# ---------- MAIN ----------
def main(page: ft.Page):
    page.window.bgcolor = ft.Colors.BLACK
    page.padding = 0
    page.spacing = 0
    LoginApp(page)


