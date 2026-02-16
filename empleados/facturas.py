import os
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.colors import navy, white, black

class GeneradorFacturas:
    MARGEN_LEFT    = 50
    MARGEN_TOP     = 50
    ANCHO_UTIL     = A4[0] - 2 * MARGEN_LEFT
    COLOR_PRIMARIO = navy

    def __init__(self):
        self.json_dir      = Path("./Json files")
        self.empresa_file  = self.json_dir / "datos_empresariales.json"
        self.facturas_file = self.json_dir / "configuracion_facturas.json"
        self.cargar_configuraciones()

    # ---------- CONFIG ----------
    def cargar_configuraciones(self):
        try:
            with open(self.empresa_file,  'r', encoding='utf-8') as f:
                self.datos_empresa   = json.load(f)
            with open(self.facturas_file, 'r', encoding='utf-8') as f:
                self.config_facturas = json.load(f)
        except Exception as e:
            print("Error cargando configuraciones:", e)

    # ---------- HEADER ----------
    def _draw_header(self, c, y_top):
        margen = self.MARGEN_LEFT
        ancho  = self.ANCHO_UTIL
        alto_logo = 70

        # logo
        if self.config_facturas.get("incluir_logo") and self.datos_empresa.get("logo_empresa"):
            try:
                logo_path = self.datos_empresa["logo_empresa"]
                if os.path.exists(logo_path):
                    c.drawImage(ImageReader(logo_path),
                              margen, y_top - alto_logo,
                              width=alto_logo, height=alto_logo,
                              preserveAspectRatio=True)
                else:
                    print(f"DEBUG: Logo no encontrado en {logo_path}")
            except Exception as e:
                print("Error logo:", e)

        # empresa
        c.setFillColor(self.COLOR_PRIMARIO)
        c.setFont("Helvetica-Bold", 18)
        text_x = margen + alto_logo + 15
        c.drawString(text_x, y_top - 25, self.datos_empresa.get("nombre_empresa", ""))

        c.setFont("Helvetica", 10)
        c.setFillColor(black)
        direccion = self.datos_empresa.get("direccion", "")
        correo    = self.datos_empresa.get("correo_electronico", "")
        telefono  = self.datos_empresa.get("numero_telefono", "")
        c.drawString(text_x, y_top - 40, direccion)
        c.drawString(text_x, y_top - 55, f"{correo}  |  {telefono}")

        # línea decorativa
        y_line = y_top - alto_logo - 10
        c.setStrokeColor(self.COLOR_PRIMARIO)
        c.setLineWidth(2)
        c.line(margen, y_line, margen + ancho, y_line)
        return y_line - 20

    # ---------- TABLE ----------
# En facturas.py - MEJORA el método _tabla_items:

    def _tabla_items(self, c, y_start, items):
        margen  = self.MARGEN_LEFT
        ancho   = self.ANCHO_UTIL
        filas   = [["Descripción", "Cant.", "P. Unit.", "Total"]]
        subtotal = 0
        total_iva = 0

        for it in items:
            desc = it.get("descripcion", "")
            cant = it.get("cantidad", 0)
            pu   = it.get("precio", 0)
            tasa = it.get("iva_porcentaje", 0)   # Porcentaje de IVA
            importe_linea = round(cant * pu, 2)
            iva_linea = round(importe_linea * (tasa / 100), 2) if tasa > 0 else 0
            subtotal  += importe_linea
            total_iva += iva_linea

            # Acortar descripción si es muy larga
            if len(desc) > 45:
                desc = desc[:42] + "..."
            
            filas.append([
                desc, 
                f"{cant}", 
                f"${pu:,.2f}", 
                f"${importe_linea:,.2f}"
            ])

        col_widths = [ancho*0.50, ancho*0.15, ancho*0.15, ancho*0.20]
        tabla = Table(filas, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), self.COLOR_PRIMARIO),
            ('TEXTCOLOR',  (0,0), (-1,0), white),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,0), 10),
            ('FONTNAME',   (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',   (0,1), (-1,-1), 9),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ]))

        w, h = tabla.wrapOn(c, ancho, A4[1])
        if y_start - h < 120:
            c.showPage()
            c.setFont("Helvetica", 9)
            y_start = A4[1] - self.MARGEN_TOP

        tabla.drawOn(c, margen, y_start - h)
        return y_start - h - 15, subtotal, total_iva

    # ---------- TOTALES ----------
    def _draw_totales(self, c, y, subtotal, total_iva):
        x_col = self.MARGEN_LEFT + self.ANCHO_UTIL - 160
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_col, y, f"Subtotal:  ${subtotal:,.2f}")
        y -= 15
        if total_iva:
            c.drawString(x_col, y, f"IVA:            ${total_iva:,.2f}")
            y -= 15
        gran_total = subtotal + total_iva
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(self.COLOR_PRIMARIO)
        c.drawString(x_col, y, f"TOTAL:  ${gran_total:,.2f}")
        c.setFillColor(black)
        return y - 25

    # ---------- PIE ----------
    def _draw_footer(self, c, y):
        if self.config_facturas.get("leyenda_pie_pagina"):
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(self.MARGEN_LEFT, y, self.config_facturas["leyenda_pie_pagina"])

    # ---------- GENERADOR ----------
# En facturas.py - REEMPLAZA el método generar_factura_pdf actual:

    def generar_factura_pdf(self, cliente, items, subtotal, iva_total, total, vendedor):
        """Genera la factura PDF con los parámetros esperados desde menu_ventas"""
        try:
            # Crear directorio de facturas si no existe
            facturas_dir = Path("./Facturas")
            facturas_dir.mkdir(exist_ok=True)
            
            # Generar nombre de archivo único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"factura_{timestamp}.pdf"
            output_path = facturas_dir / filename
            
            c = canvas.Canvas(str(output_path), pagesize=A4)
            ancho, alto = A4
            y = alto - self.MARGEN_TOP

            # 1. Header
            y = self._draw_header(c, y)

            # 2. Información de la factura y cliente
            c.setFont("Helvetica-Bold", 14)
            c.setFillColor(self.COLOR_PRIMARIO)
            serie = self.config_facturas.get("serie_facturas", "A")
            folio = self.config_facturas.get("folio_actual", "00000000000001")
            c.drawString(self.MARGEN_LEFT, y, f"FACTURA {serie}-{folio}")
            
            c.setFillColor(black)
            c.setFont("Helvetica", 10)
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
            c.drawString(self.MARGEN_LEFT, y - 15, f"Fecha: {fecha}")
            c.drawString(self.MARGEN_LEFT, y - 30, f"Vendedor: {vendedor}")
            
            # Información del cliente
            c.drawString(self.ANCHO_UTIL / 2, y - 15, f"Cliente: {cliente.get('nombre', '')}")
            c.drawString(self.ANCHO_UTIL / 2, y - 30, f"Documento: {cliente.get('rfc', '')}")
            c.drawString(self.ANCHO_UTIL / 2, y - 45, f"Tipo Venta: {cliente.get('tipo_venta', 'Normal')}")
            
            if cliente.get('direccion'):
                c.drawString(self.ANCHO_UTIL / 2, y - 60, f"Dirección: {cliente['direccion']}")
                y -= 75
            else:
                y -= 65

            # 3. Tabla de items
            y, subtotal_calculado, iva_calculado = self._tabla_items(c, y, items)

            # Recalcular totales para evitar inconsistencias
            subtotal = round(subtotal_calculado, 2)
            iva_total = round(iva_calculado, 2)
            total = round(subtotal + iva_total, 2)

            # 4. Totales
            y = self._draw_totales(c, y, subtotal, iva_total)

            # 5. Pie de página
            self._draw_footer(c, 60)

            c.save()
            self._actualizar_folio()
            
            return str(output_path)
            
        except Exception as e:
            print(f"ERROR: Generando PDF: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ---------- FOLIO ----------
    def _actualizar_folio(self):
        try:
            folio_act = int(self.config_facturas.get("folio_actual", "00000000000001"))
            self.config_facturas["folio_actual"] = str(folio_act + 1).zfill(14)
            with open(self.facturas_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_facturas, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("Error actualizando folio:", e)