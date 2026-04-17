import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
                             QGraphicsPixmapItem, QGraphicsRectItem, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QFileDialog, QLabel)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QSurfaceFormat
from PyQt6.QtCore import Qt, QRectF

from motor_grafico import RectorOP # Tu backend matemático intacto

try:
    import hardware
except ImportError:
    hardware = None

class RenderNativoQt(QGraphicsView):
    """
    Este es el NUEVO Motor de Interfaz con aceleración por hardware (GPU).
    """
    def __init__(self, motor):
        super().__init__()
        self.motor = motor
        
        # =======================================================
        # 🚀 SELECTOR DE MOTOR DE RENDERIZADO (CPU vs GPU)
        # =======================================================
        if hardware and hasattr(hardware, 'detectar_motor_optimo'):
            self.motor_render = hardware.detectar_motor_optimo()
        else:
            self.motor_render = "GPU" # Por defecto forzamos GPU si no está el archivo

        if self.motor_render == "GPU":
            from PyQt6.QtOpenGLWidgets import QOpenGLWidget
            # Inyectamos la tarjeta gráfica como lienzo
            gl_widget = QOpenGLWidget()
            self.setViewport(gl_widget)
            self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        else:
            # Configuración Clásica CPU
            self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        # =======================================================
        # 🚀 BANDERAS RASTER (SIEMPRE DESPUÉS de setViewport)
        # =======================================================
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse) 
        self.setStyleSheet("background-color: #1a1a1a; border: none;")

        self.escena = QGraphicsScene()
        self.setScene(self.escena)
        
        # Diccionarios de caché NATIVA
        self.items_ui = {}
        self.cache_pixmaps = {}
        self._is_panning = False
        
        # Pintamos el fondo del lienzo
        self.hoja_fondo = QGraphicsRectItem(0, 0, self.motor.w_pdf, self.motor.h_pdf)
        self.hoja_fondo.setBrush(QBrush(QColor("#FFFFFF")))
        self.escena.addItem(self.hoja_fondo)

    def sincronizar_con_motor(self):
        self.hoja_fondo.setRect(0, 0, self.motor.w_pdf, self.motor.h_pdf)
        self.escena.setSceneRect(-500, -500, self.motor.w_pdf + 1000, self.motor.h_pdf + 1000)

        for uid, elem in self.motor.elementos.items():
            if elem.get('oculto', False):
                if uid in self.items_ui: self.items_ui[uid].setVisible(False)
                continue

            if uid not in self.items_ui:
                self._crear_item_qt(uid, elem)

            item = self.items_ui[uid]
            item.setVisible(True)
            
            x = elem['x']
            y_qt = self.motor.h_pdf - (elem['y'] + elem['h']) 
            
            item.setPos(x, y_qt)
            item.setZValue(elem.get('z_index', 0))
            
            rot = elem.get('rotacion', 0.0)
            item.setTransformOriginPoint(elem['w']/2, elem['h']/2)
            item.setRotation(-rot)

    def _crear_item_qt(self, uid, elem):
        tipo = elem['tipo']
        
        if tipo == 'Foto':
            item = QGraphicsPixmapItem()
            ruta = str(elem['contenido'])
            
            if ruta not in self.cache_pixmaps:
                pix = QPixmap(ruta)
                self.cache_pixmaps[ruta] = pix
            
            pix_escalado = self.cache_pixmaps[ruta].scaled(
                int(elem['w']), int(elem['h']), 
                Qt.AspectRatioMode.IgnoreAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            item.setPixmap(pix_escalado)
        elif tipo == 'Forma':
            item = QGraphicsRectItem(0, 0, elem['w'], elem['h'])
            color = elem.get('color_tx', '#000000')
            item.setBrush(QBrush(QColor(color)))
            item.setPen(QPen(Qt.PenStyle.NoPen))
        else:
            item = QGraphicsRectItem(0, 0, elem['w'], elem['h'])
            item.setBrush(QBrush(QColor("#FF00FF")))

        self.escena.addItem(item)
        self.items_ui[uid] = item

    # --- CONTROLES DE CAMARA FLUIDOS ---
    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        self.scale(factor, factor) 

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self._pan_start = event.position()

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.position() - self._pan_start
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            self._pan_start = event.position()

    def mouseReleaseEvent(self, event):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

# ==========================================
# VENTANA PRINCIPAL
# ==========================================
class VentanaMotorNativo(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.motor = RectorOP()
        self.motor.crear_lienzo_vacio(842, 595)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout = QHBoxLayout(widget_central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Visor Acelerado
        self.visor = RenderNativoQt(self.motor)
        
        # 🚀 TÍTULO DINÁMICO SEGÚN EL MOTOR
        motor_actual = self.visor.motor_render
        self.setWindowTitle(f"RectorOP - Modo: {motor_actual} Acceleration")
        self.resize(1000, 700)

        # Panel de Controles
        panel = QWidget()
        panel.setFixedWidth(220)
        panel.setStyleSheet("background-color: #2c2c2c;")
        layout_panel = QVBoxLayout(panel)

        # 🚀 ETIQUETA VISUAL DEL MOTOR
        self.lbl_motor = QLabel(f"Motor Activo: {motor_actual}")
        if motor_actual == "GPU":
            self.lbl_motor.setStyleSheet("color: #00FF00; font-weight: bold; font-size: 14px;")
        else:
            self.lbl_motor.setStyleSheet("color: #FFA500; font-weight: bold; font-size: 14px;")
        layout_panel.addWidget(self.lbl_motor)

        btn_foto = QPushButton("Cargar Bestia de 10MB")
        btn_foto.clicked.connect(self.cargar_bestia)
        btn_foto.setStyleSheet("background-color: #555; color: white; padding: 10px;")
        layout_panel.addWidget(btn_foto)
        
        btn_exportar = QPushButton("Exportar PDF Final (HD)")
        btn_exportar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        btn_exportar.clicked.connect(self.exportar_pdf)
        layout_panel.addWidget(btn_exportar)

        layout_panel.addStretch()
        
        layout.addWidget(panel)
        layout.addWidget(self.visor)
        
        self.visor.sincronizar_con_motor()

    def cargar_bestia(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Cargar Imagen Pesada", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not ruta: return 

        uid = f"foto_{int(time.time())}"
        self.motor.agregar_elemento(uid=uid, tipo="Foto", contenido=ruta, x=100, y=100, w=400, h=400)
        self.visor.sincronizar_con_motor()

    def exportar_pdf(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar Producción", "salida.pdf", "PDF (*.pdf)")
        if ruta:
            self.motor.exportar_pdf(ruta)
            print("PDF Exportado con máxima calidad.")


# ==========================================
# ARRANQUE (AQUÍ ESTÁ LA MAGIA DEL ANTIALIASING)
# ==========================================
if __name__ == "__main__":
    # 🚀 1. ESTO DEBE IR ESTRICTAMENTE ANTES DE QApplication
    gl_format = QSurfaceFormat()
    gl_format.setSamples(8)  # Fuerza 8 muestras de Antialiasing (Bordes de Navaja)
    gl_format.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
    QSurfaceFormat.setDefaultFormat(gl_format)

    # 2. Ahora sí iniciamos la app
    app = QApplication(sys.argv)
    ventana = VentanaMotorNativo()
    ventana.show()
    sys.exit(app.exec())