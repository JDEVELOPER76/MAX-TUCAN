import flet as ft
from datetime import datetime, date
from BASEDATOS import db

class SalaEmpleados:
    def __init__(self, page: ft.Page, nombre_usuario: str):
        self.page = page
        self.nombre_usuario = nombre_usuario
        self.page.title = f"Sala de Empleados – {self.nombre_usuario}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f8fafc"
        self.page.padding = 0
        db.inicializar_bd()
        self.build_ui()

    # ---------- NAVEGACIÓN ----------
    def abrir_menu_ventas(self, e):
        from empleados.menu_ventas import MenuVentas
        self.page.clean()
        MenuVentas(self.page, self.nombre_usuario)
        self.page.update()

    def cerrar_sesion(self, e):
        # Obtener referencia al botón
        boton_cerrar = e.control
        
        # Deshabilitar el botón y mostrar indicador de carga
        boton_cerrar.disabled = True
        boton_cerrar.content = ft.Row([
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.INDIGO_700),
            ft.Text("Cerrando...")
        ], spacing=6)
        self.page.update()

        # Cerrar sesión después de un breve delay
        import time
        time.sleep(1.5)  # Mostrar la carga por 1.5 segundos
        
        from login import LoginApp
        self.page.clean()
        LoginApp(self.page)
        self.page.update()

    # ---------- UI COMPACTA Y RESPONSIVA ----------
    def build_ui(self):
        # Header más compacto
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.BUSINESS_CENTER, size=24, color=ft.Colors.WHITE),
                        padding=8,
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        border_radius=10,
                    ),
                    ft.Column([
                        ft.Text("Sala de Empleados", size=18, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE),
                        ft.Text(f"Bienvenido, {self.nombre_usuario}", size=12, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
                    ], spacing=1),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                
                ft.Container(expand=True),
                
                ft.Column([
                    ft.Text(f"{datetime.now().strftime('%d/%m/%Y')}", size=12, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
                    ft.Text(f"{datetime.now().strftime('%H:%M')}", size=11, color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)),
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=1),
                
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([ft.Icon(ft.Icons.LOGOUT, size=14), ft.Text("Salir")], spacing=6),
                        on_click=self.cerrar_sesion,
                        style=ft.ButtonStyle(
                            color=ft.Colors.INDIGO_700,
                            bgcolor=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=8),
                            padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        )
                    ),
                    margin=ft.margin.only(left=10)
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            bgcolor=ft.Colors.INDIGO_700,
            shadow=ft.BoxShadow(
                blur_radius=8,
                color=ft.Colors.with_opacity(0.3, ft.Colors.INDIGO_900),
                offset=ft.Offset(0, 2)
            )
        )

        # ... (el resto del código permanece igual)
        # Botón principal más compacto
        btn_ventas = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.POINT_OF_SALE, size=22, color=ft.Colors.WHITE),
                    ft.Column([
                        ft.Text("Menú de Ventas", size=16, weight=ft.FontWeight.W_600),
                        ft.Text("Sistema de ventas y facturación", size=11, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
                    ], spacing=2),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                on_click=self.abrir_menu_ventas,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(horizontal=25, vertical=15),
                ),
            ),
            alignment=ft.alignment.center,
            margin=ft.margin.symmetric(horizontal=20, vertical=8),
        )

        # Obtener datos REALES de ventas
        total_dia = db.ventas_del_dia(self.nombre_usuario)
        todas_ventas = self._obtener_todas_ventas()


        # Accesos rápidos compactos
        def btn_acceso(icon, texto, descripcion, color, on_click):
            return ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Column([
                        ft.Icon(icon, size=24, color=ft.Colors.WHITE),
                        ft.Text(texto, size=14, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        ft.Text(descripcion, size=10, color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE)),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    on_click=on_click,
                    style=ft.ButtonStyle(
                        bgcolor=color,
                        color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.padding.symmetric(horizontal=15, vertical=12),
                    ),
                ),
                margin=ft.margin.all(5),
            )

        accesos = ft.Container(
            content=ft.Column([
                ft.Text("Accesos Rápidos", size=16, weight=ft.FontWeight.W_700, color=ft.Colors.INDIGO_900),
                ft.Container(height=8),
                ft.ResponsiveRow([
                    ft.Container(
                        content=btn_acceso(
                            ft.Icons.RECEIPT_LONG, 
                            "Todas las Ventas", 
                            f"{len(todas_ventas)} transacciones", 
                            ft.Colors.INDIGO_500,
                            lambda e: self.mostrar_todas_ventas(todas_ventas)
                        ),
                        col={"sm": 12, "md": 6}
                    ),
                    ft.Container(
                        content=btn_acceso(
                            ft.Icons.BAR_CHART, 
                            "Mi Resumen", 
                            f"${total_dia:.2f} total", 
                            ft.Colors.BLUE_500,
                            lambda e: self.mostrar_resumen(total_dia, len(todas_ventas))
                        ),
                        col={"sm": 12, "md": 6}
                    ),
                ], spacing=0),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
            margin=ft.margin.symmetric(horizontal=15, vertical=5),
        )

        # Resumen del día compacto
        resumen = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TODAY, size=20, color=ft.Colors.INDIGO_600),
                    ft.Text("Resumen del Día", size=16, weight=ft.FontWeight.W_700, color=ft.Colors.INDIGO_900),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=12),
                ft.ResponsiveRow([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{len(todas_ventas)}", size=20, weight=ft.FontWeight.W_800, color=ft.Colors.INDIGO_700),
                            ft.Text("Ventas", size=12, color=ft.Colors.GREY_600),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        padding=15,
                        bgcolor=ft.Colors.INDIGO_50,
                        border_radius=10,
                        col={"sm": 12, "md": 6}
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"${total_dia:.2f}", size=20, weight=ft.FontWeight.W_800, color=ft.Colors.BLUE_700),
                            ft.Text("Total", size=12, color=ft.Colors.GREY_600),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        padding=15,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=10,
                        col={"sm": 12, "md": 6}
                    ),
                ], spacing=8),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            ),
            margin=ft.margin.symmetric(horizontal=15, vertical=5),
        )

        # Contenido principal SIN SCROLL (todo visible)
        main_content = ft.Column([
            header,
            ft.Container(height=10),
            btn_ventas,
            ft.Container(height=8),
            accesos,
            ft.Container(height=8),
            resumen,
            ft.Container(height=10),
        ], spacing=0, expand=True)

        self.page.clean()
        self.page.add(main_content)

    def _obtener_todas_ventas(self):
        """Obtiene todas las ventas del día actual SOLO de la base de datos"""
        try:
            # Obtener todas las ventas del día (limite=0 significa todas)
            ventas = db.ultimas_ventas(self.nombre_usuario, 0)
            
            # Si hay ventas, mostrar información de debug
            
            return ventas if ventas is not None else []
            
        except Exception as e:
            print(f"ERROR obteniendo ventas: {e}")
            import traceback
            traceback.print_exc()
            return []

    # ---------- DIÁLOGO MEJORADO CON SCROLL ----------
    def mostrar_todas_ventas(self, ventas):
        """Muestra TODAS las ventas del día con scroll y mejor formato"""
        if not ventas:
            contenido = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RECEIPT_LONG, size=40, color=ft.Colors.GREY_400),
                    ft.Text("No hay ventas registradas hoy", size=14, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=30,
                alignment=ft.alignment.center
            )
        else:
            # Crear lista con SCROLL
            lista_ventas = ft.ListView(
                expand=True,
                spacing=6,
                padding=10,
                auto_scroll=False,
            )
            
            # Encabezado de la tabla
            lista_ventas.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("--:--", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700, width=60),
                        ft.Text("PRODUCTOS", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700, expand=True),
                        ft.Text("MONTO", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700, width=70),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=ft.Colors.INDIGO_50,
                    border_radius=6,
                )
            )
            
            # Agregar cada venta a la lista
            for i, v in enumerate(ventas):
                # v[0] = hora, v[1] = producto, v[2] = monto
                hora = v[0] if v[0] else "--:--"  # Muestra --:-- si no hay hora
                producto = v[1] if v[1] else "Varios productos"
                monto = v[2] if v[2] else 0.0
                
                lista_ventas.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(hora, size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700, width=60),
                            ft.Text(
                                producto, 
                                size=11, 
                                color=ft.Colors.GREY_800, 
                                expand=True, 
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            ),
                            ft.Text(f"${monto:.2f}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700, width=70),
                        ], vertical_alignment=ft.CrossAxisAlignment.START),
                        padding=ft.padding.symmetric(horizontal=10, vertical=10),
                        bgcolor=ft.Colors.GREY_50 if i % 2 == 0 else ft.Colors.WHITE,
                        border_radius=6,
                    )
                )

            # Contenedor con scroll automático
            contenido = ft.Container(
                content=lista_ventas,
                width=500,
                height=400,
            )

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.INDIGO_600),
                ft.Text(f"Todas las Ventas - {len(ventas)}", size=16, weight=ft.FontWeight.W_700),
            ]),
            content=contenido,
            actions=[
                ft.TextButton(
                    "Cerrar", 
                    on_click=lambda e: self.page.close(dlg),
                    style=ft.ButtonStyle(color=ft.Colors.INDIGO_600)
                )
            ],
            content_padding=0,
            actions_padding=15,
        )
        self.page.open(dlg)

    def mostrar_resumen(self, total, cantidad_ventas):
        """Muestra resumen completo del día"""
        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.BAR_CHART, color=ft.Colors.BLUE_600),
                ft.Text("Resumen del Día", size=16, weight=ft.FontWeight.W_700),
            ]),
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"{cantidad_ventas}", size=24, weight=ft.FontWeight.W_800, color=ft.Colors.INDIGO_700),
                                ft.Text("Ventas", size=12, color=ft.Colors.GREY_600),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                            padding=15,
                            bgcolor=ft.Colors.INDIGO_50,
                            border_radius=10,
                            expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"${total:.2f}", size=24, weight=ft.FontWeight.W_800, color=ft.Colors.BLUE_700),
                                ft.Text("Total", size=12, color=ft.Colors.GREY_600),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                            padding=15,
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=10,
                            expand=True
                        ),
                    ], spacing=10),
                ),
                ft.Divider(height=15),
                ft.Text(f"Empleado: {self.nombre_usuario}", size=12, color=ft.Colors.GREY_600),
                ft.Text(f"Fecha: {date.today().strftime('%d/%m/%Y')}", size=11, color=ft.Colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            actions=[
                ft.TextButton(
                    "Cerrar", 
                    on_click=lambda e: self.page.close(dlg),
                    style=ft.ButtonStyle(color=ft.Colors.BLUE_600)
                )
            ],
        )
        self.page.open(dlg)