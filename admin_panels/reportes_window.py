import flet as ft
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import json
import os

class ReportesWindow:
    def __init__(self, page: ft.Page, admin_panel, nombre_usuario: str):
        self.page = page
        self.admin_panel = admin_panel
        self.nombre_usuario = nombre_usuario
        self.page.title = f"Reportes — {nombre_usuario}"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = "#f8f9fa"
        self.page.padding = 0

        # Directorios
        self.db_path = "./BASEDATOS/productos.db"
        self.ventas_db_path = "./BASEDATOS/ventas.db"
        self.reportes_dir = Path("./Reportes")
        self.reportes_dir.mkdir(parents=True, exist_ok=True)

        # Cargar datos empresa
        self.datos_empresa = self._cargar_datos_empresa()

        # Variables de filtros
        self.fecha_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.fecha_fin = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        self.tipo_reporte = "semana"  # Filtro predeterminado: semana
        
        # Calcular fechas para "Esta Semana"
        self._calcular_fechas_semana()

        self.build_ui()

    def _calcular_fechas_semana(self):
        """Calcula las fechas de inicio y fin de la semana actual"""
        ahora = datetime.now()
        dias_desde_lunes = ahora.weekday()
        self.fecha_inicio = (ahora - timedelta(days=dias_desde_lunes)).replace(
            hour=0, minute=0, second=0, microsecond=0)
        self.fecha_fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)

    def _cargar_datos_empresa(self):
        """Carga los datos de la empresa desde el JSON"""
        try:
            Path("./Json files").mkdir(parents=True, exist_ok=True)
            
            # Intentar cargar desde datos_empresa.json primero
            try:
                with open("./Json files/datos_empresariales.json", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                # Si no existe, intentar con datos_empresariales.json
                with open("./Json files/datos_empresariales.json", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "nombre": data.get("nombre_empresa", "Empresa no configurada"),
                        "rfc": data.get("rfc", "RFC no configurado"),
                        "direccion": data.get("direccion", "Dirección no configurada"),
                        "telefono": data.get("numero_telefono", "Teléfono no configurado")
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
        """Crea un botón de filtro con estilo premium"""
        es_activo = self.tipo_reporte == tipo
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(icono, size=18, color=ft.Colors.WHITE if es_activo else ft.Colors.INDIGO_700),
                ft.Text(texto, size=13, weight=ft.FontWeight.W_600, 
                       color=ft.Colors.WHITE if es_activo else ft.Colors.INDIGO_700),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
            bgcolor=ft.Colors.INDIGO_600 if es_activo else ft.Colors.INDIGO_50,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            on_click=lambda e: self._cambiar_filtro(tipo),
            ink=True,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8 if es_activo else 0,
                color=ft.Colors.with_opacity(0.3, ft.Colors.INDIGO_600) if es_activo else ft.Colors.TRANSPARENT,
                offset=ft.Offset(0, 2)
            )
        )

    def _obtener_texto_filtro_activo(self):
        """Obtiene el texto descriptivo del filtro activo"""
        if self.tipo_reporte == "semana":
            return f"Esta Semana ({self.fecha_inicio.strftime('%d/%m')} - {self.fecha_fin.strftime('%d/%m')})"
        elif self.tipo_reporte == "mes":
            return f"Este Mes ({self.fecha_inicio.strftime('%B %Y')})"
        elif self.tipo_reporte == "año":
            return f"Este Año ({self.fecha_inicio.strftime('%Y')})"
        elif self.tipo_reporte == "custom":
            return f"Personalizado: {self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}"
        return "Esta Semana"

    def _actualizar_texto_filtro_header(self):
        """Actualiza el texto del filtro en el header"""
        if hasattr(self, 'texto_periodo'):
            self.texto_periodo.value = self._obtener_texto_filtro_activo()
            self.texto_periodo.update()

    def _actualizar_estado_botones(self):
        """Actualiza el estado visual de todos los botones de filtro"""
        self.filtros_rapidos.content.controls.clear()
        
        self.filtros_rapidos.content.controls.extend([
            self._crear_boton_filtro("Esta Semana", "semana", ft.Icons.DATE_RANGE),
            self._crear_boton_filtro("Este Mes", "mes", ft.Icons.CALENDAR_MONTH),
            self._crear_boton_filtro("Este Año", "año", ft.Icons.CALENDAR_TODAY),
            self._crear_boton_filtro("Personalizado", "custom", ft.Icons.TUNE),
        ])
        
        self._actualizar_texto_filtro_header()
        self.filtros_rapidos.update()

    def _cambiar_filtro(self, tipo):
        """Cambia el tipo de filtro y recalcula fechas"""
        self.tipo_reporte = tipo
        ahora = datetime.now()
        
        if tipo == "semana":
            dias_desde_lunes = ahora.weekday()
            self.fecha_inicio = (ahora - timedelta(days=dias_desde_lunes)).replace(
                hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
            self.filtro_custom.visible = False
            self._cargar_reporte()
            
        elif tipo == "mes":
            self.fecha_inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
            self.filtro_custom.visible = False
            self._cargar_reporte()
            
        elif tipo == "año":
            self.fecha_inicio = ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = ahora.replace(hour=23, minute=59, second=59, microsecond=999999)
            self.filtro_custom.visible = False
            self._cargar_reporte()
            
        elif tipo == "custom":
            self.filtro_custom.visible = True
            # Actualizar los campos de fecha en el filtro personalizado
            self._actualizar_campos_fecha_custom()
        
        self._actualizar_estado_botones()

    def _actualizar_campos_fecha_custom(self):
        """Actualiza los campos de fecha en el filtro personalizado"""
        # Buscar los TextField de fecha en los controles
        for control in self.filtro_custom.content.controls:
            if hasattr(control, 'content') and isinstance(control.content, ft.Column):
                for sub_control in control.content.controls:
                    if isinstance(sub_control, ft.TextField):
                        if "Fecha Inicio" in control.content.controls[0].value:
                            sub_control.value = self.fecha_inicio.strftime("%Y-%m-%d")
                        elif "Fecha Fin" in control.content.controls[0].value:
                            sub_control.value = self.fecha_fin.strftime("%Y-%m-%d")
        self.filtro_custom.update()

    def _aplicar_filtro_custom(self):
        """Aplica el filtro personalizado"""
        self.tipo_reporte = "custom"
        self._actualizar_texto_filtro_header()
        self._cargar_reporte()

    def _cargar_reporte(self):
        """Carga los datos del reporte y actualiza la UI"""
        datos = self._obtener_datos_ventas()
        
        # Actualizar métricas principales
        if hasattr(self, 'texto_ventas_totales'):
            self.texto_ventas_totales.value = f"${datos['total_ventas']:,.2f}"
        if hasattr(self, 'texto_transacciones'):
            self.texto_transacciones.value = f"{datos['num_transacciones']:,}"
        if hasattr(self, 'texto_ticket_promedio'):
            self.texto_ticket_promedio.value = f"${datos['ticket_promedio']:,.2f}"
        
        # Actualizar tabla productos
        self.tabla_productos.rows.clear()
        for i, p in enumerate(datos["productos_top"]):
            self.tabla_productos.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Container(
                            content=ft.Text(str(i+1), size=12, weight=ft.FontWeight.BOLD, 
                                          color=ft.Colors.INDIGO_600),
                            width=40,
                            alignment=ft.alignment.center
                        )),
                        ft.DataCell(ft.Text(p["nombre"], size=13, weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(f"{p['cantidad']:,}", size=13, text_align=ft.TextAlign.RIGHT)),
                        ft.DataCell(ft.Text(f"${p['ingresos']:,.2f}", size=13, text_align=ft.TextAlign.RIGHT,
                                          weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_700)),
                    ],
                    color=ft.Colors.GREY_50 if i % 2 == 0 else ft.Colors.WHITE
                )
            )
        
        # Actualizar tabla ventas por tipo
        self.tabla_ventas_tipo.rows.clear()
        for tipo, monto in datos["ventas_por_tipo"].items():
            if monto > 0:  # Solo mostrar tipos con ventas
                self.tabla_ventas_tipo.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(tipo, size=13, weight=ft.FontWeight.W_500)),
                        ft.DataCell(ft.Text(f"${monto:,.2f}", size=13, text_align=ft.TextAlign.RIGHT,
                                          weight=ft.FontWeight.W_600, color=ft.Colors.BLUE_700)),
                    ])
                )
        
        self.page.update()

    def _obtener_datos_ventas(self):
        """Obtiene datos de ventas desde la base de datos con filtros de fecha"""
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

            # Consultar ventas en el rango de fechas
            fecha_inicio_str = self.fecha_inicio.strftime('%Y-%m-%d')
            fecha_fin_str = self.fecha_fin.strftime('%Y-%m-%d')
            
            
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
            total_ventas = 0

            for v in ventas:
                total_venta = v["total"] or 0.0
                total_ventas += total_venta
                
                # Determinar tipo de venta (aquí puedes implementar lógica más compleja si es necesario)
                tipo_venta = "Normal"
                ventas_por_tipo[tipo_venta] = ventas_por_tipo.get(tipo_venta, 0) + total_venta

                # Obtener detalles de la venta
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

            # Ordenar productos por ingresos (de mayor a menor)
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

    def _crear_pdf_reporte(self, datos):
        """Crea un PDF con el reporte con diseño premium"""
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        
        try:
            nombre_archivo = f"Reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            ruta_pdf = self.reportes_dir / nombre_archivo
            doc = SimpleDocTemplate(str(ruta_pdf), pagesize=letter,
                                   topMargin=0.5*inch, bottomMargin=0.5*inch,
                                   leftMargin=0.75*inch, rightMargin=0.75*inch)
            
            story = []
            
            # Colores premium
            COLOR_PRIMARY = HexColor('#4F46E5')  # Indigo
            COLOR_SECONDARY = HexColor('#10B981')  # Green
            COLOR_ACCENT = HexColor('#F59E0B')  # Amber
            COLOR_DARK = HexColor('#1F2937')
            COLOR_LIGHT_BG = HexColor('#F3F4F6')
            
            # Estilos personalizados
            estilo_titulo = ParagraphStyle(
                name="TitleCustom",
                fontSize=24,
                leading=28,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=COLOR_PRIMARY,
                fontName='Helvetica-Bold'
            )
            
            estilo_subtitulo = ParagraphStyle(
                name="SubtitleCustom",
                fontSize=11,
                leading=14,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=COLOR_DARK,
                fontName='Helvetica'
            )
            
            estilo_seccion = ParagraphStyle(
                name="SectionCustom",
                fontSize=14,
                leading=18,
                spaceAfter=12,
                spaceBefore=8,
                textColor=COLOR_PRIMARY,
                fontName='Helvetica-Bold'
            )
            
            # Encabezado del reporte
            story.append(Paragraph(f"<b>{self.datos_empresa['nombre_empresa']}</b>", estilo_titulo))
            story.append(Paragraph(f"Reporte de Ventas", estilo_subtitulo))
            story.append(Paragraph(
                f"Período: {self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}",
                estilo_subtitulo
            ))
            story.append(Spacer(1, 0.3*inch))
            
            # Tarjetas de métricas principales
            datos_metricas = [
                ["Métrica", "Valor"],
                ["Total de Ventas", f"${datos['total_ventas']:,.2f}"],
                ["Número de Transacciones", f"{datos['num_transacciones']:,}"],
                ["Ticket Promedio", f"${datos['ticket_promedio']:,.2f}"],
            ]
            
            tabla_metricas = Table(datos_metricas, colWidths=[3.5*inch, 2.5*inch])
            tabla_metricas.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Body
                ('BACKGROUND', (0, 1), (-1, -1), COLOR_LIGHT_BG),
                ('TEXTCOLOR', (0, 1), (0, -1), COLOR_DARK),
                ('TEXTCOLOR', (1, 1), (1, -1), COLOR_SECONDARY),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('TOPPADDING', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                ('LEFTPADDING', (0, 1), (-1, -1), 15),
                ('RIGHTPADDING', (0, 1), (-1, -1), 15),
                
                # Borders
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, COLOR_PRIMARY),
                ('GRID', (0, 1), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(tabla_metricas)
            story.append(Spacer(1, 0.4*inch))
            
            # Sección de Productos Más Vendidos
            story.append(Paragraph("📊 Productos Más Vendidos", estilo_seccion))
            story.append(Spacer(1, 0.15*inch))
            
            datos_productos = [["#", "Producto", "Cantidad", "Ingresos"]]
            for i, p in enumerate(datos["productos_top"][:10], 1):
                datos_productos.append([
                    str(i),
                    p["nombre"][:35] + "..." if len(p["nombre"]) > 35 else p["nombre"],
                    f"{p['cantidad']:,}",
                    f"${p['ingresos']:,.2f}"
                ])
            
            tabla_productos = Table(datos_productos, colWidths=[0.4*inch, 3*inch, 1.3*inch, 1.5*inch])
            tabla_productos.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_DARK),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('LEFTPADDING', (0, 1), (-1, -1), 8),
                ('RIGHTPADDING', (0, 1), (-1, -1), 8),
                
                # Alternating rows
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
                
                # Borders
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, COLOR_PRIMARY),
                ('GRID', (0, 1), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(tabla_productos)
            story.append(Spacer(1, 0.3*inch))
            
            # Sección de Ventas por Tipo
            story.append(Paragraph("💰 Ventas por Tipo", estilo_seccion))
            story.append(Spacer(1, 0.15*inch))
            
            datos_tipos = [["Tipo de Venta", "Monto", "Porcentaje"]]
            total = sum(datos["ventas_por_tipo"].values())
            for tipo, monto in datos["ventas_por_tipo"].items():
                if monto > 0:
                    porcentaje = (monto / total * 100) if total > 0 else 0
                    datos_tipos.append([
                        tipo,
                        f"${monto:,.2f}",
                        f"{porcentaje:.1f}%"
                    ])
            
            tabla_tipos = Table(datos_tipos, colWidths=[2.5*inch, 2*inch, 1.5*inch])
            tabla_tipos.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                
                # Body
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), COLOR_DARK),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('LEFTPADDING', (0, 1), (-1, -1), 12),
                ('RIGHTPADDING', (0, 1), (-1, -1), 12),
                
                # Alternating rows
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
                
                # Borders
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                ('LINEBELOW', (0, 0), (-1, 0), 1.5, COLOR_PRIMARY),
                ('GRID', (0, 1), (-1, -1), 0.5, colors.lightgrey),
            ]))
            story.append(tabla_tipos)
            
            # Footer
            story.append(Spacer(1, 0.5*inch))
            estilo_footer = ParagraphStyle(
                name="FooterCustom",
                fontSize=9,
                leading=11,
                alignment=TA_CENTER,
                textColor=colors.grey,
                fontName='Helvetica-Oblique'
            )
            story.append(Paragraph(
                f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} | {self.datos_empresa['nombre_empresa']}",
                estilo_footer
            ))
            
            doc.build(story)
            
            # CORRECCIÓN: Usar page.open() en lugar de page.show_snack_bar()
            self.page.open(
                ft.SnackBar(
                    content=ft.Text(f"Reporte PDF generado: {nombre_archivo}", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREEN_600
                )
            )
            
        except Exception as e:
            print(f"Error generando PDF: {e}")
            import traceback
            traceback.print_exc()
            
            # CORRECCIÓN: Usar page.open() en lugar de page.show_snack_bar()
            self.page.open(
                ft.SnackBar(
                    content=ft.Text("Error al generar el PDF", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED_600
                )
            )

    def build_ui(self):
        """Construye la interfaz de usuario premium"""
        
        # Primero crea el texto_periodo como atributo
        self.texto_periodo = ft.Text(
            self._obtener_texto_filtro_activo(), 
            size=12, 
            color=ft.Colors.GREY_600
        )
        
        # Header elegante
        self.header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.ANALYTICS_ROUNDED, size=28, color=ft.Colors.INDIGO_600),
                    ft.Column([
                        ft.Text("Reportes de Ventas", size=20, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.INDIGO_900),
                        self.texto_periodo,  # Ahora solo haces referencia al atributo ya creado
                    ], spacing=2),
                ], spacing=12),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_size=24,
                        icon_color=ft.Colors.INDIGO_700,
                        bgcolor=ft.Colors.INDIGO_50,
                        on_click=lambda e: self.admin_panel.setup_ui(),
                        tooltip="Volver al Panel"
                    ),
                    border_radius=10,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )

        # Filtros rápidos
        self.filtros_rapidos = ft.Container(
            content=ft.Row(
                spacing=12, 
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True
            ),
            padding=ft.padding.symmetric(horizontal=30, vertical=15),
            bgcolor=ft.Colors.WHITE,
            margin=ft.margin.only(top=10)
        )

        # Filtro personalizado
        self.filtro_custom = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Fecha Inicio", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        ft.TextField(
                            value=self.fecha_inicio.strftime("%Y-%m-%d"),
                            width=180,
                            height=50,
                            text_size=13,
                            border_color=ft.Colors.INDIGO_200,
                            focused_border_color=ft.Colors.INDIGO_600,
                            on_change=lambda e: self._actualizar_fecha_inicio(e.control.value)
                        ),
                    ], spacing=5),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Fecha Fin", size=11, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        ft.TextField(
                            value=self.fecha_fin.strftime("%Y-%m-%d"),
                            width=180,
                            height=50,
                            text_size=13,
                            border_color=ft.Colors.INDIGO_200,
                            focused_border_color=ft.Colors.INDIGO_600,
                            on_change=lambda e: self._actualizar_fecha_fin(e.control.value)
                        ),
                    ], spacing=5),
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SEARCH, size=18),
                            ft.Text("Aplicar Filtro", size=13, weight=ft.FontWeight.W_600),
                        ], spacing=8),
                        bgcolor=ft.Colors.INDIGO_600,
                        color=ft.Colors.WHITE,
                        height=50,
                        on_click=lambda e: self._aplicar_filtro_custom(),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        )
                    ),
                    margin=ft.margin.only(top=20),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
            padding=ft.padding.symmetric(horizontal=30, vertical=20),
            bgcolor=ft.Colors.INDIGO_50,
            border_radius=12,
            visible=False,
            margin=ft.margin.only(top=10, bottom=10)
        )

        # Métricas principales (tarjetas premium) - CORREGIDAS
        def crear_metrica(titulo, valor_inicial, icono, color_icono):
            # Crear el texto de la métrica como atributo para poder actualizarlo
            texto_metrica = ft.Text(valor_inicial, size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_900)
            
            # Guardar referencia para poder actualizar después
            if titulo == "Total Ventas":
                self.texto_ventas_totales = texto_metrica
            elif titulo == "Transacciones":
                self.texto_transacciones = texto_metrica
            elif titulo == "Ticket Promedio":
                self.texto_ticket_promedio = texto_metrica
            
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(icono, size=24, color=color_icono),
                            bgcolor=ft.Colors.with_opacity(0.1, color_icono),
                            padding=10,
                            border_radius=10,
                        ),
                    ]),
                    texto_metrica,
                    ft.Text(titulo, size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                bgcolor=ft.Colors.WHITE,
                padding=20,
                border_radius=12,
                expand=1,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                ),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            )

        self.metrica_ventas = crear_metrica("Total Ventas", "$0.00", ft.Icons.ATTACH_MONEY_ROUNDED, ft.Colors.GREEN_600)
        self.metrica_transacciones = crear_metrica("Transacciones", "0", ft.Icons.RECEIPT_LONG_ROUNDED, ft.Colors.BLUE_600)
        self.metrica_ticket = crear_metrica("Ticket Promedio", "$0.00", ft.Icons.SHOPPING_CART_ROUNDED, ft.Colors.PURPLE_600)

        self.metricas = ft.Container(
            content=ft.Row([
                self.metrica_ventas,
                self.metrica_transacciones,
                self.metrica_ticket,
            ], spacing=15),
            padding=ft.padding.symmetric(horizontal=30, vertical=15),
        )

        # Tabla de productos más vendidos
        self.tabla_productos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Container(
                    content=ft.Text("#", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=8,
                    border_radius=5,
                    alignment=ft.alignment.center
                )),
                ft.DataColumn(ft.Container(
                    content=ft.Text("Producto", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=8,
                    border_radius=5,
                )),
                ft.DataColumn(ft.Container(
                    content=ft.Text("Cantidad", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=8,
                    border_radius=5,
                ), numeric=True),
                ft.DataColumn(ft.Container(
                    content=ft.Text("Ingresos", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=8,
                    border_radius=5,
                ), numeric=True),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200),
            heading_row_color=ft.Colors.INDIGO_600,
            data_row_min_height=45,
            data_row_max_height=45,
            column_spacing=30,
        )

        # Tabla de ventas por tipo
        self.tabla_ventas_tipo = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Container(
                    content=ft.Text("Tipo de Venta", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=8,
                    border_radius=5,
                )),
                ft.DataColumn(ft.Container(
                    content=ft.Text("Monto", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=8,
                    border_radius=5,
                ), numeric=True),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_200),
            heading_row_color=ft.Colors.INDIGO_600,
            data_row_min_height=45,
            data_row_max_height=45,
            column_spacing=30,
        )

        # Botón de exportar PDF (premium)
        boton_exportar = ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.PICTURE_AS_PDF, size=20, color=ft.Colors.WHITE),
                    ft.Text("Exportar a PDF", size=14, weight=ft.FontWeight.W_600),
                ], spacing=10),
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                height=50,
                on_click=lambda e: self._crear_pdf_reporte(self._obtener_datos_ventas()),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    shadow_color=ft.Colors.with_opacity(0.3, ft.Colors.RED_600),
                    elevation=4,
                ),
            ),
            margin=ft.margin.only(top=20, bottom=20)
        )

        # Layout principal
        self.page.controls.clear()
        self.page.add(
            ft.Column([
                self.header,
                ft.Container(
                    content=ft.Column([
                        self.filtros_rapidos,
                        self.filtro_custom,
                        self.metricas,
                        
                        # Sección de productos
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, size=22, color=ft.Colors.INDIGO_600),
                                    ft.Text("Productos Más Vendidos", size=18, weight=ft.FontWeight.BOLD,
                                           color=ft.Colors.INDIGO_900),
                                ], spacing=10),
                                ft.Divider(height=1, color=ft.Colors.INDIGO_100),
                                ft.Container(
                                    content=self.tabla_productos,
                                    padding=15,
                                ),
                            ], spacing=12),
                            bgcolor=ft.Colors.WHITE,
                            border_radius=12,
                            padding=20,
                            margin=ft.margin.only(left=30, right=30, top=10),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=10,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                                offset=ft.Offset(0, 2)
                            )
                        ),
                        
                        # Sección de ventas por tipo
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.PIE_CHART_ROUNDED, size=22, color=ft.Colors.INDIGO_600),
                                    ft.Text("Ventas por Tipo", size=18, weight=ft.FontWeight.BOLD,
                                           color=ft.Colors.INDIGO_900),
                                ], spacing=10),
                                ft.Divider(height=1, color=ft.Colors.INDIGO_100),
                                ft.Container(
                                    content=self.tabla_ventas_tipo,
                                    padding=15,
                                ),
                            ], spacing=12),
                            bgcolor=ft.Colors.WHITE,
                            border_radius=12,
                            padding=20,
                            margin=ft.margin.only(left=30, right=30, top=15),
                            shadow=ft.BoxShadow(
                                spread_radius=0,
                                blur_radius=10,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                                offset=ft.Offset(0, 2)
                            )
                        ),
                        
                        # Botón exportar
                        ft.Container(
                            content=ft.Row([boton_exportar], alignment=ft.MainAxisAlignment.END),
                            padding=ft.padding.symmetric(horizontal=30),
                        ),
                        
                    ], spacing=0, scroll=ft.ScrollMode.AUTO),
                    expand=True,
                ),
            ], spacing=0, expand=True)
        )

        self._actualizar_estado_botones()
        self._cargar_reporte()

    def _actualizar_fecha_inicio(self, valor):
        """Actualiza la fecha de inicio"""
        try:
            self.fecha_inicio = datetime.strptime(valor, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        except ValueError:
            print("Formato de fecha inválido")

    def _actualizar_fecha_fin(self, valor):
        """Actualiza la fecha de fin"""
        try:
            self.fecha_fin = datetime.strptime(valor, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
        except ValueError:
            print("Formato de fecha inválido")