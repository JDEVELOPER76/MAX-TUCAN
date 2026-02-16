import flet as ft
from datetime import datetime, timedelta
from pathlib import Path
from BASEDATOS import db


class AuditoriaWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        self.registros = []
        self.filtro_tipo = "todos"
        self.filtro_usuario = ""
        
    def build_ui(self):
        # Header
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_size=24,
                        icon_color="#4f46e5",
                        tooltip="Volver al panel",
                        on_click=lambda _: self._volver_panel()
                    ),
                    ft.Container(
                        content=ft.Icon(ft.Icons.ASSESSMENT_ROUNDED, size=28, color=ft.Colors.WHITE),
                        bgcolor="#4f46e5",
                        border_radius=12,
                        padding=10,
                    ),
                    ft.Text("Auditoría del Sistema", size=24, weight=ft.FontWeight.BOLD, color="#1e293b"),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Exportar PDF",
                        icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                        on_click=lambda _: self._exportar_pdf(),
                        bgcolor="#10b981",
                        color=ft.Colors.WHITE,
                    ),
                    ft.ElevatedButton(
                        "Eliminar Registros",
                        icon=ft.Icons.DELETE_ROUNDED,
                        on_click=lambda _: self._mostrar_dialogo_eliminar(),
                        bgcolor="#ef4444",
                        color=ft.Colors.WHITE,
                    ),
                    ft.ElevatedButton(
                        "Actualizar",
                        icon=ft.Icons.REFRESH_ROUNDED,
                        on_click=lambda _: self._cargar_registros(),
                        bgcolor="#4f46e5",
                        color=ft.Colors.WHITE,
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=20),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
        
        # Filtros
        self.filtro_tipo_dropdown = ft.Dropdown(
            label="Tipo de Evento",
            value="todos",
            options=[
                ft.dropdown.Option("todos", "Todos"),
                ft.dropdown.Option("login", "Inicio de Sesión"),
                ft.dropdown.Option("logout", "Cierre de Sesión"),
                ft.dropdown.Option("venta", "Venta Realizada"),
            ],
            on_change=lambda _: self._aplicar_filtros(),
            width=200,
        )
        
        self.filtro_usuario_field = ft.TextField(
            label="Usuario",
            hint_text="Filtrar por usuario",
            on_change=lambda _: self._aplicar_filtros(),
            width=200,
        )
        
        self.filtro_fecha = ft.Dropdown(
            label="Período",
            value="hoy",
            options=[
                ft.dropdown.Option("hoy", "Hoy"),
                ft.dropdown.Option("semana", "Última semana"),
                ft.dropdown.Option("mes", "Último mes"),
                ft.dropdown.Option("todos", "Todos"),
            ],
            on_change=lambda _: self._cargar_registros(),
            width=200,
        )
        
        filtros_container = ft.Container(
            content=ft.Row(
                [
                    self.filtro_tipo_dropdown,
                    self.filtro_usuario_field,
                    self.filtro_fecha,
                ],
                spacing=16,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=16),
            bgcolor=ft.Colors.WHITE,
        )
        
        # Tabla de registros
        self.data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Fecha/Hora", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Usuario", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Tipo", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Descripción", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Detalles", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, "#e2e8f0"),
            border_radius=10,
            vertical_lines=ft.BorderSide(1, "#e2e8f0"),
            horizontal_lines=ft.BorderSide(1, "#e2e8f0"),
            heading_row_color="#f1f5f9",
            heading_row_height=50,
        )
        
        tabla_container = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=self.data_table,
                        border=ft.border.all(1, "#e2e8f0"),
                        border_radius=10,
                        bgcolor=ft.Colors.WHITE,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=16),
            expand=True,
        )
        
        # Cargar datos iniciales
        self._cargar_registros()
        
        return ft.Container(
            content=ft.Column(
                [
                    header,
                    filtros_container,
                    tabla_container,
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor="#f8fafc",
        )
    
    def _cargar_registros(self):
        """Carga los registros de auditoría desde la base de datos"""
        periodo = self.filtro_fecha.value if hasattr(self, 'filtro_fecha') else "hoy"
        
        # Calcular fechas según el período
        fecha_inicio = None
        if periodo == "hoy":
            fecha_inicio = datetime.now().strftime("%Y-%m-%d")
        elif periodo == "semana":
            fecha_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif periodo == "mes":
            fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        self.registros = db.obtener_auditoria(fecha_inicio=fecha_inicio)
        self._aplicar_filtros()
    
    def _aplicar_filtros(self):
        """Aplica filtros a los registros y actualiza la tabla"""
        registros_filtrados = self.registros
        
        # Filtrar por tipo
        if hasattr(self, 'filtro_tipo_dropdown'):
            tipo = self.filtro_tipo_dropdown.value
            if tipo != "todos":
                registros_filtrados = [r for r in registros_filtrados if r[3] == tipo]
        
        # Filtrar por usuario
        if hasattr(self, 'filtro_usuario_field'):
            usuario = self.filtro_usuario_field.value.strip().lower()
            if usuario:
                registros_filtrados = [r for r in registros_filtrados if usuario in r[2].lower()]
        
        self._actualizar_tabla(registros_filtrados)
    
    def _actualizar_tabla(self, registros):
        """Actualiza la tabla con los registros filtrados"""
        self.data_table.rows.clear()
        
        for reg in registros:
            # reg = (id, fecha_hora, usuario, tipo, descripcion, detalles)
            tipo_color = self._get_tipo_color(reg[3])
            tipo_icon = self._get_tipo_icon(reg[3])
            
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(reg[1], size=13)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.PERSON, size=16, color="#64748b"),
                                        ft.Text(reg[2], size=13, weight=ft.FontWeight.W_500),
                                    ],
                                    spacing=4,
                                ),
                            )
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(tipo_icon, size=16, color=tipo_color),
                                        ft.Text(reg[3].upper(), size=12, color=tipo_color, weight=ft.FontWeight.W_500),
                                    ],
                                    spacing=4,
                                ),
                            )
                        ),
                        ft.DataCell(ft.Text(reg[4], size=13)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(
                                    reg[5] if reg[5] else "-",
                                    size=12,
                                    color="#64748b",
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                width=200,
                            )
                        ),
                    ]
                )
            )
        
        if not self.data_table.rows:
            self.data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(
                            ft.Text(
                                "No hay registros para mostrar",
                                size=14,
                                color="#94a3b8",
                                italic=True,
                            )
                        ),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                    ]
                )
            )
        
        self.page.update()
    
    def _get_tipo_color(self, tipo):
        """Retorna el color según el tipo de evento"""
        colores = {
            "login": "#10b981",
            "logout": "#f59e0b",
            "venta": "#3b82f6",
        }
        return colores.get(tipo, "#6366f1")
    
    def _get_tipo_icon(self, tipo):
        """Retorna el icono según el tipo de evento"""
        iconos = {
            "login": ft.Icons.LOGIN_ROUNDED,
            "logout": ft.Icons.LOGOUT_ROUNDED,
            "venta": ft.Icons.SHOPPING_CART_ROUNDED,
        }
        return iconos.get(tipo, ft.Icons.INFO_ROUNDED)
    
    def _volver_panel(self):
        """Vuelve al panel de administración"""
        self.admin_panel.setup_ui()
    
    def _exportar_pdf(self):
        """Exporta los registros actuales a PDF"""
        try:
            # Crear carpeta si no existe
            carpeta_reportes = Path("auditoria registros")
            carpeta_reportes.mkdir(exist_ok=True)
            
            # Generar nombre de archivo con fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"auditoria_{timestamp}.pdf"
            ruta_completa = carpeta_reportes / nombre_archivo
            
            # Obtener registros actuales filtrados
            registros_actuales = []
            for row in self.data_table.rows:
                # Reconstruir el registro desde las celdas de la tabla
                if len(row.cells) >= 5:
                    # Extraer datos de las celdas
                    fecha_hora = row.cells[0].content.value if hasattr(row.cells[0].content, 'value') else ""
                    usuario_row = row.cells[1].content.content if hasattr(row.cells[1].content, 'content') else None
                    usuario = usuario_row.controls[1].value if usuario_row and len(usuario_row.controls) > 1 else ""
                    tipo_row = row.cells[2].content.content if hasattr(row.cells[2].content, 'content') else None
                    tipo = tipo_row.controls[1].value.lower() if tipo_row and len(tipo_row.controls) > 1 else ""
                    descripcion = row.cells[3].content.value if hasattr(row.cells[3].content, 'value') else ""
                    
                    if fecha_hora and usuario:  # Solo registros válidos
                        registros_actuales.append((0, fecha_hora, usuario, tipo, descripcion, ""))
            
            if not registros_actuales:
                self._mostrar_snackbar("No hay registros para exportar", ft.Colors.ORANGE)
                return
            
            # Exportar a PDF
            exito = db.exportar_auditoria_pdf(registros_actuales, str(ruta_completa))
            
            if exito:
                self._mostrar_snackbar(f"✓ PDF exportado: {nombre_archivo}", ft.Colors.GREEN)
            else:
                self._mostrar_snackbar("✗ Error al exportar PDF", ft.Colors.RED)
                
        except Exception as e:
            self._mostrar_snackbar("✗ Error al exportar PDF", ft.Colors.RED)
    
    def _mostrar_dialogo_eliminar(self):
        """Muestra diálogo de confirmación para eliminar registros"""
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()
        
        def confirmar_eliminacion(e):
            try:
                # Obtener filtros actuales
                fecha_inicio = None
                fecha_fin = None
                
                periodo = self.filtro_fecha.value
                if periodo == "hoy":
                    fecha_inicio = datetime.now().strftime("%Y-%m-%d")
                    fecha_fin = datetime.now().strftime("%Y-%m-%d")
                elif periodo == "semana":
                    fecha_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                    fecha_fin = datetime.now().strftime("%Y-%m-%d")
                elif periodo == "mes":
                    fecha_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                    fecha_fin = datetime.now().strftime("%Y-%m-%d")
                
                tipo = self.filtro_tipo_dropdown.value if self.filtro_tipo_dropdown.value != "todos" else None
                usuario = self.filtro_usuario_field.value.strip() if self.filtro_usuario_field.value.strip() else None
                
                # Eliminar registros
                eliminados = db.eliminar_registros_auditoria(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    tipo=tipo,
                    usuario=usuario
                )
                
                cerrar_dialogo(None)
                
                if eliminados > 0:
                    self._mostrar_snackbar(f"✓ {eliminados} registro(s) eliminado(s)", ft.Colors.GREEN)
                    self._cargar_registros()
                else:
                    self._mostrar_snackbar("No se eliminaron registros", ft.Colors.ORANGE)
                    
            except Exception as ex:
                self._mostrar_snackbar("✗ Error al eliminar registros", ft.Colors.RED)
                cerrar_dialogo(None)
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Confirmar Eliminación"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            "¿Está seguro de eliminar los registros de auditoría?",
                            size=14,
                        ),
                        ft.Text(
                            "Esta acción no se puede deshacer.",
                            size=12,
                            color=ft.Colors.RED,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Divider(),
                        ft.Text("Filtros aplicados:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"• Período: {self.filtro_fecha.value}", size=12),
                        ft.Text(f"• Tipo: {self.filtro_tipo_dropdown.value}", size=12),
                        ft.Text(f"• Usuario: {self.filtro_usuario_field.value or 'Todos'}", size=12),
                    ],
                    tight=True,
                    spacing=8,
                ),
                width=400,
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=cerrar_dialogo,
                ),
                ft.ElevatedButton(
                    "Eliminar",
                    on_click=confirmar_eliminacion,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    
    def _mostrar_snackbar(self, mensaje: str, color):
        """Muestra un snackbar con un mensaje"""
        snackbar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000,
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
