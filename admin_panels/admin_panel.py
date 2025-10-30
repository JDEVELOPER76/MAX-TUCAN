import flet as ft
from flet import (
    Icons, Colors, FontWeight, MainAxisAlignment, CrossAxisAlignment,
    Animation, AnimationCurve
)
import time
from admin_panels.inventario_window import InventarioWindow
from admin_panels.reportes_window import ReportesWindow
from admin_panels.configuraciones_window import ConfiguracionesWindow


class AdminPanel:
    def __init__(self, page: ft.Page, nombre_usuario: str = "Administrador"):
        self.page = page
        self.nombre_usuario = nombre_usuario
        self._setup_page()
        self.main_view = self._build_main_view()
        self.page.add(self.main_view)
        self.page.update()

    # ------------------------------------------------------------------
    # 0.  Page-level setup  (sin cambios)
    # ------------------------------------------------------------------
    def _setup_page(self):
        self.page.title = "MAX TUCAN Admin"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f8fafc"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.ADAPTIVE

        self.progress_ring = ft.ProgressRing(
            width=20, height=20, stroke_width=2.5, visible=False, color=Colors.WHITE
        )

    # ------------------------------------------------------------------
    # 1.  Main view  (sin bloque inferior de logout)
    # ------------------------------------------------------------------
    def _build_main_view(self):
        return ft.Container(
            content=ft.Column(
                [
                    self._new_header(),
                    self._welcome_banner(),
                    self._modules_grid(),
                ],
                spacing=0,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            expand=True,
        )

    # ------------------------------------------------------------------
    # 2.  Header  (botón de cerrar sesión incluido)
    # ------------------------------------------------------------------
    def _new_header(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
                                              size=28, color=Colors.WHITE),
                                bgcolor="#4f46e5",
                                border_radius=12,
                                padding=10,
                                shadow=ft.BoxShadow(
                                    spread_radius=0, blur_radius=12,
                                    color=ft.Colors.with_opacity(0.3, "#4f46e5"),
                                    offset=ft.Offset(0, 4)
                                )
                            ),
                            ft.Column(
                                [
                                    ft.Text("MAX TUCAN", size=22, weight=FontWeight.W_700,
                                            color="#1e293b"),
                                    ft.Text("Panel Administrativo", size=13,
                                            weight=FontWeight.W_400, color="#64748b"),
                                ], spacing=2, alignment=MainAxisAlignment.CENTER
                            ),
                        ], spacing=16, vertical_alignment=CrossAxisAlignment.CENTER
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(Icons.PERSON_ROUNDED, size=20, color="#4f46e5"),
                                        ft.Text(self.nombre_usuario, size=14,
                                                weight=FontWeight.W_500, color="#1e293b"),
                                    ], spacing=8
                                ),
                                bgcolor="#f1f5f9",
                                border_radius=20,
                                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        self.progress_ring,
                                        ft.Icon(Icons.LOGOUT_ROUNDED, size=18, color=Colors.WHITE),
                                        ft.Text("Cerrar Sesión", size=14, weight=FontWeight.W_500,
                                                color=Colors.WHITE)
                                    ], spacing=10
                                ),
                                bgcolor="#ef4444",
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=20, vertical=12),
                                ink=True,
                                on_click=self.cerrar_sesion,
                                animate=ft.Animation(200, AnimationCurve.EASE_OUT),
                                shadow=ft.BoxShadow(
                                    spread_radius=0,
                                    blur_radius=12,
                                    color=ft.Colors.with_opacity(0.3, "#ef4444"),
                                    offset=ft.Offset(0, 4)
                                ),
                                on_hover=self._hover_button
                            ),
                        ], spacing=12
                    ),
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=20),
            bgcolor=Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=20,
                color=ft.Colors.with_opacity(0.04, Colors.BLACK),
                offset=ft.Offset(0, 4)
            )
        )

    # ------------------------------------------------------------------
    # 3.  Welcome banner  (igual)
    # ------------------------------------------------------------------
    def _welcome_banner(self):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Bienvenido de vuelta,", size=32,
                                    weight=FontWeight.W_700, color="#1e293b"),
                            ft.Text(self.nombre_usuario.split()[0] + ".", size=32,
                                    weight=FontWeight.W_700, color="#4f46e5"),
                            ft.Container(height=8),
                            ft.Text("Gestiona tu negocio desde un solo lugar.", size=16,
                                    color="#64748b"),
                        ], spacing=4
                    ),
                    ft.Container(expand=True),
                    ft.Icon(Icons.ROCKET_LAUNCH_ROUNDED, size=80,
                            color=ft.Colors.with_opacity(0.12, "#4f46e5"))
                ], alignment=MainAxisAlignment.SPACE_BETWEEN
            ),
            margin=ft.margin.symmetric(horizontal=32, vertical=24),
            padding=ft.padding.all(32),
            bgcolor=ft.Colors.with_opacity(0.05, "#4f46e5"),
            border_radius=24,
        )

    # ------------------------------------------------------------------
    # 4.  Modules grid  (sin cambios)
    # ------------------------------------------------------------------
    def _modules_grid(self):
        def module_card(icon, label, desc, color, enabled=True):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Icon(icon, size=32,
                                          color=Colors.WHITE if enabled else "#cbd5e1"),
                            bgcolor=color if enabled else "#e2e8f0",
                            border_radius=14,
                            padding=16,
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=16,
                                color=ft.Colors.with_opacity(
                                    0.25 if enabled else 0.08,
                                    color if enabled else Colors.BLACK
                                ),
                                offset=ft.Offset(0, 6)
                            ) if enabled else None,
                        ),
                        ft.Container(height=16),
                        ft.Text(label, size=16, weight=FontWeight.W_600,
                                color="#1e293b" if enabled else "#94a3b8",
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(desc, size=12, color="#94a3b8",
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=0
                ),
                bgcolor=Colors.WHITE,
                border_radius=16,
                padding=24,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.with_opacity(0.06 if enabled else 0.03,
                                              Colors.BLACK),
                    offset=ft.Offset(0, 4)
                ),
                ink=enabled,
                animate=ft.Animation(300, AnimationCurve.EASE_OUT),
                scale=1,
                tooltip="Próximamente" if not enabled else None,
                on_click=lambda _: self._open_module(label) if enabled else None,
                on_hover=lambda e: self._hover_card(e, 1.05) if enabled else None
            )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Módulos del Sistema", size=18, weight=FontWeight.W_700,
                            color="#1e293b"),
                    ft.Container(height=16),
                    ft.ResponsiveRow(
                        [
                            ft.Container(
                                module_card(
                                    Icons.PERSON_ADD_ROUNDED, "Usuarios",
                                    "Altas, bajas y permisos", "#4f46e5", True
                                ), col={"sm": 6, "md": 3}, padding=8
                            ),
                            ft.Container(
                                module_card(
                                    Icons.SHOPPING_BAG_ROUNDED, "Productos",
                                    "Catálogo y códigos SAT", "#10b981", True
                                ), col={"sm": 6, "md": 3}, padding=8
                            ),
                            ft.Container(
                                module_card(
                                    Icons.SHOPPING_CART_ROUNDED, "Compras",
                                    "Proveedores y órdenes", "#f59e0b", True
                                ), col={"sm": 6, "md": 3}, padding=8
                            ),
                            ft.Container(
                                module_card(
                                    Icons.SETTINGS_ROUNDED, "Configuración",
                                    "Empresa e impresoras", "#6366f1", True
                                ), col={"sm": 6, "md": 3}, padding=8
                            ),
                            ft.Container(
                                module_card(
                                    Icons.INVENTORY_2_ROUNDED, "Inventario",
                                    "Gestionar stock y productos", "#8b5cf6", True
                                ), col={"sm": 6, "md": 3}, padding=8
                            ),
                            ft.Container(
                                module_card(
                                    Icons.BAR_CHART_ROUNDED, "Reportes",
                                    "Análisis y estadísticas", "#06b6d4", True
                                ), col={"sm": 6, "md": 3}, padding=8
                            ),
                        ]
                    )
                ], spacing=0
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=16)
        )

    # ------------------------------------------------------------------
    # 5.  Helpers originales  (sin cambios)
    # ------------------------------------------------------------------
    def setup_ui(self):
        self.page.clean()
        self.page.add(self.main_view)
        self.page.update()

    def _change_view(self, view):
        self.page.clean()
        self.page.add(view)
        self.page.update()

    def _hover_card(self, e, scale):
        e.control.scale = scale if e.data == "true" else 1.0
        e.control.update()

    def _hover_button(self, e):
        if e.data == "true":
            e.control.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.4, "#ef4444"),
                offset=ft.Offset(0, 6)
            )
        else:
            e.control.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.3, "#ef4444"),
                offset=ft.Offset(0, 4)
            )
        e.control.update()

    # ------------------------------------------------------------------
    # 6.  Navegación y cierre  (sin cambios)
    # ------------------------------------------------------------------
    def _open_module(self, label: str):
        if label == "Productos":
            from admin_panels.productos_window import ProductosWindow
            self._change_view(ProductosWindow(self.page, self).build_ui())
        elif label == "Usuarios":
            from admin_panels.usuarios_window import UsuariosWindow
            self._change_view(UsuariosWindow(self.page, self).build_ui())
        elif label == "Compras":
            from admin_panels.compras_window import ComprasWindow
            self._change_view(ComprasWindow(self.page, self).build_ui())
        elif label == "Configuración":
            self._change_view(ConfiguracionesWindow(self.page, self).build_ui())
        elif label == "Inventario":
            self._change_view(InventarioWindow(self.page, self).build_ui())
        elif label == "Reportes":
            nombre_usuario = getattr(self, 'nombre_usuario', 'Administrador')
            ReportesWindow(self.page, self, nombre_usuario)

    def cerrar_sesion(self, e):
        self.progress_ring.visible = True
        e.control.content.controls[2].value = "Cerrando..."
        self.page.update()
        time.sleep(0.5)
        self.progress_ring.visible = False
        e.control.content.controls[2].value = "Cerrar Sesión"
        self.page.update()
        from login import LoginApp
        LoginApp(self.page)