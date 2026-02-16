import flet as ft
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import json
import os
from admin_panels.graficas_window import GraficasWindow

class ReportesWindow:
    """Ventana de reportes con diseño profesional premium"""
    
    def __init__(self, page: ft.Page, admin_panel, nombre_usuario: str):
        self.page = page
        self.admin_panel = admin_panel
        self.nombre_usuario = nombre_usuario
        self.page.title = f"Reportes — {nombre_usuario}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f5f7fb"
        self.page.padding = 0
        self.page.scroll = ft.ScrollMode.AUTO

        # Directorios
        self.db_path = "./BASEDATOS/productos.db"
        self.ventas_db_path = "./BASEDATOS/ventas.db"
        self.reportes_dir = Path("./Reportes")
        self.reportes_dir.mkdir(parents=True, exist_ok=True)

        # Paleta de colores profesional
        self.colors = {
            "primary": "#4361ee",
            "secondary": "#3a0ca3",
            "accent": "#4cc9f0",
            "success": "#2ecc71",
            "warning": "#f39c12",
            "danger": "#e74c3c",
            "info": "#3498db",
            "light": "#f8f9fa",
            "dark": "#2c3e50",
            "gray_100": "#f1f3f5",
            "gray_200": "#e9ecef",
            "gray_300": "#dee2e6",
            "gray_600": "#6c757d",
            "gray_900": "#212529",
            "white": "#ffffff",
            "gradient_start": "#4361ee",
            "gradient_end": "#3a0ca3",
        }

        # Cargar datos empresa
        self.datos_empresa = self._cargar_datos_empresa()

        # Variables de filtros
        self.fecha_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.fecha_fin = datetime.now()
        self.tipo_reporte = "semana"
        self.intervalo_actual = "semana"
        self.panel_personalizado = None
        self.fecha_inicio_picker = ft.TextField(
            label="Fecha Inicio",
            value=self.fecha_inicio.strftime("%Y-%m-%d"),
            width=200,
            height=60,
            text_size=14,
            read_only=True,
            border_color=ft.Colors.GREY_400,
        )
        self.fecha_fin_picker = ft.TextField(
            label="Fecha Fin",
            value=self.fecha_fin.strftime("%Y-%m-%d"),
            width=200,
            height=60,
            text_size=14,
            read_only=True,
            border_color=ft.Colors.GREY_400,
        )
        
        # Calcular fechas para "Esta Semana"
        self._calcular_fechas_semana()

        # Referencias a elementos UI
        self.texto_periodo = None
        self.metricas_refs = {}
        self.tabla_productos = None
        self.tabla_ventas_tipo = None
        self.filtros_rapidos = None
        self.filtro_custom = None

        self.build_ui()

    def _calcular_fechas_semana(self):
        """Calcula las fechas de inicio y fin de la semana actual"""
        ahora = datetime.now()
        dias_desde_lunes = ahora.weekday()
        self.fecha_inicio = (ahora - timedelta(days=dias_desde_lunes)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        self.fecha_fin = ahora

    def _cargar_datos_empresa(self):
        """Carga los datos de la empresa desde el JSON"""
        try:
            Path("./Json files").mkdir(parents=True, exist_ok=True)
            
            try:
                with open("./Json files/datos_empresariales.json", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "nombre": data.get("nombre_empresa", "Empresa no configurada"),
                        "rfc": data.get("rfc", "RFC no configurado"),
                        "direccion": data.get("direccion", "Dirección no configurada"),
                        "telefono": data.get("numero_telefono", "Teléfono no configurado"),
                        "logo": data.get("logo", None)
                    }
            except FileNotFoundError:
                return {
                    "nombre": "Empresa no configurada",
                    "rfc": "RFC no configurado",
                    "direccion": "Dirección no configurada",
                    "telefono": "Teléfono no configurado"
                }
        except Exception as e:
            print(f"Error cargando datos empresa: {e}")
            return {
                "nombre": "Empresa no configurada",
                "rfc": "RFC no configurado",
                "direccion": "Dirección no configurada",
                "telefono": "Teléfono no configurado"
            }

    def _crear_boton_filtro(self, texto, tipo, icono):
        """Crea un botón de filtro con diseño premium"""
        es_activo = self.tipo_reporte == tipo
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(icono, size=18, color=ft.Colors.WHITE if es_activo else self.colors["primary"]),
                ft.Text(texto, size=13, weight=ft.FontWeight.W_600, 
                       color=ft.Colors.WHITE if es_activo else self.colors["primary"]),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=self.colors["primary"] if es_activo else ft.Colors.with_opacity(0.1, self.colors["primary"]),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=22, vertical=14),
            on_click=lambda e: self._cambiar_filtro(tipo),
            ink=True,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12 if es_activo else 0,
                color=ft.Colors.with_opacity(0.25, self.colors["primary"]) if es_activo else ft.Colors.TRANSPARENT,
                offset=ft.Offset(0, 4)
            ) if es_activo else None,
        )

    def _obtener_texto_filtro_activo(self):
        """Obtiene el texto descriptivo del filtro activo"""
        if self.tipo_reporte == "dia":
            return f"{self.fecha_inicio.strftime('%d/%m/%Y')}"
        if self.tipo_reporte == "semana":
            inicio = self.fecha_inicio.strftime('%d/%m')
            fin = self.fecha_fin.strftime('%d/%m')
            return f"Semana actual · {inicio} - {fin}"
        elif self.tipo_reporte == "mes":
            return f"{self.fecha_inicio.strftime('%B %Y').title()}"
        elif self.tipo_reporte == "año":
            return f"{self.fecha_inicio.strftime('%Y')}"
        elif self.tipo_reporte == "custom":
            inicio = self.fecha_inicio.strftime('%d/%m/%Y')
            fin = self.fecha_fin.strftime('%d/%m/%Y')
            return f"Personalizado · {inicio} - {fin}"
        return "Semana actual"

    def _cambiar_filtro(self, tipo):
        """Cambia el tipo de filtro y recalcula fechas"""
        self.tipo_reporte = tipo
        ahora = datetime.now()
        
        if tipo == "semana":
            dias_desde_lunes = ahora.weekday()
            self.fecha_inicio = (ahora - timedelta(days=dias_desde_lunes)).replace(
                hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = ahora
            self.filtro_custom.visible = False
            self._cargar_reporte()
            
        elif tipo == "mes":
            self.fecha_inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = ahora
            self.filtro_custom.visible = False
            self._cargar_reporte()
            
        elif tipo == "año":
            self.fecha_inicio = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = ahora
            self.filtro_custom.visible = False
            self._cargar_reporte()
            
        elif tipo == "custom":
            self.filtro_custom.visible = True
            self._actualizar_campos_fecha_custom()
        
        self._actualizar_estado_botones()

    def _actualizar_campos_fecha_custom(self):
        """Actualiza los campos de fecha en el filtro personalizado"""
        if hasattr(self, "fecha_inicio_picker") and self.fecha_inicio_picker:
            self.fecha_inicio_picker.value = self.fecha_inicio.strftime("%Y-%m-%d")
            self.fecha_inicio_picker.update()

        if hasattr(self, "fecha_fin_picker") and self.fecha_fin_picker:
            self.fecha_fin_picker.value = self.fecha_fin.strftime("%Y-%m-%d")
            self.fecha_fin_picker.update()

    def _aplicar_filtro_custom(self):
        """Aplica el filtro personalizado"""
        self.tipo_reporte = "custom"
        self.intervalo_actual = "personalizado"
        if self.panel_personalizado:
            self.panel_personalizado.visible = True
        self._actualizar_campos_fecha_custom()
        self._cargar_reporte()

    def _actualizar_estado_botones(self):
        """Actualiza el estado visual de todos los botones de filtro"""
        if hasattr(self, 'filtros_rapidos') and self.filtros_rapidos.content:
            self.filtros_rapidos.content.controls.clear()
            
            self.filtros_rapidos.content.controls.extend([
                self._crear_boton_filtro("Esta Semana", "semana", ft.Icons.DATE_RANGE_ROUNDED),
                self._crear_boton_filtro("Este Mes", "mes", ft.Icons.CALENDAR_MONTH_ROUNDED),
                self._crear_boton_filtro("Este Año", "año", ft.Icons.CALENDAR_TODAY_ROUNDED),
                self._crear_boton_filtro("Personalizado", "custom", ft.Icons.TUNE_ROUNDED),
            ])
            
            self.filtros_rapidos.update()

    def _crear_metric_card(self, titulo, valor_inicial, icono, color, key):
        """Crea una tarjeta de métrica con diseño premium"""
        texto_valor = ft.Text(
            valor_inicial, 
            size=28, 
            weight=ft.FontWeight.BOLD,
            color=self.colors["dark"],
            font_family="Roboto"
        )
        
        self.metricas_refs[key] = texto_valor
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icono, size=22, color=ft.Colors.WHITE),
                        bgcolor=color,
                        padding=12,
                        border_radius=12,
                    ),
                    ft.Column([
                        ft.Text(
                            titulo,
                            size=13,
                            color=self.colors["gray_600"],
                            weight=ft.FontWeight.W_500,
                        ),
                        texto_valor,
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.START),
                ], spacing=16, alignment=ft.MainAxisAlignment.START),
            ]),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            padding=20,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.08, self.colors["gray_600"]),
                offset=ft.Offset(0, 4)
            ),
            ink=True,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            border=ft.border.all(1, self.colors["gray_200"]),
        )

    def _obtener_datos_ventas(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene datos de ventas desde la base de datos con filtros de fecha"""
        if fecha_inicio is None:
            fecha_inicio = self.fecha_inicio
        if fecha_fin is None:
            fecha_fin = self.fecha_fin
            
        datos = {
            "ventas": [],
            "productos_vendidos": [],
            "total_ventas": 0,
            "num_transacciones": 0,
            "ticket_promedio": 0,
            "productos_top": [],
            "ventas_por_dia": [],
            "ventas_por_tipo": {"Normal": 0, "Mayoreo": 0, "Promoción": 0},
        }

        try:
            if not os.path.exists(self.ventas_db_path):
                print(f"Base de datos {self.ventas_db_path} no existe")
                return datos

            conn = sqlite3.connect(self.ventas_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if not self._tabla_existe(cursor, "ventas"):
                print("Error obteniendo datos de ventas: no such table: ventas")
                conn.close()
                return datos

            if not self._tabla_existe(cursor, "ventas_detalle"):
                print("Error obteniendo datos de ventas: no such table: ventas_detalle")
                conn.close()
                return datos

            fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
            fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')
            
            cursor.execute("""
                SELECT * FROM ventas 
                WHERE fecha BETWEEN ? AND ?
                ORDER BY fecha DESC
            """, [fecha_inicio_str, fecha_fin_str])
            
            ventas = cursor.fetchall()
            datos["ventas"] = ventas
            datos["num_transacciones"] = len(ventas)

            productos_dict = {}
            ventas_por_tipo = {"Normal": 0, "Mayoreo": 0, "Promoción": 0}
            ventas_por_dia = {}
            total_ventas = 0

            for v in ventas:
                total_venta = v["total"] or 0.0
                total_ventas += total_venta
                
                # Obtener tipo de venta real desde la base de datos
                try:
                    tipo_venta = v["tipo_venta"] if v["tipo_venta"] else "Normal"
                except (KeyError, IndexError):
                    tipo_venta = "Normal"
                    
                ventas_por_tipo[tipo_venta] = ventas_por_tipo.get(tipo_venta, 0) + total_venta
                
                # Ventas por día
                fecha_venta = v["fecha"]
                ventas_por_dia[fecha_venta] = ventas_por_dia.get(fecha_venta, 0) + total_venta

                cursor.execute("SELECT * FROM ventas_detalle WHERE venta_id = ?", [v["id"]])
                detalles = cursor.fetchall()

                for d in detalles:
                    nombre = d["producto"]
                    cantidad = d["cantidad"]
                    ingresos = d["precio_unit"] * cantidad

                    if nombre in productos_dict:
                        productos_dict[nombre]["cantidad"] += cantidad
                        productos_dict[nombre]["ingresos"] += ingresos
                    else:
                        productos_dict[nombre] = {
                            "nombre": nombre,
                            "cantidad": cantidad,
                            "ingresos": ingresos
                        }

            datos["total_ventas"] = total_ventas
            datos["ticket_promedio"] = total_ventas / datos["num_transacciones"] if datos["num_transacciones"] > 0 else 0
            datos["ventas_por_dia"] = ventas_por_dia

            datos["productos_top"] = sorted(
                productos_dict.values(),
                key=lambda x: x["ingresos"],
                reverse=True
            )[:10]

            datos["ventas_por_tipo"] = ventas_por_tipo
            conn.close()

        except Exception as e:
            print(f"Error obteniendo datos de ventas: {e}")
            import traceback
            traceback.print_exc()

        return datos

    def _tabla_existe(self, cursor, tabla):
        """Valida si la tabla existe en la base de datos"""
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [tabla],
        )
        return cursor.fetchone() is not None

    def _crear_campo_fecha_inicio(self):
        """Crea y registra el campo de fecha de inicio"""
        self.input_fecha_inicio = ft.TextField(
            value=self.fecha_inicio.strftime("%Y-%m-%d"),
            width=200,
            height=52,
            text_size=14,
            border_color=self.colors["gray_300"],
            focused_border_color=self.colors["primary"],
            border_radius=12,
            prefix_icon=ft.Icons.EVENT_ROUNDED,
            on_change=lambda e: self._actualizar_fecha_inicio(e.control.value),
        )
        return self.input_fecha_inicio

    def _crear_campo_fecha_fin(self):
        """Crea y registra el campo de fecha de fin"""
        self.input_fecha_fin = ft.TextField(
            value=self.fecha_fin.strftime("%Y-%m-%d"),
            width=200,
            height=52,
            text_size=14,
            border_color=self.colors["gray_300"],
            focused_border_color=self.colors["primary"],
            border_radius=12,
            prefix_icon=ft.Icons.EVENT_AVAILABLE_ROUNDED,
            on_change=lambda e: self._actualizar_fecha_fin(e.control.value),
        )
        return self.input_fecha_fin

    def _cargar_reporte(self):
        """Carga los datos del reporte y actualiza la UI"""
        datos = self._obtener_datos_ventas()

        # Actualizar texto del período
        if self.texto_periodo:
            self.texto_periodo.value = self._obtener_texto_filtro_activo()
            self.texto_periodo.update()

        # Actualizar métricas
        if 'total_ventas' in self.metricas_refs:
            self.metricas_refs['total_ventas'].value = f"${datos['total_ventas']:,.2f}"
            self.metricas_refs['total_ventas'].update()

        if 'transacciones' in self.metricas_refs:
            self.metricas_refs['transacciones'].value = f"{datos['num_transacciones']:,}"
            self.metricas_refs['transacciones'].update()

        if 'ticket_promedio' in self.metricas_refs:
            self.metricas_refs['ticket_promedio'].value = f"${datos['ticket_promedio']:,.2f}"
            self.metricas_refs['ticket_promedio'].update()

        if 'productos' in self.metricas_refs:
            self.metricas_refs['productos'].value = f"{len(datos['productos_top'])}"
            self.metricas_refs['productos'].update()

        # Actualizar tabla productos
        if self.tabla_productos:
            self.tabla_productos.rows.clear()
            for i, p in enumerate(datos["productos_top"]):
                self.tabla_productos.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Container(
                                    content=ft.Text(
                                        str(i + 1),
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=self.colors["primary"],
                                    ),
                                    width=40,
                                    alignment=ft.alignment.center,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    p["nombre"][:30] + "..." if len(p["nombre"]) > 30 else p["nombre"],
                                    size=13,
                                    weight=ft.FontWeight.W_500,
                                    color=self.colors["dark"],
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    f"{p['cantidad']:,}",
                                    size=13,
                                    text_align=ft.TextAlign.RIGHT,
                                    weight=ft.FontWeight.W_500,
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    f"${p['ingresos']:,.2f}",
                                    size=13,
                                    text_align=ft.TextAlign.RIGHT,
                                    weight=ft.FontWeight.W_600,
                                    color=self.colors["success"],
                                )
                            ),
                        ],
                        color=ft.Colors.WHITE if i % 2 == 0 else self.colors["gray_100"],
                    )
                )
            self.tabla_productos.update()

        # Actualizar tabla ventas por tipo
        if self.tabla_ventas_tipo:
            self.tabla_ventas_tipo.rows.clear()
            total = sum(datos["ventas_por_tipo"].values())
            for tipo, monto in datos["ventas_por_tipo"].items():
                if monto > 0:
                    porcentaje = (monto / total * 100) if total > 0 else 0
                    self.tabla_ventas_tipo.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(
                                    ft.Row([
                                        ft.Container(
                                            width=12,
                                            height=12,
                                            border_radius=6,
                                            bgcolor=self._get_color_for_tipo(tipo),
                                        ),
                                        ft.Text(tipo, size=13, weight=ft.FontWeight.W_500),
                                    ], spacing=8)
                                ),
                                ft.DataCell(
                                    ft.Column([
                                        ft.Text(
                                            f"${monto:,.2f}",
                                            size=13,
                                            text_align=ft.TextAlign.RIGHT,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            f"{porcentaje:.1f}%",
                                            size=11,
                                            text_align=ft.TextAlign.RIGHT,
                                            color=self.colors["gray_600"],
                                        ),
                                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END)
                                ),
                            ],
                            color=ft.Colors.WHITE,
                        )
                    )
            self.tabla_ventas_tipo.update()

    def _get_color_for_tipo(self, tipo):
        """Obtiene color para tipo de venta"""
        colors = {
            "Normal": self.colors["primary"],
            "Mayoreo": self.colors["success"],
            "Promoción": self.colors["warning"]
        }
        return colors.get(tipo, self.colors["info"])

    def _crear_pdf_reporte(self, datos):
        """Crea un PDF con el reporte con diseño premium"""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        try:
            nombre_archivo = f"Reporte_Ventas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            ruta_pdf = self.reportes_dir / nombre_archivo
            doc = SimpleDocTemplate(str(ruta_pdf), pagesize=letter,
                                   topMargin=0.6*inch, bottomMargin=0.6*inch,
                                   leftMargin=0.8*inch, rightMargin=0.8*inch)
            
            story = []
            
            # Colores corporativos
            COLOR_PRIMARY = HexColor('#4361ee')
            COLOR_SECONDARY = HexColor('#3a0ca3')
            COLOR_SUCCESS = HexColor('#2ecc71')
            COLOR_DARK = HexColor('#2c3e50')
            COLOR_LIGHT_BG = HexColor('#f8f9fa')
            
            # Estilos premium
            style_title = ParagraphStyle(
                name="CorporateTitle",
                fontSize=24,
                leading=30,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=COLOR_PRIMARY,
                fontName='Helvetica-Bold'
            )
            
            style_subtitle = ParagraphStyle(
                name="CorporateSubtitle",
                fontSize=11,
                leading=14,
                spaceAfter=25,
                alignment=TA_CENTER,
                textColor=COLOR_DARK,
                fontName='Helvetica'
            )
            
            style_section = ParagraphStyle(
                name="CorporateSection",
                fontSize=14,
                leading=18,
                spaceAfter=12,
                spaceBefore=15,
                textColor=COLOR_SECONDARY,
                fontName='Helvetica-Bold'
            )
            
            # Header del reporte
            story.append(Paragraph(f"<b>{self.datos_empresa['nombre']}</b>", style_title))
            story.append(Paragraph("Reporte de Ventas", style_subtitle))
            story.append(Paragraph(
                f"Período: {self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}",
                style_subtitle
            ))
            story.append(Spacer(1, 0.4*inch))
            
            # Métricas principales
            metrics_data = [
                ["Métrica", "Valor"],
                ["Total de Ventas", f"${datos['total_ventas']:,.2f}"],
                ["Transacciones", f"{datos['num_transacciones']:,}"],
                ["Ticket Promedio", f"${datos['ticket_promedio']:,.2f}"],
            ]
            
            table_metrics = Table(metrics_data, colWidths=[3*inch, 2.5*inch])
            table_metrics.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 14),
                ('TOPPADDING', (0, 0), (-1, 0), 14),
                ('BACKGROUND', (0, 1), (-1, -1), COLOR_LIGHT_BG),
                ('TEXTCOLOR', (1, 1), (1, -1), COLOR_SUCCESS),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('TOPPADDING', (0, 1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 20),
                ('RIGHTPADDING', (0, 0), (-1, -1), 20),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(table_metrics)
            story.append(Spacer(1, 0.5*inch))
            
            # Productos top
            story.append(Paragraph("📊 Productos Más Vendidos", style_section))
            story.append(Spacer(1, 0.1*inch))
            
            product_data = [["#", "Producto", "Cantidad", "Ingresos"]]
            for i, p in enumerate(datos["productos_top"][:10], 1):
                product_data.append([
                    str(i),
                    p["nombre"][:40] + "..." if len(p["nombre"]) > 40 else p["nombre"],
                    f"{p['cantidad']:,}",
                    f"${p['ingresos']:,.2f}"
                ])
            
            table_products = Table(product_data, colWidths=[0.5*inch, 3*inch, 1.2*inch, 1.5*inch])
            table_products.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('FONTNAME', (3, 1), (3, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (3, 1), (3, -1), COLOR_SUCCESS),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(table_products)
            story.append(Spacer(1, 0.4*inch))
            
            # Ventas por tipo
            story.append(Paragraph("💰 Distribución por Tipo de Venta", style_section))
            story.append(Spacer(1, 0.1*inch))
            
            tipo_data = [["Tipo de Venta", "Monto", "Porcentaje"]]
            total = sum(datos["ventas_por_tipo"].values())
            for tipo, monto in datos["ventas_por_tipo"].items():
                if monto > 0:
                    porcentaje = (monto / total * 100) if total > 0 else 0
                    tipo_data.append([
                        tipo,
                        f"${monto:,.2f}",
                        f"{porcentaje:.1f}%"
                    ])
            
            table_types = Table(tipo_data, colWidths=[2.2*inch, 1.8*inch, 1.2*inch])
            table_types.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('LEFTPADDING', (0, 1), (-1, -1), 15),
                ('RIGHTPADDING', (0, 1), (-1, -1), 15),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(table_types)
            
            # Footer
            story.append(Spacer(1, 0.6*inch))
            style_footer = ParagraphStyle(
                name="Footer",
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=colors.grey,
                fontName='Helvetica-Oblique'
            )
            story.append(Paragraph(
                f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} por {self.nombre_usuario}",
                style_footer
            ))
            story.append(Paragraph(
                f"{self.datos_empresa['nombre']} · {self.datos_empresa.get('rfc', '')}",
                style_footer
            ))
            
            doc.build(story)
            
            # Mostrar notificación de éxito
            self.page.open(
                ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=ft.Colors.WHITE, size=20),
                        ft.Text(f"✅ PDF generado: {nombre_archivo}", size=14, color=ft.Colors.WHITE),
                    ], spacing=10),
                    bgcolor=self.colors["success"],
                    duration=4000,
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
            )
            
        except Exception as e:
            print(f"Error generando PDF: {e}")
            import traceback
            traceback.print_exc()
            
            self.page.open(
                ft.SnackBar(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ERROR_ROUNDED, color=ft.Colors.WHITE, size=20),
                        ft.Text("❌ Error al generar el PDF", size=14, color=ft.Colors.WHITE),
                    ], spacing=10),
                    bgcolor=self.colors["danger"],
                    duration=4000,
                    behavior=ft.SnackBarBehavior.FLOATING,
                )
            )

    def _abrir_graficas(self):
        """Abre la ventana de gráficas"""
        datos = self._obtener_datos_ventas()
        GraficasWindow(self.page, datos, self.fecha_inicio, self.fecha_fin, self)

    def _actualizar_fecha_inicio(self, valor):
        """Actualiza la fecha de inicio"""
        try:
            self.fecha_inicio = datetime.strptime(valor, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        except ValueError:
            pass

    def _actualizar_fecha_fin(self, valor):
        """Actualiza la fecha de fin"""
        try:
            self.fecha_fin = datetime.strptime(valor, "%Y-%m-%d")
        except ValueError:
            pass

    def _abrir_selector_fecha(self, e, es_inicio=True):
        """Abre el selector de fecha"""
        def fecha_seleccionada(e):
            if e.control.value:
                fecha_formateada = e.control.value.strftime("%Y-%m-%d")
                if es_inicio:
                    self.fecha_inicio_picker.value = fecha_formateada
                else:
                    self.fecha_fin_picker.value = fecha_formateada
                self.page.update()
                date_picker.open = False
                self.page.update()

        fecha_actual = self.fecha_inicio if es_inicio else self.fecha_fin
        date_picker = ft.DatePicker(
            on_change=fecha_seleccionada,
            first_date=datetime(2020, 1, 1),
            last_date=datetime.now() + timedelta(days=365),
            value=fecha_actual,
        )

        self.page.overlay.append(date_picker)
        date_picker.open = True
        self.page.update()

    def _aplicar_fechas_personalizadas(self, e):
        """Aplica las fechas personalizadas ingresadas"""
        try:
            fecha_inicio_str = self.fecha_inicio_picker.value
            fecha_fin_str = self.fecha_fin_picker.value

            nueva_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            nueva_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")

            if nueva_inicio > nueva_fin:
                self.page.open(
                    ft.SnackBar(
                        content=ft.Text("La fecha de inicio debe ser anterior a la fecha de fin"),
                        bgcolor=self.colors["warning"],
                        duration=3000,
                    )
                )
                return

            self.fecha_inicio = nueva_inicio
            self.fecha_fin = nueva_fin
            self.intervalo_actual = "personalizado"
            self.tipo_reporte = "custom"
            self._cargar_reporte()

        except ValueError:
            self.page.open(
                ft.SnackBar(
                    content=ft.Text("Formato de fecha invalido. Use YYYY-MM-DD"),
                    bgcolor=self.colors["danger"],
                    duration=3000,
                )
            )

    def _cambiar_intervalo(self, intervalo):
        """Cambia el intervalo de tiempo y actualiza el reporte"""
        self.intervalo_actual = intervalo
        hoy = datetime.now()

        if intervalo == "dia":
            self.fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
            self.tipo_reporte = "dia"
        elif intervalo == "semana":
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            self.fecha_inicio = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
            self.tipo_reporte = "semana"
        elif intervalo == "mes":
            self.fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
            self.tipo_reporte = "mes"
        elif intervalo == "año":
            self.fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
            self.tipo_reporte = "año"
        elif intervalo == "personalizado":
            self.tipo_reporte = "custom"

        self._actualizar_campos_fecha_custom()

        if self.panel_personalizado:
            self.panel_personalizado.visible = (intervalo == "personalizado")

        if intervalo != "personalizado":
            self._cargar_reporte()
        else:
            self.page.update()

    def _crear_panel_intervalos(self):
        """Crea el panel de seleccion de intervalos"""
        def crear_boton_intervalo(texto, icono, intervalo, color):
            es_activo = self.intervalo_actual == intervalo
            return ft.Container(
                content=ft.Column([
                    ft.Icon(
                        icono,
                        size=28,
                        color=ft.Colors.WHITE if es_activo else color,
                    ),
                    ft.Text(
                        texto,
                        size=14,
                        weight=ft.FontWeight.BOLD if es_activo else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if es_activo else self.colors["dark"],
                    ),
                ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=color if es_activo else ft.Colors.WHITE,
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=25, vertical=18),
                border=ft.border.all(2, color),
                on_click=lambda e, i=intervalo: self._cambiar_intervalo(i),
                ink=True,
                tooltip=f"Ver datos de {texto.lower()}",
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.15 if es_activo else 0.05, color),
                    offset=ft.Offset(0, 3),
                ) if es_activo else None,
            )

        self.panel_personalizado = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Row([
                        self.fecha_inicio_picker,
                        ft.IconButton(
                            icon=ft.Icons.CALENDAR_MONTH,
                            icon_color=self.colors["primary"],
                            icon_size=24,
                            on_click=lambda e: self._abrir_selector_fecha(e, es_inicio=True),
                            tooltip="Seleccionar fecha inicio",
                        ),
                    ], spacing=8),
                ),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=24, color=ft.Colors.GREY_400),
                ft.Container(
                    content=ft.Row([
                        self.fecha_fin_picker,
                        ft.IconButton(
                            icon=ft.Icons.CALENDAR_MONTH,
                            icon_color=self.colors["primary"],
                            icon_size=24,
                            on_click=lambda e: self._abrir_selector_fecha(e, es_inicio=False),
                            tooltip="Seleccionar fecha fin",
                        ),
                    ], spacing=8),
                ),
                ft.ElevatedButton(
                    "Aplicar",
                    icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                    on_click=self._aplicar_fechas_personalizadas,
                    bgcolor=self.colors["primary"],
                    color=ft.Colors.WHITE,
                    height=60,
                    style=ft.ButtonStyle(
                        text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
                    ),
                ),
            ], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
            visible=(self.intervalo_actual == "personalizado"),
            margin=ft.margin.only(top=20),
            padding=15,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Icon(ft.Icons.DATE_RANGE_ROUNDED, size=24, color=self.colors["dark"]),
                        ft.Text(
                            "Intervalo de Tiempo",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.colors["dark"],
                        ),
                    ], spacing=10),
                    ft.Row([
                        crear_boton_intervalo("Dia", ft.Icons.TODAY_ROUNDED, "dia", self.colors["primary"]),
                        crear_boton_intervalo("Semana", ft.Icons.VIEW_WEEK_ROUNDED, "semana", self.colors["secondary"]),
                        crear_boton_intervalo("Mes", ft.Icons.CALENDAR_VIEW_MONTH_ROUNDED, "mes", self.colors["accent"]),
                        crear_boton_intervalo("Año", ft.Icons.CALENDAR_TODAY_ROUNDED, "año", self.colors["success"]),
                        crear_boton_intervalo("Personalizado", ft.Icons.TUNE_ROUNDED, "personalizado", self.colors["warning"]),
                    ], spacing=15),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.panel_personalizado,
            ], spacing=10),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=25,
            margin=ft.margin.only(left=40, right=40, top=20),
            border=ft.border.all(1.5, self.colors["gray_200"]),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )

    def build_ui(self):
        """Construye la interfaz de usuario premium"""
        
        # Texto del período
        self.texto_periodo = ft.Text(
            self._obtener_texto_filtro_activo(),
            size=13,
            color=self.colors["gray_600"],
            weight=ft.FontWeight.W_500,
            italic=True,
        )
        
        # Header premium
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.ANALYTICS_ROUNDED, size=28, color=ft.Colors.WHITE),
                        bgcolor=self.colors["primary"],
                        padding=12,
                        border_radius=14,
                    ),
                    ft.Column([
                        ft.Text(
                            "Reportes de Ventas",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=self.colors["dark"],
                        ),
                        self.texto_periodo,
                    ], spacing=4),
                ], spacing=16),
                ft.Row([
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.ARROW_BACK_ROUNDED,
                            icon_size=22,
                            icon_color=self.colors["primary"],
                            bgcolor=ft.Colors.with_opacity(0.1, self.colors["primary"]),
                            on_click=lambda e: self.admin_panel.setup_ui(),
                            tooltip="Volver al Panel",
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                            ),
                        ),
                        border_radius=12,
                    ),
                ], spacing=12),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=40, vertical=25),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            ),
        )


        # Tarjetas de métricas premium
        metricas = ft.Container(
            content=ft.Row([
                self._crear_metric_card("Total Ventas", "$0.00", ft.Icons.ATTACH_MONEY_ROUNDED, self.colors["success"], "total_ventas"),
                self._crear_metric_card("Transacciones", "0", ft.Icons.RECEIPT_LONG_ROUNDED, self.colors["primary"], "transacciones"),
                self._crear_metric_card("Ticket Promedio", "$0.00", ft.Icons.SHOPPING_CART_ROUNDED, self.colors["info"], "ticket_promedio"),
                self._crear_metric_card("Productos", "0", ft.Icons.INVENTORY_ROUNDED, self.colors["warning"], "productos"),
            ], spacing=20),
            padding=ft.padding.symmetric(horizontal=40, vertical=20),
        )

        # Botones de acción premium
        action_buttons = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SHOW_CHART_ROUNDED, size=18, color=ft.Colors.WHITE),
                            ft.Text("Ver Gráficas Analíticas", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        ], spacing=8),
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=self.colors["secondary"],
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=ft.padding.symmetric(horizontal=24, vertical=14),
                        ),
                        on_click=lambda e: self._abrir_graficas(),
                    ),
                    ink=True,
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.PICTURE_AS_PDF_ROUNDED, size=18, color=ft.Colors.WHITE),
                            ft.Text("Exportar PDF", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        ], spacing=8),
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=self.colors["danger"],
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=ft.padding.symmetric(horizontal=24, vertical=14),
                        ),
                        on_click=lambda e: self._crear_pdf_reporte(self._obtener_datos_ventas()),
                    ),
                    ink=True,
                ),
                ft.Container(
                    content=ft.OutlinedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.REFRESH_ROUNDED, size=18, color=self.colors["primary"]),
                            ft.Text("Actualizar Datos", size=13, weight=ft.FontWeight.W_600, color=self.colors["primary"]),
                        ], spacing=8),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            padding=ft.padding.symmetric(horizontal=24, vertical=14),
                            side=ft.BorderSide(1.5, self.colors["primary"]),
                        ),
                        on_click=lambda e: self._cargar_reporte(),
                    ),
                    ink=True,
                ),
            ], spacing=16, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=40, vertical=15),
            bgcolor=ft.Colors.WHITE,
            margin=ft.margin.only(bottom=10),
        )

        # Tabla de productos premium
        self.tabla_productos = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Container(
                        content=ft.Row([
                            ft.Text("#", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        width=50,
                    ),
                    numeric=True,
                ),
                ft.DataColumn(
                    ft.Text("Producto", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ),
                ft.DataColumn(
                    ft.Text("Cantidad", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    numeric=True,
                ),
                ft.DataColumn(
                    ft.Text("Ingresos", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    numeric=True,
                ),
            ],
            rows=[],
            border_radius=16,
            border=ft.border.all(1, self.colors["gray_200"]),
            horizontal_lines=ft.BorderSide(1, self.colors["gray_200"]),
            vertical_lines=ft.BorderSide(1, self.colors["gray_200"]),
            heading_row_color=self.colors["primary"],
            heading_row_height=56,
            data_row_min_height=52,
            data_row_max_height=52,
            column_spacing=30,
            width=1100,
        )

        # Tabla de ventas por tipo premium
        self.tabla_ventas_tipo = ft.DataTable(
            columns=[
                ft.DataColumn(
                    ft.Text("Tipo de Venta", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ),
                ft.DataColumn(
                    ft.Text("Monto / Porcentaje", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    numeric=True,
                ),
            ],
            rows=[],
            border_radius=16,
            border=ft.border.all(1, self.colors["gray_200"]),
            horizontal_lines=ft.BorderSide(1, self.colors["gray_200"]),
            vertical_lines=ft.BorderSide(1, self.colors["gray_200"]),
            heading_row_color=self.colors["primary"],
            heading_row_height=56,
            data_row_min_height=56,
            data_row_max_height=56,
            column_spacing=30,
            width=600,
        )

        # Sección de productos
        productos_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.INVENTORY_2_ROUNDED, size=24, color=ft.Colors.WHITE),
                        bgcolor=self.colors["primary"],
                        padding=10,
                        border_radius=12,
                    ),
                    ft.Column([
                        ft.Text(
                            "Top Productos Más Vendidos",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=self.colors["dark"],
                        ),
                        ft.Text(
                            "Ranking de productos por ingresos generados",
                            size=12,
                            color=self.colors["gray_600"],
                        ),
                    ], spacing=4),
                ], spacing=16),
                ft.Divider(height=24, color=self.colors["gray_200"]),
                ft.Container(
                    content=self.tabla_productos,
                    alignment=ft.alignment.center,
                    padding=10,
                ),
            ], spacing=12),
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=30,
            margin=ft.margin.only(left=40, right=40, top=20),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=25,
                color=ft.Colors.with_opacity(0.08, self.colors["gray_600"]),
                offset=ft.Offset(0, 5)
            ),
            border=ft.border.all(1, self.colors["gray_200"]),
        )

        # Sección de tipos de venta
        tipos_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.CATEGORY_ROUNDED, size=24, color=ft.Colors.WHITE),
                        bgcolor=self.colors["secondary"],
                        padding=10,
                        border_radius=12,
                    ),
                    ft.Column([
                        ft.Text(
                            "Distribución por Tipo de Venta",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=self.colors["dark"],
                        ),
                        ft.Text(
                            "Análisis de ventas por categoría",
                            size=12,
                            color=self.colors["gray_600"],
                        ),
                    ], spacing=4),
                ], spacing=16),
                ft.Divider(height=24, color=self.colors["gray_200"]),
                ft.Container(
                    content=self.tabla_ventas_tipo,
                    alignment=ft.alignment.center,
                    padding=10,
                ),
            ], spacing=12),
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=30,
            margin=ft.margin.only(left=40, right=40, top=20),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=25,
                color=ft.Colors.with_opacity(0.08, self.colors["gray_600"]),
                offset=ft.Offset(0, 5)
            ),
            border=ft.border.all(1, self.colors["gray_200"]),
        )

        # Layout principal
        self.page.clean()
        self.page.add(
            ft.Column([
                header,
                self._crear_panel_intervalos(),
                metricas,
                action_buttons,
                productos_section,
                tipos_section,
                ft.Container(height=40),
            ], spacing=0, scroll=ft.ScrollMode.AUTO)
        )

        self._cargar_reporte()