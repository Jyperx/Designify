# ==========================================
# dialogs.py - Ventanas emergentes del sistema
# ==========================================
from PyQt6.QtWidgets import (QDialog, QFrame, QHBoxLayout, QVBoxLayout,
                             QLabel, QPushButton, QLineEdit, QScrollArea,
                             QGridLayout, QGraphicsDropShadowEffect, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont
import qtawesome as qta 

COLOR_ACCENT = "#FE5934" 
TEXT_MAIN = "#FFFFFF"
TEXT_MUTED = "#85868A"

def apply_shadow(widget, radius=20, offset_y=5):
    """Función de sombra local"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setXOffset(0)
    shadow.setYOffset(offset_y)
    shadow.setColor(QColor(0, 0, 0, 150))
    widget.setGraphicsEffect(shadow)

# =========================================================
# 🚀 NUEVOS COMPONENTES: DROPDOWN PREMIUM (Reemplazo de QComboBox)
# =========================================================
class PremiumDropdownPopup(QDialog):
    """El menú flotante que aparece debajo del Dropdown"""
    option_selected = pyqtSignal(int, str)
    
    def __init__(self, options, parent_widget):
        super().__init__(parent_widget.window())
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(0, 0, 15, 15) # Margen para la sombra
        
        container = QFrame(self)
        container.setStyleSheet("background-color: #18191D; border: 1px solid #2A2B31; border-radius: 8px;")
        apply_shadow(container, radius=15, offset_y=5)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        
        self.list_widget = QListWidget()
        
        # 🚀 LA CURA DE LA FUENTE: Forzamos la fuente desde el objeto para que Qt no se atreva a ignorarla
        from PyQt6.QtGui import QFont
        fuente_gilroy = QFont("Gilroy", 10)
        fuente_gilroy.setBold(True)
        self.list_widget.setFont(fuente_gilroy)
        
        # 🚀 CSS REFINADO: Gris elegante para la selección y Scrollbar flotante invisible
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ 
                background: transparent; 
                border: none; 
                outline: none; 
                font-family: 'Gilroy';
            }}
            QListWidget::item {{ 
                color: {TEXT_MUTED}; 
                padding: 10px 12px; 
                border-radius: 4px; 
            }}
            QListWidget::item:hover {{ 
                background-color: #2A2B31; 
                color: {TEXT_MAIN}; 
            }}
            QListWidget::item:selected {{ 
                background-color: #3F4148; /* 🚀 Gris brillante elegante en lugar de naranja */
                color: {TEXT_MAIN}; 
            }}
            
            /* 🚀 SCROLLBAR PREMIUM: Sin contenedor, solo la barra flotando */
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 2px 2px 2px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #4A4D57;
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #85868A;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                border: none;
                background: none;
            }}
        """)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        for opt in options:
            self.list_widget.addItem(opt)
            
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)
        base_layout.addWidget(container)
        
        # Altura dinámica inteligente (con scroll si hay muchas opciones)
        h_items = len(options) * 36 + 8
        h_total = min(h_items, 200) + 15 
        self.setFixedSize(parent_widget.width() + 15, h_total)
        
    def _on_item_clicked(self, item):
        idx = self.list_widget.row(item)
        self.option_selected.emit(idx, item.text())
        self.accept()

class PremiumDropdown(QFrame):
    """El botón falso que actúa como Dropdown"""
    currentIndexChanged = pyqtSignal(int)
    
    def __init__(self, options):
        super().__init__()
        self.options = options
        self.current_index = 0
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame { background-color: #121214; border: 1px solid #2A2B31; border-radius: 6px; }
            QFrame:hover { border: 1px solid #3F4148; }
        """)
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_text = QLabel(options[0] if options else "")
        self.lbl_text.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold; background: transparent; border: none; font-family: 'Gilroy';")
        layout.addWidget(self.lbl_text)
        
        layout.addStretch()
        
        self.lbl_icon = QLabel()
        self.lbl_icon.setPixmap(qta.icon('fa5s.chevron-down', color="#85868A").pixmap(12, 12))
        self.lbl_icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.lbl_icon)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            popup = PremiumDropdownPopup(self.options, self)
            pos = self.mapToGlobal(self.rect().bottomLeft())
            # Lo pegamos exactamente 4 píxeles debajo del input
            popup.move(pos.x(), pos.y() + 4)
            popup.list_widget.setCurrentRow(self.current_index) 
            popup.option_selected.connect(self._on_selected)
            popup.exec()
            
    def _on_selected(self, idx, text):
        self.current_index = idx
        self.lbl_text.setText(text)
        self.currentIndexChanged.emit(idx)
        
    def currentIndex(self):
        return self.current_index
        
    def setCurrentIndex(self, idx):
        if 0 <= idx < len(self.options):
            self.current_index = idx
            self.lbl_text.setText(self.options[idx])

# =========================================================

class NewDocumentDialog(QDialog):
    """Diálogo profesional estilo Illustrator/Figma para crear un nuevo lienzo"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setModal(True)
        self.setFixedSize(920, 580)
        
        self.resultado = None

        main_frame = QFrame(self)
        main_frame.setGeometry(10, 10, 900, 560)
        main_frame.setObjectName("main_bg")
        main_frame.setStyleSheet("""
            #main_bg { background-color: #121214; border: 1px solid #2A2B31; border-radius: 12px; }
            QLabel { border: none; background: transparent; }
        """)
        apply_shadow(main_frame, radius=25, offset_y=10)

        layout_principal = QHBoxLayout(main_frame)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # =========================================================
        # COLUMNA IZQUIERDA: GALERÍA DE PRESETS
        # =========================================================
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        contenedor_presets = QFrame()
        contenedor_presets.setStyleSheet("background: transparent;")
        layout_presets = QVBoxLayout(contenedor_presets)
        layout_presets.setContentsMargins(30, 30, 30, 30)
        layout_presets.setSpacing(25)

        self.categorias = [
            ("fa5s.hashtag", "Redes Sociales", [("Post Instagram", 1080, 1080, "RGB"), ("Historia / Reel", 1080, 1920, "RGB"), ("Portada Facebook", 1640, 624, "RGB")]),
            ("fa5s.desktop", "Pantalla & Web", [("Full HD (1080p)", 1920, 1080, "RGB"), ("HD (720p)", 1280, 720, "RGB"), ("MacBook Pro", 1440, 900, "RGB")]),
            ("fa5s.print", "Impresión (Digital)", [("Carta (Letter)", 612, 792, "CMYK"), ("A4 Estándar", 595, 842, "CMYK"), ("Tabloide", 792, 1224, "CMYK")])
        ]

        for icono_nombre, cat_nombre, items in self.categorias:
            cat_header = QHBoxLayout()
            cat_header.setSpacing(10)
            
            icon_lbl = QLabel()
            icon_lbl.setPixmap(qta.icon(icono_nombre, color=TEXT_MUTED).pixmap(16, 16))
            cat_header.addWidget(icon_lbl)
            
            lbl_cat = QLabel(cat_nombre)
            lbl_cat.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 16px; font-weight: bold; font-family: 'Gilroy'; margin-bottom: 2px;")
            cat_header.addWidget(lbl_cat)
            cat_header.addStretch()
            
            layout_presets.addLayout(cat_header)
            
            grid = QGridLayout()
            grid.setSpacing(15)
            row, col = 0, 0
            for (nombre, w, h, modo) in items:
                btn = QPushButton()
                btn.setFixedSize(140, 100)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{ background-color: #1A1B1E; border: 1px solid #2A2B31; border-radius: 8px; color: #D1D1D5; text-align: center; padding: 15px; }}
                    QPushButton:hover {{ border: 1px solid {COLOR_ACCENT}; background-color: #202126; color: #FFFFFF; }}
                """)
                
                texto_tarjeta = f"<b>{nombre}</b><br><br><span style='font-size:11px; color:#85868A; font-weight:normal;'>{w} x {h} px</span>"
                
                lbl_interno = QLabel(btn)
                lbl_interno.setText(texto_tarjeta)
                lbl_interno.setTextFormat(Qt.TextFormat.RichText) 
                lbl_interno.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_interno.setGeometry(0, 0, 140, 100) 
                lbl_interno.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                lbl_interno.setStyleSheet("border:none; color:#D1D1D5;") 
                
                btn.clicked.connect(lambda checked, w=w, h=h, m=modo: self._cargar_preset(w, h, m))
                
                grid.addWidget(btn, row, col)
                col += 1
                if col > 2: col, row = 0, row + 1
            
            layout_presets.addLayout(grid)
            
        layout_presets.addStretch()
        scroll_area.setWidget(contenedor_presets)
        
        layout_principal.addWidget(scroll_area, stretch=6)

        # =========================================================
        # COLUMNA DERECHA: CONFIGURACIÓN EXACTA
        # =========================================================
        panel_derecho = QFrame()
        panel_derecho.setObjectName("panel_der")
        panel_derecho.setStyleSheet(f"""
            #panel_der {{ background-color: #1A1B1E; border-left: 1px solid #2A2B31; border-top-right-radius: 11px; border-bottom-right-radius: 11px; }}
        """)
        
        layout_der = QVBoxLayout(panel_derecho)
        layout_der.setContentsMargins(25, 30, 25, 30)
        layout_der.setSpacing(20)

        lbl_detalles = QLabel("Detalles del Proyecto")
        lbl_detalles.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 18px; font-weight: bold; font-family: 'Gilroy'; border:none;")
        layout_der.addWidget(lbl_detalles)

        # Inputs de Tamaño
        row_tamano = QHBoxLayout()
        self.input_w = QLineEdit("1080")
        self.input_h = QLineEdit("1080")
        
        ancho_minimo_input = 90 
        estilo_input = f"background: #121214; border: 1px solid #2A2B31; border-radius: 6px; color: {TEXT_MAIN}; padding: 10px; font-size: 14px; font-weight: bold; font-family: 'Gilroy';"
        
        self.input_w.setStyleSheet(estilo_input)
        self.input_h.setStyleSheet(estilo_input)
        self.input_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_w.setMinimumWidth(ancho_minimo_input) 
        self.input_h.setMinimumWidth(ancho_minimo_input) 
        
        lbl_w = QLabel("Ancho:"); lbl_w.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; font-size: 12px;")
        lbl_h = QLabel("Alto:"); lbl_h.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; font-size: 12px;")
        
        row_tamano.addWidget(lbl_w)
        row_tamano.addWidget(self.input_w)
        row_tamano.addWidget(lbl_h)
        row_tamano.addWidget(self.input_h)
        layout_der.addLayout(row_tamano)

        lbl_color = QLabel("Modo de Color:")
        lbl_color.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; font-size: 12px;")
        layout_der.addWidget(lbl_color)
        
        # 🚀 INYECTAMOS NUESTRO DROPDOWN PREMIUM
        self.combo_color = PremiumDropdown(["RGB (Pantallas / Digital)", "CMYK (Impresión Profesional)"])
        layout_der.addWidget(self.combo_color)

        lbl_dpi = QLabel("Resolución (PPP):")
        lbl_dpi.setStyleSheet(f"color: {TEXT_MUTED}; font-weight: bold; font-size: 12px;")
        layout_der.addWidget(lbl_dpi)
        
        # 🚀 INYECTAMOS NUESTRO DROPDOWN PREMIUM
        self.combo_dpi = PremiumDropdown(["72 ppp (Óptimo para Web)", "150 ppp (Media Calidad)", "300 ppp (Alta Impresión)"])
        layout_der.addWidget(self.combo_dpi)

        layout_der.addStretch()

        # Botones de Acción
        btn_crear = QPushButton("Crear Proyecto")
        btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_crear.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; border-radius: 8px; padding: 12px; font-weight: bold; font-size: 14px; border: none;")
        btn_crear.clicked.connect(self._aceptar)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("background-color: transparent; border: 1px solid #3F4148; color: #D1D1D5; border-radius: 8px; padding: 12px; font-weight: bold;")
        btn_cancelar.clicked.connect(self.reject)

        layout_der.addWidget(btn_crear)
        layout_der.addWidget(btn_cancelar)

        layout_principal.addWidget(panel_derecho, stretch=4)

    def _cargar_preset(self, w, h, modo):
        """Llena el panel derecho con los datos de la tarjeta clickeada"""
        self.input_w.setText(str(w))
        self.input_h.setText(str(h))
        idx = 0 if modo == "RGB" else 1
        self.combo_color.setCurrentIndex(idx)
        if modo == "CMYK": self.combo_dpi.setCurrentIndex(2) 
        else: self.combo_dpi.setCurrentIndex(0)

    def _aceptar(self):
        """Valida y empaqueta la información para crear el lienzo"""
        try:
            w = int(self.input_w.text())
            h = int(self.input_h.text())
            modo = "RGB" if self.combo_color.currentIndex() == 0 else "CMYK"
            dpi = [72, 150, 300][self.combo_dpi.currentIndex()]
            self.resultado = (w, h, modo, dpi)
            self.accept()
        except ValueError:
            pass
            
class FontPickerPopup(QDialog):
    """Un menú flotante premium y buscador de fuentes con vista previa en vivo"""
    font_selected = pyqtSignal(str)

    def __init__(self, current_font, font_list, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.font_list = font_list

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(15, 15, 15, 15)

        container = QFrame(self)
        container.setStyleSheet(f"background-color: #121214; border: 1px solid #2A2B31; border-radius: 8px;")
        apply_shadow(container, radius=20, offset_y=8)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- BARRA DE BÚSQUEDA ---
        search_bg = QFrame()
        search_bg.setStyleSheet("background-color: #18191D; border-radius: 6px; border: 1px solid transparent;")
        s_lay = QHBoxLayout(search_bg)
        s_lay.setContentsMargins(8, 6, 8, 6)
        s_lay.setSpacing(8)
        
        search_icon = QLabel()
        search_icon.setPixmap(qta.icon('fa5s.search', color=ICON_MUTED).pixmap(12, 12))
        s_lay.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar fuente...")
        self.search_input.setStyleSheet(f"background: transparent; border: none; color: {TEXT_MAIN}; font-size: 12px; font-weight: bold;")
        self.search_input.textChanged.connect(self._filter_fonts)
        s_lay.addWidget(self.search_input)
        
        layout.addWidget(search_bg)

        # --- LISTA DE FUENTES ---
        self.list_widget = QListWidget()
        
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ color: {TEXT_MUTED}; padding: 8px 10px; border-radius: 6px; }}
            QListWidget::item:hover {{ background-color: #18191D; color: {TEXT_MAIN}; }}
            QListWidget::item:selected {{ background-color: {COLOR_ACCENT}; color: #FFFFFF; }}
        """)
        
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setTextElideMode(Qt.TextElideMode.ElideRight) 
        
        self.list_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._populate_list(self.font_list)
        layout.addWidget(self.list_widget)

        self.list_widget.itemClicked.connect(self._on_item_clicked)
        base_layout.addWidget(container)
        
        self.setFixedSize(240, 320)

    def _populate_list(self, fonts):
        self.list_widget.clear()
        for f in fonts:
            item = QListWidgetItem(f)
            item.setFont(QFont(f, 14)) 
            self.list_widget.addItem(item)

    def _filter_fonts(self, text):
        filtered = [f for f in self.font_list if text.lower() in f.lower()]
        self._populate_list(filtered)

    def _on_item_clicked(self, item):
        self.font_selected.emit(item.text())
        self.accept()
            
class PremiumMessageBox(QDialog):
    """Un cuadro de diálogo flotante y elegante tipo Figma"""
    def __init__(self, parent, titulo, mensaje, botones):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resultado = None
        
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(15, 15, 15, 15)
        
        container = QFrame()
        # Aquí usamos el color de fondo definido en tu main
        container.setStyleSheet(f"QFrame {{ background-color: #1A1B1E; border-radius: 12px; border: 1px solid #2A2B31; }}")
        apply_shadow(container, radius=25, offset_y=8)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        layout.addWidget(lbl_titulo)
        
        lbl_msg = QLabel(mensaje)
        lbl_msg.setWordWrap(True)
        lbl_msg.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(lbl_msg)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        for texto, rol, color_bg in botones:
            btn = QPushButton(texto)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            bg = color_bg if color_bg else "#2A2B31"
            hover = "#E04B2A" if color_bg == COLOR_ACCENT else "#FF4040" if color_bg == "#FF5C5C" else "#3F4148"
            
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {bg}; color: {TEXT_MAIN}; border-radius: 6px; padding: 8px 20px; font-weight: bold; border: none; }}
                QPushButton:hover {{ background-color: {hover}; }}
            """)
            btn.clicked.connect(lambda checked, r=rol: self.cerrar_con_resultado(r))
            btn_layout.addWidget(btn)
            
        layout.addLayout(btn_layout)
        base_layout.addWidget(container)
        self.start_pos = None

    def cerrar_con_resultado(self, rol):
        self.resultado = rol
        self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()
            
    def mouseMoveEvent(self, event):
        if getattr(self, 'start_pos', None) is not None:
            delta = event.globalPosition().toPoint() - self.start_pos
            self.move(self.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        self.start_pos = None

# =========================================================
# 🎨 RECREACIÓN PREMIUM: SELECTOR DE COLOR ESTILO FIGMA
# =========================================================
from PyQt6.QtGui import QColor, QPainter, QLinearGradient, QConicalGradient, QBrush, QPen, QAction
from PyQt6.QtWidgets import (QDialog, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QStackedWidget, QSlider, QWidget, QGridLayout, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QPointF, QSize, pyqtSignal, QRectF
import math

# --- 🚀 WIDGETS PERSONALIZADOS PARA EL SELECTOR ---

# =========================================================
# 🎨 WIDGETS PERSONALIZADOS PARA EL SELECTOR
# =========================================================
class SaturationBrightnessField(QWidget):
    """Campo cuadrado para seleccionar saturación y brillo"""
    colorChanged = pyqtSignal(float, float)

    def __init__(self, color_base=Qt.GlobalColor.red, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 200)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.hue_color = QColor(color_base)
        self.sat = 0.0 
        self.val = 0.0 

    def set_hue(self, qcolor):
        self.hue_color = qcolor
        self.update()

    def set_sv(self, sat, val):
        self.sat, self.val = sat, val
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            
            painter.setPen(Qt.PenStyle.NoPen) 

            # 1. CAPA BASE: El color puro
            painter.setBrush(QBrush(self.hue_color))
            painter.drawRoundedRect(rect, 8, 8)
            
            # 2. CAPA DE SATURACIÓN: Blanco a Transparente
            grad_sat = QLinearGradient(0, 0, rect.width(), 0)
            grad_sat.setColorAt(0, QColor(255, 255, 255, 255))
            grad_sat.setColorAt(1, QColor(255, 255, 255, 0))   
            painter.setBrush(QBrush(grad_sat))
            painter.drawRoundedRect(rect, 8, 8)
            
            # 3. CAPA DE BRILLO: Transparente a Negro
            grad_val = QLinearGradient(0, 0, 0, rect.height())
            grad_val.setColorAt(0, QColor(0, 0, 0, 0))   
            grad_val.setColorAt(1, QColor(0, 0, 0, 255)) 
            painter.setBrush(QBrush(grad_val))
            painter.drawRoundedRect(rect, 8, 8)

            # 4. SELECTOR (Círculo)
            x = self.sat * rect.width()
            y = (1.0 - self.val) * rect.height()
            
            x = max(6, min(rect.width() - 6, x))
            y = max(6, min(rect.height() - 6, y))

            painter.setPen(QPen(Qt.GlobalColor.white, 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(x, y), 6, 6)
            
        except Exception as e:
            print(f"❌ Error visual en Saturation Field: {e}")

    def mousePressEvent(self, event): self._actualizar_desde_click(event.pos())
    def mouseMoveEvent(self, event): self._actualizar_desde_click(event.pos())

    def _actualizar_desde_click(self, pos):
        self.sat = max(0.0, min(1.0, pos.x() / self.width()))
        self.val = max(0.0, min(1.0, 1.0 - (pos.y() / self.height())))
        self.update()
        self.colorChanged.emit(self.sat, self.val)

class PremiumSliderCustom(QSlider):
    """Base para sliders de tono y opacidad con gráficos personalizados"""
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setFixedHeight(12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setProperty("premium", True)
        
    def paintEvent(self, event):
        # Desactivamos el dibujado por defecto para controlar la previsualización
        pass

class HueSlider(QWidget):
    hueChanged = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 24) 
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hue = 0.0

    def set_hue(self, hue):
        self.hue = hue
        self.update()

    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = self.rect()
            
            bar_height = 10
            bar_y = int((rect.height() - bar_height) / 2)
            bar_rect = QRectF(0, bar_y, rect.width(), bar_height)
            
            grad = QLinearGradient(0, 0, rect.width(), 0)
            grad.setColorAt(0.0, Qt.GlobalColor.red)
            grad.setColorAt(1/6, QColor("#FFFF00"))
            grad.setColorAt(2/6, Qt.GlobalColor.green)
            grad.setColorAt(3/6, Qt.GlobalColor.cyan)
            grad.setColorAt(4/6, Qt.GlobalColor.blue)
            grad.setColorAt(5/6, QColor("#FF00FF"))
            grad.setColorAt(1.0, Qt.GlobalColor.red)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(bar_rect, 5, 5) 
            
            # 🚀 CORRECCIÓN: Círculo más pequeño (radio=6) y con márgenes seguros
            radio = 6 
            track_width = rect.width() - (radio * 2)
            # El centro (x) ahora viaja desde 'radio' hasta 'width - radio'
            x = radio + (self.hue / 360.0) * track_width
            
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.drawEllipse(QPointF(x, rect.height()/2.0 + 1), radio, radio)
            
            painter.setPen(QPen(Qt.GlobalColor.white, 2.5))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(QPointF(x, rect.height()/2.0), radio, radio)
        except Exception as e:
            print(f"❌ Error visual en Hue Slider: {e}")

    def mousePressEvent(self, event): self._actualizar_desde_click(event.pos())
    def mouseMoveEvent(self, event): self._actualizar_desde_click(event.pos())

    def _actualizar_desde_click(self, pos):
        # 🚀 CORRECCIÓN: Ajustamos la zona de clic al mismo margen seguro
        radio = 6
        track_width = self.width() - (radio * 2)
        normalized_x = (pos.x() - radio) / track_width
        self.hue = max(0.0, min(360.0, normalized_x * 360.0))
        self.update()
        self.hueChanged.emit(self.hue)


class AlphaSlider(QWidget):
    alphaChanged = pyqtSignal(float) 

    def __init__(self, color_base="#FFFFFF", parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 12)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_base = QColor(color_base)
        self.alpha = 1.0 

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.update()

    def set_color_base(self, hex_color):
        if QColor.isValidColor(hex_color):
            self.color_base = QColor(hex_color)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        painter.setPen(Qt.PenStyle.NoPen)
        
        t_sz = 6
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRoundedRect(rect, 6, 6)
        painter.setBrush(QColor("#D1D1D5"))
        for i in range(0, rect.width(), t_sz*2):
            for j in range(0, rect.height(), t_sz):
                off = t_sz if (j // t_sz) % 2 else 0
                painter.drawRect(i + off, j, t_sz, t_sz)

        grad = QLinearGradient(0, 0, rect.width(), 0)
        c_trans = QColor(self.color_base)
        c_trans.setAlpha(0)
        grad.setColorAt(0.0, c_trans)
        grad.setColorAt(1.0, self.color_base)
        
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(rect, 6, 6)
        
        # 🚀 CORRECCIÓN: Círculo más pequeño (radio=6) y con márgenes seguros
        radio = 6
        track_width = rect.width() - (radio * 2)
        x = radio + (self.alpha * track_width)
        
        painter.setPen(QPen(Qt.GlobalColor.white, 2.5))
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawEllipse(QPointF(x, rect.height()/2), radio, radio)

    def mousePressEvent(self, event): self._actualizar_desde_click(event.pos())
    def mouseMoveEvent(self, event): self._actualizar_desde_click(event.pos())

    def _actualizar_desde_click(self, pos):
        # 🚀 CORRECCIÓN: Ajustamos la zona de clic al mismo margen seguro
        radio = 6
        track_width = self.width() - (radio * 2)
        normalized_x = (pos.x() - radio) / track_width
        self.alpha = max(0.0, min(1.0, normalized_x))
        self.update()
        self.alphaChanged.emit(self.alpha)


from PyQt6.QtWidgets import QComboBox # Asegúrate de que esto esté arriba en tus imports

class PremiumColorPicker(QDialog):
    def __init__(self, color_inicial="#FFFFFFFF", mostrar_opacidad=True, modo_forzado=None, parent=None):
        super().__init__(parent)
        
        if not color_inicial: 
            color_inicial = "#FFFFFFFF"
            
        self.setFixedWidth(320)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.mostrar_opacidad = mostrar_opacidad
        self.modo_forzado = modo_forzado 
        
        try:
            self.color_actual = QColor(color_inicial)
            self._construir_ui()
            
            # 🚀 Lógica de Pestañas y Ocultamiento de HEX
            if self.modo_forzado == "CMYK":
                self.cmb_mode.setCurrentIndex(1)
                self.stack_inputs.setCurrentIndex(1)
                self.cmb_mode.hide()
                self.txt_hex_container.hide() # Ocultar el HEX en impresión
            elif self.modo_forzado == "RGB":
                self.cmb_mode.setCurrentIndex(0)
                self.stack_inputs.setCurrentIndex(0)
                self.cmb_mode.hide()
                self.txt_hex_container.show()

            hue_val = max(0, self.color_actual.hue())
            hue_f = max(0.0, self.color_actual.hueF())
            
            self.sat_field.set_hue(QColor.fromHsv(hue_val, 255, 255))
            self.sat_field.set_sv(self.color_actual.saturationF(), self.color_actual.valueF())
            self.hue_slider.set_hue(hue_f * 360.0)
            self.alpha_slider.set_color_base(self.color_actual.name())
            self.alpha_slider.set_alpha(self.color_actual.alphaF())
            
            self._actualizar_desde_color(self.color_actual)
            apply_shadow(self.container)

            self.setFocus()
            
        except Exception as e:
            import traceback
            print(f"❌ [CRASH PREVENIDO en Init Picker]: {e}")
            traceback.print_exc()

    def _construir_ui(self):
        layout_global = QVBoxLayout(self)
        layout_global.setContentsMargins(10, 10, 10, 10)
        layout_global.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        
        self.container = QFrame(self)
        self.container.setObjectName("color_picker_container") # 🚀 ID ÚNICO
        
        # 🚀 LA CURA DE LOS CUADRADOS RAROS: Le decimos a Qt que SOLO le ponga el borde al contenedor principal
        self.container.setStyleSheet("""
            #color_picker_container { background-color: #1A1B1E; border-radius: 12px; border: 1px solid #3F4148; }
            QLabel { border: none; background: transparent; }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        self.sat_field = SaturationBrightnessField(parent=self)
        self.sat_field.colorChanged.connect(self._sat_val_cambiado)
        layout.addWidget(self.sat_field, alignment=Qt.AlignmentFlag.AlignCenter)
        
        lay_sliders = QVBoxLayout()
        lay_sliders.setSpacing(10)
        self.hue_slider = HueSlider(parent=self)
        self.hue_slider.hueChanged.connect(self._hue_cambiado)
        lay_sliders.addWidget(self.hue_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.alpha_slider = AlphaSlider(parent=self)
        self.alpha_slider.alphaChanged.connect(self._alpha_cambiado)
        if self.mostrar_opacidad:
            lay_sliders.addWidget(self.alpha_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            self.alpha_slider.hide()
        layout.addLayout(lay_sliders)
        
        # ==========================================
        # 🚀 SECCIÓN: CUENTAGOTAS + BARRA DE COLOR
        # ==========================================
        lay_previa_mode = QHBoxLayout()
        lay_previa_mode.setSpacing(10)
        
        # 1. El botón de cuentagotas
        self.btn_eyedropper = QPushButton()
        self.btn_eyedropper.setFixedSize(32, 32)
        self.btn_eyedropper.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eyedropper.setIcon(qta.icon('fa5s.eye-dropper', color="#85868A"))
        self.btn_eyedropper.setStyleSheet("""
            QPushButton { background-color: #121214; border: 1px solid #3F4148; border-radius: 6px; }
            QPushButton:hover { border: 1px solid #FE5934; background-color: #1A1B1E; }
        """)
        self.btn_eyedropper.clicked.connect(self._activar_cuentagotas)
        lay_previa_mode.addWidget(self.btn_eyedropper)
        
        # 2. La barra de previsualización (se expande sola)
        self.color_preview = QFrame()
        self.color_preview.setFixedHeight(32) 
        lay_previa_mode.addWidget(self.color_preview)
        
        # 3. El selector de Modo
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["RGB", "CMYK"])
        self.cmb_mode.setFixedHeight(32)
        self.cmb_mode.setStyleSheet("""
            QComboBox { background-color: #121214; color: white; border: 1px solid #3F4148; border-radius: 6px; padding: 0px 10px; font-weight: bold; font-family: 'Gilroy'; }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_mode.currentIndexChanged.connect(self._cambiar_modo_inputs)
        lay_previa_mode.addWidget(self.cmb_mode)
        layout.addLayout(lay_previa_mode)
        
        # ==========================================
        # 🚀 SECCIÓN: INPUTS
        # ==========================================
        lay_inputs_row = QHBoxLayout()
        lay_inputs_row.setSpacing(8)
        
        # Aquí ya solo dejamos el contenedor del HEX
        self.txt_hex_container = self._crear_input_hex()
        lay_inputs_row.addWidget(self.txt_hex_container)
        
        self.stack_inputs = QStackedWidget()
        self.stack_inputs.setFixedHeight(50)
        self.stack_inputs.setStyleSheet("QStackedWidget { border: none; background: transparent; }") # Limpieza extra
        
        page_rgb = QWidget()
        page_rgb.setObjectName("transparent_wrapper")
        page_rgb.setStyleSheet("#transparent_wrapper { border: none; background: transparent; }")
        lay_rgb = QHBoxLayout(page_rgb)
        lay_rgb.setContentsMargins(0,0,0,0)
        lay_rgb.setSpacing(4)
        self.spn_r = self._crear_input_num("R", 255)
        self.spn_g = self._crear_input_num("G", 255)
        self.spn_b = self._crear_input_num("B", 255)
        lay_rgb.addWidget(self.spn_r); lay_rgb.addWidget(self.spn_g); lay_rgb.addWidget(self.spn_b)
        if self.mostrar_opacidad:
            self.spn_a_rgb = self._crear_input_num("A", 100)
            lay_rgb.addWidget(self.spn_a_rgb)
        self.stack_inputs.addWidget(page_rgb)
        
        page_cmyk = QWidget()
        page_cmyk.setObjectName("transparent_wrapper")
        page_cmyk.setStyleSheet("#transparent_wrapper { border: none; background: transparent; }")
        lay_cmyk = QHBoxLayout(page_cmyk)
        lay_cmyk.setContentsMargins(0,0,0,0)
        lay_cmyk.setSpacing(4)
        self.spn_c = self._crear_input_num("C", 100)
        self.spn_m = self._crear_input_num("M", 100)
        self.spn_y = self._crear_input_num("Y", 100)
        self.spn_k = self._crear_input_num("K", 100)
        lay_cmyk.addWidget(self.spn_c); lay_cmyk.addWidget(self.spn_m)
        lay_cmyk.addWidget(self.spn_y); lay_cmyk.addWidget(self.spn_k)
        if self.mostrar_opacidad:
            self.spn_a_cmyk = self._crear_input_num("A", 100)
            lay_cmyk.addWidget(self.spn_a_cmyk)
        self.stack_inputs.addWidget(page_cmyk)
        
        lay_inputs_row.addWidget(self.stack_inputs)
        layout.addLayout(lay_inputs_row)
        
        lay_btns = QHBoxLayout()
        lay_btns.setContentsMargins(0, 5, 0, 0)
        
        btn_cancel = QPushButton(" Cancelar")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("background-color:transparent; color:#D1D1D5; border:1px solid #3F4148; border-radius:6px; padding:10px; font-weight:bold; font-family:'Gilroy';")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton(" Guardar Color")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("background-color:#FE5934; color:#FFF; border-radius:6px; padding:10px; font-weight:bold; font-family:'Gilroy'; border:none;")
        btn_save.clicked.connect(self.accept)
        
        lay_btns.addWidget(btn_cancel)
        lay_btns.addWidget(btn_save)
        layout.addLayout(lay_btns)
        
        layout_global.addWidget(self.container)

    def _crear_input_hex(self):
        widget = QWidget()
        # 🚀 BLINDAJE: Evita que herede bordes globales de QWidget
        widget.setObjectName("transparent_wrapper")
        widget.setStyleSheet("#transparent_wrapper { border: none; background: transparent; }")
        
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4) 
        
        label = QLabel("HEX")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color:#85868A; font-size:10px; font-weight:bold; font-family:'Gilroy'; background: transparent; border: none;")
        lay.addWidget(label)
        
        self.txt_hex = QLineEdit()
        self.txt_hex.setFixedWidth(65)
        self.txt_hex.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_hex.setStyleSheet("""
            QLineEdit { 
                background-color: #121214; 
                color: white; 
                border: 1px solid #2A2B31; 
                border-radius: 6px; 
                padding: 6px; 
                font-family: 'Courier'; 
                font-weight: bold; 
                font-size: 11px; 
            }
            QLineEdit:hover { border: 1px solid #3F4148; }
            QLineEdit:focus { border: 1px solid #FE5934; }
        """)
        self.txt_hex.textEdited.connect(self._desde_hex)
        lay.addWidget(self.txt_hex)
        
        return widget

    def _crear_input_num(self, label_text, max_val):
        widget = QWidget()
        # 🚀 BLINDAJE: Evita que herede bordes globales
        widget.setObjectName("transparent_wrapper")
        widget.setStyleSheet("#transparent_wrapper { border: none; background: transparent; }")
        
        lay = QVBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4) 
        
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color:#85868A; font-size:10px; font-weight:bold; font-family:'Gilroy'; background: transparent; border: none;")
        lay.addWidget(label)
        
        spin = QDoubleSpinBox()
        spin.setRange(0, max_val)
        spin.setDecimals(0)
        spin.setMinimumWidth(38) 
        spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #121214; 
                color: white; 
                border: 1px solid #2A2B31; 
                border-radius: 6px; 
                padding: 6px; 
                font-weight: bold; 
                font-size: 11px; 
                font-family: 'Gilroy'; 
            }
            QDoubleSpinBox:hover { border: 1px solid #3F4148; }
            QDoubleSpinBox:focus { border: 1px solid #FE5934; }
        """)
        spin.valueChanged.connect(self._desde_spinboxes)
        lay.addWidget(spin)
        
        return widget

    def _cambiar_modo_inputs(self, idx):
        self.stack_inputs.setCurrentIndex(idx)
        # 🚀 Si cambian el dropdown a CMYK, se oculta el HEX automáticamente
        if idx == 1: self.txt_hex_container.hide()
        else: self.txt_hex_container.show()
        
        self._bloqueo_signals = True 
        self._actualizar_spinboxes(self.color_actual)
        self._bloqueo_signals = False

    def _hue_cambiado(self, hue):
        try:
            # 🚀 LA CURA: Forzamos a que el máximo absoluto sea 359
            hue_seguro = min(359, max(0, int(hue))) 
            
            c_base = QColor.fromHsv(hue_seguro, 255, 255)
            self.sat_field.set_hue(c_base)
            qcolor = QColor.fromHsv(hue_seguro, int(self.sat_field.sat * 255), int(self.sat_field.val * 255))
            qcolor.setAlphaF(self.alpha_slider.alpha)
            self._actualizar_desde_color(qcolor, ignorar_campo=True, ignorar_tono=True, ignorar_alpha=True)
        except Exception as e: print(f"❌ Error _hue_cambiado: {e}")

    def _sat_val_cambiado(self, sat, val):
        try:
            # 🚀 LA CURA: Igual aquí, nos aseguramos de que no llegue a 360
            hue_seguro = min(359, max(0, int(self.hue_slider.hue))) 
            
            qcolor = QColor.fromHsv(hue_seguro, int(sat * 255), int(val * 255))
            qcolor.setAlphaF(self.alpha_slider.alpha)
            self._actualizar_desde_color(qcolor, ignorar_campo=True, ignorar_tono=True, ignorar_alpha=True)
        except Exception as e: print(f"❌ Error _sat_val_cambiado: {e}")

    def _alpha_cambiado(self, alpha):
        self.color_actual.setAlphaF(alpha)
        self._bloqueo_signals = True
        if self.mostrar_opacidad:
            self._set_spin_value(self.spn_a_rgb, int(alpha * 100))
            self._set_spin_value(self.spn_a_cmyk, int(alpha * 100))
        self._bloqueo_signals = False
        self._set_preview_style(self.color_actual)

    def _desde_hex(self, text):
        if text.startswith("#") and QColor.isValidColor(text):
            try:
                qcolor = QColor(text)
                if len(text) <= 7: qcolor.setAlphaF(self.alpha_slider.alpha)
                hue_val = max(0, qcolor.hue())
                hue_f = max(0.0, qcolor.hueF())
                self.sat_field.set_hue(QColor.fromHsv(hue_val, 255, 255))
                self.sat_field.set_sv(qcolor.saturationF(), qcolor.valueF())
                self.hue_slider.set_hue(hue_f * 360.0)
                self.alpha_slider.set_alpha(qcolor.alphaF())
                self._actualizar_desde_color(qcolor, ignorar_campo=True, ignorar_tono=True, ignorar_alpha=True, ignorar_hex=True)
            except Exception as e: print(f"❌ Error _desde_hex: {e}")

    def _desde_spinboxes(self, _):
        if getattr(self, '_bloqueo_signals', False): return
        try:
            # 🚀 Detectamos qué pestaña está viendo el usuario (RGB o CMYK)
            if self.stack_inputs.currentIndex() == 0: # RGB
                r = int(self._get_spin_value(self.spn_r))
                g = int(self._get_spin_value(self.spn_g))
                b = int(self._get_spin_value(self.spn_b))
                qcolor = QColor(r, g, b)
                alpha = self._get_spin_value(self.spn_a_rgb)/100.0 if self.mostrar_opacidad else 1.0
                qcolor.setAlphaF(alpha)
            else: # CMYK
                c = self._get_spin_value(self.spn_c)/100.0
                m = self._get_spin_value(self.spn_m)/100.0
                y = self._get_spin_value(self.spn_y)/100.0
                k = self._get_spin_value(self.spn_k)/100.0
                # Conversión corregida
                r = int(255 * (1 - c) * (1 - k))
                g = int(255 * (1 - m) * (1 - k))
                b = int(255 * (1 - y) * (1 - k))
                qcolor = QColor(r, g, b)
                alpha = self._get_spin_value(self.spn_a_cmyk)/100.0 if self.mostrar_opacidad else 1.0
                qcolor.setAlphaF(alpha)
            
            # Sincronizar el resto del diálogo
            self._actualizar_desde_color(qcolor, ignorar_spinboxes=True)
        except Exception as e:
            print(f"Error en spinboxes: {e}")

    def _activar_cuentagotas(self):
        # 1. Nos escondemos, pero como abrimos con .open(), NO bloqueamos la app
        self.hide() 
        
        # 2. Le avisamos a la ventana principal que estamos esperando un color
        main_studio = self.parentWidget().window() if self.parentWidget() else None
        if hasattr(main_studio, 'preparar_receptor_color'):
            main_studio.preparar_receptor_color(self)
            
        # 3. Forzamos la herramienta simulando un clic en la barra flotante
        if hasattr(main_studio, 'main_canvas') and hasattr(main_studio.main_canvas, 'toolbar'):
            # Encontramos el botón del cuentagotas
            btn_gotero = next((b for b in main_studio.main_canvas.toolbar.btn_group.buttons() if b.property("tool_id") == "eyedropper"), None)
            if btn_gotero:
                btn_gotero.click() # Simulamos el clic para que active toda la maquinaria

    def recibir_color_robado(self, qcolor):
        """Recibe el color final y vuelve a mostrar el diálogo"""
        self._actualizar_desde_color(qcolor)
        self.show()
        self.raise_()
        
    def recibir_color_hover(self, qcolor):
        """Previsualiza el color mientras se mueve el ratón"""
        self._actualizar_desde_color(qcolor)

    def cancelar_robo(self):
        """Si el usuario se arrepiente y presiona ESC o clic derecho, vuelve a aparecer"""
        self.show()
        self.raise_()

    def _actualizar_desde_color(self, qcolor, ignorar_campo=False, ignorar_tono=False, ignorar_alpha=False, ignorar_hex=False, ignorar_spinboxes=False):
        try:
            self.color_actual = qcolor
            self._bloqueo_signals = True
            self._set_preview_style(qcolor)
            self.alpha_slider.set_color_base(qcolor.name())
            
            hue_f = max(0.0, qcolor.hueF())
            if not ignorar_campo: self.sat_field.set_sv(qcolor.saturationF(), qcolor.valueF())
            if not ignorar_tono: self.hue_slider.set_hue(hue_f * 360.0)
            if not ignorar_alpha: self.alpha_slider.set_alpha(qcolor.alphaF())
            
            if not ignorar_hex:
                if self.mostrar_opacidad: 
                    self.txt_hex.setText(qcolor.name(QColor.NameFormat.HexArgb).upper())
                else: 
                    self.txt_hex.setText(qcolor.name(QColor.NameFormat.HexRgb).upper())
                
            if not ignorar_spinboxes: self._actualizar_spinboxes(qcolor)
            self._bloqueo_signals = False
        except Exception as e: print(f"❌ Error _actualizar_desde_color: {e}")

    def _actualizar_spinboxes(self, qcolor):
        if self.stack_inputs.currentIndex() == 0:
            self._set_spin_value(self.spn_r, qcolor.red())
            self._set_spin_value(self.spn_g, qcolor.green())
            self._set_spin_value(self.spn_b, qcolor.blue())
            if self.mostrar_opacidad: self._set_spin_value(self.spn_a_rgb, int(qcolor.alphaF() * 100))
        else:
            r_p, g_p, b_p = qcolor.red()/255, qcolor.green()/255, qcolor.blue()/255
            k = 1 - max(r_p, g_p, b_p)
            if k == 1: c = m = y = 0
            else: c, m, y = (1 - r_p - k) / (1 - k), (1 - g_p - k) / (1 - k), (1 - b_p - k) / (1 - k)
            self._set_spin_value(self.spn_c, int(c * 100))
            self._set_spin_value(self.spn_m, int(m * 100))
            self._set_spin_value(self.spn_y, int(y * 100))
            self._set_spin_value(self.spn_k, int(k * 100))
            if self.mostrar_opacidad: self._set_spin_value(self.spn_a_cmyk, int(qcolor.alphaF() * 100))

    def _set_preview_style(self, qcolor):
        self.color_preview.setStyleSheet(f"background-color: {qcolor.name(QColor.NameFormat.HexRgb)}; border-radius: 6px; border: 1px solid #3F4148;")

    def _set_spin_value(self, widget, value):
        spin = widget.findChild(QDoubleSpinBox)
        if spin:
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)

    def _get_spin_value(self, widget):
        spin = widget.findChild(QDoubleSpinBox)
        return spin.value() if spin else 0.0

    def get_color(self):
        if self.mostrar_opacidad:
            # Qt necesita formato #AARRGGBB cuando hay opacidad
            return self.color_actual.name(QColor.NameFormat.HexArgb).upper()
        else:
            # Formato clásico #RRGGBB para colores sólidos
            return self.color_actual.name(QColor.NameFormat.HexRgb).upper()