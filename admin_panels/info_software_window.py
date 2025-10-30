# admin_panels/info_software_window.py
import flet as ft
from pathlib import Path
import shutil
import requests
from packaging import version
import threading
import zipfile
import io


class InfoSoftwareWindow:
    def __init__(self, page: ft.Page, admin_panel):
        self.page = page
        self.admin_panel = admin_panel

        self.file_picker = ft.FilePicker(on_result=self._file_picker_result)
        self.save_picker = ft.FilePicker(on_result=self._save_zip_result)
        self.page.overlay.extend([self.file_picker, self.save_picker])

        # rutas esperadas
        self.archivos_requeridos = {
            "PRODUCTOS_DB": Path("./BASEDATOS/productos.db"),
            "PROVEDORES": Path("./BASEDATOS/provedores.db"),
            "VENTAS": Path("./BASEDATOS/ventas.db"),
            "JSON_ADMIN": Path("./Json files/admin.json"),
            "CONFIG_JSON_FACT": Path("./Json files/configuracion_facturas.json"),
            "DATOS_CLIENTE": Path("./Json files/datos_cliente_default.json"),
            "DATOS_EMPRESA": Path("./Json files/datos_empresariales.json"),
            "EMAIL": Path("./Json files/email.json"),
            "JSON_USER": Path("./Json files/users.json")
        }

        # crear directorios si no existen
        for ruta in self.archivos_requeridos.values():
            ruta.parent.mkdir(parents=True, exist_ok=True)

    # ------------------ UI -------------------
    def build_ui(self):
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.INDIGO_600, on_click=self._go_back),
                ft.Text("Información del Software", size=24, weight=ft.FontWeight.W_600, color=ft.Colors.INDIGO_900)
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(16),
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=8, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK), offset=ft.Offset(0, 2))
        )

        info = [
            ("Nombre del software", "TUCAN MAX"),
            ("Versión actual", "1.0.0"),
            ("Motor de base de datos", "SQLite 3"),
            ("Lenguaje base", "Python 3.12"),
            ("Framework GUI", "Flet"),
            ("Desarrollador", "JOSDVP76"),
            ("Licencia", "Privada / Interna"),
            ("CPU Mínimo", "Intel Celeron N4020 CPU 1.10 GHz")
        ]

        info_rows = [
            ft.Row([
                ft.Text(k, size=13, color=ft.Colors.GREY_700, expand=2),
                ft.Text(v, size=13, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_700, expand=1)
            ]) for k, v in info
        ]

        btn_check_update = ft.ElevatedButton(
            text="Verificar actualizaciones",
            icon=ft.Icons.SYSTEM_UPDATE_ALT,
            bgcolor=ft.Colors.INDIGO_600,
            color=ft.Colors.WHITE,
            on_click=self._verificar_actualizacion
        )

        btn_cargar_archivos = ft.ElevatedButton(
            text="Cargar archivos del sistema",
            icon=ft.Icons.UPLOAD_FILE,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            on_click=self._abrir_explorador
        )

        btn_exportar_datos = ft.ElevatedButton(
            text="Extraer datos del sistema",
            icon=ft.Icons.DOWNLOAD,
            bgcolor=ft.Colors.GREEN_700,
            color=ft.Colors.WHITE,
            on_click=self._extraer_datos
        )

        return ft.Container(
            content=ft.Column([
                header,
                ft.Container(
                    content=ft.Column([
                        ft.Text("Detalles del sistema", size=20, weight=ft.FontWeight.W_500, color=ft.Colors.INDIGO_700),
                        ft.Text("Información general del entorno de ejecución", size=14, color=ft.Colors.GREY_600),
                        ft.Divider(height=20, thickness=1, color=ft.Colors.INDIGO_100),
                        *info_rows,
                        ft.Divider(height=25, thickness=1, color=ft.Colors.INDIGO_100),
                        ft.Row([btn_check_update, btn_cargar_archivos, btn_exportar_datos], spacing=16)
                    ], spacing=12),
                    padding=24
                )
            ], scroll=ft.ScrollMode.AUTO)
        )

    # ------------------ Navegación -------------------
    def _go_back(self, e):
        self.admin_panel.setup_ui()

    # ------------------ Verificación de actualizaciones -------------------
    def _verificar_actualizacion(self, e):
        loading = ft.AlertDialog(
            modal=True,
            title=ft.Text("Buscando actualizaciones..."),
            content=ft.Row([
                ft.ProgressRing(),
                ft.Text("  Por favor, espere...")
            ]),
            actions=[]
        )
        self.page.open(loading)
        self.page.update()

        def check_update_thread():
            ultima_info = self._obtener_ultima_version()
            version_local = "1.0.0"

            if ultima_info:
                tag_name, name, created_at, body, html_url = ultima_info
                try:
                    if version.parse(tag_name) > version.parse(version_local):
                        contenido = ft.Column([
                            ft.Text(f"🔔 Nueva versión disponible: {tag_name}", weight=ft.FontWeight.W_600, color=ft.Colors.GREEN_700),
                            ft.Text(f"📦 Nombre: {name}", size=13),
                            ft.Text(f"📅 Creado el: {created_at}", size=13),
                            ft.Text("📝 Especificaciones:", size=13, weight=ft.FontWeight.W_500),
                            ft.Text(body or "Sin descripción disponible.", size=12, color=ft.Colors.GREY_700),
                            ft.Text(f"URL: {html_url}", size=12, color=ft.Colors.BLUE_700)
                        ], spacing=6)

                        btn_open_url = ft.TextButton(
                            "Abrir enlace de descarga",
                            icon=ft.Icons.OPEN_IN_NEW,
                            on_click=lambda _: self.page.launch_url(html_url)
                        )
                        acciones = [
                            btn_open_url,
                            ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dlg))
                        ]
                    else:
                        contenido = ft.Text(f"Tu software ({version_local}) ya está actualizado con la última versión ({tag_name}).")
                        acciones = [ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dlg))]
                except Exception as e:
                    contenido = ft.Text(f"No se pudo comparar la versión local ({version_local}) con la última versión ({tag_name}). Error: {e}")
                    acciones = [ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dlg))]
            else:
                contenido = ft.Text("No se pudo consultar la actualización en GitHub.")
                acciones = [ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dlg))]

            def show_result():
                self.page.close(loading)
                global dlg
                dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Verificación de Actualizaciones"),
                    content=contenido,
                    actions=acciones,
                    actions_alignment=ft.MainAxisAlignment.END
                )
                self.page.open(dlg)
                self.page.update()

            self.page.run_thread(show_result)

        threading.Thread(target=check_update_thread, daemon=True).start()

    def _obtener_ultima_version(self, repo="JDEVELOPER76/MAX-TUCAN"):
        """Consulta la última release en GitHub y devuelve detalles relevantes."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tag_name = data.get("tag_name", "")
                name = data.get("name", "")
                created_at = data.get("created_at", "")
                body = data.get("body", "")
                html_url = data.get("html_url", "")
                return tag_name, name, created_at, body, html_url
            return None
        except Exception as e:
            print("Error al obtener versión:", e)
            return None

    # ------------------ Extracción de datos -------------------
    def _extraer_datos(self, e):
        """Crea un ZIP con los archivos del sistema y permite guardarlo."""
        self.save_picker.save_file(
            dialog_title="Guardar datos del sistema como archivo ZIP",
            file_name="export_data.zip"
        )

    def _save_zip_result(self, e: ft.FilePickerResultEvent):
        if not e.path:
            return

        zip_path = Path(e.path)
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for key, ruta in self.archivos_requeridos.items():
                    if ruta.exists():
                        zf.write(ruta, arcname=ruta.relative_to(Path(".")))
            self._mostrar_exito(f"Datos exportados correctamente a:\n{zip_path}")
        except Exception as ex:
            self._mostrar_error(f"Error al crear el archivo ZIP: {ex}")

    # ------------------ Explorador de archivos -------------------
    def _abrir_explorador(self, e):
        self.file_picker.pick_files(
            dialog_title="Seleccionar archivos de configuración o base de datos",
            allow_multiple=True
        )

    # ------------------ Manejo de archivos -------------------
    def _file_picker_result(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        errores = []
        exitosos = 0

        for f in e.files:
            nombre_archivo = Path(f.name).name.lower()
            encontrado = False

            for key, destino in self.archivos_requeridos.items():
                if nombre_archivo == destino.name.lower():
                    try:
                        shutil.copy2(f.path, destino)
                        exitosos += 1
                        encontrado = True
                    except Exception as ex:
                        errores.append(f"{nombre_archivo} (Error: {ex})")
                    break

            if not encontrado:
                errores.append(nombre_archivo)

        if exitosos:
            self._mostrar_exito(f"{exitosos} archivos copiados correctamente y reemplazados si existían.")

        if errores:
            self._mostrar_error("Los siguientes archivos no son válidos o no se copiaron:\n" + "\n".join(errores))

    # ------------------ Mensajes -------------------
    def _mostrar_exito(self, msg):
        self.page.open(ft.SnackBar(
            content=ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN), ft.Text(msg,color=ft.Colors.BLACK)]),
            bgcolor=ft.Colors.GREEN_50
        ))

    def _mostrar_error(self, msg):
        self.page.open(ft.SnackBar(
            content=ft.Row([ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED), ft.Text(msg,color=ft.Colors.BLACK)]),
            bgcolor=ft.Colors.RED_50
        ))
