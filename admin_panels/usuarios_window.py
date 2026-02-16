# usuarios_window.py – Versión corregida: widgets a pantalla completa
import flet as ft
from mananger.user_manager import (
    crear_usuario, listar_todos, usuario_existe,
    actualizar_usuario, eliminar_usuario
)

class UsuariosWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        self.page.title = "Usuarios - MAX TUCAN"
        self.page.bgcolor = "#f3f4f6"
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window_maximized = True  # 🔹 abre maximizada
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.page.clean()
        self.page.add(self.build_ui())
        self.page.update()

    # -----------------  INTERFAZ PRINCIPAL -----------------
    def build_ui(self):
        self.tabla_usuarios = self._crear_tabla_usuarios()

        # HEADER - parte superior fija
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW,
                    on_click=self.regresar_panel_admin,
                    tooltip="Volver",
                    icon_color="#6366f1"
                ),
                ft.Text("Gestión de Usuarios",
                        size=28, weight=ft.FontWeight.BOLD,
                        color="#1e293b"),
                ft.ElevatedButton(
                    "Nuevo Usuario",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=self.nuevo_usuario,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor="#6366f1",
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.padding.symmetric(horizontal=18, vertical=14)
                    )
                )
            ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)),
        )

        # TABLA - ocupa el resto del espacio disponible
        tabla_container = ft.Container(
            content=self.tabla_usuarios,
            padding=ft.padding.all(20),
            expand=True,  # 🔹 ocupa todo el alto restante
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK))
        )

        # Layout principal en columna
        main_layout = ft.Column(
            [
                header,
                tabla_container
            ],
            expand=True,  # 🔹 hace que todo llene la ventana
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # Contenedor raíz (ocupa toda la ventana)
        root = ft.Container(
            content=main_layout,
            expand=True  # 🔹 ocupa todo el espacio de la página
        )

        return root

    # -----------------  NAVEGACIÓN  -----------------
    def regresar_panel_admin(self, e):
        self.page.clean()
        self.admin_panel.setup_ui()

    # -----------------  TABLA DE USUARIOS -----------------
    def _crear_tabla_usuarios(self):
        return ft.DataTable(
            expand=True,
            heading_row_color=ft.Colors.with_opacity(0.05, "#6366f1"),
            heading_text_style=ft.TextStyle(size=16, weight=ft.FontWeight.W_600, color="#1e293b"),
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=12,
            column_spacing=24,
            columns=[
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Rol")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Archivo")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=self._crear_filas_usuarios()
        )

    def _crear_filas_usuarios(self):
        filas = []
        for usuario_data in listar_todos():
            def editar(e, u=usuario_data): self.editar_usuario(u)
            def eliminar(e, u=usuario_data): self.confirmar_eliminar(u)

            # Determinar en qué archivo está guardado el usuario
            archivo = "admin.json" if usuario_data["tipo"] == "admin" else "users.json"

            filas.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(usuario_data["usuario"], size=15, weight=ft.FontWeight.W_500)),
                ft.DataCell(ft.Text(usuario_data["rol"], size=15)),
                ft.DataCell(ft.Container(
                    content=ft.Text(usuario_data["estado"], size=14,
                                    color="#059669" if usuario_data["estado"] == "Activo" else "#dc2626"),
                    bgcolor=ft.Colors.with_opacity(0.12,
                                    "#059669" if usuario_data["estado"] == "Activo" else "#dc2626"),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4)
                )),
                ft.DataCell(ft.Text(usuario_data["tipo"].capitalize(), size=15)),
                ft.DataCell(ft.Text(archivo, size=14, color=ft.Colors.GREY_600)),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_color="#6366f1", tooltip="Editar", on_click=editar),
                    ft.IconButton(ft.Icons.DELETE, icon_color="#ef4444", tooltip="Eliminar", on_click=eliminar)
                ], spacing=8))
            ]))
        return filas

    # -----------------  ALTA / EDICIÓN -----------------
    def nuevo_usuario(self, e): self._abrir_dialogo_usuario()
    def editar_usuario(self, u): self._abrir_dialogo_usuario(u)

    # -----------------  ELIMINAR -----------------
    def confirmar_eliminar(self, u):
        def confirmar(e):
            try:
                eliminar_usuario(u["usuario"])
                self.page.close(dlg)
                self.actualizar_vista()
                self._mostrar_mensaje("Usuario eliminado")
            except Exception as ex:
                self._mostrar_mensaje(f"Error: {ex}")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar eliminación"),
            content=ft.Text(f"¿Eliminar usuario {u['usuario']}?"),
            actions=[
                ft.TextButton("Sí", on_click=confirmar),
                ft.TextButton("No", on_click=lambda _: self.page.close(dlg)),
            ]
        )
        self.page.open(dlg)

    # -----------------  FORMULARIO -----------------
    def _abrir_dialogo_usuario(self, usuario=None):
        es_edicion = usuario is not None
        campo_usuario = ft.TextField(
            label="Usuario",
            value=usuario["usuario"] if es_edicion else "",
            disabled=es_edicion,
            border_radius=8
        )
        campo_password = ft.TextField(
            label="Contraseña",
            password=True,
            can_reveal_password=True,
            value=usuario["password"] if es_edicion else "",
            border_radius=8
        )
        dropdown_rol = ft.Dropdown(
            label="Rol",
            value=usuario["rol"] if es_edicion else "Cajero",
            options=[ft.dropdown.Option(r) for r in ["Admin", "Cajero", "Auditor"]],
            border_radius=8
        )
        dropdown_estado = ft.Dropdown(
            label="Estado",
            value=usuario["estado"] if es_edicion else "Activo",
            options=[ft.dropdown.Option(e) for e in ["Activo", "Inactivo"]],
            border_radius=8
        )
        dropdown_tipo = ft.Dropdown(
            label="Tipo",
            value=usuario["tipo"] if es_edicion else "empleado",
            options=[ft.dropdown.Option(t) for t in ["admin", "empleado"]],
            border_radius=8
        )

        def guardar(e):
            if not campo_usuario.value or not campo_password.value:
                self._mostrar_mensaje("Complete todos los campos")
                return
            if not es_edicion and usuario_existe(campo_usuario.value):
                self._mostrar_mensaje("Usuario ya existe")
                return

            datos = {
                "password": campo_password.value,
                "rol": dropdown_rol.value,
                "estado": dropdown_estado.value,
                "tipo": dropdown_tipo.value
            }

            try:
                if es_edicion:
                    # Si cambió el tipo, necesitamos eliminar y recrear en el archivo correcto
                    if usuario["tipo"] != dropdown_tipo.value:
                        # Eliminar del archivo actual
                        eliminar_usuario(usuario["usuario"])
                        # Crear en el nuevo archivo
                        crear_usuario(
                            username=campo_usuario.value,
                            password=datos["password"],
                            rol=datos["rol"],
                            estado=datos["estado"],
                            tipo=datos["tipo"]
                        )
                    else:
                        # Actualizar en el mismo archivo
                        actualizar_usuario(campo_usuario.value, datos)
                    msg = "Usuario actualizado"
                else:
                    # Crear nuevo usuario en el archivo correspondiente
                    crear_usuario(
                        username=campo_usuario.value,
                        password=datos["password"],
                        rol=datos["rol"],
                        estado=datos["estado"],
                        tipo=datos["tipo"]
                    )
                    msg = "Usuario creado"

                self.page.close(dlg)
                self.actualizar_vista()
                self._mostrar_mensaje(msg)
            except Exception as ex:
                self._mostrar_mensaje(f"Error: {ex}")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar usuario" if es_edicion else "Nuevo usuario"),
            content=ft.Column([
                campo_usuario, campo_password, dropdown_rol,
                dropdown_estado, dropdown_tipo
            ], spacing=12, tight=True),
            actions=[
                ft.TextButton("Guardar", on_click=guardar),
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dlg)),
            ]
        )
        self.page.open(dlg)

    # -----------------  UTILS -----------------
    def _mostrar_mensaje(self, msg):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg))
        self.page.snack_bar.open = True
        self.page.update()

    def actualizar_vista(self):
        self.tabla_usuarios.rows = self._crear_filas_usuarios()
        self.page.update()