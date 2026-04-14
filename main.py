import sys
import io
import os
import math
import copy
import platform
import psutil
import time
from PIL import Image

Image.MAX_IMAGE_PIXELS = None 
from PyQt6.QtGui import QImageReader
QImageReader.setAllocationLimit(2048)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QPushButton, QLineEdit, QFrame, QGraphicsDropShadowEffect, 
                             QScrollArea, QTabWidget, QGraphicsView, QGraphicsScene, 
                             QGraphicsItemGroup, QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem,
                             QSlider, QSizePolicy, QTreeWidget, QTreeWidgetItem, QGraphicsPixmapItem, QTreeWidgetItemIterator,
                             QGraphicsPathItem, QGraphicsTextItem, QGraphicsSimpleTextItem, QGraphicsItem, QComboBox, QListWidget, QListWidgetItem, QAbstractItemView,
                             QFileDialog, QMenu, QWidgetAction, QDialog, QMessageBox, QTabBar, QSizeGrip, QStackedWidget, QButtonGroup, QProxyStyle, QStyle)
from PyQt6.QtCore import Qt, QSize, QRect, pyqtSignal, QTimer, QPointF, QEvent
from PyQt6.QtGui import (QIcon, QColor, QPalette, QFont, QPainter, QBrush, QPen, 
                         QLinearGradient, QPixmap, QPainterPath, QFontDatabase,
                         QTransform, QCursor, QFontMetricsF)
import qtawesome as qta
from motor_grafico import RectorOP
from dialogs import NewDocumentDialog
from properties_panel import PropertiesPanel

# --- COLORES EXACTOS DEL DISEÑO PREMIUM ---
BG_NAV = "#1A1B1E"          # Fondo de la barra de navegación (Columna 1)
BG_ASSETS = "#2C2E33"
BORDER_NAV = "#2A2B31"       # Fondo del panel de activos (Columna 2)
BG_CANVAS_HEADER = "#2C2E33" # Fondo del encabezado del lienzo
BG_CANVAS_BODY = "#121214"   # Fondo del lienzo abismal (Columna 3)
BG_PROPERTIES = "#2C2E33"    # Fondo del panel de propiedades (Columna 4)
BG_PANEL_HOVER = "#2D2E36"   # Hover de botones oscuros
COLOR_ACCENT = "#FE5934"     # Naranja vibrante
TEXT_MAIN = "#FFFFFF"        # Texto blanco
TEXT_MUTED = "#85868A"       # Texto gris
ICON_MUTED = "#85868A"       # Iconos grises

# Configuración de fuente (Asegúrate de tener Gilroy instalada)
GLOBAL_FONT_FAMILY = "Gilroy" 
GLOBAL_FONT_SIZE = 10

# =======================================================
# 🚀 CACHÉ GLOBAL DE ICONOS (VELOCIDAD EXTREMA)
# =======================================================
_GLOBAL_ICON_CACHE = {}
def get_cached_icon(icon_name, color, size=16, as_icon=False):
    key = f"{icon_name}_{color}_{size}_{as_icon}"
    if key not in _GLOBAL_ICON_CACHE:
        if as_icon:
            _GLOBAL_ICON_CACHE[key] = qta.icon(icon_name, color=color)
        else:
            _GLOBAL_ICON_CACHE[key] = qta.icon(icon_name, color=color).pixmap(size, size)
    return _GLOBAL_ICON_CACHE[key]
# =======================================================

def set_premium_dark_theme(app):
    """Aplica la paleta de colores y la fuente global Gilroy a la aplicación"""
    app.setStyle("Fusion")
    
    # Aplicar la fuente global Gilroy
    gilroy_font = QFont(GLOBAL_FONT_FAMILY, GLOBAL_FONT_SIZE)
    app.setFont(gilroy_font)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_NAV))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_MAIN))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG_ASSETS))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_NAV))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(TEXT_MAIN))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT_MAIN))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_MAIN))
    palette.setColor(QPalette.ColorRole.Button, QColor(BG_ASSETS))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_MAIN))
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Link, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLOR_ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)
    # --- SCROLLBARS PREMIUM (Minimalistas y Oscuras) ---
    app.setStyleSheet(f"""
        QScrollBar:vertical {{
            border: none;
            background: {BG_NAV};
            width: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: #3F4148;
            min-height: 30px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: #5A5D65;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px; 
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            border: none;
            background: {BG_NAV};
            height: 12px;
            margin: 0px;
        }}
        QScrollBar::handle:horizontal {{
            background: #3F4148;
            min-width: 30px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: #5A5D65;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}

        /* --- TOOLTIPS PREMIUM (Minimalistas) --- */
        QToolTip {{
            color: #E2E2E2;
            background-color: #121214; /* Fondo abismal puro */
            border: 1px solid #2A2B31; /* Borde apenas visible, cero naranja */
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: normal;
        }}
    """)

def apply_shadow(widget, radius=20, offset_y=10):
    """Aplica una sombra suave para dar profundidad"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setXOffset(0)
    shadow.setYOffset(offset_y)
    shadow.setColor(QColor(0, 0, 0, 100)) # Sombra negra semitransparente
    widget.setGraphicsEffect(shadow)

class IconButton(QPushButton):
    """Botón de icono vectorial usando QtAwesome"""
    def __init__(self, icon_name, color=ICON_MUTED, hover_color=TEXT_MAIN, size=20, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"QPushButton {{ background-color: transparent; border: none; border-radius: 8px; }} QPushButton:hover {{ background-color: {BG_PANEL_HOVER}; }}")
        # 🚀 USAMOS EL CACHÉ AQUÍ
        self.setIcon(get_cached_icon(icon_name, color, size, as_icon=True))
        self.setIconSize(QSize(size, size))

class ExportMenuItem(QWidget):
    """Una opción premium para el menú de exportación con título y subtítulo"""
    clicked = pyqtSignal(str) # Avisa qué formato se eligió

    def __init__(self, formato, icon_name, title, subtitle, color):
        super().__init__()
        self.formato = formato
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(15)

        # Icono grande
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon(icon_name, color=color).pixmap(24, 24))
        layout.addWidget(icon_lbl)

        # Textos apilados
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 14px; font-weight: bold; background: transparent;")
        text_layout.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;")
        text_layout.addWidget(sub_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

        # Efecto Hover
        self.setStyleSheet(f"""
            ExportMenuItem {{ background-color: transparent; border-radius: 8px; }}
            ExportMenuItem:hover {{ background-color: #2D2E36; }}
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        """Al soltar el clic, emite la señal y deja que el padre cierre el menú"""
        self.clicked.emit(self.formato)
        super().mouseReleaseEvent(event)

class PropertyRow(QWidget):
    def __init__(self, icon_name, tooltip_text, value_dict):
        super().__init__()
        self.inputs = {} 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 🚀 Envolvemos el icono para darle peso visual
        icon_frame = QFrame()
        icon_frame.setFixedSize(28, 28)
        icon_frame.setStyleSheet("background-color: #202126; border-radius: 6px;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=ICON_MUTED).pixmap(14, 14))
        icon_layout.addWidget(icon_label)
        
        self.setToolTip(tooltip_text)
        layout.addWidget(icon_frame)
        
        for key, val in value_dict.items():
            box = QFrame()
            # 🚀 Bordes invisibles que reaccionan al ratón
            box.setStyleSheet(f"""
                QFrame {{ background-color: #18191D; border-radius: 6px; border: 1px solid transparent; }}
                QFrame:hover {{ border: 1px solid #3F4148; }}
            """)
            box_layout = QHBoxLayout(box)
            box_layout.setContentsMargins(8, 4, 8, 4)
            
            if key:
                k_lbl = QLabel(key)
                k_lbl.setStyleSheet(f"color: {ICON_MUTED}; font-size: 10px; font-weight: 800;")
                box_layout.addWidget(k_lbl)
                
            v_lbl = QLineEdit(str(val))
            v_lbl.setStyleSheet(f"background: transparent; border: none; color: {TEXT_MAIN}; font-size: 12px; font-weight: bold;")
            
            self.inputs[key] = v_lbl 
            box_layout.addWidget(v_lbl)
            layout.addWidget(box)

class FontSelectorRow(QWidget):
    """Reemplazo premium del ComboBox para las fuentes"""
    font_changed = pyqtSignal(str)

    def __init__(self, icon_name, tooltip_text, font_list):
        super().__init__()
        self.font_list = font_list
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Icono lateral
        icon_frame = QFrame()
        icon_frame.setFixedSize(28, 28)
        icon_frame.setStyleSheet("background-color: #202126; border-radius: 6px;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=ICON_MUTED).pixmap(14, 14))
        icon_layout.addWidget(icon_label)
        self.setToolTip(tooltip_text)
        layout.addWidget(icon_frame)

        # El "Input" falso que en realidad es un botón
        self.btn_box = QPushButton()
        self.btn_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 🚀 Diseño idéntico a tus otros inputs
        self.btn_box.setStyleSheet(f"""
            QPushButton {{ background-color: #18191D; border-radius: 6px; border: 1px solid transparent; color: {TEXT_MAIN}; font-size: 12px; font-weight: bold; text-align: left; padding: 6px 10px; }}
            QPushButton:hover {{ border: 1px solid #3F4148; }}
        """)
        self.btn_box.setText("Helvetica")
        self.btn_box.clicked.connect(self._show_popup)
        layout.addWidget(self.btn_box)

    def _show_popup(self):
        # 🚀 Calculamos dónde abrir el popup para que caiga justo debajo del botón
        popup = FontPickerPopup(self.btn_box.text(), self.font_list, self.window())
        pos = self.btn_box.mapToGlobal(self.btn_box.rect().bottomLeft())
        # Ajustamos un poco para la sombra del popup
        popup.move(pos.x() - 15, pos.y() - 5) 
        
        popup.font_selected.connect(self._on_font_selected)
        popup.exec()

    def _on_font_selected(self, font_name):
        self.set_font(font_name)
        self.font_changed.emit(font_name)

    def set_font(self, font_name):
        self.btn_box.setText(font_name)
        
    def currentText(self):
        return self.btn_box.text()

class ComboBoxRow(QWidget):
    def __init__(self, icon_name, tooltip_text, items):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(28, 28)
        icon_frame.setStyleSheet("background-color: #202126; border-radius: 6px;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=ICON_MUTED).pixmap(14, 14))
        icon_layout.addWidget(icon_label)
        
        self.setToolTip(tooltip_text)
        layout.addWidget(icon_frame)
        
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{ background-color: #18191D; border-radius: 6px; border: 1px solid transparent; }}
            QFrame:hover {{ border: 1px solid #3F4148; }}
        """)
        box_layout = QHBoxLayout(box)
        box_layout.setContentsMargins(8, 4, 8, 4)
        
        self.combo = QComboBox()
        self.combo.addItems(items)
        self.combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo.setMinimumWidth(50)
        
        self.combo.setStyleSheet(f"""
            QComboBox {{ background: transparent; border: none; color: {TEXT_MAIN}; font-size: 12px; font-weight: bold; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{ background-color: #18191D; color: {TEXT_MAIN}; selection-background-color: {COLOR_ACCENT}; border: 1px solid #2A2B31; }}
        """)
        
        box_layout.addWidget(self.combo)
        layout.addWidget(box)


class SliderRow(QWidget):
    valores_cambiados = pyqtSignal(int)
    
    def __init__(self, icon_name, tooltip_text, value=100):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(28, 28)
        icon_frame.setStyleSheet("background-color: #202126; border-radius: 6px;")
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color=ICON_MUTED).pixmap(14, 14))
        icon_layout.addWidget(icon_label)
        
        self.setToolTip(tooltip_text)
        layout.addWidget(icon_frame)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(int(value))
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{ border: none; background: #18191D; height: 4px; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {COLOR_ACCENT}; border: none; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
            /* 🚀 EL TRUCO: Cambiamos dimensiones reales en vez de usar 'transform' */
            QSlider::handle:horizontal:hover {{ background: #FFFFFF; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }}
        """)
        
        layout.addWidget(self.slider)
        
        self.percentage_display = QLineEdit(f"{int(value)}%")
        self.percentage_display.setFixedWidth(50)
        self.percentage_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_display.setStyleSheet(f"""
            QLineEdit {{ background-color: #18191D; border-radius: 6px; border: 1px solid transparent; color: {TEXT_MAIN}; font-size: 12px; font-weight: bold; padding: 5px; }}
            QLineEdit:hover {{ border: 1px solid #3F4148; }}
        """)
        
        layout.addWidget(self.percentage_display)
        
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.percentage_display.returnPressed.connect(self._on_input_changed)
        
    def _on_slider_changed(self, value):
        self.percentage_display.blockSignals(True)
        self.percentage_display.setText(f"{value}%")
        self.percentage_display.blockSignals(False)
        self.valores_cambiados.emit(value)
        
    def _on_input_changed(self):
        txt = self.percentage_display.text().replace('%', '')
        try:
            value = max(0, min(100, int(txt)))
            self.slider.setValue(value)
            self.percentage_display.setText(f"{value}%")
        except ValueError:
            self.percentage_display.setText(f"{self.slider.value()}%")
            
    def set_value(self, value):
        self.slider.blockSignals(True)
        self.percentage_display.blockSignals(True)
        v = int(value * 100)
        self.slider.setValue(v)
        self.percentage_display.setText(f"{v}%")
        self.percentage_display.blockSignals(False)
        self.slider.blockSignals(False)
        
    def get_value(self):
        return self.slider.value() / 100.0

class LayerNameEditor(QLineEdit):
    """Input inteligente: Muestra '...' si es muy largo, pero al editar muestra el texto completo"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self._is_editing = False
        self.textChanged.connect(self._sync_text)

    def _sync_text(self, text):
        if self._is_editing:
            self._full_text = text

    def focusInEvent(self, event):
        self._is_editing = True
        self.setText(self._full_text)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._is_editing = False
        self._elide_text()
        super().focusOutEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._is_editing:
            self._elide_text()

    def _elide_text(self):
        fm = self.fontMetrics()
        # Recorta con "..." si supera el ancho disponible
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, self.width() - 5)
        self.setText(elided)
        self.setCursorPosition(0)

    def get_real_text(self):
        return self._full_text

class LayerCard(QFrame):
    """Una tarjeta premium estilo Figma (Thumbnail, Badge, Elipsis y Ajuste Perfecto)"""
    nombre_cambiado = pyqtSignal(str, str)     
    oculto_cambiado = pyqtSignal(str, bool)     
    bloqueado_cambiado = pyqtSignal(str, bool)  
    seleccionada = pyqtSignal(str, bool)  # 🚀 CURA: Ahora envía 'True' si presionas Shift/Ctrl

    def __init__(self, uid, elem, motor_mapa_fuentes, motor_ref, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.tipo = elem['tipo']
        self.oculto = elem.get('oculto', False)
        self.bloqueado = elem.get('bloqueado', False)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) 
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 🚀 LA CURA: Añadimos 'parent=self' o '(self)' a absolutamente todo.
        # Ahora nacen encapsulados y Windows no crea ventanas fantasma.
        self.btn_folder = IconButton('fa5s.chevron-right', color=TEXT_MUTED, size=10, parent=self) 
        self.btn_folder.setFixedSize(20, 20)
        self.btn_folder.setVisible(False) 
        self.btn_folder.clicked.connect(self._on_folder_clicked)
        layout.addWidget(self.btn_folder)
        
        grip = QLabel(self) # 🚀 parent=self
        grip.setPixmap(get_cached_icon('fa5s.grip-vertical', '#4A4D57', 14))
        grip.setCursor(Qt.CursorShape.OpenHandCursor)
        grip.setStyleSheet("background: transparent; border: none; padding: 0px;") 
        layout.addWidget(grip)
        
        thumb_frame = QFrame(self) # 🚀 parent=self
        thumb_frame.setFixedSize(36, 36) 
        thumb_frame.setStyleSheet("background-color: #121214; border: 1px solid #2A2B31; border-radius: 6px;")
        
        thumb_layout = QVBoxLayout(thumb_frame)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        thumb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        self.thumb_icon = QLabel(thumb_frame) # 🚀 Su padre es el marco donde vive
        self.thumb_icon.setFixedSize(16, 16) 
        icon_name = 'fa5s.image' if self.tipo == 'Foto' else 'fa5s.font' if self.tipo == 'Texto' else 'fa5s.shapes'
        
        self.thumb_icon.setPixmap(get_cached_icon(icon_name, TEXT_MAIN, 16))
        self.thumb_icon.setScaledContents(True) 
        self.thumb_icon.setStyleSheet("border: none; background: transparent;") 
        thumb_layout.addWidget(self.thumb_icon)
        layout.addWidget(thumb_frame)
        
        mid_layout = QVBoxLayout()
        mid_layout.setSpacing(6) 
        mid_layout.setContentsMargins(0, 0, 0, 8) 
        mid_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        nombre_base = elem.get('nombre') or elem.get('nombre_capa')
        if not nombre_base:
            if self.tipo == 'Texto': nombre_base = str(elem.get('contenido', '')).replace('\n', ' ')
            elif self.tipo == 'Foto': nombre_base = os.path.basename(str(elem.get('contenido', '')))
            else: nombre_base = self.uid.split('_')[0].capitalize()

        self.name_edit = LayerNameEditor(nombre_base, parent=self) # 🚀 parent=self
        self.name_edit.setStyleSheet(f"""
            LayerNameEditor {{ border: none; background: transparent; color: {TEXT_MAIN}; font-size: 13px; font-weight: bold; padding: 0px 4px; selection-background-color: {COLOR_ACCENT}; }}
            LayerNameEditor:focus {{ color: {COLOR_ACCENT}; background-color: #1A1B1E; border-radius: 4px; }}
        """)
        self.name_edit.setMinimumHeight(24) 
        self.name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.name_edit.setMinimumWidth(50)
        mid_layout.addWidget(self.name_edit)
        
        badge_layout = QHBoxLayout()
        badge_layout.setContentsMargins(4, 4, 0, 0) 
        
        badge = QLabel(self) # 🚀 parent=self
        badge.setFixedHeight(18) 
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        badge_base_style = "border-radius: 4px; padding: 0px 6px; font-size: 9px; font-weight: bold;"
        if self.tipo == 'Foto':
            badge.setText("IMAGEN") 
            badge.setStyleSheet(f"background-color: #2D2145; color: #B689FF; {badge_base_style}")
        elif self.tipo == 'Texto':
            badge.setText("TEXTO") 
            badge.setStyleSheet(f"background-color: #1E2D45; color: #66A3FF; {badge_base_style}")
        else:
            badge.setText("FORMA") 
            badge.setStyleSheet(f"background-color: #452D1E; color: #FF9E59; {badge_base_style}")
            
        badge_layout.addWidget(badge)
        badge_layout.addStretch()
        mid_layout.addLayout(badge_layout)
        layout.addLayout(mid_layout, 1)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        btn_style = """
            QPushButton { background: transparent; border: none; border-radius: 4px; padding: 4px; }
            QPushButton:hover { background: #2A2B31; }
        """
        
        self.lock_btn = QPushButton(self) # 🚀 parent=self
        self.lock_btn.setFixedSize(26, 26)
        self.lock_btn.setStyleSheet(btn_style)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        es_hijo = elem.get('parent_marco') is not None
        self.lock_btn.setVisible(not es_hijo)
        
        self.eye_btn = QPushButton(self) # 🚀 parent=self
        self.eye_btn.setFixedSize(26, 26)
        self.eye_btn.setStyleSheet(btn_style)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._update_lock_icon()
        self._update_eye_icon()
        
        actions_layout.addWidget(self.lock_btn)
        actions_layout.addWidget(self.eye_btn)
        layout.addLayout(actions_layout)
        
        self.setObjectName("tarjeta_capa")
        self.setStyleSheet("""
            #tarjeta_capa { background-color: #18191D; border-radius: 8px; border: 1px solid #2A2B31; }
            #tarjeta_capa:hover { background-color: #202126; border: 1px solid #3F4148; }
        """)
        
        self.name_edit.returnPressed.connect(self._on_name_edited)
        self.eye_btn.clicked.connect(self._on_eye_clicked)
        self.lock_btn.clicked.connect(self._on_lock_clicked)

    toggled_folder = pyqtSignal(bool)

    def hacer_carpeta(self, estado):
        self.btn_folder.setVisible(estado)
        if estado: 
            self.thumb_icon.setPixmap(get_cached_icon('fa5s.folder', COLOR_ACCENT, 16))

    def _on_folder_clicked(self):
        esta_abierto = getattr(self, '_folder_open', False)
        self._folder_open = not esta_abierto
        icon = 'fa5s.chevron-down' if self._folder_open else 'fa5s.chevron-right'
        self.btn_folder.setIcon(get_cached_icon(icon, TEXT_MAIN, 10, as_icon=True))
        self.toggled_folder.emit(self._folder_open)

    # 🚀 CURA REFINAMIENTO: Selector sutil (Transparente para hijos, Naranja para Grupos)
    def set_activa(self, activa, sutil=False):
        if getattr(self, '_is_active', None) == activa and getattr(self, '_is_sutil', None) == sutil: return
        self._is_active = activa
        self._is_sutil = sutil
        
        if sutil and activa:
            color_borde = "rgba(254, 89, 52, 0.3)" 
            bg_color = "#202126"
            hover_borde = COLOR_ACCENT
        else:
            color_borde = COLOR_ACCENT if activa else "#2A2B31"
            bg_color = "#202126" if activa else "#18191D"
            hover_borde = COLOR_ACCENT if activa else "#3F4148"
        
        self.setStyleSheet(f"""
            #tarjeta_capa {{ background-color: {bg_color}; border-radius: 8px; border: 1px solid {color_borde}; }}
            #tarjeta_capa:hover {{ background-color: #202126; border: 1px solid {hover_borde}; }}
        """)

    def _update_eye_icon(self):
        icon_name = 'fa5s.eye-slash' if self.oculto else 'fa5s.eye'
        color = COLOR_ACCENT if self.oculto else ICON_MUTED
        self.eye_btn.setIcon(get_cached_icon(icon_name, color, 16, as_icon=True))
        
    def _update_lock_icon(self):
        icon_name = 'fa5s.lock' if self.bloqueado else 'fa5s.lock-open'
        color = COLOR_ACCENT if self.bloqueado else ICON_MUTED
        self.lock_btn.setIcon(get_cached_icon(icon_name, color, 16, as_icon=True))

    def _on_name_edited(self):
        new_name = self.name_edit.get_real_text()
        self.name_edit.clearFocus()
        self.nombre_cambiado.emit(self.uid, new_name)
        
    def _on_eye_clicked(self):
        self.oculto = not self.oculto
        self._update_eye_icon()
        self.oculto_cambiado.emit(self.uid, self.oculto)
        
    def _on_lock_clicked(self):
        self.bloqueado = not self.bloqueado
        self._update_lock_icon()
        self.bloqueado_cambiado.emit(self.uid, self.bloqueado)
        
    def mousePressEvent(self, event):
        # Detectamos si mantienes presionado Shift o Control
        multi = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier) or bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        self.seleccionada.emit(self.uid, multi)
        super().mousePressEvent(event)

class LeftNavPanel(QFrame):
    """Columna 1: Barra de Navegación (Router)"""
    tab_changed = pyqtSignal(int) # 🚀 Señal que avisa al VDOM qué índice mostrar

    def __init__(self):
        super().__init__()
        self.setFixedWidth(80)
        
        # 🚀 EL DIVISOR: Borde derecho ultra sutil
        self.setStyleSheet(f"background: transparent; border-right: 1px solid {BORDER_NAV};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.nav_icons = [
            ('fa5s.folder-open', 'Proyectos'),
            ('fa5s.pencil-ruler', 'Diseño'), 
            ('fa5s.font', 'Texto'),
            ('fa5s.cubes', 'Componentes'),
            ('fa5s.layer-group', 'Capas')
        ]
        
        self.nav_btns = []
        for idx, (icon, text) in enumerate(self.nav_icons):
            btn = IconButton(icon, size=24)
            btn.setFixedSize(50, 50)
            btn.setToolTip(text)
            # Conectamos el clic al enrutador interno
            btn.clicked.connect(lambda checked, i=idx: self.cambiar_pestana(i))
            self.nav_btns.append(btn)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
        layout.addStretch()
        
        # Iconos inferiores
        btn_ajustes = IconButton("fa5s.cogs", size=24)
        btn_ajustes.setToolTip("Ajustes")
        layout.addWidget(btn_ajustes, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn_ayuda = IconButton("fa5s.question-circle", size=24)
        btn_ayuda.setToolTip("Ayuda")
        layout.addWidget(btn_ayuda, alignment=Qt.AlignmentFlag.AlignCenter)
        
        profile_layout = QVBoxLayout()
        profile_layout.setContentsMargins(10, 20, 10, 0)
        
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(40, 40)
        self.avatar_label.setStyleSheet("border-radius: 20px; background-color: #404040; border: 2px solid #FE5934;") 
        profile_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(profile_layout)

    def cambiar_pestana(self, index):
        """VDOM Visual: Ilumina el botón activo y avisa al contenedor principal en 0ms"""
        for i, btn in enumerate(self.nav_btns):
            color = COLOR_ACCENT if i == index else ICON_MUTED
            btn.setIcon(qta.icon(self.nav_icons[i][0], color=color))
        self.tab_changed.emit(index)

class PremiumDropStyle(QProxyStyle):
    """Secuestra el dibujado nativo de Windows/Qt para crear un Drag & Drop estilo Figma"""
    def drawPrimitive(self, element, option, painter, widget=None):
        from PyQt6.QtGui import QPen, QColor, QBrush, QFont
        from PyQt6.QtCore import Qt, QRect
        
        if element == QStyle.PrimitiveElement.PE_IndicatorItemViewItemDrop:
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            rect = option.rect
            color_acento = QColor("#FE5934") 
            
            # 1. ¿LÍNEA? (Soltando ENTRE capas o al inicio)
            if rect.height() <= 2:
                y_pos = rect.top()
                
                if y_pos < 12: 
                    y_pos = 4
                else:
                    y_pos += 1 # La calibración que te quedó perfecta
                
                x_inicio = rect.left() + 4
                
                painter.setPen(QPen(color_acento, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(int(x_inicio + 6), int(y_pos), int(rect.right()), int(y_pos))
                
                painter.setBrush(QBrush(color_acento))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(x_inicio), int(y_pos - 3), 6, 6)
            
            # 2. ¿CAJA INTELIGENTE Y TRANSPARENTE?
            else:
                texto_bolsillo = "AGRUPAR"
                color_bolsillo = QColor("#FE5934") 
                
                if widget:
                    target_item = widget.itemAt(rect.center())
                    if target_item:
                        uid = target_item.data(0, Qt.ItemDataRole.UserRole)
                        main_studio = widget.window()
                        if hasattr(main_studio, 'motor'):
                            elem = main_studio.motor.elementos.get(uid)
                            if elem and elem.get('tipo') == 'Marco': 
                                texto_bolsillo = "METER DENTRO"
                                color_bolsillo = QColor("#66A3FF") 
                
                # Techo oculto bajo la tarjeta y bajamos solo 6px para no tocar la capa inferior
                y_techo = rect.top() + 20 
                y_suelo = rect.bottom() + 6 
                
                caja_bolsillo = QRect(int(rect.left() + 2), int(y_techo), int(rect.width() - 4), int(y_suelo - y_techo))
                
                painter.setPen(QPen(color_bolsillo, 2, Qt.PenStyle.SolidLine))
                color_fondo = QColor(color_bolsillo)
                color_fondo.setAlpha(35) # Transparencia original
                painter.setBrush(QBrush(color_fondo))
                
                painter.drawRoundedRect(caja_bolsillo, 6, 6)
                
                # 🚀 TEXTO DEL MISMO COLOR QUE EL BOLSILLO + FUENTE GILROY
                painter.setPen(QPen(color_bolsillo)) 
                font = QFont("Gilroy")
                font.setPixelSize(10)
                font.setBold(True)
                font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
                painter.setFont(font)
                
                # Centramos el texto exactamente en ese margen inferior transparente
                caja_texto = QRect(int(rect.left()), int(rect.bottom() - 6), int(rect.width()), 12)
                painter.drawText(caja_texto, Qt.AlignmentFlag.AlignCenter, texto_bolsillo)
                
            painter.restore()
            return
            
        super().drawPrimitive(element, option, painter, widget)


class AssetsPanel(QFrame):
    """Panel lateral de capas premium con soporte para Carpetas (Jerarquía)"""
    def __init__(self, motor, mapa_fuentes):
        super().__init__()
        self.motor = motor
        self.mapa_fuentes = mapa_fuentes
        
        # 🚀 LA CURA DE LA LÍNEA CORTADA: Le damos un ID exclusivo (#panel_activos)
        # para que los textos internos no hereden el borde derecho por error.
        self.setObjectName("panel_activos")
        self.setStyleSheet(f"#panel_activos {{ background: transparent; border-right: 1px solid {BORDER_NAV}; }}")
        
        self.setFixedWidth(340)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 🚀 EL VIRTUAL DOM MANAGER
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # --- Índices 0 al 3: Vistas rápidas pre-renderizadas ---
        self.stack.addWidget(self._crear_vista_vacia("Gestor de Archivos", "fa5s.folder-open", "Tus proyectos locales y en la nube"))
        self.stack.addWidget(self._crear_vista_vacia("Recursos de Diseño", "fa5s.pencil-ruler", "Formas, fotos y vectores"))
        self.stack.addWidget(self._crear_vista_vacia("Tipografías", "fa5s.font", "Gestor de estilos globales"))
        self.stack.addWidget(self._crear_vista_vacia("Componentes", "fa5s.cubes", "Librería de símbolos reutilizables"))
        
        # --- Índice 4: EL PANEL DE CAPAS ORIGINAL ---
        vista_capas = QWidget()
        capas_layout = QVBoxLayout(vista_capas)
        # 🚀 Movemos el margen aquí para que el motor de Qt tenga vía libre en la Y=0
        capas_layout.setContentsMargins(15, 0, 15, 15)
        capas_layout.setSpacing(0)
        
        header = QLabel("Capas & Estructura") # Traducido para más limpieza
        header.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 14px; font-weight: bold; padding: 20px;")
        capas_layout.addWidget(header)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setColumnCount(2) 
        self.tree_widget.hideColumn(1)
        self.tree_widget.setIndentation(20) 
        self.tree_widget.setAnimated(True)
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        # 🚀 ACTIVAMOS EL MENÚ CONTEXTUAL (Clic Derecho) EN EL PANEL DE CAPAS
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._mostrar_menu_contextual)
        
        self.tree_widget.setStyleSheet(f"""
            QTreeView, QTreeWidget {{ 
                background: transparent; 
                border: none; 
                outline: none; 
                margin: 0px; 
                show-decoration-selected: 0; 
            }}
            /* 🚀 MARGIN-TOP 8px: Crea un espacio transparente encima de la tarjeta 
               para que la línea naranja de inserción no quede escondida detrás del widget sólido */
            QTreeWidget::item {{ 
                margin-top: 8px; 
                margin-bottom: 8px; 
                background: transparent; 
                border: none; 
                outline: none; 
            }}
            QTreeWidget::item:selected, QTreeWidget::item:hover, QTreeWidget::item:focus {{ 
                background-color: transparent; border: none; outline: none;
            }}
            QTreeWidget::item:drop-target {{ background-color: transparent; border: none; outline: none; }}
            QTreeWidget::branch:selected, QTreeWidget::branch:hover {{ background-color: transparent; }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{ border-image: none; image: url(none); }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings  {{ border-image: none; image: url(none); }}
            
            /* 🚀 LA CURA DE LA LÍNEA GRIS (Fondo del Scrollbar Track) */
            QScrollBar:vertical {{
                border: none;
                background: transparent; /* Hace invisible el carril fantasma */
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #3F4148;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #5A5D65;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        # 🚀 APLICAMOS EL ESTILO SECUESTRADOR PARA EL DRAG & DROP
        self.tree_widget.setStyle(PremiumDropStyle(self.tree_widget.style()))
        
        palette = self.tree_widget.palette()
        palette.setColor(QPalette.ColorRole.Highlight, Qt.GlobalColor.transparent)
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.transparent)
        self.tree_widget.setPalette(palette)

        self.tree_widget.dropEvent = self._manejar_drop_evento
        self.tree_widget.keyPressEvent = self._manejar_teclas_panel
        
        capas_layout.addWidget(self.tree_widget)
        self.stack.addWidget(vista_capas)
        
        self.tarjetas_ui = {}
        self.list_items_ui = {}

    def _crear_vista_vacia(self, titulo, icono, subtitulo):
        """Generador de componentes de UI pre-renderizados"""
        w = QWidget()
        l = QVBoxLayout(w)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(10)
        
        lbl_icon = QLabel()
        lbl_icon.setPixmap(qta.icon(icono, color="#3F4148").pixmap(64, 64))
        
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 16px; font-weight: bold;")
        
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        
        l.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl_tit, alignment=Qt.AlignmentFlag.AlignCenter)
        l.addWidget(lbl_sub, alignment=Qt.AlignmentFlag.AlignCenter)
        return w

    def cargar_capas(self):
        if not self.motor:
            self.tree_widget.clear() 
            self.tarjetas_ui = {}
            self.list_items_ui = {}
            return
            
        scroll_pos = self.tree_widget.verticalScrollBar().value()
        
        # 🚀 QUITAMOS EL SET UPDATES FALSE QUE CRASHEABA LOS GRUPOS NUEVOS
        self.tree_widget.blockSignals(True)
        
        uids_motor = [u for u, e in self.motor.elementos.items() if e.get('tipo') != 'Ignorar']
        
        # 1. ESCUDO ANTI-SEGFAULT (Sincronización de punteros vivos)
        nuevos_items = {}
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            it = iterator.value()
            try:
                uid = it.data(0, Qt.ItemDataRole.UserRole)
                if uid: nuevos_items[uid] = it
            except RuntimeError: pass 
            iterator += 1
        self.list_items_ui = nuevos_items
        
        # 2. VIRTUAL DOM: Matar lo inexistente
        uids_a_borrar = [u for u in self.list_items_ui if u not in uids_motor]
        for uid in uids_a_borrar:
            item = self.list_items_ui.pop(uid)
            self.tarjetas_ui.pop(uid, None)
            try:
                parent = item.parent()
                if parent: parent.removeChild(item)
                else: 
                    idx = self.tree_widget.indexOfTopLevelItem(item)
                    if idx >= 0: self.tree_widget.takeTopLevelItem(idx)
            except RuntimeError: pass
                
        # 3. VIRTUAL DOM: Procesar de arriba abajo
        raices = [uid for uid in uids_motor if not self.motor.elementos[uid].get('parent_marco')]
        for uid in raices:
            self._procesar_nodo_vdom(uid, self.tree_widget)
            
        # 4. Ordenar visualmente
        self.tree_widget.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.tree_widget.setSortingEnabled(False) 
        
        self.tree_widget.blockSignals(False)
        self.tree_widget.verticalScrollBar().setValue(scroll_pos)

    def _procesar_nodo_vdom(self, uid, parent_obj, padre_expandido=True):
        from PyQt6.QtWidgets import QApplication
        
        elem = self.motor.elementos.get(uid)
        if not elem: return

        reubicado = False 

        if uid in self.list_items_ui:
            item = self.list_items_ui[uid]
            padre_actual = item.parent() if item.parent() else item.treeWidget()
            if padre_actual != parent_obj:
                try:
                    self.tree_widget.removeItemWidget(item, 0)
                    if item.parent(): item.parent().removeChild(item)
                    else:
                        idx = self.tree_widget.indexOfTopLevelItem(item)
                        if idx >= 0: self.tree_widget.takeTopLevelItem(idx)
                    
                    if isinstance(parent_obj, QTreeWidget): parent_obj.addTopLevelItem(item)
                    else: parent_obj.addChild(item)
                    reubicado = True 
                except RuntimeError: pass
        else:
            item = QTreeWidgetItem()
            item.setData(0, Qt.ItemDataRole.UserRole, uid)
            if isinstance(parent_obj, QTreeWidget): parent_obj.addTopLevelItem(item)
            else: parent_obj.addChild(item)
            self.list_items_ui[uid] = item
            reubicado = True

        item.setData(1, Qt.ItemDataRole.DisplayRole, int(elem.get('z_index', 0)))
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled
        item.setFlags(flags)

        card = self.tarjetas_ui.get(uid)
        
        # ==========================================
        # 🚀 LA CURA EXTREMA: VIRTUAL DOM PEREZOSO
        # ==========================================
        if padre_expandido:
            # MODO ACTIVO: El nodo es visible. Creamos o actualizamos su Tarjeta UI.
            cxx_vivo = False
            if card and not reubicado:
                try:
                    _ = card.name_edit.text() 
                    if self.tree_widget.itemWidget(item, 0) is None: cxx_vivo = False
                    else: cxx_vivo = True
                except RuntimeError: cxx_vivo = False

            if cxx_vivo:
                nuevo_nombre = elem.get('nombre') or elem.get('nombre_capa') or str(elem.get('contenido', '')).replace('\n', ' ')
                if card.name_edit.text() != nuevo_nombre: card.name_edit.setText(nuevo_nombre)
                if card.oculto != elem.get('oculto', False):
                    card.oculto = elem.get('oculto', False)
                    card._update_eye_icon()
                if card.bloqueado != elem.get('bloqueado', False):
                    card.bloqueado = elem.get('bloqueado', False)
                    card._update_lock_icon()
            else:
                card = LayerCard(uid, elem, self.mapa_fuentes, self.motor, parent=None) 
                item.setSizeHint(0, card.sizeHint())
                self.tree_widget.setItemWidget(item, 0, card)
                self.tarjetas_ui[uid] = card
                
                main_studio = self.window()
                if main_studio and hasattr(main_studio, 'seleccionar_desde_capas'):
                    card.seleccionada.connect(main_studio.seleccionar_desde_capas)
                    card.oculto_cambiado.connect(main_studio._al_cambiar_oculto_capa)
                    card.bloqueado_cambiado.connect(main_studio._al_cambiar_bloqueado_capa)
                    card.nombre_cambiado.connect(main_studio._al_cambiar_nombre_capa)
        else:
            # 🚀 MODO GHOST: La carpeta padre está cerrada. NO CREAMOS LA UI.
            # El procesador descansa. Solo le indicamos a Qt cuánto mediría la tarjeta
            # (aprox 46px) para que la barra de desplazamiento (Scroll) no se rompa.
            item.setSizeHint(0, QSize(200, 46))
            if card:
                # Si existía (porque la carpeta antes estaba abierta), la destruimos
                # para liberar memoria RAM.
                self.tree_widget.removeItemWidget(item, 0)
                card.deleteLater()
                del self.tarjetas_ui[uid]
                card = None

        # ==========================================
        # 🚀 LÓGICA DE CARPETAS Y CARGA EN RÁFAGAS
        # ==========================================
        hijos = [h_uid for h_uid, h_elem in self.motor.elementos.items() if h_elem.get('parent_marco') == uid]
        
        if hijos:
            if card and hasattr(card, 'hacer_carpeta'):
                card.hacer_carpeta(True)
                try: card.toggled_folder.disconnect()
                except: pass
                
                # 🚀 EL BATCH RENDERER: Interceptamos el clic en la carpeta
                def al_alternar(abierto, it=item, hs=hijos):
                    it.setExpanded(abierto)
                    if abierto:
                        # Mostramos el cursor de carga
                        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                        for i, h_uid in enumerate(hs):
                            # Al abrirse, forzamos a sus hijos a crear su interfaz visual
                            self._procesar_nodo_vdom(h_uid, it, padre_expandido=True)
                            
                            # 🚀 MAGIA: Cada 15 capas renderizadas, hacemos una pausa de 0.001s 
                            # para que Qt redibuje la pantalla. ¡Adiós al "Programa no responde"!
                            if i % 15 == 0: QApplication.processEvents()
                            
                        QApplication.restoreOverrideCursor()
                    else:
                        # Si el usuario cierra la carpeta, destruimos las tarjetas hijas para vaciar RAM
                        for h_uid in hs:
                            self._procesar_nodo_vdom(h_uid, it, padre_expandido=False)
                            
                card.toggled_folder.connect(al_alternar)
                
            es_abierta = item.isExpanded()
            for h_uid in hijos:
                # Solo autorizamos la creación de UI en hijos si NOSOTROS estamos visibles y abiertos
                self._procesar_nodo_vdom(h_uid, item, padre_expandido=(padre_expandido and es_abierta))
        else:
            if card and hasattr(card, 'hacer_carpeta'):
                card.hacer_carpeta(False)


    def get_list_items(self):
        items = []
        iterator = QTreeWidgetItemIterator(self.tree_widget)
        while iterator.value():
            items.append(iterator.value())
            iterator += 1
        return items

    def _manejar_drop_evento(self, event):
        # 1. Dejar que PyQt haga el movimiento visual nativo primero
        QTreeWidget.dropEvent(self.tree_widget, event)
        
        # 2. Leer el nuevo orden visual y pasarlo a la 'Matemática' (el motor)
        self._sincronizar_orden_capas()
        
        # 3. Guardar en el historial de deshacer
        main_studio = self.window()
        if main_studio and hasattr(main_studio, 'motor'):
            main_studio.motor.registrar_punto_historial()
            
        # 4. 🚀 LA CLAVE: Forzar la recarga del VDOM usando TU función 'cargar_capas'
        self.cargar_capas() 
        
        # 5. Actualizar el lienzo principal para reflejar el nuevo orden
        if main_studio and hasattr(main_studio, 'main_canvas'):
            main_studio.main_canvas.actualizar_lienzo()
            # 🚀 CORRECCIÓN: Emitimos la señal desde el lienzo activo (canvas_view_actual)
            if main_studio.canvas_view_actual:
                main_studio.canvas_view_actual.lienzo_modificado.emit()

    def _sincronizar_orden_capas(self):
        # Asignaremos z_index: el de más arriba en el panel tendrá el z_index mayor
        total_items = len(self.motor.elementos)
        contador_z = total_items * 10  # Damos un salto de 10 en 10
        
        def procesar_rama(parent_item, parent_uid):
            nonlocal contador_z
            for i in range(parent_item.childCount()):
                item = parent_item.child(i)
                uid = item.data(0, Qt.ItemDataRole.UserRole)
                
                if uid and uid in self.motor.elementos:
                    # Actualizar la matemática pura
                    self.motor.elementos[uid]['z_index'] = contador_z
                    # Si lo soltaste dentro de un grupo/marco, actualizamos su padre
                    self.motor.elementos[uid]['parent_marco'] = parent_uid
                    
                    contador_z -= 10
                    
                    # Si es una carpeta, procesar sus hijos recursivamente
                    procesar_rama(item, uid)
                    
        # Iniciar el recorrido desde la raíz invisible del árbol
        root = self.tree_widget.invisibleRootItem()
        procesar_rama(root, None)

    def _manejar_teclas_panel(self, event):
        
        # 1. Obtenemos el lienzo principal donde está programada toda la magia
        main_studio = self.window()
        if main_studio and hasattr(main_studio, 'canvas_view_actual') and main_studio.canvas_view_actual:
            canvas = main_studio.canvas_view_actual
            is_ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            
            # 2. Definimos las teclas que queremos robar (Borrar, Copiar, Pegar, Cortar, Duplicar)
            atajos_validos = [Qt.Key.Key_Delete, Qt.Key.Key_Backspace]
            if is_ctrl and event.key() in (Qt.Key.Key_C, Qt.Key.Key_V, Qt.Key.Key_X, Qt.Key.Key_D):
                atajos_validos.append(event.key())
            
            if event.key() in atajos_validos or (is_ctrl and event.key() in atajos_validos):
                # 🚀 EL TRUCO: Le disparamos el evento al lienzo y abortamos aquí
                canvas.keyPressEvent(event)
                return 
                
        # 3. Si es una flecha de navegación o un clic, dejamos que el panel actúe normal
        QTreeWidget.keyPressEvent(self.tree_widget, event)

    def _mostrar_menu_contextual(self, pos):
        """Menú premium al hacer clic derecho en una capa del panel"""
        
        item = self.tree_widget.itemAt(pos)
        if not item: return
        
        uid = item.data(0, Qt.ItemDataRole.UserRole)
        if not uid: return
        
        # 1. Si la capa no estaba seleccionada, la seleccionamos al hacer clic derecho
        if not item.isSelected():
            self.tree_widget.clearSelection()
            item.setSelected(True)
            main_studio = self.window()
            if main_studio and hasattr(main_studio, 'seleccionar_desde_capas'):
                main_studio.seleccionar_desde_capas(uid, multi=False)
                
        # 2. Creamos el Menú Flotante
        menu = QMenu(self.tree_widget)
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 🚀 MISMO CSS PREMIUM QUE EL LIENZO
        menu.setStyleSheet("""
            QMenu { background-color: #18191D; border: 1px solid #2A2B31; border-radius: 8px; padding: 6px 0px; }
            QMenu::item { color: #D1D1D5; padding: 6px 40px 6px 35px; margin: 1px 6px; border-radius: 4px; font-family: 'Gilroy'; font-weight: 500; font-size: 13px; }
            QMenu::item:selected { background-color: #2D2E36; color: #FFFFFF; }
            QMenu::icon { padding-left: 12px; }
            QMenu::separator { height: 1px; background: #2A2B31; margin: 4px 12px; }
        """)
        
        icon_color = "#85868A"
        
        # 3. Opciones de Ordenamiento
        accion_subir = menu.addAction(qta.icon('fa5s.angle-up', color=icon_color), "Traer hacia adelante")
        accion_bajar = menu.addAction(qta.icon('fa5s.angle-down', color=icon_color), "Enviar hacia atrás")
        accion_frente = menu.addAction(qta.icon('fa5s.angle-double-up', color=icon_color), "Traer al frente")
        accion_fondo = menu.addAction(qta.icon('fa5s.angle-double-down', color=icon_color), "Enviar al fondo")
        
        menu.addSeparator()
        
        # 4. Opción extra destructiva (roja)
        accion_eliminar = menu.addAction(qta.icon('fa5s.trash', color="#FF5C5C"), "Eliminar capa")
        
        # Ejecutamos el menú exactamente en la posición del ratón
        accion = menu.exec(self.tree_widget.viewport().mapToGlobal(pos))
        
        # 5. Conectamos las acciones al motor matemático
        if accion:
            main_studio = self.window()
            if main_studio and hasattr(main_studio, 'motor'):
                main_studio.motor.registrar_punto_historial()
                
                if accion == accion_subir: main_studio.motor.subir_capa(uid)
                elif accion == accion_bajar: main_studio.motor.bajar_capa(uid)
                elif accion == accion_frente: main_studio.motor.traer_al_frente(uid)
                elif accion == accion_fondo: main_studio.motor.enviar_al_fondo(uid)
                elif accion == accion_eliminar: 
                    main_studio.motor.eliminar_elemento(uid)
                    if main_studio.canvas_view_actual:
                        main_studio.canvas_view_actual.uids_seleccionados = []
                        main_studio.canvas_view_actual.uid_activo = None
                        # 🚀 LA CURA DEL BUG: Llamamos a la señal desde el lienzo
                        main_studio.canvas_view_actual.elemento_seleccionado.emit("")
                
                # Refrescamos todo el programa para que los cambios se vean al instante
                main_studio.actualizar_lienzo()
                main_studio._refrescar_panel_capas()
                if main_studio.canvas_view_actual:
                    main_studio.canvas_view_actual.lienzo_modificado.emit()

class PremiumTextItem(QGraphicsPathItem):
    """SISTEMA IMPECABLE: Renderizado Vectorial Absoluto con Hitbox Optimizado."""
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self._text = text
        self._font = QFont()
        self.setPen(QPen(Qt.PenStyle.NoPen)) 
        self._update_path()

    def setFont(self, font):
        self._font = font
        self._update_path()
        
    def text(self):
        return self._text

    def _update_path(self):
        from PyQt6.QtGui import QPainterPath, QFontMetricsF
        path = QPainterPath()
        if self._text:
            metrics = QFontMetricsF(self._font)
            path.addText(0, metrics.ascent(), self._font, self._text)
        self.setPath(path)
        
        # 🚀 LA CURA MATEMÁTICA: HITBOX RECTANGULAR
        # Extraemos la caja límite y creamos un rectángulo simple.
        self._cached_rect = path.boundingRect().adjusted(-2, -2, 2, 2)
        
        self._cached_shape = QPainterPath()
        self._cached_shape.addRect(self._cached_rect)

    def shape(self):
        # 🚀 Al devolver un rectángulo en lugar de las letras, 
        # Qt calcula colisiones 10,000 veces más rápido al pasar el ratón.
        if hasattr(self, '_cached_shape') and self._cached_shape: 
            return self._cached_shape
        return super().shape()

    def boundingRect(self):
        if hasattr(self, '_cached_rect') and self._cached_rect: 
            return self._cached_rect
        return super().boundingRect()


class PremiumStrokeItem(QGraphicsPathItem):
    """Optimización Extrema para Vectores: Cacheo de Geometría y Hitbox Rectangular."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cached_rect = None
        self._cached_shape = None

    def setPath(self, path):
        super().setPath(path)
        
        # 🚀 LA CURA MATEMÁTICA: HITBOX RECTANGULAR PARA LA PLUMA
        self._cached_rect = path.boundingRect().adjusted(-2, -2, 2, 2)
        
        # En lugar de guardar el "path" original con miles de curvas complejas
        # como nuestra área de choque, creamos un rectángulo básico.
        self._cached_shape = QPainterPath()
        self._cached_shape.addRect(self._cached_rect)
        
    def boundingRect(self):
        if self._cached_rect is not None: return self._cached_rect
        return super().boundingRect()

    def shape(self):
        # 🚀 Magia de Rendimiento: Cuando Qt pregunte "¿Qué forma tiene esto?", 
        # le devolvemos un rectángulo. El procesador ni se entera.
        if self._cached_shape is not None: return self._cached_shape
        return super().shape()

class PerformanceMonitor(QLabel):
    """Overlay tipo Game Engine para medir FPS y RAM en vivo"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # 🚀 Tamaño fijo para que el texto siempre sea visible
        self.setFixedSize(220, 30) 
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            background-color: rgba(18, 18, 20, 220); 
            color: #00FF00; 
            font-family: 'Consolas', monospace; 
            font-size: 11px; 
            font-weight: bold; 
            border-radius: 6px; 
            border: 1px solid #2A2B31;
        """)
        self.frames = 0
        self.last_time = time.perf_counter()
        self.setText("🖥️ Iniciando Motor...")
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000) # Actualizamos cada 1 segundo para mayor estabilidad

    def tick(self):
        self.frames += 1

    def update_stats(self):
        now = time.perf_counter()
        dt = now - self.last_time
        fps = self.frames / dt if dt > 0 else 0
        try:
            process = psutil.Process(os.getpid())
            ram_mb = process.memory_info().rss / (1024 * 1024)
            ram_str = f"{ram_mb:.1f} MB"
        except: ram_str = "-- MB"
        
        # Color dinámico: Verde (Pro), Naranja (Alerta), Rojo (Lag)
        color = "#00FF00" if fps > 50 else "#FFB84D" if fps > 25 else "#FF5C5C"
        self.setStyleSheet(f"background-color: rgba(18, 18, 20, 220); color: {color}; border-radius: 6px; border: 1px solid #2A2B31; font-family: 'Consolas'; font-weight: bold;")
        self.setText(f"🖥️ FPS: {int(fps)} | 💾 RAM: {ram_str}")
        self.frames = 0
        self.last_time = now

class InteractiveCanvasView(QGraphicsView):
    elemento_seleccionado = pyqtSignal(str)
    lienzo_modificado = pyqtSignal()

    def __init__(self, scene, motor, parent_panel, mapa_fuentes):
        super().__init__(scene)
        self.motor = motor
        self.parent_panel = parent_panel
        self.mapa_fuentes = mapa_fuentes
        self.zoom = 1.0
        
        self.uids_seleccionados = [] 
        self.uid_activo = None       
        self.modo_accion = None
        self.handle_activo = None 
        self.start_pdf_x = 0
        self.start_pdf_y = 0
        self.start_cajas = {} 

        # 🚀 1. LÍMITES MATEMÁTICOS DE ESCENA
        self.scene().setSceneRect(-2000, -2000, self.motor.w_pdf + 4000, self.motor.h_pdf + 4000)

        # 🚀 2. BANDERAS RASTER DE MÁXIMO RENDIMIENTO (D3D11 Vía Bootloader)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # ⚡ EL SECRETO DE LOS 60 FPS: BoundingRectViewportUpdate
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        
        # ⚡ MEMORIA Y CACHÉ
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        # ❌ (Línea de IndirectPainting eliminada, Qt6 ya lo hace por defecto)

        # 🚀 3. INTERACCIÓN Y CÁMARA
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        # 🚀 Colisión por caja matemática, evita recalcular 50,000 curvas de Bézier al arrastrar
        self.setRubberBandSelectionMode(Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.viewport().setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        
        self.setStyleSheet(f"""
            background-color: {BG_CANVAS_BODY}; 
            border: none; 
            border-bottom-left-radius: 10px; 
            border-bottom-right-radius: 10px; 
            border-top-right-radius: 10px;   
            border-top-left-radius: 0px; 
        """)
        self.setMouseTracking(True) 

        self.items_ui = {}       
        self.cache_pixmaps = {}  
        
        # 🚀 4. DIBUJO DE LA HOJA
        self.hoja_fondo = QGraphicsRectItem(0, 0, self.motor.w_pdf, self.motor.h_pdf)
        self.hoja_fondo.setBrush(QBrush(QColor("#FFFFFF")))
        self.hoja_fondo.setPen(QPen(Qt.PenStyle.NoPen))
        self.hoja_fondo.setZValue(-999999) # Fondo absoluto
        self.scene().addItem(self.hoja_fondo)

        self.tecla_s_presionada = False
        self.tecla_a_presionada = False
        self.grosor_pluma_actual = 3.0

        # 🚀 5. MONITOR DE RENDIMIENTO
        self.perf_monitor = PerformanceMonitor(self)
        self.perf_monitor.show()

    def set_tool(self, tool_id):
        """Cambia el comportamiento del ratón según la herramienta activa"""
        self.herramienta_activa = tool_id
        
        # 🚀 LA MAGIA ABSOLUTA: Desactivamos la interactividad para Mano y Gotero.
        self.setInteractive(tool_id not in ["hand", "eyedropper"])
        
        # =======================================================
        # 🚀 RESTRICCIÓN 3D / PERSPECTIVA: Embudo de Selección Única
        # =======================================================
        if tool_id in ["3d", "perspective"] and len(self.uids_seleccionados) > 1:
            self.uid_activo = self.uids_seleccionados[0]
            self.uids_seleccionados = [self.uid_activo]
            self.dibujar_controles_seleccion()
            QTimer.singleShot(0, lambda: self.elemento_seleccionado.emit(self.uid_activo))
        # =======================================================

        # 🚀 LA CURA DEL CURSOR FANTASMA: Quitamos la mano de todos los objetos si tienes la pluma
        cursor_obj = Qt.CursorShape.CrossCursor if tool_id in ['pen', 'node_edit', '3d', 'perspective'] else Qt.CursorShape.OpenHandCursor
        for item in self.items_ui.values():
            item.setCursor(cursor_obj)

        if tool_id == "hand":
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif tool_id == "eyedropper": 
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            try:
                pixmap_cursor = qta.icon('fa5s.eye-dropper', color="#FFFFFF").pixmap(20, 20)
                self.viewport().setCursor(QCursor(pixmap_cursor, 0, 19))
            except:
                self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        elif tool_id == "text":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        elif tool_id == "pen":
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        elif tool_id == "3d": 
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        elif tool_id == "perspective": 
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        else: # "select"
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            
        if hasattr(self, 'uid_activo') and self.uid_activo:
            self.dibujar_controles_seleccion()

    # ==========================================
    # 🚀 MOTOR MATEMÁTICO: CASCADA DE DEFORMACIONES
    # ==========================================
    def _obtener_opacidad_acumulada(self, uid):
        """Multiplica la opacidad del elemento por la de todos sus grupos padres"""
        opacidad = 1.0
        actual = uid
        while actual and actual in self.motor.elementos:
            elem = self.motor.elementos[actual]
            opacidad *= float(elem.get('opacidad', 1.0))
            actual = elem.get('parent_marco')
        return opacidad

    def _obtener_matriz_acumulada(self, uid):
        """Calcula la deformación visual total heredando de forma perfecta.
           Mapeo absoluto de vértices para evitar estiramientos y desfases."""
        from PyQt6.QtGui import QTransform, QPolygonF
        from PyQt6.QtCore import QPointF, Qt
        
        def deformacion_local(nodo_uid, is_base=False):
            elem = self.motor.elementos.get(nodo_uid)
            if not elem: return QTransform()
            
            caja = self.motor.obtener_caja_elemento(nodo_uid)
            w_real = float(caja.get('w') or 0.0)
            h_real = float(caja.get('h') or 0.0)
            
            t = QTransform()
            
            # 1. ESCALADO (Ajustar al tamaño real de la caja)
            if is_base:
                tipo = elem.get('tipo')
                # 🚀 LA CURA DEL GIGANTISMO: Si no se define, no lo escalamos por defecto
                pw, ph = w_real, h_real 
                
                if tipo == 'Foto':
                    item = self.items_ui.get(nodo_uid)
                    if item and item.data(998): pw, ph = item.data(998)
                elif tipo == 'Texto':
                    pw, ph = float(elem.get('_qt_w', w_real)), float(elem.get('_qt_h', h_real))
                elif tipo == 'Trazo':
                    # Buscamos el tamaño con el que nació el dibujo
                    pw, ph = float(elem.get('base_w', w_real)), float(elem.get('base_h', h_real))
                
                scale_x = w_real / pw if pw > 0 else 1.0
                scale_y = h_real / ph if ph > 0 else 1.0
                t.scale(scale_x, scale_y)
                
            # 2. ROTACIONES 3D
            t_3d = QTransform()
            rot_3dx = float(elem.get('rot_3d_x', 0.0))
            rot_3dy = float(elem.get('rot_3d_y', 0.0))
            if rot_3dx != 0.0: t_3d.rotate(rot_3dx, Qt.Axis.XAxis)
            if rot_3dy != 0.0: t_3d.rotate(rot_3dy, Qt.Axis.YAxis)
            
            t = t * t_3d
            
            # 3. OBTENER LOS LÍMITES EXACTOS POST-3D
            hw, hh = w_real / 2.0, h_real / 2.0
            pts_3d = [t_3d.map(QPointF(-hw, -hh)), t_3d.map(QPointF(hw, -hh)), 
                      t_3d.map(QPointF(hw, hh)), t_3d.map(QPointF(-hw, hh))]
            
            min_x = min(p.x() for p in pts_3d)
            max_x = max(p.x() for p in pts_3d)
            min_y = min(p.y() for p in pts_3d)
            max_y = max(p.y() for p in pts_3d)

            # 4. PERSPECTIVA (Usando los vértices reales de la malla 3D)
            persp = elem.get('perspectiva')
            if persp and any(pt != [0,0] for pt in persp):
                poly_src = QPolygonF([
                    QPointF(min_x, min_y), QPointF(max_x, min_y), 
                    QPointF(max_x, max_y), QPointF(min_x, max_y)
                ])
                poly_dst = QPolygonF([
                    QPointF(min_x + persp[0][0], min_y + persp[0][1]),
                    QPointF(max_x + persp[1][0], min_y + persp[1][1]),
                    QPointF(max_x + persp[2][0], max_y + persp[2][1]),
                    QPointF(min_x + persp[3][0], max_y + persp[3][1])
                ])
                trans_p = QTransform()
                if QTransform.quadToQuad(poly_src, poly_dst, trans_p):
                    t = t * trans_p
                    
            # 5. ROTACIÓN 2D
            t_rot = QTransform()
            rot = float(elem.get('rotacion', 0.0))
            t_rot.rotate(-rot)
            
            t = t * t_rot
            return t

        # --- FASE DE ACUMULACIÓN ---
        caja_base = self.motor.obtener_caja_elemento(uid)
        if not caja_base: return QTransform()
        
        cx_base = float(caja_base.get('x') or 0.0) + (float(caja_base.get('w') or 0.0) / 2.0)
        cy_base = self.motor.h_pdf - (float(caja_base.get('y') or 0.0) + (float(caja_base.get('h') or 0.0) / 2.0))

        t_final = deformacion_local(uid, is_base=True)
        t_final = t_final * QTransform().translate(cx_base, cy_base)
        
        padre_uid = self.motor.elementos.get(uid, {}).get('parent_marco')
        while padre_uid and padre_uid in self.motor.elementos:
            caja_p = self.motor.obtener_caja_elemento(padre_uid)
            if not caja_p: break
            cx_p = float(caja_p.get('x') or 0.0) + (float(caja_p.get('w') or 0.0) / 2.0)
            cy_p = self.motor.h_pdf - (float(caja_p.get('y') or 0.0) + (float(caja_p.get('h') or 0.0) / 2.0))
            
            t_padre = deformacion_local(padre_uid, is_base=False)
            
            t_final = t_final * QTransform().translate(-cx_p, -cy_p)
            t_final = t_final * t_padre
            t_final = t_final * QTransform().translate(cx_p, cy_p)
            
            padre_uid = self.motor.elementos.get(padre_uid, {}).get('parent_marco')

        return t_final

    def sincronizar_con_motor(self, uids_especificos=None):
        # 🚀 1. VIRTUAL DOM DEL LIENZO: Solo escaneamos todo si no nos dan una lista específica
        if uids_especificos is None:
            uids_a_borrar = [uid for uid in self.items_ui if uid not in self.motor.elementos]
            for uid in uids_a_borrar:
                item_fantasma = self.items_ui.pop(uid)
                self.scene().removeItem(item_fantasma)

            self.hoja_fondo.setRect(0, 0, self.motor.w_pdf, self.motor.h_pdf)
            self.setSceneRect(-500, -500, self.motor.w_pdf + 1000, self.motor.h_pdf + 1000)
            lista_iterar = self.motor.elementos.keys()
        else:
            # Sincronización Láser: Ignoramos el 99% del proyecto, solo tocamos lo que se mueve
            lista_iterar = uids_especificos

        for uid in lista_iterar:
            elem = self.motor.elementos.get(uid)
            if not elem: continue

            if elem.get('oculto', False) or elem.get('tipo') == 'Ignorar':
                if uid in self.items_ui: self.items_ui[uid].setVisible(False)
                continue

            tipo = elem['tipo']
            
            if tipo == 'Texto':
                fuente_motor = elem.get('fuente', 'Helvetica')
                fuente_qt_name = self.mapa_fuentes.get(fuente_motor, fuente_motor)
                fuente_qt = QFont(fuente_qt_name)
                
                font_size = float(elem.get('w', 36))
                fuente_qt.setPixelSize(int(font_size))
                
                lineas = str(elem.get('contenido', '')).split('\n')
                interlineado = font_size * float(elem.get('interlineado', 1.2))
                
                metrics = QFontMetricsF(fuente_qt)
                
                max_w_visual = 0.1
                for l in lineas:
                    br_w = metrics.boundingRect(l).width()
                    adv_w = metrics.horizontalAdvance(l)
                    
                    # 🚀 MATEMÁTICA PURA: Usamos exactamente el tamaño máximo de la tinta.
                    # El rastro ya está protegido por el escudo de la GPU, así que la caja
                    # vuelve a estar perfectamente centrada sin márgenes deformes.
                    ancho_max_seguro = max(br_w, adv_w)
                    
                    if ancho_max_seguro > max_w_visual:
                        max_w_visual = ancho_max_seguro
                        
                elem['_qt_w'] = float(max_w_visual)
                elem['_qt_h'] = float(metrics.height() + (interlineado * (len(lineas) - 1)))
                elem['_qt_ascent'] = float(metrics.ascent())
                
                # Mantenemos las matemáticas internas intactas para que la alineación (Justificado/Centro) no se rompa
                elem['_qt_margenes'] = [float(metrics.boundingRect(l).left()) for l in lineas]
                elem['_qt_advances'] = [float(metrics.horizontalAdvance(l)) for l in lineas]

            # =========================================================
            # 🚀 2. OPTIMIZACIÓN EXTREMA DE RAM: CACHÉ JERÁRQUICO
            # =========================================================
            def get_hierarchical_hash(nodo_uid):
                h_data = []
                curr = nodo_uid
                # Leemos los datos del objeto y de todos sus abuelos hacia arriba
                while curr and curr in self.motor.elementos:
                    e_curr = self.motor.elementos[curr]
                    persp = e_curr.get('perspectiva', [[0,0],[0,0],[0,0],[0,0]])
                    p_hash = tuple(tuple(round(v, 2) for v in pt) for pt in persp)
                    
                    # Usamos float() por seguridad contra variables vacías o strings
                    h_data.append((
                        round(float(e_curr.get('x', 0.0)), 2), round(float(e_curr.get('y', 0.0)), 2), 
                        round(float(e_curr.get('w', 0.0)), 2), round(float(e_curr.get('h', 0.0)), 2), 
                        round(float(e_curr.get('rotacion', 0.0)), 2), round(float(e_curr.get('opacidad', 1.0)), 2), 
                        e_curr.get('z_index', 0), e_curr.get('fuente', ''),
                        round(float(e_curr.get('stretch_x', 1.0)), 4), round(float(e_curr.get('stretch_y', 1.0)), 4),
                        round(float(e_curr.get('rot_3d_x', 0.0)), 2), round(float(e_curr.get('rot_3d_y', 0.0)), 2),
                        p_hash
                    ))
                    curr = e_curr.get('parent_marco')
                return tuple(h_data)

            # El ADN final del caché ahora incluye si alguien de su familia se movió
            fast_hash = get_hierarchical_hash(uid)
            color_hash = (elem.get('color_tx', ''), elem.get('contenido', ''))
            # =========================================================

            # 🚀 HÍBRIDO RE-RENDER
            if uid in self.items_ui and elem['tipo'] == 'Foto' and str(elem.get('contenido', '')).lower().endswith('.svg'):
                if self.items_ui[uid].data(997) != color_hash:
                    viejo_item = self.items_ui.pop(uid)
                    self.scene().removeItem(viejo_item)

            if uid not in self.items_ui:
                self._crear_item_qt(uid, elem)
                self.items_ui[uid].setData(997, color_hash)

            item = self.items_ui[uid]
            item.setVisible(True)
            tipo = elem['tipo']

            if item.data(999) == fast_hash and item.data(997) == color_hash:
                continue 

            item.setData(999, fast_hash)

            # --- MATEMÁTICA PURA (ZERO-ORIGIN) ---
            caja = self.motor.obtener_caja_elemento(uid)
            if not caja: caja = elem # Fallback de seguridad
            
            # 🚀 ESCUDO MATEMÁTICO: El "or 0.0" evita que el programa colapse si una medida es None
            w_real = float(caja.get('w') or 0.0)
            h_real = float(caja.get('h') or 0.0)
            
            cx_pdf = float(caja.get('x') or 0.0) + (w_real / 2.0)
            cy_pdf = float(caja.get('y') or 0.0) + (h_real / 2.0)
            cy_qt = self.motor.h_pdf - cy_pdf
            
            # 🚀 LA CURA DEL "AUTO-SHEAR": Anulamos las variables sueltas de Qt
            # para que no multiplique la rotación y la escala en el orden incorrecto.
            item.setPos(0, 0)
            item.setRotation(0)
            item.setTransformOriginPoint(0, 0)
            item.setZValue(elem.get('z_index', 0))
            
            if tipo == 'Foto':
                ruta = str(elem.get('contenido', ''))
                if isinstance(item, QGraphicsPixmapItem):
                    pw_ph = item.data(998)
                    pw, ph = pw_ph if pw_ph else (100.0, 100.0)
                    item.setOffset(-pw / 2.0, -ph / 2.0)
                    
                    # 🚀 APLICACIÓN MATEMÁTICA JERÁRQUICA
                    item.setTransform(self._obtener_matriz_acumulada(uid))
                    item.setOpacity(self._obtener_opacidad_acumulada(uid))

            elif tipo == 'Texto' and isinstance(item, QGraphicsItemGroup):
                content_hash = (elem.get('contenido'), elem.get('w'), elem.get('fuente'), elem.get('color_tx'), elem.get('align'), elem.get('borde_color'), elem.get('borde_grosor'))
                if item.data(995) != content_hash:
                    item.resetTransform()
                    item.setData(995, content_hash)
                    for child in item.childItems():
                        item.removeFromGroup(child)
                        self.scene().removeItem(child)
                    
                    fuente_qt_name = self.mapa_fuentes.get(elem.get('fuente', 'Helvetica'), 'Helvetica')
                    fuente_qt = QFont(fuente_qt_name)
                    font_size = float(elem.get('w', 36))
                    fuente_qt.setPixelSize(int(font_size))
                    brush = QBrush(QColor(elem.get('color_tx', '#000000')))
                    
                    lineas = str(elem.get('contenido', '')).split('\n')
                    align = elem.get('align', 'Centrado')
                    interlineado = font_size * float(elem.get('interlineado', 1.2))
                    ancho_max_qt, alto_qt_total = elem['_qt_w'], elem['_qt_h']
                    margenes, advances = elem['_qt_margenes'], elem['_qt_advances']
                    
                    offset_x, offset_y = -ancho_max_qt / 2.0, -alto_qt_total / 2.0
                    y_cursor = offset_y
                    
                    for i, linea in enumerate(lineas):
                        ancho_linea, margen_izq = advances[i], margenes[i]
                        palabras = linea.split()
                        
                        if align == "Justificado" and i < len(lineas) - 1 and len(palabras) > 1:
                            ancho_palabras = sum([QFontMetricsF(fuente_qt).horizontalAdvance(p) for p in palabras])
                            gap = (ancho_max_qt - ancho_palabras) / (len(palabras) - 1)
                            cursor_x = 0.0 - (margen_izq / 2.0)
                            for p in palabras:
                                text_word = PremiumTextItem(p) 
                                text_word.setFont(fuente_qt); text_word.setBrush(brush); text_word.setData(100, uid)
                                b_color, b_grosor = elem.get('borde_color'), float(elem.get('borde_grosor', 0))
                                if b_color and b_grosor > 0: text_word.setPen(QPen(QColor(b_color), b_grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                                text_word.setPos(cursor_x + offset_x, y_cursor)
                                item.addToGroup(text_word)
                                cursor_x += QFontMetricsF(fuente_qt).horizontalAdvance(p) + gap
                            y_cursor += interlineado
                            continue

                        if align == "Izquierda" or align == "Justificado": start_x = 0.0 - (margen_izq / 2.0)
                        elif align == "Centrado": start_x = (ancho_max_qt / 2.0) - (ancho_linea / 2.0)
                        else: start_x = ancho_max_qt - ancho_linea + (margen_izq / 2.0)
                        
                        text_line = PremiumTextItem(linea)
                        text_line.setFont(fuente_qt); text_line.setBrush(brush); text_line.setData(100, uid)
                        b_color, b_grosor = elem.get('borde_color'), float(elem.get('borde_grosor', 0))
                        if b_color and b_grosor > 0: text_line.setPen(QPen(QColor(b_color), b_grosor, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                        text_line.setPos(start_x + offset_x, y_cursor)
                        item.addToGroup(text_line)
                        y_cursor += interlineado
                
                # 🚀 APLICACIÓN MATEMÁTICA JERÁRQUICA
                item.setTransform(self._obtener_matriz_acumulada(uid))
                item.setOpacity(self._obtener_opacidad_acumulada(uid))

            elif tipo == 'Trazo':
                if uid not in self.items_ui:
                    # 🚀 APLICAMOS NUESTRO VECTOR OPTIMIZADO
                    item = PremiumStrokeItem() # <--- ¡CAMBIADO AQUÍ!
                    item.setData(100, uid)
                    self.scene().addItem(item)
                    self.items_ui[uid] = item
                else:
                    item = self.items_ui[uid]
                    
                # ==========================================
                # 🚀 PROCESAMIENTO DEL TRAZO (Tinta Sólida)
                # ==========================================
                puntos_relativos = elem.get('puntos', [])
                pts_relativos_qt = []
                
                for p_rel in puntos_relativos:
                    g_pt = p_rel[2] if len(p_rel) > 2 else float(elem.get('borde_grosor', 3.0))
                    pts_relativos_qt.append((QPointF(p_rel[0], -p_rel[1]), g_pt))
                    
                # 2. Generamos la curva suave
                path_suave = self._generar_patron_variable(pts_relativos_qt)
                
                # 🚀 LA CURA DE LAS PUNTAS TRANSPARENTES: Fusión Vectorial al Final
                # Al soltar el ratón y generar el objeto final, sí aplicamos .simplified() 
                # (la función booleana que borramos antes) para fundir los círculos de tapa.
                # Como solo se hace una vez al soltar, no causará lag al mover.
                path_suave = path_suave.simplified() # 🚀 RESTAURADO AL SOLTAR
                
                item.setPath(path_suave) # Le damos la miniatura
                
                # 🚀 LA CURA DEL CACHÉ DE HARDWARE
                # Al quitar el Lápiz Cosmético, le devolvemos a Qt el permiso 
                # de guardar este vector en la VRAM de tu tarjeta gráfica.
                color_borde = elem.get('borde_color', '#000000')
                item.setPen(QPen(Qt.PenStyle.NoPen))
                item.setBrush(QBrush(QColor(color_borde)))
                
                # 4. Y en lugar de deformar el vector, usamos la matriz para MOVER EL ÍTEM COMPLETO
                t_final = self._obtener_matriz_acumulada(uid)
                item.setTransform(t_final) 
                item.setOpacity(self._obtener_opacidad_acumulada(uid))
                
            elif tipo in ['Forma', 'Marco'] and isinstance(item, QGraphicsPathItem):
                forma, radio = elem.get('forma', 'Rectángulo'), elem.get('radio_esquinas', 0.0)
                path = QPainterPath()
                
                # 🚀 LA CURA DE LA DEFORMACIÓN DEL MARCO:
                # El Marco no debe dibujar color si no tiene uno definido explícitamente (es invisible)
                w_real = float(caja.get('w') or 0.0) if caja else float(elem.get('w', 0.0))
                h_real = float(caja.get('h') or 0.0) if caja else float(elem.get('h', 0.0))
                
                ox, oy = -w_real / 2.0, -h_real / 2.0
                
                if forma in ['Elipse', 'Circular']: path.addEllipse(ox, oy, w_real, h_real)
                elif radio > 0: path.addRoundedRect(ox, oy, w_real, h_real, radio, radio)
                else: path.addRect(ox, oy, w_real, h_real)
                
                item.setPath(path)
                color_relleno, color_borde, grosor = elem.get('color_tx'), elem.get('borde_color'), elem.get('borde_grosor', 0)
                item.setBrush(QBrush(QColor(color_relleno)) if color_relleno else QBrush(Qt.BrushStyle.NoBrush))
                item.setPen(QPen(QColor(color_borde), grosor) if grosor > 0 and color_borde else QPen(Qt.PenStyle.NoPen))
                
                # 🚀 APLICACIÓN MATEMÁTICA JERÁRQUICA
                item.setTransform(self._obtener_matriz_acumulada(uid))
                item.setOpacity(self._obtener_opacidad_acumulada(uid))

    def _crear_item_qt(self, uid, elem):
        tipo = elem['tipo']
        import os 
        
        if tipo == 'Foto':
            ruta = str(elem.get('contenido', ''))
            
            if ruta.lower().endswith('.svg'):
                # 🚀 EL ESCUDO DE DUPLICACIÓN: Caché estricto de SVG
                color_hex = elem.get('color_tx', '')
                cache_key = f"svg_{ruta}_{color_hex}" # DNI único del archivo
                
                # Si ya procesamos este SVG, lo sacamos de la memoria RAM en 0.0001 segundos
                if cache_key in self.cache_pixmaps and not self.cache_pixmaps[cache_key].isNull():
                    pixmap = self.cache_pixmaps[cache_key]
                    pw = pixmap.width()
                    ph = pixmap.height()
                    
                    item = QGraphicsPixmapItem(pixmap)
                    item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                    item.setData(998, (float(pw), float(ph)))
                    
                # Si es la primera vez, hacemos el trabajo pesado y lo guardamos
                else:
                    from PyQt6.QtSvg import QSvgRenderer
                    from PyQt6.QtCore import QByteArray
                    import re
                    
                    try:
                        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                            svg_data = f.read()
                            
                        # 🎨 COLORIZACIÓN EN TIEMPO REAL
                        if color_hex:
                            svg_data = re.sub(r'fill\s*=\s*["\'][^"\']*["\']', f'fill="{color_hex}"', svg_data, flags=re.IGNORECASE)
                            svg_data = re.sub(r'stroke\s*=\s*["\'][^"\']*["\']', f'stroke="{color_hex}"', svg_data, flags=re.IGNORECASE)
                            svg_data = re.sub(r'fill\s*:\s*[^;"]*', f'fill:{color_hex}', svg_data, flags=re.IGNORECASE)

                        byte_array = QByteArray(svg_data.encode('utf-8'))
                        renderer = QSvgRenderer(byte_array)
                        
                        def_w = max(1, renderer.defaultSize().width())
                        def_h = max(1, renderer.defaultSize().height())
                        ratio = def_w / def_h
                        
                        w_lienzo = float(elem.get('w', 300))
                        target_w = max(w_lienzo * 3.0, 1500.0) 
                        target_w = min(target_w, 3500.0) # Límite de seguridad de VRAM
                        
                        pw = int(target_w)
                        ph = int(target_w / ratio)
                        
                        pixmap = QPixmap(pw, ph)
                        pixmap.fill(Qt.GlobalColor.transparent)
                        
                        painter = QPainter(pixmap)
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                        renderer.render(painter)
                        painter.end()
                        
                        # 🚀 GUARDAMOS LA IMAGEN HD EN LA CACHÉ MAESTRA
                        self.cache_pixmaps[cache_key] = pixmap
                        
                        item = QGraphicsPixmapItem(pixmap)
                        item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                        item.setData(998, (float(pw), float(ph))) 
                    except Exception as e:
                        print(f"Error Híbrido SVG: {e}")
                        item = QGraphicsPixmapItem()
            else:
                # JPG o PNG normal
                item = QGraphicsPixmapItem()
                item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
                if ruta and os.path.exists(ruta):
                    if ruta not in self.cache_pixmaps:
                        pix = QPixmap(ruta)
                        if not pix.isNull():
                            self.cache_pixmaps[ruta] = pix
                            
                    # 🚀 LA CURA DEL UNDO: Si la foto está en la memoria RAM, 
                    # debemos estamparla obligatoriamente en el ítem que acabamos de revivir.
                    if ruta in self.cache_pixmaps and not self.cache_pixmaps[ruta].isNull():
                        item.setPixmap(self.cache_pixmaps[ruta])
                        item.setData(998, (float(self.cache_pixmaps[ruta].width()), float(self.cache_pixmaps[ruta].height())))
                
        elif tipo == 'Texto':
            item = QGraphicsItemGroup()
            # 🚀 APAGADO: Ya no delegamos la selección visual a Qt
            item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
            item.setData(100, uid) 
        else: 
            item = QGraphicsPathItem()

        # 🚀 APAGADO: Destruimos los bordes punteados nativos y ahorramos un 60% de CPU
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        
        # 🚀 CURA: El cursor nace según la herramienta actual, no como mano por defecto
        herramienta = getattr(self, 'herramienta_activa', 'select')
        cursor_obj = Qt.CursorShape.CrossCursor if herramienta in ['pen', '3d', 'perspective'] else Qt.CursorShape.OpenHandCursor
        item.setCursor(cursor_obj)
        
        item.setData(100, uid)
        
        # 🚀 LA MAGIA DE LA VELOCIDAD: Hardware Caching Local
        es_svg = tipo == 'Foto' and str(elem.get('contenido', '')).lower().endswith('.svg')
        es_texto = tipo == 'Texto'
        es_trazo = tipo == 'Trazo'
        
        # 🚀 AÑADIMOS EL TRAZO PARA QUE SE COMPORTE COMO UNA FOTO AL MOVERSE
        if es_svg or es_texto or es_trazo:
            # ItemCoordinateCache aísla la figura en una textura pequeña (BBox real)
            # Esto permite hacer zoom y mover a 60 FPS sin recalcular matemáticas.
            item.setCacheMode(QGraphicsItem.CacheMode.ItemCoordinateCache)
        else:
            item.setCacheMode(QGraphicsItem.CacheMode.NoCache)

        self.scene().addItem(item)
        self.items_ui[uid] = item


    def get_pdf_coords(self, event):
        pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        pos_scene = self.mapToScene(pos_view)
        # 🚀 CORRECCIÓN: Forzamos el zoom a 1.0 porque mapToScene ya absorbió el nivel de zoom
        return self.motor.ui_a_pdf(pos_scene.x(), pos_scene.y(), 1.0)

    def dibujar_controles_seleccion(self):
        if self.modo_accion in ["MOVE", "RESIZE", "ROTATE", "ROTATE_3D"]: 
            if hasattr(self, 'grupo_controles') and self.grupo_controles:
                if self.modo_accion != "ROTATE_3D":
                    self.grupo_controles.setOpacity(0.0) 
            return
            
        if hasattr(self, 'grupo_controles') and self.grupo_controles in self.scene().items():
            self.scene().removeItem(self.grupo_controles)

        if hasattr(self, 'grupo_nodos') and self.grupo_nodos in self.scene().items():
            self.scene().removeItem(self.grupo_nodos)
        
        if not self.uids_seleccionados: return
        if self.modo_accion in ["MOVE", "RESIZE", "ROTATE", "ROTATE_3D"]: return
        
        es_multiple = len(self.uids_seleccionados) > 1
        
        # 🚀 LA CURA DE LA SELECCIÓN MÚLTIPLE: 
        # Forzamos ángulo 0.0 y no aplicamos 3D/Perspectiva a la caja grupal
        if es_multiple:
            caja = self.motor.obtener_caja_multiple(self.uids_seleccionados)
            angulo_pdf = 0.0
            rot_3dx = 0.0
            rot_3dy = 0.0
            tiene_perspectiva = False
            # Para la caja múltiple, el "elem" simulado estará vacío
            elem = {} 
        else:
            caja = self.motor.obtener_caja_elemento(self.uid_activo)
            elem = self.motor.elementos[self.uid_activo]
            angulo_pdf = float(elem.get('rotacion', 0.0))
            rot_3dx = float(elem.get('rot_3d_x', 0.0))
            rot_3dy = float(elem.get('rot_3d_y', 0.0))
            persp = elem.get('perspectiva', [[0,0], [0,0], [0,0], [0,0]])
            tiene_perspectiva = any(pt != [0,0] for pt in persp)
            
        if not caja: return

        # Transformación de las coordenadas de la caja a UI (PyQt)
        cx = float(caja.get('x') or 0.0)
        cy = float(caja.get('y') or 0.0)
        cw = float(caja.get('w') or 0.0)
        ch = float(caja.get('h') or 0.0)

        x1_orig, y1_orig, x2_orig, y2_orig = self.motor.pdf_a_ui(cx, cy, cw, ch, 1.0, self.motor.h_pdf)
        w_orig, h_orig = x2_orig - x1_orig, y2_orig - y1_orig
        cx_orig, cy_orig = x1_orig + (w_orig / 2.0), y1_orig + (h_orig / 2.0)

        from PyQt6.QtGui import QTransform, QPolygonF
        from PyQt6.QtCore import QPointF
        
        # =========================================================
        # OJO: Si es múltiple, nos saltamos todo este cálculo deformante 
        # y pasamos directo a las variables _f (finales)
        # =========================================================
        if not es_multiple:
            # 1. Aplicamos 3D para sacar los límites reales
            hw_orig, hh_orig = w_orig / 2.0, h_orig / 2.0
            t_3d = QTransform()
            if rot_3dx != 0.0 or rot_3dy != 0.0:
                t_3d.rotate(rot_3dx, Qt.Axis.XAxis)
                t_3d.rotate(rot_3dy, Qt.Axis.YAxis)
                
            pts_3d = [t_3d.map(QPointF(-hw_orig, -hh_orig)), t_3d.map(QPointF(hw_orig, -hh_orig)), 
                      t_3d.map(QPointF(hw_orig, hh_orig)), t_3d.map(QPointF(-hw_orig, hh_orig))]
            
            min_x_3d = min(p.x() for p in pts_3d)
            max_x_3d = max(p.x() for p in pts_3d)
            min_y_3d = min(p.y() for p in pts_3d)
            max_y_3d = max(p.y() for p in pts_3d)

            # 2. Perspectiva exacta amarrada a esos límites
            if tiene_perspectiva:
                poly_src = QPolygonF([
                    QPointF(min_x_3d, min_y_3d), QPointF(max_x_3d, min_y_3d),
                    QPointF(max_x_3d, max_y_3d), QPointF(min_x_3d, max_y_3d)
                ])
                poly_dst = QPolygonF([
                    QPointF(min_x_3d + persp[0][0], min_y_3d + persp[0][1]),
                    QPointF(max_x_3d + persp[1][0], min_y_3d + persp[1][1]),
                    QPointF(max_x_3d + persp[2][0], max_y_3d + persp[2][1]),
                    QPointF(min_x_3d + persp[3][0], max_y_3d + persp[3][1])
                ])
                t_deform = QTransform()
                QTransform.quadToQuad(poly_src, poly_dst, t_deform)
                
                pts_final = [t_deform.map(p) for p in poly_src]
                min_x_f = min(p.x() for p in pts_final)
                max_x_f = max(p.x() for p in pts_final)
                min_y_f = min(p.y() for p in pts_final)
                max_y_f = max(p.y() for p in pts_final)
            else:
                min_x_f, max_x_f = min_x_3d, max_x_3d
                min_y_f, max_y_f = min_y_3d, max_y_3d
        else:
            # 🚀 Si es múltiple, la caja gigante que sacó el motor ya viene perfecta y plana
            min_x_f, max_x_f = -(w_orig/2.0), (w_orig/2.0)
            min_y_f, max_y_f = -(h_orig/2.0), (h_orig/2.0)

        # 3. La caja azul (o naranja) perfecta
        x1 = cx_orig + min_x_f
        y1 = cy_orig + min_y_f
        x2 = cx_orig + max_x_f
        y2 = cy_orig + max_y_f
        w_ui = x2 - x1
        h_ui = y2 - y1
        cx_ui = x1 + (w_ui / 2.0)
        cy_ui = y1 + (h_ui / 2.0)

        self.grupo_controles = QGraphicsItemGroup()
        self.grupo_controles.setFiltersChildEvents(False)

        herramienta = getattr(self, 'herramienta_activa', 'select')

        # 🚀 LA CURA DE LA VISTA LIMPIA: Si tienes la pluma, NO dibujamos ninguna caja.
        if herramienta in ['pen', 'node_edit']:
            pass 
        elif herramienta not in ['3d', 'perspective']:
            # ==========================================
            # 🟦 MODO NORMAL: Caja Azul y 8 Cuadritos Blancos
            # ==========================================
            rect_item = QGraphicsRectItem(x1, y1, w_ui, h_ui)
            pen_borde = QPen(QColor(COLOR_ACCENT), 2, Qt.PenStyle.SolidLine)
            pen_borde.setCosmetic(True) 
            rect_item.setPen(pen_borde)
            rect_item.setBrush(QBrush(QColor(0, 0, 0, 0))) 
            rect_item.setData(0, "move")
            rect_item.setZValue(0) 
            rect_item.setCursor(Qt.CursorShape.SizeAllCursor) 
            self.grupo_controles.addToGroup(rect_item)

            distancia_extra = 30 / self.zoom
            rx_ui = cx_ui
            ry_ui = y2 + distancia_extra

            linea_rot = QGraphicsLineItem(cx_ui, y2, rx_ui, ry_ui)
            pen_linea = QPen(QColor(COLOR_ACCENT), 1.5, Qt.PenStyle.DashLine)
            pen_linea.setCosmetic(True)
            linea_rot.setPen(pen_linea)
            linea_rot.setZValue(0)
            self.grupo_controles.addToGroup(linea_rot)

            BG_SIZE = 28 / self.zoom
            handle_rot_bg = QGraphicsEllipseItem(rx_ui - BG_SIZE/2, ry_ui - BG_SIZE/2, BG_SIZE, BG_SIZE)
            handle_rot_bg.setBrush(QBrush(QColor(BG_CANVAS_HEADER))) 
            pen_rot = QPen(QColor(COLOR_ACCENT), 2)
            pen_rot.setCosmetic(True)
            handle_rot_bg.setPen(pen_rot)
            handle_rot_bg.setData(0, "rot") 
            handle_rot_bg.setZValue(1) 
            handle_rot_bg.setCursor(Qt.CursorShape.PointingHandCursor)
            self.grupo_controles.addToGroup(handle_rot_bg)

            ICON_SIZE = 16 / self.zoom
            icon_pixmap = qta.icon('fa5s.sync-alt', color=TEXT_MAIN).pixmap(int(16), int(16))
            handle_rot_icon = QGraphicsPixmapItem(icon_pixmap)
            handle_rot_icon.setScale(1.0 / self.zoom) 
            handle_rot_icon.setPos(rx_ui - (ICON_SIZE / 2), ry_ui - (ICON_SIZE / 2))
            handle_rot_icon.setData(0, "rot") 
            handle_rot_icon.setZValue(2) 
            handle_rot_icon.setCursor(Qt.CursorShape.PointingHandCursor)
            self.grupo_controles.addToGroup(handle_rot_icon)

            H_SIZE = 8 / self.zoom
            OFFSET = H_SIZE / 2
            for key, (px, py) in {'tl': (x1 - OFFSET, y1 - OFFSET), 'tc': (x1 + (w_ui/2) - OFFSET, y1 - OFFSET), 'tr': (x2 - OFFSET, y1 - OFFSET), 'ml': (x1 - OFFSET, y1 + (h_ui/2) - OFFSET), 'mr': (x2 - OFFSET, y1 + (h_ui/2) - OFFSET), 'bl': (x1 - OFFSET, y2 - OFFSET), 'bc': (x1 + (w_ui/2) - OFFSET, y2 - OFFSET), 'br': (x2 - OFFSET, y2 - OFFSET)}.items():
                handle = QGraphicsRectItem(px, py, H_SIZE, H_SIZE)
                handle.setBrush(QBrush(QColor(TEXT_MAIN)))
                pen_handle = QPen(QColor(COLOR_ACCENT), 1.5)
                pen_handle.setCosmetic(True)
                handle.setPen(pen_handle)
                handle.setData(0, key) 
                handle.setZValue(1) 
                handle.setCursor(self._obtener_cursor_rotado(key, angulo_pdf))
                self.grupo_controles.addToGroup(handle)

        elif herramienta == 'perspective':
            from PyQt6.QtCore import QPointF
            from PyQt6.QtGui import QPolygonF
            from PyQt6.QtWidgets import QGraphicsPolygonItem
            
            elem_activo = self.motor.elementos.get(self.uid_activo, {}) 
            persp = elem_activo.get('perspectiva', [[0,0], [0,0], [0,0], [0,0]])
            
            # 🚀 LA CURA MATEMÁTICA: Usamos los límites reales calculados arriba (min_x_3d, etc.)
            p_tl = QPointF(cx_orig + min_x_3d + persp[0][0], cy_orig + min_y_3d + persp[0][1])
            p_tr = QPointF(cx_orig + max_x_3d + persp[1][0], cy_orig + min_y_3d + persp[1][1])
            p_br = QPointF(cx_orig + max_x_3d + persp[2][0], cy_orig + max_y_3d + persp[2][1])
            p_bl = QPointF(cx_orig + min_x_3d + persp[3][0], cy_orig + max_y_3d + persp[3][1])

            # Dibujamos el polígono conector
            poly = QGraphicsPolygonItem(QPolygonF([p_tl, p_tr, p_br, p_bl]))
            color_malla = QColor(COLOR_ACCENT) 
            color_malla.setAlpha(180)
            poly.setPen(QPen(color_malla, 2.0, Qt.PenStyle.DashLine))
            poly.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            poly.setZValue(0)
            self.grupo_controles.addToGroup(poly)
            self.caja_persp = poly
            
            # Hitbox invisible central
            hitbox_centro = QGraphicsPolygonItem(QPolygonF([p_tl, p_tr, p_br, p_bl]))
            hitbox_centro.setBrush(QBrush(QColor(255, 255, 255)))
            hitbox_centro.setPen(QPen(Qt.PenStyle.NoPen))
            hitbox_centro.setOpacity(0.01)
            hitbox_centro.setData(0, "move")
            hitbox_centro.setCursor(Qt.CursorShape.SizeAllCursor)
            hitbox_centro.setZValue(5)
            self.grupo_controles.addToGroup(hitbox_centro)
            self.hitbox_persp = hitbox_centro
            
            # Dibujamos los 4 nodos agarrables
            puntos = [('p_tl', p_tl), ('p_tr', p_tr), ('p_br', p_br), ('p_bl', p_bl)]
            ns = 18 / self.zoom 
            
            for clave, pt in puntos:
                nodo = QGraphicsEllipseItem(pt.x() - ns/2, pt.y() - ns/2, ns, ns)
                nodo.setBrush(QBrush(QColor(COLOR_ACCENT)))
                nodo.setPen(QPen(QColor("#FFFFFF"), 2.0))
                nodo.setData(0, clave)
                nodo.setCursor(Qt.CursorShape.CrossCursor)
                nodo.setZValue(10)
                self.grupo_controles.addToGroup(nodo)
                
        else:
            # ==========================================
            # 🟪 MODO 3D PREMIUM: Controles Perimetrales
            # ==========================================
            margen = 35 / self.zoom 
            nodo_size = 18 / self.zoom 
            self.gizmo_ns = nodo_size 
            
            min_len = 120 / self.zoom 

            elem_activo = self.motor.elementos.get(self.uid_activo, {})
            a_x = float(elem_activo.get('rot_3d_x', 0.0))
            a_y = float(elem_activo.get('rot_3d_y', 0.0))

            # 1. EL BORDE VISUAL (Caja Naranja Translúcida)
            rect_item = QGraphicsRectItem(x1, y1, w_ui, h_ui)
            color_caja = QColor(COLOR_ACCENT)
            color_caja.setAlpha(150) # Translúcido
            pen_borde = QPen(color_caja, 1.5, Qt.PenStyle.DashLine)
            pen_borde.setCosmetic(True)
            rect_item.setPen(pen_borde)
            rect_item.setBrush(QBrush(Qt.BrushStyle.NoBrush)) 
            rect_item.setZValue(0)
            self.grupo_controles.addToGroup(rect_item)
            
            # 🚀 Guardamos referencia directa a la caja visual para apagarla luego
            self.caja_3d = rect_item 
            
            # Hitbox Central Infalible
            hitbox_centro = QGraphicsRectItem(x1, y1, w_ui, h_ui)
            hitbox_centro.setBrush(QBrush(QColor(255, 255, 255))) 
            hitbox_centro.setPen(QPen(Qt.PenStyle.NoPen))
            hitbox_centro.setOpacity(0.01) 
            hitbox_centro.setData(0, "move")
            hitbox_centro.setCursor(Qt.CursorShape.SizeAllCursor)
            hitbox_centro.setZValue(5)
            self.grupo_controles.addToGroup(hitbox_centro)
            
            # 🚀 Guardamos referencia a la Hitbox para que no interfiera el ratón al rotar
            self.hitbox_3d = hitbox_centro

            # 🚀 MATEMÁTICA DE TAMAÑO MÍNIMO: Aseguramos que la pista nunca sea más corta que min_len
            tw = max(w_ui, min_len)
            tx1 = cx_ui - (tw / 2)
            tx2 = cx_ui + (tw / 2)

            th = max(h_ui, min_len)
            ty1 = cy_ui - (th / 2)
            ty2 = cy_ui + (th / 2)

            # --- CONTROL Y (Naranja, Inferior) ---
            centro_abajo_y = y2 + margen
            
            # Hitbox Y centrada y con tamaño mínimo
            self.pista_y_hitbox = QGraphicsRectItem(tx1, centro_abajo_y - 15, tw, 30)
            self.pista_y_hitbox.setBrush(QBrush(QColor(255, 255, 255)))
            self.pista_y_hitbox.setPen(QPen(Qt.PenStyle.NoPen))
            self.pista_y_hitbox.setOpacity(0.01)
            self.pista_y_hitbox.setData(0, '3d_y')
            self.pista_y_hitbox.setCursor(Qt.CursorShape.SizeHorCursor)
            self.pista_y_hitbox.setZValue(10)
            self.grupo_controles.addToGroup(self.pista_y_hitbox)
            
            # 🚀 LÍNEA VISUAL Y: Más gruesa (4) y color Naranja
            color_linea_y = QColor(COLOR_ACCENT)
            color_linea_y.setAlpha(120)
            self.pista_y = QGraphicsLineItem(tx1, centro_abajo_y, tx2, centro_abajo_y)
            self.pista_y.setPen(QPen(color_linea_y, 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            self.pista_y.setZValue(9)
            self.grupo_controles.addToGroup(self.pista_y)
            
            # Calculamos la posición del nodo basándonos en el tamaño garantizado (tw)
            porcentaje_y = max(min((a_y + 180) / 360.0, 1.0), 0.0)
            pos_nodo_y = tx1 + (tw * porcentaje_y)

            self.nodo_y = QGraphicsEllipseItem(pos_nodo_y - (nodo_size/2), centro_abajo_y - (nodo_size/2), nodo_size, nodo_size)
            self.nodo_y.setBrush(QBrush(QColor(COLOR_ACCENT)))
            self.nodo_y.setPen(QPen(QColor("#FFFFFF"), 2.0))
            self.nodo_y.setData(0, '3d_y')
            self.nodo_y.setCursor(Qt.CursorShape.SizeHorCursor)
            self.nodo_y.setZValue(11)
            self.grupo_controles.addToGroup(self.nodo_y)

            # --- CONTROL X (Morado, Derecho) ---
            centro_der_x = x2 + margen
            
            # Hitbox X centrada y con tamaño mínimo
            self.pista_x_hitbox = QGraphicsRectItem(centro_der_x - 15, ty1, 30, th)
            self.pista_x_hitbox.setBrush(QBrush(QColor(255, 255, 255)))
            self.pista_x_hitbox.setPen(QPen(Qt.PenStyle.NoPen))
            self.pista_x_hitbox.setOpacity(0.01)
            self.pista_x_hitbox.setData(0, '3d_x')
            self.pista_x_hitbox.setCursor(Qt.CursorShape.SizeVerCursor)
            self.pista_x_hitbox.setZValue(10)
            self.grupo_controles.addToGroup(self.pista_x_hitbox)
            
            # 🚀 LÍNEA VISUAL X: Más gruesa (4) y color Morado
            color_linea_x = QColor("#B689FF")
            color_linea_x.setAlpha(120)
            self.pista_x = QGraphicsLineItem(centro_der_x, ty1, centro_der_x, ty2)
            self.pista_x.setPen(QPen(color_linea_x, 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            self.pista_x.setZValue(9)
            self.grupo_controles.addToGroup(self.pista_x)

            porcentaje_x = max(min((a_x + 180) / 360.0, 1.0), 0.0)
            pos_nodo_x = ty1 + (th * porcentaje_x)

            self.nodo_x = QGraphicsEllipseItem(centro_der_x - (nodo_size/2), pos_nodo_x - (nodo_size/2), nodo_size, nodo_size)
            self.nodo_x.setBrush(QBrush(QColor("#B689FF")))
            self.nodo_x.setPen(QPen(QColor("#FFFFFF"), 2.0))
            self.nodo_x.setData(0, '3d_x')
            self.nodo_x.setCursor(Qt.CursorShape.SizeVerCursor)
            self.nodo_x.setZValue(11)
            self.grupo_controles.addToGroup(self.nodo_x)
            
            # 🚀 Guardamos las nuevas dimensiones forzadas para el motor de arrastre
            self.gizmo_cx = cx_ui
            self.gizmo_cy = cy_ui
            self.gizmo_tw = tw
            self.gizmo_th = th
            self.gizmo_tx1 = tx1
            self.gizmo_ty1 = ty1
            
            self.gizmo_x1 = x1
            self.gizmo_y1 = y1
            self.gizmo_w = w_ui
            self.gizmo_h = h_ui

        # Aplicamos la matriz final al grupo entero
        # 🚀 LA CURA DEL DESFASE DE ROTACIÓN: Rotar sobre el pivote original absoluto
        self.grupo_controles.setTransformOriginPoint(cx_orig, cy_orig) 
        self.grupo_controles.setRotation(-angulo_pdf)
        self.grupo_controles.setZValue(999999.0)
        self.grupo_controles.setOpacity(1.0)
        self.scene().addItem(self.grupo_controles)

        # ==========================================
        # 🚀 OVERLAY DE NODOS VECTORIALES (Para Trazos) - Estilo Premium
        # ==========================================
        if not es_multiple and elem.get('tipo') == 'Trazo' and herramienta in ['node_edit', 'pen']:
            self.grupo_nodos = QGraphicsItemGroup()
            self.grupo_nodos.setZValue(999999.5) # Encima de todo
            
            pts_rel = elem.get('puntos', [])
            t_final = self._obtener_matriz_acumulada(self.uid_activo)
            
            # Nodos más pequeños y elegantes
            ns = 6.0 / self.zoom 
            
            for i, p in enumerate(pts_rel):
                p_qt = QPointF(p[0], -p[1])
                p_scene = t_final.map(p_qt)
                
                if i == 0 or i == len(pts_rel) - 1:
                    nodo = QGraphicsEllipseItem(p_scene.x() - (ns*1.4)/2, p_scene.y() - (ns*1.4)/2, ns*1.4, ns*1.4)
                    nodo.setBrush(QBrush(QColor("#FFFFFF")))
                    nodo.setPen(QPen(QColor(COLOR_ACCENT), 1.5 / self.zoom))
                else:
                    nodo = QGraphicsEllipseItem(p_scene.x() - ns/2, p_scene.y() - ns/2, ns, ns)
                    nodo.setBrush(QBrush(QColor("#FFFFFF")))
                    nodo.setPen(QPen(QColor("#6A6D75"), 1.0 / self.zoom))
                
                # 🚀 LA MAGIA: Le asignamos un ID y cursor a cada nodo
                nodo.setData(0, f"nodo_{i}") 
                if herramienta == 'node_edit':
                    nodo.setCursor(Qt.CursorShape.SizeAllCursor)
                
                self.grupo_nodos.addToGroup(nodo)
                
            self.scene().addItem(self.grupo_nodos)

    def _suavizar_trazo(self, puntos, factor):
        """Aplica un algoritmo de Media Móvil (Moving Average) para fluidificar el trazo manual"""
        if len(puntos) < 3 or factor == 0:
            return puntos
            
        puntos_suaves = [puntos[0]]
        ventana = factor # Cuántos puntos vecinos promedia
        for i in range(1, len(puntos) - 1):
            inicio = max(0, i - ventana)
            fin = min(len(puntos), i + ventana + 1)
            vecinos = puntos[inicio:fin]
            
            avg_x = sum(p.x() for p in vecinos) / len(vecinos)
            avg_y = sum(p.y() for p in vecinos) / len(vecinos)
            puntos_suaves.append(QPointF(avg_x, avg_y))
            
        puntos_suaves.append(puntos[-1])
        return puntos_suaves

    def wheelEvent(self, event):
        """Controla el Zoom y el Desplazamiento usando el estándar de diseño"""
        mods = event.modifiers()
        delta = event.angleDelta().y()
        
        # 1. SHIFT + Rueda = Desplazamiento Horizontal
        if mods & Qt.KeyboardModifier.ShiftModifier:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            
        # 2. ALT + Rueda = Desplazamiento Vertical
        elif mods & Qt.KeyboardModifier.AltModifier:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta)
            
        # 3. Solo Rueda = ZOOM INTERACTIVO
        else:
            # 🚀 LA CURA DEL ZOOM HACIA EL RATÓN (Matemática Absoluta)
            # Apagamos el ancla de Qt temporalmente porque se congela con la herramienta mano
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            
            # Guardamos qué punto exacto del mapa (escena) estamos mirando bajo el ratón
            pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            pos_scene_antes = self.mapToScene(pos_view)

            factor = 1.15 if delta > 0 else 1.0 / 1.15
            self.scale(factor, factor)
            self.zoom *= factor
            
            # Tras hacer zoom, el lienzo se quedó quieto y el punto se movió. Calculamos dónde quedó.
            pos_scene_despues = self.mapToScene(pos_view)
            
            # Ajustamos las barras de desplazamiento forzando a que la pantalla siga tu puntero
            delta_x = (pos_scene_antes.x() - pos_scene_despues.x()) * self.transform().m11()
            delta_y = (pos_scene_antes.y() - pos_scene_despues.y()) * self.transform().m22()

            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + int(delta_x))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + int(delta_y))
            
            # Restauramos el ancla por seguridad interna de Qt
            self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

            # Redibujamos la caja azul para que sus controles se adapten a la nueva escala
            if getattr(self, 'uid_activo', None):
                self.dibujar_controles_seleccion()

    # ==========================================
    # SISTEMA DE EDICIÓN DE TEXTO (DOBLE CLIC)
    # ==========================================
    def mouseDoubleClickEvent(self, event):
        # Si hicimos doble clic y es un texto, abrimos el editor
        if self.uid_activo and self.motor.elementos.get(self.uid_activo, {}).get('tipo') == 'Texto':
            self.abrir_editor_texto(self.uid_activo)
            return
        super().mouseDoubleClickEvent(event)

    def abrir_editor_texto(self, uid):
        from PyQt6.QtWidgets import QTextEdit, QLabel
        
        elem = self.motor.elementos[uid]
        if hasattr(self, 'editor_flotante') and self.editor_flotante:
            self.cerrar_editor_texto()

        self.uid_en_edicion = uid
        self.editor_flotante = QTextEdit(self)
        self.editor_flotante.setPlainText(str(elem.get('contenido', '')))
        
        # 🚀 CORRECCIÓN: El editor flotante siempre se centrará en sí mismo para no verse "corrido",
        # respetando que la alineación de diseño solo pertenece al lienzo matemático.
        self.editor_flotante.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Estilo Premium Oscuro
        self.editor_flotante.setStyleSheet("""
            QTextEdit {
                background-color: rgba(26, 27, 30, 0.95);
                color: #FFFFFF;
                border: 2px solid #FE5934;
                border-radius: 12px;
                padding: 15px;
                font-size: 20px;
                selection-background-color: #FE5934;
            }
        """)
        
        self.lbl_ayuda_editor = QLabel("Presiona <b>Ctrl + Enter</b> para guardar, o <b>Esc</b> para cancelar", self)
        self.lbl_ayuda_editor.setStyleSheet("color: #A0A0A5; font-size: 13px; background: transparent;")
        self.lbl_ayuda_editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Centrar en la pantalla
        w, h = 450, 150
        v_rect = self.viewport().rect()
        cx, cy = v_rect.center().x(), v_rect.center().y()
        
        self.editor_flotante.setGeometry(int(cx - w/2), int(cy - h/2), w, h)
        self.lbl_ayuda_editor.setGeometry(int(cx - w/2), int(cy + h/2 + 5), w, 20)
        
        self.editor_flotante.show()
        self.lbl_ayuda_editor.show()
        self.editor_flotante.setFocus()
        
        # Selecciona todo el texto para reemplazarlo rápido
        cursor = self.editor_flotante.textCursor()
        cursor.select(cursor.SelectionType.Document)
        self.editor_flotante.setTextCursor(cursor)
        
        # Instalamos el vigía de teclado
        self.editor_flotante.installEventFilter(self)
        self.modo_accion = "EDITANDO_TEXTO"

    def guardar_texto_editado(self):
        if not hasattr(self, 'editor_flotante') or not self.editor_flotante: return
        nuevo_texto = self.editor_flotante.toPlainText()
        uid = self.uid_en_edicion
        self.cerrar_editor_texto()
        
        if uid in self.motor.elementos:
            self.motor.registrar_punto_historial()
            self.motor.modificar_elemento(uid, contenido=nuevo_texto)
            self.sincronizar_con_motor([uid])
            self.dibujar_controles_seleccion()
            if hasattr(self, 'parent_panel'): 
                self.parent_panel.actualizar_lienzo()
                self.parent_panel.window()._refrescar_panel_capas() # 🚀 REFRESCAR AL CAMBIAR TEXTO
            self.lienzo_modificado.emit()

    def cerrar_editor_texto(self):
        if hasattr(self, 'editor_flotante') and self.editor_flotante:
            self.editor_flotante.removeEventFilter(self)
            self.editor_flotante.deleteLater()
            self.editor_flotante = None
        if hasattr(self, 'lbl_ayuda_editor') and self.lbl_ayuda_editor:
            self.lbl_ayuda_editor.deleteLater()
            self.lbl_ayuda_editor = None
        self.modo_accion = None
        self.uid_en_edicion = None
        self.setFocus()

    def eventFilter(self, source, event):
        if hasattr(self, 'editor_flotante') and source is self.editor_flotante:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                    self.guardar_texto_editado()
                    return True
                elif event.key() == Qt.Key.Key_Escape:
                    self.cerrar_editor_texto()
                    return True
            elif event.type() == QEvent.Type.FocusOut:
                # 🚀 Auto-guardado de calidad de vida: Si haces clic fuera del cuadro, se guarda solo.
                self.guardar_texto_editado()
                return True
        return super().eventFilter(source, event)

    def _ejecutar_copiar(self):
        """Copia los elementos seleccionados al Portapapeles Global"""
        if not self.uids_seleccionados: return
        elementos_copiados = []
        uids_ya_copiados = set() # Evitar duplicados
        
        # 🚀 LA CURA: Copia profunda incluyendo nietos y bisnietos
        def copiar_recursivo(uid_actual):
            if uid_actual in uids_ya_copiados or uid_actual not in self.motor.elementos: return
            uids_ya_copiados.add(uid_actual)
            
            elem = self.motor.elementos[uid_actual]
            # 🚀 USAMOS EL CLONADOR DEL MOTOR PARA COPIAR AL PORTAPAPELES
            elementos_copiados.append((uid_actual, self.motor._clonar_seguro(elem)))
            
            if elem['tipo'] == 'Marco':
                for h_uid, h_elem in self.motor.elementos.items():
                    if h_elem.get('parent_marco') == uid_actual:
                        copiar_recursivo(h_uid)

        for uid in self.uids_seleccionados:
            copiar_recursivo(uid)
            
        self.window().portapapeles_global = elementos_copiados

    def _ejecutar_pegar(self, pdf_x=None, pdf_y=None):
        """Pega los elementos. Si recibe coordenadas, los centra en el ratón."""
        clipboard = getattr(self.window(), 'portapapeles_global', None)
        if not clipboard: return
        
        self.motor.registrar_punto_historial()
        
        nuevos_uids_seleccion = []
        mapa_uids = {} 
        max_z = max([e.get('z_index', 0) for e in self.motor.elementos.values()] or [0])
        
        # 🚀 INICIO DE CARGA
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        try:
            # 🚀 LÓGICA DE POSICIÓN: Atajo de teclado (+20px) VS Clic Derecho (Centro del ratón)
            offset_x, offset_y = 20, -20
            main_elems = [e for uid, e in clipboard if not e.get('parent_marco')]
        
            if main_elems and pdf_x is not None and pdf_y is not None:
                min_x = min([e.get('x', 0) for e in main_elems])
                max_x = max([e.get('x', 0) + e.get('w', 0) for e in main_elems])
                min_y = min([e.get('y', 0) for e in main_elems])
                max_y = max([e.get('y', 0) + e.get('h', 0) for e in main_elems])
                
                centro_cb_x = min_x + (max_x - min_x) / 2.0
                centro_cb_y = min_y + (max_y - min_y) / 2.0
                
                offset_x = pdf_x - centro_cb_x
                offset_y = pdf_y - centro_cb_y
            
            for i, (old_uid, elem_data) in enumerate(clipboard):
                nuevo_uid = f"paste_{int(time.time() * 1000)}_{i}"
                mapa_uids[old_uid] = nuevo_uid
                
                # 🚀 USAMOS EL CLONADOR DEL MOTOR PARA PEGAR EN EL LIENZO
                nuevo_elem = self.motor._clonar_seguro(elem_data)
                
                nuevo_elem['x'] += offset_x
            
            for n_uid in mapa_uids.values():
                padre_viejo = self.motor.elementos[n_uid].get('parent_marco')
                if padre_viejo and padre_viejo in mapa_uids:
                    self.motor.elementos[n_uid]['parent_marco'] = mapa_uids[padre_viejo]
                elif padre_viejo:
                    self.motor.elementos[n_uid]['parent_marco'] = None
                
                if not self.motor.elementos[n_uid].get('parent_marco'):
                    nuevos_uids_seleccion.append(n_uid)
            
            self.motor._normalizar_z_index()
            if nuevos_uids_seleccion:
                self.uids_seleccionados = nuevos_uids_seleccion
                self.uid_activo = nuevos_uids_seleccion[-1]
                self.parent_panel.actualizar_lienzo()
                self.parent_panel.window()._refrescar_panel_capas()
                self.lienzo_modificado.emit()
                self.elemento_seleccionado.emit(self.uid_activo)
                
        finally:
            # 🚀 FIN DE CARGA
            QApplication.restoreOverrideCursor()

    def _iniciar_memoria_arrastre(self, pdf_x, pdf_y):
        """Toma una foto a las posiciones absolutas y crea una lista ultra-rápida (O(1))"""
        self.modo_accion = "MOVE"
        self.start_pdf_x, self.start_pdf_y = pdf_x, pdf_y
        self.last_mouse_x, self.last_mouse_y = pdf_x, pdf_y
        
        # 1. Recolectar jerarquía (padres e hijos) una sola vez
        self.uids_arrastre = list(self.uids_seleccionados)
        def recolectar(p_uid):
            for h_uid, h_e in self.motor.elementos.items():
                if h_e.get('parent_marco') == p_uid:
                    if h_uid not in self.uids_arrastre:
                        self.uids_arrastre.append(h_uid)
                        recolectar(h_uid)
                    
        for u in self.uids_seleccionados:
            if self.motor.elementos.get(u, {}).get('tipo') == 'Marco':
                recolectar(u)
                
        # 🚀 2. PRE-CÁLCULO EXTREMO (Data-Oriented Design)
        # En vez de buscar en diccionarios 60 veces por segundo, guardamos 
        # punteros directos a la RAM en una lista plana súper rápida.
        self._arrastre_fast_cache = []
        for u in self.uids_arrastre:
            e = self.motor.elementos.get(u)
            ui_item = self.items_ui.get(u)
            if e and ui_item:
                self._arrastre_fast_cache.append({
                    'dict_ref': e,          # Puntero directo a la base de datos (Motor)
                    'math_x': float(e.get('x', 0.0)),
                    'math_y': float(e.get('y', 0.0)),
                    'item_ref': ui_item,    # Puntero directo al objeto gráfico en C++ (Qt)
                    'ui_x': ui_item.pos().x(),
                    'ui_y': ui_item.pos().y()
                })
                
        # 3. Guardar posición de la caja azul
        if hasattr(self, 'grupo_controles') and self.grupo_controles:
            self.start_caja_pos = self.grupo_controles.pos()

    def mousePressEvent(self, event):
        # 🚀 1. AISLAR MOTOR DE PANEO NATIVO DE C++
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
            return super().mousePressEvent(event)
            
        self.setFocus() 

        # ========================================================
        # 🚀 1.5. LA HERRAMIENTA CUENTAGOTAS NATIVA
        # ========================================================
        if getattr(self, 'herramienta_activa', 'select') == "eyedropper":
            # Borramos el tooltip personalizado y repintamos para que desaparezca visualmente
            if hasattr(self, '_color_gotero'):
                del self._color_gotero
                del self._pos_gotero
                self.viewport().update()
                
            if event.button() == Qt.MouseButton.LeftButton:
                pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
                
                # Le tomamos foto SOLAMENTE al lienzo (viewport) en ese píxel exacto
                captura = self.viewport().grab(QRect(pos_view.x(), pos_view.y(), 1, 1))
                color = captura.toImage().pixelColor(0, 0)
                
                main_studio = self.window()
                if hasattr(main_studio, 'procesar_color_robado'):
                    main_studio.procesar_color_robado(color)
                    
                self.set_tool("select")
                return # Abortamos cualquier otra acción
                
            elif event.button() == Qt.MouseButton.RightButton:
                main_studio = self.window()
                if hasattr(main_studio, 'cancelar_cuentagotas'):
                    main_studio.cancelar_cuentagotas()
                    
                self.set_tool("select")
                return # Abortamos cualquier otra acción

        # 🚀 2. INTERCEPTOR DE LA MIRA ÓPTICA (Delante de / Detrás de)
        if getattr(self, "modo_accion", None) in ["TARGET_DELANTE", "TARGET_DETRAS"]:
            if event.button() == Qt.MouseButton.LeftButton:
                pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
                pos_scene = self.mapToScene(pos_view)
                items_bajo_raton = self.scene().items(pos_scene, Qt.ItemSelectionMode.IntersectsItemShape, Qt.SortOrder.DescendingOrder, self.viewportTransform())
                
                uid_encontrado = None
                for it in items_bajo_raton:
                    if it.data(100) and it.data(100) != self.uid_objetivo_origen:
                        uid_encontrado = it.data(100)
                        break
                        
                if uid_encontrado:
                    self.motor.registrar_punto_historial()
                    if self.modo_accion == "TARGET_DELANTE":
                        self.motor.mover_delante_de(self.uid_objetivo_origen, uid_encontrado)
                    else:
                        self.motor.mover_detras_de(self.uid_objetivo_origen, uid_encontrado)
                    self._refrescar_despues_de_capa()
                    
            self.modo_accion = None
            self.uid_objetivo_origen = None
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            return

        # 🚀 3. MENÚ CONTEXTUAL PREMIUM (Clic Derecho)
        if event.button() == Qt.MouseButton.RightButton:
            pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            pos_scene = self.mapToScene(pos_view)
            pdf_x, pdf_y = self.get_pdf_coords(event) 
            
            items_bajo_raton = self.scene().items(pos_scene, Qt.ItemSelectionMode.IntersectsItemBoundingRect, Qt.SortOrder.DescendingOrder, self.viewportTransform())
            
            uid_encontrado = None
            for it in items_bajo_raton:
                if it.data(100):
                    uid_encontrado = it.data(100)
                    break
                    
            if uid_encontrado:
                if uid_encontrado not in self.uids_seleccionados:
                    self.uids_seleccionados = [uid_encontrado]
                    self.uid_activo = uid_encontrado
                    self.dibujar_controles_seleccion()
                    self.elemento_seleccionado.emit(self.uid_activo)
                    
                self._mostrar_menu_capas(event.globalPosition().toPoint())
            else:
                self.scene().clearSelection()
                self.uids_seleccionados = []
                self.uid_activo = None
                self.dibujar_controles_seleccion()
                self.elemento_seleccionado.emit("")
                self._mostrar_menu_canvas(event.globalPosition().toPoint(), pdf_x, pdf_y)
            return



        # 🚀 4. SELECCIÓN, ARRASTRE Y HERRAMIENTA DE TEXTO (Clic Izquierdo)
        if event.button() == Qt.MouseButton.LeftButton:
            pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            pos_scene = self.mapToScene(pos_view)
            pdf_x, pdf_y = self.get_pdf_coords(event)
            
            self.hubo_arrastre = False # 🚀 Bandera para saber si solo dio clic o arrastró
            
            # =======================================================
            # 🚀 INICIO DEL DIBUJO CON PLUMA E IMÁN VECTORIAL
            # =======================================================
            herramienta = getattr(self, 'herramienta_activa', 'select')
            if herramienta == 'pen':
                from PyQt6.QtGui import QPainterPath, QBrush, QColor, QPen
                from PyQt6.QtCore import QPointF, QLineF
                
                uid_continuar = None
                puntos_heredados_pdf = []
                puntos_heredados_scene = []
                invertir_trazo = False
                
                # IMÁN MAGNÉTICO
                if self.uid_activo and self.motor.elementos.get(self.uid_activo, {}).get('tipo') == 'Trazo':
                    elem = self.motor.elementos[self.uid_activo]
                    t_final = self._obtener_matriz_acumulada(self.uid_activo)
                    pts_rel = elem.get('puntos', [])
                    if pts_rel:
                        p_inicio_scene = t_final.map(QPointF(pts_rel[0][0], -pts_rel[0][1]))
                        p_fin_scene = t_final.map(QPointF(pts_rel[-1][0], -pts_rel[-1][1]))
                        umbral = 15.0 / self.zoom
                        
                        if QLineF(pos_scene, p_fin_scene).length() <= umbral: uid_continuar = self.uid_activo
                        elif QLineF(pos_scene, p_inicio_scene).length() <= umbral:
                            uid_continuar = self.uid_activo; invertir_trazo = True

                # MEMORIA DE GROSOR
                if uid_continuar:
                    elem = self.motor.elementos[uid_continuar]
                    pts_rel = elem.get('puntos', [])
                    t_final = self._obtener_matriz_acumulada(uid_continuar)
                    for p in pts_rel:
                        p_scene = t_final.map(QPointF(p[0], -p[1]))
                        p_pdf_x, p_pdf_y = self.motor.ui_a_pdf(p_scene.x(), p_scene.y(), 1.0)
                        
                        # Rescatamos el grosor individual de cada punto guardado
                        g_pt = p[2] if len(p) > 2 else float(elem.get('borde_grosor', 3.0))
                        puntos_heredados_scene.append((p_scene, g_pt))
                        puntos_heredados_pdf.append((QPointF(p_pdf_x, p_pdf_y), g_pt))
                        
                    if invertir_trazo:
                        puntos_heredados_scene.reverse(); puntos_heredados_pdf.reverse()
                        
                    self.puntos_trazo = puntos_heredados_pdf
                    self.puntos_visuales = puntos_heredados_scene
                    self.uid_en_edicion_trazo = uid_continuar
                    # El grosor arranca en el grosor del último punto del imán
                    self.grosor_pluma_actual = puntos_heredados_pdf[-1][1]
                    if uid_continuar in self.items_ui: self.items_ui[uid_continuar].setVisible(False)
                else:
                    self.grosor_pluma_actual = 5.0 # Grosor estándar
                    self.puntos_trazo = [(QPointF(pdf_x, pdf_y), self.grosor_pluma_actual)] 
                    self.puntos_visuales = [(pos_scene, self.grosor_pluma_actual)]          
                    self.uid_en_edicion_trazo = None

                self.item_trazo_temp = QGraphicsPathItem()
                # 🚀 LA MAGIA: El trazo en vivo ya no es una "línea" (Pen), ahora es una "forma rellena" (Brush)
                self.item_trazo_temp.setPen(QPen(Qt.PenStyle.NoPen))
                self.item_trazo_temp.setBrush(QBrush(QColor("#FE5934")))
                self.item_trazo_temp.setZValue(999999)
                self.scene().addItem(self.item_trazo_temp)
                
                if uid_continuar:
                    self.item_trazo_temp.setPath(self._generar_patron_variable(self.puntos_visuales))
                
                self.modo_accion = "DRAWING"
                return
            # =======================================================
            
            # A. ¿Hicimos clic en un control de transformación (caja azul)?
            item = self.scene().itemAt(pos_scene, self.viewportTransform())
            if item and item.data(0):
                clave = str(item.data(0))
                es_multiple = len(self.uids_seleccionados) > 1
                
                if clave.startswith("nodo_"):
                    self.motor.registrar_punto_historial(self.uids_seleccionados)
                    self.modo_accion = "MOVE_NODE"
                    self.nodo_activo_idx = int(clave.split("_")[1])
                    self.start_pdf_x, self.start_pdf_y = pdf_x, pdf_y
                    self.start_puntos = copy.deepcopy(self.motor.elementos[self.uid_activo]['puntos'])
                    
                    # 🚀 LA CURA DEL TIEMPO REAL: Apagamos el caché mientras editamos
                    item_real = self.items_ui[self.uid_activo]
                    item_real.setCacheMode(QGraphicsItem.CacheMode.NoCache)
                    
                    return
                
                if clave == "rot":
                    self.motor.registrar_punto_historial(self.uids_seleccionados)
                    self.setCursor(Qt.CursorShape.ClosedHandCursor) # 🚀 Cerramos la mano al rotar
                    self.modo_accion = "ROTATE"
                    if es_multiple:
                        caja_global = self.motor.obtener_caja_multiple(self.uids_seleccionados)
                        self.caja_multiple_fija = caja_global.copy()
                        self.angulo_multiple_fijo = 0.0
                        self.start_cx_global = caja_global['x'] + (caja_global['w']/2.0)
                        self.start_cy_global = caja_global['y'] + (caja_global['h']/2.0)
                        self.last_angulo = self.motor.calcular_angulo_raton_multiple(self.uids_seleccionados, pdf_x, pdf_y)
                    else:
                        self.last_angulo = self.motor.calcular_angulo_raton(self.uid_activo, pdf_x, pdf_y)
                    return

                elif clave == "move":
                    self.motor.registrar_punto_historial(self.uids_seleccionados)
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    # 🚀 Invocamos la memoria absoluta
                    self._iniciar_memoria_arrastre(pdf_x, pdf_y)
                    return
                
                elif clave in ['tl', 'tc', 'tr', 'ml', 'mr', 'bl', 'bc', 'br']:
                    self.motor.registrar_punto_historial(self.uids_seleccionados)
                    # 🚀 COPIAMOS EL CURSOR NATIVO DEL CUADRITO ANTES DE BLOQUEAR LA ACCIÓN
                    self.setCursor(item.cursor()) 
                    self.modo_accion = "RESIZE"
                    self.handle_activo = clave
                    self.start_pdf_x, self.start_pdf_y = pdf_x, pdf_y
                    self.start_caja = self.motor.obtener_caja_multiple(self.uids_seleccionados) if es_multiple else self.motor.obtener_caja_elemento(self.uid_activo).copy()
                    return
                
                # 🚀 INICIA LA ROTACIÓN 3D (GIZMO INDIVIDUAL)
                elif clave in ['3d_x', '3d_y']:
                    self.motor.registrar_punto_historial(self.uids_seleccionados)
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    self.modo_accion = "ROTATE_3D"
                    self.handle_activo = clave
                    self.start_pdf_x, self.start_pdf_y = pdf_x, pdf_y
                    
                    elem = self.motor.elementos[self.uid_activo]
                    self.start_3d_x = float(elem.get('rot_3d_x', 0.0))
                    self.start_3d_y = float(elem.get('rot_3d_y', 0.0))
                    
                    # 🚀 MAGIA UX: Ocultamos visual y físicamente la pista que NO estamos usando
                    if clave == '3d_x':
                        self.pista_y.setVisible(False)
                        self.nodo_y.setVisible(False)
                        self.pista_y_hitbox.setVisible(False)
                    else:
                        self.pista_x.setVisible(False)
                        self.nodo_x.setVisible(False)
                        self.pista_x_hitbox.setVisible(False)
                        
                    # 🚀 LA CURA DE LA CAJA INVISIBLE: Apagamos el recuadro naranja
                    if hasattr(self, 'caja_3d'): self.caja_3d.setVisible(False)
                    if hasattr(self, 'hitbox_3d'): self.hitbox_3d.setVisible(False)
                        
                    return # 🚀 <--- ABORTA LA SELECCIÓN MÚLTIPLE

                # 🚀 INICIA PERSPECTIVA LIBRE (4 PUNTOS)
                elif clave in ['p_tl', 'p_tr', 'p_br', 'p_bl']:
                    self.motor.registrar_punto_historial(self.uids_seleccionados)
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    self.modo_accion = "PERSPECTIVE"
                    self.handle_activo = clave
                    self.start_pdf_x, self.start_pdf_y = pdf_x, pdf_y
                    
                    elem = self.motor.elementos[self.uid_activo]
                    self.start_persp = copy.deepcopy(elem.get('perspectiva', [[0,0], [0,0], [0,0], [0,0]]))
                    
                    # Ocultamos la caja cyan para limpiar la vista
                    if hasattr(self, 'caja_persp'): self.caja_persp.setVisible(False)
                    if hasattr(self, 'hitbox_persp'): self.hitbox_persp.setVisible(False)
                    
                    return # 🚀 ABORTA LA SELECCIÓN MÚLTIPLE
            
            # B. ¿Hicimos clic sobre un elemento del lienzo?
            items_bajo_raton = self.scene().items(pos_scene, Qt.ItemSelectionMode.IntersectsItemBoundingRect, Qt.SortOrder.DescendingOrder, self.viewportTransform())
            
            uid_encontrado = None
            for it in items_bajo_raton:
                if it.data(100): 
                    uid_encontrado = it.data(100)
                    break
            
            if uid_encontrado:
                elem = self.motor.elementos.get(uid_encontrado)
                if elem and not elem.get('bloqueado', False) and not elem.get('oculto', False):
                    self.motor.registrar_punto_historial()
                    uid_seleccion = elem.get('parent_marco') if elem.get('parent_marco') in self.motor.elementos else uid_encontrado

                    mods = event.modifiers()
                    herramienta = getattr(self, 'herramienta_activa', 'select')
                    
                    # =======================================================
                    # 🚀 RESTRICCIÓN 3D / PERSPECTIVA: Anular tecla Shift
                    # =======================================================
                    if herramienta in ['3d', 'perspective']:
                        # Ignoramos el Shift. Forzamos a que el clic sea individual siempre.
                        if uid_seleccion not in self.uids_seleccionados or len(self.uids_seleccionados) > 1:
                            self.uids_seleccionados = [uid_seleccion]
                        self.uid_activo = uid_seleccion
                    else:
                        # Comportamiento normal con la flecha de Selección (V)
                        if mods & Qt.KeyboardModifier.ShiftModifier:
                            if uid_seleccion in self.uids_seleccionados:
                                self.uids_seleccionados.remove(uid_seleccion)
                                self.uid_activo = self.uids_seleccionados[-1] if self.uids_seleccionados else None
                            else:
                                self.uids_seleccionados.append(uid_seleccion)
                                self.uid_activo = uid_seleccion
                        else:
                            if uid_seleccion not in self.uids_seleccionados: self.uids_seleccionados = [uid_seleccion]
                            self.uid_activo = uid_seleccion
                    # =======================================================

                    # Lo marcamos para MOVER (incluso si tenemos la herramienta de texto activa)
                    self._iniciar_memoria_arrastre(pdf_x, pdf_y) # 🚀 Memoria Absoluta
                    
                    uid_emit = self.uid_activo if self.uid_activo else ""
                    QTimer.singleShot(0, lambda u=uid_emit: self.elemento_seleccionado.emit(u))
                    
                    self.dibujar_controles_seleccion()
                    return
            
            # C. ¿Hicimos clic en el ESPACIO VACÍO del lienzo con la herramienta de TEXTO?
            if getattr(self, 'herramienta_activa', 'select') == 'text':
                uid_nuevo = f"txt_{int(time.time() * 1000)}"
                
                self.motor.registrar_punto_historial()
                self.motor.agregar_elemento(
                    uid_nuevo, 'Texto', contenido="Nuevo texto", 
                    x=pdf_x, y=pdf_y, w=36, color_tx="#000000", fuente="Helvetica" 
                )
                self.motor._normalizar_z_index()
                
                self.uids_seleccionados = [uid_nuevo]
                self.uid_activo = uid_nuevo
                self.sincronizar_con_motor()
                self.dibujar_controles_seleccion()
                
                if hasattr(self, 'parent_panel'):
                    self.parent_panel.window()._refrescar_panel_capas()
                    if hasattr(self.parent_panel.main_canvas, 'toolbar'):
                        self.parent_panel.main_canvas.toolbar._set_initial_tool("select")
                    
                self.elemento_seleccionado.emit(uid_nuevo)
                self.lienzo_modificado.emit()
                
                QTimer.singleShot(50, lambda: self.abrir_editor_texto(uid_nuevo))
                event.accept()
                return

            # D. Si hicimos clic en el espacio vacío con la flecha normal
            self.scene().clearSelection() # 🚀 FORZAMOS LA LIMPIEZA NATIVA DE QT
            
            self.uids_seleccionados = []
            self.uid_activo = None
            self.modo_accion = None
            
            # Limpiamos cualquier memoria residual de transformaciones múltiples
            if hasattr(self, 'caja_multiple_fija'): del self.caja_multiple_fija
            if hasattr(self, 'angulo_multiple_fijo'): del self.angulo_multiple_fijo
            
            QTimer.singleShot(0, lambda: self.elemento_seleccionado.emit(""))
            self.dibujar_controles_seleccion()
            
            super().mousePressEvent(event)
            return
            
        super().mousePressEvent(event)

    def _obtener_cursor_rotado(self, handle_id, angulo_base):
        """
        Dibuja un cursor vectorial personalizado: Flecha negra, borde blanco.
        TAMAÑO CORREGIDO y ROTACIÓN SINCRONIZADA MATEMÁTICAMENTE.
        """
        # 1. Los ángulos base de hacia dónde apunta cada flecha (0° = Derecha, 90° = Abajo)
        angulos_base = {
            'mr': 0, 'ml': 0,
            'br': 45, 'tl': 45,
            'bc': 90, 'tc': 90,
            'bl': 135, 'tr': 135
        }

        # 🚀 2. LA CORRECCIÓN: Restamos el ángulo en lugar de sumarlo.
        # ¿Por qué? Porque PyQt gira los objetos en dirección contraria (-rot)
        # al motor matemático. Ahora la flecha girará exactamente con el objeto.
        angulo_total = int(angulos_base[handle_id] - float(angulo_base)) % 180
        
        # Evitamos ángulos negativos para la caché
        if angulo_total < 0:
            angulo_total += 180

        if not hasattr(self, '_cursor_cache'):
            self._cursor_cache = {}

        if angulo_total in self._cursor_cache:
            return self._cursor_cache[angulo_total]

        # 3. Cuadro de 24x24 píxeles (Estándar UI)
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Movemos el pincel al centro exacto (12, 12)
        painter.translate(12, 12)
        painter.rotate(angulo_total)
        
        # 4. DIBUJO VECTORIAL
        path = QPainterPath()
        path.moveTo(-4, -1.5)  
        path.lineTo(-4, -4)    
        path.lineTo(-11, 0)    
        path.lineTo(-4, 4)     
        path.lineTo(-4, 1.5)   
        path.lineTo(4, 1.5)    
        path.lineTo(4, 4)      
        path.lineTo(11, 0)     
        path.lineTo(4, -4)     
        path.lineTo(4, -1.5)   
        path.closeSubpath()
        
        # 5. ESTILOS PROPORCIONALES
        painter.setBrush(QColor("#000000")) 
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        painter.drawPath(path)
        painter.end() 

        # Convertimos el dibujo en un cursor
        cursor = QCursor(pixmap, 12, 12)
        self._cursor_cache[angulo_total] = cursor
        
        return cursor

    def setCursor(self, cursor):
        """Interceptamos setCursor para evitar el bug de 'flecha parpadeante' y anular manos estorbosas"""
        # 🚀 BLOQUEO TOTAL: Si estamos transformando, el cursor se congela
        if getattr(self, 'modo_accion', None) in ["RESIZE", "MOVE", "ROTATE", "ROTATE_3D"]:
            return
            
        # 🚀 LA CURA DEL CURSOR ESTORBOSO: Si la pluma está activa, la mira es absoluta
        if getattr(self, 'herramienta_activa', 'select') == 'pen':
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
            super().setCursor(Qt.CursorShape.CrossCursor)
            return

        self.viewport().setCursor(cursor)
        super().setCursor(cursor)

    def descomponer_svg_en_capas(self, uid_svg):
        """Convierte un SVG flat en una estructura de capas reales (Grupo)"""
        self.motor.registrar_punto_historial()
        
        # Cambiamos el cursor a "Cargando" por si el SVG tiene miles de trazos
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents() 
        
        # Llamamos a tu motor gráfico
        nuevo_id_grupo = self.motor.desagrupar_svg(uid_svg)
        
        QApplication.restoreOverrideCursor() 
        
        if nuevo_id_grupo:
            self.uids_seleccionados = [nuevo_id_grupo]
            self.uid_activo = nuevo_id_grupo
            if hasattr(self, 'parent_panel'): 
                self.parent_panel.actualizar_lienzo()
                self.parent_panel.window()._refrescar_panel_capas()
            self.lienzo_modificado.emit()
            self.elemento_seleccionado.emit(self.uid_activo)

    def _mostrar_menu_capas(self, pos_global):
        """Menú para Objetos: Capas, Copiar, Ocultar, Bloquear, Descomponer y Eliminar"""
        menu = QMenu(self.viewport())
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 🚀 CSS PREMIUM ESTILO FIGMA / MACOS
        menu.setStyleSheet("""
            QMenu { 
                background-color: #18191D; 
                border: 1px solid #2A2B31; 
                border-radius: 8px; 
                padding: 6px 0px; 
            }
            QMenu::item { 
                color: #D1D1D5; 
                padding: 6px 40px 6px 35px; /* Espacio para el icono */
                margin: 1px 6px; 
                border-radius: 4px; 
                font-family: 'Gilroy'; 
                font-weight: 500; 
                font-size: 13px; 
            }
            QMenu::item:selected { 
                background-color: #2D2E36; 
                color: #FFFFFF; 
            }
            QMenu::icon {
                padding-left: 12px; 
            }
            QMenu::separator { 
                height: 1px; 
                background: #2A2B31; 
                margin: 4px 12px; 
            }
        """)
        
        elem = self.motor.elementos.get(self.uid_activo, {})
        esta_oculto = elem.get('oculto', False)
        esta_bloqueado = elem.get('bloqueado', False)
        es_svg = elem.get('tipo') == 'Foto' and str(elem.get('contenido', '')).lower().endswith('.svg')
        
        # 🚀 MONOCROMO: Todos los iconos usan el gris silencioso
        icon_color = "#85868A" 
        
        accion_copiar = menu.addAction(qta.icon('fa5s.copy', color=icon_color), "Copiar")
        accion_copiar.setShortcut("Ctrl+C")
        
        accion_descomponer = None
        if es_svg:
            accion_descomponer = menu.addAction(qta.icon('fa5s.object-ungroup', color=icon_color), "Descomponer SVG")
            accion_descomponer.setShortcut("Ctrl+Shift+G")
            
        menu.addSeparator()
        
        accion_subir = menu.addAction(qta.icon('fa5s.angle-up', color=icon_color), "Traer hacia adelante")
        accion_bajar = menu.addAction(qta.icon('fa5s.angle-down', color=icon_color), "Enviar hacia atrás")
        accion_frente = menu.addAction(qta.icon('fa5s.angle-double-up', color=icon_color), "Traer al frente")
        accion_fondo = menu.addAction(qta.icon('fa5s.angle-double-down', color=icon_color), "Enviar al fondo")
        
        menu.addSeparator()
        
        accion_delante = menu.addAction(qta.icon('fa5s.bullseye', color=icon_color), "Delante de...")
        accion_detras = menu.addAction(qta.icon('fa5s.bullseye', color=icon_color), "Detrás de...")
        
        menu.addSeparator()
        
        accion_bloquear = menu.addAction(qta.icon('fa5s.lock-open' if esta_bloqueado else 'fa5s.lock', color=icon_color), "Desbloquear" if esta_bloqueado else "Bloquear")
        accion_ocultar = menu.addAction(qta.icon('fa5s.eye' if esta_oculto else 'fa5s.eye-slash', color=icon_color), "Mostrar" if esta_oculto else "Ocultar")

        menu.addSeparator()

        # 🚀 LA OPCIÓN DE ELIMINAR (Gris, elegante y con atajo)
        accion_eliminar = menu.addAction(qta.icon('fa5s.trash', color=icon_color), "Eliminar")
        accion_eliminar.setShortcut("Del") # Qt traducirá esto automáticamente a "Supr" o "Del" según el idioma del OS

        accion = menu.exec(pos_global)
        
        if accion:
            if accion == accion_copiar:
                self._ejecutar_copiar()
                return 
                
            if accion_descomponer and accion == accion_descomponer:
                self.descomponer_svg_en_capas(self.uid_activo)
                return

            self.motor.registrar_punto_historial()
            
            if accion == accion_subir: self.motor.subir_capa(self.uid_activo)
            elif accion == accion_bajar: self.motor.bajar_capa(self.uid_activo)
            elif accion == accion_frente: self.motor.traer_al_frente(self.uid_activo)
            elif accion == accion_fondo: self.motor.enviar_al_fondo(self.uid_activo)
            elif accion == accion_delante:
                self.modo_accion = "TARGET_DELANTE"; self.uid_objetivo_origen = self.uid_activo
                self.viewport().setCursor(Qt.CursorShape.CrossCursor); return 
            elif accion == accion_detras:
                self.modo_accion = "TARGET_DETRAS"; self.uid_objetivo_origen = self.uid_activo
                self.viewport().setCursor(Qt.CursorShape.CrossCursor); return
            elif accion == accion_bloquear:
                self.motor.modificar_elemento(self.uid_activo, bloqueado=not esta_bloqueado)
            elif accion == accion_ocultar:
                self.motor.modificar_elemento(self.uid_activo, oculto=not esta_oculto)
            elif accion == accion_eliminar:
                # 🚀 DESTRUCCIÓN OPTIMIZADA INSTANTÁNEA (Soporta múltiples objetos)
                for uid_sel in self.uids_seleccionados:
                    if uid_sel in self.items_ui:
                        item_ui = self.items_ui.pop(uid_sel)
                        self.scene().removeItem(item_ui)
                    self.motor.eliminar_elemento(uid_sel, limpiar_cache=False)
                    
                self.motor.limpiar_cache_imagenes()
                self.uids_seleccionados = []
                self.uid_activo = None
                
                self.dibujar_controles_seleccion()
                self.elemento_seleccionado.emit("")
                self.solicitar_actualizacion_masiva()
                return # Escapamos para no hacer el refresco estándar y ganar velocidad
                
            self._refrescar_despues_de_capa()

    def _mostrar_menu_canvas(self, pos_global, pdf_x, pdf_y):
        """Menú del Fondo: Pegar"""
        menu = QMenu(self.viewport())
        menu.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # 🚀 Mismo CSS premium
        menu.setStyleSheet("""
            QMenu { 
                background-color: #18191D; 
                border: 1px solid #2A2B31; 
                border-radius: 8px; 
                padding: 6px 0px; 
            }
            QMenu::item { 
                color: #D1D1D5; 
                padding: 6px 40px 6px 35px; 
                margin: 1px 6px; 
                border-radius: 4px; 
                font-family: 'Gilroy'; 
                font-weight: 500; 
                font-size: 13px; 
            }
            QMenu::item:selected { 
                background-color: #2D2E36; 
                color: #FFFFFF; 
            }
            QMenu::icon {
                padding-left: 12px; 
            }
            QMenu::item:disabled { 
                color: #4A4D57; 
            }
        """)
        
        clipboard = getattr(self.window(), 'portapapeles_global', None)
        accion_pegar = menu.addAction(qta.icon('fa5s.paste', color="#85868A" if clipboard else "#4A4D57"), "Pegar aquí")
        accion_pegar.setShortcut("Ctrl+V") # 🚀 Añade atajo a la derecha
        
        if not clipboard:
            accion_pegar.setEnabled(False)
            
        accion = menu.exec(pos_global)
        if accion == accion_pegar:
            self._ejecutar_pegar(pdf_x, pdf_y)

    def _refrescar_despues_de_capa(self):
        """Redibuja y sincroniza los paneles después de mover capas"""
        self.sincronizar_con_motor()
        self.dibujar_controles_seleccion()
        if hasattr(self, 'parent_panel'): 
            self.parent_panel.actualizar_lienzo()
            # Le pedimos a la ventana principal que refresque la lista de capas a la izquierda
            self.parent_panel.window()._refrescar_panel_capas()
        self.lienzo_modificado.emit()

    def mouseMoveEvent(self, event):
        # ========================================================
        # 🚀 PRIORIDAD ABSOLUTA: HOVER DEL CUENTAGOTAS NATIVO
        # ========================================================
        herramienta = getattr(self, 'herramienta_activa', 'select')
        pos_scene = self.mapToScene(event.pos())
        
        if herramienta == "eyedropper":
            pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            captura = self.viewport().grab(QRect(pos_view.x(), pos_view.y(), 1, 1))
            color = captura.toImage().pixelColor(0, 0)
            
            # Guardamos el color y la posición del ratón para dibujarlos luego
            self._color_gotero = color
            self._pos_gotero = pos_view
            
            # Le decimos a la ventana principal que actualice el panel lateral (opcional)
            main_studio = self.window()
            if hasattr(main_studio, 'procesar_color_hover'):
                main_studio.procesar_color_hover(color)
                
            # 🚀 Forzamos a Qt a repintar el lienzo para dibujar nuestra UI flotante
            self.viewport().update()
            
            # IMPORTANTE: Abortamos para que Qt no empiece a dibujar cursores fantasma ni a mover cajas
            return 
            
        # Si la herramienta NO es el gotero, borramos sus datos de memoria y actualizamos la pantalla
        if hasattr(self, '_color_gotero'):
            del self._color_gotero
            del self._pos_gotero
            self.viewport().update()

        # 🚀 ESCUDO CONTRA EL PUNTERO FANTASMA (VERSIÓN MULTI-HERRAMIENTA)
        if event.buttons() == Qt.MouseButton.NoButton:
            items_bajo_raton = self.items(event.pos())
            tiene_cursor_especial = any(item.hasCursor() for item in items_bajo_raton)
            
            if not tiene_cursor_especial:
                if herramienta == "hand":
                    self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
                elif herramienta == "text":
                    self.viewport().setCursor(Qt.CursorShape.IBeamCursor) 
                elif herramienta in ["pen", "shape", "3d", "perspective"]:
                    self.viewport().setCursor(Qt.CursorShape.CrossCursor) 
                elif herramienta != "eyedropper": # 🚀 No interferimos si es el cuentagotas
                    self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

        # 🚀 1. AISLAR MOTOR DE PANEO NATIVO DE C++
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag:
            return super().mouseMoveEvent(event)

        pos_view = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        pos_scene = self.mapToScene(pos_view)
        
        # 🚀 2. EFECTOS DE CURSOR HOVER
        if not self.modo_accion and self.uid_activo and hasattr(self, 'grupo_controles'):
            encontrado = False
            for handle in self.grupo_controles.childItems():
                if handle.contains(handle.mapFromScene(pos_scene)):
                    data = handle.data(0)
                    elem = self.motor.elementos.get(self.uid_activo) 
                    if elem:
                        angulo_obj = 0.0 if len(self.uids_seleccionados) > 1 else float(elem.get('rotacion', 0.0))
                        if data in ('tl', 'tc', 'tr', 'ml', 'mr', 'bl', 'bc', 'br'):
                            self.setCursor(self._obtener_cursor_rotado(data, angulo_obj))
                            encontrado = True; break
                            
                        # CURSORES 3D AL PASAR EL RATÓN (GIZMO)
                        elif data == '3d_x':
                            self.setCursor(Qt.CursorShape.SizeVerCursor)
                            encontrado = True; break
                        elif data == '3d_y':
                            self.setCursor(Qt.CursorShape.SizeHorCursor)
                            encontrado = True; break
                        elif data == "rot":
                            self.setCursor(Qt.CursorShape.PointingHandCursor)
                            encontrado = True; break
                        elif data == "move":
                            self.setCursor(Qt.CursorShape.SizeAllCursor)
                            encontrado = True; break

        

        

        
        # =======================================================
        # 🚀 2.5 DIBUJO EN VIVO MAGISTRAL (Con sensibilidad de teclas)
        # =======================================================
        if self.modo_accion == "DRAWING":
            pdf_x, pdf_y = self.get_pdf_coords(event)
                
            # 🚀 DINÁMICA S/A (Crecer / Encoger suavemente)
            if self.tecla_s_presionada: self.grosor_pluma_actual = min(60.0, self.grosor_pluma_actual + 1.0)
            if self.tecla_a_presionada: self.grosor_pluma_actual = max(1.0, self.grosor_pluma_actual - 1.0)
                
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.puntos_trazo = [self.puntos_trazo[0], (QPointF(pdf_x, pdf_y), self.grosor_pluma_actual)] 
                self.puntos_visuales = [self.puntos_visuales[0], (pos_scene, self.grosor_pluma_actual)]         
            else:
                self.puntos_trazo.append((QPointF(pdf_x, pdf_y), self.grosor_pluma_actual)) 
                self.puntos_visuales.append((pos_scene, self.grosor_pluma_actual))         
                
            # 🚀 RESTAURADO: Tu generador de curvas perfecto.
            # Al no tener que recalcular la sombra de toda la pantalla,
            # esto ahora se dibujará instantáneamente.
            path_suave = self._generar_patron_variable(self.puntos_visuales)
            self.item_trazo_temp.setPath(path_suave)
            return
            

        # 🚀 3. LÓGICA DE TRANSFORMACIÓN Y ARRASTRE
        if self.modo_accion and self.uids_seleccionados: 
            pdf_x, pdf_y = self.get_pdf_coords(event)
            es_multiple = len(self.uids_seleccionados) > 1
            
            if self.modo_accion == "MOVE":
                self.hubo_arrastre = True
                
                dx_global = pdf_x - self.start_pdf_x
                dy_global = pdf_y - self.start_pdf_y
                
                if dx_global == 0 and dy_global == 0: 
                    return
                
                if len(getattr(self, '_arrastre_fast_cache', [])) > 0:
                    dy_qt = -dy_global # Invertimos Y para la pantalla
                    
                    # 🚀 APAGAMOS LA PANTALLA POR 1 MILISEGUNDO
                    self.viewport().setUpdatesEnabled(False)
                    
                    # 🚀 BUCLE SÚPER OPTIMIZADO EN C++ Y RAM PURA
                    # Sin 'ifs', sin funciones '.get()', sin buscar en diccionarios.
                    # Pura escritura directa a la memoria.
                    for obj in self._arrastre_fast_cache:
                        # 1. Matemática directa en RAM
                        obj['dict_ref']['x'] = obj['math_x'] + dx_global
                        obj['dict_ref']['y'] = obj['math_y'] + dy_global
                        
                        # 2. Movimiento directo en C++
                        obj['item_ref'].setPos(obj['ui_x'] + dx_global, obj['ui_y'] + dy_qt)
                            
                    # 3. Deslizamos la caja naranja (controles)
                    if hasattr(self, 'grupo_controles') and self.grupo_controles and hasattr(self, 'start_caja_pos'):
                        self.grupo_controles.setPos(self.start_caja_pos.x() + dx_global, self.start_caja_pos.y() + dy_qt)
                        
                    # 🚀 ENCENDEMOS LA PANTALLA (Pinta todo de 1 solo golpe)
                    self.viewport().setUpdatesEnabled(True)

                self.last_mouse_x = pdf_x
                self.last_mouse_y = pdf_y
                return

            # =======================================================
            # 🚀 TRANSFORMAR ELEMENTOS SELECCIONADOS (Tiempo Real Nodos)
            # =======================================================
            elif self.modo_accion == "MOVE_NODE":
                dx_global = pdf_x - self.start_pdf_x
                dy_global = pdf_y - self.start_pdf_y
                
                angulo = float(self.motor.elementos[self.uid_activo].get('rotacion', 0.0))
                if angulo != 0.0:
                    rad = math.radians(angulo)
                    dx = (dx_global * math.cos(rad)) + (dy_global * math.sin(rad))
                    dy = -(dx_global * math.sin(rad)) + (dy_global * math.cos(rad))
                else:
                    dx, dy = dx_global, dy_global
                    
                idx = self.nodo_activo_idx
                pt_orig = self.start_puntos[idx]
                
                # 1. Actualizamos el punto exacto en el motor
                self.motor.elementos[self.uid_activo]['puntos'][idx][0] = round(pt_orig[0] + dx, 2)
                self.motor.elementos[self.uid_activo]['puntos'][idx][1] = round(pt_orig[1] + dy, 2)
                
                # 2. REGENERAMOS EL PATH VISUAL DEL ITEM REAL
                item_real = self.items_ui[self.uid_activo]
                puntos_relativos = self.motor.elementos[self.uid_activo].get('puntos', [])
                pts_relativos_qt = []
                for p_rel in puntos_relativos:
                    g_pt = p_rel[2] if len(p_rel) > 2 else float(self.motor.elementos[self.uid_activo].get('borde_grosor', 3.0))
                    pts_relativos_qt.append((QPointF(p_rel[0], -p_rel[1]), g_pt))
                
                path_suave = self._generar_patron_variable(pts_relativos_qt)
                t_final = self._obtener_matriz_acumulada(self.uid_activo)
                item_real.setPath(path_suave)
                item_real.setTransform(t_final)
                
                # 🚀 LA CURA DE LA DESTRUCCIÓN MASIVA: Mover el nodo sin recrear todo
                # ❌ Eliminamos self.dibujar_controles_seleccion()
                # ✅ En su lugar, buscamos el puntito blanco específico y lo movemos.
                pos_actualizada = t_final.map(QPointF(puntos_relativos[idx][0], -puntos_relativos[idx][1]))
                ns = 6.0 / self.zoom 
                
                for child in self.grupo_nodos.childItems():
                    if child.data(0) == f"nodo_{idx}":
                        if idx == 0 or idx == len(puntos_relativos) - 1:
                            child.setRect(pos_actualizada.x() - (ns*1.4)/2, pos_actualizada.y() - (ns*1.4)/2, ns*1.4, ns*1.4)
                        else:
                            child.setRect(pos_actualizada.x() - ns/2, pos_actualizada.y() - ns/2, ns, ns)
                        break
                
                return

            elif self.modo_accion == "RESIZE":
                mods = event.modifiers()
                candado_activo = False
                if hasattr(self.parent_panel.properties_panel, 'btn_lock_ratio'):
                    candado_activo = self.parent_panel.properties_panel.btn_lock_ratio.isChecked()
                
                es_esquina = self.handle_activo in ['tl', 'tr', 'bl', 'br']
                if es_esquina:
                    es_proporcional = bool(mods & Qt.KeyboardModifier.ShiftModifier) or candado_activo
                else:
                    es_proporcional = bool(mods & Qt.KeyboardModifier.ShiftModifier) 

                desde_centro = bool(mods & Qt.KeyboardModifier.AltModifier)
                angulo = 0.0 if es_multiple else float(self.motor.elementos[self.uid_activo].get('rotacion', 0.0))
                
                dx_global = pdf_x - self.start_pdf_x
                dy_global = pdf_y - self.start_pdf_y
                
                if angulo != 0.0:
                    rad = math.radians(angulo)
                    dx = (dx_global * math.cos(rad)) + (dy_global * math.sin(rad))
                    dy = -(dx_global * math.sin(rad)) + (dy_global * math.cos(rad))
                else:
                    dx, dy = dx_global, dy_global

                mapa_anclas = {
                    'tl': ('bottom_right', -dx, dy), 'tc': ('bottom_center', 0, dy), 'tr': ('bottom_left', dx, dy),
                    'ml': ('center_right', -dx, 0), 'mr': ('center_left', dx, 0),
                    'bl': ('top_right', -dx, -dy), 'bc': ('top_center', 0, -dy), 'br': ('top_left', dx, -dy)
                }
                
                ancla, delta_w, delta_h = mapa_anclas[self.handle_activo]
                if desde_centro: delta_w *= 2; delta_h *= 2

                nuevo_w = self.start_caja['w'] + delta_w
                nuevo_h = self.start_caja['h'] + delta_h
                ratio_inicio = self.start_caja['w'] / self.start_caja['h'] if self.start_caja['h'] != 0 else 1.0

                if es_multiple:
                    self.motor.escalar_multiples(self.uids_seleccionados, nuevo_w, nuevo_h, ancla, desde_centro, es_proporcional)
                else:
                    self.motor.redimensionar_elemento(self.uid_activo, nuevo_w=nuevo_w, nuevo_h=nuevo_h, ancla=ancla, desde_centro=desde_centro, proporcional=es_proporcional, ratio_fijo=ratio_inicio)
            
            elif self.modo_accion == "ROTATE":
                if es_multiple:
                    nuevo_angulo = self.motor.calcular_angulo_raton_multiple(self.uids_seleccionados, pdf_x, pdf_y)
                    delta = nuevo_angulo - self.last_angulo
                    self.motor.rotar_multiples(self.uids_seleccionados, delta, self.start_cx_global, self.start_cy_global)
                    self.angulo_multiple_fijo = (self.angulo_multiple_fijo + delta) % 360
                    self.last_angulo = nuevo_angulo
                else:
                    nuevo_angulo = self.motor.calcular_angulo_raton(self.uid_activo, pdf_x, pdf_y)
                    self.motor.modificar_elemento(self.uid_activo, rotacion=nuevo_angulo)

            elif self.modo_accion == "ROTATE_3D":
                dx_global = pdf_x - self.start_pdf_x
                dy_global = pdf_y - self.start_pdf_y
                
                sensibilidad_y = 360.0 / self.gizmo_tw if self.gizmo_tw > 0 else 1.0
                sensibilidad_x = 360.0 / self.gizmo_th if self.gizmo_th > 0 else 1.0
                
                if self.handle_activo == '3d_x':
                    nuevo_3dx = self.start_3d_x - (dy_global * sensibilidad_x) 
                    nuevo_3dx = max(-180.0, min(180.0, nuevo_3dx))
                    self.motor.modificar_elemento(self.uid_activo, rot_3d_x=nuevo_3dx)
                    
                    porcentaje_x = (nuevo_3dx + 180) / 360.0
                    ny_x = self.gizmo_ty1 + (self.gizmo_th * porcentaje_x)
                    nx_x = self.gizmo_x1 + self.gizmo_w + (35 / self.zoom)
                    self.nodo_x.setRect(nx_x - (self.gizmo_ns/2), ny_x - (self.gizmo_ns/2), self.gizmo_ns, self.gizmo_ns)
                    
                elif self.handle_activo == '3d_y':
                    nuevo_3dy = self.start_3d_y + (dx_global * sensibilidad_y)
                    nuevo_3dy = max(-180.0, min(180.0, nuevo_3dy))
                    self.motor.modificar_elemento(self.uid_activo, rot_3d_y=nuevo_3dy)
                    
                    porcentaje_y = (nuevo_3dy + 180) / 360.0
                    nx_y = self.gizmo_tx1 + (self.gizmo_tw * porcentaje_y)
                    ny_y = self.gizmo_y1 + self.gizmo_h + (35 / self.zoom)
                    self.nodo_y.setRect(nx_y - (self.gizmo_ns/2), ny_y - (self.gizmo_ns/2), self.gizmo_ns, self.gizmo_ns)

            elif self.modo_accion == "PERSPECTIVE":
                dx_global = pdf_x - self.start_pdf_x
                dy_global = pdf_y - self.start_pdf_y
                
                angulo = float(self.motor.elementos[self.uid_activo].get('rotacion', 0.0))
                if angulo != 0.0:
                    rad = math.radians(angulo)
                    dx = (dx_global * math.cos(rad)) + (dy_global * math.sin(rad))
                    dy = -(dx_global * math.sin(rad)) + (dy_global * math.cos(rad))
                else:
                    dx, dy = dx_global, dy_global
                    
                nueva_persp = copy.deepcopy(self.start_persp)
                
                mapa_idx = {'p_tl': 0, 'p_tr': 1, 'p_br': 2, 'p_bl': 3}
                idx = mapa_idx[self.handle_activo]
                
                nueva_persp[idx][0] += dx
                nueva_persp[idx][1] -= dy 
                
                caja = self.motor.obtener_caja_elemento(self.uid_activo)
                if caja:
                    hw, hh = caja['w'] / 2.0, caja['h'] / 2.0
                    
                    P0 = [-hw + nueva_persp[0][0], -hh + nueva_persp[0][1]] 
                    P1 = [ hw + nueva_persp[1][0], -hh + nueva_persp[1][1]] 
                    P2 = [ hw + nueva_persp[2][0],  hh + nueva_persp[2][1]] 
                    P3 = [-hw + nueva_persp[3][0],  hh + nueva_persp[3][1]] 
                    
                    def cross_product(a, b, c):
                        return (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
                        
                    cp1 = cross_product(P0, P1, P2)
                    cp2 = cross_product(P1, P2, P3)
                    cp3 = cross_product(P2, P3, P0)
                    cp4 = cross_product(P3, P0, P1)
                    
                    margen = 10.0 
                    es_valido = (cp1 > margen and cp2 > margen and cp3 > margen and cp4 > margen)
                                
                    if not es_valido: return 
                        
                self.motor.modificar_elemento(self.uid_activo, perspectiva=nueva_persp)
            
            uids_a_sincronizar = list(self.uids_seleccionados)
            
            def recolectar_para_ui(padre_uid):
                for h_uid, h_elem in self.motor.elementos.items():
                    if h_elem.get('parent_marco') == padre_uid:
                        uids_a_sincronizar.append(h_uid)
                        recolectar_para_ui(h_uid)
                        
            for uid_sel in self.uids_seleccionados:
                if self.motor.elementos[uid_sel]['tipo'] == 'Marco':
                    recolectar_para_ui(uid_sel)
                    
            self.sincronizar_con_motor(uids_a_sincronizar)
            self.dibujar_controles_seleccion()
        
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        if hasattr(self, 'perf_monitor'):
            self.perf_monitor.tick()
        # 1. Dejamos que PyQt dibuje el lienzo, las fotos, los textos y la caja azul
        super().paintEvent(event)
        
        # 2. 🚀 Si el cuentagotas está activo, dibujamos nuestra UI Premium encima de todo
        if getattr(self, 'herramienta_activa', 'select') == "eyedropper" and hasattr(self, '_pos_gotero') and hasattr(self, '_color_gotero'):
            from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QFont, QFontMetrics
            from PyQt6.QtCore import QRect, Qt
            
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            fuente_ui = QFont("Gilroy", 10, QFont.Weight.Bold)
            fm = QFontMetrics(fuente_ui)
            
            # ==========================================
            # 🚀 A: LA PÍLDORA DE INSTRUCCIONES SUPERIOR
            # ==========================================
            texto_ayuda = "Presiona ESC o Clic Derecho para cancelar"
            ancho_texto = fm.horizontalAdvance(texto_ayuda)
            
            ancho_pildora = ancho_texto + 40
            alto_pildora = 36
            # Centrado arriba en el viewport del lienzo
            cx_pildora = int((self.viewport().width() - ancho_pildora) / 2)
            caja_ayuda = QRect(cx_pildora, 25, ancho_pildora, alto_pildora)
            
            painter.setBrush(QBrush(QColor(24, 25, 29, 230))) # Fondo oscuro translúcido
            painter.setPen(QPen(QColor(63, 65, 72), 1))       # Borde sutil
            painter.drawRoundedRect(caja_ayuda, 18, 18)       # Píldora redondeada
            
            painter.setPen(QColor("#85868A"))
            painter.setFont(fuente_ui)
            painter.drawText(caja_ayuda, Qt.AlignmentFlag.AlignCenter, texto_ayuda)
            
            # ==========================================
            # 🚀 B: EL TOOLTIP HEX/CMYK PEGADO AL RATÓN
            # ==========================================
            # Posición del Tooltip (A la derecha y abajo del puntero)
            tx = self._pos_gotero.x() + 15
            ty = self._pos_gotero.y() + 15
            color = self._color_gotero
            
            # Formateo inteligente según el modo del documento
            modo_color = getattr(self.motor, 'modo_color', "RGB")
            if modo_color == "CMYK":
                r, g, b = color.red()/255, color.green()/255, color.blue()/255
                k = 1 - max(r, g, b)
                if k == 1: c = m = y = 0
                else: c, m, y = (1-r-k)/(1-k), (1-g-k)/(1-k), (1-b-k)/(1-k)
                txt_color = f"C:{int(c*100)} M:{int(m*100)} Y:{int(y*100)} K:{int(k*100)}"
            else:
                txt_color = color.name().upper()
                
            ancho_txt_color = fm.horizontalAdvance(txt_color)
            box_w = 30 + ancho_txt_color + 15 # Espacio para cuadro color + texto + padding
            box_h = 32
            
            # Evitar que se salga por la derecha o abajo de la pantalla
            if tx + box_w > self.viewport().width(): tx = self._pos_gotero.x() - box_w - 10
            if ty + box_h > self.viewport().height(): ty = self._pos_gotero.y() - box_h - 10
            
            tooltip_rect = QRect(tx, ty, box_w, box_h)
            
            # Fondo del Tooltip
            painter.setBrush(QColor(18, 18, 20, 240))
            painter.setPen(QPen(QColor(63, 65, 72), 1))
            painter.drawRoundedRect(tooltip_rect, 6, 6)
            
            # Cuadrito de Muestra de Color
            swatch_rect = QRect(tx + 8, ty + 8, 16, 16)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1)) # Borde blanco suave
            painter.drawRoundedRect(swatch_rect, 4, 4)
            
            # Texto del Código de Color
            painter.setPen(QColor(255, 255, 255))
            caja_txt = QRect(tx + 32, ty, ancho_txt_color + 10, box_h)
            painter.drawText(caja_txt, Qt.AlignmentFlag.AlignVCenter, txt_color)
            
            painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 🚀 Lo ponemos un poco más adentro (20px) para que no choque con los bordes
        if hasattr(self, 'perf_monitor'):
            self.perf_monitor.move(20, 20)
            self.perf_monitor.raise_() # Nos aseguramos que esté por encima de todo

    def mouseReleaseEvent(self, event):

        # 🚀 FINALIZACIÓN DEL DIBUJO CON PLUMA
        if getattr(self, 'modo_accion', None) == "DRAWING":
            self.modo_accion = None
            if hasattr(self, 'item_trazo_temp'):
                self.scene().removeItem(self.item_trazo_temp)
            
            # 🚀 LA CURA: Leemos el slider directamente desde la sub-barra premium
            ventana_principal = self.window()
            valor_suavizado = 8
            if hasattr(ventana_principal, 'main_canvas') and hasattr(ventana_principal.main_canvas, 'sub_toolbar_pen'):
                valor_suavizado = ventana_principal.main_canvas.sub_toolbar_pen.slider_suavizado.value()
            
            tolerancia = 0.2 + (valor_suavizado * 0.3)
            
            # Usamos el simplificador variable
            puntos_finales = self._simplificar_puntos_variable(self.puntos_trazo, epsilon=tolerancia)
            
            if len(puntos_finales) >= 2:
                # Ahora p es una tupla: (QPointF, grosor)
                min_x = min(p[0].x() for p in puntos_finales)
                max_x = max(p[0].x() for p in puntos_finales)
                min_y = min(p[0].y() for p in puntos_finales)
                max_y = max(p[0].y() for p in puntos_finales)
                
                w = max(max_x - min_x, 1.0)
                h = max(max_y - min_y, 1.0)
                cx, cy = min_x + w / 2.0, min_y + h / 2.0
                
                # 🚀 GUARDAMOS 3 DATOS EN LA BASE DE DATOS: [x, y, grosor]
                pts_relativos = [[round(p[0].x() - cx, 2), round(p[0].y() - cy, 2), round(p[1], 2)] for p in puntos_finales]
                
                # ==========================================
                # 🚀 LA MAGIA DE LA FUSIÓN: Sobreescribimos o creamos
                # ==========================================
                uid_existente = getattr(self, 'uid_en_edicion_trazo', None)
                color_trazo = getattr(self.parent_panel.properties_panel, 'color_actual', '#000000')
                
                if uid_existente:
                    uid = uid_existente
                    z_index = self.motor.elementos[uid].get('z_index', len(self.motor.elementos) * 10)
                    # Respetamos el color original porque estamos alargando una línea vieja
                    color_trazo = self.motor.elementos[uid].get('borde_color', color_trazo)
                else:
                    uid = self.motor.generar_uid(prefijo="pen")
                    z_index = len(self.motor.elementos) * 10
                
                self.motor.elementos[uid] = {
                    'tipo': 'Trazo',
                    'x': min_x, 'y': min_y, 'w': w, 'h': h,
                    'base_w': w, 'base_h': h,
                    'puntos': pts_relativos,
                    'borde_color': color_trazo,
                    'borde_grosor': 3.0,
                    'rotacion': 0.0, 'rot_3d_x': 0.0, 'rot_3d_y': 0.0,
                    'perspectiva': [[0,0],[0,0],[0,0],[0,0]],
                    'z_index': z_index
                }
                
                self.uid_en_edicion_trazo = None # Limpiamos memoria
                # ==========================================
                
                self.motor.registrar_punto_historial()
                self.uids_seleccionados = [uid]
                self.uid_activo = uid
                self.sincronizar_con_motor()
                self.dibujar_controles_seleccion()
                self.elemento_seleccionado.emit(uid)
                self.solicitar_actualizacion_masiva()
            else:
                # 🚀 PREVENCIÓN DE BUG: Si dio un micro-clic pero no dibujó nada, 
                # y habíamos ocultado una línea para editarla, la revivimos.
                uid_existente = getattr(self, 'uid_en_edicion_trazo', None)
                if uid_existente and uid_existente in self.items_ui:
                    self.items_ui[uid_existente].setVisible(True)
                self.uid_en_edicion_trazo = None
                
            return

        if event.button() == Qt.MouseButton.LeftButton:
            
            # 🚀 1. SI ESTÁBAMOS TRANSFORMANDO (Mover, Escalar, Rotar, 3D o EDITAR NODOS)
            if self.modo_accion in ["MOVE", "RESIZE", "ROTATE", "SHEAR", "ROTATE_3D", "MOVE_NODE"]:
                    
                accion_anterior = self.modo_accion
                self.modo_accion = None # Apagamos la acción actual
                
                # ==========================================================
                # 🚀 AUTO-AJUSTE DEL BOUNDING BOX (Lo que añadimos para que no se corte la forma)
                # ==========================================================
                if accion_anterior == "MOVE_NODE" and self.uid_activo:
                    elem = self.motor.elementos[self.uid_activo]
                    puntos = elem.get('puntos', [])
                    if puntos:
                        min_x = min(p[0] for p in puntos)
                        max_x = max(p[0] for p in puntos)
                        min_y = min(p[1] for p in puntos)
                        max_y = max(p[1] for p in puntos)
                        
                        w_nuevo = max(max_x - min_x, 1.0)
                        h_nuevo = max(max_y - min_y, 1.0)
                        cx_rel = min_x + w_nuevo / 2.0
                        cy_rel = min_y + h_nuevo / 2.0
                        
                        for p in puntos:
                            p[0] = round(p[0] - cx_rel, 2)
                            p[1] = round(p[1] - cy_rel, 2)
                            
                        angulo = float(elem.get('rotacion', 0.0))
                        rad = math.radians(angulo)
                        dx_glob = (cx_rel * math.cos(rad)) - (cy_rel * math.sin(rad))
                        dy_glob = (cx_rel * math.sin(rad)) + (cy_rel * math.cos(rad))
                            
                        elem['w'] = w_nuevo
                        elem['h'] = h_nuevo
                        elem['x'] = round(elem['x'] + dx_glob, 2)
                        elem['y'] = round(elem['y'] + dy_glob, 2)
                        elem['base_w'] = w_nuevo
                        elem['base_h'] = h_nuevo

                # 🧹 Limpiamos la memoria de la caja visual múltiple
                if hasattr(self, 'caja_multiple_fija'): del self.caja_multiple_fija
                if hasattr(self, 'angulo_multiple_fijo'): del self.angulo_multiple_fijo
                
                # ==========================================================
                # 🚀 AQUÍ VA LO NUEVO: HORNEADO Y CACHÉ
                # ==========================================================
                if self.uid_activo and self.uid_activo in self.items_ui:
                    item_real = self.items_ui[self.uid_activo]
                    item_real.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
                
                self.motor.registrar_punto_historial()
                
                # 🚀 HORNEADO FINAL: Sincronizamos las posiciones temporales en la matriz absoluta
                if accion_anterior == "MOVE" and getattr(self, 'hubo_arrastre', False):
                    uids_a_sincronizar = getattr(self, 'uids_arrastre', self.uids_seleccionados)
                    self.sincronizar_con_motor(uids_a_sincronizar)
                elif self.uid_activo:
                    self.sincronizar_con_motor([self.uid_activo])
                    
                # Volvemos a generar la caja azul en su posición final limpia
                self.dibujar_controles_seleccion()
                
                # Avisamos que hubo cambios para el sistema de guardado
                self.lienzo_modificado.emit()
                uid_emit = self.uid_activo if self.uid_activo else ""
                self.elemento_seleccionado.emit(uid_emit)
                
                # Lógica para abrir el editor de texto si diste clic en un texto
                if accion_anterior == "MOVE" and not getattr(self, 'hubo_arrastre', False):
                    if getattr(self, 'herramienta_activa', 'select') == 'text' and self.uid_activo:
                        elem_t = self.motor.elementos.get(self.uid_activo, {})
                        if elem_t.get('tipo') == 'Texto':
                            if hasattr(self.parent_panel.main_canvas, 'toolbar'):
                                self.parent_panel.main_canvas.toolbar._set_initial_tool("select")
                            QTimer.singleShot(50, lambda: self.abrir_editor_texto(self.uid_activo))
                            return
                
                super().mouseReleaseEvent(event)
                return
                
            # 🚀 2. SI NO HACÍAMOS NADA, ES SELECCIÓN DE ARRASTRE (Red Azul)
            elif not self.modo_accion:
                # 1. Atrapamos las coordenadas exactas de la red azul ANTES de que Qt la destruya
                lazo_viewport = self.rubberBandRect()
                lazo_scene = self.mapToScene(lazo_viewport).boundingRect()
                
                super().mouseReleaseEvent(event) 
                
                uids_atrapados = set() # Usamos set para evitar duplicados
                
                # 2. Si la red tiene un tamaño real (no fue un clic accidental)
                if lazo_viewport.width() > 5 and lazo_viewport.height() > 5:
                    # Buscamos los objetos usando colisión de cajas (Ultra rápido)
                    items_atrapados = self.scene().items(lazo_scene, Qt.ItemSelectionMode.IntersectsItemBoundingRect)
                    
                    for item in items_atrapados:
                        uid = item.data(100) 
                        if uid and uid in self.motor.elementos:
                            elem = self.motor.elementos[uid]
                            uid_padre = elem.get('parent_marco')
                            
                            # Subimos al ancestro más viejo si es un grupo anidado
                            while uid_padre and uid_padre in self.motor.elementos:
                                uid = uid_padre
                                uid_padre = self.motor.elementos[uid].get('parent_marco')
                                
                            uids_atrapados.add(uid)
                            
                # Limpiamos memorias nativas por seguridad
                self.scene().clearSelection()
                        
                if uids_atrapados:
                    self.uids_seleccionados = list(uids_atrapados)
                    self.uid_activo = self.uids_seleccionados[-1] 
                    
                    self.dibujar_controles_seleccion()
                    self.elemento_seleccionado.emit(self.uid_activo)
                else:
                    self.uids_seleccionados = []
                    self.uid_activo = None
                    self.dibujar_controles_seleccion()
                    self.elemento_seleccionado.emit("")
                return

        self.modo_accion = None
        super().mouseReleaseEvent(event)

        # 🚀 REINICIO DE PUNTERO MULTI-HERRAMIENTA AL SOLTAR EL CLIC
        herramienta = getattr(self, 'herramienta_activa', 'select')

        if herramienta == "hand":
            self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
        elif herramienta == "text":
            self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        elif herramienta == "pen" or herramienta == "shape":
            self.viewport().setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)

    def centrar_y_encajar(self):
        """Calcula el tamaño de la pantalla, ajusta el zoom al 85% y centra la hoja."""
        if self.motor.w_pdf == 0 or self.motor.h_pdf == 0: return
        
        # 1. Obtenemos el tamaño real de la vista en tu monitor
        view_w = self.viewport().width()
        view_h = self.viewport().height()
        
        # Si la ventana aún se está construyendo (mide menos de 100px), lo intentamos de nuevo en 50ms
        if view_w < 100 or view_h < 100:
            QTimer.singleShot(50, self.centrar_y_encajar)
            return

        # 2. Calculamos el zoom perfecto para que la hoja ocupe el 85% del espacio visual
        margen = 0.85 
        factor_w = (view_w * margen) / self.motor.w_pdf
        factor_h = (view_h * margen) / self.motor.h_pdf
        
        # Tomamos el factor más pequeño para asegurar que no se corte por ningún lado
        nuevo_zoom = min(factor_w, factor_h)
        
        # 3. Aplicamos el zoom matemáticamente
        self.resetTransform()
        self.scale(nuevo_zoom, nuevo_zoom)
        self.zoom = nuevo_zoom # Sincronizamos tu variable interna
        
        # 4. Apuntamos la cámara exactamente al centro de la hoja blanca
        self.centerOn(self.motor.w_pdf / 2.0, self.motor.h_pdf / 2.0)
        
        # Redibujamos la caja azul si hay algo seleccionado para que sus controles no queden gigantes
        if self.uid_activo:
            self.dibujar_controles_seleccion()

    def solicitar_actualizacion_masiva(self):
        """Acumula llamadas para evitar lag del Panel de Capas"""
        if not hasattr(self, '_timer_masivo'):
            self._timer_masivo = QTimer(self)
            self._timer_masivo.setSingleShot(True)
            self._timer_masivo.timeout.connect(self._ejecutar_actualizacion_masiva)
        self._timer_masivo.start(300) # 🚀 Espera estricta de 300ms a que sueltes la tecla

    def _ejecutar_actualizacion_masiva(self):
        
        if hasattr(self, 'parent_panel'):
            # 🚀 SEGURO DE VIDA: Forzamos al lienzo a pintar todo lo que falte
            self.sincronizar_con_motor()
            self.dibujar_controles_seleccion()
            # Y luego actualizamos el panel izquierdo
            self.parent_panel.window()._refrescar_panel_capas() 

        # =========================================================
        # 🚀 LA CURA DEL MICRO-TIRÓN (Pre-Calentamiento del BSP Tree)
        # Le hacemos una "pregunta falsa" al motor de colisiones pidiéndole
        # que busque objetos en un píxel invisible (0,0). Esto obliga a Qt 
        # a indexar toda la pantalla AHORA MISMO en silencio. 
        # Así, al arrastrar el ratón, el mapa ya estará procesado y a 120 FPS.
        # =========================================================
        from PyQt6.QtCore import QRectF
        self.scene().items(QRectF(0, 0, 1, 1))

        self.lienzo_modificado.emit()

    def keyPressEvent(self, event):
        """Atajos de Teclado Premium: Paneo, Copiar, Pegar, Duplicar, Deshacer, Rehacer y Eliminar"""

        if event.key() == Qt.Key.Key_S: self.tecla_s_presionada = True
        if event.key() == Qt.Key.Key_A: self.tecla_a_presionada = True
        
        # 🚀 0. PANEO NATIVO (Espacio) - Motor C++
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat() and not getattr(self, 'editor_flotante', None):
            self.setInteractive(False)
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            event.accept()
            return

        # CANCELAR MIRA ÓPTICA CON ESCAPE
        if event.key() == Qt.Key.Key_Escape and getattr(self, "modo_accion", None) in ["TARGET_DELANTE", "TARGET_DETRAS"]:
            self.modo_accion = None
            self.uid_objetivo_origen = None
            self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        mods = event.modifiers()
        is_ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)

        # 🚀 ATAJOS DE HERRAMIENTAS (V, H, T, P)
        if not getattr(self, 'editor_flotante', None) and not is_ctrl:
            if event.key() == Qt.Key.Key_V:
                if hasattr(self.parent_panel, 'main_canvas'): self.parent_panel.main_canvas.toolbar._set_initial_tool("select")
                event.accept()
                return
            elif event.key() == Qt.Key.Key_N: # 🚀 NUEVO ATAJO
                if hasattr(self.parent_panel, 'main_canvas'): self.parent_panel.main_canvas.toolbar._set_initial_tool("node_edit")
                event.accept(); return
            elif event.key() == Qt.Key.Key_H:
                if hasattr(self.parent_panel, 'main_canvas'): self.parent_panel.main_canvas.toolbar._set_initial_tool("hand")
                event.accept()
                return
            elif event.key() == Qt.Key.Key_T:
                if hasattr(self.parent_panel, 'main_canvas'): self.parent_panel.main_canvas.toolbar._set_initial_tool("text")
                event.accept()
                return
            elif event.key() == Qt.Key.Key_P:
                if hasattr(self.parent_panel, 'main_canvas'): self.parent_panel.main_canvas.toolbar._set_initial_tool("pen")
                event.accept()
                return
            elif event.key() == Qt.Key.Key_I:
                if hasattr(self.parent_panel, 'main_canvas'): self.parent_panel.main_canvas.toolbar._set_initial_tool("eyedropper")
                event.accept(); return

        # 🚀 1. COPIAR (Ctrl + C) 
        if is_ctrl and event.key() == Qt.Key.Key_C:
            self._ejecutar_copiar()
            event.accept()
            return

        # 🚀 2. PEGAR (Ctrl + V) 
        elif is_ctrl and event.key() == Qt.Key.Key_V:
            self._ejecutar_pegar() 
            event.accept()
            return

        # 🚀 3. DUPLICAR RÁPIDO (Ctrl + D)
        elif is_ctrl and event.key() == Qt.Key.Key_D:
            
            if self.uids_seleccionados:
                if not event.isAutoRepeat():
                    self.motor.registrar_punto_historial() 
                    
                uids_viejos = set(self.motor.elementos.keys())
                
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                
                try:
                    nuevos_uids = []
                    for uid_sel in self.uids_seleccionados:
                        nuevo_uid = self.motor.duplicar_elemento(uid_sel)
                        if nuevo_uid: nuevos_uids.append(nuevo_uid)
                
                    uids_nuevos_totales = list(set(self.motor.elementos.keys()) - uids_viejos)
                    
                    if nuevos_uids:
                        self.uids_seleccionados = nuevos_uids
                        self.uid_activo = nuevos_uids[-1] 
                        self.sincronizar_con_motor(uids_nuevos_totales) 
                        self.dibujar_controles_seleccion()
                        self.elemento_seleccionado.emit(self.uid_activo)
                        self.solicitar_actualizacion_masiva()
                        
                finally:
                    QApplication.restoreOverrideCursor()
                    
            event.accept()
            return

        # 🚀 4. DESHACER VISUAL (Ctrl + Z)
        elif is_ctrl and event.key() == Qt.Key.Key_Z:
            if self.motor.deshacer():
                self.uids_seleccionados = [] 
                self.uid_activo = None 
                self.sincronizar_con_motor() # 🚀 DIBUJA AL INSTANTE
                self.dibujar_controles_seleccion()
                self.elemento_seleccionado.emit("") 
                self.solicitar_actualizacion_masiva()
            event.accept()
            return

        # 🚀 5. REHACER VISUAL (Ctrl + Y)
        elif is_ctrl and event.key() == Qt.Key.Key_Y:
            if self.motor.rehacer():
                self.uids_seleccionados = [] 
                self.uid_activo = None 
                self.sincronizar_con_motor() # 🚀 DIBUJA AL INSTANTE
                self.dibujar_controles_seleccion()
                self.elemento_seleccionado.emit("") 
                self.solicitar_actualizacion_masiva()
            event.accept()
            return

        # 🚀 6. AGRUPAR (Ctrl + G)
        elif is_ctrl and event.key() == Qt.Key.Key_G and not (mods & Qt.KeyboardModifier.ShiftModifier):
            if len(self.uids_seleccionados) > 1:
                self.motor.registrar_punto_historial()
                nuevo_grupo_uid = f"grupo_{int(time.time() * 1000)}"
                
                caja_grupo = self.motor.obtener_caja_multiple(self.uids_seleccionados)
                if caja_grupo:
                    self.motor.agregar_elemento(
                        nuevo_grupo_uid, "Marco", 
                        x=caja_grupo['x'], y=caja_grupo['y'], 
                        w=caja_grupo['w'], h=caja_grupo['h'],
                        nombre_capa="Grupo", borde_grosor=0, color_tx=None
                    )
                    for uid_sel in self.uids_seleccionados:
                        self.motor.insertar_en_marco(uid_sel, nuevo_grupo_uid)
                    
                    self.uids_seleccionados = [nuevo_grupo_uid]
                    self.uid_activo = nuevo_grupo_uid
                    
                    self.sincronizar_con_motor() # 🚀 DIBUJA AL INSTANTE
                    self.dibujar_controles_seleccion()
                    
                    self.elemento_seleccionado.emit(self.uid_activo)
                    self.solicitar_actualizacion_masiva()
            event.accept()
            return

        # 🚀 7. DESAGRUPAR (Ctrl + Shift + G)
        elif is_ctrl and (mods & Qt.KeyboardModifier.ShiftModifier) and event.key() == Qt.Key.Key_G:
            if len(self.uids_seleccionados) == 1:
                uid_grupo = self.uids_seleccionados[0]
                elem_grupo = self.motor.elementos.get(uid_grupo)
                
                if not elem_grupo: return
                
                if elem_grupo.get('tipo') == 'Marco':
                    self.motor.registrar_punto_historial()
                    uids_restaurados = []
                    
                    # 🚀 HERENCIA DIRECTA DE PARÁMETROS (La Cura del Estiramiento)
                    for uid_hijo, elem_hijo in list(self.motor.elementos.items()):
                        if elem_hijo.get('parent_marco') == uid_grupo:
                            
                            # 1. Obtenemos el centro real global en la pantalla (píxel exacto)
                            t_final = self._obtener_matriz_acumulada(uid_hijo)
                            from PyQt6.QtCore import QPointF
                            centro_global = t_final.map(QPointF(0, 0))
                            
                            # 2. Calculamos sus nuevas coordenadas X, Y para mantenerlo en ese sitio
                            caja_hijo = self.motor.obtener_caja_elemento(uid_hijo)
                            w_hijo = float(caja_hijo.get('w') or 0.0)
                            h_hijo = float(caja_hijo.get('h') or 0.0)
                            
                            nuevo_x = centro_global.x() - (w_hijo / 2.0)
                            nuevo_y = self.motor.h_pdf - (centro_global.y() + (h_hijo / 2.0))
                            
                            # 3. 🚀 TRANSFERENCIA MATEMÁTICA AL PANEL DE PROPIEDADES
                            # Al sumar los valores, el usuario verá las rotaciones en el panel
                            # y podrá ponerlas a 0 manualmente para "volver a como estaban".
                            rot_p = float(elem_grupo.get('rotacion', 0.0))
                            rot3dx_p = float(elem_grupo.get('rot_3d_x', 0.0))
                            rot3dy_p = float(elem_grupo.get('rot_3d_y', 0.0))
                            
                            elem_hijo['rotacion'] = float(elem_hijo.get('rotacion', 0.0)) + rot_p
                            elem_hijo['rot_3d_x'] = float(elem_hijo.get('rot_3d_x', 0.0)) + rot3dx_p
                            elem_hijo['rot_3d_y'] = float(elem_hijo.get('rot_3d_y', 0.0)) + rot3dy_p
                            
                            # 4. Transferencia Proporcional de Perspectiva
                            # Si el padre tenía perspectiva, la achicamos para que no deforme gigante al hijo
                            persp_p = elem_grupo.get('perspectiva')
                            if persp_p and any(pt != [0,0] for pt in persp_p):
                                caja_padre = self.motor.obtener_caja_elemento(uid_grupo)
                                w_padre = float(caja_padre.get('w') or 1.0)
                                h_padre = float(caja_padre.get('h') or 1.0)
                                
                                ratio_w = w_hijo / w_padre if w_padre > 0 else 1.0
                                ratio_h = h_hijo / h_padre if h_padre > 0 else 1.0
                                
                                persp_h = elem_hijo.get('perspectiva', [[0,0], [0,0], [0,0], [0,0]])
                                nueva_persp = []
                                for i in range(4):
                                    dx = persp_h[i][0] + (persp_p[i][0] * ratio_w)
                                    dy = persp_h[i][1] + (persp_p[i][1] * ratio_h)
                                    nueva_persp.append([round(dx, 2), round(dy, 2)])
                                elem_hijo['perspectiva'] = nueva_persp
                            
                            # 5. Desvinculamos del padre de forma segura
                            elem_hijo['parent_marco'] = None 
                            elem_hijo['x'] = nuevo_x
                            elem_hijo['y'] = nuevo_y
                            
                            uids_restaurados.append(uid_hijo)
                            
                    if uids_restaurados:
                        self.motor.eliminar_elemento(uid_grupo) 
                        self.uids_seleccionados = uids_restaurados
                        self.uid_activo = uids_restaurados[-1] if uids_restaurados else None
                        
                        self.sincronizar_con_motor() # Dibuja al instante
                        self.dibujar_controles_seleccion()
                        
                        self.elemento_seleccionado.emit(self.uid_activo)
                        self.solicitar_actualizacion_masiva()

                        
                elif elem_grupo.get('tipo') == 'Foto' and str(elem_grupo.get('contenido', '')).lower().endswith('.svg'):
                    self.motor.registrar_punto_historial()
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    QApplication.processEvents() 
                    nuevo_id_grupo = self.motor.desagrupar_svg(uid_grupo)
                    QApplication.restoreOverrideCursor() 
                    
                    if nuevo_id_grupo:
                        self.uids_seleccionados = [nuevo_id_grupo]
                        self.uid_activo = nuevo_id_grupo
                        
                        self.sincronizar_con_motor() # 🚀 DIBUJA AL INSTANTE
                        self.dibujar_controles_seleccion()
                        
                        self.elemento_seleccionado.emit(self.uid_activo)
                        self.solicitar_actualizacion_masiva()
            event.accept()
            return

        # 🚀 8. ELIMINAR (Suprimir / Backspace)
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            
            if self.uids_seleccionados:
                if not event.isAutoRepeat():
                    self.motor.registrar_punto_historial() 
                
                # ==========================================
                # FASE 1: OPTIMISTIC UI (Borrado Visual Instantáneo)
                # ==========================================
                # 1. Destruimos la caja azul de controles para que desaparezca YA
                if hasattr(self, 'grupo_controles') and self.grupo_controles in self.scene().items():
                    self.scene().removeItem(self.grupo_controles)
                    
                # 2. Desaparecemos los objetos del lienzo visual inmediatamente
                for uid_sel in self.uids_seleccionados:
                    if uid_sel in self.items_ui:
                        item_ui = self.items_ui.pop(uid_sel)
                        self.scene().removeItem(item_ui)
                        
                # 3. Forzamos a la pantalla a repintarse vacía al instante
                self.viewport().repaint() 
                
                # ==========================================
                # FASE 2: TRABAJO PESADO EN SEGUNDO PLANO
                # ==========================================
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                
                try:
                    # 4. Le decimos al motor matemático que destruya los datos y limpie la RAM
                    for uid_sel in self.uids_seleccionados:
                        self.motor.eliminar_elemento(uid_sel, limpiar_cache=False)
                    self.motor.limpiar_cache_imagenes()
                    
                    self.uids_seleccionados = []
                    self.uid_activo = None
                    
                    # 5. Emitimos señales y actualizamos en silencio
                    self.dibujar_controles_seleccion()
                    self.elemento_seleccionado.emit("") 
                    self.solicitar_actualizacion_masiva() 
                finally:
                    # 6. Apagamos el reloj de arena
                    QApplication.restoreOverrideCursor()
                    
            event.accept()
            return
            
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_S: self.tecla_s_presionada = False
        if event.key() == Qt.Key.Key_A: self.tecla_a_presionada = False
        
        # 🚀 SOLUCIÓN AL BUG DEL ESPACIO (PANNING)
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            # Le preguntamos a nuestro propio lienzo qué herramienta está activa
            if getattr(self, 'herramienta_activa', 'select') == "hand":
                self.viewport().setCursor(Qt.CursorShape.OpenHandCursor)
                if hasattr(self, 'setDragMode'):
                    self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
                    self.setInteractive(False) # 🚀 Mantenemos apagado porque la herramienta mano sigue activa
            else:
                self.viewport().setCursor(Qt.CursorShape.ArrowCursor)
                if hasattr(self, 'setDragMode'):
                    self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                    self.setInteractive(True) # 🚀 VOLVEMOS A ENCENDER AL SOLTAR ESPACIO
                    
            event.accept()
            return
            
        # Para cualquier otra tecla que no sea el espacio
        super().keyReleaseEvent(event) 

    # =======================================================
    # 🚀 MOTOR DE TINTA DINÁMICA (GROSOR VARIABLE)
    # =======================================================
    def _simplificar_puntos_variable(self, puntos_w, epsilon=1.0):
        """Simplifica la curva pero ahora respeta el grosor (x, y, grosor)"""
        from PyQt6.QtCore import QLineF
        if len(puntos_w) < 3: return puntos_w

        def d_espacio(p_w, a_w, b_w):
            p, a, b = p_w[0], a_w[0], b_w[0]
            if a == b: return QLineF(p, a).length()
            dist = abs((b.x() - a.x()) * (a.y() - p.y()) - (a.x() - p.x()) * (b.y() - a.y()))
            norma = ((b.x() - a.x())**2 + (b.y() - a.y())**2)**0.5
            return dist / norma if norma > 0 else 0

        dmax, index, end = 0.0, 0, len(puntos_w) - 1
        for i in range(1, end):
            d = d_espacio(puntos_w[i], puntos_w[0], puntos_w[end])
            if d > dmax: index, dmax = i, d

        if dmax > epsilon:
            rec1 = self._simplificar_puntos_variable(puntos_w[:index+1], epsilon)
            rec2 = self._simplificar_puntos_variable(puntos_w[index:], epsilon)
            return rec1[:-1] + rec2
        else:
            return [puntos_w[0], puntos_w[end]]

    def _generar_patron_variable(self, puntos_con_grosor):
        """Convierte la ruta en Forma 2D usando nuestro propio Teselador Paramétrico.
           Miter Robusto (Anti-Spike), Cúpulas perfectas y Rendimiento Máximo."""
        from PyQt6.QtGui import QPainterPath, QPolygonF
        from PyQt6.QtCore import QPointF, Qt
        
        path_final = QPainterPath()
        path_final.setFillRule(Qt.FillRule.WindingFill) 
        
        if len(puntos_con_grosor) < 2:
            if puntos_con_grosor:
                pt, w = puntos_con_grosor[0]
                path_final.addEllipse(pt.x() - w/2, pt.y() - w/2, w, w)
            return path_final

        # =======================================================
        # 🚀 1. MUESTREO MATEMÁTICO DE PRECISIÓN ABSOLUTA
        # =======================================================
        puntos_finos = [puntos_con_grosor[0]] 
        
        for i in range(1, len(puntos_con_grosor) - 1):
            p0, w0 = puntos_finos[-1] 
            p1, w1 = puntos_con_grosor[i] 
            p2_orig, w2_orig = puntos_con_grosor[i+1]

            mid_x = (p1.x() + p2_orig.x()) / 2.0
            mid_y = (p1.y() + p2_orig.y()) / 2.0
            mid_w = (w1 + w2_orig) / 2.0
            p2 = QPointF(mid_x, mid_y)
            w2 = mid_w

            d1 = math.hypot(p1.x() - p0.x(), p1.y() - p0.y())
            d2 = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
            d3 = math.hypot(p2.x() - p0.x(), p2.y() - p0.y())
            
            longitud_curva = (d1 + d2 + d3) / 2.0
            pasos = max(3, min(int(longitud_curva / 8.0), 30))

            for j in range(1, pasos + 1):
                t = j / float(pasos)
                mt = 1.0 - t
                x = (mt * mt * p0.x()) + (2 * mt * t * p1.x()) + (t * t * p2.x())
                y = (mt * mt * p0.y()) + (2 * mt * t * p1.y()) + (t * t * p2.y())
                w = (mt * mt * w0) + (2 * mt * t * w1) + (t * t * w2)
                puntos_finos.append((QPointF(x, y), w))

        p_ultimo, w_ultimo = puntos_finos[-1]
        p_final_real, w_final_real = puntos_con_grosor[-1]
        dist_fin = math.hypot(p_final_real.x() - p_ultimo.x(), p_final_real.y() - p_ultimo.y())
        pasos_fin = max(2, min(int(dist_fin / 8.0), 15))

        for j in range(1, pasos_fin + 1):
            t = j / float(pasos_fin)
            x = p_ultimo.x() + (p_final_real.x() - p_ultimo.x()) * t
            y = p_ultimo.y() + (p_final_real.y() - p_ultimo.y()) * t
            w = w_ultimo + (w_final_real - w_ultimo) * t
            puntos_finos.append((QPointF(x, y), w))

        # =======================================================
        # 🚀 2. EXTRUSIÓN MATEMÁTICA ROBUSTA (Cero Picos Opuestos)
        # =======================================================
        borde_izq = []
        borde_der = []

        total = len(puntos_finos)
        for i in range(total):
            pt, w = puntos_finos[i]

            if i == 0:
                sig = puntos_finos[1][0]
                dx, dy = sig.x() - pt.x(), sig.y() - pt.y()
                l = math.hypot(dx, dy)
                vx, vy = (dx/l, dy/l) if l > 0 else (1, 0)
                nx, ny = -vy, vx
            elif i == total - 1:
                ant = puntos_finos[i-1][0]
                dx, dy = pt.x() - ant.x(), pt.y() - ant.y()
                l = math.hypot(dx, dy)
                vx, vy = (dx/l, dy/l) if l > 0 else (1, 0)
                nx, ny = -vy, vx
            else:
                ant = puntos_finos[i-1][0]
                sig = puntos_finos[i+1][0]
                
                dx1, dy1 = pt.x() - ant.x(), pt.y() - ant.y()
                l1 = math.hypot(dx1, dy1)
                vx1, vy1 = (dx1/l1, dy1/l1) if l1 > 0 else (1, 0)
                
                dx2, dy2 = sig.x() - pt.x(), sig.y() - pt.y()
                l2 = math.hypot(dx2, dy2)
                vx2, vy2 = (dx2/l2, dy2/l2) if l2 > 0 else (1, 0)

                # 🚀 LA CURA DEL PICO FANTASMA: Normales Promediadas
                # Calculamos la normal pura de cada segmento independiente
                n1x, n1y = -vy1, vx1
                n2x, n2y = -vy2, vx2
                
                # Promediamos ambas normales (Bisectriz perfecta e infalible)
                nx = (n1x + n2x) / 2.0
                ny = (n1y + n2y) / 2.0
                
                l_sq = nx*nx + ny*ny
                
                # Si la curva da una vuelta de 180° extrema, l_sq se acerca a 0.
                if l_sq > 0.01:
                    # Aplicar la expansión del Miter (Grosor)
                    nx /= l_sq
                    ny /= l_sq
                    
                    # Limitador de picos inquebrantable (Max 2.5x el grosor original)
                    miter_len = 1.0 / math.sqrt(l_sq)
                    if miter_len > 2.5:
                        nx = nx * (2.5 / miter_len)
                        ny = ny * (2.5 / miter_len)
                else:
                    # En una vuelta de horquilla extrema, simplemente cerramos el ángulo a mano
                    nx, ny = -vy1, vx1

            r = w / 2.0
            borde_izq.append(QPointF(pt.x() + nx * r, pt.y() + ny * r))
            borde_der.append(QPointF(pt.x() - nx * r, pt.y() - ny * r))

        # =======================================================
        # 🚀 3. CÚPULAS TRIGONOMÉTRICAS DE ALTA PRECISIÓN
        # =======================================================
        def generar_tapa(pt_centro, radio, es_inicio):
            arco = []
            # 🚀 Reducimos los puntos de la cúpula de 0.8 a 0.4
            pasos = max(4, int(radio * 0.4))
            
            if es_inicio:
                sig = puntos_finos[1][0]
                dx, dy = sig.x() - pt_centro.x(), sig.y() - pt_centro.y()
                ang_tangente = math.atan2(dy, dx)
                
                # 🚀 LA CURA DEL "PAC-MAN": Empezar en +pi/2 para ir por DETRÁS de la línea
                ang_start = ang_tangente + (math.pi / 2.0) 
                ang_sweep = math.pi 
            else:
                ant = puntos_finos[-2][0]
                dx, dy = pt_centro.x() - ant.x(), pt_centro.y() - ant.y()
                ang_tangente = math.atan2(dy, dx)
                
                # Para el final, empezamos en -pi/2 y vamos por el FRENTE
                ang_start = ang_tangente - (math.pi / 2.0) 
                ang_sweep = math.pi 

            for j in range(pasos + 1):
                t = j / float(pasos)
                ang = ang_start + (ang_sweep * t)
                arco.append(QPointF(pt_centro.x() + radio * math.cos(ang), pt_centro.y() + radio * math.sin(ang)))
            return arco

        # =======================================================
        # 🚀 4. ENSAMBLAJE FINAL DEL POLÍGONO MAESTRO
        # =======================================================
        poly_maestro = borde_izq[:]
        
        # Tapamos la punta final
        pt_fin, w_fin = puntos_finos[-1]
        poly_maestro.extend(generar_tapa(pt_fin, w_fin / 2.0, es_inicio=False))
        
        # Volvemos por el borde derecho
        poly_maestro.extend(borde_der[::-1])
        
        # Tapamos el inicio
        pt_ini, w_ini = puntos_finos[0]
        poly_maestro.extend(generar_tapa(pt_ini, w_ini / 2.0, es_inicio=True))

        path_final.addPolygon(QPolygonF(poly_maestro))
        
        return path_final

class DocumentTab(QWidget):
    """Una pestaña independiente que contiene su propio Motor y su propio Lienzo"""
    def __init__(self, main_studio, mapa_fuentes, ruta_archivo=None):
        super().__init__()
        self.main_studio = main_studio
        self.motor = RectorOP() 
        self.ruta_archivo = ruta_archivo
        self.modificado = False
        
        if ruta_archivo:
            self.motor.cargar_proyecto(ruta_archivo)
            # 🚀 CORRECCIÓN: Extraemos el nombre limpio sin el ".diseno"
            self.nombre_archivo = os.path.splitext(os.path.basename(ruta_archivo))[0]
        else:
            self.motor.crear_lienzo_vacio(800, 600) 
            self.nombre_archivo = "Diseño Sin Título"
            
        self.scene = QGraphicsScene()
        # 🚀 CINTURÓN NEGRO: BspTreeIndex agrupa los objetos espacialmente.
        # Hace que el lazo azul no se congele al tener cientos de objetos.
        self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.BspTreeIndex)
        
        # Pasamos main_studio para que el lienzo pueda avisarle de los cambios
        self.canvas_view = InteractiveCanvasView(self.scene, self.motor, self.main_studio, mapa_fuentes)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas_view) # El lienzo ocupa toda la pestaña
        
        # 🚀 LA LÍNEA MÁGICA QUE FALTABA
        # Le decimos al lienzo que lea la memoria del motor y pinte todo de inmediato
        self.actualizar_lienzo()
        
    def actualizar_lienzo(self):
        self.canvas_view.sincronizar_con_motor()
        self.canvas_view.dibujar_controles_seleccion()

class FloatingToolBar(QFrame):
    """Barra de herramientas flotante central inferior con diseño cuadrado redondeado"""
    tool_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.herramienta_actual = "select"
        
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1B1E;
                border: 1px solid #3F4148;
                border-radius: 12px;
            }
        """)
        apply_shadow(self, radius=15, offset_y=8)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.tools = [
            ("select", "fa5s.mouse-pointer", "Selección (V)"),
            ("node_edit", "fa5s.project-diagram", "Editar Nodos (N)"),
            ("hand", "fa5s.hand-paper", "Mano (H)"),
            ("text", "fa5s.font", "Texto (T)"),
            ("eyedropper", "fa5s.eye-dropper", "Cuentagotas (I)"),
            ("pen", "fa5s.pen-nib", "Pluma (P)"),
            ("3d", "fa5s.cube", "Inclinación 3D")
        ]

        for tool_id, icon, tooltip in self.tools:
            btn = QPushButton()
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setProperty("tool_id", tool_id)
            
            # 🚀 AHORA LA PLUMA BRILLA COMO LAS DEMÁS
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 8px; padding: 0px; }}
                QPushButton:hover {{ background-color: #2A2B31; border: 1px solid #3F4148; }}
                QPushButton:checked {{ background-color: {COLOR_ACCENT}; }}
            """)
            
            self.btn_group.addButton(btn)
            layout.addWidget(btn)

        self.btn_group.buttonClicked.connect(self._on_tool_clicked)
        self._set_initial_tool("select")

    def _set_initial_tool(self, tool_id):
        btn = next(b for b in self.btn_group.buttons() if b.property("tool_id") == tool_id)
        btn.setChecked(True)
        self._on_tool_clicked(btn)

    def _on_tool_clicked(self, btn):
        self.herramienta_actual = btn.property("tool_id")
        self._update_icons()
        self.tool_changed.emit(self.herramienta_actual)

    def _update_icons(self):
        for btn in self.btn_group.buttons():
            icon_name = next(t[1] for t in self.tools if t[0] == btn.property("tool_id"))
            # Ahora todos se ponen blancos al seleccionarse
            color = "#FFFFFF" if btn.isChecked() else ICON_MUTED
            btn.setIcon(qta.icon(icon_name, color=color, size=QSize(18, 18)))

class PenSubToolBar(QFrame):
    """Sub-barra flotante que aparece al seleccionar la herramienta Pluma"""
    pincel_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pincel_actual = "boligrafo"
        
        # Diseño ligeramente más pequeño y sutil que la barra principal
        self.setStyleSheet("""
            QFrame {
                background-color: #202126; /* Un gris ligeramente distinto para diferenciarla */
                border: 1px solid #2A2B31;
                border-radius: 10px;
            }
        """)
        apply_shadow(self, radius=10, offset_y=4)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        # Diferentes tipos de plumas/pinceles
        self.pinceles = [
            ("boligrafo", "fa5s.pen", "Bolígrafo (Trazos finos)"),
            ("rotulador", "fa5s.marker", "Rotulador (Trazos gruesos)"),
            ("resaltador", "fa5s.highlighter", "Resaltador (Translúcido)"),
            ("borrador", "fa5s.eraser", "Borrador")
        ]

        for brush_id, icon, tooltip in self.pinceles:
            btn = QPushButton()
            btn.setFixedSize(30, 30) # Un poco más pequeños que los principales
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setProperty("brush_id", brush_id)
            
            # Hover sutil, Checked con color de acento pero sin relleno fuerte
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #2A2B31; }}
                QPushButton:checked {{ background-color: rgba(254, 89, 52, 0.15); border: 1px solid {COLOR_ACCENT}; }}
            """)
            
            self.btn_group.addButton(btn)
            layout.addWidget(btn)

        self.btn_group.buttonClicked.connect(self._on_brush_clicked)
        
        # Seleccionamos el bolígrafo por defecto
        btn_default = next(b for b in self.btn_group.buttons() if b.property("brush_id") == "boligrafo")
        btn_default.setChecked(True)
        self._update_icons()

        # ==========================================
        # 🚀 LA CURA: SLIDER PREMIUM INTEGRADO
        # ==========================================
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.VLine)
        separador.setStyleSheet("background-color: #2A2B31; max-height: 20px;")
        layout.addWidget(separador)

        lbl_suavizado = QLabel("Suavizado")
        lbl_suavizado.setStyleSheet("color: #85868A; font-size: 11px; font-weight: bold; margin-left: 5px;")
        layout.addWidget(lbl_suavizado)

        self.slider_suavizado = QSlider(Qt.Orientation.Horizontal)
        self.slider_suavizado.setRange(0, 20)
        self.slider_suavizado.setValue(8)
        self.slider_suavizado.setFixedWidth(80)
        self.slider_suavizado.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider_suavizado.setStyleSheet(f"""
            QSlider::groove:horizontal {{ border: none; background: #18191D; height: 4px; border-radius: 2px; }}
            QSlider::handle:horizontal {{ background: {COLOR_ACCENT}; border: none; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
            QSlider::handle:horizontal:hover {{ background: #FFFFFF; transform: scale(1.2); }}
        """)
        layout.addWidget(self.slider_suavizado)

    def _on_brush_clicked(self, btn):
        self.pincel_actual = btn.property("brush_id")
        self._update_icons()
        self.pincel_changed.emit(self.pincel_actual)

    def _update_icons(self):
        for btn in self.btn_group.buttons():
            icon_name = next(t[1] for t in self.pinceles if t[0] == btn.property("brush_id"))
            # El icono activo toma el color naranja, los inactivos gris
            color = COLOR_ACCENT if btn.isChecked() else ICON_MUTED
            btn.setIcon(qta.icon(icon_name, color=color, size=QSize(14, 14)))

    def reset_state(self):
        """🚀 Fuerza el reseteo al pincel por defecto al reabrir el panel"""
        btn_default = next(b for b in self.btn_group.buttons() if b.property("brush_id") == "boligrafo")
        if not btn_default.isChecked():
            btn_default.setChecked(True)
            self._on_brush_clicked(btn_default)

class ThreeDSubToolBar(QFrame):
    """Sub-barra flotante que aparece al seleccionar la herramienta 3D"""
    tool_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.herramienta_actual = "3d" # 🚀 CAMBIO 1: Ahora se llama "3d"
        
        self.setStyleSheet("""
            QFrame {
                background-color: #202126;
                border: 1px solid #2A2B31;
                border-radius: 10px;
            }
        """)
        apply_shadow(self, radius=10, offset_y=4)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.herramientas = [
            ("3d", "fa5s.cube", "Rotación 3D"), # 🚀 CAMBIO 2: "3d"
            ("perspective", "fa5s.project-diagram", "Perspectiva Libre")
        ]

        for tool_id, icon, tooltip in self.herramientas:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setProperty("tool_id", tool_id)
            
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: 1px solid transparent; border-radius: 6px; }}
                QPushButton:hover {{ background-color: #2A2B31; }}
                QPushButton:checked {{ background-color: rgba(254, 89, 52, 0.15); border: 1px solid {COLOR_ACCENT}; }}
            """)
            
            self.btn_group.addButton(btn)
            layout.addWidget(btn)

        self.btn_group.buttonClicked.connect(self._on_tool_clicked)
        
        # 🚀 CAMBIO 3: Seleccionamos "3d" por defecto
        btn_default = next(b for b in self.btn_group.buttons() if b.property("tool_id") == "3d")
        btn_default.setChecked(True)
        self._update_icons()

    def _on_tool_clicked(self, btn):
        self.herramienta_actual = btn.property("tool_id")
        self._update_icons()
        self.tool_changed.emit(self.herramienta_actual)

    def _update_icons(self):
        for btn in self.btn_group.buttons():
            icon_name = next(t[1] for t in self.herramientas if t[0] == btn.property("tool_id"))
            color = COLOR_ACCENT if btn.isChecked() else ICON_MUTED
            btn.setIcon(qta.icon(icon_name, color=color, size=QSize(14, 14)))

    def reset_state(self):
        """🚀 Fuerza el reseteo a la herramienta por defecto al reabrir el panel"""
        btn_default = next(b for b in self.btn_group.buttons() if b.property("tool_id") == "3d")
        if not btn_default.isChecked():
            btn_default.setChecked(True)
            self._on_tool_clicked(btn_default)

class MainCanvasPanel(QFrame):
    """Columna 3: El Lienzo Real conectado al Motor"""
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(10)

        # Header de Pestañas y Botones
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet(f"background-color: {BG_CANVAS_HEADER}; border-radius: 10px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # 🚀 EL GESTOR DE PESTAÑAS REAL
        self.tabs_canvas = QTabWidget()
        self.tabs_canvas.setTabsClosable(True) 
        self.tabs_canvas.setMovable(True) # 🚀 MAGIA: Permite arrastrar para reordenar pestañas
        # 🚀 LA CURA DE LA MANO: Solo la barra de pestañas (tabBar) tendrá la mano
        self.tabs_canvas.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        self.tabs_canvas.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; background-color: transparent; }} 
            QTabBar::tab {{ 
                background-color: #202126; 
                color: {TEXT_MUTED}; 
                padding: 10px 35px 10px 15px; 
                border-top-left-radius: 8px; 
                border-top-right-radius: 8px; 
                margin-right: 0px; /* 🚀 Juntamos las pestañas (antes 4px) */
                font-size: 13px; 
                font-weight: bold; 
                border-bottom: 2px solid transparent; 
            }} 
            QTabBar::tab:selected {{ 
                background-color: {BG_CANVAS_HEADER}; 
                color: {TEXT_MAIN}; 
                border-bottom: 2px solid {COLOR_ACCENT}; 
            }} 
            QTabBar::tab:hover:!selected {{ 
                background-color: #282A30; 
                color: {TEXT_MAIN}; 
            }}
        """)
        header_layout.addWidget(self.tabs_canvas)
        
        # --- BOTONES DE ACCIÓN SUPERIOR ---
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        self.btn_new = QPushButton(" Nuevo")
        self.btn_new.setIcon(qta.icon('fa5s.plus', color=TEXT_MAIN))
        self.btn_new.setStyleSheet(f"QPushButton {{ background-color: #2A2B31; color: {TEXT_MAIN}; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; }} QPushButton:hover {{ background-color: #3F4148; }}")
        actions_layout.addWidget(self.btn_new)

        self.btn_open = QPushButton(" Abrir")
        self.btn_open.setIcon(qta.icon('fa5s.folder-open', color=TEXT_MAIN))
        self.btn_open.setStyleSheet(f"QPushButton {{ background-color: #2A2B31; color: {TEXT_MAIN}; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; }} QPushButton:hover {{ background-color: #3F4148; }}")
        actions_layout.addWidget(self.btn_open)

        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setIcon(qta.icon('fa5s.save', color=TEXT_MAIN))
        self.btn_save.setStyleSheet(f"QPushButton {{ background-color: #2A2B31; color: {TEXT_MAIN}; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; }} QPushButton:hover {{ background-color: #3F4148; }}")
        actions_layout.addWidget(self.btn_save)

        self.btn_import = QPushButton(" Importar")
        self.btn_import.setIcon(qta.icon('fa5s.file-import', color=TEXT_MAIN))
        self.btn_import.setStyleSheet(f"QPushButton {{ background-color: #2A2B31; color: {TEXT_MAIN}; border: none; border-radius: 6px; padding: 10px 15px; font-weight: bold; }} QPushButton:hover {{ background-color: #3F4148; }}")
        actions_layout.addWidget(self.btn_import)

        self.btn_export = QPushButton(" Exportar")
        self.btn_export.setIcon(qta.icon('fa5s.file-export', color=TEXT_MAIN))
        self.btn_export.setStyleSheet(f"QPushButton {{ background-color: {COLOR_ACCENT}; color: {TEXT_MAIN}; border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold; }} QPushButton:hover {{ background-color: #E04B2A; }}")
        actions_layout.addWidget(self.btn_export)
        
        header_layout.addLayout(actions_layout)
        layout.addWidget(header_frame)
        
        # 🚀 AÑADIMOS EL CONTENEDOR DE PESTAÑAS AL CUERPO
        layout.addWidget(self.tabs_canvas, stretch=1)

        # 🚀 AÑADE ESTO AL FINAL DEL __init__: Instanciamos la barra flotante
        self.toolbar = FloatingToolBar(self.tabs_canvas)
        self.toolbar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # 🚀 NUEVO: Instanciamos la sub-barra de pinceles oculta por defecto
        self.sub_toolbar_pen = PenSubToolBar(self.tabs_canvas)
        self.sub_toolbar_pen.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sub_toolbar_pen.hide()
        
        # 🚀 NUEVO: Instanciamos la sub-barra 3D oculta por defecto
        self.sub_toolbar_3d = ThreeDSubToolBar(self.tabs_canvas)
        self.sub_toolbar_3d.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sub_toolbar_3d.hide()
        
        # Conectamos un vigilante para mostrar/ocultar
        self.toolbar.tool_changed.connect(self._gestionar_sub_barras)

    def _gestionar_sub_barras(self, tool_id):
        """Muestra u oculta sub-menús dependiendo de la herramienta seleccionada"""
        if tool_id == "pen":
            self.sub_toolbar_pen.show()
            self.sub_toolbar_pen.raise_()
            self.sub_toolbar_3d.hide()
            self.sub_toolbar_pen.reset_state() # 🚀 RESETEO AUTOMÁTICO
            
        elif tool_id == "3d":
            self.sub_toolbar_3d.show()
            self.sub_toolbar_3d.raise_()
            self.sub_toolbar_pen.hide()
            self.sub_toolbar_3d.reset_state() # 🚀 RESETEO AUTOMÁTICO
            
        else:
            self.sub_toolbar_pen.hide()
            self.sub_toolbar_3d.hide()

    def actualizar_lienzo(self):
        """Redirige la orden de redibujado EXCLUSIVAMENTE a la pestaña que estás viendo"""
        tab = self.tabs_canvas.currentWidget()
        if tab:
            tab.actualizar_lienzo()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'toolbar'):
            tb_w = self.toolbar.sizeHint().width()
            tb_h = self.toolbar.sizeHint().height()
            x = int((self.tabs_canvas.width() - tb_w) / 2)
            y = int(self.tabs_canvas.height() - tb_h - 40)
            self.toolbar.setGeometry(x, y, tb_w, tb_h)
            self.toolbar.raise_()
            
            # Posicionamos la sub-barra de pluma
            if hasattr(self, 'sub_toolbar_pen'):
                st_w = self.sub_toolbar_pen.sizeHint().width()
                st_h = self.sub_toolbar_pen.sizeHint().height()
                st_x = int((self.tabs_canvas.width() - st_w) / 2)
                st_y = y - st_h - 10 # 10 píxeles de aire entre ambas barras
                self.sub_toolbar_pen.setGeometry(st_x, st_y, st_w, st_h)

            # 🚀 Posicionamos la nueva sub-barra 3D
            if hasattr(self, 'sub_toolbar_3d'):
                st3d_w = self.sub_toolbar_3d.sizeHint().width()
                st3d_h = self.sub_toolbar_3d.sizeHint().height()
                st3d_x = int((self.tabs_canvas.width() - st3d_w) / 2)
                st3d_y = y - st3d_h - 10 
                self.sub_toolbar_3d.setGeometry(st3d_x, st3d_y, st3d_w, st3d_h)

    def draw_mockup(self):
        # Dibujar la maqueta móvil con texto gigante en Gilroy
        pen = QPen(Qt.GlobalColor.white, 2)
        brush_hero = QBrush(QColor("#FF1493"))
        brush_features = QBrush(QColor("#8A2BE2"))
        brush_testimonials = QBrush(QColor("#007BFF"))

        # El móvil (centrado)
        mobile_rect = QGraphicsRectItem(100, 50, 250, 500)
        mobile_rect.setBrush(QBrush(QColor("#FFFFFF")))
        mobile_rect.setPen(pen)
        self.scene.addItem(mobile_rect)

        # Texto Gigante Hero en Gilroy
        text_hero = self.scene.addText("Hero")
        text_hero.setDefaultTextColor(QColor("#18191D")) # Texto oscuro en fondo blanco del móvil
        gilroy_hero_font = QFont(GLOBAL_FONT_FAMILY, 36, QFont.Weight.Bold)
        text_hero.setFont(gilroy_hero_font)
        text_hero.setPos(130, 80)
        
        # Bloques simulados
        hero_rect = QGraphicsRectItem(120, 150, 100, 100)
        hero_rect.setBrush(brush_hero)
        hero_rect.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(hero_rect)
        
        # Texto Gigante Key Features en Gilroy
        text_features = self.scene.addText("Key Features")
        text_features.setDefaultTextColor(QColor("#18191D"))
        gilroy_features_font = QFont(GLOBAL_FONT_FAMILY, 24, QFont.Weight.Bold)
        text_features.setFont(gilroy_features_font)
        text_features.setPos(130, 270)
        
        features_rect = QGraphicsRectItem(120, 310, 150, 120)
        features_rect.setBrush(brush_features)
        features_rect.setPen(QPen(Qt.PenStyle.NoPen))
        self.scene.addItem(features_rect)


class CustomTitleBar(QFrame):
    """Barra de título premium tipo Figma con controles integrados (Motor Manual)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(45)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent; 
                border-bottom: 1px solid {BORDER_NAV};
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(10)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(qta.icon('fa5s.paint-brush', color=COLOR_ACCENT).pixmap(16, 16))
        layout.addWidget(icon_lbl)
        
        title_lbl = QLabel("Designify")
        title_lbl.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 13px; font-weight: bold; background: transparent;")
        layout.addWidget(title_lbl)
        
        layout.addStretch()
        
        btn_style = f"QPushButton {{ background: transparent; border: none; border-radius: 6px; }} QPushButton:hover {{ background: #3F4148; }}"
        close_style = f"QPushButton {{ background: transparent; border: none; border-radius: 6px; }} QPushButton:hover {{ background: #FF5C5C; }}"
        
        self.btn_min = IconButton('fa5s.minus', size=12, color=TEXT_MUTED)
        self.btn_min.setFixedSize(34, 34)
        self.btn_min.setStyleSheet(btn_style)
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        
        self.btn_max = IconButton('fa5s.square', size=12, color=TEXT_MUTED)
        self.btn_max.setFixedSize(34, 34)
        self.btn_max.setStyleSheet(btn_style)
        self.btn_max.clicked.connect(self.toggle_maximize)
        
        self.btn_close = IconButton('fa5s.times', size=12, color=TEXT_MUTED, hover_color="#FFFFFF")
        self.btn_close.setFixedSize(34, 34)
        self.btn_close.setStyleSheet(close_style)
        self.btn_close.clicked.connect(self.parent_window.close)
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        
        self.start_pos = None

    def toggle_maximize(self):
        """Control manual de maximizado con memoria física"""
        
        # 🚀 PASE VIP: Le avisamos al lienzo que este cambio es INTENCIONAL
        self.parent_window._cambio_intencional = True
        
        if getattr(self.parent_window, '_estado_actual_ui', 'NORMAL') == 'MAX':
            self.parent_window.showNormal()
            # Le forzamos las medidas exactas que tenía antes de maximizarse
            if hasattr(self.parent_window, 'geometria_flotante'):
                self.parent_window.setGeometry(self.parent_window.geometria_flotante)
        else:
            self.parent_window.showMaximized()
            
        # Apagamos el Pase VIP 100 milisegundos después, cuando ya terminó de encogerse
        QTimer.singleShot(100, lambda: setattr(self.parent_window, '_cambio_intencional', False))

    # 🚀 MOTOR DE ARRASTRE MANUAL INDESTRUCTIBLE
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if getattr(self, 'start_pos', None) is not None and not self.parent_window.isMaximized():
            delta = event.globalPosition().toPoint() - self.start_pos
            self.parent_window.move(self.parent_window.pos() + delta)
            self.start_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()

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
        
        # 🚀 Le quitamos el font-size forzado al CSS para que la vista previa pueda brillar
        self.list_widget.setStyleSheet(f"""
            QListWidget {{ background: transparent; border: none; outline: none; }}
            QListWidget::item {{ color: {TEXT_MUTED}; padding: 8px 10px; border-radius: 6px; }}
            QListWidget::item:hover {{ background-color: #18191D; color: {TEXT_MAIN}; }}
            QListWidget::item:selected {{ background-color: {COLOR_ACCENT}; color: #FFFFFF; }}
        """)
        
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 🚀 LA CURA DEL SCROLL HORIZONTAL
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setTextElideMode(Qt.TextElideMode.ElideRight) # Corta con "..." los nombres muy largos
        
        self.list_widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._populate_list(self.font_list)
        layout.addWidget(self.list_widget)

        self.list_widget.itemClicked.connect(self._on_item_clicked)
        base_layout.addWidget(container)
        
        self.setFixedSize(240, 320)

    def _populate_list(self, fonts):
        from PyQt6.QtGui import QFont
        self.list_widget.clear()
        for f in fonts:
            item = QListWidgetItem(f)
            
            # 🚀 VISTA PREVIA EN VIVO: Le decimos al ítem que se dibuje con su propia tipografía
            # Le damos un tamaño de 14 para que las curvas de la letra se aprecien perfectamente
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
        
        # Layout base para permitir que se vea la sombra
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(15, 15, 15, 15)
        
        container = QFrame()
        container.setStyleSheet(f"QFrame {{ background-color: {BG_NAV}; border-radius: 12px; border: 1px solid {BORDER_NAV}; }}")
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
        
        # Generador dinámico de botones
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
        """Guarda qué botón presionó el usuario y cierra la ventana"""
        self.resultado = rol
        self.accept()

    # 🚀 MOTOR DE ARRASTRE MANUAL PARA EL DIÁLOGO
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

class MainDesignStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 🚀 1. ASESINAR EL MARCO DE WINDOWS Y FORZAR TRANSPARENCIA
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(1600, 1000)
        
        set_premium_dark_theme(QApplication.instance())

        # --- SINCRONIZAR FUENTES GLOBALES ---
        ruta_fuentes = "fuentes"
        self.motor_temp = RectorOP() 
        fuentes_cargadas = self.motor_temp.cargar_fuentes_locales(ruta_fuentes) 
        self.mapa_fuentes_qt = {} 
        if os.path.exists(ruta_fuentes):
            for archivo in os.listdir(ruta_fuentes):
                if archivo.lower().endswith(".ttf"):
                    font_id = QFontDatabase.addApplicationFont(os.path.join(ruta_fuentes, archivo))
                    familias = QFontDatabase.applicationFontFamilies(font_id)
                    if familias: self.mapa_fuentes_qt[os.path.splitext(archivo)[0]] = familias[0]

        # 🚀 2. CREACIÓN DEL LIENZO BASE (Para la Sombra y las Esquinas)
        self.base_widget = QWidget()
        self.base_widget.setObjectName("base_widget")
        self.base_widget.setStyleSheet("QWidget#base_widget { background: transparent; }") # <-- Fuga de esquinas curada
        self.setCentralWidget(self.base_widget)
        self.base_layout = QVBoxLayout(self.base_widget)
        self.base_layout.setContentsMargins(15, 15, 15, 15)
        
        self.main_container = QFrame()
        self.main_container.setObjectName("main_container")
        self.main_container.setStyleSheet(f"QFrame#main_container {{ background-color: {BG_NAV}; border-radius: 12px; border: 1px solid {BORDER_NAV}; }}")
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # 🚀 3. INYECTAR LA NUEVA BARRA DE TÍTULO
        self.title_bar = CustomTitleBar(self)
        container_layout.addWidget(self.title_bar)

        # --- 4. CONFIGURACIÓN DEL WIDGET DE CONTENIDO ---
        content_widget = QWidget()
        main_layout = QHBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 🚀 LA CURA DE LA INVISIBILIDAD: Conectamos las cajas
        container_layout.addWidget(content_widget)      
        self.base_layout.addWidget(self.main_container)
        
        # --- 5. CREACIÓN DE PANELES ---
        self.motor = None 
        self.left_nav = LeftNavPanel()
        self.assets_panel = AssetsPanel(None, self.mapa_fuentes_qt) 
        self.main_canvas = MainCanvasPanel()
        self.properties_panel = PropertiesPanel() 
        self.properties_panel.property_changed.connect(self._aplicar_cambio_desde_panel)

        # 🚀 CONEXIÓN VDOM (Enrutamiento en caliente)
        self.left_nav.tab_changed.connect(self.assets_panel.stack.setCurrentIndex)
        
        # Inicializamos encendiendo la pestaña "Capas" (índice 4) por defecto
        self.left_nav.cambiar_pestana(4)

        # --- 6. AGREGAR PANELES A LA PANTALLA ---
        main_layout.addWidget(self.left_nav)
        main_layout.addWidget(self.assets_panel)
        main_layout.addWidget(self.main_canvas, stretch=1)
        main_layout.addWidget(self.properties_panel)

        self.assets_panel.tree_widget.model().rowsMoved.connect(self._al_reordenar_capas)
        
        # --- 7. CONEXIONES MULTIPESTAÑA ---
        self.main_canvas.btn_new.clicked.connect(self._accion_nuevo_documento)
        self.main_canvas.btn_open.clicked.connect(self._abrir_proyecto)
        self.main_canvas.btn_save.clicked.connect(self._guardar_proyecto)
        self.main_canvas.btn_import.clicked.connect(self._importar_archivo)
        self.main_canvas.btn_export.clicked.connect(self._mostrar_menu_exportar)
        
        self.main_canvas.tabs_canvas.currentChanged.connect(self._al_cambiar_pestana)
        self.main_canvas.tabs_canvas.tabCloseRequested.connect(self._cerrar_pestana)
        self.main_canvas.tabs_canvas.tabCloseRequested.connect(self._cerrar_pestana)
        # Conexión de la barra flotante
        self.main_canvas.toolbar.tool_changed.connect(self._al_cambiar_herramienta)
        self.main_canvas.sub_toolbar_3d.tool_changed.connect(self._al_cambiar_herramienta)
        
        # --- 8. ARRANQUE ---
        self._nueva_pestana()

    @property
    def canvas_view_actual(self):
        tab = self.main_canvas.tabs_canvas.currentWidget()
        return tab.canvas_view if tab else None

    def actualizar_lienzo(self):
        tab = self.main_canvas.tabs_canvas.currentWidget()
        if tab: tab.actualizar_lienzo()

    def _accion_nuevo_documento(self):
        """Abre el diálogo profesional de creación y configura la nueva pestaña"""
        dialog = NewDocumentDialog(self)
        
        # Opcional: Oscurecemos la ventana principal para dar enfoque al menú
        efecto_sombra = QGraphicsDropShadowEffect()
        efecto_sombra.setBlurRadius(30)
        self.main_container.setGraphicsEffect(efecto_sombra)
        
        if dialog.exec():
            # Si el usuario aceptó y eligió un formato:
            w, h, modo_color, dpi = dialog.resultado
            
            # 1. Creamos la pestaña vacía estándar
            self._nueva_pestana()
            
            # 2. Inyectamos las matemáticas profesionales al motor de esa nueva pestaña
            self.motor.w_pdf = w
            self.motor.h_pdf = h
            self.motor.modo_color = modo_color
            self.motor.dpi_exportacion = dpi
            self.properties_panel.modo_color_doc = modo_color
            
            # 3. Refrescamos el lienzo visual para que la hoja tome el nuevo tamaño
            self.canvas_view_actual.sincronizar_con_motor()
            self.canvas_view_actual.centrar_y_encajar()
            
        # Quitamos la sombra al terminar
        self.main_container.setGraphicsEffect(None)


    def _nueva_pestana(self, ruta_archivo=None):
        tab = DocumentTab(self, self.mapa_fuentes_qt, ruta_archivo)
        tab.canvas_view.elemento_seleccionado.connect(self.al_seleccionar_elemento)
        tab.canvas_view.lienzo_modificado.connect(self._al_modificar_lienzo)
        
        idx = self.main_canvas.tabs_canvas.addTab(tab, tab.nombre_archivo)
        
        contenedor_btn = QWidget()
        layout_btn = QHBoxLayout(contenedor_btn)
        layout_btn.setContentsMargins(5, 0, 10, 0) 
        layout_btn.setSpacing(0)

        btn_close = IconButton('fa5s.times', size=12, color=TEXT_MUTED, hover_color='#FF5C5C')
        btn_close.setFixedSize(24, 24) 
        btn_close.setStyleSheet("""
            QPushButton { background: transparent; border: none; } 
            QPushButton:hover { background: #3F4148; border-radius: 6px; }
        """)
        
        btn_close.clicked.connect(lambda checked, w=tab: self._cerrar_pestana_por_widget(w))
        layout_btn.addWidget(btn_close) 
        
        self.main_canvas.tabs_canvas.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, contenedor_btn)
        self.main_canvas.tabs_canvas.setCurrentIndex(idx)
        QTimer.singleShot(100, tab.canvas_view.centrar_y_encajar)
        QTimer.singleShot(150, tab.canvas_view.setFocus)

    def _ajustar_estilos_segun_estado(self):
        """Función auxiliar que aplica el diseño final sin interferir con la animación de Windows"""
        if self.isMaximized():
            # 🖥️ ESTILO PANTALLA COMPLETA
            self.base_layout.setContentsMargins(0, 0, 0, 0)
            self.main_container.setStyleSheet(f"QFrame#main_container {{ background-color: {BG_NAV}; border-radius: 0px; border: none; }}")
            self.properties_panel.setStyleSheet(f"background-color: {BG_PROPERTIES}; border-left: 1px solid #2A2B31; border-bottom-right-radius: 0px;")
            self.title_bar.btn_max.setIcon(qta.icon('fa5s.compress', color=TEXT_MUTED))
            if hasattr(self, 'size_grip'): self.size_grip.hide()
        elif not self.isMinimized():
            # 🪟 ESTILO VENTANA FLOTANTE (Solo si NO está minimizada)
            self.base_layout.setContentsMargins(15, 15, 15, 15)
            self.main_container.setStyleSheet(f"QFrame#main_container {{ background-color: {BG_NAV}; border-radius: 12px; border: 1px solid {BORDER_NAV}; }}")
            self.properties_panel.setStyleSheet(f"background-color: {BG_PROPERTIES}; border-left: 1px solid #2A2B31; border-bottom-right-radius: 12px;")
            self.title_bar.btn_max.setIcon(qta.icon('fa5s.square', color=TEXT_MUTED))
            if hasattr(self, 'size_grip'): self.size_grip.show()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            
            # 🚀 SI TIENE PASE VIP (Viene del botón), lo dejamos encogerse en paz
            if getattr(self, '_cambio_intencional', False):
                return super().changeEvent(event)
                
            # 🚀 LA CURA DEL AMNESIA DE WINDOWS (Solo actúa si no hay Pase VIP)
            if not self.isMinimized() and getattr(self, '_estado_actual_ui', None) == 'MAX':
                if not self.isMaximized():
                    QTimer.singleShot(0, self.showMaximized)
                    
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        # 1. Control del Grip de redimensión (Esquinero)
        if not hasattr(self, 'size_grip'):
            self.size_grip = QSizeGrip(self.main_container)
            self.size_grip.setStyleSheet("background: transparent;")
        self.size_grip.resize(20, 20)
        self.size_grip.move(self.main_container.width() - 20, self.main_container.height() - 20)

        # 2. Sincronización visual y memoria
        if self.isMaximized():
            if getattr(self, '_estado_actual_ui', None) != 'MAX':
                self.base_layout.setContentsMargins(0, 0, 0, 0)
                self.main_container.setStyleSheet(f"QFrame#main_container {{ background-color: {BG_NAV}; border-radius: 0px; border: none; }}")
                self.properties_panel.setStyleSheet(f"background-color: {BG_PROPERTIES}; border-left: 1px solid #2A2B31; border-bottom-right-radius: 0px;")
                if hasattr(self, 'title_bar'): self.title_bar.btn_max.setIcon(qta.icon('fa5s.compress', color=TEXT_MUTED))
                self.size_grip.hide()
                self._estado_actual_ui = 'MAX'
                
        elif not self.isMinimized():
            # 🚀 GUARDADO DE GEOMETRÍA: Solo tomamos foto de su tamaño si está flotando normal
            if getattr(self, '_estado_actual_ui', None) != 'MAX':
                self.geometria_flotante = self.geometry()
                
            if getattr(self, '_estado_actual_ui', None) != 'NORMAL':
                self.base_layout.setContentsMargins(15, 15, 15, 15)
                self.main_container.setStyleSheet(f"QFrame#main_container {{ background-color: {BG_NAV}; border-radius: 12px; border: 1px solid {BORDER_NAV}; }}")
                self.properties_panel.setStyleSheet(f"background-color: {BG_PROPERTIES}; border-left: 1px solid #2A2B31; border-bottom-right-radius: 12px;")
                if hasattr(self, 'title_bar'): self.title_bar.btn_max.setIcon(qta.icon('fa5s.square', color=TEXT_MUTED))
                self.size_grip.show()
                self._estado_actual_ui = 'NORMAL'

    def _al_cambiar_herramienta(self, tool_id):
        if self.canvas_view_actual:
            self.canvas_view_actual.set_tool(tool_id)

    # ==========================================
    # PUENTE DE COMUNICACIÓN DEL CUENTAGOTAS
    # ==========================================
    def preparar_receptor_color(self, picker_dialog):
        """Guarda la referencia del diálogo que está esperando el color"""
        self._color_picker_esperando = picker_dialog

    def procesar_color_robado(self, qcolor):
        """Recibe el color del lienzo y se lo pasa al diálogo, o pinta la selección actual."""
        from PyQt6.QtWidgets import QToolTip
        QToolTip.hideText()
        
        # 1. Si el color picker estaba abierto esperando
        if hasattr(self, '_color_picker_esperando') and self._color_picker_esperando:
            self._color_picker_esperando.recibir_color_robado(qcolor)
            self._color_picker_esperando = None
            
            # Devolvemos el lienzo al modo de selección simulando un clic en la barra
            if hasattr(self, 'main_canvas') and hasattr(self.main_canvas, 'toolbar'):
                btn_select = next((b for b in self.main_canvas.toolbar.btn_group.buttons() if b.property("tool_id") == "select"), None)
                if btn_select:
                    btn_select.click()
        else:
            # 2. Si lo activó desde la barra y no hay diálogo, pinta el objeto seleccionado
            canvas = self.canvas_view_actual
            if canvas and canvas.uids_seleccionados:
                self.motor.registrar_punto_historial()
                hex_color = qcolor.name() 
                
                for uid in canvas.uids_seleccionados:
                    self.motor.modificar_elemento(uid, color_tx=hex_color)
                    
                canvas.dibujar_controles_seleccion()
                self.actualizar_lienzo()
                if canvas.uid_activo:
                    canvas.elemento_seleccionado.emit(canvas.uid_activo)
            
            # Volvemos a la herramienta de selección
            if hasattr(self, 'main_canvas') and hasattr(self.main_canvas, 'toolbar'):
                btn_select = next((b for b in self.main_canvas.toolbar.btn_group.buttons() if b.property("tool_id") == "select"), None)
                if btn_select:
                    btn_select.click()

    def procesar_color_hover(self, qcolor):
        """Actualiza el color en vivo mientras el ratón se mueve por el lienzo"""
        if hasattr(self, '_color_picker_esperando') and self._color_picker_esperando:
            self._color_picker_esperando.recibir_color_hover(qcolor)

    def cancelar_cuentagotas(self):
        """Restaura el diálogo si el usuario canceló"""
        if hasattr(self, '_color_picker_esperando') and self._color_picker_esperando:
            self._color_picker_esperando.cancelar_robo()
            self._color_picker_esperando = None
            
        # Volvemos a la herramienta de selección
        if hasattr(self, 'main_canvas') and hasattr(self.main_canvas, 'toolbar'):
            btn_select = next((b for b in self.main_canvas.toolbar.btn_group.buttons() if b.property("tool_id") == "select"), None)
            if btn_select:
                btn_select.click()


    def _al_modificar_lienzo(self):
        tab = self.main_canvas.tabs_canvas.currentWidget()
        if tab and not tab.modificado:
            tab.modificado = True
            idx = self.main_canvas.tabs_canvas.indexOf(tab)
            self.main_canvas.tabs_canvas.setTabText(idx, f"{tab.nombre_archivo} *")

    def _al_cambiar_pestana(self, index):
        if self.canvas_view_actual:
            self.canvas_view_actual.set_tool(self.main_canvas.toolbar.herramienta_actual)

        if index < 0:
            self.motor = None
            self.assets_panel.motor = None
            self.assets_panel.cargar_capas()
            self.al_seleccionar_elemento(None)
            return
            
        tab = self.main_canvas.tabs_canvas.widget(index)
        self.motor = tab.motor
        self.assets_panel.motor = tab.motor

        self.properties_panel.modo_color_doc = getattr(self.motor, 'modo_color', 'RGB')
        
        self._refrescar_panel_capas()
        self.al_seleccionar_elemento(None)
        
    def _cerrar_pestana_por_widget(self, widget):
        idx = self.main_canvas.tabs_canvas.indexOf(widget)
        if idx != -1:
            self._cerrar_pestana(idx)

    def _cerrar_pestana(self, index):
        tab = self.main_canvas.tabs_canvas.widget(index)
        if not tab: return
        
        # 🚀 1. CIERRE INTELIGENTE (Solo pregunta si hay cambios sin guardar)
        if tab.modificado:
            botones = [
                ("Guardar", "guardar", COLOR_ACCENT),
                ("No Guardar", "descartar", "#FF5C5C"),
                ("Cancelar", "cancelar", None)
            ]
            msg = PremiumMessageBox(self, "Guardar cambios", f"¿Deseas guardar los cambios en '{tab.nombre_archivo}' antes de cerrar?", botones)
            msg.exec() 
            
            if msg.resultado == "guardar":
                self.main_canvas.tabs_canvas.setCurrentIndex(index)
                self._guardar_proyecto()
                # Si falló el guardado (ej. canceló la ventana), abortamos el cierre
                if tab.modificado: return 
            elif msg.resultado == "cancelar" or msg.resultado is None:
                return # 🚀 ABORTA EL CIERRE 
                
        if getattr(tab, 'ruta_archivo', None):
            lock_file = f"{tab.ruta_archivo}.lock"
            if os.path.exists(lock_file):
                try: os.remove(lock_file)
                except: pass
                
        self.main_canvas.tabs_canvas.removeTab(index)

    def _abrir_proyecto(self):
        filtro = "Designify File (*.dfy)"
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Proyecto", "", filtro)
        
        if ruta:
            for i in range(self.main_canvas.tabs_canvas.count()):
                tab = self.main_canvas.tabs_canvas.widget(i)
                if getattr(tab, 'ruta_archivo', None) == ruta:
                    self.main_canvas.tabs_canvas.setCurrentIndex(i)
                    return 
                    
            # 🚀 2. DETECCIÓN DE RED: ¿Alguien más lo está usando?
            lock_file = f"{ruta}.lock"
            if os.path.exists(lock_file):
                botones = [("Sí, abrir de todas formas", "yes", COLOR_ACCENT), ("Cancelar", "no", None)]
                msg = PremiumMessageBox(self, "Archivo en uso", "Alguien más parece estar editando este archivo en la red.\n\n¿Deseas abrirlo y arriesgarte a crear conflictos?", botones)
                msg.exec()
                if msg.resultado != "yes":
                    return

            try:
                self.al_seleccionar_elemento(None) 
                try:
                    with open(lock_file, 'w') as f: f.write("locked_by_designify")
                except: pass

                # 🚀 INICIO DE CARGA
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                self._nueva_pestana(ruta)
                print(f"✅ Proyecto cargado con éxito desde: {ruta}")
            except Exception as e:
                print(f"❌ Error crítico al abrir: {e}")
            finally:
                # 🚀 FIN DE CARGA
                QApplication.restoreOverrideCursor()

    def _guardar_proyecto(self):
        if not self.motor: return
        tab = self.main_canvas.tabs_canvas.currentWidget()
        filtro = "Designify File (*.dfy)"
        
        ruta_sugerida = f"{tab.nombre_archivo}.dfy"
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Proyecto", ruta_sugerida, filtro)
        
        if ruta:
            if ruta != tab.ruta_archivo:
                lock_file_nuevo = f"{ruta}.lock"
                # 🚀 1. Si está guardando con un NUEVO nombre, revisamos candados de red
                if ruta != tab.ruta_archivo:
                    lock_file_nuevo = f"{ruta}.lock"
                    if os.path.exists(lock_file_nuevo):
                        botones = [("Sí, sobrescribir", "yes", "#FF5C5C"), ("Cancelar", "no", None)]
                        msg = PremiumMessageBox(self, "Archivo bloqueado", "Este nombre de archivo está en uso por otro usuario.\n\n¿Sobrescribir bajo tu propio riesgo?", botones)
                        msg.exec()
                        if msg.resultado != "yes": return
            
            try:
                # 🚀 INICIO DE CARGA: Convirtiendo imágenes a Base64...
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                
                self.motor.guardar_proyecto(ruta)
                
                if getattr(tab, 'ruta_archivo', None) and tab.ruta_archivo != ruta:
                    try: os.remove(f"{tab.ruta_archivo}.lock")
                    except: pass
                    
                nombre_limpio = os.path.splitext(os.path.basename(ruta))[0]
                
                tab.modificado = False
                tab.nombre_archivo = nombre_limpio 
                tab.ruta_archivo = ruta 
                self.main_canvas.tabs_canvas.setTabText(self.main_canvas.tabs_canvas.currentIndex(), nombre_limpio)
                
                try:
                    with open(f"{ruta}.lock", 'w') as f: f.write("locked")
                except: pass
                
                print(f"✅ Proyecto guardado exitosamente en: {ruta}")
            except Exception as e:
                print(f"❌ Error crítico al guardar: {e}")
            finally:
                # 🚀 FIN DE CARGA
                QApplication.restoreOverrideCursor()

    def _importar_archivo(self):
        if not self.motor: return
        tab = self.main_canvas.tabs_canvas.currentWidget()
        if not tab: return

        filtro = "Imágenes y Vectores (*.png *.jpg *.jpeg *.svg)"
        rutas, _ = QFileDialog.getOpenFileNames(self, "Importar Archivos", "", filtro)
        
        if rutas:
            self.motor.registrar_punto_historial()

            # 🚀 INICIO DE CARGA: Bloqueamos interfaz y mostramos reloj
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            try:
                nuevos_uids = []
                for ruta in rutas:
                    # 👇 A PARTIR DE AQUÍ TODO ESTO VA DENTRO DEL FOR (indentado a la derecha) 👇
                    uid = f"img_{int(time.time() * 1000)}_{len(nuevos_uids)}"
                    w, h = 200, 200
                    if ruta.lower().endswith('.svg'):
                        import xml.etree.ElementTree as ET
                        ratio = 1.0
                        try:
                            tree = ET.parse(ruta)
                            root = tree.getroot()
                            vb = root.attrib.get('viewBox')
                            if vb:
                                parts = vb.replace(',', ' ').split()
                                if len(parts) >= 4:
                                    ratio = float(parts[3]) / float(parts[2])
                            else:
                                vw = root.attrib.get('width', '100').replace('px','').replace('%','')
                                vh = root.attrib.get('height', '100').replace('px','').replace('%','')
                                ratio = float(vh) / float(vw)
                        except: pass
                        w = 300
                        h = 300 * ratio
                    else:
                        try:
                            with Image.open(ruta) as img:
                                w, h = img.width, img.height
                                if w > 600 or h > 600:
                                    ratio = min(600/w, 600/h)
                                    w, h = w * ratio, h * ratio
                        except: pass
                    
                    cx = self.motor.w_pdf / 2.0 - (w/2.0)
                    cy = self.motor.h_pdf / 2.0 - (h/2.0)
                    
                    nombre_limpio = os.path.basename(ruta)
                    self.motor.agregar_elemento(uid, 'Foto', contenido=ruta, x=cx, y=cy, w=w, h=h, nombre_capa=nombre_limpio)
                    nuevos_uids.append(uid)
                # 👆 HASTA AQUÍ TERMINA EL FOR 👆
            
                if nuevos_uids:
                    self.canvas_view_actual.uids_seleccionados = nuevos_uids
                    self.canvas_view_actual.uid_activo = nuevos_uids[-1]
                    self.actualizar_lienzo()
                    self._refrescar_panel_capas()
                    self._al_modificar_lienzo()
                    self.al_seleccionar_elemento(self.canvas_view_actual.uid_activo)
                    
            finally:
                # 🚀 FIN DE CARGA: Aseguramos que el cursor vuelva a la normalidad
                QApplication.restoreOverrideCursor()
    
    def seleccionar_desde_capas(self, uid, multi=False):
        if not self.canvas_view_actual: return 
        
        # =======================================================
        # 🚀 RESTRICCIÓN 3D / PERSPECTIVA DESDE EL PANEL DE CAPAS
        # =======================================================
        herramienta = getattr(self.canvas_view_actual, 'herramienta_activa', 'select')
        if herramienta in ['3d', 'perspective']:
            multi = False # Apagamos la intención de multi-selección obligatoriamente
        # =======================================================
            
        # 🚀 CURA DE SELECCIÓN MÚLTIPLE DESDE EL PANEL
        if multi:
            if uid in self.canvas_view_actual.uids_seleccionados:
                self.canvas_view_actual.uids_seleccionados.remove(uid)
                self.canvas_view_actual.uid_activo = self.canvas_view_actual.uids_seleccionados[-1] if self.canvas_view_actual.uids_seleccionados else None
            else:
                self.canvas_view_actual.uids_seleccionados.append(uid)
                self.canvas_view_actual.uid_activo = uid
        else:
            self.canvas_view_actual.uid_activo = uid
            self.canvas_view_actual.uids_seleccionados = [uid] 
            
        self.canvas_view_actual.dibujar_controles_seleccion()
        self.al_seleccionar_elemento(self.canvas_view_actual.uid_activo)

    def al_seleccionar_elemento(self, uid_activo):
        if not self.canvas_view_actual: return

        uids_sel = self.canvas_view_actual.uids_seleccionados

        if not uids_sel:
            self.properties_panel.actualizar_desde_motor(None, None)
            uids_viejos = getattr(self, '_last_uids_sel', []) or []
            for uid_viejo in uids_viejos:
                card = getattr(self.assets_panel, 'tarjetas_ui', {}).get(uid_viejo)
                if card:
                    try: card.set_activa(False)
                    except RuntimeError: pass
            self._last_uids_sel = []
            return

        # 1. Determinar si hay un Grupo Padre implicado
        padre_principal_uid = None
        if uid_activo:
            elem_activo = self.motor.elementos.get(uid_activo)
            if elem_activo:
                parent_marco = elem_activo.get('parent_marco')
                padre_principal_uid = parent_marco if parent_marco else uid_activo

        es_multiple = len(uids_sel) > 1

        # 2. Cargar panel derecho (VDOM)
        if es_multiple:
            self.properties_panel.actualizar_desde_motor(None, None)
        else:
            elem = self.motor.elementos.get(uid_activo) if uid_activo else None
            self.properties_panel.actualizar_desde_motor(uid_activo, elem)
            
        # 3. Lógica de apagado/encendido
        if getattr(self, '_last_uids_sel', None) != uids_sel:
            uids_viejos = getattr(self, '_last_uids_sel', []) or []
            
            # Apagar las que ya no están seleccionadas
            for uid_viejo in uids_viejos:
                if uid_viejo not in uids_sel and uid_viejo != padre_principal_uid:
                    card = getattr(self.assets_panel, 'tarjetas_ui', {}).get(uid_viejo)
                    if card:
                        try: card.set_activa(False)
                        except RuntimeError: pass
            
            self._last_uids_sel = list(uids_sel)
            if padre_principal_uid and padre_principal_uid not in self._last_uids_sel:
                self._last_uids_sel.append(padre_principal_uid)

            # 🚀 CURA 2: Encender todas las tarjetas seleccionadas
            for uid_nuevo in uids_sel:
                card = getattr(self.assets_panel, 'tarjetas_ui', {}).get(uid_nuevo)
                if card:
                    # Es sutil solo si es un hijo individual dentro de un grupo
                    es_sutil = not es_multiple and padre_principal_uid and uid_nuevo != padre_principal_uid
                    try: card.set_activa(True, sutil=es_sutil)
                    except RuntimeError: pass

            # Si es un solo elemento y tiene padre, iluminar el padre también
            if not es_multiple and padre_principal_uid and padre_principal_uid not in uids_sel:
                card_padre = getattr(self.assets_panel, 'tarjetas_ui', {}).get(padre_principal_uid)
                if card_padre:
                    try: card_padre.set_activa(True, sutil=False)
                    except RuntimeError: pass

            # 4. Auto-Scroll a la capa tocada
            if uid_activo:
                list_item = getattr(self.assets_panel, 'list_items_ui', {}).get(uid_activo)
                if list_item: self.assets_panel.tree_widget.scrollToItem(list_item)

    def _aplicar_cambio_desde_panel(self, uid, cambios):
        """Recibe los cambios del VDOM y se los manda al motor"""
        if not uid or not self.canvas_view_actual: return
        
        self.motor.registrar_punto_historial()
        self.motor.modificar_elemento(uid, **cambios) 
        
        self.canvas_view_actual.dibujar_controles_seleccion()
        self.main_canvas.actualizar_lienzo()
        self.canvas_view_actual.lienzo_modificado.emit()

    def _conectar_señales_capas(self):
        list_items = self.assets_panel.get_list_items()
        
        for i in range(len(list_items)):
            list_item = list_items[i]
            card = self.assets_panel.list_widget.itemWidget(list_item)
            
            if card:
                card.blockSignals(True) 
                card.seleccionada.connect(self.seleccionar_desde_capas)
                card.oculto_cambiado.connect(self._al_cambiar_oculto_capa)
                card.bloqueado_cambiado.connect(self._al_cambiar_bloqueado_capa)
                card.nombre_cambiado.connect(self._al_cambiar_nombre_capa)
                card.blockSignals(False)
                
        self.assets_panel.tree_widget.model().rowsMoved.connect(self._al_reordenar_capas)

    def _al_cambiar_oculto_capa(self, uid, esta_oculto):
        self.motor.modificar_elemento(uid, oculto=esta_oculto)
        self.main_canvas.actualizar_lienzo()

    def _al_cambiar_bloqueado_capa(self, uid, esta_bloqueado):
        self.motor.modificar_elemento(uid, bloqueado=esta_bloqueado)

    def _al_cambiar_nombre_capa(self, uid, nuevo_nombre):
        self.motor.modificar_elemento(uid, nombre=nuevo_nombre)

    def _al_reordenar_capas(self, source_parent, source_start, source_end, destination_parent, destination_row):
        QTimer.singleShot(50, self._procesar_reordenamiento_diferido)

    def _procesar_reordenamiento_diferido(self):
        z_index = 10000 
        tree = self.assets_panel.tree_widget
        
        def procesar_nodo(item, parent_uid=None):
            nonlocal z_index
            try:
                uid = item.data(0, Qt.ItemDataRole.UserRole)
            except RuntimeError:
                return 
                
            if uid:
                if parent_uid:
                    padre_elem = self.motor.elementos.get(parent_uid)
                    
                    # 🚀 MAGIA UX: AUTO-AGRUPACIÓN TIPO iOS
                    if padre_elem and padre_elem.get('tipo') != 'Marco':
                        # 1. Creamos el nuevo grupo
                        nuevo_grupo_uid = f"grupo_auto_{int(time.time() * 1000)}_{uid}"
                        
                        # 2. Calculamos la caja que envuelve a ambas imágenes
                        caja_g = self.motor.obtener_caja_multiple([parent_uid, uid])
                        if not caja_g: caja_g = padre_elem
                        
                        self.motor.agregar_elemento(
                            nuevo_grupo_uid, "Marco", 
                            x=caja_g['x'], y=caja_g['y'], w=caja_g['w'], h=caja_g['h'],
                            nombre_capa="Nuevo Grupo", borde_grosor=0, color_tx=None,
                            z_index=padre_elem.get('z_index', z_index + 1)
                        )
                        
                        # 3. Metemos a la imagen receptora original dentro del grupo
                        self.motor.modificar_elemento(parent_uid, parent_marco=nuevo_grupo_uid)
                        
                        # 4. El elemento que estamos arrastrando también irá al nuevo grupo
                        parent_uid = nuevo_grupo_uid
                        
                self.motor.modificar_elemento(uid, z_index=z_index, parent_marco=parent_uid)
                z_index -= 1
                
                for i in range(item.childCount()):
                    procesar_nodo(item.child(i), parent_uid=uid)

        for i in range(tree.topLevelItemCount()):
            procesar_nodo(tree.topLevelItem(i), parent_uid=None)
                
        self.motor._normalizar_z_index() # 🚀 Limpiamos la matemática de capas
        self.main_canvas.actualizar_lienzo()
        QTimer.singleShot(10, self._refrescar_panel_capas)
        
    def _refrescar_panel_capas(self):
        self.assets_panel.cargar_capas()
        self._last_uids_sel = None 
        
        if self.canvas_view_actual:
            uid_activo = self.canvas_view_actual.uid_activo 
            if uid_activo:
                self.al_seleccionar_elemento(uid_activo)

    def _mostrar_menu_exportar(self):
        self.menu_exportar = QMenu(self)
        self.menu_exportar.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.menu_exportar.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.menu_exportar.setStyleSheet(f"""
            QMenu {{ background-color: #18191D; border: 1px solid #2A2B31; border-radius: 8px; padding: 5px; }}
        """)

        opciones = [
            ("PDF", "fa5s.file-pdf", "Exportar como PDF", "Alta calidad vectorial para imprenta.", "#FF5C5C"),
            ("PNG", "fa5s.image", "Exportar como PNG", "Fondo transparente, ideal para web.", "#66A3FF"),
            ("JPG", "fa5s.file-image", "Exportar como JPG", "Archivo ligero con fondo blanco.", "#FFB84D")
        ]

        for fmt, icono, titulo, subtitulo, color in opciones:
            item_widget = ExportMenuItem(fmt, icono, titulo, subtitulo, color)
            item_widget.clicked.connect(self._ejecutar_exportacion_desde_menu)
            action = QWidgetAction(self.menu_exportar)
            action.setDefaultWidget(item_widget)
            self.menu_exportar.addAction(action)

        btn = self.main_canvas.btn_export
        self.menu_exportar.adjustSize() 
        pos_menu = btn.mapToGlobal(btn.rect().bottomRight())
        pos_menu.setX(pos_menu.x() - self.menu_exportar.width())
        pos_menu.setY(pos_menu.y() + 5) 
        self.menu_exportar.exec(pos_menu)

    def _ejecutar_exportacion_desde_menu(self, formato):
        self.menu_exportar.close()
        self.ejecutar_exportacion(formato)

    def ejecutar_exportacion(self, formato):
        if formato == "PDF":
            filtro = "Archivos PDF (*.pdf)"; ext = ".pdf"
        elif formato == "PNG":
            filtro = "Imágenes PNG Transparentes (*.png)"; ext = ".png"
        else: 
            filtro = "Imágenes JPEG (*.jpg)"; ext = ".jpg"
            
        ruta_salida, _ = QFileDialog.getSaveFileName(self, f"Exportar diseño como {formato}", f"mi_diseno_premium{ext}", filtro)
        
        if ruta_salida:
            self.al_seleccionar_elemento(None) 
            self.main_canvas.actualizar_lienzo()
            
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            # 🚀 INICIO DEL RASTERIZADOR OFF-SCREEN (Puro, sin hacks visuales)
            import tempfile
            import os
            from PyQt6.QtGui import QImage, QPainter
            from PyQt6.QtCore import QRectF
            from PyQt6.QtWidgets import QGraphicsScene
            
            hay_3d = False
            self.motor.registrar_punto_historial() 
            archivos_temporales = []
            
            try:
                for uid, elem in list(self.motor.elementos.items()):
                    if elem.get('rot_3d_x', 0.0) != 0.0 or elem.get('rot_3d_y', 0.0) != 0.0:
                        hay_3d = True
                        item = self.canvas_view_actual.items_ui.get(uid)
                        if item:
                            # =======================================================
                            # 1. AISLAMIENTO ABSOLUTO (Sin ocultar elementos de la UI)
                            # Extraemos el objeto y lo metemos en una cámara de vacío.
                            # =======================================================
                            main_scene = self.canvas_view_actual.scene()
                            main_scene.removeItem(item) # Lo sacamos del lienzo principal
                            
                            render_scene = QGraphicsScene()
                            render_scene.addItem(item)  # Lo metemos al lienzo matemático
                            
                            # =======================================================
                            # 2. MAPEO MATEMÁTICO DE POLÍGONO
                            # Extraemos la silueta real 3D (para evitar los recortes de Qt)
                            # =======================================================
                            poly = item.mapToScene(item.boundingRect())
                            rect = poly.boundingRect()
                            rect.adjust(-15, -15, 15, 15) # 15px de aire para que jamás se mutile
                            
                            # =======================================================
                            # 3. RASTERIZADO EN RAM A 300 DPI (Calidad de Imprenta)
                            # =======================================================
                            dpi_scale = 300.0 / 72.0
                            img_w = int(rect.width() * dpi_scale)
                            img_h = int(rect.height() * dpi_scale)
                            
                            img = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
                            img.fill(Qt.GlobalColor.transparent)
                            
                            painter = QPainter(img)
                            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                            
                            # Rasterización directa: Mapeo perfecto sin desfases ni traslaciones
                            target_rect = QRectF(0, 0, img_w, img_h)
                            render_scene.render(painter, target=target_rect, source=rect)
                            painter.end()
                            
                            # =======================================================
                            # 4. RESTAURACIÓN Y PUENTE AL PDF
                            # =======================================================
                            # Devolvemos el objeto al lienzo de la interfaz intacto
                            render_scene.removeItem(item)
                            main_scene.addItem(item)
                            
                            # Guardamos el buffer purificado y lo inyectamos al motor
                            fd, tmp_path = tempfile.mkstemp(suffix=".png")
                            os.close(fd)
                            img.save(tmp_path, "PNG")
                            archivos_temporales.append(tmp_path)
                            
                            pdf_x, pdf_y = self.motor.ui_a_pdf(rect.left(), rect.bottom(), 1.0)
                            
                            self.motor.modificar_elemento(uid, 
                                tipo="Foto", contenido=tmp_path, 
                                x=pdf_x, y=pdf_y, w=rect.width(), h=rect.height(),
                                rotacion=0.0, rot_3d_x=0.0, rot_3d_y=0.0, 
                                stretch_x=1.0, stretch_y=1.0, opacidad=1.0
                            )
                
                # 🚀 AHORA SÍ, EXPORTAMOS EL PDF/IMAGEN
                if formato == "PDF": self.motor.exportar_pdf(ruta_salida)
                elif formato == "PNG": self.motor.exportar_png_transparente(ruta_salida)
                elif formato == "JPG": self.motor.exportar_imagen(ruta_salida)
                print(f"✅ ¡Exportación a {formato} exitosa!")
                
            except Exception as e:
                print(f"❌ Error crítico al exportar: {e}")
            finally:
                # Restauramos la matemática vectorial destruyendo la evidencia del Raster
                if hay_3d:
                    self.motor.deshacer()
                    self.main_canvas.actualizar_lienzo()
                    for tmp in archivos_temporales:
                        try: os.remove(tmp)
                        except: pass
                        
                QApplication.restoreOverrideCursor()



def boot_motor_aceleracion():
    """🚀 VECTIFY ENGINE: HARDWARE DETECTION & OVERRIDE 🚀"""
    print("\n" + "="*50)
    print("🚀 === INICIANDO MOTOR (DETECCIÓN DE HARDWARE) === 🚀")
    
    # 1. Análisis de CPU
    hilos = os.cpu_count() or 4
    print(f"🧠 Núcleos Lógicos de CPU: {hilos} Activos")

    # 2. Análisis de RAM y Asignación Dinámica
    ram_total_gb = psutil.virtual_memory().total / (1024**3)
    print(f"💾 RAM Total del Sistema: {ram_total_gb:.1f} GB")
    
    from PyQt6.QtGui import QImageReader
    if ram_total_gb >= 16.0:
        QImageReader.setAllocationLimit(4096) # 4 GB de buffer para gigantografías
        print("✅ Modo Ultra-RAM Activado (Buffer de 4GB)")
    else:
        QImageReader.setAllocationLimit(2048) # 2 GB
        print("✅ Modo RAM Estándar Activado (Buffer de 2GB)")

    # 3. 🎮 FORZAR LA GPU NATIVA (Sin QOpenGLWidget)
    # Usamos la Interfaz de Renderizado de Hardware (RHI) de Qt6
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
    if platform.system() == "Windows":
        # Direct3D 11 es estable, rápido y NO rompe ventanas sin bordes
        os.environ["QT_RHI_BACKEND"] = "d3d11"
        os.environ["QT_ANGLE_PLATFORM"] = "d3d11"
        print("🎮 Motor Gráfico Enrutado a: Direct3D 11 (GPU)")
    elif platform.system() == "Darwin":
        os.environ["QT_RHI_BACKEND"] = "metal"
        print("🎮 Motor Gráfico Enrutado a: Metal (GPU Apple Silicon)")
        
    print("========================================================\n")


if __name__ == "__main__":
    # Arrancamos la detección ANTES de que nazca la aplicación
    boot_motor_aceleracion()
    
    app = QApplication(sys.argv)
    window = MainDesignStudio()
    window.show()
    sys.exit(app.exec())