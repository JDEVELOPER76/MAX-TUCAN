# compras_window.py  —  Sin SQL_TOOLS, solo sqlite3
import flet as ft
import sqlite3
import datetime
import os


BASEDB = "./BASEDATOS/provedores.db"
os.makedirs(os.path.dirname(BASEDB), exist_ok=True)

# ----------  AYUDANTE: conexión nueva por uso  ----------
def get_conn() -> sqlite3.Connection:
    """Devuelve una conexión nueva para el hilo actual."""
    conn = sqlite3.connect(BASEDB, check_same_thread=False)
    conn.row_factory = sqlite3.Row      # filas tipo dict
    return conn

# ----------  CREAR TABLAS (si no existen)  ----------
def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT NOT NULL,
                contacto    TEXT,
                telefono    TEXT,
                email       TEXT,
                direccion   TEXT,
                activo      INTEGER DEFAULT 1,
                creado_en   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                folio         TEXT UNIQUE,
                fecha         TEXT NOT NULL,
                proveedor_id  INTEGER,
                total         REAL DEFAULT 0,
                estado        TEXT DEFAULT 'Pendiente',
                notas         TEXT,
                creado_en     TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detalle_compras (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id       INTEGER,
                producto        TEXT NOT NULL,
                cantidad        INTEGER DEFAULT 1,
                precio_unitario REAL DEFAULT 0,
                total           REAL DEFAULT 0,
                FOREIGN KEY (compra_id) REFERENCES compras(id)
            )
        """)
        conn.commit()

# =========================  VENTANA PRINCIPAL  =========================
class ComprasWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        page.title = "Compras - MAX TUCAN"

        # ---- tabla ----
        self.compras_data = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Folio", weight=ft.FontWeight.BOLD), numeric=False),
                ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD), numeric=False),
                ft.DataColumn(ft.Text("Proveedor", weight=ft.FontWeight.BOLD), numeric=False),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD), numeric=False),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD), numeric=False),
            ],
            rows=[],
            expand=True,
            column_spacing=100,  # Reduced spacing between columns
            divider_thickness=1,
        )
        
        # ---- cards responsivas ----
        self.compras_cards = ft.Column([], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        # ---- filtros ----
        self.buscar_field = ft.TextField(
            label="Buscar...", prefix_icon=ft.Icons.SEARCH,
            expand=True, on_change=self.buscar_compras
        )
        self.filtro_estado = ft.Dropdown(
            label="Filtrar por estado",
            options=[ft.dropdown.Option(x) for x in ("Todos","Recibido","Parcial","Pendiente")],
            value="Todos", on_change=self.filtrar_compras, expand=True 
        )

        init_db()                       # crear tablas
        self.cargar_compras()           # primera carga

    # ----------------  UI  ----------------
    def build_ui(self):
        # Contenedor de la tabla que se expande completamente
        tabla_container = ft.Container(
            content=ft.Column([
                # Título de la lista (Altura fija)
                ft.Row([
                    ft.Icon(ft.Icons.LIST_ALT, color=ft.Colors.BLUE_700),
                    ft.Text("Lista de Compras", size=20, weight=ft.FontWeight.BOLD),
                ], spacing=10),
                # Separador (Altura fija)
                ft.Divider(height=1, color=ft.Colors.GREY_300),
                # La tabla ocupa todo el espacio disponible
                ft.Container(
                    content=self.compras_data,
                    expand=True,
                    padding=5,  # Reduced padding inside table container
                )
            ], spacing=10, expand=True),  # Reduced spacing between elements
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            padding=15,  # Reduced padding for compact layout
            expand=True,
            margin=ft.margin.all(10),  # Added margin to separate from edges
        )
        
        return ft.Column([
            # Header (Altura fija)
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        on_click=lambda _: self.admin_panel.setup_ui(),
                        tooltip="Volver al Panel", 
                        icon_size=30
                    ),
                    ft.Text("Gestión de Compras", size=28, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Row([
                        ft.ElevatedButton(
                            "Nueva Compra", 
                            icon=ft.Icons.ADD,
                            on_click=self.nueva_compra,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE, 
                                bgcolor=ft.Colors.GREEN_700
                            )
                        ),
                        ft.ElevatedButton(
                            "Proveedores", 
                            icon=ft.Icons.CONTACTS, 
                            on_click=self.abrir_proveedores
                        ),
                    ], spacing=10)  # Reduced spacing between buttons
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=ft.Colors.BLUE_50, 
                padding=15,  # Reduced padding
                border_radius=10
            ),
            
            # Filtros (Altura fija)
            ft.ResponsiveRow([
                ft.Container(content=self.buscar_field, col={"md": 6}, padding=8),  # Reduced padding
                ft.Container(content=self.filtro_estado, col={"md": 4}, padding=8),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Limpiar Filtros", 
                        icon=ft.Icons.CLEAR, 
                        on_click=self.limpiar_filtros
                    ),
                    col={"md": 2}, 
                    padding=8
                ),
            ], expand=False, spacing=8),

            # Tabla (EXPANDIBLE)
            tabla_container,
        ], spacing=15, expand=True, alignment=ft.MainAxisAlignment.START)

    # ----------------  CRUD  ----------------
    def cargar_compras(self, filtro=None, estado=None):
        sql = """
            SELECT c.id, c.folio, c.fecha, c.total, c.estado, c.notas, c.proveedor_id,
                p.nombre as proveedor_nombre
            FROM compras c
            JOIN proveedores p ON p.id = c.proveedor_id
            WHERE 1=1
        """
        params = []
        if filtro:
            sql += " AND (c.folio LIKE ? OR p.nombre LIKE ? OR c.notas LIKE ?)"
            params += [f"%{filtro}%"]*3
        if estado and estado != "Todos":
            sql += " AND c.estado = ?"
            params.append(estado)
        sql += " ORDER BY c.fecha DESC"

        with get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        def color_estado(e):
            return {"Recibido": ft.Colors.GREEN,
                    "Parcial": ft.Colors.ORANGE,
                    "Pendiente": ft.Colors.RED}.get(e, ft.Colors.GREY)

        def botones(r):
            return ft.Row([
                ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    tooltip="Editar",
                    bgcolor=ft.Colors.BLUE_50,
                    icon_color=ft.Colors.BLUE_700,
                    on_click=lambda _: self.editar_compra(r)
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINED,
                    tooltip="Eliminar",
                    bgcolor=ft.Colors.RED_50,
                    icon_color=ft.Colors.RED_700,
                    on_click=lambda _: self.eliminar_compra(r)
                ),
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY_OUTLINED,
                    tooltip="Ver detalles",
                    bgcolor=ft.Colors.GREEN_50,
                    icon_color=ft.Colors.GREEN_700,
                    on_click=lambda _: self.ver_detalles(r)
                ),
            ], spacing=4)  # Increased spacing between buttons aqui antes era 8

        self.compras_data.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Container(content=ft.Text(r["folio"], no_wrap=False), padding=5)),  # Added padding
                ft.DataCell(ft.Container(content=ft.Text(r["fecha"], no_wrap=False), padding=5)),
                ft.DataCell(ft.Container(content=ft.Text(r["proveedor_nombre"], no_wrap=False), padding=5)),
                ft.DataCell(ft.Container(content=ft.Text(f"${r['total']:,.2f}", text_align=ft.TextAlign.RIGHT), padding=5)),
                ft.DataCell(
                    ft.Container(
                        content=ft.Text(r["estado"], color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=color_estado(r["estado"]),

                        border_radius=20, #asntes 20
                        alignment=ft.alignment.center,height=35 ,width=100
                    )
                ),
                ft.DataCell(ft.Container(content=botones(r), padding=5))
            ]) for r in rows
        ]

        self.page.update()

    def buscar_compras(self, _): self.filtrar_compras()
    def filtrar_compras(self, _=None):
        self.cargar_compras(self.buscar_field.value, self.filtro_estado.value)
    def limpiar_filtros(self, _):
        self.buscar_field.value = ""; self.filtro_estado.value = "Todos"
        self.cargar_compras()

    # ----------------  DIALOGOS  ----------------
    def nueva_compra(self, _):
        FormularioCompra(self.page, self)

    def editar_compra(self, row):
        dic = dict(row)
        FormularioCompra(self.page, self, dic)

    def eliminar_compra(self, row):
        def confirmar(_):
            try:
                with get_conn() as conn:
                    conn.execute("DELETE FROM detalle_compras WHERE compra_id = ?", [row["id"]])
                    conn.execute("DELETE FROM compras WHERE id = ?", [row["id"]])
                    conn.commit()
                self.cargar_compras()
                self.page.close(dlg)
                self.mostrar_mensaje("Compra eliminada", ft.Colors.GREEN)
            except Exception as ex:
                self.mostrar_mensaje(f"Error: {ex}", ft.Colors.RED)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Eliminar compra {row['folio']}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dlg)),
                ft.TextButton("Eliminar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)

    def ver_detalles(self, row):
        with get_conn() as conn:
            detalles = conn.execute(
                "SELECT producto,cantidad,precio_unitario,total FROM detalle_compras WHERE compra_id = ?",
                [row["id"]]
            ).fetchall()
            prov = conn.execute("SELECT nombre FROM proveedores WHERE id = ?", [row["proveedor_id"]]).fetchone()
        prov_nombre = prov["nombre"] if prov else "Desconocido"

        dlg = ft.AlertDialog(
            title=ft.Text(f"Detalles de Compra: {row['folio']}"),
            content=ft.Column([
                ft.Text(f"Proveedor: {prov_nombre}"),
                ft.Text(f"Fecha: {row['fecha']}"),
                ft.Text(f"Estado: {row['estado']}"),
                ft.Text(f"Total: ${row['total']:,.2f}"),
                ft.Divider(),
                ft.Text("Productos:", weight=ft.FontWeight.BOLD),
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Producto")),
                        ft.DataColumn(ft.Text("Cantidad")),
                        ft.DataColumn(ft.Text("P. Unitario")),
                        ft.DataColumn(ft.Text("Total")),
                    ],
                    rows=[ft.DataRow(cells=[
                        ft.DataCell(ft.Text(d["producto"])),
                        ft.DataCell(ft.Text(str(d["cantidad"]))),
                        ft.DataCell(ft.Text(f"${d['precio_unitario']:,.2f}")),
                        ft.DataCell(ft.Text(f"${d['total']:,.2f}")),
                    ]) for d in detalles],
                    column_spacing=20,  # Added spacing for detail table
                ) if detalles else ft.Text("Sin productos")
            ], tight=True, spacing=15),  # Increased spacing in dialog
            actions=[ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dlg))]
        )
        self.page.open(dlg)

    def abrir_proveedores(self, _):
        VentanaProveedores(self.page, self)

    def mostrar_mensaje(self, txt, color=ft.Colors.GREEN):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(txt), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

# =========================  FORMULARIO COMPRA  =========================
class FormularioCompra:
    def __init__(self, page: ft.Page, win, compra=None):
        self.page = page
        self.win = win
        self.es_edit = compra is not None
        self.compra_id = compra["id"] if compra else None

        # campos
        self.prov_dd = ft.Dropdown(label="Proveedor", options=[], expand=True)
        self.est_dd = ft.Dropdown(label="Estado", options=[
            ft.dropdown.Option("Pendiente"),
            ft.dropdown.Option("Parcial"),
            ft.dropdown.Option("Recibido"),
        ], value="Pendiente" if not compra else compra["estado"], expand=True)
        self.notas = ft.TextField(label="Notas", multiline=True, expand=True)

        self.productos = []
        self.lista_prod = ft.Column(expand=True)

        self.txt_prod = ft.TextField(label="Producto", expand=True)
        self.txt_cant = ft.TextField(label="Cantidad", value="1", expand=True)
        self.txt_pu = ft.TextField(label="Precio Unitario", expand=True)
        self.total_lbl = ft.Text("Total: $0.00", size=16, weight=ft.FontWeight.BOLD)

        self.cargar_proveedores()
        if self.es_edit:
            self.cargar_existente()
        self.construir_dialog()
        self.actualizar_total()

    # ----------  helpers  ----------
    def cargar_proveedores(self):
        with get_conn() as conn:
            rows = conn.execute("SELECT id, nombre FROM proveedores WHERE activo = 1 ORDER BY nombre").fetchall()
        self.prov_dd.options = [ft.dropdown.Option(text=r["nombre"], key=str(r["id"])) for r in rows]
        if self.es_edit:
            with get_conn() as conn:
                compra_data = conn.execute("SELECT proveedor_id FROM compras WHERE id = ?", [self.compra_id]).fetchone()
                if compra_data:
                    self.prov_dd.value = str(compra_data["proveedor_id"])
        self.page.update()

    def cargar_existente(self):
        with get_conn() as conn:
            compra_data = conn.execute("SELECT notas FROM compras WHERE id = ?", [self.compra_id]).fetchone()
            self.notas.value = compra_data["notas"] or "" if compra_data else ""
            self.productos = [
                dict(r)
                for r in conn.execute(
                    "SELECT producto,cantidad,precio_unitario,total FROM detalle_compras WHERE compra_id = ?",
                    [self.compra_id]
                ).fetchall()
            ]
        self.actualizar_lista_prod()

    # ----------  UI  ----------
    def construir_dialog(self):
        content = ft.Container(
            content=ft.ResponsiveRow([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Editar Compra" if self.es_edit else "Nueva Compra", size=20, weight=ft.FontWeight.BOLD),
                        ft.ResponsiveRow([
                            ft.Container(content=self.prov_dd, col=6, padding=5),  # Added padding
                            ft.Container(content=self.est_dd, col=6, padding=5),
                        ], spacing=10),
                        self.notas,
                    ], spacing=15), col=12  # Increased spacing
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Productos de la Compra", size=16, weight=ft.FontWeight.BOLD),
                        ft.ResponsiveRow([
                            ft.Container(content=self.txt_prod, col=4, padding=5),
                            ft.Container(content=self.txt_cant, col=2, padding=5),
                            ft.Container(content=self.txt_pu, col=3, padding=5),
                            ft.Container(
                                content=ft.ElevatedButton("Agregar Producto", icon=ft.Icons.ADD, on_click=self.agregar_producto),
                                col=3, padding=5
                            ),
                        ], spacing=10),
                        ft.Container(
                            content=ft.Column([ft.Text("Lista de Productos:", weight=ft.FontWeight.BOLD), self.lista_prod], spacing=10),
                            height=200, border=ft.border.all(1, ft.Colors.GREY_300), padding=15, border_radius=5  # Increased padding
                        ),
                        ft.Row([self.total_lbl], spacing=10)
                    ], spacing=15), col=12  # Increased spacing
                )
            ], spacing=20),
            width=800, padding=20
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Gestión de Compra"),
            content=content,
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar),
                ft.TextButton("Guardar", on_click=self.guardar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(self.dialog)

    # ----------  lógica  ----------
    def agregar_producto(self, _):
        prod = self.txt_prod.value.strip()
        try:
            cant = int(self.txt_cant.value or 1)
            pu = float(self.txt_pu.value or 0)
            total = cant * pu
            if prod and cant > 0 and pu >= 0:
                self.productos.append({'producto': prod, 'cantidad': cant, 'precio_unitario': pu, 'total': total})
                self.txt_prod.value = ""
                self.txt_cant.value = "1"
                self.txt_pu.value = ""
                self.actualizar_lista_prod()
                self.actualizar_total()
            else:
                self.mostrar_error("Datos del producto inválidos")
        except ValueError:
            self.mostrar_error("Cantidad y precio deben ser números válidos")

    def actualizar_lista_prod(self):
        self.lista_prod.controls = []
        for i, p in enumerate(self.productos):
            self.lista_prod.controls.append(
                ft.Row([
                    ft.Text(f"{p['producto']} ({p['cantidad']} x ${p['precio_unitario']:.2f})"),
                    ft.Text(f"${p['total']:.2f}", weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, icon_size=20,
                                  on_click=lambda _, idx=i: self.eliminar_producto(idx))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=10)
            )
        self.page.update()

    def eliminar_producto(self, idx):
        if 0 <= idx < len(self.productos):
            self.productos.pop(idx)
            self.actualizar_lista_prod()
            self.actualizar_total()

    def actualizar_total(self):
        self.total_lbl.value = f"Total: ${sum(p['total'] for p in self.productos):,.2f}"
        self.page.update()

    def guardar(self, _):
        if not self.prov_dd.value:
            self.mostrar_error("Seleccione proveedor")
            return
        if not self.productos:
            self.mostrar_error("Agregue al menos un producto")
            return
        try:
            total = sum(p['total'] for p in self.productos)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            datos = {
                'proveedor_id': int(self.prov_dd.value),
                'fecha': fecha,
                'total': total,
                'estado': self.est_dd.value,
                'notas': self.notas.value
            }
            with get_conn() as conn:
                if self.es_edit:
                    conn.execute(
                        "UPDATE compras SET proveedor_id=?, fecha=?, total=?, estado=?, notas=? WHERE id=?",
                        [datos['proveedor_id'], datos['fecha'], datos['total'], datos['estado'], datos['notas'], self.compra_id]
                    )
                    compra_id = self.compra_id
                    conn.execute("DELETE FROM detalle_compras WHERE compra_id=?", [compra_id])
                else:
                    ult = conn.execute("SELECT id FROM compras ORDER BY id DESC LIMIT 1").fetchone()
                    nro = (ult["id"] + 1) if ult else 1
                    datos['folio'] = f"C-{nro:04d}"
                    cur = conn.execute(
                        "INSERT INTO compras (proveedor_id, fecha, total, estado, notas, folio) VALUES (?,?,?,?,?,?)",
                        [datos['proveedor_id'], datos['fecha'], datos['total'], datos['estado'], datos['notas'], datos['folio']]
                    )
                    compra_id = cur.lastrowid

                for pr in self.productos:
                    conn.execute(
                        "INSERT INTO detalle_compras (compra_id, producto, cantidad, precio_unitario, total) VALUES (?,?,?,?,?)",
                        [compra_id, pr['producto'], pr['cantidad'], pr['precio_unitario'], pr['total']]
                    )
                conn.commit()

            self.win.cargar_compras()
            self.page.close(self.dialog)
            self.win.mostrar_mensaje("Compra guardada!")
        except Exception as ex:
            self.mostrar_error(f"Error al guardar: {ex}")

    def mostrar_error(self, txt):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(txt), bgcolor=ft.Colors.RED)
        self.page.snack_bar.open = True
        self.page.update()

    def cerrar(self, _):
        self.page.close(self.dialog)

# =========================  VENTANA PROVEEDORES  =========================
class VentanaProveedores:
    def __init__(self, page: ft.Page, win):
        self.page = page
        self.win = win
        self.items_por_pagina = 10
        self.offset_actual = 0
        self.total_proveedores = 0
        self.todos_cargados = False
        
        # Contenedor scrollable para los proveedores
        self.lista_proveedores = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            on_scroll=self.detectar_final_scroll,
            spacing=8
        )
        
        self.construir_dialog()
        self.cargar_primera_pagina()

    def construir_dialog(self):
        content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Gestión de Proveedores", size=20, weight=ft.FontWeight.BOLD, expand=True),
                    ft.ElevatedButton("Nuevo Proveedor", icon=ft.Icons.ADD, on_click=self.nuevo_prov)
                ], spacing=15),
                ft.Container(content=self.lista_proveedores, expand=True, padding=10)
            ], expand=True, spacing=15),
            width=800, height=500, padding=20
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Proveedores"),
            content=content,
            actions=[ft.TextButton("Cerrar", on_click=self.cerrar)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(self.dialog)

    def detectar_final_scroll(self, e):
        """Se ejecuta cuando el usuario scrollea"""
        try:
            # Si no están todos cargados, cargar más cuando scrollea
            if not self.todos_cargados:
                self.cargar_mas_proveedores()
        except Exception as ex:
            pass

    def cargar_primera_pagina(self):
        """Carga los primeros 10 proveedores"""
        with get_conn() as conn:
            # Obtener total de proveedores
            total = conn.execute("SELECT COUNT(*) as cnt FROM proveedores").fetchone()
            self.total_proveedores = total["cnt"] if total else 0
            
            # Cargar primeros 10
            rows = conn.execute(
                f"SELECT * FROM proveedores ORDER BY nombre LIMIT {self.items_por_pagina}"
            ).fetchall()
        
        self.lista_proveedores.controls.clear()
        self.offset_actual = len(rows)
        
        # Verificar si ya están todos cargados
        if len(rows) < self.items_por_pagina:
            self.todos_cargados = True
        
        for r in rows:
            self.lista_proveedores.controls.append(self._crear_fila_proveedor(r))
        
        self.page.update()

    def cargar_mas_proveedores(self):
        """Carga los siguientes 10 proveedores cuando se scrollea al final"""
        with get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM proveedores ORDER BY nombre LIMIT {self.items_por_pagina} OFFSET {self.offset_actual}"
            ).fetchall()
        
        if not rows:
            self.todos_cargados = True
            return
        
        # Agregar nuevos proveedores a la lista
        for r in rows:
            self.lista_proveedores.controls.append(self._crear_fila_proveedor(r))
        
        self.offset_actual += len(rows)
        
        # Si la cantidad de registros cargados es menor que items_por_pagina, ya no hay más
        if len(rows) < self.items_por_pagina:
            self.todos_cargados = True
        
        self.page.update()

    def _crear_fila_proveedor(self, r):
        """Crea una fila de proveedor con estilo de tabla"""
        return ft.Container(
            content=ft.Row([
                ft.Text(r["nombre"], size=12, expand=True),
                ft.Text(r["contacto"] or "", size=12, expand=True),
                ft.Text(r["telefono"] or "", size=12, expand=True),
                ft.Text(r["email"] or "", size=12, expand=True),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, icon_color=ft.Colors.BLUE,
                                  tooltip="Editar", on_click=lambda _, rr=r: self.editar_prov(rr)),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED,
                                  tooltip="Eliminar", on_click=lambda _, rr=r: self.eliminar_prov(rr)),
                ], spacing=0, tight=True),
            ], spacing=15, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
            padding=10
        )

    def nuevo_prov(self, _):
        self.abrir_formulario()

    def editar_prov(self, row):
        self.abrir_formulario(row)

    def eliminar_prov(self, row):
        def confirmar(_):
            try:
                with get_conn() as conn:
                    conn.execute("DELETE FROM proveedores WHERE id=?", [row["id"]])
                    conn.commit()
                self.cargar_primera_pagina()  # Recarga la lista
                self.page.close(dlg)
                self.win.mostrar_mensaje("Proveedor eliminado")
            except Exception as ex:
                self.win.mostrar_mensaje(f"Error: {ex}", ft.Colors.RED)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(f"¿Eliminar proveedor {row['nombre']}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.close(dlg)),
                ft.TextButton("Eliminar", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)

    def abrir_formulario(self, prov=None):
        FormularioProveedor(self.page, self, prov)

    def cerrar(self, _):
        self.page.close(self.dialog)

# =========================  FORMULARIO PROVEEDOR  =========================
class FormularioProveedor:
    def __init__(self, page: ft.Page, win, prov=None):
        self.page = page
        self.win = win
        self.es_edit = prov is not None
        self.prov_id = prov["id"] if prov else None

        self.nombre = ft.TextField(label="Nombre", expand=True)
        self.contacto = ft.TextField(label="Contacto", expand=True)
        self.tel = ft.TextField(label="Teléfono", expand=True)
        self.email = ft.TextField(label="Email", expand=True)
        self.dir = ft.TextField(label="Dirección", multiline=True, expand=True)

        if prov:
            self.cargar_datos(prov)
        self.construir_dialog()
        self.page.open(self.dialog)

    def cargar_datos(self, prov):
        self.nombre.value = prov["nombre"]
        self.contacto.value = prov["contacto"] or ""
        self.tel.value = prov["telefono"] or ""
        self.email.value = prov["email"] or ""
        self.dir.value = prov["direccion"] or ""

    def construir_dialog(self):
        content = ft.Container(
            content=ft.ResponsiveRow([
                ft.Container(content=self.nombre, col=12, padding=5),  # Added padding
                ft.Container(content=self.contacto, col=6, padding=5),
                ft.Container(content=self.tel, col=6, padding=5),
                ft.Container(content=self.email, col=12, padding=5),
                ft.Container(content=self.dir, col=12, padding=5),
            ], spacing=15),  # Increased spacing
            width=500, padding=20
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Proveedor" if self.es_edit else "Nuevo Proveedor"),
            content=content,
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar),
                ft.TextButton("Guardar", on_click=self.guardar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def guardar(self, _):
        if not self.nombre.value.strip():
            self.mostrar_error("El nombre es obligatorio")
            return
        data = {
            "nombre": self.nombre.value,
            "contacto": self.contacto.value,
            "telefono": self.tel.value,
            "email": self.email.value,
            "direccion": self.dir.value,
            "activo": 1
        }
        try:
            with get_conn() as conn:
                if self.es_edit:
                    conn.execute(
                        """UPDATE proveedores
                           SET nombre=?, contacto=?, telefono=?, email=?, direccion=?
                           WHERE id=?""",
                        [data["nombre"], data["contacto"], data["telefono"], data["email"], data["direccion"], self.prov_id]
                    )
                else:
                    conn.execute(
                        """INSERT INTO proveedores (nombre,contacto,telefono,email,direccion,activo)
                           VALUES (?,?,?,?,?,1)""",
                        [data["nombre"], data["contacto"], data["telefono"], data["email"], data["direccion"]]
                    )
                conn.commit()
            self.win.cargar_primera_pagina()
            self.page.close(self.dialog)
            self.win.win.mostrar_mensaje("Proveedor guardado!")
        except Exception as ex:
            self.mostrar_error(f"Error al guardar: {ex}")

    def mostrar_error(self, txt):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(txt), bgcolor=ft.Colors.RED)
        self.page.snack_bar.open = True
        self.page.update()

    def cerrar(self, _):
        self.page.close(self.dialog)