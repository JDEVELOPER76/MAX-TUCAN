# admin_panels/configuraciones_window.py
import flet as ft
from flet import (
    Icons, Colors, FontWeight, MainAxisAlignment, CrossAxisAlignment
)
import json
from pathlib import Path
import shutil 
from admin_panels.info_software_window import InfoSoftwareWindow

class ConfiguracionesWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel
        self.json_dir = Path("./Json files")
        self.logos_dir = Path("./assets/logos")
        self.empresa_file = self.json_dir / "datos_empresariales.json"
        self.facturas_file = self.json_dir / "configuracion_facturas.json"
        self.email_file = self.json_dir / "email.json"
        self._ensure_directories()
        self.datos_empresa = self._cargar_datos_empresa()
        self.config_facturas = self._cargar_config_facturas()
        self.config_email = self._cargar_config_email()
        
        self.file_picker = ft.FilePicker(on_result=self._file_picker_result)
        self.page.overlay.append(self.file_picker)
        self.logo_field = None

    def _ensure_directories(self):
        self.json_dir.mkdir(exist_ok=True)
        self.logos_dir.mkdir(parents=True, exist_ok=True)

    def _cargar_datos_empresa(self):
        datos_default = {
            "nombre_empresa": "MI EMPRESA",
            "direccion": "Calle Principal #123, Ciudad",
            "correo_electronico": "usertest@maxtucan.com",
            "numero_telefono": "+00000000000000",
            "logo_empresa": ""
        }
        
        try:
            if self.empresa_file.exists():
                with open(self.empresa_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(self.empresa_file, 'w', encoding='utf-8') as f:
                    json.dump(datos_default, f, indent=4, ensure_ascii=False)
                return datos_default
        except Exception as e:
            print(f"Error cargando datos empresariales: {e}")
            return datos_default

    def _cargar_config_facturas(self):
        config_default = {
            "serie_facturas": "A",
            "folio_actual": "00000000000001",
            "siguiente_folio": "00000000000002",
            "formato_pdf": True,
            "incluir_logo": True,
            "incluir_direccion": True,
            "incluir_contacto": True,
            "leyenda_pie_pagina": "Gracias por su preferencia"
        }
        
        try:
            if self.facturas_file.exists():
                with open(self.facturas_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(self.facturas_file, 'w', encoding='utf-8') as f:
                    json.dump(config_default, f, indent=4, ensure_ascii=False)
                return config_default
        except Exception as e:
            print(f"Error cargando configuración de facturas: {e}")
            return config_default

    def _cargar_config_email(self):
        config_default = {
            "servidor_smtp": "smtp.gmail.com",
            "puerto": 587,
            "email_remitente": "facturacion@tuempresa.com",
            "password_app": "",
            "usar_ssl": False,
            "usar_tls": True,
            "timeout": 30,
            "enviar_facturas_auto": False,
            "asunto_factura": "Factura #{numero_factura} - {empresa}",
            "cuerpo_factura": "Estimado {cliente},\n\nAdjuntamos su factura #{numero_factura} por un total de ${total}.\n\nGracias por su preferencia."
        }
        
        try:
            if self.email_file.exists():
                with open(self.email_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(self.email_file, 'w', encoding='utf-8') as f:
                    json.dump(config_default, f, indent=4, ensure_ascii=False)
                return config_default
        except Exception as e:
            print(f"Error cargando configuración de email: {e}")
            return config_default

    def _guardar_datos_empresa(self, datos):
        try:
            with open(self.empresa_file, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
            self.datos_empresa = datos
            return True
        except Exception as e:
            print(f"Error guardando datos empresariales: {e}")
            return False
        
    def _abrir_info_software(self, e):
        info_window = InfoSoftwareWindow(self.page, self.admin_panel)
        self.page.clean()  # Limpiamos la UI actual
        self.page.add(info_window.build_ui())
        self.page.update()


    def _guardar_config_facturas(self, config):
        try:
            with open(self.facturas_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.config_facturas = config
            return True
        except Exception as e:
            print(f"Error guardando configuración de facturas: {e}")
            return False

    def _guardar_config_email(self, config):
        try:
            with open(self.email_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.config_email = config
            return True
        except Exception as e:
            print(f"Error guardando configuración de email: {e}")
            return False

    def _file_picker_result(self, e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            archivo_seleccionado = e.files[0]
            
            extensiones_validas = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            extension = Path(archivo_seleccionado.name).suffix.lower()
            
            if extension not in extensiones_validas:
                self._mostrar_mensaje_error(f"Formato no válido. Use: {', '.join(extensiones_validas)}")
                return
            
            try:
                nombre_logo = f"logo_empresa{extension}"
                ruta_destino = self.logos_dir / nombre_logo
                
                shutil.copy2(archivo_seleccionado.path, ruta_destino)
                
                ruta_relativa = str(ruta_destino)
                if self.logo_field:
                    self.logo_field.value = ruta_relativa
                    self.logo_field.update()
                
                self._mostrar_mensaje_exito(f"Logo cargado exitosamente: {nombre_logo}")
                
            except Exception as ex:
                self._mostrar_mensaje_error(f"Error al cargar el logo: {str(ex)}")

    def build_ui(self):
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=Icons.ARROW_BACK,
                    icon_size=24,
                    icon_color=Colors.INDIGO_600,
                    on_click=self._go_back
                ),
                ft.Text("Configuraciones", size=24, weight=FontWeight.W_600,
                        color=Colors.INDIGO_900),
            ], vertical_alignment=CrossAxisAlignment.CENTER, spacing=12),
            padding=ft.padding.only(left=16, right=24, top=18, bottom=18),
            bgcolor=Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8, 
                color=ft.Colors.with_opacity(0.08, Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        )
        config_cards = ft.ResponsiveRow([
            ft.Container(self._config_card_empresa(), col={"sm": 12, "md": 6}, padding=8),
            ft.Container(self._config_card_facturas(), col={"sm": 12, "md": 6}, padding=8),
            ft.Container(self._config_card_email(), col={"sm": 12, "md": 6}, padding=8),
            ft.Container(self._config_card_sistema(), col={"sm": 12, "md": 6}, padding=8),
        ])

        main_content = ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=ft.Column([
                        ft.Text("Configuración del Sistema", size=20, weight=FontWeight.W_500, color=Colors.INDIGO_700),
                        ft.Text("Administra la configuración general de tu empresa y sistema", size=14, color=Colors.GREY_600),
                        ft.Divider(height=20, thickness=1, color=Colors.INDIGO_100),
                        config_cards,
                        ft.Container(height=20)
                    ], spacing=16),
                    padding=24,
                    expand=True
                )
            ], scroll=ft.ScrollMode.ADAPTIVE, spacing=0),
            expand=True
        )

        return main_content

    def _config_card_empresa(self):
        def btn_editar():
            return ft.IconButton(
                icon=Icons.EDIT, icon_size=18, icon_color=Colors.INDIGO_600,
                on_click=self._editar_informacion_empresa, tooltip="Editar información de la empresa"
            )

        logo_status = "No configurado"
        if self.datos_empresa.get("logo_empresa"):
            logo_path = Path(self.datos_empresa.get("logo_empresa"))
            if logo_path.exists():
                logo_status = f"✓ {logo_path.name}"
            else:
                logo_status = "⚠ Archivo no encontrado"

        option_rows = [
            ft.Row([
                ft.Text("Nombre de la empresa", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.datos_empresa.get("nombre_empresa", "N/A"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Dirección", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.datos_empresa.get("direccion", "N/A")[:30] + "..." if len(self.datos_empresa.get("direccion", "")) > 30 else self.datos_empresa.get("direccion", "N/A"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Correo electrónico", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.datos_empresa.get("correo_electronico", "N/A"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Número de teléfono", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.datos_empresa.get("numero_telefono", "N/A"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Logo de la empresa", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(logo_status, size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700 if "✓" in logo_status else Colors.ORANGE_600, expand=1),
            ]),
        ]

        return ft.Card(
            elevation=0,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(Icons.BUSINESS, size=24, color=Colors.INDIGO_600),
                        ft.Text("Información de la Empresa", size=16, weight=FontWeight.W_600, color=Colors.INDIGO_900, expand=True),
                        btn_editar()
                    ]),
                    ft.Text("Configura los datos básicos de tu empresa", size=13, color=Colors.GREY_600),
                    ft.Divider(height=12, thickness=1, color=Colors.INDIGO_100),
                    *option_rows
                ], spacing=10),
                padding=20, bgcolor=Colors.WHITE, border_radius=12,
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color=ft.Colors.with_opacity(0.07, Colors.BLACK), offset=ft.Offset(0, 2)),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                on_hover=lambda e: self._hover_card(e, 1.02)
            )
        )

    def _config_card_facturas(self):
        def btn_editar():
            return ft.IconButton(
                icon=Icons.EDIT, icon_size=18, icon_color=Colors.INDIGO_600,
                on_click=self._editar_configuracion_facturas, tooltip="Configurar facturas PDF"
            )

        estado_logo = "✓ Incluir" if self.config_facturas.get("incluir_logo", True) else "✗ Excluir"
        estado_direccion = "✓ Incluir" if self.config_facturas.get("incluir_direccion", True) else "✗ Excluir"
        estado_contacto = "✓ Incluir" if self.config_facturas.get("incluir_contacto", True) else "✗ Excluir"

        option_rows = [
            ft.Row([
                ft.Text("Serie de facturas", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.config_facturas.get("serie_facturas", "A"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Folio actual", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.config_facturas.get("folio_actual", "0001"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Formato PDF", size=13, color=Colors.GREY_700, expand=2),
                ft.Text("Activado" if self.config_facturas.get("formato_pdf", True) else "Desactivado", size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Logo empresa", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(estado_logo, size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Dirección", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(estado_direccion, size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Contacto", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(estado_contacto, size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
        ]

        return ft.Card(
            elevation=0,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(Icons.RECEIPT_LONG, size=24, color=Colors.INDIGO_600),
                        ft.Text("Facturas PDF", size=16, weight=FontWeight.W_600, color=Colors.INDIGO_900, expand=True),
                        btn_editar()
                    ]),
                    ft.Text("Configuración de folios y formato de facturas", size=13, color=Colors.GREY_600),
                    ft.Divider(height=12, thickness=1, color=Colors.INDIGO_100),
                    *option_rows
                ], spacing=10),
                padding=20, bgcolor=Colors.WHITE, border_radius=12,
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color=ft.Colors.with_opacity(0.07, Colors.BLACK), offset=ft.Offset(0, 2)),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                on_hover=lambda e: self._hover_card(e, 1.02)
            )
        )

    def _config_card_email(self):
        def btn_editar():
            return ft.IconButton(
                icon=Icons.EDIT, icon_size=18, icon_color=Colors.INDIGO_600,
                on_click=self._editar_configuracion_email, tooltip="Configurar envío de emails"
            )

        estado_servicio = "✓ Configurado" if self.config_email.get("email_remitente") and self.config_email.get("password_app") else "⚠ Sin configurar"
        estado_auto = "✓ Activado" if self.config_email.get("enviar_facturas_auto") else "✗ Desactivado"

        option_rows = [
            ft.Row([
                ft.Text("Servicio de Email", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(estado_servicio, size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700 if "✓" in estado_servicio else Colors.ORANGE_600, expand=1),
            ]),
            ft.Row([
                ft.Text("Servidor SMTP", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.config_email.get("servidor_smtp", "No configurado"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Email remitente", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(self.config_email.get("email_remitente", "No configurado"), size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
            ft.Row([
                ft.Text("Envío automático", size=13, color=Colors.GREY_700, expand=2),
                ft.Text(estado_auto, size=13, weight=FontWeight.W_500, color=Colors.INDIGO_700, expand=1),
            ]),
        ]

        return ft.Card(
            elevation=0,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(Icons.EMAIL, size=24, color=Colors.INDIGO_600),
                        ft.Text("Envío de Emails", size=16, weight=FontWeight.W_600, color=Colors.INDIGO_900, expand=True),
                        btn_editar()
                    ]),
                    ft.Text("Configuración para envío de facturas por email", size=13, color=Colors.GREY_600),
                    ft.Divider(height=12, thickness=1, color=Colors.INDIGO_100),
                    *option_rows
                ], spacing=10),
                padding=20, bgcolor=Colors.WHITE, border_radius=12,
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color=ft.Colors.with_opacity(0.07, Colors.BLACK), offset=ft.Offset(0, 2)),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                on_hover=lambda e: self._hover_card(e, 1.02)
            )
        )

    def _config_card_sistema(self):
        btn_info_software = ft.ElevatedButton(
            text="Información del Software",
            icon=ft.Icons.INFO,
            bgcolor=ft.Colors.INDIGO_600,
            color=ft.Colors.WHITE,
            on_click=self._abrir_info_software
        )

        return ft.Card(
            elevation=0,
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SETTINGS, size=24, color=ft.Colors.INDIGO_600),
                        ft.Text("Sistema", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.INDIGO_900, expand=True),
                    ]),
                    ft.Text("Ajustes generales del sistema", size=13, color=ft.Colors.GREY_600),
                    ft.Divider(height=12, thickness=1, color=ft.Colors.INDIGO_100),
                    ft.Row([ft.Text("Versión: 1.1.0", size=13, color=ft.Colors.GREY_700)]),
                    ft.Row([ft.Text("Base de datos: SQLite3", size=13, color=ft.Colors.GREY_700)]),
                    ft.Row([ft.Text("Backup: Manual", size=13, color=ft.Colors.GREY_700)]),
                    ft.Container(height=10),
                    btn_info_software
                ], spacing=10),
                padding=20, bgcolor=ft.Colors.WHITE, border_radius=12,
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=6, color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK), offset=ft.Offset(0, 2)),
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                on_hover=lambda e: self._hover_card(e, 1.02)
            )
        )


    def _hover_card(self, e, scale):
        e.control.scale = scale if e.data == "true" else 1.0
        e.control.update()

    def _go_back(self, e):
        self.admin_panel.setup_ui()

    def _editar_informacion_empresa(self, e=None):
        nombre_field = ft.TextField(label="Nombre de la empresa", value=self.datos_empresa.get("nombre_empresa", ""), expand=True, border_color=Colors.INDIGO_200)
        direccion_field = ft.TextField(label="Dirección", value=self.datos_empresa.get("direccion", ""), expand=True, multiline=True, max_lines=3, border_color=Colors.INDIGO_200)
        correo_field = ft.TextField(label="Correo electrónico", value=self.datos_empresa.get("correo_electronico", ""), expand=True, border_color=Colors.INDIGO_200)
        telefono_field = ft.TextField(label="Número de teléfono", value=self.datos_empresa.get("numero_telefono", ""), expand=True, border_color=Colors.INDIGO_200)
        
        self.logo_field = ft.TextField(label="Logo de la empresa", value=self.datos_empresa.get("logo_empresa", ""), expand=True, read_only=True, border_color=Colors.INDIGO_200, hint_text="Selecciona un archivo de imagen")
        
        logo_preview = ft.Container(
            content=ft.Column([
                ft.Text("Vista previa del logo:", size=12, color=Colors.GREY_600),
                ft.Container(content=self._get_logo_preview(self.datos_empresa.get("logo_empresa", "")), width=150, height=150, bgcolor=Colors.GREY_100, border_radius=8, alignment=ft.alignment.center)
            ], spacing=8), visible=bool(self.datos_empresa.get("logo_empresa"))
        )
        
        def seleccionar_logo(e):
            self.file_picker.pick_files(dialog_title="Seleccionar logo de la empresa", allowed_extensions=["png", "jpg", "jpeg", "gif", "bmp"], allow_multiple=False)

        btn_seleccionar_logo = ft.ElevatedButton(
            content=ft.Row([ft.Icon(Icons.UPLOAD_FILE, size=18), ft.Text("Seleccionar Logo")], spacing=8),
            on_click=seleccionar_logo, style=ft.ButtonStyle(color=Colors.INDIGO_600, bgcolor=Colors.INDIGO_50, shape=ft.RoundedRectangleBorder(radius=8))
        )

        def guardar_cambios(_):
            nuevos_datos = {
                "nombre_empresa": nombre_field.value,
                "direccion": direccion_field.value,
                "correo_electronico": correo_field.value,
                "numero_telefono": telefono_field.value,
                "logo_empresa": self.logo_field.value
            }
            
            if self._guardar_datos_empresa(nuevos_datos):
                self.page.close(dlg_empresa)
                self._mostrar_mensaje_exito("Información de la empresa actualizada correctamente")
                self.page.clean()
                self.page.add(self.build_ui())
                self.page.update()
            else:
                self._mostrar_mensaje_error("Error al guardar los datos")

        dlg_empresa = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(Icons.BUSINESS, color=Colors.INDIGO_600), ft.Text("Editar Información de la Empresa")], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    nombre_field, direccion_field, correo_field, telefono_field,
                    ft.Divider(height=10, color=Colors.INDIGO_100),
                    ft.Text("Logo de la Empresa", size=14, weight=FontWeight.W_500, color=Colors.INDIGO_700),
                    ft.Row([self.logo_field, btn_seleccionar_logo], spacing=10),
                    logo_preview,
                ], spacing=12, scroll=ft.ScrollMode.ADAPTIVE), width=550, height=500
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_empresa)),
                ft.ElevatedButton("Guardar", on_click=guardar_cambios, style=ft.ButtonStyle(color=Colors.WHITE, bgcolor=Colors.INDIGO_600)),
            ], actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg_empresa)

    def _get_logo_preview(self, logo_path):
        if not logo_path or not Path(logo_path).exists():
            return ft.Column([
                ft.Icon(Icons.IMAGE_NOT_SUPPORTED, size=40, color=Colors.GREY_400),
                ft.Text("Sin logo", size=12, color=Colors.GREY_500)
            ], horizontal_alignment=CrossAxisAlignment.CENTER, alignment=MainAxisAlignment.CENTER)
        
        try:
            return ft.Image(src=logo_path, width=140, height=140, fit=ft.ImageFit.CONTAIN)
        except Exception as e:
            return ft.Icon(Icons.BROKEN_IMAGE, size=40, color=Colors.ORANGE_400)

    def _editar_configuracion_facturas(self, e=None):
        serie_field = ft.TextField(label="Serie de facturas", value=self.config_facturas.get("serie_facturas", "A"), expand=True, border_color=Colors.INDIGO_200)
        folio_field = ft.TextField(label="Folio actual", value=self.config_facturas.get("folio_actual", "0001"), expand=True, border_color=Colors.INDIGO_200)
        formato_pdf = ft.Switch(label="Generar facturas en PDF", value=self.config_facturas.get("formato_pdf", True), active_color=Colors.INDIGO_600)
        incluir_logo = ft.Switch(label="Incluir logo de la empresa", value=self.config_facturas.get("incluir_logo", True), active_color=Colors.INDIGO_600)
        incluir_direccion = ft.Switch(label="Incluir dirección", value=self.config_facturas.get("incluir_direccion", True), active_color=Colors.INDIGO_600)
        incluir_contacto = ft.Switch(label="Incluir información de contacto", value=self.config_facturas.get("incluir_contacto", True), active_color=Colors.INDIGO_600)
        leyenda_field = ft.TextField(label="Leyenda pie de página", value=self.config_facturas.get("leyenda_pie_pagina", "Gracias por su preferencia"), multiline=True, max_lines=3, expand=True, border_color=Colors.INDIGO_200)

        def guardar_cambios(_):
            nueva_config = {
                "serie_facturas": serie_field.value,
                "folio_actual": folio_field.value,
                "siguiente_folio": str(int(folio_field.value) + 1).zfill(4),
                "formato_pdf": formato_pdf.value,
                "incluir_logo": incluir_logo.value,
                "incluir_direccion": incluir_direccion.value,
                "incluir_contacto": incluir_contacto.value,
                "leyenda_pie_pagina": leyenda_field.value
            }
            
            if self._guardar_config_facturas(nueva_config):
                self.page.close(dlg_facturas)
                self._mostrar_mensaje_exito("Configuración de facturas actualizada correctamente")
                self.page.clean()
                self.page.add(self.build_ui())
                self.page.update()
            else:
                self._mostrar_mensaje_error("Error al guardar la configuración")

        dlg_facturas = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(Icons.RECEIPT_LONG, color=Colors.INDIGO_600), ft.Text("Configuración de Facturas PDF")], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([serie_field, folio_field]), formato_pdf,
                    ft.Divider(height=10, color=Colors.INDIGO_100),
                    ft.Text("Elementos a incluir en las facturas:", size=14, weight=FontWeight.W_500, color=Colors.INDIGO_700),
                    incluir_logo, incluir_direccion, incluir_contacto,
                    ft.Divider(height=10, color=Colors.INDIGO_100), leyenda_field,
                ], spacing=12, scroll=ft.ScrollMode.ADAPTIVE), width=500, height=450
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_facturas)),
                ft.ElevatedButton("Guardar", on_click=guardar_cambios, style=ft.ButtonStyle(color=Colors.WHITE, bgcolor=Colors.INDIGO_600)),
            ], actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg_facturas)

    def _editar_configuracion_email(self, e=None):
        servidor_field = ft.TextField(label="Servidor SMTP", value=self.config_email.get("servidor_smtp", "smtp.gmail.com"), expand=True, border_color=Colors.INDIGO_200, hint_text="Ej: smtp.gmail.com, smtp.office365.com")
        puerto_field = ft.TextField(label="Puerto", value=str(self.config_email.get("puerto", 587)), expand=True, border_color=Colors.INDIGO_200, keyboard_type=ft.KeyboardType.NUMBER)
        email_field = ft.TextField(label="Email remitente", value=self.config_email.get("email_remitente", ""), expand=True, border_color=Colors.INDIGO_200, hint_text="facturacion@tuempresa.com")
        password_field = ft.TextField(label="Contraseña de aplicación", value=self.config_email.get("password_app", ""), expand=True, password=True, can_reveal_password=True, border_color=Colors.INDIGO_200, hint_text="Contraseña de aplicación, NO la normal")
        usar_tls = ft.Switch(label="Usar TLS (recomendado)", value=self.config_email.get("usar_tls", True), active_color=Colors.INDIGO_600)
        enviar_auto = ft.Switch(label="Envío automático de facturas", value=self.config_email.get("enviar_facturas_auto", False), active_color=Colors.INDIGO_600)
        asunto_field = ft.TextField(label="Asunto del email", value=self.config_email.get("asunto_factura", "Factura #{numero_factura} - {empresa}"), multiline=True, max_lines=2, expand=True, border_color=Colors.INDIGO_200, hint_text="Variables: {numero_factura}, {empresa}, {cliente}, {total}")
        cuerpo_field = ft.TextField(label="Cuerpo del email", value=self.config_email.get("cuerpo_factura", ""), multiline=True, max_lines=5, expand=True, border_color=Colors.INDIGO_200, hint_text="Texto que aparecerá en el cuerpo del email")

        info_help = ft.Container(
            content=ft.Column([
                ft.Text("Variables disponibles:", size=12, weight=FontWeight.W_500, color=Colors.INDIGO_600),
                ft.Text("{numero_factura} - Número de factura", size=11, color=Colors.GREY_600),
                ft.Text("{empresa} - Nombre de la empresa", size=11, color=Colors.GREY_600),
                ft.Text("{cliente} - Nombre del cliente", size=11, color=Colors.GREY_600),
                ft.Text("{total} - Total de la factura", size=11, color=Colors.GREY_600),
                ft.Text("{fecha} - Fecha de emisión", size=11, color=Colors.GREY_600),
            ], spacing=4), bgcolor=Colors.INDIGO_50, padding=10, border_radius=8
        )

        def guardar_cambios(_):
            nueva_config = {
                "servidor_smtp": servidor_field.value,
                "puerto": int(puerto_field.value) if puerto_field.value else 587,
                "email_remitente": email_field.value,
                "password_app": password_field.value,
                "usar_tls": usar_tls.value,
                "enviar_facturas_auto": enviar_auto.value,
                "asunto_factura": asunto_field.value,
                "cuerpo_factura": cuerpo_field.value
            }
            
            if self._guardar_config_email(nueva_config):
                self.page.close(dlg_email)
                self._mostrar_mensaje_exito("Configuración de email guardada correctamente")
                self.page.clean()
                self.page.add(self.build_ui())
                self.page.update()
            else:
                self._mostrar_mensaje_error("Error al guardar la configuración de email")

        dlg_email = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(Icons.EMAIL, color=Colors.INDIGO_600), ft.Text("Configuración de Email")], spacing=10),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([servidor_field, puerto_field]), email_field, password_field,
                    ft.Divider(height=10, color=Colors.INDIGO_100), usar_tls, enviar_auto,
                    ft.Divider(height=10, color=Colors.INDIGO_100),
                    ft.Text("Plantilla de Email:", size=14, weight=FontWeight.W_500, color=Colors.INDIGO_700),
                    asunto_field, cuerpo_field, info_help, ft.Container(height=10)
                ], spacing=12, scroll=ft.ScrollMode.ADAPTIVE), width=600, height=650
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg_email)),
                ft.ElevatedButton("Guardar", on_click=guardar_cambios, style=ft.ButtonStyle(color=Colors.WHITE, bgcolor=Colors.INDIGO_600)),
            ], actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg_email)

    def _editar_configuracion(self, seccion):
        dlg_generico = ft.AlertDialog(
            modal=True, title=ft.Text(f"Editar {seccion}"),
            content=ft.Text(f"Funcionalidad de {seccion} en desarrollo"),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dlg_generico))],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg_generico)

    def _mostrar_mensaje_exito(self, mensaje):
        snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.CHECK_CIRCLE, color=Colors.GREEN),
                ft.Text(mensaje , color="green")
            ]),
            bgcolor=Colors.GREEN_50,
        )
        self.page.open(snack_bar)

    def _mostrar_mensaje_error(self, mensaje):
        snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.ERROR, color=Colors.RED),
                ft.Text(mensaje , color="green")
            ]),
            bgcolor=Colors.RED_50,
        )
        self.page.open(snack_bar)