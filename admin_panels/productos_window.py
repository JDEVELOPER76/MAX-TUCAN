# admin_panels/productos_window.py - Administrador Premium de Productos
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

def init_db():
    """Inicializa la base de datos con tablas premium"""
    with get_conn() as conn:
        # Tabla de productos premium (sin categorías)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                
                -- Precios y tipos de venta
                precio_compra REAL DEFAULT 0,
                precio_venta_normal REAL DEFAULT 0,
                precio_venta_mayoreo REAL DEFAULT 0,
                precio_venta_promocion REAL DEFAULT 0,
                
                -- Stocks
                stock_actual INTEGER DEFAULT 0,
                stock_minimo INTEGER DEFAULT 0,
                stock_maximo INTEGER DEFAULT 0,
                
                -- Configuración de tipos de venta
                venta_normal_activa INTEGER DEFAULT 1,
                venta_mayoreo_activa INTEGER DEFAULT 0,
                venta_promocion_activa INTEGER DEFAULT 0,
                minimo_mayoreo INTEGER DEFAULT 10,
                fecha_inicio_promocion TEXT,
                fecha_fin_promocion TEXT,
                
                -- IVA personalizado
                iva_porcentaje REAL DEFAULT 16.0,
                
                -- Imágenes y multimedia
                imagen_path TEXT,
                especificaciones_json TEXT,
                
                -- Estado
                activo INTEGER DEFAULT 1,
                destacado INTEGER DEFAULT 0,
                creado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de historial de precios
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historial_precios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                tipo_precio TEXT,
                precio_anterior REAL,
                precio_nuevo REAL,
                fecha_cambio TEXT DEFAULT CURRENT_TIMESTAMP,
                usuario TEXT DEFAULT 'Sistema',
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        
        conn.commit()

class ProductosWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        self.filtro_activo = "Todos"
        self.termino_busqueda = ""
        init_db()
        
        # Controles de UI
        self.grid_productos = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=350,
            child_aspect_ratio=0.7,
            spacing=20,
            run_spacing=20,
            on_scroll=self._detectar_scroll
        )

        # Control de carga progresiva
        self.productos_offset = 0
        self.productos_cargando = False
        self.productos_finalizados = False

        self.cargar_productos()
        self._cargar_estadisticas()

    def _cargar_estadisticas(self):
        """Carga estadísticas reales desde la base de datos"""
        try:
            with get_conn() as conn:
                # Total productos activos
                total = conn.execute("SELECT COUNT(*) as count FROM productos WHERE activo = 1").fetchone()["count"]
                
                # Productos bajo stock
                bajo_stock = conn.execute(
                    "SELECT COUNT(*) as count FROM productos WHERE stock_actual <= stock_minimo AND activo = 1"
                ).fetchone()["count"]
                
                # Productos destacados
                destacados = conn.execute(
                    "SELECT COUNT(*) as count FROM productos WHERE destacado = 1 AND activo = 1"
                ).fetchone()["count"]
                
                # Nuevos hoy
                hoy = datetime.now().strftime("%Y-%m-%d")
                nuevos_hoy = conn.execute(
                    "SELECT COUNT(*) as count FROM productos WHERE DATE(creado_en) = ? AND activo = 1",
                    [hoy]
                ).fetchone()["count"]
                
                self.estadisticas = {
                    "total": total,
                    "bajo_stock": bajo_stock,
                    "destacados": destacados,
                    "nuevos_hoy": nuevos_hoy
                }
                
        except Exception as e:
            print(f"Error cargando estadísticas: {e}")
            self.estadisticas = {
                "total": 0,
                "bajo_stock": 0,
                "destacados": 0,
                "nuevos_hoy": 0
            }

    def build_ui(self):
        """Construye la interfaz premium de productos"""
        return ft.Container(
            content=ft.Column([
                self._build_header(),
                self._build_filtros(),
                ft.Container(
                    content=self.grid_productos,
                    expand=True,
                    margin=ft.margin.only(top=20),
                    padding=20
                )
            ], expand=True),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=["#F8FAFC", "#F1F5F9"]
            )
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
                    ft.Text("Gestor de Productos", 
                           size=28, weight=FontWeight.W_700,
                           color=Colors.INDIGO_900),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Nuevo Producto",
                        icon=Icons.ADD_CIRCLE_OUTLINED,
                        on_click=self._abrir_formulario_producto,
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
                        self._stat_card("Total Productos", str(self.estadisticas["total"]), Icons.INVENTORY_2, Colors.BLUE_500),
                        self._stat_card("Bajo Stock", str(self.estadisticas["bajo_stock"]), Icons.WARNING, Colors.ORANGE_500),
                        self._stat_card("Destacados", str(self.estadisticas["destacados"]), Icons.STAR, Colors.AMBER_500),
                        self._stat_card("Nuevos Hoy", str(self.estadisticas["nuevos_hoy"]), Icons.NEW_RELEASES, Colors.GREEN_500),
                    ], spacing=15),
                    margin=ft.margin.only(top=20)
                )
            ]),
            bgcolor=Colors.WHITE,
            padding=25,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.1, Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

    def _stat_card(self, title, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=color, size=20),
                    ft.Text(value, size=24, weight=FontWeight.W_700, color=Colors.INDIGO_900)
                ]),
                ft.Text(title, size=14, color=Colors.GREY_600)
            ], spacing=8),
            padding=20,
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
        """Filtros y búsqueda premium (sin categoría)"""
        return ft.Container(
            content=ft.ResponsiveRow([
                ft.Container(
                    content=ft.TextField(
                        label="Buscar productos...",
                        prefix_icon=Icons.SEARCH,
                        on_change=self._buscar_productos,
                        border_color=Colors.INDIGO_200,
                        focused_border_color=Colors.INDIGO_500
                    ),
                    col={"sm": 12, "md": 6},
                    padding=5
                ),
                ft.Container(
                    content=ft.Dropdown(
                        label="Tipo de Venta",
                        options=[
                            ft.dropdown.Option("Todos"),
                            ft.dropdown.Option("Normal"),
                            ft.dropdown.Option("Mayoreo"),
                            ft.dropdown.Option("Promoción")
                        ],
                        on_change=self._filtrar_por_tipo_venta,
                        border_color=Colors.INDIGO_200
                    ),
                    col={"sm": 12, "md": 4},
                    padding=5
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Filtrar",
                        icon=Icons.FILTER_ALT,
                        on_click=self._aplicar_filtros,
                        style=ft.ButtonStyle(
                            bgcolor=Colors.INDIGO_100,
                            color=Colors.INDIGO_700
                        )
                    ),
                    col={"sm": 12, "md": 2},
                    padding=5
                )
            ]),
            bgcolor=Colors.WHITE,
            padding=20,
            margin=ft.margin.only(top=10),
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.05, Colors.BLACK)
            )
        )

    def _crear_tarjeta_producto(self, producto):
        """Crea una tarjeta premium para cada producto"""
        # Determinar color de stock
        stock_color = (
            Colors.RED_500 if producto["stock_actual"] <= producto["stock_minimo"] else
            Colors.GREEN_500 if producto["stock_actual"] > producto["stock_minimo"] * 2 else
            Colors.ORANGE_500
        )
        
        # Badges de tipos de venta activos
        badges = []
        if producto["venta_normal_activa"]:
            badges.append(ft.Container(
                content=ft.Text("NORMAL", size=11, color=Colors.WHITE, weight=FontWeight.BOLD),
                bgcolor=Colors.BLUE_600,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=15,
                margin=ft.margin.only(bottom=2)
            ))
        if producto["venta_mayoreo_activa"]:
            badges.append(ft.Container(
                content=ft.Text("MAYOREO", size=11, color=Colors.WHITE, weight=FontWeight.BOLD),
                bgcolor=Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=15,
                margin=ft.margin.only(bottom=2)
            ))
        if producto["venta_promocion_activa"]:
            badges.append(ft.Container(
                content=ft.Text("PROMO", size=11, color=Colors.WHITE, weight=FontWeight.BOLD),
                bgcolor=Colors.RED_600,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=15,
                margin=ft.margin.only(bottom=2)
            ))

        return ft.Container(
            content=ft.Column([
                # Imagen del producto
                ft.Container(
                    content=ft.Icon(
                        Icons.SHOPPING_BAG_OUTLINED,
                        size=50,
                        color=Colors.INDIGO_400
                    ) if not producto["imagen_path"] else ft.Image(
                        src=producto["imagen_path"],
                        fit=ft.ImageFit.COVER
                    ),
                    width=140,
                    height=140,
                    alignment=ft.alignment.center,
                    bgcolor=Colors.INDIGO_50,
                    border_radius=12,
                    margin=ft.margin.only(bottom=12)
                ),
                
                # Nombre y descripción
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            producto["nombre"],
                            size=16,
                            weight=FontWeight.W_600,
                            color=Colors.INDIGO_900,
                            text_align="center"
                        ),
                        ft.Text(
                            producto["descripcion"][:60] + "..." if producto["descripcion"] and len(producto["descripcion"]) > 60 else producto["descripcion"] or "Sin descripción",
                            size=12,
                            color=Colors.GREY_600,
                            text_align="center"
                        ),
                    ], spacing=6),
                    margin=ft.margin.only(bottom=8)
                ),
                
                # Badges de tipos de venta
                ft.Container(
                    content=ft.Column(
                        badges, 
                        spacing=4,
                        horizontal_alignment=CrossAxisAlignment.CENTER
                    ) if badges else ft.Container(),
                    margin=ft.margin.only(bottom=10)
                ),
                
                # Precios
                ft.Container(
                    content=ft.Column([
                        # Precio normal siempre visible
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Normal:", size=13, color=Colors.GREY_700, weight=FontWeight.W_500),
                                ft.Text(f"${producto['precio_venta_normal']:,.2f}", 
                                       size=14, weight=FontWeight.W_700, color=Colors.INDIGO_700)
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(vertical=2)
                        ),
                        
                        # Precio mayoreo si está activo
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Mayoreo:", size=12, color=Colors.GREY_600, weight=FontWeight.W_500),
                                ft.Text(f"${producto['precio_venta_mayoreo']:,.2f}", 
                                       size=13, weight=FontWeight.W_600, color=Colors.GREEN_600)
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(vertical=2),
                            visible=producto["venta_mayoreo_activa"]
                        ) if producto["venta_mayoreo_activa"] else ft.Container(),
                        
                        # Precio promoción si está activo
                        ft.Container(
                            content=ft.Row([
                                ft.Text("Promoción:", size=12, color=Colors.GREY_600, weight=FontWeight.W_500),
                                ft.Text(f"${producto['precio_venta_promocion']:,.2f}", 
                                       size=13, weight=FontWeight.W_600, color=Colors.RED_600)
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(vertical=2),
                            visible=producto["venta_promocion_activa"]
                        ) if producto["venta_promocion_activa"] else ft.Container(),

                        # IVA personalizado
                        ft.Container(
                            content=ft.Row([
                                ft.Text("IVA:", size=12, color=Colors.GREY_600, weight=FontWeight.W_500),
                                ft.Text(f"{producto['iva_porcentaje']}%", 
                                       size=12, weight=FontWeight.W_600, color=Colors.PURPLE_600)
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(vertical=2),
                        ),
                    ], spacing=2),
                    margin=ft.margin.only(bottom=12)
                ),
                
                # Stock y botones
                ft.Row([
                    # Información de stock
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Text(
                                    f"Stock: {producto['stock_actual']}",
                                    size=12,
                                    color=Colors.WHITE,
                                    weight=FontWeight.BOLD
                                ),
                                bgcolor=stock_color,
                                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                border_radius=20
                            ),
                            ft.Text(
                                f"Mín: {producto['stock_minimo']}",
                                size=10,
                                color=Colors.GREY_500
                            ) if producto["stock_actual"] <= producto["stock_minimo"] else ft.Container()
                        ], spacing=4, horizontal_alignment=CrossAxisAlignment.CENTER),
                        expand=True
                    ),
                    
                    # Menú de tres puntos para acciones
                    ft.PopupMenuButton(
                        icon=ft.Icon(Icons.MORE_VERT, color=Colors.GREY_600, size=20),
                        items=[
                            ft.PopupMenuItem(
                                icon=ft.Icon(Icons.EDIT, color=Colors.BLUE_600),
                                text="Editar",
                                on_click=lambda _, p=producto: self._editar_producto(p)
                            ),
                            ft.PopupMenuItem(
                                icon=ft.Icon(Icons.VISIBILITY, color=Colors.GREEN_600),
                                text="Ver detalles",
                                on_click=lambda _, p=producto: self._ver_detalles(p)
                            ),
                            ft.PopupMenuItem(
                                icon=ft.Icon(Icons.DELETE, color=Colors.RED_600),
                                text="Eliminar",
                                on_click=lambda _, p=producto: self._eliminar_producto(p)
                            ),
                        ]
                    )
                ], alignment=MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=8, horizontal_alignment=CrossAxisAlignment.CENTER),
            padding=20,
            bgcolor=Colors.WHITE,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.1, Colors.BLACK),
                offset=ft.Offset(0, 3)
            ),
            width=320,
            height=500,
            animate=Animation(300, AnimationCurve.EASE_OUT),
            on_hover=lambda e: self._animar_tarjeta(e)
        )

    def _animar_tarjeta(self, e):
        """Animación hover para las tarjetas"""
        e.control.scale = 1.05 if e.data == "true" else 1.0
        e.control.update()

    def cargar_productos(self, filtro=None, tipo_venta=None):
        """Reinicia la lista y carga la primera tanda de productos"""
        self.productos_offset = 0
        self.productos_finalizados = False
        self.termino_busqueda = filtro or ""
        self.filtro_activo = tipo_venta or "Todos"
        self.grid_productos.controls.clear()
        self.page.update()
        self._cargar_mas_productos()

    def _cargar_mas_productos(self):
        """Carga productos de forma incremental (scroll infinito)"""
        if self.productos_cargando or self.productos_finalizados:
            return

        self.productos_cargando = True
        
        # Mostrar indicador de carga
        if self.productos_offset > 0:
            self.grid_productos.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.ProgressRing(width=30, height=30, color=Colors.INDIGO_600),
                        ft.Text("Cargando más productos...", size=12, color=Colors.GREY_600)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            self.page.update()

        try:
            with get_conn() as conn:
                query = """
                    SELECT p.*
                    FROM productos p
                    WHERE p.activo = 1
                """
                params = []

                if self.termino_busqueda:
                    query += " AND (p.nombre LIKE ? OR p.descripcion LIKE ? OR p.codigo_barras LIKE ?)"
                    params.extend([f"%{self.termino_busqueda}%", f"%{self.termino_busqueda}%", f"%{self.termino_busqueda}%"])

                if self.filtro_activo and self.filtro_activo != "Todos":
                    if self.filtro_activo == "Normal":
                        query += " AND p.venta_normal_activa = 1"
                    elif self.filtro_activo == "Mayoreo":
                        query += " AND p.venta_mayoreo_activa = 1"
                    elif self.filtro_activo == "Promoción":
                        query += " AND p.venta_promocion_activa = 1"

                query += " ORDER BY p.destacado DESC, p.creado_en DESC LIMIT 12 OFFSET ?"
                params.append(self.productos_offset)

                productos = conn.execute(query, params).fetchall()

            # Quitar loader si existe
            if (self.productos_offset > 0 and 
                self.grid_productos.controls and 
                isinstance(self.grid_productos.controls[-1], ft.Container) and
                len(self.grid_productos.controls[-1].content.controls) > 0 and
                isinstance(self.grid_productos.controls[-1].content.controls[0], ft.ProgressRing)):
                self.grid_productos.controls.pop()

            if not productos:
                self.productos_finalizados = True
                if self.productos_offset == 0:
                    self.grid_productos.controls.append(
                        ft.Container(
                            content=ft.Text("No se encontraron productos", size=16, color=Colors.GREY_600),
                            alignment=ft.alignment.center,
                            padding=40
                        )
                    )
                else:
                    # Mensaje de fin de productos
                    self.grid_productos.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(Icons.CHECK_CIRCLE, color=Colors.GREEN_500, size=30),
                                ft.Text("¡Has llegado al final!", size=14, color=Colors.GREY_600),
                                ft.Text(f"Se cargaron {self.productos_offset} productos", size=12, color=Colors.GREY_500)
                            ], horizontal_alignment=CrossAxisAlignment.CENTER, spacing=8),
                            alignment=ft.alignment.center,
                            padding=30
                        )
                    )
            else:
                for producto in productos:
                    self.grid_productos.controls.append(self._crear_tarjeta_producto(dict(producto)))

                self.productos_offset += len(productos)
                if len(productos) < 12:
                    self.productos_finalizados = True

            self.page.update()

        except Exception as e:
            print(f"Error cargando productos: {e}")
            # Quitar loader si existe
            if (self.productos_offset > 0 and 
                self.grid_productos.controls and 
                isinstance(self.grid_productos.controls[-1], ft.Container) and
                len(self.grid_productos.controls[-1].content.controls) > 0 and
                isinstance(self.grid_productos.controls[-1].content.controls[0], ft.ProgressRing)):
                self.grid_productos.controls.pop()
                
            self.grid_productos.controls.append(
                ft.Container(
                    content=ft.Text(f"Error al cargar productos", color=Colors.RED_600),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            self.page.update()

        self.productos_cargando = False

    def _detectar_scroll(self, e):
        """Detecta cuando se llega al final del scroll para cargar más"""
        if e.pixels >= e.max_scroll_extent - 100 and not self.productos_cargando:
            self._cargar_mas_productos()

    def _buscar_productos(self, e):
        self.termino_busqueda = e.control.value
        self.cargar_productos(self.termino_busqueda)

    def _filtrar_por_tipo_venta(self, e):
        self.cargar_productos(self.termino_busqueda, e.control.value)

    def _aplicar_filtros(self, e):
        self.cargar_productos(self.termino_busqueda)

    def _abrir_formulario_producto(self, e):
        """Abre el formulario para nuevo producto"""
        formulario = FormularioProducto(self.page, self)
        self.page.open(formulario.dialog)

    def _editar_producto(self, producto):
        """Abre el formulario para editar producto"""
        formulario = FormularioProducto(self.page, self, producto)
        self.page.open(formulario.dialog)

    def _eliminar_producto(self, producto):
        """Elimina un producto con confirmación"""
        def confirmar_eliminacion(e):
            try:
                with get_conn() as conn:
                    conn.execute("UPDATE productos SET activo = 0 WHERE id = ?", [producto["id"]])
                    conn.commit()
                self.cargar_productos()
                self._cargar_estadisticas()
                self.page.close(dialog)
                self._mostrar_mensaje("Producto eliminado")
            except Exception as ex:
                self._mostrar_mensaje(f"Error: {ex}")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Eliminar el producto '{producto['nombre']}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.TextButton("Eliminar", on_click=confirmar_eliminacion),
            ]
        )
        self.page.open(dialog)

    def _ver_detalles(self, producto):
        """Muestra detalles completos del producto"""
        detalles = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Detalles: {producto['nombre']}"),
            content=ft.Column([
                ft.Text(f"Código: {producto['codigo_barras'] or 'N/A'}"),
                ft.Text(f"Descripción: {producto['descripcion'] or 'N/A'}"),
                ft.Text(f"Stock: {producto['stock_actual']} (Mín: {producto['stock_minimo']}, Máx: {producto['stock_maximo']})"),
                ft.Text(f"Precio Compra: ${producto['precio_compra']:,.2f}"),
                ft.Text(f"Precio Venta Normal: ${producto['precio_venta_normal']:,.2f}"),
                ft.Text(f"Precio Mayoreo: ${producto['precio_venta_mayoreo']:,.2f}"),
                ft.Text(f"Precio Promoción: ${producto['precio_venta_promocion']:,.2f}"),
                ft.Text(f"IVA: {producto['iva_porcentaje']}%"),
            ], tight=True),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.close(detalles))]
        )
        self.page.open(detalles)

    def _mostrar_mensaje(self, mensaje):
        snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.CHECK_CIRCLE, color=Colors.WHITE),
                ft.Text(mensaje, color="black")
            ]),
            bgcolor=Colors.GREEN_50,
        )
        self.page.open(snack_bar)

# ... (La clase FormularioProducto se mantiene igual)
class FormularioProducto:
    def __init__(self, page: ft.Page, win, producto=None):
        self.page = page
        self.win = win
        self.producto = producto
        self.es_edicion = producto is not None
        
        # Campos del formulario
        self.codigo_barras = ft.TextField(label="Código de Barras", expand=True)
        self.nombre = ft.TextField(label="Nombre del Producto*", expand=True)
        self.descripcion = ft.TextField(label="Descripción", multiline=True, expand=True)
        
        # Precios
        self.precio_compra = ft.TextField(label="Precio Compra*", value="0", expand=True)
        self.precio_normal = ft.TextField(label="Precio Venta Normal*", value="0", expand=True)
        self.precio_mayoreo = ft.TextField(label="Precio Mayoreo", value="0", expand=True)
        self.precio_promocion = ft.TextField(label="Precio Promoción", value="0", expand=True)
        
        # Stocks
        self.stock_actual = ft.TextField(label="Stock Actual*", value="0", expand=True)
        self.stock_minimo = ft.TextField(label="Stock Mínimo", value="5", expand=True)
        self.stock_maximo = ft.TextField(label="Stock Máximo", value="100", expand=True)
        
        # IVA personalizado
        self.iva_porcentaje = ft.TextField(label="IVA %", value="16.0", expand=True)
        
        # Switches para tipos de venta
        self.switch_normal = ft.Switch(label="Venta Normal", value=True)
        self.switch_mayoreo = ft.Switch(label="Venta por Mayoreo", value=False)
        self.switch_promocion = ft.Switch(label="Venta en Promoción", value=False)
        self.minimo_mayoreo = ft.TextField(label="Mínimo para Mayoreo", value="10", expand=True)
        
        if self.es_edicion:
            self._cargar_datos_existentes()
            
        self._construir_dialog()

    def _cargar_datos_existentes(self):
        """Carga los datos del producto en edición"""
        if self.producto:
            self.codigo_barras.value = self.producto.get("codigo_barras") or ""
            self.nombre.value = self.producto.get("nombre") or ""
            self.descripcion.value = self.producto.get("descripcion") or ""
            
            # Precios
            self.precio_compra.value = str(self.producto.get("precio_compra") or 0)
            self.precio_normal.value = str(self.producto.get("precio_venta_normal") or 0)
            self.precio_mayoreo.value = str(self.producto.get("precio_venta_mayoreo") or 0)
            self.precio_promocion.value = str(self.producto.get("precio_venta_promocion") or 0)
            self.iva_porcentaje.value = str(self.producto.get("iva_porcentaje") or 16.0)
            
            # Stocks
            self.stock_actual.value = str(self.producto.get("stock_actual") or 0)
            self.stock_minimo.value = str(self.producto.get("stock_minimo") or 5)
            self.stock_maximo.value = str(self.producto.get("stock_maximo") or 100)
            
            # Switches
            self.switch_normal.value = bool(self.producto.get("venta_normal_activa", True))
            self.switch_mayoreo.value = bool(self.producto.get("venta_mayoreo_activa", False))
            self.switch_promocion.value = bool(self.producto.get("venta_promocion_activa", False))
            self.minimo_mayoreo.value = str(self.producto.get("minimo_mayoreo") or 10)

    def _construir_dialog(self):
        """Construye el diálogo del formulario"""
        content = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Editar Producto" if self.es_edicion else "Nuevo Producto",
                    size=20,
                    weight=FontWeight.BOLD,
                    color=Colors.INDIGO_900
                ),
                
                # Información básica
                ft.Text("Información Básica", size=16, weight=FontWeight.W_600, color=Colors.INDIGO_700),
                ft.ResponsiveRow([
                    ft.Container(self.codigo_barras, col=6, padding=5),
                    ft.Container(self.nombre, col=6, padding=5),
                ]),
                self.descripcion,
                
                # Precios
                ft.Text("Precios y Stocks", size=16, weight=FontWeight.W_600, color=Colors.INDIGO_700),
                ft.ResponsiveRow([
                    ft.Container(self.precio_compra, col=6, padding=5),
                    ft.Container(self.precio_normal, col=6, padding=5),
                ]),
                ft.ResponsiveRow([
                    ft.Container(self.precio_mayoreo, col=4, padding=5),
                    ft.Container(self.precio_promocion, col=4, padding=5),
                    ft.Container(self.iva_porcentaje, col=4, padding=5),
                ]),
                
                # Stocks
                ft.ResponsiveRow([
                    ft.Container(self.stock_actual, col=4, padding=5),
                    ft.Container(self.stock_minimo, col=4, padding=5),
                    ft.Container(self.stock_maximo, col=4, padding=5),
                ]),
                
                # Tipos de venta
                ft.Text("Tipos de Venta Activos", size=16, weight=FontWeight.W_600, color=Colors.INDIGO_700),
                ft.ResponsiveRow([
                    ft.Container(self.switch_normal, col=4, padding=5),
                    ft.Container(self.switch_mayoreo, col=4, padding=5),
                    ft.Container(self.switch_promocion, col=4, padding=5),
                ]),
                ft.ResponsiveRow([
                    ft.Container(self.minimo_mayoreo, col=6, padding=5),
                ]),
            ], scroll=ft.ScrollMode.ADAPTIVE),
            width=700,
            height=600
        )
        
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Gestión de Producto"),
            content=content,
            actions=[
                ft.TextButton("Cancelar", on_click=self._cancelar),
                ft.TextButton("Guardar", on_click=self._guardar_producto),
            ]
        )

    def _cancelar(self, e):
        self.page.close(self.dialog)

    def _guardar_producto(self, e):
        """Guarda o actualiza el producto"""
        try:
            # Validaciones básicas
            if not self.nombre.value.strip():
                self._mostrar_error("El nombre del producto es obligatorio")
                return

            # Preparar datos
            datos = {
                "codigo_barras": self.codigo_barras.value.strip() or None,
                "nombre": self.nombre.value.strip(),
                "descripcion": self.descripcion.value.strip() or None,
                "precio_compra": float(self.precio_compra.value or 0),
                "precio_venta_normal": float(self.precio_normal.value or 0),
                "precio_venta_mayoreo": float(self.precio_mayoreo.value or 0),
                "precio_venta_promocion": float(self.precio_promocion.value or 0),
                "stock_actual": int(self.stock_actual.value or 0),
                "stock_minimo": int(self.stock_minimo.value or 5),
                "stock_maximo": int(self.stock_maximo.value or 100),
                "iva_porcentaje": float(self.iva_porcentaje.value or 16.0),
                "venta_normal_activa": 1 if self.switch_normal.value else 0,
                "venta_mayoreo_activa": 1 if self.switch_mayoreo.value else 0,
                "venta_promocion_activa": 1 if self.switch_promocion.value else 0,
                "minimo_mayoreo": int(self.minimo_mayoreo.value or 10),
                "actualizado_en": datetime.now().isoformat()
            }

            with get_conn() as conn:
                if self.es_edicion:
                    # Actualizar producto existente
                    conn.execute("""
                        UPDATE productos 
                        SET codigo_barras=?, nombre=?, descripcion=?, precio_compra=?,
                            precio_venta_normal=?, precio_venta_mayoreo=?, precio_venta_promocion=?,
                            stock_actual=?, stock_minimo=?, stock_maximo=?, iva_porcentaje=?,
                            venta_normal_activa=?, venta_mayoreo_activa=?, venta_promocion_activa=?,
                            minimo_mayoreo=?, actualizado_en=?
                        WHERE id=?
                    """, [
                        datos["codigo_barras"], datos["nombre"], datos["descripcion"], 
                        datos["precio_compra"], datos["precio_venta_normal"], 
                        datos["precio_venta_mayoreo"], datos["precio_venta_promocion"],
                        datos["stock_actual"], datos["stock_minimo"], datos["stock_maximo"],
                        datos["iva_porcentaje"], datos["venta_normal_activa"],
                        datos["venta_mayoreo_activa"], datos["venta_promocion_activa"],
                        datos["minimo_mayoreo"], datos["actualizado_en"], self.producto["id"]
                    ])
                else:
                    # Insertar nuevo producto
                    conn.execute("""
                        INSERT INTO productos (
                            codigo_barras, nombre, descripcion, precio_compra,
                            precio_venta_normal, precio_venta_mayoreo, precio_venta_promocion,
                            stock_actual, stock_minimo, stock_maximo, iva_porcentaje,
                            venta_normal_activa, venta_mayoreo_activa, venta_promocion_activa,
                            minimo_mayoreo, creado_en, actualizado_en
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        datos["codigo_barras"], datos["nombre"], datos["descripcion"], 
                        datos["precio_compra"], datos["precio_venta_normal"], 
                        datos["precio_venta_mayoreo"], datos["precio_venta_promocion"],
                        datos["stock_actual"], datos["stock_minimo"], datos["stock_maximo"],
                        datos["iva_porcentaje"], datos["venta_normal_activa"],
                        datos["venta_mayoreo_activa"], datos["venta_promocion_activa"],
                        datos["minimo_mayoreo"], datos["actualizado_en"], datos["actualizado_en"]
                    ])

                conn.commit()

            self.page.close(self.dialog)
            self.win.cargar_productos()
            self.win._cargar_estadisticas()
            self.win._mostrar_mensaje("Producto guardado exitosamente")

        except Exception as ex:
            print(f"Error guardando producto: {ex}")
            self._mostrar_error(f"Error al guardar: {str(ex)}")

    def _mostrar_error(self, mensaje):
        snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.ERROR, color=Colors.WHITE),
                ft.Text(mensaje, color="black")
            ]),
            bgcolor=Colors.RED_50,
        )
        self.page.open(snack_bar)