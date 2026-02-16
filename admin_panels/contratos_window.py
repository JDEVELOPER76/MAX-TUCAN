# contratos_window.py – Gestión de contratos de empleados
import flet as ft
from BuilderSql.contratos_builder import ContratosBuilder
from datetime import datetime


class ContratosWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        self.page.title = "Contratos - MAX TUCAN"
        self.page.bgcolor = "#f3f4f6"
        self.page.padding = 0
        self.page.spacing = 0
        self.page.window_maximized = True
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        
        # Inicializar base de datos
        ContratosBuilder.inicializar_bd()
        
        self.page.clean()
        self.page.add(self.build_ui())
        self.page.update()

    # -----------------  INTERFAZ PRINCIPAL -----------------
    def build_ui(self):
        self.tabla_contratos = self._crear_tabla_contratos()

        # HEADER - parte superior fija
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW,
                    on_click=self.regresar_panel_admin,
                    tooltip="Volver",
                    icon_color="#6366f1"
                ),
                ft.Text("Gestión de Contratos",
                        size=28, weight=ft.FontWeight.BOLD,
                        color="#1e293b"),
                ft.ElevatedButton(
                    "Nuevo Contrato",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=self.nuevo_contrato,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor="#6366f1",
                        shape=ft.RoundedRectangleBorder(radius=10),
                        padding=ft.padding.symmetric(horizontal=18, vertical=14)
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            bgcolor="#ffffff",
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=8,
                color=ft.Colors.with_opacity(0.1, "#000000"),
                offset=ft.Offset(0, 2)
            )
        )

        # BARRA DE BÚSQUEDA Y FILTROS
        self.campo_busqueda = ft.TextField(
            hint_text="Buscar por nombre o puesto...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            on_change=self.buscar_contratos,
            expand=True
        )

        self.filtro_estado = ft.Dropdown(
            label="Filtrar por estado",
            options=[
                ft.dropdown.Option("Todos"),
                ft.dropdown.Option("Activo"),
                ft.dropdown.Option("Finalizado")
            ],
            value="Todos",
            width=200,
            on_change=self.filtrar_por_estado
        )

        barra_busqueda = ft.Container(
            content=ft.Row([
                self.campo_busqueda,
                self.filtro_estado
            ], spacing=15),
            padding=ft.padding.all(20),
            bgcolor="#ffffff",
            margin=ft.margin.only(top=10),
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=4,
                color=ft.Colors.with_opacity(0.05, "#000000")
            )
        )

        # CONTENEDOR PRINCIPAL CON SCROLL
        contenedor_principal = ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=ft.Column([
                        barra_busqueda,
                        self.tabla_contratos
                    ], spacing=0),
                    padding=ft.padding.symmetric(horizontal=30),
                    expand=True
                )
            ], spacing=0, scroll=ft.ScrollMode.AUTO),
            expand=True
        )

        return contenedor_principal

    # -----------------  TABLA DE CONTRATOS -----------------
    def _crear_tabla_contratos(self):
        """Crea la tabla con todos los contratos"""
        contratos = ContratosBuilder.listar_contratos()
        
        filas = []
        for contrato in contratos:
            estado_color = "#10b981" if contrato['estado'] == 'Activo' else "#ef4444"
            estado_bg = "#d1fae5" if contrato['estado'] == 'Activo' else "#fee2e2"
            
            fila = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(contrato['id']), size=14)),
                    ft.DataCell(ft.Text(contrato['nombre_empleado'], size=14, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(contrato['puesto'], size=14)),
                    ft.DataCell(ft.Text(contrato['fecha_inicio'], size=14)),
                    ft.DataCell(ft.Text(f"${contrato['salario']:,.2f}", size=14)),
                    ft.DataCell(ft.Text(contrato['frecuencia_pago'], size=14)),
                    ft.DataCell(ft.Text(contrato['tipo_contrato'], size=14)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(contrato['estado'], size=12, color=estado_color, weight=ft.FontWeight.BOLD),
                            bgcolor=estado_bg,
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=12
                        )
                    ),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color="#3b82f6",
                                tooltip="Editar",
                                on_click=lambda e, c=contrato: self.editar_contrato(e, c)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color="#ef4444",
                                tooltip="Eliminar",
                                on_click=lambda e, c=contrato: self.eliminar_contrato(e, c)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.INFO_OUTLINED,
                                icon_color="#8b5cf6",
                                tooltip="Ver detalles",
                                on_click=lambda e, c=contrato: self.ver_detalles(e, c)
                            )
                        ], spacing=5)
                    )
                ]
            )
            filas.append(fila)

        tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Empleado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Puesto", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha Inicio", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Salario", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Frecuencia Pago", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tipo Contrato", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
            ],
            rows=filas,
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
            horizontal_lines=ft.border.BorderSide(1, "#f1f5f9"),
            heading_row_color="#f8fafc",
            heading_row_height=50,
            data_row_min_height=60,
        )

        return ft.Container(
            content=ft.Column([tabla], scroll=ft.ScrollMode.ALWAYS),
            bgcolor="#ffffff",
            padding=20,
            margin=ft.margin.only(top=10),
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=4,
                color=ft.Colors.with_opacity(0.05, "#000000")
            )
        )

    # -----------------  ACTUALIZAR TABLA -----------------
    def actualizar_tabla(self):
        """Recarga la tabla de contratos"""
        nuevo_contenido = self.build_ui()
        self.page.clean()
        self.page.add(nuevo_contenido)
        self.page.update()

    # -----------------  NUEVO CONTRATO -----------------
    def nuevo_contrato(self, e):
        """Abre el diálogo para crear un nuevo contrato"""
        # Campos del formulario
        nombre_field = ft.TextField(label="Nombre del Empleado", autofocus=True)
        puesto_field = ft.TextField(label="Puesto/Cargo")
        fecha_inicio_field = ft.TextField(
            label="Fecha de Inicio",
            hint_text="AAAA-MM-DD",
            value=datetime.now().strftime("%Y-%m-%d")
        )
        salario_field = ft.TextField(label="Salario", keyboard_type=ft.KeyboardType.NUMBER)
        
        frecuencia_dropdown = ft.Dropdown(
            label="Frecuencia de Pago",
            options=[
                ft.dropdown.Option("Semanal"),
                ft.dropdown.Option("Quincenal"),
                ft.dropdown.Option("Mensual")
            ],
            value="Mensual"
        )
        
        tipo_dropdown = ft.Dropdown(
            label="Tipo de Contrato",
            options=[
                ft.dropdown.Option("Indefinido"),
                ft.dropdown.Option("Temporal"),
                ft.dropdown.Option("Por Proyecto"),
                ft.dropdown.Option("Freelance")
            ],
            value="Indefinido"
        )
        
        notas_field = ft.TextField(
            label="Notas adicionales",
            multiline=True,
            min_lines=3,
            max_lines=5
        )

        def guardar_contrato(e):
            if not nombre_field.value or not puesto_field.value or not salario_field.value:
                self.mostrar_mensaje("Error", "Por favor completa todos los campos obligatorios", ft.Icons.ERROR, "#ef4444")
                return
            
            try:
                salario = float(salario_field.value)
            except ValueError:
                self.mostrar_mensaje("Error", "El salario debe ser un número válido", ft.Icons.ERROR, "#ef4444")
                return
            
            datos = {
                'nombre_empleado': nombre_field.value,
                'puesto': puesto_field.value,
                'fecha_inicio': fecha_inicio_field.value,
                'salario': salario,
                'frecuencia_pago': frecuencia_dropdown.value,
                'tipo_contrato': tipo_dropdown.value,
                'estado': 'Activo',
                'notas': notas_field.value
            }
            
            if ContratosBuilder.crear_contrato(datos):
                self.mostrar_mensaje("Éxito", "Contrato creado exitosamente", ft.Icons.CHECK_CIRCLE, "#10b981")
                self.page.close(dialog)
                self.actualizar_tabla()
            else:
                self.mostrar_mensaje("Error", "No se pudo crear el contrato", ft.Icons.ERROR, "#ef4444")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nuevo Contrato", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    puesto_field,
                    fecha_inicio_field,
                    salario_field,
                    frecuencia_dropdown,
                    tipo_dropdown,
                    notas_field
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=500
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Guardar", on_click=guardar_contrato,
                                style=ft.ButtonStyle(bgcolor="#6366f1", color=ft.Colors.WHITE))
            ]
        )
        
        self.page.open(dialog)

    # -----------------  EDITAR CONTRATO -----------------
    def editar_contrato(self, e, contrato):
        """Abre el diálogo para editar un contrato existente"""
        nombre_field = ft.TextField(label="Nombre del Empleado", value=contrato['nombre_empleado'])
        puesto_field = ft.TextField(label="Puesto/Cargo", value=contrato['puesto'])
        fecha_inicio_field = ft.TextField(label="Fecha de Inicio", value=contrato['fecha_inicio'])
        salario_field = ft.TextField(label="Salario", value=str(contrato['salario']))
        
        frecuencia_dropdown = ft.Dropdown(
            label="Frecuencia de Pago",
            options=[
                ft.dropdown.Option("Semanal"),
                ft.dropdown.Option("Quincenal"),
                ft.dropdown.Option("Mensual")
            ],
            value=contrato['frecuencia_pago']
        )
        
        tipo_dropdown = ft.Dropdown(
            label="Tipo de Contrato",
            options=[
                ft.dropdown.Option("Indefinido"),
                ft.dropdown.Option("Temporal"),
                ft.dropdown.Option("Por Proyecto"),
                ft.dropdown.Option("Freelance")
            ],
            value=contrato['tipo_contrato']
        )
        
        estado_dropdown = ft.Dropdown(
            label="Estado",
            options=[
                ft.dropdown.Option("Activo"),
                ft.dropdown.Option("Finalizado")
            ],
            value=contrato['estado']
        )
        
        notas_field = ft.TextField(
            label="Notas adicionales",
            value=contrato.get('notas', ''),
            multiline=True,
            min_lines=3,
            max_lines=5
        )

        def actualizar_contrato(e):
            if not nombre_field.value or not puesto_field.value or not salario_field.value:
                self.mostrar_mensaje("Error", "Por favor completa todos los campos obligatorios", ft.Icons.ERROR, "#ef4444")
                return
            
            try:
                salario = float(salario_field.value)
            except ValueError:
                self.mostrar_mensaje("Error", "El salario debe ser un número válido", ft.Icons.ERROR, "#ef4444")
                return
            
            datos = {
                'nombre_empleado': nombre_field.value,
                'puesto': puesto_field.value,
                'fecha_inicio': fecha_inicio_field.value,
                'salario': salario,
                'frecuencia_pago': frecuencia_dropdown.value,
                'tipo_contrato': tipo_dropdown.value,
                'estado': estado_dropdown.value,
                'notas': notas_field.value
            }
            
            if ContratosBuilder.actualizar_contrato(contrato['id'], datos):
                self.mostrar_mensaje("Éxito", "Contrato actualizado exitosamente", ft.Icons.CHECK_CIRCLE, "#10b981")
                self.page.close(dialog)
                self.actualizar_tabla()
            else:
                self.mostrar_mensaje("Error", "No se pudo actualizar el contrato", ft.Icons.ERROR, "#ef4444")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Contrato", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    nombre_field,
                    puesto_field,
                    fecha_inicio_field,
                    salario_field,
                    frecuencia_dropdown,
                    tipo_dropdown,
                    estado_dropdown,
                    notas_field
                ], spacing=15, scroll=ft.ScrollMode.AUTO),
                width=500,
                height=550
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Actualizar", on_click=actualizar_contrato,
                                style=ft.ButtonStyle(bgcolor="#6366f1", color=ft.Colors.WHITE))
            ]
        )
        
        self.page.open(dialog)

    # -----------------  ELIMINAR CONTRATO -----------------
    def eliminar_contrato(self, e, contrato):
        """Abre el diálogo de confirmación para eliminar un contrato"""
        def confirmar_eliminacion(e):
            if ContratosBuilder.eliminar_contrato(contrato['id']):
                self.mostrar_mensaje("Éxito", "Contrato eliminado exitosamente", ft.Icons.CHECK_CIRCLE, "#10b981")
                self.page.close(dialog)
                self.actualizar_tabla()
            else:
                self.mostrar_mensaje("Error", "No se pudo eliminar el contrato", ft.Icons.ERROR, "#ef4444")

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación", weight=ft.FontWeight.BOLD),
            content=ft.Text(f"¿Estás seguro de eliminar el contrato de {contrato['nombre_empleado']}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dialog)),
                ft.ElevatedButton("Eliminar", on_click=confirmar_eliminacion,
                                style=ft.ButtonStyle(bgcolor="#ef4444", color=ft.Colors.WHITE))
            ]
        )
        
        self.page.open(dialog)

    # -----------------  VER DETALLES -----------------
    def ver_detalles(self, e, contrato):
        """Muestra los detalles completos de un contrato"""
        detalles = ft.Column([
            ft.Row([
                ft.Text("ID:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(str(contrato['id']))
            ]),
            ft.Row([
                ft.Text("Empleado:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['nombre_empleado'])
            ]),
            ft.Row([
                ft.Text("Puesto:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['puesto'])
            ]),
            ft.Row([
                ft.Text("Fecha Inicio:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['fecha_inicio'])
            ]),
            ft.Row([
                ft.Text("Salario:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(f"${contrato['salario']:,.2f}")
            ]),
            ft.Row([
                ft.Text("Frecuencia Pago:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['frecuencia_pago'])
            ]),
            ft.Row([
                ft.Text("Tipo Contrato:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['tipo_contrato'])
            ]),
            ft.Row([
                ft.Text("Estado:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['estado'])
            ]),
            ft.Row([
                ft.Text("Fecha Fin:", weight=ft.FontWeight.BOLD, width=150),
                ft.Text(contrato['fecha_fin'] if contrato['fecha_fin'] else "N/A")
            ]),
            ft.Divider(),
            ft.Text("Notas:", weight=ft.FontWeight.BOLD),
            ft.Text(contrato.get('notas', 'Sin notas'), italic=True),
            ft.Divider(),
            ft.Row([
                ft.Text("Fecha Creación:", weight=ft.FontWeight.BOLD, size=12),
                ft.Text(contrato['fecha_creacion'], size=12)
            ]),
            ft.Row([
                ft.Text("Última Modificación:", weight=ft.FontWeight.BOLD, size=12),
                ft.Text(contrato['fecha_modificacion'] if contrato['fecha_modificacion'] else "N/A", size=12)
            ])
        ], spacing=10)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalles del Contrato", weight=ft.FontWeight.BOLD),
            content=ft.Container(content=detalles, width=500),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dialog))
            ]
        )
        
        self.page.open(dialog)

    # -----------------  BÚSQUEDA Y FILTROS -----------------
    def buscar_contratos(self, e):
        """Busca contratos por nombre o puesto"""
        termino = self.campo_busqueda.value.strip()
        
        if termino:
            contratos = ContratosBuilder.buscar_contratos(termino)
        else:
            # Si el filtro está activo, aplicarlo
            if self.filtro_estado.value != "Todos":
                contratos = ContratosBuilder.listar_contratos(self.filtro_estado.value)
            else:
                contratos = ContratosBuilder.listar_contratos()
        
        self._actualizar_tabla_con_datos(contratos)

    def filtrar_por_estado(self, e):
        """Filtra los contratos por estado"""
        estado = self.filtro_estado.value
        
        if estado == "Todos":
            contratos = ContratosBuilder.listar_contratos()
        else:
            contratos = ContratosBuilder.listar_contratos(estado)
        
        self._actualizar_tabla_con_datos(contratos)

    def _actualizar_tabla_con_datos(self, contratos):
        """Actualiza la tabla con datos específicos"""
        filas = []
        for contrato in contratos:
            estado_color = "#10b981" if contrato['estado'] == 'Activo' else "#ef4444"
            estado_bg = "#d1fae5" if contrato['estado'] == 'Activo' else "#fee2e2"
            
            fila = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(contrato['id']), size=14)),
                    ft.DataCell(ft.Text(contrato['nombre_empleado'], size=14, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(contrato['puesto'], size=14)),
                    ft.DataCell(ft.Text(contrato['fecha_inicio'], size=14)),
                    ft.DataCell(ft.Text(f"${contrato['salario']:,.2f}", size=14)),
                    ft.DataCell(ft.Text(contrato['frecuencia_pago'], size=14)),
                    ft.DataCell(ft.Text(contrato['tipo_contrato'], size=14)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(contrato['estado'], size=12, color=estado_color, weight=ft.FontWeight.BOLD),
                            bgcolor=estado_bg,
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=12
                        )
                    ),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color="#3b82f6",
                                tooltip="Editar",
                                on_click=lambda e, c=contrato: self.editar_contrato(e, c)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color="#ef4444",
                                tooltip="Eliminar",
                                on_click=lambda e, c=contrato: self.eliminar_contrato(e, c)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.INFO_OUTLINED,
                                icon_color="#8b5cf6",
                                tooltip="Ver detalles",
                                on_click=lambda e, c=contrato: self.ver_detalles(e, c)
                            )
                        ], spacing=5)
                    )
                ]
            )
            filas.append(fila)

        self.tabla_contratos.content.controls[0].rows = filas
        self.page.update()

    # -----------------  UTILIDADES -----------------
    def mostrar_mensaje(self, titulo, mensaje, icono, color):
        """Muestra un mensaje temporal"""
        snackbar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(icono, color=color),
                ft.Text(mensaje, color=color)
            ]),
            bgcolor="#ffffff",
            duration=3000
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()

    def regresar_panel_admin(self, e):
        """Regresa al panel de administración"""
        from admin_panels.admin_panel import AdminPanel
        self.page.clean()
        AdminPanel(self.page, self.admin_panel.nombre_usuario if hasattr(self.admin_panel, 'nombre_usuario') else "Administrador")
        self.page.update()
