# admin_panels/inventario_window.py - Gestor de Inventario Premium SIMPLIFICADO
import flet as ft
from flet import (
    Icons, Colors, FontWeight, MainAxisAlignment, CrossAxisAlignment,
    Animation, AnimationCurve
)
import sqlite3
import os
from datetime import datetime

# Configuración de base de datos
BASEDB = "./BASEDATOS/productos.db"
os.makedirs(os.path.dirname(BASEDB), exist_ok=True)

def get_conn() -> sqlite3.Connection:
    """Devuelve una conexión nueva para el hilo actual."""
    conn = sqlite3.connect(BASEDB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

class InventarioWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        self.termino_busqueda = ""
        self.filtro_estado = "Todos"
        self.orden_actual = "Nombre A-Z"
        
        # Variables para estadísticas
        self.total_productos = ft.Text("0", size=24, weight=FontWeight.W_700, color=Colors.INDIGO_900)
        self.bajo_stock = ft.Text("0", size=24, weight=FontWeight.W_700, color=Colors.INDIGO_900)
        self.sin_stock = ft.Text("0", size=24, weight=FontWeight.W_700, color=Colors.INDIGO_900)
        self.valor_total = ft.Text("$0.00", size=24, weight=FontWeight.W_700, color=Colors.INDIGO_900)
        
        # Controles de UI
        self.grid_inventario = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=320,
            child_aspect_ratio=0.8,
            spacing=15,
            run_spacing=15,
        )
        
        # Controles para filtros
        self.buscar_field = ft.TextField(
            label="Buscar productos...",
            prefix_icon=Icons.SEARCH,
            on_change=self._buscar_productos,
            border_color=Colors.INDIGO_200,
            focused_border_color=Colors.INDIGO_500
        )
        
        self.filtro_estado_dd = ft.Dropdown(
            label="Estado Stock",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Normal"),
                ft.dropdown.Option("Bajo Stock"),
                ft.dropdown.Option("Sin Stock")
            ],
            on_change=self._filtrar_por_estado,
            border_color=Colors.INDIGO_200
        )
        
        self.ordenar_dd = ft.Dropdown(
            label="Ordenar por",
            options=[
                ft.dropdown.Option("Nombre A-Z"),
                ft.dropdown.Option("Nombre Z-A"),
                ft.dropdown.Option("Stock Ascendente"),
                ft.dropdown.Option("Stock Descendente"),
                ft.dropdown.Option("Valor Ascendente"),
                ft.dropdown.Option("Valor Descendente")
            ],
            on_change=self._ordenar_inventario,
            border_color=Colors.INDIGO_200
        )
        
        self.cargar_inventario_completo()

    def cargar_inventario_completo(self):
        """Carga inventario y estadísticas"""
        self.cargar_inventario()
        self.actualizar_estadisticas()

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas en tiempo real"""
        try:
            with get_conn() as conn:
                # Total productos
                total = conn.execute("SELECT COUNT(*) as count FROM productos WHERE activo = 1").fetchone()["count"]
                
                # Productos bajo stock
                bajo_stock = conn.execute(
                    "SELECT COUNT(*) as count FROM productos WHERE stock_actual <= stock_minimo AND stock_actual > 0 AND activo = 1"
                ).fetchone()["count"]
                
                # Productos sin stock
                sin_stock = conn.execute(
                    "SELECT COUNT(*) as count FROM productos WHERE stock_actual = 0 AND activo = 1"
                ).fetchone()["count"]
                
                # Valor total del inventario
                valor_total = conn.execute(
                    "SELECT SUM(stock_actual * precio_compra) as total FROM productos WHERE activo = 1"
                ).fetchone()["total"] or 0
                
                # Actualizar los controles de texto
                self.total_productos.value = str(total)
                self.bajo_stock.value = str(bajo_stock)
                self.sin_stock.value = str(sin_stock)
                self.valor_total.value = f"${valor_total:,.2f}"
                
                # Forzar actualización
                self.page.update()
                
        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")

    def build_ui(self):
        """Construye la interfaz premium de inventario"""
        return ft.Container(
            content=ft.Column([
                self._build_header(),
                self._build_filtros(),
                ft.Container(
                    content=self.grid_inventario,
                    expand=True,
                    margin=ft.margin.only(top=10),
                    padding=10
                )
            ], expand=True, scroll=ft.ScrollMode.ADAPTIVE),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=["#F8FAFC", "#F1F5F9"]
            ),
            padding=10
        )

    def _build_header(self):
        """Header premium con estadísticas"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.IconButton(
                        icon=Icons.ARROW_BACK,
                        icon_size=24,
                        icon_color=Colors.INDIGO_600,
                        on_click=lambda _: self.admin_panel.setup_ui()
                    ),
                    ft.Text("Gestor de Inventario", 
                           size=28, weight=FontWeight.W_700,
                           color=Colors.INDIGO_900),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Actualizar",
                        icon=Icons.REFRESH,
                        on_click=self._actualizar_inventario_completo,
                        style=ft.ButtonStyle(
                            color=Colors.WHITE,
                            bgcolor=Colors.INDIGO_600,
                            padding=ft.padding.symmetric(horizontal=20, vertical=12)
                        )
                    )
                ]),
                
                # Tarjetas de estadísticas
                ft.Container(
                    content=ft.ResponsiveRow([
                        self._stat_card("Total Productos", self.total_productos, Icons.INVENTORY_2, Colors.BLUE_500),
                        self._stat_card("Bajo Stock", self.bajo_stock, Icons.WARNING, Colors.ORANGE_500),
                        self._stat_card("Sin Stock", self.sin_stock, Icons.ERROR, Colors.RED_500),
                        self._stat_card("Valor Total", self.valor_total, Icons.ATTACH_MONEY, Colors.GREEN_500),
                    ], spacing=10),
                    margin=ft.margin.only(top=15)
                )
            ]),
            bgcolor=Colors.WHITE,
            padding=20,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.1, Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

    def _stat_card(self, title, value_control, icon, color):
        """Crea una tarjeta de estadística con controles dinámicos"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=20),
                    value_control
                ]),
                ft.Text(title, size=14, color=Colors.GREY_600)
            ], spacing=8),
            padding=15,
            bgcolor=Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.08, Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            col={"sm": 6, "md": 3}
        )

    def _build_filtros(self):
        """Filtros para el inventario - SIMPLIFICADO"""
        return ft.Container(
            content=ft.ResponsiveRow([
                ft.Container(
                    content=self.buscar_field,
                    col={"sm": 12, "md": 5},
                    padding=5
                ),
                ft.Container(
                    content=self.filtro_estado_dd,
                    col={"sm": 12, "md": 3},
                    padding=5
                ),
                ft.Container(
                    content=self.ordenar_dd,
                    col={"sm": 12, "md": 3},
                    padding=5
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Limpiar",
                        icon=Icons.CLEAR_ALL,
                        on_click=self._limpiar_filtros,
                        style=ft.ButtonStyle(
                            bgcolor=Colors.INDIGO_100,
                            color=Colors.INDIGO_700
                        )
                    ),
                    col={"sm": 12, "md": 1},
                    padding=5
                )
            ]),
            bgcolor=Colors.WHITE,
            padding=15,
            margin=ft.margin.only(top=10),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.05, Colors.BLACK)
            )
        )

    def _crear_tarjeta_inventario(self, producto):
        """Crea una tarjeta premium para cada producto en inventario"""
        if producto["stock_actual"] == 0:
            stock_color = Colors.RED_500
            estado_texto = "SIN STOCK"
            estado_color = Colors.RED_500
        elif producto["stock_actual"] <= producto["stock_minimo"]:
            stock_color = Colors.ORANGE_500
            estado_texto = "BAJO STOCK"
            estado_color = Colors.ORANGE_500
        else:
            stock_color = Colors.GREEN_500
            estado_texto = "NORMAL"
            estado_color = Colors.GREEN_500
        
        valor_total = producto["stock_actual"] * producto["precio_compra"]

        return ft.Container(
            content=ft.Column([
                # Header con nombre y estado
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            producto["nombre"],
                            size=15,
                            weight=FontWeight.W_600,
                            color=Colors.INDIGO_900,
                            text_align="center"
                        ),
                        ft.Container(
                            content=ft.Text(
                                estado_texto,
                                size=10,
                                color=Colors.WHITE,
                                weight=FontWeight.BOLD
                            ),
                            bgcolor=estado_color,
                            padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            border_radius=12,
                            alignment=ft.alignment.center
                        )
                    ], spacing=6),
                    margin=ft.margin.only(bottom=8)
                ),
                
                # Información de stock
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Stock Actual:", size=12, color=Colors.GREY_700, expand=True),
                            ft.Text(str(producto["stock_actual"]), 
                                   size=14, weight=FontWeight.W_700, color=stock_color)
                        ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Row([
                            ft.Text("Mínimo:", size=11, color=Colors.GREY_600, expand=True),
                            ft.Text(str(producto["stock_minimo"]), size=11, color=Colors.GREY_600)
                        ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Row([
                            ft.Text("Máximo:", size=11, color=Colors.GREY_600, expand=True),
                            ft.Text(str(producto["stock_maximo"]), size=11, color=Colors.GREY_600)
                        ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                        
                        ft.Divider(height=8, color=Colors.GREY_300),
                        
                        ft.Row([
                            ft.Text("Valor Total:", size=12, color=Colors.GREY_700, expand=True),
                            ft.Text(f"${valor_total:,.2f}", 
                                   size=12, weight=FontWeight.W_600, color=Colors.INDIGO_700)
                        ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=4),
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Controles rápidos de stock
                ft.Container(
                    content=ft.Column([
                        ft.Text("Ajuste Rápido:", size=11, color=Colors.GREY_600, weight=FontWeight.W_500),
                        ft.Row([
                            ft.IconButton(
                                icon=Icons.ADD,
                                icon_size=16,
                                icon_color=Colors.GREEN_600,
                                on_click=lambda _, p=producto: self._agregar_stock(p, 1),
                                tooltip="+1 Unidad",
                                style=ft.ButtonStyle(
                                    bgcolor=Colors.GREEN_50,
                                    padding=ft.padding.all(4)
                                )
                            ),
                            ft.IconButton(
                                icon=Icons.ADD,
                                icon_size=16,
                                icon_color=Colors.GREEN_600,
                                on_click=lambda _, p=producto: self._agregar_stock(p, 5),
                                tooltip="+5 Unidades",
                                style=ft.ButtonStyle(
                                    bgcolor=Colors.GREEN_50,
                                    padding=ft.padding.all(4)
                                )
                            ),
                            ft.IconButton(
                                icon=Icons.REMOVE,
                                icon_size=16,
                                icon_color=Colors.RED_600,
                                on_click=lambda _, p=producto: self._quitar_stock(p, 1),
                                tooltip="-1 Unidad",
                                style=ft.ButtonStyle(
                                    bgcolor=Colors.RED_50,
                                    padding=ft.padding.all(4)
                                )
                            ),
                            ft.IconButton(
                                icon=Icons.REMOVE,
                                icon_size=16,
                                icon_color=Colors.RED_600,
                                on_click=lambda _, p=producto: self._quitar_stock(p, 5),
                                tooltip="-5 Unidades",
                                style=ft.ButtonStyle(
                                    bgcolor=Colors.RED_50,
                                    padding=ft.padding.all(4)
                                )
                            ),
                        ], alignment=MainAxisAlignment.SPACE_EVENLY)
                    ], spacing=6),
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Botones de acción avanzada
                ft.Row([
                    ft.ElevatedButton(
                        "Ajuste Fino",
                        icon=Icons.EDIT,
                        on_click=lambda _, p=producto: self._abrir_ajuste_fino(p),
                        style=ft.ButtonStyle(
                            color=Colors.BLUE_700,
                            bgcolor=Colors.BLUE_50,
                            padding=ft.padding.symmetric(horizontal=10, vertical=6)
                        )
                    ),
                ], alignment=MainAxisAlignment.CENTER)
            ], spacing=10, horizontal_alignment=CrossAxisAlignment.CENTER),
            padding=15,
            bgcolor=Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.08, Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
            width=300,
            height=280,
            animate=Animation(300, AnimationCurve.EASE_OUT),
            on_hover=lambda e: self._animar_tarjeta(e)
        )

    def _animar_tarjeta(self, e):
        """Animación hover para las tarjetas"""
        e.control.scale = 1.02 if e.data == "true" else 1.0
        e.control.update()

    def cargar_inventario(self, filtro=None, estado=None, orden=None):
        """Carga inventario desde la base de datos con LIMIT para evitar lag"""
        try:
            # Actualizar variables internas si se proporcionan nuevos valores
            if filtro is not None:
                self.termino_busqueda = filtro
                self.buscar_field.value = filtro
            if estado is not None:
                self.filtro_estado = estado
                self.filtro_estado_dd.value = estado
            if orden is not None:
                self.orden_actual = orden
                self.ordenar_dd.value = orden

            with get_conn() as conn:
                query = """
                    SELECT p.*
                    FROM productos p
                    WHERE p.activo = 1
                """
                params = []
                
                if self.termino_busqueda:
                    query += " AND (p.nombre LIKE ? OR p.descripcion LIKE ?)"
                    params.extend([f"%{self.termino_busqueda}%", f"%{self.termino_busqueda}%"])
                
                if self.filtro_estado and self.filtro_estado != "Todos":
                    if self.filtro_estado == "Bajo Stock":
                        query += " AND p.stock_actual <= p.stock_minimo AND p.stock_actual > 0"
                    elif self.filtro_estado == "Sin Stock":
                        query += " AND p.stock_actual = 0"
                    elif self.filtro_estado == "Normal":
                        query += " AND p.stock_actual > p.stock_minimo"
                
                # ORDENAMIENTO
                if self.orden_actual == "Nombre A-Z":
                    query += " ORDER BY p.nombre ASC"
                elif self.orden_actual == "Nombre Z-A":
                    query += " ORDER BY p.nombre DESC"
                elif self.orden_actual == "Stock Ascendente":
                    query += " ORDER BY p.stock_actual ASC"
                elif self.orden_actual == "Stock Descendente":
                    query += " ORDER BY p.stock_actual DESC"
                elif self.orden_actual == "Valor Ascendente":
                    query += " ORDER BY (p.stock_actual * p.precio_compra) ASC"
                elif self.orden_actual == "Valor Descendente":
                    query += " ORDER BY (p.stock_actual * p.precio_compra) DESC"
                else:
                    query += " ORDER BY p.nombre ASC"

                # ✅ LIMITAR a máximo 100 productos
                query += " LIMIT 100"

                productos = conn.execute(query, params).fetchall()
                
                # Limpiar y actualizar grid
                self.grid_inventario.controls.clear()
                for producto in productos:
                    self.grid_inventario.controls.append(
                        self._crear_tarjeta_inventario(dict(producto))
                    )
                
                self.page.update()
                
        except Exception as e:
            print(f"Error cargando inventario: {e}")


    # ==================== FUNCIONES DE STOCK ====================

    def _agregar_stock(self, producto, cantidad):
        """Agrega stock automáticamente"""
        try:
            with get_conn() as conn:
                nuevo_stock = producto["stock_actual"] + cantidad
                conn.execute(
                    "UPDATE productos SET stock_actual = ?, actualizado_en = ? WHERE id = ?",
                    [nuevo_stock, datetime.now().isoformat(), producto["id"]]
                )
                conn.commit()
            
            self._mostrar_mensaje(f"+{cantidad} unidades agregadas a {producto['nombre']}",Colors.GREEN)
            self.cargar_inventario_completo()
            
        except Exception as e:
            self._mostrar_mensaje(f"Error: {str(e)}", Colors.RED)

    def _quitar_stock(self, producto, cantidad):
        """Quita stock automáticamente"""
        try:
            nuevo_stock = max(0, producto["stock_actual"] - cantidad)
            with get_conn() as conn:
                conn.execute(
                    "UPDATE productos SET stock_actual = ?, actualizado_en = ? WHERE id = ?",
                    [nuevo_stock, datetime.now().isoformat(), producto["id"]]
                )
                conn.commit()
            
            self._mostrar_mensaje(f"-{cantidad} unidades quitadas de {producto['nombre']}", Colors.ORANGE)
            self.cargar_inventario_completo()
            
        except Exception as e:
            self._mostrar_mensaje(f"Error: {str(e)}", Colors.RED)

    def _abrir_ajuste_fino(self, producto):
        """Abre diálogo para ajuste fino de stock"""
        stock_actual = ft.TextField(
            label="Nuevo Stock",
            value=str(producto["stock_actual"]),
            keyboard_type=ft.KeyboardType.NUMBER,
            width=200
        )
        
        def guardar_ajuste(_):
            try:
                nuevo_stock = int(stock_actual.value)
                with get_conn() as conn:
                    conn.execute(
                        "UPDATE productos SET stock_actual = ?, actualizado_en = ? WHERE id = ?",
                        [nuevo_stock, datetime.now().isoformat(), producto["id"]]
                    )
                    conn.commit()
                
                self._mostrar_mensaje(f"Stock de {producto['nombre']} actualizado a {nuevo_stock}", Colors.GREEN)
                self.cargar_inventario_completo()
                self.page.close(dialog)
                
            except ValueError:
                self._mostrar_mensaje("Ingrese un número válido", Colors.RED)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Ajuste Fino: {producto['nombre']}"),
            content=ft.Column([
                ft.Text(f"Stock actual: {producto['stock_actual']}"),
                ft.Text(f"Mínimo: {producto['stock_minimo']} | Máximo: {producto['stock_maximo']}"),
                stock_actual
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dialog)),
                ft.TextButton("Guardar", on_click=guardar_ajuste),
            ]
        )
        self.page.open(dialog)

    # ==================== FUNCIONES DE FILTROS ====================

    def _actualizar_inventario_completo(self, e=None):
        """Actualiza completamente el inventario"""
        self.cargar_inventario_completo()
        self._mostrar_mensaje("Inventario actualizado", Colors.GREEN)

    def _limpiar_filtros(self, e):
        """Limpia todos los filtros"""
        self.termino_busqueda = ""
        self.filtro_estado = "Todos"
        self.orden_actual = "Nombre A-Z"
        
        # Limpiar los controles visuales
        self.buscar_field.value = ""
        self.filtro_estado_dd.value = "Todos"
        self.ordenar_dd.value = "Nombre A-Z"
        
        self.cargar_inventario_completo()
        self._mostrar_mensaje("Filtros limpiados", Colors.INDIGO)

    def _buscar_productos(self, e):
        """Busca productos"""
        self.termino_busqueda = e.control.value
        self.cargar_inventario()

    def _filtrar_por_estado(self, e):
        """Filtra por estado de stock"""
        self.filtro_estado = e.control.value
        self.cargar_inventario()

    def _ordenar_inventario(self, e):
        """Ordena el inventario"""
        orden = e.control.value
        self.orden_actual = orden
        
        # Mensajes explicativos para cada tipo de ordenamiento
        mensajes = {
            "Nombre A-Z": "Ordenado por nombre (A a Z)",
            "Nombre Z-A": "Ordenado por nombre (Z a A)", 
            "Stock Ascendente": "Ordenado por stock (menor a mayor)",
            "Stock Descendente": "Ordenado por stock (mayor a menor)",
            "Valor Ascendente": "Ordenado por valor (menor a mayor)",
            "Valor Descendente": "Ordenado por valor (mayor a menor)"
        }
        
        if orden in mensajes:
            self._mostrar_mensaje(mensajes[orden], Colors.PURPLE)
        
        self.cargar_inventario()

    def _mostrar_mensaje(self, mensaje ,color):
        snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.CHECK_CIRCLE, color=color),
                ft.Text(mensaje , color="green")
            ]),
            bgcolor=Colors.GREEN_50,
        )
        self.page.open(snack_bar)