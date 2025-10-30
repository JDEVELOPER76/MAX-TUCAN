import flet as ft
from datetime import datetime
from BASEDATOS import db
import json
from pathlib import Path
import sqlite3
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import threading

try:
    from .facturas import GeneradorFacturas
    FACTURAS_DISPONIBLE = True
except ImportError:
    print("Advertencia: Módulo facturas no disponible")
    FACTURAS_DISPONIBLE = False


class MenuVentas:
    def __init__(self, page: ft.Page, nombre_usuario: str):
        self.page = page
        self.nombre_usuario = nombre_usuario
        self.page.title = f"Ventas – {self.nombre_usuario}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f3f4f6"
        self.page.padding = 0
        self.carrito = []
        self.tipo_venta_actual = "normal"
        
        if FACTURAS_DISPONIBLE:
            self.generador_facturas = GeneradorFacturas()
        else:
            self.generador_facturas = None
            
        self.json_dir = Path("./Json files")
        self.datos_cliente_default = self._cargar_datos_cliente_default()
        self.config_email = self._cargar_config_email()
        self.datos_empresa = self._cargar_datos_empresa()
        self.productos = []
        self.total_productos = 0

        self.cargar_productos_db()
        self.build_ui()

    def _cargar_datos_cliente_default(self):
        """Carga datos de cliente por defecto desde JSON"""
        cliente_file = self.json_dir / "datos_cliente_default.json"
        datos_default = {
            "nombre": "CONSUMIDOR FINAL",
            "rfc": "XXXXXXXXXX",
            "direccion": "",
            "correo": "",
            "telefono": ""
        }
        
        try:
            if cliente_file.exists():
                with open(cliente_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                cliente_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cliente_file, 'w', encoding='utf-8') as f:
                    json.dump(datos_default, f, indent=4, ensure_ascii=False)
                return datos_default
        except Exception as e:
            print(f"Error cargando datos cliente: {e}")
            return datos_default

    def _cargar_config_email(self):
        """Carga configuración de email desde JSON"""
        email_file = self.json_dir / "email.json"
        config_default = {
            "servidor_smtp": "smtp.gmail.com",
            "puerto": 587,
            "email_remitente": "",
            "password_app": "",
            "usar_tls": True,
            "asunto_factura": "Factura #{numero_factura} - {empresa}",
            "cuerpo_factura": "Estimado {cliente},\n\nAdjuntamos su factura #{numero_factura} por un total de ${total}.\n\nGracias por su preferencia."
        }
        
        try:
            if email_file.exists():
                with open(email_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return config_default
        except Exception as e:
            print(f"Error cargando configuración de email: {e}")
            return config_default

    def _cargar_datos_empresa(self):
        """Carga datos de la empresa desde JSON"""
        empresa_file = self.json_dir / "datos_empresariales.json"
        datos_default = {
            "nombre_empresa": "MI EMPRESA",
            "direccion": "Calle Principal #123",
            "correo_electronico": "contacto@miempresa.com",
            "numero_telefono": "+000000000"
        }
        
        try:
            if empresa_file.exists():
                with open(empresa_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return datos_default
        except Exception as e:
            print(f"Error cargando datos empresa: {e}")
            return datos_default

    def cargar_productos_db(self):
        """Carga productos activos desde la base de datos."""
        try:
            db_path = "./BASEDATOS/productos.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productos'")
            tabla_existe = cursor.fetchone()
            
            if not tabla_existe:
                print("⚠️ La tabla 'productos' no existe. No se cargarán productos.")
                self.productos = []
                self.total_productos = 0
                conn.close()
                return
            
            cursor.execute("""
                SELECT 
                    id, codigo_barras, nombre, descripcion,
                    precio_venta_normal, precio_venta_mayoreo, precio_venta_promocion,
                    stock_actual, stock_minimo, stock_maximo,
                    venta_normal_activa, venta_mayoreo_activa, venta_promocion_activa,
                    minimo_mayoreo, imagen_path, activo, iva_porcentaje
                FROM productos 
                WHERE activo = 1 AND stock_actual > 0
                ORDER BY nombre
            """)
            
            productos_db = cursor.fetchall()
            self.productos = []
            
            for producto in productos_db:
                precio_activo, tipo_precio = self._obtener_precio_segun_tipo_venta(producto)
                
                producto_dict = {
                    "id": producto['id'],
                    "codigo_barras": producto['codigo_barras'],
                    "nombre": producto['nombre'],
                    "descripcion": producto['descripcion'],
                    "precio": precio_activo,
                    "stock": producto['stock_actual'],
                    "stock_minimo": producto['stock_minimo'],
                    "tipo_precio": tipo_precio,
                    "imagen_path": producto['imagen_path'],
                    "precio_normal": producto['precio_venta_normal'],
                    "precio_mayoreo": producto['precio_venta_mayoreo'],
                    "precio_promocion": producto['precio_venta_promocion'],
                    "iva_porcentaje": producto['iva_porcentaje'] if producto['iva_porcentaje'] is not None else 16.0,
                    "venta_normal_activa": producto['venta_normal_activa'],
                    "venta_mayoreo_activa": producto['venta_mayoreo_activa'],
                    "venta_promocion_activa": producto['venta_promocion_activa'],
                    "minimo_mayoreo": producto['minimo_mayoreo']
                }
                self.productos.append(producto_dict)
            
            self.total_productos = len(self.productos)
            conn.close()
            
            if not self.productos:
                print("ℹ️ No se encontraron productos activos con stock > 0.")
                self.productos = []
                self.total_productos = 0
            
        except Exception as e:
            print(f"Error cargando productos desde DB: {e}")
            self.productos = []
            self.total_productos = 0

    def _obtener_precio_segun_tipo_venta(self, producto):
        """Determina el precio activo según el tipo de venta actual"""
        if self.tipo_venta_actual == "promocion" and producto['venta_promocion_activa'] and producto['precio_venta_promocion'] and producto['precio_venta_promocion'] > 0:
            return producto['precio_venta_promocion'], "Promoción"
        elif self.tipo_venta_actual == "mayoreo" and producto['venta_mayoreo_activa'] and producto['precio_venta_mayoreo'] and producto['precio_venta_mayoreo'] > 0:
            return producto['precio_venta_mayoreo'], "Mayoreo"
        else:
            return producto['precio_venta_normal'], "Normal"

    def build_ui(self):
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.POINT_OF_SALE, size=28, color=ft.Colors.INDIGO_600),
                ft.Column([
                    ft.Text("Menú de Ventas", size=20, weight=ft.FontWeight.W_600, color=ft.Colors.INDIGO_900),
                    ft.Text(f"Empleado: {self.nombre_usuario}", size=16, color=ft.Colors.GREY_700),
                ], spacing=2),
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Tipo de Venta", size=12, color=ft.Colors.GREY_600),
                        self._crear_selector_tipo_venta(),
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=10)
                ),
                ft.Column([
                    ft.Text(f"{datetime.now():%d/%m/%Y}", size=14, color=ft.Colors.GREY_600),
                    ft.Text(f"Productos: {self.total_productos}", size=12, color=ft.Colors.GREY_500),
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.Icons.ARROW_BACK, size=18), ft.Text("Regresar")], spacing=8),
                    on_click=self.regresar,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE, bgcolor=ft.Colors.INDIGO_600,
                        shape=ft.RoundedRectangleBorder(radius=8), padding=ft.padding.symmetric(horizontal=16, vertical=12)
                    )
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=24, right=24, top=18, bottom=18),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        self.buscador = ft.TextField(
            label="🔍 Buscar producto...",
            hint_text="Escribe el nombre o código del producto",
            on_change=self.filtrar_productos,
            border_radius=12,
            border_color=ft.Colors.INDIGO_300,
            focused_border_color=ft.Colors.INDIGO_500,
            width=350,
            height=45
        )

        self.lista_productos = ft.GridView(
            runs_count=3,
            max_extent=260,
            spacing=15,
            run_spacing=15,
            padding=20,
            expand=True,
        )
        self.cargar_productos_ui(self.productos)

        self.total_text = ft.Text("Total: $0.00", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
        
        self.carrito_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHOPPING_CART, size=24, color=ft.Colors.INDIGO_600),
                ft.Text("Carrito de Compras", size=18, weight=ft.FontWeight.BOLD, 
                       color=ft.Colors.INDIGO_900, expand=True),
                ft.Container(
                    content=ft.Text(f"0", 
                                   size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                    bgcolor=ft.Colors.INDIGO_500,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4)
                )
            ]),
            padding=ft.padding.only(bottom=10)
        )

        self.lista_carrito = ft.ListView(
            spacing=8,
            height=220,
            auto_scroll=True
        )

        botones_carrito = ft.Row([
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.PAYMENT, size=20),
                    ft.Text("Procesar Compra", weight=ft.FontWeight.W_600)
                ], spacing=8),
                on_click=self.mostrar_dialogo_tipo_cliente,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN_600,
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.padding.symmetric(horizontal=20, vertical=14)
                ),
                expand=True
            ),
        ], spacing=10)

        botones_accion = ft.Row([
            ft.OutlinedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CLEAR_ALL, size=18),
                    ft.Text("Vaciar Carrito")
                ], spacing=6),
                on_click=self.limpiar_carrito,
                style=ft.ButtonStyle(
                    color=ft.Colors.RED_600,
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(color=ft.Colors.RED_300, width=1)
                ),
                expand=True
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color=ft.Colors.INDIGO_600,
                on_click=self.actualizar_productos,
                tooltip="Actualizar productos",
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=8),
                    side=ft.BorderSide(color=ft.Colors.INDIGO_300, width=1)
                )
            ),
        ], spacing=8)

        carrito_area = ft.Container(
            content=ft.Column([
                self.carrito_header,
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=self.lista_carrito,
                            bgcolor=ft.Colors.GREY_50,
                            border_radius=12,
                            padding=12,
                            height=220,
                            expand=True
                        ),
                    ]),
                    expand=True
                ),
                ft.Container(
                    content=self.total_text,
                    padding=ft.padding.symmetric(vertical=10),
                    alignment=ft.alignment.center
                ),
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                botones_carrito,
                botones_accion,
            ], spacing=12),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=0, 
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), 
                offset=ft.Offset(0, 4)
            ),
            width=320,
        )

        self.page.clean()
        self.page.add(
            ft.Column([
                header,
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Container(
                                content=self.buscador,
                                padding=ft.padding.only(bottom=10)
                            ),
                            self.lista_productos
                        ], expand=True, spacing=0),
                        carrito_area,
                    ], expand=True, spacing=20),
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                ),
            ], expand=True, spacing=0)
        )
        self.actualizar_vista_carrito()

    def _crear_selector_tipo_venta(self):
        """Crea el selector de tipo de venta"""
        self.selector_tipo_venta = ft.Dropdown(
            value=self.tipo_venta_actual,
            options=[
                ft.dropdown.Option("normal", "Venta Normal"),
                ft.dropdown.Option("mayoreo", "Venta Mayoreo"),
                ft.dropdown.Option("promocion", "Venta Promoción"),
            ],
            width=150,
            border_radius=8,
            border_color=ft.Colors.INDIGO_300,
            focused_border_color=ft.Colors.INDIGO_500,
            on_change=self.cambiar_tipo_venta
        )
        return ft.Container(
            content=self.selector_tipo_venta,
            height=45,
            alignment=ft.alignment.center
        )

    def cambiar_tipo_venta(self, e):
        """Cambia el tipo de venta y actualiza los precios"""
        nuevo_tipo = self.selector_tipo_venta.value
        if nuevo_tipo != self.tipo_venta_actual:
            self.tipo_venta_actual = nuevo_tipo
            self.mostrar_mensaje_exito(f"Tipo de venta cambiado a: {self.obtener_nombre_tipo_venta()}")
            
            for producto in self.productos:
                producto["precio"], producto["tipo_precio"] = self._obtener_precio_segun_tipo_venta_db(producto)
            
            for item in self.carrito:
                producto_actualizado = next((p for p in self.productos if p["id"] == item["producto"]["id"]), None)
                if producto_actualizado:
                    item["producto"]["precio"] = producto_actualizado["precio"]
                    item["producto"]["tipo_precio"] = producto_actualizado["tipo_precio"]
            
            self.cargar_productos_ui(self.productos)
            self.actualizar_vista_carrito()
            self.calcular_total()

    def _obtener_precio_segun_tipo_venta_db(self, producto):
        """Determina el precio activo según el tipo de venta actual para productos ya cargados"""
        if (self.tipo_venta_actual == "promocion" and 
            producto.get('venta_promocion_activa') and 
            producto.get('precio_promocion') and 
            producto['precio_promocion'] > 0):
            return producto['precio_promocion'], "Promoción"
        elif (self.tipo_venta_actual == "mayoreo" and 
              producto.get('venta_mayoreo_activa') and 
              producto.get('precio_mayoreo') and 
              producto['precio_mayoreo'] > 0):
            return producto['precio_mayoreo'], "Mayoreo"
        else:
            return producto['precio_normal'], "Normal"

    def obtener_nombre_tipo_venta(self):
        """Obtiene el nombre legible del tipo de venta actual"""
        nombres = {
            "normal": "Venta Normal",
            "mayoreo": "Venta Mayoreo", 
            "promocion": "Venta Promoción"
        }
        return nombres.get(self.tipo_venta_actual, "Venta Normal")

    def cargar_productos_ui(self, productos):
        """Carga hasta 60 productos en la vista sin scroll infinito."""
        self.lista_productos.controls.clear()

        # Limitar a 60 productos visibles
        productos_visibles = productos[:60]

        if not productos_visibles:
            self.lista_productos.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INVENTORY_2, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No hay productos", size=16, color=ft.Colors.GREY_600),
                        ft.Text("Actualiza o verifica el inventario", size=12, color=ft.Colors.GREY_400),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                    padding=40,
                    alignment=ft.alignment.center
                )
            )
        else:
            for p in productos_visibles:
                stock_color = ft.Colors.GREEN_600
                stock_icon = ft.Icons.INVENTORY
                if p["stock"] <= p.get("stock_minimo", 5):
                    stock_color = ft.Colors.ORANGE_600
                    stock_icon = ft.Icons.WARNING
                if p["stock"] == 0:
                    stock_color = ft.Colors.RED_600
                    stock_icon = ft.Icons.ERROR

                badge_color = ft.Colors.BLUE_500
                if p.get("tipo_precio") == "Mayoreo":
                    badge_color = ft.Colors.GREEN_500
                elif p.get("tipo_precio") == "Promoción":
                    badge_color = ft.Colors.RED_500

                tile = ft.Card(
                    elevation=2,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text(
                                        p["nombre"], 
                                        size=15, 
                                        weight=ft.FontWeight.W_600, 
                                        color=ft.Colors.GREY_800,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS
                                    ),
                                    ft.Container(height=5),
                                    ft.Row([
                                        ft.Icon(ft.Icons.ATTACH_MONEY, size=14, color=ft.Colors.GREEN_700),
                                        ft.Text(
                                            f"{p['precio']:.2f}", 
                                            size=16, 
                                            weight=ft.FontWeight.BOLD, 
                                            color=ft.Colors.GREEN_700
                                        ),
                                    ], spacing=5),
                                ]),
                                padding=ft.padding.symmetric(horizontal=15, vertical=10)
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Row([
                                        ft.Icon(stock_icon, size=12, color=stock_color),
                                        ft.Text(f"Stock: {p['stock']}", size=11, color=stock_color),
                                    ], spacing=5),
                                    ft.Container(expand=True),
                                    ft.Container(
                                        content=ft.Text(
                                            p.get("tipo_precio", "Normal"), 
                                            size=10, 
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.W_500
                                        ),
                                        bgcolor=badge_color,
                                        border_radius=8,
                                        padding=ft.padding.symmetric(horizontal=6, vertical=2)
                                    )
                                ]),
                                padding=ft.padding.symmetric(horizontal=15),
                                bgcolor=ft.Colors.GREY_50,
                            ),
                            ft.Container(
                                content=ft.ElevatedButton(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.ADD_SHOPPING_CART, size=16),
                                        ft.Text("Agregar", size=12, weight=ft.FontWeight.W_500)
                                    ], spacing=6, alignment=ft.MainAxisAlignment.CENTER),
                                    on_click=lambda e, prod=p: self.mostrar_dialogo_cantidad(prod),
                                    style=ft.ButtonStyle(
                                        color=ft.Colors.WHITE,
                                        bgcolor=ft.Colors.INDIGO_600,
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                        padding=ft.padding.symmetric(horizontal=12, vertical=8)
                                    ),
                                    width=120
                                ),
                                padding=ft.padding.symmetric(vertical=10),
                                alignment=ft.alignment.center
                            )
                        ], spacing=0),
                        border_radius=12,
                    )
                )
                self.lista_productos.controls.append(tile)

        # Configurar GridView sin scroll infinito
        self.lista_productos.expand = False
        self.lista_productos.height = 900  # altura fija razonable
        self.page.update()


    def filtrar_productos(self, e):
        texto = self.buscador.value.lower().strip()
        if not texto:
            self.cargar_productos_ui(self.productos)
            return
            
        filtrados = [
            p for p in self.productos 
            if texto in p["nombre"].lower() or 
               (p.get("codigo_barras") and texto in p["codigo_barras"].lower())
        ]
        self.cargar_productos_ui(filtrados)

    def actualizar_productos(self, e=None):
        self.cargar_productos_db()
        self.cargar_productos_ui(self.productos)
        self.mostrar_mensaje_exito("Productos actualizados")
        self.page.update()

    def mostrar_dialogo_cantidad(self, producto):
        cantidad_field = ft.TextField(
            label="Cantidad",
            value="1",
            keyboard_type=ft.KeyboardType.NUMBER,
            width=150
        )
        
        def agregar_con_cantidad(e):
            try:
                cantidad = int(cantidad_field.value)
                if cantidad > 0:
                    if cantidad <= producto["stock"]:
                        self.agregar_al_carrito(producto, cantidad)
                        self.page.close(dlg)
                        self.mostrar_mensaje_exito(f"Agregado: {producto['nombre']} x{cantidad}")
                    else:
                        self.mostrar_mensaje_error(f"Stock insuficiente. Disponible: {producto['stock']}")
                else:
                    self.mostrar_mensaje_error("La cantidad debe ser mayor a 0")
            except ValueError:
                self.mostrar_mensaje_error("Ingrese una cantidad válida")

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Agregar {producto['nombre']}"),
            content=ft.Column([
                ft.Text(f"Precio: ${producto['precio']:.2f} ({producto.get('tipo_precio', 'Normal')})"),
                ft.Text(f"Stock disponible: {producto['stock']}"),
                ft.Text(f"Tipo de Venta: {self.obtener_nombre_tipo_venta()}"),
                cantidad_field
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.TextButton("Agregar", on_click=agregar_con_cantidad),
            ],
        )
        self.page.open(dlg)

    def agregar_al_carrito(self, producto, cantidad=1):
        for item in self.carrito:
            if item["producto"]["id"] == producto["id"]:
                item["cantidad"] += cantidad
                break
        else:
            self.carrito.append({"producto": producto, "cantidad": cantidad})
        
        self.actualizar_vista_carrito()
        self.calcular_total()

    def actualizar_vista_carrito(self):
        self.lista_carrito.controls.clear()
        
        if not self.carrito:
            self.lista_carrito.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHOPPING_CART_OUTLINED, size=40, color=ft.Colors.GREY_400),
                        ft.Text("Carrito vacío", size=14, color=ft.Colors.GREY_500),
                        ft.Text("Agrega productos para continuar", size=12, color=ft.Colors.GREY_400),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=30,
                    alignment=ft.alignment.center
                )
            )
        else:
            for i, item in enumerate(self.carrito):
                producto = item["producto"]
                cantidad = item["cantidad"]
                total_item = producto["precio"] * cantidad
                
                item_card = ft.Card(
                    elevation=1,
                    content=ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(
                                    producto["nombre"], 
                                    size=13, 
                                    weight=ft.FontWeight.W_600,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                ft.Row([
                                    ft.Text(f"${producto['precio']:.2f}", size=11, color=ft.Colors.GREY_600),
                                    ft.Text(f"({producto.get('tipo_precio', 'Normal')})", size=10, color=ft.Colors.GREY_500),
                                    ft.Text("×", size=11, color=ft.Colors.GREY_500),
                                    ft.Text(f"{cantidad}", size=11, color=ft.Colors.GREY_600),
                                ], spacing=4),
                            ], expand=True, spacing=4),
                            ft.Row([
                                ft.Text(f"${total_item:.2f}", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_size=18,
                                    icon_color=ft.Colors.RED_500,
                                    on_click=lambda e, idx=i: self.eliminar_del_carrito(idx),
                                    tooltip="Eliminar",
                                    style=ft.ButtonStyle(
                                        padding=ft.padding.all(6),
                                        side=ft.BorderSide(color=ft.Colors.RED_100, width=1)
                                    )
                                )
                            ], spacing=8)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        border_radius=8,
                    )
                )
                self.lista_carrito.controls.append(item_card)
        
        self.actualizar_contador_carrito()
        self.page.update()

    def actualizar_contador_carrito(self):
        """Actualiza el contador de items en el carrito"""
        total_items = sum(item["cantidad"] for item in self.carrito)
        self.carrito_header.content.controls[2].content.value = str(total_items)
        self.carrito_header.update()

    def mostrar_dialogo_tipo_cliente(self, e):
        if not self.carrito:
            self.mostrar_mensaje_error("El carrito está vacío")
            return

        def seleccionar_tipo_cliente(tipo):
            self.page.close(dlg_tipo)
            if tipo == "consumidor":
                self.mostrar_dialogo_cobro("CONSUMIDOR FINAL", "XAXX010101000", True)
            else:
                self.mostrar_dialogo_cobro("", "", False)

        dlg_tipo = ft.AlertDialog(
            modal=True,
            title=ft.Text("Tipo de Cliente"),
            content=ft.Column([
                ft.Text("Seleccione el tipo de cliente:", size=14, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Column([
                            ft.Icon(ft.Icons.PERSON, size=30, color=ft.Colors.BLUE_600),
                            ft.Text("Consumidor Final", size=12, weight=ft.FontWeight.W_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        on_click=lambda e: seleccionar_tipo_cliente("consumidor"),
                        style=ft.ButtonStyle(
                            color=ft.Colors.BLUE_600,
                            bgcolor=ft.Colors.BLUE_50,
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=20
                        ),
                        expand=True
                    ),
                    ft.ElevatedButton(
                        content=ft.Column([
                            ft.Icon(ft.Icons.BUSINESS, size=30, color=ft.Colors.GREEN_600),
                            ft.Text("Con RUC/Cédula", size=12, weight=ft.FontWeight.W_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        on_click=lambda e: seleccionar_tipo_cliente("ruc"),
                        style=ft.ButtonStyle(
                            color=ft.Colors.GREEN_600,
                            bgcolor=ft.Colors.GREEN_50,
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=20
                        ),
                        expand=True
                    ),
                ], spacing=15)
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_tipo)),
            ],
        )
        self.page.open(dlg_tipo)

    def mostrar_dialogo_opcion_factura(self, datos_cliente, subtotal, iva_total, total):
        """Diálogo para seleccionar si desea factura y el tipo"""
        
        def opcion_seleccionada(opcion):
            self.page.close(dlg_factura)
            
            if opcion == "no":
                self.procesar_compra_final(datos_cliente, subtotal, iva_total, total, generar_factura=False)
            elif opcion == "fisica":
                self.procesar_compra_final(datos_cliente, subtotal, iva_total, total, 
                                         generar_factura=True, tipo_envio="fisica")
            elif opcion == "email":
                self.mostrar_dialogo_correo(datos_cliente, subtotal, iva_total, total)
            elif opcion == "ambas":
                self.mostrar_dialogo_correo(datos_cliente, subtotal, iva_total, total, enviar_ambas=True)

        dlg_factura = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.INDIGO_600, size=28),
                ft.Text("¿Desea Factura?", size=20, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Seleccione una opción:", size=14, color=ft.Colors.GREY_700),
                    ft.Container(height=15),
                    
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CANCEL_OUTLINED, size=24, color=ft.Colors.GREY_700),
                                ft.Column([
                                    ft.Text("Sin Factura", size=14, weight=ft.FontWeight.W_600),
                                    ft.Text("Solo confirmar la compra", size=11, color=ft.Colors.GREY_600),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            on_click=lambda e: opcion_seleccionada("no"),
                            style=ft.ButtonStyle(
                                color=ft.Colors.GREY_700,
                                bgcolor=ft.Colors.GREY_100,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.padding.symmetric(horizontal=20, vertical=15)
                            ),
                        ),
                        width=400
                    ),
                    
                    ft.Container(height=10),
                    
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.PRINT, size=24, color=ft.Colors.BLUE_700),
                                ft.Column([
                                    ft.Text("Factura Física", size=14, weight=ft.FontWeight.W_600),
                                    ft.Text("Abrir en navegador para imprimir", size=11, color=ft.Colors.GREY_600),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            on_click=lambda e: opcion_seleccionada("fisica"),
                            style=ft.ButtonStyle(
                                color=ft.Colors.BLUE_700,
                                bgcolor=ft.Colors.BLUE_50,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.padding.symmetric(horizontal=20, vertical=15)
                            ),
                        ),
                        width=400
                    ),
                    
                    ft.Container(height=10),
                    
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.EMAIL, size=24, color=ft.Colors.GREEN_700),
                                ft.Column([
                                    ft.Text("Factura por Email", size=14, weight=ft.FontWeight.W_600),
                                    ft.Text("Enviar PDF por correo electrónico", size=11, color=ft.Colors.GREY_600),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            on_click=lambda e: opcion_seleccionada("email"),
                            style=ft.ButtonStyle(
                                color=ft.Colors.GREEN_700,
                                bgcolor=ft.Colors.GREEN_50,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.padding.symmetric(horizontal=20, vertical=15)
                            ),
                        ),
                        width=400
                    ),
                    
                    ft.Container(height=10),
                    
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([
                                ft.Icon(ft.Icons.ALL_INBOX, size=24, color=ft.Colors.PURPLE_700),
                                ft.Column([
                                    ft.Text("Ambas Opciones", size=14, weight=ft.FontWeight.W_600),
                                    ft.Text("Email + Abrir en navegador", size=11, color=ft.Colors.GREY_600),
                                ], spacing=2, expand=True),
                            ], spacing=12),
                            on_click=lambda e: opcion_seleccionada("ambas"),
                            style=ft.ButtonStyle(
                                color=ft.Colors.PURPLE_700,
                                bgcolor=ft.Colors.PURPLE_50,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.padding.symmetric(horizontal=20, vertical=15)
                            ),
                        ),
                        width=400
                    ),
                    
                ], spacing=5),
                width=420
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_factura)),
            ],
        )
        self.page.open(dlg_factura)

    def mostrar_dialogo_correo(self, datos_cliente, subtotal, iva_total, total, enviar_ambas=False):
        """Diálogo para solicitar correo electrónico"""
        
        correo_field = ft.TextField(
            label="Correo Electrónico",
            hint_text="ejemplo@correo.com",
            prefix_icon=ft.Icons.EMAIL,
            keyboard_type=ft.KeyboardType.EMAIL,
            border_radius=10,
            width=350
        )
        
        def enviar_con_correo(e):
            correo = correo_field.value.strip()
            if correo and "@" in correo and "." in correo:
                datos_cliente["correo"] = correo
                self.page.close(dlg_correo)
                
                if enviar_ambas:
                    self.procesar_compra_final(datos_cliente, subtotal, iva_total, total, 
                                             generar_factura=True, tipo_envio="ambas")
                else:
                    self.procesar_compra_final(datos_cliente, subtotal, iva_total, total, 
                                             generar_factura=True, tipo_envio="email")
            else:
                self.mostrar_mensaje_error("Por favor ingrese un correo válido")
        
        dlg_correo = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.EMAIL, color=ft.Colors.GREEN_600, size=26),
                ft.Text("Correo Electrónico", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=ft.Column([
                ft.Text("Ingrese el correo electrónico del cliente:", size=14, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                correo_field,
                ft.Container(height=5),
                ft.Text("La factura se enviará en formato PDF", size=12, color=ft.Colors.GREY_500, italic=True),
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_correo)),
                ft.FilledButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.SEND, size=18),
                        ft.Text("Enviar")
                    ], spacing=6),
                    on_click=enviar_con_correo,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)
                ),
            ],
        )
        self.page.open(dlg_correo)

    def mostrar_dialogo_cobro(self, nombre_default="", rfc_default="", es_consumidor_final=False):
        nombre_field = ft.TextField(
            label="Nombre o Razón Social",
            value=nombre_default,
            prefix_icon=ft.Icons.PERSON,
            border_radius=8,
            expand=True
        )
        
        tipo_documento = ft.Dropdown(
            label="Tipo de Documento",
            value="RUC" if rfc_default else "Cédula",
            options=[
                ft.dropdown.Option("Cédula"),
                ft.dropdown.Option("RUC"),
            ],
            width=120,
            border_radius=8,
            visible=not es_consumidor_final
        )
        
        documento_field = ft.TextField(
            label="Número de Documento",
            value=rfc_default,
            prefix_icon=ft.Icons.CREDIT_CARD,
            border_radius=8,
            expand=True,
            visible=not es_consumidor_final
        )
        
        direccion_field = ft.TextField(
            label="Dirección (Opcional)",
            prefix_icon=ft.Icons.LOCATION_ON,
            multiline=True,
            max_lines=2,
            border_radius=8,
            expand=True
        )

        items_resumen = []
        subtotal = 0
        iva_total = 0
        
        for item in self.carrito:
            producto = item["producto"]
            cantidad = item["cantidad"]
            total_item = producto["precio"] * cantidad
            subtotal += total_item
            
            iva_porcentaje = producto.get("iva_porcentaje", 16.0)
            iva_item = total_item * (iva_porcentaje / 100)
            iva_total += iva_item
            
            items_resumen.append(
                ft.Row([
                    ft.Text(f"{producto['nombre']}", size=12, expand=2,
                           max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"x{cantidad}", size=12, width=40),
                    ft.Text(f"${total_item:.2f}", size=12, weight=ft.FontWeight.W_500, width=70),
                    ft.Text(f"IVA {iva_porcentaje}%", size=10, color=ft.Colors.GREY_500, width=60),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        total = subtotal + iva_total

        def confirmar_datos(e):
            datos_cliente = {
                "nombre": nombre_field.value,
                "rfc": documento_field.value if not es_consumidor_final else "XXXXXXXXXX",
                "direccion": direccion_field.value,
                "tipo_documento": tipo_documento.value if not es_consumidor_final else "Consumidor Final",
                "tipo_venta": self.obtener_nombre_tipo_venta()
            }
            
            self.page.close(dlg_cobro)
            self.mostrar_dialogo_opcion_factura(datos_cliente, subtotal, iva_total, total)

        dlg_cobro = ft.AlertDialog(
            modal=True,
            title=ft.Text("Procesar Compra"),
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Información del Cliente", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
                        ft.Row([nombre_field], spacing=10),
                        ft.Row([tipo_documento, documento_field], spacing=10) if not es_consumidor_final else ft.Container(),
                        ft.Row([direccion_field], spacing=10),
                    ], spacing=12),
                    padding=ft.padding.only(bottom=20)
                ),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("Resumen de la Compra", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_800),
                        ft.Column(items_resumen, spacing=6),
                        ft.Divider(height=20),
                        ft.Row([
                            ft.Text("Subtotal:", size=14, weight=ft.FontWeight.W_500, expand=True),
                            ft.Text(f"${subtotal:.2f}", size=14, weight=ft.FontWeight.W_500),
                        ]),
                        ft.Row([
                            ft.Text("IVA:", size=14, weight=ft.FontWeight.W_500, expand=True),
                            ft.Text(f"${iva_total:.2f}", size=14, weight=ft.FontWeight.W_500),
                        ]),
                        ft.Row([
                            ft.Text("TOTAL:", size=16, weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(f"${total:.2f}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                        ]),
                    ], spacing=8),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=12,
                    padding=15
                ),
            ], scroll=ft.ScrollMode.AUTO, height=400),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_cobro)),
                ft.FilledButton(
                    content=ft.Row([ft.Icon(ft.Icons.ARROW_FORWARD), ft.Text("Continuar")]),
                    on_click=confirmar_datos,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO_600, padding=15)
                ),
            ],
        )
        self.page.open(dlg_cobro)

    def procesar_compra_final(self, datos_cliente, subtotal, iva_total, total, generar_factura=False, tipo_envio=None):
        """Procesa la compra final con o sin factura"""
        print("DEBUG: Iniciando procesamiento de compra...")
        
        try:
            print("DEBUG: Actualizando stock en base de datos...")
            db_path = "./BASEDATOS/productos.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            for item in self.carrito:
                producto_id = item["producto"]["id"]
                cantidad_vendida = item["cantidad"]
                
                cursor.execute(
                    "UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?",
                    [cantidad_vendida, producto_id]
                )
                print(f"DEBUG: Stock actualizado para producto ID {producto_id}, cantidad: {cantidad_vendida}")
            
            conn.commit()
            conn.close()
            print("DEBUG: Stock actualizado exitosamente")
            
        except Exception as ex:
            print(f"ERROR: Al actualizar stock: {ex}")
            import traceback
            traceback.print_exc()
        
        print("DEBUG: Guardando venta en base de datos...")
        if db.guardar_venta(self.nombre_usuario, self.carrito):
            print("DEBUG: Venta guardada exitosamente")
            
            if generar_factura and FACTURAS_DISPONIBLE and self.generador_facturas:
                print("DEBUG: Generando factura PDF...")
                try:
                    items_factura = [
                        {
                            "descripcion": item["producto"]["nombre"],
                            "cantidad": item["cantidad"],
                            "precio": item["producto"]["precio"],
                            "iva_porcentaje": item["producto"].get("iva_porcentaje", 16.0)
                        }
                        for item in self.carrito
                    ]
                    
                    ruta_factura = self.generador_facturas.generar_factura_pdf(
                        cliente=datos_cliente,
                        items=items_factura,
                        subtotal=subtotal,
                        iva_total=iva_total,
                        total=total,
                        vendedor=self.nombre_usuario
                    )
                    
                    if ruta_factura:
                        print(f"DEBUG: Factura generada exitosamente: {ruta_factura}")
                        
                        if tipo_envio == "fisica":
                            self.abrir_archivo(ruta_factura)
                            self.mostrar_mensaje_exito("¡Venta procesada! Factura abierta en navegador")
                        elif tipo_envio == "email":
                            exito_envio = self.enviar_factura_por_email(
                                ruta_factura, 
                                datos_cliente.get("correo", ""),
                                datos_cliente.get("nombre", "Cliente"),
                                total
                            )
                            if exito_envio:
                                self.mostrar_mensaje_exito(f"¡Venta procesada! Factura enviada a {datos_cliente.get('correo')}")
                            else:
                                self.mostrar_mensaje_error("Venta procesada pero hubo un error al enviar el email")
                        elif tipo_envio == "ambas":
                            self.abrir_archivo(ruta_factura)
                            exito_envio = self.enviar_factura_por_email(
                                ruta_factura, 
                                datos_cliente.get("correo", ""),
                                datos_cliente.get("nombre", "Cliente"),
                                total
                            )
                            if exito_envio:
                                self.mostrar_mensaje_exito(f"¡Venta procesada! Factura abierta y enviada a {datos_cliente.get('correo')}")
                            else:
                                self.mostrar_mensaje_error("Factura abierta pero hubo un error al enviar el email")
                    else:
                        print("ERROR: No se pudo generar la factura")
                        self.mostrar_mensaje_error("Error al generar la factura")
                        
                except Exception as ex:
                    print(f"ERROR: Al generar factura: {ex}")
                    import traceback
                    traceback.print_exc()
                    self.mostrar_mensaje_error("Error al generar la factura")
            else:
                self.mostrar_mensaje_exito("¡Venta procesada exitosamente!")
            
            self.limpiar_carrito()
            self.actualizar_productos()
        else:
            self.mostrar_mensaje_error("Error al procesar la venta en la base de datos")

    def enviar_factura_por_email(self, ruta_factura, correo_destino, nombre_cliente, total):
        """Envía la factura por correo electrónico usando la configuración guardada"""
        
        # Crear diálogo de progreso
        self.progress_logs = ft.Column(scroll=ft.ScrollMode.AUTO, height=200)
        self.progress_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.ProgressRing(width=20, height=20, color=ft.Colors.BLUE_600),
                ft.Text("Enviando Factura por Email", size=18, weight=ft.FontWeight.BOLD),
            ], spacing=12),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Enviando factura a: {correo_destino}", size=14, weight=ft.FontWeight.W_500),
                    ft.Divider(height=10),
                    ft.Container(
                        content=self.progress_logs,
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=8,
                        padding=10,
                        height=200
                    )
                ], spacing=12),
                width=500
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self._cancelar_envio_email),
            ],
        )
        
        # Mostrar diálogo
        self.page.open(self.progress_dialog)
        self.page.update()
        
        # Función para agregar logs al diálogo con actualización forzada
        def agregar_log(mensaje, tipo="info"):
            import time
            color = ft.Colors.BLUE_600 if tipo == "info" else ft.Colors.RED_600
            icon = ft.Icons.INFO if tipo == "info" else ft.Icons.ERROR
            
            log_row = ft.Row([
                ft.Icon(icon, size=14, color=color),
                ft.Text(mensaje, size=12, color=ft.Colors.GREY_700),
            ], spacing=8)
            
            self.progress_logs.controls.append(log_row)
            # Forzar actualización
            self.progress_logs.update()
            self.page.update()
            time.sleep(0.5)  # Pequeña pausa para que se vea cada paso
        
        # Ejecutar en un hilo para no bloquear la UI
        def enviar_email_thread():
            try:
                agregar_log("Iniciando envío de factura...")
                agregar_log(f"Archivo: {os.path.basename(ruta_factura)}")
                
                # Verificar configuración de email
                if not self.config_email.get("email_remitente") or not self.config_email.get("password_app"):
                    agregar_log("ERROR: Configuración de email incompleta", "error")
                    self.mostrar_mensaje_error("Configure el email en Configuraciones antes de enviar facturas")
                    # Cambiar a botón cerrar
                    self.progress_dialog.actions = [
                        ft.TextButton("Cerrar", on_click=lambda e: self.page.close(self.progress_dialog)),
                    ]
                    self.progress_dialog.update()
                    return False
                
                # Obtener configuración
                servidor_smtp = self.config_email.get("servidor_smtp", "smtp.gmail.com")
                puerto = self.config_email.get("puerto", 587)
                email_remitente = self.config_email.get("email_remitente")
                password_app = self.config_email.get("password_app")
                usar_tls = self.config_email.get("usar_tls", True)
                
                agregar_log(f"Servidor SMTP: {servidor_smtp}:{puerto}")
                agregar_log(f"Email remitente: {email_remitente}")
                
                # Obtener plantillas
                asunto_template = self.config_email.get("asunto_factura", "Factura #{numero_factura} - {empresa}")
                cuerpo_template = self.config_email.get("cuerpo_factura", "Adjunto encontrará su factura.")
                
                # Obtener número de factura del nombre del archivo
                nombre_archivo = os.path.basename(ruta_factura)
                numero_factura = nombre_archivo.replace("Factura_", "").replace(".pdf", "")
                
                # Reemplazar variables en las plantillas
                nombre_empresa = self.datos_empresa.get("nombre_empresa", "MI EMPRESA")
                fecha_actual = datetime.now().strftime("%d/%m/%Y")
                
                asunto = asunto_template.format(
                    numero_factura=numero_factura,
                    empresa=nombre_empresa,
                    cliente=nombre_cliente,
                    total=f"{total:.2f}",
                    fecha=fecha_actual
                )
                
                cuerpo = cuerpo_template.format(
                    numero_factura=numero_factura,
                    empresa=nombre_empresa,
                    cliente=nombre_cliente,
                    total=f"{total:.2f}",
                    fecha=fecha_actual
                )
                
                agregar_log("Preparando mensaje de email...")
                
                # Crear mensaje
                msg = MIMEMultipart()
                msg['From'] = email_remitente
                msg['To'] = correo_destino
                msg['Subject'] = asunto
                
                # Adjuntar cuerpo del mensaje
                msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))
                
                # Adjuntar PDF
                agregar_log("Adjuntando archivo PDF...")
                with open(ruta_factura, 'rb') as f:
                    attach = MIMEApplication(f.read(), _subtype='pdf')
                    attach.add_header('Content-Disposition', 'attachment', filename=nombre_archivo)
                    msg.attach(attach)
                
                # Enviar email
                agregar_log(f"Conectando a {servidor_smtp}:{puerto}...")
                server = smtplib.SMTP(servidor_smtp, puerto)
                agregar_log("Conexión establecida")
                
                if usar_tls:
                    agregar_log("Iniciando TLS...")
                    server.starttls()
                    agregar_log("TLS activado")
                
                agregar_log("Autenticando con el servidor...")
                server.login(email_remitente, password_app)
                agregar_log("Autenticación exitosa")
                
                agregar_log("Enviando mensaje...")
                server.send_message(msg)
                agregar_log("Mensaje enviado al servidor")
                server.quit()
                agregar_log("Conexión cerrada")
                
                # Éxito - mostrar mensaje final y cerrar
                agregar_log("✅ Factura enviada exitosamente", "info")
                
                # Cambiar el título a éxito
                self.progress_dialog.title = ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=24),
                    ft.Text("Email Enviado Exitosamente", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_600),
                ], spacing=12)
                
                # Cambiar botón a "Cerrar"
                self.progress_dialog.actions = [
                    ft.TextButton("Cerrar", on_click=lambda e: self.page.close(self.progress_dialog)),
                ]
                
                self.progress_dialog.update()
                
                # Cerrar automáticamente después de 2 segundos
                import time
                time.sleep(2)
                self.page.close(self.progress_dialog)
                
                # Mostrar mensaje de éxito en snackbar
                self.mostrar_mensaje_exito(f"Factura enviada a {correo_destino}")
                
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                agregar_log("ERROR: Error de autenticación SMTP", "error")
                agregar_log(f"Detalle: {str(e)}", "error")
                agregar_log("Verifica que:", "error")
                agregar_log("1. El email y contraseña sean correctos", "error")
                agregar_log("2. Si usas Gmail, usa una 'Contraseña de aplicación'", "error")
                agregar_log("3. La verificación en 2 pasos esté activada en Gmail", "error")
                
                # Cambiar título a error
                self.progress_dialog.title = ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=24),
                    ft.Text("Error de Autenticación", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600),
                ], spacing=12)
                
                # Cambiar botón a "Cerrar"
                self.progress_dialog.actions = [
                    ft.TextButton("Cerrar", on_click=lambda e: self.page.close(self.progress_dialog)),
                ]
                self.progress_dialog.update()
                
                return False
                
            except smtplib.SMTPException as e:
                agregar_log(f"ERROR SMTP: {str(e)}", "error")
                
                # Cambiar título a error
                self.progress_dialog.title = ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=24),
                    ft.Text("Error de Envío", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600),
                ], spacing=12)
                
                # Cambiar botón a "Cerrar"
                self.progress_dialog.actions = [
                    ft.TextButton("Cerrar", on_click=lambda e: self.page.close(self.progress_dialog)),
                ]
                self.progress_dialog.update()
                
                return False
                
            except Exception as e:
                agregar_log(f"ERROR inesperado: {str(e)}", "error")
                
                # Cambiar título a error
                self.progress_dialog.title = ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=24),
                    ft.Text("Error Inesperado", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_600),
                ], spacing=12)
                
                # Cambiar botón a "Cerrar"
                self.progress_dialog.actions = [
                    ft.TextButton("Cerrar", on_click=lambda e: self.page.close(self.progress_dialog)),
                ]
                self.progress_dialog.update()
                
                return False
        
        # Ejecutar en un hilo separado
        threading.Thread(target=enviar_email_thread, daemon=True).start()
        
        return True  # Retornar True inmediatamente, el proceso continúa en el hilo

    def _cancelar_envio_email(self, e):
        """Cancela el envío de email"""
        self.page.close(self.progress_dialog)
        self.mostrar_mensaje_info("Envío de email cancelado")

    def eliminar_del_carrito(self, indice):
        if 0 <= indice < len(self.carrito):
            producto_nombre = self.carrito[indice]["producto"]["nombre"]
            self.carrito.pop(indice)
            self.actualizar_vista_carrito()
            self.calcular_total()
            self.mostrar_mensaje_exito(f"Eliminado: {producto_nombre}")

    def abrir_archivo(self, ruta_archivo):
        """Abre un archivo con la aplicación predeterminada del sistema"""
        try:
            import os
            import platform
            import subprocess
            
            ruta_absoluta = os.path.abspath(ruta_archivo)
            print(f"DEBUG: Intentando abrir archivo: {ruta_absoluta}")
            
            if not os.path.exists(ruta_absoluta):
                print(f"ERROR: El archivo no existe: {ruta_absoluta}")
                return False
                
            sistema = platform.system()
            
            if sistema == "Windows":
                os.startfile(ruta_absoluta)
            elif sistema == "Darwin":
                subprocess.run(["open", ruta_absoluta])
            else:
                subprocess.run(["xdg-open", ruta_absoluta])
                
            print("DEBUG: Archivo abierto exitosamente")
            return True
            
        except Exception as e:
            print(f"ERROR: No se pudo abrir el archivo: {e}")
            self.mostrar_mensaje_info(f"Factura generada en: {ruta_archivo}")
            return False

    def limpiar_carrito(self, e=None):
        if self.carrito:
            self.carrito.clear()
            self.actualizar_vista_carrito()
            self.calcular_total()
            self.mostrar_mensaje_exito("Carrito vaciado")
        else:
            self.mostrar_mensaje_info("El carrito ya está vacío")

    def calcular_total(self):
        total = sum(item["producto"]["precio"] * item["cantidad"] for item in self.carrito)
        self.total_text.value = f"Total: ${total:.2f}"
        self.total_text.update()

    def mostrar_mensaje_exito(self, mensaje):
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.WHITE, size=20),
                ft.Text(mensaje, color=ft.Colors.WHITE, size=14)
            ], spacing=10),
            bgcolor=ft.Colors.GREEN_600,
            duration=2500,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def mostrar_mensaje_error(self, mensaje):
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.WHITE, size=20),
                ft.Text(mensaje, color=ft.Colors.WHITE, size=14)
            ], spacing=10),
            bgcolor=ft.Colors.RED_600,
            duration=3500,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def mostrar_mensaje_info(self, mensaje):
        snack = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.WHITE, size=20),
                ft.Text(mensaje, color=ft.Colors.WHITE, size=14)
            ], spacing=10),
            bgcolor=ft.Colors.BLUE_600,
            duration=2500,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()

    def regresar(self, e):
        from empleados.sala_empleados import SalaEmpleados
        self.page.clean()
        SalaEmpleados(self.page, self.nombre_usuario)