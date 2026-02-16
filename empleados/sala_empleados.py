import flet as ft
import asyncio
from datetime import datetime, date
from BASEDATOS import db

class SalaEmpleados:
    """Sala de Empleados"""
    
    def __init__(self, page: ft.Page, nombre_usuario: str):
        self.page = page
        self.nombre_usuario = nombre_usuario
        self.page.title = f"Sala de Empleados – {self.nombre_usuario}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f5f7fb"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO

        self.reloj_hora = None
        self.reloj_fecha = None
        self.reloj_task = None
        
        # Paleta de colores premium
        self.colors = {
            "primary": "#0a2540",
            "secondary": "#2d7ee9",
            "accent": "#6c5ce7",
            "success": "#27ae60",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "info": "#3498db",
            "dark": "#1a2634",
            "light": "#ffffff",
            "gray_100": "#f8fafc",
            "gray_200": "#f1f5f9",
            "gray_300": "#e2e8f0",
            "gray_400": "#cbd5e0",
            "gray_500": "#94a3b8",
            "gray_600": "#64748b",
            "gray_700": "#475569",
            "gray_800": "#1e293b",
            "gray_900": "#0f172a",
        }
        
        db.inicializar_bd()
        self.build_ui()

    def _actualizar_reloj(self):
        """Actualiza la hora y fecha en pantalla"""
        ahora = datetime.now()
        if self.reloj_hora:
            self.reloj_hora.value = ahora.strftime("%H:%M")
        if self.reloj_fecha:
            self.reloj_fecha.value = ahora.strftime("%A, %d %B %Y")

    async def _reloj_loop(self):
        """Bucle de actualizacion de reloj"""
        while True:
            try:
                self._actualizar_reloj()
                if self.page:
                    self.page.update()
            except Exception as e:
                # Silenciar errores cuando la página cambia o se cierra
                print(f"⚠️ Advertencia en reloj: {e}")
                break
            await asyncio.sleep(1)

    # ---------- NAVEGACIÓN ----------
    def abrir_menu_ventas(self, e):
        from empleados.menu_ventas import MenuVentas
        self.page.clean()
        MenuVentas(self.page, self.nombre_usuario)
        self.page.update()

    def cerrar_sesion(self, e):
        boton_cerrar = e.control
        
        boton_cerrar.disabled = True
        boton_cerrar.content = ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=self.colors["secondary"]),
            ft.Text("Cerrando sesión...", size=14, color=self.colors["gray_600"]),
        ], spacing=8)
        self.page.update()

        db.registrar_auditoria(
            usuario=self.nombre_usuario,
            tipo="logout",
            descripcion="Cierre de sesión",
            detalles="Salida del sistema de ventas"
        )

        import time
        time.sleep(1.5)
        
        from inicio.login import LoginApp
        self.page.clean()
        LoginApp(self.page)
        self.page.update()

    # ---------- COMPONENTES PREMIUM ----------
    def _crear_header(self):
        """Header con diseño"""
        ahora = datetime.now()
        self.reloj_hora = ft.Text(
            ahora.strftime("%H:%M"),
            size=18,
            weight=ft.FontWeight.W_700,
            color=ft.Colors.WHITE,
        )
        self.reloj_fecha = ft.Text(
            ahora.strftime("%A, %d %B %Y"),
            size=11,
            color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
            weight=ft.FontWeight.W_400,
        )
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.APARTMENT_ROUNDED, size=28, color=ft.Colors.WHITE),
                                ft.Text(
                                    "Sala de Empleados",
                                    size=24,
                                    weight=ft.FontWeight.W_700,
                                    color=ft.Colors.WHITE,
                                ),
                            ], spacing=12),
                            padding=ft.padding.only(left=8, right=20, top=8, bottom=8),
                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                            border_radius=40,
                        ),
                        ft.Column([
                            ft.Text(
                                f"{self.nombre_usuario}",
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                "Empleado",
                                size=12,
                                color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE),
                                weight=ft.FontWeight.W_400,
                            ),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START),
                    ], spacing=20),
                    
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                self.reloj_hora,
                                self.reloj_fecha,
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                            border_radius=12,
                        ),
                        ft.Container(
                            content=ft.IconButton(
                                icon=ft.Icons.LOGOUT_ROUNDED,
                                icon_size=20,
                                icon_color=self.colors["gray_700"],
                                bgcolor=ft.Colors.WHITE,
                                on_click=self.cerrar_sesion,
                                tooltip="Cerrar sesión",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    padding=12,
                                ),
                            ),
                            border_radius=10,
                        ),
                    ], spacing=12),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ]),
            padding=ft.padding.symmetric(horizontal=40, vertical=28),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[self.colors["primary"], self.colors["dark"]],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=30,
                color=ft.Colors.with_opacity(0.2, self.colors["dark"]),
                offset=ft.Offset(0, 8)
            ),
        )

    def _crear_banner_principal(self):
        """Banner principal con acceso a menú de ventas - Diseño premium"""
        return ft.Container(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.POINT_OF_SALE_ROUNDED, size=32, color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                            padding=14,
                            border_radius=16,
                        ),
                        ft.Column([
                            ft.Text(
                                "Sistema de Ventas",
                                size=22,
                                weight=ft.FontWeight.W_700,
                                color=ft.Colors.WHITE,
                            ),
                            ft.Text(
                                "Acceso directo al módulo de facturación y ventas",
                                size=13,
                                color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                            ),
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.START),
                        ft.Container(expand=True),
                        ft.Container(
                            content=ft.Row([
                                ft.Text(
                                    "Iniciar",
                                    size=15,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.WHITE,
                                ),
                                ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=18, color=ft.Colors.WHITE),
                            ], spacing=8),
                            padding=ft.padding.symmetric(horizontal=24, vertical=12),
                            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                            border_radius=30,
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ]),
                padding=30,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.center_left,
                    end=ft.alignment.center_right,
                    colors=[self.colors["secondary"], "#4b9fe1"],
                ),
                border_radius=20,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=25,
                    color=ft.Colors.with_opacity(0.25, self.colors["secondary"]),
                    offset=ft.Offset(0, 10)
                ),
            ),
            margin=ft.margin.symmetric(horizontal=40, vertical=20),
            ink=True,
            on_click=self.abrir_menu_ventas,
        )

    def _crear_tarjeta_acceso(self, titulo, descripcion, valor, icono, color):
        """Tarjeta de acceso rápido premium"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icono, size=24, color=ft.Colors.WHITE),
                        bgcolor=color,
                        padding=12,
                        border_radius=12,
                    ),
                    ft.Column([
                        ft.Text(
                            titulo,
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.colors["gray_800"],
                        ),
                        ft.Text(
                            descripcion,
                            size=12,
                            color=self.colors["gray_600"],
                        ),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START, expand=True),
                ], spacing=16),
                ft.Divider(height=24, color=self.colors["gray_200"]),
                ft.Row([
                    ft.Text(
                        valor,
                        size=24,
                        weight=ft.FontWeight.W_700,
                        color=color,
                    ),
                    ft.Container(expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=18, color=self.colors["gray_400"]),
                ]),
            ]),
            padding=24,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.08, self.colors["gray_700"]),
                offset=ft.Offset(0, 5)
            ),
            ink=True,
            on_click=None,
        )

    def _crear_kpi_card(self, titulo, valor, subtitulo, icono, color_fondo, color_icono):
        """Tarjeta KPI premium"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icono, size=20, color=color_icono),
                        bgcolor=ft.Colors.with_opacity(0.15, color_icono),
                        padding=10,
                        border_radius=10,
                    ),
                    ft.Column([
                        ft.Text(
                            titulo,
                            size=13,
                            color=self.colors["gray_600"],
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Text(
                            valor,
                            size=26,
                            weight=ft.FontWeight.W_700,
                            color=self.colors["gray_800"],
                        ),
                    ], spacing=2, expand=True, horizontal_alignment=ft.CrossAxisAlignment.END),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=8),
                ft.Text(
                    subtitulo,
                    size=11,
                    color=self.colors["gray_500"],
                ),
            ]),
            padding=20,
            bgcolor=color_fondo,
            border_radius=14,
            border=ft.border.all(1, ft.Colors.with_opacity(0.1, color_icono)),
            expand=True,
        )

    # ---------- UI PRINCIPAL ----------
    def build_ui(self):
        """Construye la interfaz principal con diseño lobby premium"""
        
        # Obtener datos reales (recarga siempre los datos frescos)
        total_dia = db.ventas_del_dia(self.nombre_usuario)
        todas_ventas = self._obtener_todas_ventas()
        cantidad_ventas = len(todas_ventas)
        
        print(f"DEBUG Sala Empleados - Total día: ${total_dia}, Cantidad ventas: {cantidad_ventas}")
        print(f"DEBUG Sala Empleados - Ventas obtenidas: {todas_ventas[:3] if len(todas_ventas) > 0 else 'ninguna'}")
        
        # Header
        header = self._crear_header()
        
        # Banner principal
        banner_ventas = self._crear_banner_principal()
        
        # Grid de accesos rápidos premium
        accesos_rapidos = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE_ROUNDED, size=22, color=self.colors["primary"]),
                            ft.Text(
                                "Panel de Control",
                                size=18,
                                weight=ft.FontWeight.W_600,
                                color=self.colors["gray_800"],
                            ),
                        ], spacing=12),
                        padding=ft.padding.only(bottom=8),
                    ),
                ]),
                ft.ResponsiveRow([
                    ft.Container(
                        content=self._crear_tarjeta_acceso(
                            "Historial de Ventas",
                            "Todas las transacciones del día",
                            f"{cantidad_ventas} operaciones",
                            ft.Icons.RECEIPT_LONG_ROUNDED,
                            self.colors["info"],
                        ),
                        col={"sm": 12, "md": 6},
                        on_click=lambda e: self.mostrar_todas_ventas(todas_ventas),
                    ),
                    ft.Container(
                        content=self._crear_tarjeta_acceso(
                            "Resumen Financiero",
                            "Ingresos y estadísticas",
                            f"${total_dia:,.2f}",
                            ft.Icons.ANALYTICS_ROUNDED,
                            self.colors["success"],
                        ),
                        col={"sm": 12, "md": 6},
                        on_click=lambda e: self.mostrar_resumen(total_dia, cantidad_ventas),
                    ),
                ], spacing=20),
            ]),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            margin=ft.margin.only(left=40, right=40, top=0, bottom=20),
            border_radius=20,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=30,
                color=ft.Colors.with_opacity(0.06, self.colors["gray_700"]),
                offset=ft.Offset(0, 5)
            ),
        )
        
        # Panel KPI premium
        kpi_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INSIGHTS_ROUNDED, size=22, color=self.colors["primary"]),
                    ft.Text(
                        "Métricas del Día",
                        size=18,
                        weight=ft.FontWeight.W_600,
                        color=self.colors["gray_800"],
                    ),
                ], spacing=12),
                ft.Container(height=16),
                ft.ResponsiveRow([
                    ft.Container(
                        content=self._crear_kpi_card(
                            "Transacciones",
                            f"{cantidad_ventas}",
                            "Ventas realizadas hoy",
                            ft.Icons.SHOPPING_CART_ROUNDED,
                            "#eff6ff",
                            self.colors["info"],
                        ),
                        col={"sm": 12, "md": 4},
                    ),
                    ft.Container(
                        content=self._crear_kpi_card(
                            "Ingresos",
                            f"${total_dia:,.2f}",
                            "Total acumulado",
                            ft.Icons.ATTACH_MONEY_ROUNDED,
                            "#f0fdf4",
                            self.colors["success"],
                        ),
                        col={"sm": 12, "md": 4},
                    ),
                    ft.Container(
                        content=self._crear_kpi_card(
                            "Ticket Promedio",
                            f"${total_dia / cantidad_ventas:,.2f}" if cantidad_ventas > 0 else "$0.00",
                            "Por transacción",
                            ft.Icons.CALCULATE_ROUNDED,
                            "#fefce8",
                            self.colors["warning"],
                        ),
                        col={"sm": 12, "md": 4},
                    ),
                ], spacing=20),
            ]),
            padding=40,
            bgcolor=ft.Colors.WHITE,
            margin=ft.margin.only(left=40, right=40, top=0, bottom=20),
            border_radius=20,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=30,
                color=ft.Colors.with_opacity(0.06, self.colors["gray_700"]),
                offset=ft.Offset(0, 5)
            ),
        )
        
        # Layout principal
        main_content = ft.Column([
            header,
            banner_ventas,
            accesos_rapidos,
            kpi_panel,
        ], spacing=0, scroll=ft.ScrollMode.AUTO)
        
        self.page.clean()
        self.page.add(main_content)

        if not self.reloj_task:
            self.reloj_task = self.page.run_task(self._reloj_loop)

    # ---------- FUNCIONES DE DATOS ----------
    def _obtener_todas_ventas(self):
        """Obtiene todas las ventas del día actual"""
        try:
            ventas = db.ultimas_ventas(self.nombre_usuario, 0)
            print(f"DEBUG: Ventas obtenidas de DB: {len(ventas) if ventas else 0} registros")
            return ventas if ventas is not None else []
        except Exception as e:
            print(f"Error obteniendo ventas: {e}")
            import traceback
            traceback.print_exc()
            return []

    # ---------- DIÁLOGOS PREMIUM ----------
    def mostrar_todas_ventas(self, ventas):
        """Muestra todas las ventas en diálogo premium"""
        if not ventas:
            contenido = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RECEIPT_ROUNDED, size=56, color=self.colors["gray_300"]),
                    ft.Text(
                        "Sin ventas registradas",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=self.colors["gray_600"],
                    ),
                    ft.Text(
                        "Hoy no se han realizado transacciones",
                        size=13,
                        color=self.colors["gray_500"],
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
                padding=40,
            )
        else:
            # ListView con scroll
            lista = ft.ListView(
                expand=True,
                spacing=8,
                padding=20,
                auto_scroll=False,
            )
            
            # Header
            lista.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("Hora", size=12, weight=ft.FontWeight.W_600, color=self.colors["primary"], width=70),
                        ft.Text("Descripción", size=12, weight=ft.FontWeight.W_600, color=self.colors["primary"], expand=True),
                        ft.Text("Monto", size=12, weight=ft.FontWeight.W_600, color=self.colors["primary"], width=100, text_align=ft.TextAlign.RIGHT),
                    ]),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    bgcolor=ft.Colors.with_opacity(0.08, self.colors["primary"]),
                    border_radius=10,
                )
            )
            
            # Filas de ventas
            for i, v in enumerate(ventas):
                bg_color = ft.Colors.WHITE if i % 2 == 0 else self.colors["gray_100"]
                
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(v[0] if v[0] else "--:--", size=12, color=self.colors["gray_700"], width=70),
                            ft.Text(
                                v[1] if v[1] else "Producto no especificado",
                                size=12,
                                color=self.colors["gray_800"],
                                expand=True,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"${v[2]:.2f}" if v[2] else "$0.00",
                                size=12,
                                weight=ft.FontWeight.W_600,
                                color=self.colors["success"],
                                width=100,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                        ]),
                        padding=ft.padding.symmetric(horizontal=16, vertical=12),
                        bgcolor=bg_color,
                        border_radius=8,
                    )
                )
            
            contenido = ft.Container(
                content=lista,
                width=600,
                height=450,
            )
        
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, size=24, color=ft.Colors.WHITE),
                    bgcolor=self.colors["primary"],
                    padding=10,
                    border_radius=10,
                ),
                ft.Text(
                    f"Historial de Ventas · {len(ventas)} transacciones",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=self.colors["gray_800"],
                ),
            ], spacing=16),
            content=contenido,
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self.page.close(dlg),
                    style=ft.ButtonStyle(
                        color=self.colors["primary"],
                        text_style=ft.TextStyle(weight=ft.FontWeight.W_600, size=13),
                    ),
                )
            ],
            content_padding=0,
            actions_padding=20,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        self.page.open(dlg)

    def mostrar_resumen(self, total, cantidad_ventas):
        """Muestra resumen financiero en diálogo premium"""
        ticket_promedio = total / cantidad_ventas if cantidad_ventas > 0 else 0
        
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.ANALYTICS_ROUNDED, size=24, color=ft.Colors.WHITE),
                    bgcolor=self.colors["success"],
                    padding=10,
                    border_radius=10,
                ),
                ft.Text(
                    "Resumen Financiero",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=self.colors["gray_800"],
                ),
            ], spacing=16),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.SHOPPING_CART_ROUNDED, size=32, color=self.colors["info"]),
                                ft.Text(
                                    f"{cantidad_ventas}",
                                    size=36,
                                    weight=ft.FontWeight.W_700,
                                    color=self.colors["gray_800"],
                                ),
                                ft.Text(
                                    "Transacciones",
                                    size=13,
                                    color=self.colors["gray_600"],
                                    weight=ft.FontWeight.W_500,
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                            padding=24,
                            bgcolor="#eff6ff",
                            border_radius=16,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.ATTACH_MONEY_ROUNDED, size=32, color=self.colors["success"]),
                                ft.Text(
                                    f"${total:,.2f}",
                                    size=36,
                                    weight=ft.FontWeight.W_700,
                                    color=self.colors["gray_800"],
                                ),
                                ft.Text(
                                    "Ingresos",
                                    size=13,
                                    color=self.colors["gray_600"],
                                    weight=ft.FontWeight.W_500,
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                            padding=24,
                            bgcolor="#f0fdf4",
                            border_radius=16,
                            expand=True,
                        ),
                    ], spacing=16),
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text("Ticket Promedio", size=14, color=self.colors["gray_600"]),
                                ft.Container(expand=True),
                                ft.Text(f"${ticket_promedio:,.2f}", size=20, weight=ft.FontWeight.W_700, color=self.colors["gray_800"]),
                            ]),
                            ft.Divider(height=20, color=self.colors["gray_200"]),
                            ft.Row([
                                ft.Column([
                                    ft.Text("Empleado", size=12, color=self.colors["gray_500"]),
                                    ft.Text(self.nombre_usuario, size=14, weight=ft.FontWeight.W_600, color=self.colors["gray_700"]),
                                ], spacing=4),
                                ft.Container(expand=True),
                                ft.Column([
                                    ft.Text("Fecha", size=12, color=self.colors["gray_500"]),
                                    ft.Text(
                                        date.today().strftime("%d/%m/%Y"),
                                        size=14,
                                        weight=ft.FontWeight.W_600,
                                        color=self.colors["gray_700"],
                                    ),
                                ], spacing=4),
                            ]),
                        ]),
                        padding=24,
                        bgcolor=self.colors["gray_100"],
                        border_radius=14,
                    ),
                ]),
                padding=20,
                width=500,
            ),
            actions=[
                ft.TextButton(
                    "Cerrar",
                    on_click=lambda e: self.page.close(dlg),
                    style=ft.ButtonStyle(
                        color=self.colors["success"],
                        text_style=ft.TextStyle(weight=ft.FontWeight.W_600, size=13),
                    ),
                )
            ],
            actions_padding=20,
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        self.page.open(dlg)