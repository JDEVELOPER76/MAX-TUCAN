import flet as ft
from datetime import datetime, timedelta

class GraficasWindow:
    """Ventana de gráficas interactivas con Flet - Diseño Profesional"""
    
    def __init__(self, page: ft.Page, datos_ventas, fecha_inicio, fecha_fin, reportes_window=None):
        self.page = page
        self.datos = datos_ventas
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.reportes_window = reportes_window
        self.intervalo_actual = "personalizado"
        self.panel_personalizado = None  # Referencia al panel de fechas personalizadas
        self.info_text = ft.Text(
            "Haz clic en cualquier punto, barra o sección para ver detalles",
            size=16,
            color=ft.Colors.BLUE_800,
            weight=ft.FontWeight.W_600,
            italic=True,
        )
        
        # Controles de fecha para modo personalizado
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
        
        # Paleta de colores profesional
        self.colors = {
            "primary": ft.Colors.BLUE_700,
            "secondary": ft.Colors.INDIGO_600,
            "accent": ft.Colors.CYAN_500,
            "success": ft.Colors.GREEN_600,
            "warning": ft.Colors.ORANGE_600,
            "danger": ft.Colors.RED_600,
            "light_bg": ft.Colors.GREY_50,
            "border": ft.Colors.GREY_300,
            "text_primary": ft.Colors.GREY_900,
            "text_secondary": ft.Colors.GREY_700,
            "gradient_start": ft.Colors.BLUE_800,
            "gradient_end": ft.Colors.INDIGO_900,
        }
        
        self.build_ui()
    
    def _crear_tarjeta_estadistica(self, titulo, valor, icono, color):
        """Crea tarjetas de estadísticas con diseño profesional"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icono, size=28, color=color),
                    ft.Text(titulo, size=15, color=self.colors["text_secondary"], weight=ft.FontWeight.W_600),
                ], spacing=10),
                ft.Text(
                    valor, 
                    size=32, 
                    weight=ft.FontWeight.BOLD, 
                    color=color,
                ),
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=25,
            expand=1,
            border=ft.border.all(1.5, self.colors["border"]),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            ink=True,
        )
    
    def _crear_header_grafica(self, titulo, icono, color):
        """Crea el header para las gráficas"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icono, size=26, color=ft.Colors.WHITE),
                    bgcolor=color,
                    padding=12,
                    border_radius=10,
                ),
                ft.Text(
                    titulo,
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=self.colors["text_primary"],
                ),
            ], spacing=15),
            padding=ft.padding.only(left=5, bottom=15),
        )
    
    def _generar_grafica_ventas_diarias_bonita(self):
        """Genera gráfica interactiva de ventas por día con diseño profesional"""
        try:
            ventas_por_dia = {}
            for v in self.datos.get("ventas", []):
                try:
                    fecha = v["fecha"]
                    monto = v["total"] or 0.0
                except (KeyError, TypeError):
                    continue
                ventas_por_dia[fecha] = ventas_por_dia.get(fecha, 0) + monto
            
            if not ventas_por_dia:
                return self._crear_mensaje_sin_datos("No hay datos de ventas diarias")
            
            fechas = sorted(ventas_por_dia.keys())
            montos = [ventas_por_dia[f] for f in fechas]
            
            # Puntos con diseño mejorado
            puntos = [
                ft.LineChartDataPoint(
                    x=i + 1,
                    y=monto,
                    tooltip=f"📅 {fecha}\n💰 ${monto:,.2f}",
                    selected_below_line=ft.ChartPointLine(width=3, color=self.colors["primary"]),
                    selected_point=ft.ChartCirclePoint(
                        radius=10, 
                        color=self.colors["primary"],
                        stroke_color=ft.Colors.WHITE,
                        stroke_width=3,
                    ),
                )
                for i, (fecha, monto) in enumerate(zip(fechas, montos))
            ]
            
            def on_chart_event(e: ft.LineChartEvent):
                if e.type == "tap" and e.bar_index is not None:
                    index = int(e.bar_index)
                    if 0 <= index < len(fechas):
                        self.info_text.value = f"📊 {fechas[index]}: ${montos[index]:,.2f} en ventas"
                        self.info_text.color = self.colors["primary"]
                        self.info_text.italic = False
                        self.page.update()
            
            data = ft.LineChartData(
                data_points=puntos,
                color=self.colors["primary"],
                stroke_width=4,
                curved=True,
                below_line_bgcolor=ft.Colors.with_opacity(0.1, self.colors["primary"]),
                below_line_gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[
                        ft.Colors.with_opacity(0.4, self.colors["primary"]),
                        ft.Colors.with_opacity(0.05, ft.Colors.BLUE_50),
                    ],
                ),
            )
            
            bottom_labels = [
                ft.ChartAxisLabel(
                    value=i + 1,
                    label=ft.Container(
                        ft.Text(
                            datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m"),
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=self.colors["text_secondary"],
                        ),
                        padding=5,
                    ),
                )
                for i, fecha in enumerate(fechas)
            ]
            
            max_ventas = max(montos) if montos else 100
            step = max(int(max_ventas / 6), 1)
            left_labels = [
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Container(
                        ft.Text(f"${i:,.0f}", size=14, weight=ft.FontWeight.W_600),
                        padding=ft.padding.only(right=10),
                    ),
                )
                for i in range(0, int(max_ventas) + step, step)
            ]
            
            chart = ft.LineChart(
                data_series=[data],
                border=ft.border.all(1, self.colors["border"]),
                horizontal_grid_lines=ft.ChartGridLines(
                    interval=step,
                    color=ft.Colors.GREY_200,
                    width=1,
                ),
                vertical_grid_lines=ft.ChartGridLines(
                    interval=1,
                    color=ft.Colors.GREY_200,
                    width=1,
                ),
                left_axis=ft.ChartAxis(
                    labels=left_labels,
                    title=ft.Text("Ventas ($)", size=15, weight=ft.FontWeight.BOLD),
                    title_size=30,
                    labels_size=60,
                ),
                bottom_axis=ft.ChartAxis(
                    labels=bottom_labels,
                    title=ft.Text("Fecha", size=15, weight=ft.FontWeight.BOLD),
                    title_size=25,
                    labels_size=50,
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.BLACK),
                tooltip_margin=10,
                expand=True,
                animate=800,
                max_y=max_ventas + step,
                min_y=0,
                min_x=0.5,
                max_x=len(fechas) + 0.5,
                interactive=True,
                on_chart_event=on_chart_event,
            )
            
            return ft.Column([
                self._crear_header_grafica("Tendencia de Ventas Diarias", ft.Icons.TRENDING_UP_ROUNDED, self.colors["primary"]),
                ft.Container(
                    content=chart,
                    height=400,
                    padding=10,
                ),
            ])
            
        except Exception as e:
            print(f"Error generando gráfica diaria: {e}")
            return self._crear_mensaje_sin_datos("Error al cargar los datos")
    
    def _generar_grafica_productos_bonita(self):
        """Genera gráfica interactiva de productos con diseño profesional"""
        try:
            productos_top = self.datos.get("productos_top", [])
            if not productos_top:
                return self._crear_mensaje_sin_datos("No hay datos de productos")
            
            productos_top = productos_top[:10]
            nombres = [p["nombre"][:25] + "..." if len(p["nombre"]) > 25 else p["nombre"] 
                      for p in productos_top]
            ingresos = [p["ingresos"] for p in productos_top]
            
            # Paleta de colores degradados
            colores_barra = [
                ft.Colors.BLUE_600, ft.Colors.INDIGO_600, ft.Colors.CYAN_600,
                ft.Colors.TEAL_600, ft.Colors.GREEN_600, ft.Colors.BLUE,
                ft.Colors.LIME_600, ft.Colors.AMBER_600, ft.Colors.ORANGE_600, 
                ft.Colors.DEEP_ORANGE_600
            ]
            
            def on_chart_event(e: ft.BarChartEvent):
                if e.type == "tap" and e.rod_index is not None:
                    index = int(e.rod_index)
                    if 0 <= index < len(productos_top):
                        prod = productos_top[index]
                        cantidad = prod.get('cantidad', 0)
                        self.info_text.value = f"📦 {prod['nombre']}: ${prod['ingresos']:,.2f} - {cantidad} unidades vendidas"
                        self.info_text.color = colores_barra[index % len(colores_barra)]
                        self.info_text.italic = False
                        self.page.update()
            
            bar_groups = [
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=ingreso,
                            width=35,
                            color=colores_barra[i % len(colores_barra)],
                            tooltip=f"📊 {nombres[i]}\n💰 Ingresos: ${ingreso:,.0f}\n📦 Cantidad: {productos_top[i].get('cantidad', 0)}",
                            border_radius=ft.border_radius.only(top_left=6, top_right=6),
                        ),
                    ],
                )
                for i, ingreso in enumerate(ingresos)
            ]
            
            bottom_labels = [
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Container(
                        ft.Text(
                            f"{i+1}",
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=self.colors["text_secondary"],
                        ),
                        padding=ft.padding.only(top=5),
                    ),
                )
                for i in range(len(nombres))
            ]
            
            max_ingreso = max(ingresos) if ingresos else 100
            step = max(int(max_ingreso / 5), 1)
            left_labels = [
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Container(
                        ft.Text(f"${i:,.0f}", size=14, weight=ft.FontWeight.W_600),
                        padding=ft.padding.only(right=10),
                    ),
                )
                for i in range(0, int(max_ingreso) + step, step)
            ]
            
            chart = ft.BarChart(
                bar_groups=bar_groups,
                border=ft.border.all(1, self.colors["border"]),
                horizontal_grid_lines=ft.ChartGridLines(
                    interval=step,
                    color=ft.Colors.GREY_200,
                    width=1,
                ),
                vertical_grid_lines=ft.ChartGridLines(
                    interval=1,
                    color=ft.Colors.GREY_200,
                    width=1,
                ),
                left_axis=ft.ChartAxis(
                    labels=left_labels,
                    title=ft.Text("Ingresos ($)", size=15, weight=ft.FontWeight.BOLD),
                    title_size=30,
                    labels_size=60,
                ),
                bottom_axis=ft.ChartAxis(
                    labels=bottom_labels,
                    title=ft.Text("Productos (ID)", size=15, weight=ft.FontWeight.BOLD),
                    title_size=25,
                    labels_size=50,
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.95, ft.Colors.BLACK),
                expand=True,
                animate=800,
                max_y=max_ingreso + step,
                min_y=0,
                interactive=True,
                on_chart_event=on_chart_event,
            )
            
            # Leyenda de productos
            leyenda = ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    width=12,
                                    height=12,
                                    bgcolor=colores_barra[i % len(colores_barra)],
                                    border_radius=3,
                                ),
                                ft.Text(
                                    f"{i+1}. {nombres[i][:15]}{'...' if len(nombres[i]) > 15 else ''}",
                                    size=13,
                                    color=self.colors["text_secondary"],
                                ),
                            ], spacing=6),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        )
                        for i in range(len(nombres[:5]))  # Mostrar solo primeros 5
                    ],
                    wrap=True,
                    spacing=8,
                ),
                padding=ft.padding.only(top=15, left=5),
            )
            
            return ft.Column([
                self._crear_header_grafica("Top 10 Productos por Ingresos", ft.Icons.BAR_CHART_ROUNDED, self.colors["secondary"]),
                ft.Container(
                    content=chart,
                    height=350,
                    padding=10,
                ),
                leyenda,
            ])
            
        except Exception as e:
            print(f"Error generando gráfica productos: {e}")
            return self._crear_mensaje_sin_datos("Error al cargar los productos")
    
    def _generar_grafica_pastel_bonita(self):
        """Genera gráfica de pastel interactiva con diseño profesional"""
        try:
            ventas_por_tipo_raw = self.datos.get("ventas_por_tipo", {})
            ventas_tipo = {k: v for k, v in ventas_por_tipo_raw.items() if v > 0}
            
            if not ventas_tipo:
                return self._crear_mensaje_sin_datos("No hay datos por tipo de venta")
            
            # Paleta de colores más profesional
            colores_pastel = [
                ft.Colors.BLUE_600, ft.Colors.INDIGO_600, ft.Colors.CYAN_600,
                ft.Colors.TEAL_600, ft.Colors.GREEN_600, ft.Colors.BLUE,
                ft.Colors.AMBER_600, ft.Colors.ORANGE_600, ft.Colors.PURPLE_600,
                ft.Colors.PINK_600
            ]
            
            total = sum(ventas_tipo.values())
            
            sections = []
            for i, (tipo, value) in enumerate(ventas_tipo.items()):
                porcentaje = (value/total*100)
                sections.append(
                    ft.PieChartSection(
                        value,
                        title=f"{porcentaje:.1f}%",
                        color=colores_pastel[i % len(colores_pastel)],
                        radius=100,
                        title_style=ft.TextStyle(
                            size=16,
                            color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD,
                        ),
                        badge=ft.Container(
                            ft.Text(
                                tipo[:8] + ('...' if len(tipo) > 8 else ''),
                                size=12,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                            ),
                            bgcolor=colores_pastel[i % len(colores_pastel)],
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=12,
                        ),
                        badge_position=0.7,
                    )
                )
            
            def on_chart_event(e: ft.PieChartEvent):
                if e.type == "tap" and e.section_index is not None:
                    index = int(e.section_index)
                    tipos = list(ventas_tipo.keys())
                    if 0 <= index < len(tipos):
                        tipo = tipos[index]
                        valor = ventas_tipo[tipo]
                        porcentaje = (valor/total*100)
                        self.info_text.value = f"📊 {tipo}: ${valor:,.2f} ({porcentaje:.1f}% del total)"
                        self.info_text.color = colores_pastel[index % len(colores_pastel)]
                        self.info_text.italic = False
                        self.page.update()
            
            chart = ft.PieChart(
                sections=sections,
                sections_space=2,
                center_space_radius=50,
                expand=True,
                animate=800,
                on_chart_event=on_chart_event,
                start_degree_offset=90,
            )
            
            # Leyenda interactiva
            leyenda = ft.GridView(
                expand=True,
                max_extent=200,
                spacing=10,
                run_spacing=10,
                padding=10,
            )
            
            for i, (tipo, value) in enumerate(ventas_tipo.items()):
                porcentaje = (value/total*100)
                leyenda.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                width=16,
                                height=16,
                                bgcolor=colores_pastel[i % len(colores_pastel)],
                                border_radius=4,
                            ),
                            ft.Column([
                                ft.Text(
                                    tipo[:20] + ('...' if len(tipo) > 20 else ''),
                                    size=14,
                                    weight=ft.FontWeight.W_600,
                                    color=self.colors["text_primary"],
                                ),
                                ft.Text(
                                    f"${value:,.0f} ({porcentaje:.1f}%)",
                                    size=13,
                                    color=self.colors["text_secondary"],
                                ),
                            ], spacing=2, tight=True),
                        ], spacing=12),
                        padding=12,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        border=ft.border.all(1, self.colors["border"]),
                        ink=True,
                        on_click=lambda e, idx=i: self._actualizar_info_pastel(idx, tipos=list(ventas_tipo.keys()), 
                                                                               valores=list(ventas_tipo.values()), 
                                                                               total=total, colores=colores_pastel),
                    )
                )
            
            return ft.Column([
                self._crear_header_grafica("Distribución por Tipo de Venta", ft.Icons.PIE_CHART_ROUNDED, self.colors["accent"]),
                ft.Row([
                    ft.Container(
                        content=chart,
                        width=350,
                        height=350,
                        padding=10,
                    ),
                    ft.Container(
                        content=leyenda,
                        width=400,
                        height=350,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ])
            
        except Exception as e:
            print(f"Error generando gráfica pastel: {e}")
            return self._crear_mensaje_sin_datos("Error al cargar la distribución")
    
    def _actualizar_info_pastel(self, index, tipos, valores, total, colores):
        """Actualiza la información al hacer clic en la leyenda"""
        if 0 <= index < len(tipos):
            porcentaje = (valores[index]/total*100)
            self.info_text.value = f"📊 {tipos[index]}: ${valores[index]:,.2f} ({porcentaje:.1f}% del total)"
            self.info_text.color = colores[index % len(colores)]
            self.info_text.italic = False
            self.page.update()
    
    def _crear_mensaje_sin_datos(self, mensaje):
        """Crea un mensaje profesional cuando no hay datos"""
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=64, color=ft.Colors.GREY_400),
                ft.Text(
                    mensaje,
                    size=16,
                    color=ft.Colors.GREY_600,
                    weight=ft.FontWeight.W_600,
                ),
                ft.Text(
                    "Intenta seleccionar un rango de fechas diferente",
                    size=14,
                    color=ft.Colors.GREY_500,
                    italic=True,
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=50,
            height=400,
            border=ft.border.all(1, ft.Colors.GREY_200),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
        )
    
    def _cambiar_intervalo(self, intervalo):
        """Cambia el intervalo de tiempo y actualiza las gráficas"""
        self.intervalo_actual = intervalo
        hoy = datetime.now()
        
        if intervalo == "dia":
            self.fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
        elif intervalo == "semana":
            # Inicio de la semana (lunes)
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            self.fecha_inicio = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
        elif intervalo == "mes":
            self.fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
        elif intervalo == "año":
            self.fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.fecha_fin = hoy
        
        # No cambiar fechas si es personalizado, solo actualizar la UI
        if intervalo != "personalizado":
            # Actualizar los campos de fecha
            self.fecha_inicio_picker.value = self.fecha_inicio.strftime("%Y-%m-%d")
            self.fecha_fin_picker.value = self.fecha_fin.strftime("%Y-%m-%d")
            
            # Recargar datos si existe reportes_window
            if self.reportes_window:
                self._recargar_datos()
            else:
                self.build_ui()
        else:
            # Solo actualizar la UI para mostrar el panel personalizado
            if self.panel_personalizado:
                self.panel_personalizado.visible = True
            self.build_ui()
    
    def _recargar_datos(self):
        """Recarga los datos desde reportes_window con las nuevas fechas"""
        if self.reportes_window:
            # Llamar al método de reportes para obtener nuevos datos
            try:
                # Pasar las fechas como parámetros
                self.datos = self.reportes_window._obtener_datos_ventas(self.fecha_inicio, self.fecha_fin)
                self.build_ui()
            except Exception as e:
                print(f"Error recargando datos: {e}")
                import traceback
                traceback.print_exc()
                self.build_ui()
    
    def _aplicar_fechas_personalizadas(self, e):
        """Aplica las fechas personalizadas ingresadas"""
        try:
            fecha_inicio_str = self.fecha_inicio_picker.value
            fecha_fin_str = self.fecha_fin_picker.value
            
            nueva_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
            nueva_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
            
            if nueva_inicio > nueva_fin:
                # Mostrar error
                self.info_text.value = "⚠️ La fecha de inicio debe ser anterior a la fecha de fin"
                self.info_text.color = self.colors["danger"]
                self.page.update()
                return
            
            self.fecha_inicio = nueva_inicio
            self.fecha_fin = nueva_fin
            self.intervalo_actual = "personalizado"
            
            self._recargar_datos()
            
        except ValueError as e:
            self.info_text.value = "⚠️ Formato de fecha inválido. Use YYYY-MM-DD"
            self.info_text.color = self.colors["danger"]
            self.page.update()
    
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
    
    def _crear_panel_intervalos(self):
        """Crea el panel de selección de intervalos"""
        
        def crear_boton_intervalo(texto, icono, intervalo, color):
            es_activo = self.intervalo_actual == intervalo
            return ft.Container(
                content=ft.Column([
                    ft.Icon(
                        icono, 
                        size=28, 
                        color=ft.Colors.WHITE if es_activo else color
                    ),
                    ft.Text(
                        texto,
                        size=14,
                        weight=ft.FontWeight.BOLD if es_activo else ft.FontWeight.W_500,
                        color=ft.Colors.WHITE if es_activo else self.colors["text_primary"],
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
                    offset=ft.Offset(0, 3)
                ) if es_activo else None,
            )
        
        # Panel de fechas personalizadas
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
                        ft.Icon(ft.Icons.DATE_RANGE_ROUNDED, size=24, color=self.colors["text_primary"]),
                        ft.Text(
                            "Intervalo de Tiempo",
                            size=16,
                            weight=ft.FontWeight.W_600,
                            color=self.colors["text_primary"],
                        ),
                    ], spacing=10),
                    ft.Row([
                        crear_boton_intervalo("Día", ft.Icons.TODAY_ROUNDED, "dia", self.colors["primary"]),
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
            border=ft.border.all(1.5, self.colors["border"]),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )
    
    def build_ui(self):
        """Construye la interfaz con diseño profesional"""
        self.page.bgcolor = self.colors["light_bg"]
        self.page.padding = 0
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.scroll = ft.ScrollMode.AUTO
        
        # Generar gráficas
        grafica_diarias = self._generar_grafica_ventas_diarias_bonita()
        grafica_productos = self._generar_grafica_productos_bonita()
        grafica_pastel = self._generar_grafica_pastel_bonita()
        
        # Header con diseño mejorado
        header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=30, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        padding=12,
                        border_radius=12,
                    ),
                    ft.Column([
                        ft.Text(
                            "Panel de Análisis de Ventas",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            f"{self.fecha_inicio.strftime('%d de %B, %Y')} - {self.fecha_fin.strftime('%d de %B, %Y')}",
                            size=13,
                            color=ft.Colors.BLUE_100,
                        ),
                    ], spacing=2),
                ], spacing=20),
                ft.Container(
                    content=ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_size=22,
                        icon_color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        on_click=lambda e: self._retroceder(),
                        tooltip="Volver a Reportes",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        ),
                    ),
                    border_radius=10,
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=40, vertical=25),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[self.colors["gradient_start"], self.colors["gradient_end"]],
            ),
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=20,
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                offset=ft.Offset(0, 5),
            ),
        )
        
        # Calcular estadísticas
        ventas_list = self.datos.get("ventas", [])
        try:
            total_ventas = sum([v["total"] or 0 for v in ventas_list])
        except (KeyError, TypeError):
            total_ventas = 0
        num_ventas = len(ventas_list)
        promedio = total_ventas / num_ventas if num_ventas > 0 else 0
        productos_vendidos = len(self.datos.get("productos_top", []))
        
        # Panel de estadísticas
        stats_panel = ft.Container(
            content=ft.Row([
                self._crear_tarjeta_estadistica(
                    "Ventas Totales", 
                    f"${total_ventas:,.2f}", 
                    ft.Icons.ATTACH_MONEY_ROUNDED,
                    self.colors["primary"]
                ),
                self._crear_tarjeta_estadistica(
                    "Ticket Promedio", 
                    f"${promedio:,.2f}", 
                    ft.Icons.ANALYTICS_ROUNDED,
                    self.colors["success"]
                ),
                self._crear_tarjeta_estadistica(
                    "Transacciones", 
                    f"{num_ventas}", 
                    ft.Icons.RECEIPT_ROUNDED,
                    self.colors["warning"]
                ),
                self._crear_tarjeta_estadistica(
                    "Productos", 
                    f"{productos_vendidos}", 
                    ft.Icons.INVENTORY_ROUNDED,
                    self.colors["danger"]
                ),
            ], spacing=20),
            margin=ft.margin.only(left=40, right=40, top=25, bottom=15),
        )
        
        # Contenedor de gráficas con diseño mejorado
        def crear_contenedor_grafica(contenido):
            if isinstance(contenido, ft.Container) and contenido.content is None:
                return contenido
            
            return ft.Container(
                content=contenido,
                bgcolor=ft.Colors.WHITE,
                border_radius=16,
                padding=25,
                margin=ft.margin.only(left=40, right=40, top=20),
                border=ft.border.all(1.5, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=20,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                    offset=ft.Offset(0, 5),
                ),
            )
        
        # Panel de información interactiva mejorado
        info_panel = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.INFO_OUTLINE_ROUNDED, size=26, color=self.colors["primary"]),
                    bgcolor=ft.Colors.with_opacity(0.1, self.colors["primary"]),
                    padding=12,
                    border_radius=10,
                ),
                ft.Container(
                    content=self.info_text,
                    expand=True,
                ),
            ], spacing=18),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=25,
            margin=ft.margin.only(left=40, right=40, top=20, bottom=40),
            border=ft.border.all(1.5, self.colors["border"]),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                offset=ft.Offset(0, 4),
            ),
        )
        
        # Contenido principal
        contenido = ft.Column([
            header,
            self._crear_panel_intervalos(),
            stats_panel,
            crear_contenedor_grafica(grafica_diarias),
            crear_contenedor_grafica(grafica_productos),
            crear_contenedor_grafica(grafica_pastel),
            info_panel,
        ], spacing=0, scroll=ft.ScrollMode.AUTO)
        
        self.page.clean()
        self.page.add(contenido)
    
    def _retroceder(self):
        """Retrocede a la ventana de reportes"""
        if self.reportes_window:
            self.reportes_window.build_ui()