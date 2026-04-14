import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
                             QGraphicsPixmapItem, QGraphicsRectItem, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QFileDialog)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import Qt, QRectF

from motor_grafico import RectorOP # Tu backend matemático intacto

class RenderNativoQt(QGraphicsView):
    """
    Este es el NUEVO Motor de Interfaz. 
    Usa la GPU para mover imágenes gigantes sin pestañear.
    """
    def __init__(self, motor):
        super().__init__()
        self.motor = motor # Solo lo usamos para leer el diccionario y exportar
        
        # Optimizaciones extremas de GPU de Qt
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse) 
        self.setStyleSheet("background-color: #1a1a1a; border: none;")

        self.escena = QGraphicsScene()
        self.setScene(self.escena)
        
        # Diccionarios de caché NATIVA
        self.items_ui = {}       # Guarda los QGraphicsItem vivos
        self.cache_pixmaps = {}  # Guarda las texturas en VRAM (Tarjeta Gráfica)
        
        self._is_panning = False
        
        # Pintamos el fondo del lienzo (La hoja de papel en blanco)
        self.hoja_fondo = QGraphicsRectItem(0, 0, self.motor.w_pdf, self.motor.h_pdf)
        self.hoja_fondo.setBrush(QBrush(QColor("#FFFFFF")))
        self.escena.addItem(self.hoja_fondo)

    def sincronizar_con_motor(self):
        """
        LA MAGIA: Lee la matemática de RectorOP y actualiza los objetos en la GPU.
        NO renderiza PDFs, solo mueve coordenadas en la pantalla.
        """
        # 1. Ajustar el tamaño del lienzo
        self.hoja_fondo.setRect(0, 0, self.motor.w_pdf, self.motor.h_pdf)
        self.escena.setSceneRect(-500, -500, self.motor.w_pdf + 1000, self.motor.h_pdf + 1000)

        # 2. Iterar sobre los elementos del backend
        for uid, elem in self.motor.elementos.items():
            if elem.get('oculto', False):
                if uid in self.items_ui: self.items_ui[uid].setVisible(False)
                continue

            # Si el objeto no existe en la UI, lo creamos
            if uid not in self.items_ui:
                self._crear_item_qt(uid, elem)

            # 3. ACTUALIZAR POSICIÓN Y ESTADO (60 FPS)
            item = self.items_ui[uid]
            item.setVisible(True)
            
            # Matemática de coordenadas (PDF a Qt)
            x = elem['x']
            # En PDF 'y' es abajo, en Qt 'y' es arriba. Invertimos:
            y_qt = self.motor.h_pdf - (elem['y'] + elem['h']) 
            
            item.setPos(x, y_qt)
            item.setZValue(elem.get('z_index', 0))
            
            # Rotación Nativa (Pivotando en el centro exacto)
            rot = elem.get('rotacion', 0.0)
            item.setTransformOriginPoint(elem['w']/2, elem['h']/2)
            item.setRotation(-rot) # Invertimos el ángulo para coincidir con el PDF

    def _crear_item_qt(self, uid, elem):
        """Fabrica el objeto visual según su tipo."""
        tipo = elem['tipo']
        
        if tipo == 'Foto':
            item = QGraphicsPixmapItem()
            ruta = str(elem['contenido'])
            
            # Carga optimizada de texturas (1 sola vez directo a la RAM de Qt)
            if ruta not in self.cache_pixmaps:
                pix = QPixmap(ruta)
                self.cache_pixmaps[ruta] = pix
            
            # Escalado ultrarrápido por hardware
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
            # Fallback temporal para textos y otras cosas (se pueden hacer con QGraphicsTextItem)
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
        self.setWindowTitle("RectorOP + Qt Native GPU Engine")
        self.resize(1000, 700)

        self.motor = RectorOP()
        self.motor.crear_lienzo_vacio(842, 595) # A4 Apaisado

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout = QHBoxLayout(widget_central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Panel de Controles
        panel = QWidget()
        panel.setFixedWidth(200)
        layout_panel = QVBoxLayout(panel)

        btn_foto = QPushButton("Cargar Bestia de 10MB")
        btn_foto.clicked.connect(self.cargar_bestia)
        layout_panel.addWidget(btn_foto)
        
        btn_exportar = QPushButton("Exportar PDF Final (HD)")
        btn_exportar.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_exportar.clicked.connect(self.exportar_pdf)
        layout_panel.addWidget(btn_exportar)

        layout_panel.addStretch()
        layout.addWidget(panel)

        # Visor Acelerado
        self.visor = RenderNativoQt(self.motor)
        layout.addWidget(self.visor)
        self.visor.sincronizar_con_motor()

    def cargar_bestia(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Cargar Imagen Pesada", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not ruta: return 

        uid = f"foto_{int(time.time())}"
        # Metemos la matemática al backend
        self.motor.agregar_elemento(uid=uid, tipo="Foto", contenido=ruta, x=100, y=100, w=400, h=400)
        
        # Le decimos a la GPU que dibuje lo nuevo
        self.visor.sincronizar_con_motor()

    def exportar_pdf(self):
        # AQUI ES DONDE BRILLA REPORTLAB. Solo cuando el usuario lo pide.
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar Producción", "salida.pdf", "PDF (*.pdf)")
        if ruta:
            self.motor.exportar_pdf(ruta)
            print("PDF Exportado con máxima calidad.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaMotorNativo()
    ventana.show()
    sys.exit(app.exec())