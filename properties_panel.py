# ==========================================
# properties_panel.py - VDOM Inspector de Propiedades
# ==========================================
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QDoubleSpinBox, 
                             QLabel, QFrame, QScrollArea, QPushButton, QHBoxLayout, QStackedWidget, QSlider)
from PyQt6.QtCore import pyqtSignal, Qt
from dialogs import PremiumDropdown, PremiumColorPicker
import qtawesome as qta # IMPORTAMOS ICONOS

# PALETA EXACTA DEL DISEÑO PREMIUM
BG_PANEL = "#1A1B1E"      
BG_INPUT = "#121214"      
BORDER = "#2A2B31"        
BORDER_HOVER = "#3F4148"  
COLOR_ACCENT = "#FE5934"  
TEXT_MAIN = "#FFFFFF"
TEXT_MUTED = "#85868A"
BG_PANEL = "#1A1B1E"      
BG_INPUT = "#121214"

PRESETS_LIENZO = {
    "Personalizado": None,
    "Post Instagram (1080x1080)": (1080, 1080),
    "Historia / Reel (1080x1920)": (1080, 1920),
    "A4 Digital (595x842)": (595, 842),
    "Full HD (1920x1080)": (1920, 1080),
    "HD (1280x720)": (1280, 720)
}

class StyledSpinBox(QDoubleSpinBox):
    def __init__(self, suffix="", max_val=99999.0):
        super().__init__()
        self.setRange(1, max_val)
        self.setSuffix(suffix)
        self.setDecimals(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        
        self.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: {BG_INPUT};
                color: {TEXT_MAIN};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Gilroy';
            }}
            QDoubleSpinBox:hover {{ border: 1px solid {BORDER_HOVER}; }}
            QDoubleSpinBox:focus {{ border: 1px solid {COLOR_ACCENT}; background-color: #1A1B1E; }}
        """)

class PropertiesPanel(QScrollArea):
    property_changed = pyqtSignal(str, dict)

    def __init__(self):
        super().__init__()
        self.setFixedWidth(320) 
        self.setWidgetResizable(True)
        self.setStyleSheet(f"QScrollArea {{ border: none; background-color: {BG_PANEL}; border-left: 1px solid {BORDER}; }}")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;") 
        self.layout_principal = QVBoxLayout(self.container)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)
        self.layout_principal.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.uid_actual = None 
        
        self._construir_ui()
        self.setWidget(self.container)

    def _crear_seccion(self, titulo):
        lbl = QLabel(titulo)
        lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-weight: bold; font-size: 16px; font-family: 'Gilroy';")
        return lbl

    def _crear_label(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; font-weight: bold; font-family: 'Gilroy';")
        return lbl

    def _crear_separador(self):
        linea = QFrame()
        linea.setFixedHeight(1)
        linea.setStyleSheet(f"background-color: {BORDER}; margin: 5px 20px;")
        return linea

    def _construir_ui(self):
        # =======================================================
        # 📄 GRUPO 0: PROPIEDADES DEL DOCUMENTO
        # =======================================================
        self.grupo_documento = QWidget()
        lay_doc = QVBoxLayout(self.grupo_documento)
        lay_doc.setContentsMargins(20, 25, 20, 20)
        lay_doc.setSpacing(0)
        
        lay_doc.addWidget(self._crear_seccion("Documento"))
        lay_doc.addSpacing(16)
        
        lay_doc.addWidget(self._crear_label("Preset de Lienzo"))
        lay_doc.addSpacing(4)
        self.cmb_presets = PremiumDropdown(list(PRESETS_LIENZO.keys()))
        lay_doc.addWidget(self.cmb_presets)
        lay_doc.addSpacing(16)
        
        grid_doc = QGridLayout()
        grid_doc.setVerticalSpacing(4)
        grid_doc.setHorizontalSpacing(12)
        grid_doc.addWidget(self._crear_label("Ancho"), 0, 0)
        grid_doc.addWidget(self._crear_label("Alto"), 0, 1)
        self.spn_doc_w = StyledSpinBox(" px")
        self.spn_doc_h = StyledSpinBox(" px")
        grid_doc.addWidget(self.spn_doc_w, 1, 0)
        grid_doc.addWidget(self.spn_doc_h, 1, 1)
        lay_doc.addLayout(grid_doc)
        lay_doc.addSpacing(16)
        
        # 🚀 NUEVOS BOTONES DE ORIENTACIÓN
        lay_doc.addWidget(self._crear_label("Orientación"))
        lay_doc.addSpacing(4)
        lay_orient = QHBoxLayout()
        lay_orient.setSpacing(8)
        
        self.btn_vert = QPushButton(" Vertical")
        self.btn_vert.setIcon(qta.icon('fa5s.file', color=TEXT_MAIN))
        self.btn_horiz = QPushButton(" Horizontal")
        self.btn_horiz.setIcon(qta.icon('fa5s.file', color=TEXT_MAIN, rotated=90))
        
        # Estilo base para los botones de orientación
        estilo_btn = f"""
            QPushButton {{ 
                background-color: {BG_INPUT}; color: {TEXT_MAIN}; border: 1px solid {BORDER}; 
                border-radius: 6px; padding: 10px; font-size: 12px; font-weight: bold; font-family: 'Gilroy'; 
            }}
            QPushButton:hover {{ border: 1px solid {BORDER_HOVER}; }}
        """
        self.btn_vert.setStyleSheet(estilo_btn)
        self.btn_horiz.setStyleSheet(estilo_btn)
        self.btn_vert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_horiz.setCursor(Qt.CursorShape.PointingHandCursor)
        
        lay_orient.addWidget(self.btn_vert)
        lay_orient.addWidget(self.btn_horiz)
        lay_doc.addLayout(lay_orient)
        lay_doc.addSpacing(16) # <--- Busca esto
        
        # 🚀 NUEVO: SELECTOR DE COLOR DEL LIENZO (ESTILO INPUT PREMIUM)
        # 🚀 SELECTOR DE COLOR (DISEÑO PREMIUM ESTILO FIGMA)
        lay_doc.addWidget(self._crear_label("Color de Fondo"))
        lay_doc.addSpacing(4)
        
        self.btn_color_canvas = QPushButton()
        self.btn_color_canvas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_color_canvas.setFixedHeight(40)
        self.btn_color_canvas.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_INPUT}; border: 1px solid {BORDER};
                border-radius: 6px; text-align: left;
            }}
            QPushButton:hover {{ border: 1px solid {BORDER_HOVER}; }}
        """)
        
        # Layout interno del botón para que tenga el cuadrito y el texto pegados
        btn_lay = QHBoxLayout(self.btn_color_canvas)
        btn_lay.setContentsMargins(10, 0, 10, 0)
        btn_lay.setSpacing(10)
        
        self.preview_dot = QFrame()
        self.preview_dot.setFixedSize(18, 18)
        self.preview_dot.setStyleSheet("border-radius: 4px; border: 1px solid #3F4148;")
        
        self.lbl_color_val = QLabel("#FFFFFF")
        self.lbl_color_val.setStyleSheet(f"color: {TEXT_MAIN}; font-family: 'Gilroy'; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        
        btn_lay.addWidget(self.preview_dot)
        btn_lay.addWidget(self.lbl_color_val)
        btn_lay.addStretch()
        
        self.btn_color_canvas.clicked.connect(self._abrir_selector_color_canvas)
        lay_doc.addWidget(self.btn_color_canvas)

        # =======================================================
        # 📐 GRUPO 1: TRANSFORMACIÓN
        # =======================================================
        self.grupo_transform = QWidget()
        lay_trans = QVBoxLayout(self.grupo_transform)
        lay_trans.setContentsMargins(20, 25, 20, 20)
        lay_trans.setSpacing(0)
        
        lay_trans.addWidget(self._crear_seccion("Transformación"))
        lay_trans.addSpacing(16)
        
        grid_trans = QGridLayout()
        grid_trans.setVerticalSpacing(4)
        grid_trans.setHorizontalSpacing(12)
        grid_trans.addWidget(self._crear_label("Ancho"), 0, 0)
        grid_trans.addWidget(self._crear_label("Alto"), 0, 1)
        self.spn_w = StyledSpinBox(" px")
        self.spn_h = StyledSpinBox(" px")
        grid_trans.addWidget(self.spn_w, 1, 0)
        grid_trans.addWidget(self.spn_h, 1, 1)
        
        grid_trans.addWidget(self._crear_label("Rotación"), 2, 0)
        self.spn_rot = StyledSpinBox(" °", 360.0)
        grid_trans.addWidget(self.spn_rot, 3, 0)
        lay_trans.addLayout(grid_trans)
        
        # =======================================================
        # 📝 GRUPO 2: TEXTO
        # =======================================================
        self.grupo_texto = QWidget()
        lay_txt = QVBoxLayout(self.grupo_texto)
        lay_txt.setContentsMargins(20, 0, 20, 20)
        lay_txt.setSpacing(0)
        
        lay_txt.addWidget(self._crear_separador())
        lay_txt.addSpacing(20)
        lay_txt.addWidget(self._crear_seccion("Tipografía"))
        lay_txt.addSpacing(16)
        lay_txt.addWidget(self._crear_label("Fuente"))
        lay_txt.addSpacing(4)
        self.cmb_fuente = PremiumDropdown(["Arial", "Helvetica", "Times New Roman", "Courier", "Gilroy"])
        lay_txt.addWidget(self.cmb_fuente)
        
        # =======================================================
        # 🖼️ GRUPO 3: IMAGEN/EFECTOS
        # =======================================================
        self.grupo_imagen = QWidget()
        lay_img = QVBoxLayout(self.grupo_imagen)
        lay_img.setContentsMargins(20, 0, 20, 20)
        lay_img.setSpacing(0)
        
        lay_img.addWidget(self._crear_separador())
        lay_img.addSpacing(20)
        lay_img.addWidget(self._crear_seccion("Efectos Visuales"))
        lay_img.addSpacing(16)
        lay_img.addWidget(self._crear_label("Opacidad"))
        lay_img.addSpacing(4)
        self.spn_opacidad = StyledSpinBox(" %", 100.0)
        lay_img.addWidget(self.spn_opacidad)

        self.layout_principal.addWidget(self.grupo_documento)
        self.layout_principal.addWidget(self.grupo_transform)
        self.layout_principal.addWidget(self.grupo_texto)
        self.layout_principal.addWidget(self.grupo_imagen)
        
        # --- CONEXIONES ---
        self.spn_w.valueChanged.connect(lambda v: self._emitir_cambio('w', v))
        self.spn_h.valueChanged.connect(lambda v: self._emitir_cambio('h', v))
        self.spn_rot.valueChanged.connect(lambda v: self._emitir_cambio('rotacion', v))
        self.spn_opacidad.valueChanged.connect(lambda v: self._emitir_cambio('opacidad', v / 100.0))
        
        self.cmb_presets.currentIndexChanged.connect(self._aplicar_preset_documento)
        self.cmb_fuente.currentIndexChanged.connect(self._aplicar_fuente)
        
        self.spn_doc_w.valueChanged.connect(self._medida_doc_cambiada)
        self.spn_doc_h.valueChanged.connect(self._medida_doc_cambiada)
        
        self.btn_vert.clicked.connect(lambda: self._set_orientacion("V"))
        self.btn_horiz.clicked.connect(lambda: self._set_orientacion("H"))

    def _emitir_cambio(self, clave, valor):
        if self.uid_actual:
            self.property_changed.emit(self.uid_actual, {clave: valor})
        elif clave in ['doc_w', 'doc_h']:
            self.property_changed.emit("DOCUMENTO", {clave: valor})

    def _set_orientacion(self, modo):
        w, h = self.spn_doc_w.value(), self.spn_doc_h.value()
        if modo == "V" and w > h:
            self.spn_doc_w.setValue(h); self.spn_doc_h.setValue(w)
        elif modo == "H" and h > w:
            self.spn_doc_w.setValue(h); self.spn_doc_h.setValue(w)
        self._actualizar_estilo_orientacion()

    def _actualizar_estilo_orientacion(self):
        w, h = self.spn_doc_w.value(), self.spn_doc_h.value()
        is_vert = h >= w
        
        estilo_activo = f"background-color: {BG_INPUT}; color: {COLOR_ACCENT}; border: 1.5px solid {COLOR_ACCENT}; border-radius: 6px; padding: 10px; font-size: 12px; font-weight: bold; font-family: 'Gilroy';"
        estilo_normal = f"background-color: {BG_INPUT}; color: {TEXT_MAIN}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px; font-size: 12px; font-weight: bold; font-family: 'Gilroy';"
        
        self.btn_vert.setStyleSheet(estilo_activo if is_vert else estilo_normal)
        self.btn_horiz.setStyleSheet(estilo_normal if is_vert else estilo_activo)
        
        # Actualizamos iconos
        self.btn_vert.setIcon(qta.icon('fa5s.file', color=COLOR_ACCENT if is_vert else TEXT_MAIN))
        self.btn_horiz.setIcon(qta.icon('fa5s.file', color=TEXT_MAIN if is_vert else COLOR_ACCENT, rotated=90))

    def _medida_doc_cambiada(self):
        self._actualizar_estilo_orientacion()
        idx_perso = self.cmb_presets.options.index("Personalizado")
        self.cmb_presets.blockSignals(True)
        self.cmb_presets.setCurrentIndex(idx_perso)
        self.cmb_presets.blockSignals(False)
        self._emitir_cambio('doc_w', self.spn_doc_w.value())
        self._emitir_cambio('doc_h', self.spn_doc_h.value())

    def _aplicar_fuente(self, idx):
        self._emitir_cambio('fuente', self.cmb_fuente.options[idx])

    def _aplicar_preset_documento(self, idx):
        preset = self.cmb_presets.options[idx]
        if preset == "Personalizado": return
        w, h = PRESETS_LIENZO[preset]
        self.spn_doc_w.blockSignals(True); self.spn_doc_h.blockSignals(True)
        self.spn_doc_w.setValue(w); self.spn_doc_h.setValue(h)
        self.spn_doc_w.blockSignals(False); self.spn_doc_h.blockSignals(False)
        self._actualizar_estilo_orientacion()
        self._emitir_cambio('doc_w', w); self._emitir_cambio('doc_h', h)

    def actualizar_desde_motor(self, uid, datos_elemento, w_pdf=1080, h_pdf=1080):
        self.uid_actual = uid
        if not uid or not datos_elemento:
            self.grupo_documento.show()
            self.grupo_transform.hide(); self.grupo_texto.hide(); self.grupo_imagen.hide()
            self.spn_doc_w.blockSignals(True); self.spn_doc_h.blockSignals(True)
            self.spn_doc_w.setValue(w_pdf); self.spn_doc_h.setValue(h_pdf)
            self.spn_doc_w.blockSignals(False); self.spn_doc_h.blockSignals(False)
            self._actualizar_estilo_orientacion()
            return

        self.grupo_documento.hide()
        self.spn_w.blockSignals(True); self.spn_h.blockSignals(True)
        self.spn_rot.blockSignals(True); self.spn_opacidad.blockSignals(True)

        tipo = datos_elemento.get("tipo", "")
        self.grupo_transform.show()
        self.spn_w.setValue(float(datos_elemento.get('w', 100)))
        self.spn_h.setValue(float(datos_elemento.get('h', 100)))
        self.spn_rot.setValue(float(datos_elemento.get('rotacion', 0)))

        if tipo == "Texto":
            self.grupo_texto.show(); self.grupo_imagen.hide()
            fuente = datos_elemento.get('fuente', 'Arial')
            if fuente in self.cmb_fuente.options:
                self.cmb_fuente.blockSignals(True)
                self.cmb_fuente.setCurrentIndex(self.cmb_fuente.options.index(fuente))
                self.cmb_fuente.blockSignals(False)
        elif tipo in ["Foto", "SVG", "Forma"]:
            self.grupo_texto.hide(); self.grupo_imagen.show() 
            self.spn_opacidad.setValue(float(datos_elemento.get('opacidad', 1.0)) * 100)
        else:
            self.grupo_texto.hide(); self.grupo_imagen.hide()

        self.spn_w.blockSignals(False); self.spn_h.blockSignals(False)
        self.spn_rot.blockSignals(False); self.spn_opacidad.blockSignals(False)

    def _estilizar_btn_color(self, hex_rgba):
        """Actualiza el input de color basándose estrictamente en el modo del doc"""
        from PyQt6.QtGui import QColor
        if not hex_rgba: hex_rgba = "#FFFFFFFF"
        color = QColor(hex_rgba)
        
        # Punto de color sólido
        self.preview_dot.setStyleSheet(f"background-color: {color.name(QColor.NameFormat.HexRgb)}; border-radius: 4px; border: 1px solid #3F4148;")
        
        # 🚀 LÓGICA DE TEXTO INTELIGENTE (CMYK o RGB)
        # Obtenemos el modo del motor o de una variable local
        modo = getattr(self, 'modo_color_doc', "RGB") 
        
        if modo == "CMYK":
            # Conversión para el label
            r, g, b = color.red()/255, color.green()/255, color.blue()/255
            k = 1 - max(r, g, b)
            if k == 1: c = m = y = 0
            else:
                c, m, y = (1-r-k)/(1-k), (1-g-k)/(1-k), (1-b-k)/(1-k)
            texto = f"{int(c*100)}, {int(m*100)}, {int(y*100)}, {int(k*100)}"
        else:
            # En RGB mostramos el HEX para que sea corto y elegante
            texto = hex_rgba.upper()[:7]
            
        self.lbl_color_val.setText(texto)
        self.btn_color_canvas.setProperty("color_actual", hex_rgba)

    def _abrir_selector_color_canvas(self):
        try:
            self.btn_color_canvas.setEnabled(False)
            color_actual = self.btn_color_canvas.property("color_actual")
            
            # 🚀 PASAMOS EL MODO DEL DOCUMENTO AL PICKER
            modo_doc = getattr(self, 'modo_color_doc', "RGB")
            
            # 🚀 IMPORTANTE: Guardamos el diálogo en `self` para que no sea destruido por el Garbage Collector
            self._color_dialog = PremiumColorPicker(color_inicial=color_actual, mostrar_opacidad=False, modo_forzado=modo_doc, parent=self)

            self._color_dialog.adjustSize() 
            pos = self.btn_color_canvas.mapToGlobal(self.btn_color_canvas.rect().topLeft())
            self._color_dialog.move(pos.x() - 340, pos.y() - 100)
            
            # ========================================================
            # 🚀 LA CURA ABSOLUTA: PATRÓN MODAL ASÍNCRONO (.open)
            # ========================================================
            # 1. Conectamos la señal de "Aceptar" (Guardar Color) a nuestra función
            self._color_dialog.accepted.connect(self._aplicar_color_desde_dialogo)
            
            # 2. Conectamos señales de limpieza por si se cierra o cancela
            self._color_dialog.rejected.connect(self._limpiar_dialogo_color)
            self._color_dialog.finished.connect(self._limpiar_dialogo_color)
            
            # 3. DERRIBAMOS EL MURO: .open() muestra el diálogo SIN detener el programa
            self._color_dialog.open()
            
        except Exception as e:
            print(f"❌ Error en selector: {e}")
            self.btn_color_canvas.setEnabled(True)

    # 🚀 NUEVAS FUNCIONES PARA MANEJAR LA RESPUESTA ASÍNCRONA
    def _aplicar_color_desde_dialogo(self):
        """Se ejecuta mágicamente cuando el usuario presiona 'Guardar Color' en el diálogo"""
        if hasattr(self, '_color_dialog') and self._color_dialog:
            nuevo_hex = self._color_dialog.get_color()
            self._estilizar_btn_color(nuevo_hex)
            self.property_changed.emit("DOCUMENTO", {'bg_color': nuevo_hex})

    def _limpiar_dialogo_color(self):
        """Libera la memoria y rehabilita el botón de forma segura"""
        self.btn_color_canvas.setEnabled(True)
        
        # 🚀 EL DOBLE CANDADO: Verificamos que exista Y que no sea None
        if hasattr(self, '_color_dialog') and self._color_dialog is not None:
            self._color_dialog.deleteLater()
            self._color_dialog = None