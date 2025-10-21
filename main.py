# main.py  –  versión 1.2  (simplificada + nombre real del release)
import flet as ft
import requests
import os
import tempfile
import subprocess
import sys
import shutil
import time
from pathlib import Path

# ------------------------------------------------------------------
#  LÓGICA DE ACTUALIZACIONES
# ------------------------------------------------------------------
class AppUpdater:
    def __init__(self):
        self.current_version = "1.2"                       # <-- tu versión actual
        self.github_repo    = "JDEVELOPER76/MAX-TUCAN"     # <-- tu repo
        self.api_url        = f"https://api.github.com/repos/{self.github_repo}/releases/latest"

    # ----------  obtiene el release más reciente  ----------
    def get_latest_release(self):
        try:
            r = requests.get(self.api_url, timeout=10)
            return r.json() if r.status_code == 200 else None
        except:
            return None

    # ----------  compara versiones  ----------
    def check_update(self):
        rel = self.get_latest_release()
        if not rel:
            return {"available": False, "error": "No se pudo conectar"}
        latest = rel["tag_name"]
        if latest != self.current_version:
            return {
                "available": True,
                "version": latest,
                "notes": rel.get("body", "Nueva versión disponible"),
                "assets": rel.get("assets", []),
                "url": rel["html_url"]
            }
        return {"available": False}

    # ----------  descarga con el NOMBRE REAL del asset  ----------
    def download_exe(self, asset_url, asset_name, progress_callback=None):
        try:
            r = requests.get(asset_url, stream=True)
            total = int(r.headers.get('content-length', 0))

            temp_file = os.path.join(tempfile.gettempdir(), asset_name)  # <-- nombre real

            down = 0
            with open(temp_file, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        down += len(chunk)
                        if progress_callback and total:
                            progress_callback(down / total, down, total)
            return temp_file
        except Exception as e:
            print("Error descarga:", e)
            return None


# ------------------------------------------------------------------
#  MANEJO DE COPIAS / REEMPLAZO
# ------------------------------------------------------------------
class UpdateManager:
    def __init__(self):
        self.old_folder = "version-olds"

    def current_dir(self):
        return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)

    def backup_and_replace(self, new_exe):
        """Crea backup y reemplaza el ejecutable actual."""
        current_exe = sys.executable
        dir_old     = os.path.join(self.current_dir(), self.old_folder)
        os.makedirs(dir_old, exist_ok=True)

        ts = int(time.time())
        backup = os.path.join(dir_old, f"{Path(current_exe).stem}.{ts}.old.exe")
        shutil.copy2(current_exe, backup)

        # ----  reemplazo  ----
        shutil.copy2(new_exe, current_exe)
        return True

    def create_updater_bat(self, new_exe_path):
        """Script batch que se autoconsume tras reemplazar."""
        current = sys.executable
        bat_path = os.path.join(tempfile.gettempdir(), f"upd_{int(time.time())}.bat")
        with open(bat_path, 'w', encoding='utf-8') as b:
            b.write(f"""
@echo off
echo 🔄  Actualizando…
timeout /t 2 >nul
copy /Y "{new_exe_path}" "{current}" >nul
start "" "{current}"
del "{new_exe_path}" 2>nul
del "%~f0" 2>nul
""")
        return bat_path


# ------------------------------------------------------------------
#  INTERFAZ FLET
# ------------------------------------------------------------------
def main(page: ft.Page):
    updater   = AppUpdater()
    mgr       = UpdateManager()

    page.title                 = "AutoUpdater"
    page.vertical_alignment    = "center"
    page.horizontal_alignment  = "center"
    page.padding               = 30

    lbl_status   = ft.Text("Versión actual: " + updater.current_version)
    pb           = ft.ProgressBar(width=400, visible=False)
    lbl_pct      = ft.Text()
    lbl_details  = ft.Text(size=12, color=ft.Colors.GREY_500)

    # ----------  progreso  ----------
    def set_progress(ratio, done, total):
        pb.value = ratio
        lbl_pct.value = f"{ratio*100:.1f} %"
        lbl_details.value = f"{done//1024} KB / {total//1024} KB"
        page.update()

    # ----------  descarga + instala  ----------
    def download_and_install(info):
        asset = next((a for a in info["assets"] if a["name"].lower().endswith(".exe")), None)
        if not asset:
            lbl_status.value = "❌ No hay .exe en el release"
            page.update()
            return

        lbl_status.value = "📥 Descargando…"
        pb.visible = True
        page.update()

        temp_file = updater.download_exe(asset["browser_download_url"],
                                         asset["name"],        # <-- nombre real
                                         progress_callback=set_progress)
        if not temp_file:
            lbl_status.value = "❌ Error al descargar"
            pb.visible = False
            page.update()
            return

        # backup y reemplazo
        mgr.backup_and_replace(temp_file)
        lbl_status.value = "✅ Actualización lista – reiniciando…"
        page.update()
        time.sleep(2)

        # lanzar el .bat que se autoconsume
        bat = mgr.create_updater_bat(temp_file)
        subprocess.Popen([bat], shell=True)
        sys.exit(0)

    # ----------  botón comprobar  ----------
    def check(e):
        lbl_status.value = "🔍 Buscando…"
        page.update()
        res = updater.check_update()
        if res.get("available"):
            download_and_install(res)
        elif res.get("error"):
            lbl_status.value = "❌ " + res["error"]
        else:
            lbl_status.value = "✅ Ya estás en la última versión"
        pb.visible = False
        page.update()

    # ----------  UI  ----------
    page.add(
        ft.Column([
            ft.Text("MI APLICACIÓN", size=24, weight="bold"),
            lbl_status,
            ft.ElevatedButton("🔄 Buscar actualización", on_click=check,
                              style=ft.ButtonStyle(padding=20)),
            ft.Container(height=15),
            ft.Column([pb, lbl_pct, lbl_details])
        ], alignment="center", horizontal_alignment="center")
    )


if __name__ == "__main__":
    ft.app(target=main)
