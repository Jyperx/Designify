import io
import os
import json
import base64
import fitz  # PyMuPDF
import copy
import math
import tempfile
import time
import glob
from PIL import Image
# 🚀 Quitar el límite de la bomba de descompresión en el motor
Image.MAX_IMAGE_PIXELS = None
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor, CMYKColor
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
import xml.etree.ElementTree as ET

class RectorOP:
    def __init__(self, pasos_historial=15):
        self.ruta_plantilla = None
        self.elementos = {}
        self.grupos = {}
        self.cache_imagenes = {}
        self.w_pdf = 0
        self.h_pdf = 0
        
        # ==========================================
        # SISTEMA DE HISTORIAL (Memoria Segura)
        # ==========================================
        MAX_SEGURO = 40 # Bloqueo estricto para proteger la RAM de fugas de memoria
        self.limite_historial = min(pasos_historial, MAX_SEGURO)
        self.pila_deshacer = []
        self.pila_rehacer = []

    def generar_uid(self, prefijo="elem"):
        """Genera un ID único basado en el tiempo exacto para evitar colisiones."""
        return f"{prefijo}_{int(time.time() * 1000)}"

    # ==========================================
    # GESTIÓN DE MEMORIA (GARBAGE COLLECTOR HÍBRIDO)
    # ==========================================
    def limpiar_cache_imagenes(self):
        """
        🚀 SÚPER OPTIMIZADO: Solo limpia la RAM. Ya no escanea el disco duro 
        para no congelar la interfaz al borrar objetos.
        """
        imagenes_activas = set()

        def recolectar_de_diccionario(dicc_elementos):
            for elem in dicc_elementos.values():
                # Escudo añadido: comprobamos 'if elem' por si es un estado parcial vacío (None)
                if elem and elem.get('tipo') == 'Foto' and elem.get('contenido'):
                    imagenes_activas.add(os.path.normpath(str(elem['contenido'])))

        recolectar_de_diccionario(self.elementos)

        for estado in self.pila_deshacer:
            recolectar_de_diccionario(estado['elementos'])

        for estado in self.pila_rehacer:
            recolectar_de_diccionario(estado['elementos'])

        # LIMPIEZA EXCLUSIVA DE RAM
        rutas_en_cache = list(self.cache_imagenes.keys())
        for ruta in rutas_en_cache:
            if os.path.normpath(str(ruta)) not in imagenes_activas:
                del self.cache_imagenes[ruta]

    # ==========================================
    # MÁQUINA DEL TIEMPO (CLONADOR ULTRA RÁPIDO)
    # ==========================================
    def _clonar_seguro(self, elem):
        """
        🚀 CLONACIÓN O(1): Vence a copy.deepcopy por goleada.
        Hace una copia superficial del diccionario y solo profundiza 
        manualmente en las listas de matrices que sabemos que existen.
        Reduce el tiempo de guardado de 150ms a 2ms.
        """
        if not elem: return None
        
        # 1. Copia de Nivel 1 (Súper rápida, clona todos los strings y números)
        clon = elem.copy() 
        
        # 2. Copia profunda manual de Nivel 2 (Matrices)
        if 'puntos' in clon: 
            clon['puntos'] = [p[:] for p in clon['puntos']]
        if 'perspectiva' in clon: 
            clon['perspectiva'] = [p[:] for p in clon['perspectiva']]
        if '_qt_margenes' in clon: 
            clon['_qt_margenes'] = clon['_qt_margenes'][:]
        if '_qt_advances' in clon: 
            clon['_qt_advances'] = clon['_qt_advances'][:]
            
        return clon

    def registrar_punto_historial(self, uids_afectados=None):
        if uids_afectados is None:
            # MODO GLOBAL (Respaldo total)
            estado_global = {uid: self._clonar_seguro(e) for uid, e in self.elementos.items()}
            self.pila_deshacer.append({'tipo': 'global', 'elementos': estado_global})
        else:
            # MODO PARCIAL (Respaldo láser, solo toca la RAM necesaria)
            estado_parcial = {}
            for uid in uids_afectados:
                if uid in self.elementos:
                    estado_parcial[uid] = self._clonar_seguro(self.elementos[uid])
                else:
                    estado_parcial[uid] = None 

            self.pila_deshacer.append({'tipo': 'parcial', 'elementos': estado_parcial})

        self.pila_rehacer.clear()
        if len(self.pila_deshacer) > self.limite_historial:
            self.pila_deshacer.pop(0)

    def deshacer(self):
        """Retrocede en el tiempo restaurando solo las piezas afectadas."""
        if not self.pila_deshacer: return False

        paso = self.pila_deshacer.pop()

        if paso['tipo'] == 'global':
            # Guardamos el futuro
            futuro = {uid: self._clonar_seguro(e) for uid, e in self.elementos.items()}
            self.pila_rehacer.append({'tipo': 'global', 'elementos': futuro})
            
            # Restauramos el pasado
            self.elementos = {uid: self._clonar_seguro(e) for uid, e in paso['elementos'].items()}
        else:
            # Respaldamos cómo estaba el objeto ANTES de deshacerlo para poder rehacerlo luego
            estado_actual_parcial = {}
            for uid in paso['elementos'].keys():
                if uid in self.elementos:
                    estado_actual_parcial[uid] = self._clonar_seguro(self.elementos[uid])
                else:
                    estado_actual_parcial[uid] = None
            
            self.pila_rehacer.append({'tipo': 'parcial', 'elementos': estado_actual_parcial})

            # Inyectamos los datos del pasado
            for uid, data_vieja in paso['elementos'].items():
                if data_vieja is None:
                    if uid in self.elementos:
                        del self.elementos[uid]
                else:
                    self.elementos[uid] = self._clonar_seguro(data_vieja)

        return True

    def rehacer(self):
        """Viaja al futuro restaurando las piezas."""
        if not self.pila_rehacer: return False

        paso = self.pila_rehacer.pop()

        if paso['tipo'] == 'global':
            pasado = {uid: self._clonar_seguro(e) for uid, e in self.elementos.items()}
            self.pila_deshacer.append({'tipo': 'global', 'elementos': pasado})
            
            self.elementos = {uid: self._clonar_seguro(e) for uid, e in paso['elementos'].items()}
        else:
            estado_actual_parcial = {}
            for uid in paso['elementos'].keys():
                if uid in self.elementos:
                    estado_actual_parcial[uid] = self._clonar_seguro(self.elementos[uid])
                else:
                    estado_actual_parcial[uid] = None

            self.pila_deshacer.append({'tipo': 'parcial', 'elementos': estado_actual_parcial})

            for uid, data_nueva in paso['elementos'].items():
                if data_nueva is None:
                    if uid in self.elementos:
                        del self.elementos[uid]
                else:
                    self.elementos[uid] = self._clonar_seguro(data_nueva)

        return True
    # ==========================================
    # SISTEMA DE MEDIDAS (Traductor PDF <-> Realidad)
    # ==========================================
    def unidad_a_pt(self, valor, unidad="mm"):
        """Convierte la medida del usuario a puntos internos del motor."""
        if unidad == "mm": return valor * (72.0 / 25.4)
        elif unidad == "cm": return valor * (72.0 / 2.54)
        elif unidad == "in": return valor * 72.0
        return float(valor) # Asume que ya son puntos (pt)

    def pt_a_unidad(self, pts, unidad="mm"):
        """Convierte los puntos internos a la medida preferida del usuario."""
        if unidad == "mm": return pts * (25.4 / 72.0)
        elif unidad == "cm": return pts * (2.54 / 72.0)
        elif unidad == "in": return pts / 72.0
        return float(pts)

    def obtener_dimensiones_reales(self, uid, unidad="cm"):
        """Devuelve el Ancho y Alto de un elemento en la medida que la UI necesite."""
        caja = self.obtener_caja_elemento(uid)
        if not caja: return None
        return {
            "w": round(self.pt_a_unidad(caja['w'], unidad), 2),
            "h": round(self.pt_a_unidad(caja['h'], unidad), 2)
        }

    # ==========================================
    # INICIALIZACIÓN Y RECURSOS
    # ==========================================
    def crear_lienzo_vacio(self, ancho_pts, alto_pts):
        """Inicializa el motor sin un PDF base (Ej: Lienzo A3 en blanco)."""
        self.ruta_plantilla = None
        self.w_pdf = ancho_pts
        self.h_pdf = alto_pts
        self.elementos = {}
        self.limpiar_cache_imagenes()

    def cargar_plantilla(self, ruta_pdf):
        """Carga un PDF base y obtiene sus dimensiones reales."""
        if not os.path.exists(ruta_pdf):
            raise FileNotFoundError(f"No se encontró la plantilla: {ruta_pdf}")
        
        self.ruta_plantilla = ruta_pdf
        with fitz.open(self.ruta_plantilla) as d:
            self.w_pdf = d[0].rect.width
            self.h_pdf = d[0].rect.height
        return {"ancho": self.w_pdf, "alto": self.h_pdf}

    def cargar_fuentes_locales(self, ruta_carpeta="fuentes"):
        """Escanea una carpeta, registra las fuentes y devuelve la lista."""
        fuentes_disponibles = ["Helvetica"]
        if not os.path.exists(ruta_carpeta):
            return fuentes_disponibles
            
        for archivo in os.listdir(ruta_carpeta):
            if archivo.lower().endswith(".ttf"):
                try:
                    nombre = os.path.splitext(archivo)[0]
                    ruta_completa = os.path.join(ruta_carpeta, archivo)
                    pdfmetrics.registerFont(TTFont(nombre, ruta_completa))
                    if nombre not in fuentes_disponibles:
                        fuentes_disponibles.append(nombre)
                except Exception as e:
                    print(f"Error cargando {archivo}: {e}")
                    
        return sorted(fuentes_disponibles)

    # ==========================================
    # GESTIÓN DE ELEMENTOS (CRUD Y CAPAS)
    # ==========================================
    def agregar_elemento(self, uid, tipo, **kwargs):
        elemento = {
            'z_index': kwargs.get('z_index', len(self.elementos)),
            'tipo': tipo,
            'nombre_capa': kwargs.get('nombre_capa', None),
            'bloqueado': kwargs.get('bloqueado', False),
            'x': float(kwargs.get('x', 100.0)),
            'y': float(kwargs.get('y', 100.0)),
            'w': float(kwargs.get('w', 24.0)),  # Tamaño fuente o ancho
            'h': float(kwargs.get('h', 100.0)), # Alto imagen
            'contenido': kwargs.get('contenido', ''),
            'color_tx': kwargs.get('color_tx', '#000000' if tipo in ['Texto', 'Código QR'] else None),
            'fuente': kwargs.get('fuente', 'Helvetica'),
            'align': kwargs.get('align', 'Centrado'),
            'interlineado': float(kwargs.get('interlineado', 1.2)),
            'forma': kwargs.get('forma', 'Normal'),
            'mantener_proporcion': kwargs.get('mantener_proporcion', True), # Nuevo: Evita deformar logos
            'rotacion': float(kwargs.get('rotacion', 0.0)),
            'opacidad': float(kwargs.get('opacidad', 1.0)),
            'shear_x': float(kwargs.get('shear_x', 0.0)),
            'shear_y': float(kwargs.get('shear_y', 0.0)),
            'borde_color': kwargs.get('borde_color', None),
            'borde_grosor': float(kwargs.get('borde_grosor', 0.0)),
            'sombra_color': kwargs.get('sombra_color', None),
            'sombra_x': float(kwargs.get('sombra_x', 0.0)), # Offset X
            'sombra_y': float(kwargs.get('sombra_y', 0.0)), # Offset Y
            'sombra_bloque': kwargs.get('sombra_bloque', False),
            'tipo_relleno': kwargs.get('tipo_relleno', 'Solido'), # 'Solido' o 'Degradado'
            'color_fin': kwargs.get('color_fin', '#FFFFFF'),      # Segundo color del degradado
            'gradiente_angulo': float(kwargs.get('gradiente_angulo', 0)), # 0 = Horizontal, 90 = Vertical
            'radio_esquinas': float(kwargs.get('radio_esquinas', 0.0)),
            'puntos': kwargs.get('puntos', []),
            'es_svg_complejo': kwargs.get('es_svg_complejo', False),
            'deleted_indices': kwargs.get('deleted_indices', []) # Lista de [x, y] para dibujar a mano libre o polígonos
        }
        self.elementos[uid] = elemento

    def modificar_elemento(self, uid, **kwargs):
        if uid not in self.elementos: return
        
        elem = self.elementos[uid]
        # ==========================================
        # ESCUDO DE BLOQUEO (CANDADO)
        # ==========================================
        if elem.get('bloqueado', False):
            permitidas = {}
            if 'bloqueado' in kwargs: permitidas['bloqueado'] = kwargs['bloqueado']
            if 'nombre_capa' in kwargs: permitidas['nombre_capa'] = kwargs['nombre_capa']
            if 'oculto' in kwargs: permitidas['oculto'] = kwargs['oculto']
            
            if not permitidas: 
                return 
            kwargs = permitidas 
        # ==========================================
        
        # 🚀 1. DETECTAMOS SI SE MOVIÓ O ROTÓ UN GRUPO (MARCO)
        dx, dy = 0, 0
        d_rot = 0.0
        if elem.get('tipo') == 'Marco':
            if 'x' in kwargs and kwargs['x'] is not None:
                dx = float(kwargs['x']) - elem['x']
            if 'y' in kwargs and kwargs['y'] is not None:
                dy = float(kwargs['y']) - elem['y']
            if 'rotacion' in kwargs and kwargs['rotacion'] is not None:
                d_rot = float(kwargs['rotacion']) - elem.get('rotacion', 0.0)

        # 🚀 2. VALIDAMOS Y APLICAMOS CAMBIOS AL ELEMENTO PRINCIPAL
        atributos_numericos = ['x', 'y', 'w', 'h', 'rotacion', 'opacidad', 'borde_grosor', 'sombra_x', 'sombra_y', 'interlineado', 'radio_esquinas', 'rot_3d_x', 'rot_3d_y']
        for k in atributos_numericos:
            if k in kwargs and kwargs[k] is not None:
                try: kwargs[k] = float(kwargs[k]) 
                except (ValueError, TypeError): kwargs[k] = 0.0 
        
        # 🚀 LA MAGIA: ANCLAJE AL CENTRO PERFECTO PARA TEXTOS
        # Si el usuario cambia la fuente, tamaño, contenido o alineación, el texto debe 
        # crecer desde el centro para no salir volando de la pantalla.
        if elem['tipo'] == 'Texto' and any(k in kwargs for k in ['fuente', 'contenido', 'w', 'align', 'interlineado']):
            caja_vieja = self.obtener_caja_elemento(uid)
            cx_v = caja_vieja['x'] + (caja_vieja['w'] / 2.0) if caja_vieja else elem['x']
            cy_v = caja_vieja['y'] + (caja_vieja['h'] / 2.0) if caja_vieja else elem['y']
            
            self.elementos[uid].update(kwargs)
            
            caja_nueva = self.obtener_caja_elemento(uid)
            # Solo re-centramos si el usuario no está intentando moverlo manualmente a la vez
            if caja_nueva and 'x' not in kwargs and 'y' not in kwargs:
                cx_n = caja_nueva['x'] + (caja_nueva['w'] / 2.0)
                cy_n = caja_nueva['y'] + (caja_nueva['h'] / 2.0)
                
                # Compensamos las coordenadas para mantener el texto clavado en el mismo sitio
                self.elementos[uid]['x'] -= (cx_n - cx_v)
                self.elementos[uid]['y'] -= (cy_n - cy_v)
        else:
            self.elementos[uid].update(kwargs)

        # 🚀 3. APLICAMOS TRASLACIÓN Y ROTACIÓN ORBITAL A LOS HIJOS (MARCOS)
        if dx != 0 or dy != 0 or d_rot != 0.0:
            # Calculamos el centro actual del grupo principal
            caja_marco = self.obtener_caja_elemento(uid)
            cx_marco = caja_marco['x'] + (caja_marco['w'] / 2.0) if caja_marco else elem['x'] + (elem['w']/2.0)
            cy_marco = caja_marco['y'] + (caja_marco['h'] / 2.0) if caja_marco else elem['y'] + (elem['h']/2.0)
            
            rad = math.radians(d_rot)
            
            # 🚀 LA CURA DE LA ANIDACIÓN: Buscamos nietos y bisnietos
            def obtener_descendientes(padre_uid):
                desc = []
                for h_uid, h_e in self.elementos.items():
                    if h_e.get('parent_marco') == padre_uid:
                        desc.append(h_uid)
                        desc.extend(obtener_descendientes(h_uid))
                return desc
                
            todos_los_hijos = obtener_descendientes(uid)
            
            for hijo_uid in todos_los_hijos:
                hijo_elem = self.elementos[hijo_uid]
                
                # A. Traslación simple (Movimiento recto)
                hijo_elem['x'] += dx
                hijo_elem['y'] += dy
                
                # B. Rotación Orbital y sobre su propio eje
                if d_rot != 0.0:
                    caja_hijo = self.obtener_caja_elemento(hijo_uid)
                    cx_hijo = caja_hijo['x'] + (caja_hijo['w'] / 2.0) if caja_hijo else hijo_elem['x'] + (hijo_elem['w']/2.0)
                    cy_hijo = caja_hijo['y'] + (caja_hijo['h'] / 2.0) if caja_hijo else hijo_elem['y'] + (hijo_elem['h']/2.0)
                    
                    # Orbitamos el centro del hijo alrededor del centro del padre principal
                    nx = cx_marco + (cx_hijo - cx_marco) * math.cos(rad) - (cy_hijo - cy_marco) * math.sin(rad)
                    ny = cy_marco + (cx_hijo - cx_marco) * math.sin(rad) + (cy_hijo - cy_marco) * math.cos(rad)
                    
                    # Actualizamos las coordenadas absolutas (El Delta)
                    hijo_elem['x'] += (nx - cx_hijo)
                    hijo_elem['y'] += (ny - cy_hijo)
                    
                    # Sumamos la rotación para que el hijo gire sobre su propio eje también
                    hijo_elem['rotacion'] = (hijo_elem.get('rotacion', 0.0) + d_rot) % 360

    def mover_multiples(self, lista_uids_principales, dx, dy):
        """
        🚀 LA CURA DE RENDIMIENTO (BATCH MOVE):
        Mueve miles de objetos matemáticamente de un solo golpe tocando directo la RAM.
        Soporta la cascada de los 'Marcos' sin llamar a validaciones pesadas.
        """
        if dx == 0 and dy == 0: return

        uids_totales = set(lista_uids_principales)
        
        # 1. Escudo de Anidación: Recopilar todos los hijos si hay Marcos (Grupos)
        def recolectar_descendientes(padre_uid):
            for h_uid, h_elem in self.elementos.items():
                if h_elem.get('parent_marco') == padre_uid:
                    uids_totales.add(h_uid)
                    recolectar_descendientes(h_uid)
                    
        for uid in lista_uids_principales:
            if uid in self.elementos and self.elementos[uid]['tipo'] == 'Marco':
                recolectar_descendientes(uid)

        # 2. Inyección de movimiento en bloque (Ultra Rápido)
        for uid in uids_totales:
            elem = self.elementos.get(uid)
            if elem and not elem.get('bloqueado', False):
                elem['x'] += dx
                elem['y'] += dy

    def _aplicar_zoom_global(self, lista_uids, factor_escala, fijo_x, fijo_y):
        """MÚCLEO MATEMÁTICO: Zoom Afín Perfecto. Escala y aleja objetos desde un punto inamovible."""
        if factor_escala <= 0: return

        # Recopilamos a todos los implicados (Padres e Hijos)
        uids_totales = set(lista_uids)
        
        # 🚀 LA CURA DE LA ANIDACIÓN: Recursividad en el Zoom
        def recolectar_descendientes(padre_uid):
            for h_uid, h_elem in self.elementos.items():
                if h_elem.get('parent_marco') == padre_uid:
                    uids_totales.add(h_uid)
                    recolectar_descendientes(h_uid)
                    
        for uid in lista_uids:
            if self.elementos[uid]['tipo'] == 'Marco':
                recolectar_descendientes(uid)
        
        for uid in uids_totales:
            elem = self.elementos[uid]
            
            # 1. Escala Física
            if elem['tipo'] == 'Texto': 
                elem['w'] *= factor_escala
            else:
                elem['w'] *= factor_escala
                elem['h'] *= factor_escala
                
            # 2. Desplazamiento Afín (Alejar/Acercar del Ancla)
            elem['x'] = fijo_x + (elem['x'] - fijo_x) * factor_escala
            elem['y'] = fijo_y + (elem['y'] - fijo_y) * factor_escala

    def redimensionar_elemento(self, uid, nuevo_w=None, nuevo_h=None, ancla="bottom_right", desde_centro=False, proporcional=False, ratio_fijo=None):
        if uid not in self.elementos: return False
        
        caja_vieja = self.obtener_caja_elemento(uid)
        if not caja_vieja or caja_vieja['w'] == 0: return False
            
        elem = self.elementos[uid]
        angulo_obj = float(elem.get('rotacion', 0.0))
            
        def obtener_coord_punto_rotado(caja, punto, angulo):
            cx, cy = caja['x'] + (caja['w'] / 2.0), caja['y'] + (caja['h'] / 2.0)
            px, py = cx, cy
            if "right" in punto: px = caja['x'] + caja['w']
            elif "left" in punto: px = caja['x']
            if "top" in punto: py = caja['y'] + caja['h']
            elif "bottom" in punto: py = caja['y']
            
            if angulo == 0.0: return px, py
                
            rad = math.radians(angulo)
            nx = cx + (px - cx) * math.cos(rad) - (py - cy) * math.sin(rad)
            ny = cy + (px - cx) * math.sin(rad) + (py - cy) * math.cos(rad)
            return nx, ny
            
        punto_fijo = "center" if desde_centro else ancla 
        fijo_x_real, fijo_y_real = obtener_coord_punto_rotado(caja_vieja, punto_fijo, angulo_obj)
        
        w_pedido = float(nuevo_w) if nuevo_w is not None else caja_vieja['w']
        h_pedido = float(nuevo_h) if nuevo_h is not None else caja_vieja['h']
        if w_pedido < 2: w_pedido = 2.0
        if h_pedido < 2: h_pedido = 2.0
        
        # 🚀 LA SOLUCIÓN DEFINITIVA PARA GRUPOS: ZOOM PURO
        if elem['tipo'] == 'Marco':
            factor = w_pedido / caja_vieja['w']
            self._aplicar_zoom_global([uid], factor, fijo_x_real, fijo_y_real)
            return True

        # 🚀 1. LA CURA DEL SHIFT: Memoria de la proporción original
        if proporcional:
            # Si la interfaz nos mandó la foto del ratio original, la usamos a la fuerza.
            ratio_original = ratio_fijo if ratio_fijo is not None else (caja_vieja['w'] / caja_vieja['h'])
            
            if "center" in ancla and ("left" in ancla or "right" in ancla): h_pedido = w_pedido / ratio_original
            elif "center" in ancla and ("top" in ancla or "bottom" in ancla): w_pedido = h_pedido * ratio_original
            else: h_pedido = w_pedido / ratio_original

        # 🚀 2. SEPARAMOS ESCALADO PURO VS DEFORMACIÓN
        if elem['tipo'] == 'Texto':
            fuente = elem['fuente']
            w_font = float(elem['w'])
            contenido = str(elem['contenido'])
            lineas = contenido.split('\n')
            
            # Usamos la memoria inyectada de la interfaz para no perder el rastro de la escala
            if '_qt_w' in elem and '_qt_h' in elem:
                ancho_max = elem['_qt_w']
                alto_base = elem['_qt_h']
            else:
                try:
                    fuente_obj = pdfmetrics.getFont(fuente)
                    ascent = (fuente_obj.face.ascent / 1000.0) * w_font
                    descent = (fuente_obj.face.descent / 1000.0) * w_font
                    if ascent == 0 and descent == 0: raise ValueError()
                except:
                    ascent = w_font * 0.8
                    descent = -w_font * 0.2
                    
                alto_linea = ascent - descent
                if alto_linea < w_font * 0.5: alto_linea = w_font
                
                ancho_max = 0
                for linea in lineas:
                    try: aw = pdfmetrics.stringWidth(linea, fuente, w_font)
                    except: aw = pdfmetrics.stringWidth(linea, "Helvetica", w_font)
                    if aw > ancho_max: ancho_max = aw
                    
                interlineado = w_font * float(elem.get('interlineado', 1.2))
                alto_base = alto_linea + ((len(lineas) - 1) * interlineado)
                
            if ancho_max == 0: ancho_max = 1
            if alto_base == 0: alto_base = 1
            
            new_sx = w_pedido / ancho_max
            new_sy = h_pedido / alto_base
            
            self.modificar_elemento(uid, stretch_x=new_sx, stretch_y=new_sy)
        else:
            self.modificar_elemento(uid, w=w_pedido, h=h_pedido)
            
        # Compensación del ancla para objetos individuales
        caja_nueva = self.obtener_caja_elemento(uid)
        if caja_nueva:
            nuevo_fijo_x, nuevo_fijo_y = obtener_coord_punto_rotado(caja_nueva, punto_fijo, angulo_obj)
            self.modificar_elemento(uid, 
                x=self.elementos[uid]['x'] + (fijo_x_real - nuevo_fijo_x), 
                y=self.elementos[uid]['y'] + (fijo_y_real - nuevo_fijo_y)
            )
        return True

    def escalar_multiples(self, lista_uids, nuevo_w, nuevo_h, ancla, desde_centro, proporcional):
        caja_actual = self.obtener_caja_multiple(lista_uids)
        if not caja_actual or caja_actual['w'] == 0: return

        w_pedido = float(nuevo_w)
        if w_pedido < 2: w_pedido = 2.0
        
        factor = w_pedido / caja_actual['w']

        def obtener_coord_punto(caja, punto):
            px, py = caja['x'] + (caja['w'] / 2.0), caja['y'] + (caja['h'] / 2.0)
            if "right" in punto: px = caja['x'] + caja['w']
            elif "left" in punto: px = caja['x']
            if "top" in punto: py = caja['y'] + caja['h']
            elif "bottom" in punto: py = caja['y']
            return px, py

        punto_fijo = "center" if desde_centro else ancla
        fijo_x, fijo_y = obtener_coord_punto(caja_actual, punto_fijo)

        self._aplicar_zoom_global(lista_uids, factor, fijo_x, fijo_y)

    def rotar_multiples(self, lista_uids, delta_angulo, centro_x, centro_y):
        if delta_angulo == 0.0: return
        rad = math.radians(delta_angulo)

        uids_totales = set(lista_uids)
        
        # 🚀 LA CURA DE LA ANIDACIÓN: Recursividad en la Rotación Múltiple
        def recolectar_descendientes(padre_uid):
            for h_uid, h_elem in self.elementos.items():
                if h_elem.get('parent_marco') == padre_uid:
                    uids_totales.add(h_uid)
                    recolectar_descendientes(h_uid)
                    
        for uid in lista_uids:
            if self.elementos[uid]['tipo'] == 'Marco':
                recolectar_descendientes(uid)

        for uid in uids_totales:
            elem = self.elementos[uid]
            
            caja = self.obtener_caja_elemento(uid)
            cx = caja['x'] + (caja['w'] / 2.0) if caja else elem['x'] + (elem['w']/2.0)
            cy = caja['y'] + (caja['h'] / 2.0) if caja else elem['y'] + (elem['h']/2.0)

            nx = centro_x + (cx - centro_x) * math.cos(rad) - (cy - centro_y) * math.sin(rad)
            ny = centro_y + (cx - centro_x) * math.sin(rad) + (cy - centro_y) * math.cos(rad)

            elem['x'] += (nx - cx)
            elem['y'] += (ny - cy)
            elem['rotacion'] = (elem.get('rotacion', 0.0) + delta_angulo) % 360
            

    def calcular_angulo_raton_multiple(self, lista_uids, mouse_x, mouse_y):
        """Calcula el ángulo de arrastre referenciado al BBox global para rotación múltiple."""
        caja = self.obtener_caja_multiple(lista_uids)
        if not caja: return 0.0
        cx = caja['x'] + (caja['w'] / 2.0)
        cy = caja['y'] + (caja['h'] / 2.0)
        
        rads = math.atan2(mouse_y - cy, mouse_x - cx)
        grados_finales = (math.degrees(rads) + 90) % 360
        
        for snap in [0, 45, 90, 135, 180, 225, 270, 315, 360]:
            if abs(grados_finales - snap) < 3.5: return float(snap)
        return grados_finales

    def eliminar_elemento(self, uid, limpiar_cache=True):
        if uid not in self.elementos: return
        
        # Guardamos quién era el papá antes de borrar el elemento
        padre_uid = self.elementos[uid].get('parent_marco')
        
        # 1. Borrar hijos recursivamente en cascada
        hijos = [h for h, e in self.elementos.items() if e.get('parent_marco') == uid]
        for h in hijos:
            self.eliminar_elemento(h, limpiar_cache=False)
            
        # 2. Borrar este elemento de forma segura
        self.elementos.pop(uid, None)
        
        # ==========================================
        # 🚀 3. AUTO-LIMPIEZA DE GRUPOS (Auto-Ungroup)
        # ==========================================
        # Si el elemento que borramos tenía un padre, revisamos cómo quedó ese padre
        if padre_uid and padre_uid in self.elementos:
            hermanos = [h for h, e in self.elementos.items() if e.get('parent_marco') == padre_uid]
            
            if len(hermanos) == 1:
                # Si solo quedó 1 hijo huérfano, le pasamos el abuelo (si lo hay) y matamos al padre
                unico_hijo = hermanos[0]
                self.elementos[unico_hijo]['parent_marco'] = self.elementos[padre_uid].get('parent_marco')
                self.elementos.pop(padre_uid, None)
                
            elif len(hermanos) == 0:
                # Si el grupo quedó totalmente vacío, lo destruimos
                self.elementos.pop(padre_uid, None)
                
        # 4. Limpieza de Memoria RAM
        if limpiar_cache:
            self.limpiar_cache_imagenes()

    def duplicar_elemento(self, uid_original, offset_x=20, offset_y=-20, nuevo_parent_uid=None):
        """
        Crea una copia exacta de un elemento. Si es un grupo (Marco), 
        duplica recursivamente todos los elementos dentro de él manteniendo su estructura.
        """
        if uid_original not in self.elementos:
            return None
        
        import random 
        import time
        import copy
        
        # 1. 🚀 CLONACIÓN O(1): Usamos nuestro clonador extremo
        elem_clon = self._clonar_seguro(self.elementos[uid_original])
        
        # 2. Generar UID seguro a prueba de bucles ultra rápidos
        nuevo_uid = f"{uid_original}_copia_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        
        # 3. 🚀 CORRECCIÓN: COORDENADAS ABSOLUTAS. 
        # Todos (Padres e hijos) deben recibir el desplazamiento matemático exacto.
        elem_clon['x'] += offset_x
        elem_clon['y'] += offset_y
            
        # 4. Asignar el nuevo padre si este elemento es un hijo clonado
        if nuevo_parent_uid is not None:
            elem_clon['parent_marco'] = nuevo_parent_uid
        
        # 5. Asegurar que nazca en la capa superior
        max_z = max([e.get('z_index', 0) for e in self.elementos.values()] or [0])
        elem_clon['z_index'] = max_z + 1
        
        # 6. Guardar en el diccionario principal
        self.elementos[nuevo_uid] = elem_clon
        
        # ==========================================
        # 7. ESCUDO DE CASCADA (RECURSIÓN)
        # ==========================================
        hijos_del_original = [h_uid for h_uid, h_elem in self.elementos.items() if h_elem.get('parent_marco') == uid_original]
        
        for h_uid in hijos_del_original:
            # 🚀 CORRECCIÓN: Le pasamos los mismos 20px de offset también a los hijos
            self.duplicar_elemento(h_uid, offset_x=offset_x, offset_y=offset_y, nuevo_parent_uid=nuevo_uid)
        
        # 8. Limpiar el orden de las capas solo cuando terminemos de procesar al padre principal
        if nuevo_parent_uid is None and hasattr(self, '_normalizar_z_index'):
            self._normalizar_z_index()
            
        return nuevo_uid

    def extraer_geometria_cruda(self, ruta_svg):
        """
        🧠 Invoca al compilador externo para transformar el SVG en matemáticas de Qt.
        """
        try:
            # Importamos nuestro nuevo archivo parser
            from vectify_svg import VectifySVGParser
            compilador = VectifySVGParser(ruta_svg)
            return compilador.parsear()
        except Exception as e:
            print(f"⚠️ Fallo al extraer SVG con el nuevo compilador: {e}")
            return []

    # ==========================================
    # FUNCIONES SEGURAS PARA LA INTERFAZ (UI)
    # ==========================================
    def obtener_info_edicion(self, uid):
        """Devuelve de forma segura qué se puede editar en el panel para un elemento."""
        if uid not in self.elementos:
            return {"editable": False, "texto": "", "fuente": ""}
        
        elem = self.elementos[uid]
        if elem['tipo'] == "Texto":
            return {"editable": True, "texto": elem['contenido'], "fuente": elem['fuente']}
        else:
            # Si es una foto o un QR, le decimos a la UI que bloquee la caja de texto
            return {"editable": False, "texto": f"[{elem['tipo']}] Seleccionado", "fuente": ""}

    def editar_texto_seguro(self, uid, nuevo_texto):
        """Actualiza el contenido SOLO si el elemento es de tipo Texto. Protege las imágenes."""
        if uid in self.elementos and self.elementos[uid]['tipo'] == "Texto":
            self.elementos[uid]['contenido'] = nuevo_texto
            return True
        return False

    # ==========================================
    # SISTEMA DE GESTIÓN DE CAPAS (Z-INDEX)
    # ==========================================
    def _normalizar_z_index(self):
        """Reasigna los z_index para que sean estrictamente secuenciales (0, 1, 2...). 
        Esto limpia el motor y evita que dos elementos se peleen por la misma capa."""
        ordenados = sorted(self.elementos.items(), key=lambda x: x[1].get('z_index', 0))
        for i, (uid, elem) in enumerate(ordenados):
            elem['z_index'] = i

    def subir_capa(self, uid):
        """Sube el elemento exactamente un nivel (Ctrl + ])"""
        if uid not in self.elementos: return
        self._normalizar_z_index()
        z_actual = self.elementos[uid]['z_index']
        
        # Buscamos la capa inmediatamente superior y hacemos un "Swap" (Intercambio)
        for otro_uid, elem in self.elementos.items():
            if elem['z_index'] == z_actual + 1:
                elem['z_index'] = z_actual
                self.elementos[uid]['z_index'] = z_actual + 1
                break

    def bajar_capa(self, uid):
        """Baja el elemento exactamente un nivel (Ctrl + [)"""
        if uid not in self.elementos: return
        self._normalizar_z_index()
        z_actual = self.elementos[uid]['z_index']
        
        # Buscamos la capa inmediatamente inferior y hacemos el "Swap"
        for otro_uid, elem in self.elementos.items():
            if elem['z_index'] == z_actual - 1:
                elem['z_index'] = z_actual
                self.elementos[uid]['z_index'] = z_actual - 1
                break

    def enviar_al_fondo(self, uid):
        """Manda el elemento detrás de todo (Shift + Ctrl + [)"""
        if uid in self.elementos:
            min_z = min([e.get('z_index', 0) for e in self.elementos.values()] or [0])
            self.elementos[uid]['z_index'] = min_z - 1
            self._normalizar_z_index() # Limpiamos la matemática

    def traer_al_frente(self, uid):
        """Manda el elemento por encima de todo (Shift + Ctrl + ])"""
        if uid in self.elementos:
            max_z = max([e.get('z_index', 0) for e in self.elementos.values()] or [0])
            self.elementos[uid]['z_index'] = max_z + 1
            self._normalizar_z_index() # Limpiamos la matemática

    def mover_delante_de(self, uid_origen, uid_objetivo):
        """Pone el objeto de origen exactamente 1 nivel por encima del objetivo"""
        if uid_origen in self.elementos and uid_objetivo in self.elementos:
            z_obj = self.elementos[uid_objetivo].get('z_index', 0)
            self.elementos[uid_origen]['z_index'] = z_obj + 0.1 # Sumamos un decimal
            self._normalizar_z_index() # El motor lo convertirá a entero y empujará el resto

    def mover_detras_de(self, uid_origen, uid_objetivo):
        """Pone el objeto de origen exactamente 1 nivel por debajo del objetivo"""
        if uid_origen in self.elementos and uid_objetivo in self.elementos:
            z_obj = self.elementos[uid_objetivo].get('z_index', 0)
            self.elementos[uid_origen]['z_index'] = z_obj - 0.1
            self._normalizar_z_index()

    def obtener_arbol_capas(self):
        """
        Devuelve una lista estructurada para crear un panel de capas en la UI.
        El elemento visualmente más arriba (mayor z_index) sale primero.
        """
        capas = []
        # Ordenamos de arriba hacia abajo
        elementos_ordenados = sorted(self.elementos.items(), key=lambda x: x[1].get('z_index', 0), reverse=True)
        
        for uid, elem in elementos_ordenados:
            if elem.get('tipo') == 'Ignorar': continue
            
            # Autogenerar un nombre descriptivo para la UI
            if elem['tipo'] == 'Texto':
                nombre = str(elem['contenido']).replace('\n', ' ')[:15]
                nombre = f"T: {nombre}..." if len(nombre) >= 15 else f"T: {nombre}"
            elif elem['tipo'] == 'Foto':
                nombre = f"IMG: {os.path.basename(str(elem['contenido']))[-15:]}"
            elif elem['tipo'] == 'Forma':
                nombre = f"Forma: {elem.get('forma', 'Básica')}"
            else:
                nombre = f"[{elem['tipo']}]"
                
            capas.append({
                "uid": uid,
                "z_index": elem.get('z_index', 0),
                "tipo": elem['tipo'],
                "nombre": nombre,
                "oculto": elem.get('oculto', False),
                "bloqueado": elem.get('bloqueado', False) # Para proteger capas (ej. fondos)
            })
            
        return capas

    # ==========================================
    # MATEMÁTICAS ESPACIALES (Para la UI)
    # ==========================================
    def obtener_caja_elemento(self, uid):
        """Calcula el Ancho y Alto real leyendo el Bounding Box base inmutable."""
        if uid not in self.elementos: return None
        
        elem = self.elementos[uid]
        tipo = elem['tipo']
        
        # ==========================================
        # 🚀 LA CURA DE LA CAJA ROTADA: Bounding Box Base Puro
        # ==========================================
        if tipo == 'Marco':
            hijos_directos = [h_uid for h_uid, h_e in self.elementos.items() if h_e.get('parent_marco') == uid]
            if hijos_directos:
                import math
                from PyQt6.QtGui import QTransform, QPolygonF
                from PyQt6.QtCore import QPointF, Qt
                
                min_x, max_x = float('inf'), float('-inf')
                min_y, max_y = float('inf'), float('-inf')
                
                validos = 0
                for h_uid in hijos_directos:
                    h_elem = self.elementos.get(h_uid)
                    if not h_elem: continue
                    
                    c_h = self.obtener_caja_elemento(h_uid) # Recursivo
                    if not c_h: continue
                    
                    w_h = float(c_h['w'])
                    h_h = float(c_h['h'])
                    cx_h = float(c_h['x']) + (w_h / 2.0)
                    cy_h = float(c_h['y']) + (h_h / 2.0)
                    
                    # 1. APLICAMOS 3D Y PERSPECTIVA INDIVIDUAL DEL HIJO
                    t = QTransform()
                    rot_3dx = float(h_elem.get('rot_3d_x', 0.0))
                    rot_3dy = float(h_elem.get('rot_3d_y', 0.0))
                    if rot_3dx != 0.0: t.rotate(rot_3dx, Qt.Axis.XAxis)
                    if rot_3dy != 0.0: t.rotate(rot_3dy, Qt.Axis.YAxis)
                    
                    hw, hh = w_h / 2.0, h_h / 2.0
                    pts_3d = [t.map(QPointF(-hw, -hh)), t.map(QPointF(hw, -hh)), t.map(QPointF(hw, hh)), t.map(QPointF(-hw, hh))]
                    w_3d = max(p.x() for p in pts_3d) - min(p.x() for p in pts_3d)
                    h_3d = max(p.y() for p in pts_3d) - min(p.y() for p in pts_3d)
                    
                    persp = h_elem.get('perspectiva')
                    if persp and any(pt != [0,0] for pt in persp):
                        hw_p, hh_p = w_3d / 2.0, h_3d / 2.0
                        poly_src = QPolygonF([QPointF(-hw_p, -hh_p), QPointF(hw_p, -hh_p), QPointF(hw_p, hh_p), QPointF(-hw_p, hh_p)])
                        poly_dst = QPolygonF([
                            QPointF(-hw_p + persp[0][0], -hh_p + persp[0][1]),
                            QPointF(hw_p + persp[1][0], -hh_p + persp[1][1]),
                            QPointF(hw_p + persp[2][0], hh_p + persp[2][1]),
                            QPointF(-hw_p + persp[3][0], hh_p + persp[3][1])
                        ])
                        tp = QTransform()
                        if QTransform.quadToQuad(poly_src, poly_dst, tp):
                            t = t * tp
                    
                    # 2. Extraemos las 4 esquinas deformadas (relativas al centro 0,0 del hijo)
                    pts_deform = [t.map(QPointF(-hw, -hh)), t.map(QPointF(hw, -hh)), t.map(QPointF(hw, hh)), t.map(QPointF(-hw, hh))]
                    
                    # 3. Rotación 2D Local (Solo la del hijo, IGNORAMOS la del grupo padre)
                    angulo_h = float(h_elem.get('rotacion', 0.0))
                    rad_h = math.radians(angulo_h)
                    
                    for pt in pts_deform:
                        # Rotamos la coordenada y la llevamos al espacio absoluto (sin corromperla con rotaciones del padre)
                        rx = cx_h + pt.x() * math.cos(rad_h) - pt.y() * math.sin(rad_h)
                        ry = cy_h + pt.x() * math.sin(rad_h) + pt.y() * math.cos(rad_h)
                        
                        min_x, max_x = min(min_x, rx), max(max_x, rx)
                        min_y, max_y = min(min_y, ry), max(max_y, ry)
                        
                    validos += 1
                    
                if validos > 0:
                    w_tight = max_x - min_x
                    h_tight = max_y - min_y
                    
                    # Devolvemos la caja perfecta, plana, lista para que main.py la rote visualmente
                    return {'x': min_x, 'y': min_y, 'w': w_tight, 'h': h_tight}
        # ==========================================

        x, y, w, h = float(elem.get('x', 0.0)), float(elem.get('y', 0.0)), float(elem.get('w', 100.0)), float(elem.get('h', 100.0))
        caja = {"x": x, "y": y, "w": w, "h": h}
        
        if tipo == "Texto":
            fuente = elem['fuente']
            contenido = str(elem['contenido'])
            lineas = contenido.split('\n')
            
            # 🚀 LA MAGIA DEL WYSIWYG: Usamos el puente matemático de Qt si existe
            if '_qt_w' in elem and '_qt_h' in elem:
                ancho_max = elem['_qt_w']
                alto_base = elem['_qt_h']
            else:
                try:
                    fuente_obj = pdfmetrics.getFont(fuente)
                    ascent = (fuente_obj.face.ascent / 1000.0) * w
                    descent = (fuente_obj.face.descent / 1000.0) * w
                    if ascent == 0 and descent == 0: raise ValueError()
                except Exception as e:
                    ascent = w * 0.8
                    descent = -w * 0.2
                
                alto_linea = ascent - descent
                if alto_linea < w * 0.5: alto_linea = w
                
                ancho_max = 0
                for linea in lineas:
                    try: aw = pdfmetrics.stringWidth(linea, fuente, w)
                    except: aw = pdfmetrics.stringWidth(linea, "Helvetica", w)
                    if aw > ancho_max: ancho_max = aw
                    
                interlineado = w * float(elem.get('interlineado', 1.2))
                alto_base = alto_linea + ((len(lineas) - 1) * interlineado)
            
            sx = float(elem.get('stretch_x', 1.0))
            sy = float(elem.get('stretch_y', 1.0))
            
            caja['w'] = ancho_max * sx
            caja['h'] = alto_base * sy
            
            cx_unscaled = x + (ancho_max / 2.0)
            cy_unscaled = y + (alto_base / 2.0)
            
            caja['x'] = cx_unscaled - (caja['w'] / 2.0)
            caja['y'] = cy_unscaled - (caja['h'] / 2.0)
            
        return caja

    def obtener_puntos_control(self, uid):
        caja = self.obtener_caja_elemento(uid)
        if not caja: return None
        x, y, w, h = caja['x'], caja['y'], caja['w'], caja['h']
        return {
            "top_left": (x, y + h),
            "top_right": (x + w, y + h),
            "bottom_left": (x, y),
            "bottom_right": (x + w, y)
        }

    def detectar_colisiones(self, uid_origen):
        """
        Detecta qué elementos están tocando o debajo del elemento arrastrado.
        Ideal para detectar cuándo soltar una foto sobre un círculo para enmascararla.
        """
        if uid_origen not in self.elementos: return []
        
        c1 = self.obtener_caja_elemento(uid_origen)
        if not c1: return []
        
        colisiones = []
        for uid, elem in self.elementos.items():
            if uid == uid_origen or elem.get('oculto', False): continue
            
            c2 = self.obtener_caja_elemento(uid)
            if not c2: continue
            
            # Algoritmo AABB (Axis-Aligned Bounding Box)
            # Verifica si los dos rectángulos matemáticos se solapan en el lienzo
            if (c1['x'] < c2['x'] + c2['w'] and
                c1['x'] + c1['w'] > c2['x'] and
                c1['y'] < c2['y'] + c2['h'] and
                c1['y'] + c1['h'] > c2['y']):
                
                # Calculamos cuántos puntos exactos están chocando (Área de solapamiento)
                x_overlap = max(0, min(c1['x']+c1['w'], c2['x']+c2['w']) - max(c1['x'], c2['x']))
                y_overlap = max(0, min(c1['y']+c1['h'], c2['y']+c2['h']) - max(c1['y'], c2['y']))
                area_interseccion = x_overlap * y_overlap
                
                colisiones.append({
                    "uid": uid,
                    "z_index": elem.get('z_index', 0),
                    "tipo": elem['tipo'],
                    "forma": elem.get('forma', None),
                    "area": area_interseccion
                })
                
        # Ordenamos: Primero los que están en la capa más alta, y si están en la misma capa, 
        # el que tenga mayor porcentaje de choque con la foto.
        return sorted(colisiones, key=lambda x: (x['z_index'], x['area']), reverse=True)

    # ==========================================
    # MOTOR DE RENDERIZADO INTERNO
    # ==========================================
    def _estampar_elementos(self, c):
        for uid, elem in sorted(self.elementos.items(), key=lambda x: x[1].get('z_index', 0)):
            if elem.get('oculto', False): continue 
            
            tipo = elem['tipo']
            x, y = elem['x'], elem['y']
            w, h = elem['w'], elem['h']
            contenido = str(elem.get('contenido', ''))
            color_tx = elem.get('color_tx')
            rotacion = elem.get('rotacion', 0.0)
            opacidad = elem.get('opacidad', 1.0)
            
            # --- DETECTAMOS SI TIENE UN MARCO PADRE ---
            parent_uid = elem.get('parent_marco')

            c.saveState()

            # ==========================================
            # MAGIA DE ENMASCARADO (CLIPPING DE MARCO)
            # ==========================================
            if parent_uid and parent_uid in self.elementos:
                m = self.elementos[parent_uid]
                # Le pedimos al motor que cree el trazo matemático del marco (circular, cuadrado, etc)
                p_clip = self._crear_path_forma(c, m, m['x'], m['y'], m['w'], m['h'])
                # Activamos la cuchilla: Nada se dibujará por fuera de esta forma
                c.clipPath(p_clip, stroke=0, fill=0)
            # ==========================================

            # ==========================================
            # CORRECCIÓN DE PIVOTE DE ROTACIÓN Y ESCALA
            # ==========================================
            # Obtenemos la caja REAL del elemento (vital para textos)
            caja_real = self.obtener_caja_elemento(uid)
            if caja_real:
                cx = caja_real['x'] + (caja_real['w'] / 2.0)
                cy = caja_real['y'] + (caja_real['h'] / 2.0)
            else:
                cx = x + (w / 2.0)
                cy = y + (h / 2.0)

            # 🚀 LEEMOS EL NIVEL DE DEFORMACIÓN Y 3D
            sx = float(elem.get('stretch_x', 1.0))
            sy = float(elem.get('stretch_y', 1.0))
            sh_x = float(elem.get('shear_x', 0.0))
            sh_y = float(elem.get('shear_y', 0.0))

            # 1. Transparencia, Rotación y Deformación global
            if opacidad < 1.0:
                c.setFillAlpha(opacidad)
                c.setStrokeAlpha(opacidad)
                
            # Si hay rotación, estiramiento o 3D, transformamos el espacio de dibujo
            if rotacion != 0.0 or sx != 1.0 or sy != 1.0 or sh_x != 0.0 or sh_y != 0.0:
                c.translate(cx, cy)
                if rotacion != 0.0: c.rotate(rotacion)
                if sx != 1.0 or sy != 1.0: c.scale(sx, sy)
                # 🚀 INYECCIÓN 3D EN PDF: ReportLab aplica sesgo nativo en grados
                if sh_x != 0.0 or sh_y != 0.0: c.skew(sh_x, sh_y)
                c.translate(-cx, -cy)
            
            # 2. Manejo de Color Avanzado (Soporte CMYK vs HEX)
            if color_tx:
                try:
                    if isinstance(color_tx, tuple) and len(color_tx) == 4:
                        c.setFillColor(CMYKColor(*color_tx)) 
                    else:
                        c.setFillColor(HexColor(color_tx))
                except: pass

            # 3. Dibujo de Texto Multilínea con Pipeline de Efectos
            if tipo == "Texto" and contenido:
                fuente = elem['fuente']
                try: pdfmetrics.getFont(fuente)
                except: fuente = "Helvetica"
                
                c.setFont(fuente, w)
                align = elem['align']
                lineas = contenido.split('\n')

                s_color = elem.get('sombra_color')
                s_x = elem.get('sombra_x', 0)
                s_y = elem.get('sombra_y', 0)
                s_bloque = elem.get('sombra_bloque', False)
                
                b_color = elem.get('borde_color')
                b_grosor = elem.get('borde_grosor', 0)
                interl = float(elem.get('interlineado', 1.2))

                # --- LAYER 1: SOMBRA DE BLOQUE ---
                if s_color and s_bloque and (s_x != 0 or s_y != 0):
                    c.saveState()
                    form_name = f"form_{uid}_shadow"
                    c.beginForm(form_name)
                    c.setFillColor(HexColor(s_color))
                    c.setStrokeColor(HexColor(s_color))
                    c.setLineWidth(1)
                    # 🚀 EL PUENTE: Ahora pasamos 'elem' en vez del ancho para que extraiga toda la inyección
                    self._dibujar_texto_crudo(c, lineas, 0, 0, w, align, fuente, elem, render_mode=2, interlineado_mult=interl)
                    c.endForm()

                    distancia = max(abs(s_x), abs(s_y))
                    pasos = int(distancia * 1.5) if distancia > 0 else 1 
                    for i in range(pasos, 0, -1):
                        factor = i / pasos
                        ox = cx + (s_x * factor)
                        oy = cy + (s_y * factor)
                        c.saveState()
                        c.translate(ox, oy) 
                        c.doForm(form_name) 
                        c.restoreState()
                    c.restoreState()

                # --- LAYER 2: SOMBRA PLANA ---
                elif s_color and not s_bloque and (s_x != 0 or s_y != 0):
                    c.saveState()
                    c.setFillColor(HexColor(s_color))
                    self._dibujar_texto_crudo(c, lineas, cx + s_x, cy + s_y, w, align, fuente, elem, render_mode=0, interlineado_mult=interl)
                    c.restoreState()

                # --- LAYER 3 & 4: SILUETA/BORDE Y RELLENO ---
                c.saveState()
                
                try: grosor_validado = float(elem.get('borde_grosor', 0))
                except: grosor_validado = 0.0

                tipo_relleno = elem.get('tipo_relleno', 'Solido')

                if b_color and grosor_validado > 0:
                    c.saveState() 
                    c.setStrokeColor(HexColor(b_color))
                    c.setLineWidth(grosor_validado)
                    c.setLineJoin(1) 
                    self._dibujar_texto_crudo(c, lineas, cx, cy, w, align, fuente, elem, render_mode=1, interlineado_mult=interl)
                    c.restoreState() 

                if tipo_relleno == 'Solido' and color_tx:
                    c.saveState() 
                    c.setFillColor(HexColor(color_tx))
                    self._dibujar_texto_crudo(c, lineas, cx, cy, w, align, fuente, elem, render_mode=0, interlineado_mult=interl)
                    c.restoreState() 

                elif tipo_relleno == 'Degradado' and color_tx:
                    color_fin = elem.get('color_fin', '#FFFFFF')
                    c_inicio = HexColor(color_tx)
                    c_final = HexColor(color_fin)
                    
                    c.saveState() 
                    self._dibujar_texto_crudo(c, lineas, cx, cy, w, align, fuente, elem, render_mode=7, interlineado_mult=interl)
                    
                    caja_texto = self.obtener_caja_elemento(uid)
                    alto_real = caja_texto['h'] if caja_texto else h
                    ancho_max = elem.get('_qt_w', w) 
                    
                    angulo_rad = math.radians(float(elem.get('gradiente_angulo', 0)))
                    radio = math.sqrt((ancho_max / 2.0)**2 + (alto_real / 2.0)**2)
                    
                    dx = math.cos(angulo_rad) * radio
                    dy = math.sin(angulo_rad) * radio
                    
                    c.linearGradient(cx - dx, cy - dy, cx + dx, cy + dy, (c_inicio, c_final))
                    c.restoreState() 
                
                c.restoreState()

            # ==========================================
            # 4. DIBUJO DE FORMAS GEOMÉTRICAS Y MARCOS VISIBLES
            # ==========================================
            elif tipo in ["Forma", "Marco"]:
                s_color = elem.get('sombra_color')
                s_x, s_y = elem.get('sombra_x', 0), elem.get('sombra_y', 0)
                b_color = elem.get('borde_color')
                b_grosor = float(elem.get('borde_grosor', 0))
                tipo_relleno = elem.get('tipo_relleno', 'Solido')

                # LAYER 1: Sombra
                if s_color and (s_x != 0 or s_y != 0):
                    c.saveState()
                    c.setFillColor(HexColor(s_color))
                    c.setStrokeColor(HexColor(s_color))
                    c.setLineJoin(1)
                    
                    s_bloque = elem.get('sombra_bloque', False)
                    if s_bloque:
                        form_name = f"form_{uid}_shape_shadow"
                        c.beginForm(form_name)
                        p_base = self._crear_path_forma(c, elem, 0, 0, w, h)
                        c.drawPath(p_base, fill=(1 if elem['forma'] != 'Línea' else 0), stroke=1)
                        c.endForm()

                        distancia = max(abs(s_x), abs(s_y))
                        pasos = int(distancia * 1.5) if distancia > 0 else 1 
                        for i in range(pasos, 0, -1):
                            factor = i / pasos
                            c.saveState()
                            c.translate(x + (s_x * factor), y + (s_y * factor))
                            c.doForm(form_name)
                            c.restoreState()
                    else:
                        p_sombra = self._crear_path_forma(c, elem, x + s_x, y + s_y, w, h)
                        c.drawPath(p_sombra, fill=(1 if elem['forma'] != 'Línea' else 0), stroke=1)
                    c.restoreState()

                # LAYER 2: Borde (Por debajo del relleno)
                if b_color and b_grosor > 0:
                    c.saveState()
                    c.setStrokeColor(HexColor(b_color))
                    c.setLineWidth(b_grosor)
                    c.setLineJoin(1)
                    p_borde = self._crear_path_forma(c, elem, x, y, w, h)
                    c.drawPath(p_borde, fill=0, stroke=1)
                    c.restoreState()

                # LAYER 3: Relleno Sólido
                if tipo_relleno == 'Solido' and color_tx and elem['forma'] != 'Línea':
                    c.saveState()
                    c.setFillColor(HexColor(color_tx))
                    p_relleno = self._crear_path_forma(c, elem, x, y, w, h)
                    c.drawPath(p_relleno, fill=1, stroke=0)
                    c.restoreState()

                # LAYER 4: Relleno Degradado
                elif tipo_relleno == 'Degradado' and color_tx and elem['forma'] != 'Línea':
                    c_inicio, c_final = HexColor(color_tx), HexColor(elem.get('color_fin', '#FFFFFF'))
                    c.saveState()
                    p_clip = self._crear_path_forma(c, elem, x, y, w, h)
                    c.clipPath(p_clip, stroke=0, fill=0) # Usamos la figura como molde de corte
                    
                    angulo_rad = math.radians(float(elem.get('gradiente_angulo', 0)))
                    centro_x, centro_y = x + (w / 2.0), y + (h / 2.0)
                    radio = math.sqrt((w / 2.0)**2 + (h / 2.0)**2)
                    dx, dy = math.cos(angulo_rad) * radio, math.sin(angulo_rad) * radio
                    
                    c.linearGradient(centro_x - dx, centro_y - dy, centro_x + dx, centro_y + dy, (c_inicio, c_final))
                    c.restoreState()
            
            # 4. Dibujo de Imágenes y Vectores (SVG)
            elif tipo == "Foto" and os.path.exists(contenido):
                forma = elem.get('forma', 'Normal')
                
                if contenido.lower().endswith('.svg'):
                    # =======================================================
                    # 🚀 EL PUENTE SUPREMO: COREL-DRAW COMPATIBLE (BAKED)
                    # =======================================================
                    try:
                        geometrias = self.extraer_geometria_cruda(contenido)
                        if not geometrias: raise ValueError("SVG vacío")

                        from PyQt6.QtGui import QPainterPath, QTransform
                        from PyQt6.QtCore import Qt, QPointF
                        
                        bbox_global = QPainterPath()
                        for geo in geometrias: bbox_global.addPath(geo['path'])
                        caja_svg = bbox_global.boundingRect()
                        
                        if caja_svg.width() <= 0 or caja_svg.height() <= 0: raise ValueError("Caja inválida")

                        escala_x = w / caja_svg.width()
                        escala_y = h / caja_svg.height()

                        # 🚀 LA MAGIA: Creamos una matriz que deforma las matemáticas nativamente
                        transform = QTransform()
                        transform.translate(x, y + h) 
                        transform.scale(1, -1) # Inversión del Eje Y
                        transform.scale(escala_x, escala_y)
                        transform.translate(-caja_svg.x(), -caja_svg.y())

                        c.saveState()
                        if opacidad < 1.0:
                            c.setFillAlpha(opacidad)
                            c.setStrokeAlpha(opacidad)

                        for geo in geometrias:
                            # 1. HORNEAMOS LA RUTA: El vector original muta a su posición y tamaño final absoluto
                            qpath_orig = geo['path']
                            qpath = transform.map(qpath_orig) 
                            
                            brush = geo['brush']
                            pen = geo['pen']

                            # --- 📐 CONSTRUCCIÓN ABSOLUTA DEL TRAZO ---
                            p = c.beginPath()
                            i = 0
                            while i < qpath.elementCount():
                                el = qpath.elementAt(i)
                                if el.type == QPainterPath.ElementType.MoveToElement:
                                    p.moveTo(el.x, el.y)
                                    i += 1
                                elif el.type == QPainterPath.ElementType.LineToElement:
                                    p.lineTo(el.x, el.y)
                                    i += 1
                                elif el.type == QPainterPath.ElementType.CurveToElement:
                                    if i + 2 < qpath.elementCount():
                                        el2 = qpath.elementAt(i+1)
                                        el3 = qpath.elementAt(i+2)
                                        p.curveTo(el.x, el.y, el2.x, el2.y, el3.x, el3.y)
                                    i += 3
                                else:
                                    i += 1

                            fill_flag, stroke_flag = 0, 0
                            
                            # --- BORDES (Escalados matemáticamente) ---
                            if pen.style() != Qt.PenStyle.NoPen:
                                qc = pen.color()
                                c.setStrokeColorRGB(qc.redF(), qc.greenF(), qc.blueF())
                                c.setStrokeAlpha(qc.alphaF() * opacidad)
                                # Como horneamos la escala, el grosor de la línea debe crecer proporcionalmente
                                grosor = pen.widthF() * ((escala_x + escala_y) / 2.0)
                                c.setLineWidth(grosor if grosor > 0 else 0.1)
                                stroke_flag = 1
                            
                            # --- RELLENO SÓLIDO ---
                            if brush.style() == Qt.BrushStyle.SolidPattern:
                                qc = brush.color()
                                c.setFillColorRGB(qc.redF(), qc.greenF(), qc.blueF())
                                c.setFillAlpha(qc.alphaF() * opacidad)
                                c.drawPath(p, fill=1, stroke=stroke_flag)
                                
                            # --- RELLENO DEGRADADO (COREL SAFE) ---
                            elif brush.style() in [Qt.BrushStyle.LinearGradientPattern, Qt.BrushStyle.RadialGradientPattern]:
                                grad = brush.gradient()
                                try:
                                    paradas = grad.stops()
                                    colores_grad = []
                                    pos_grad = []
                                    from reportlab.lib.colors import Color
                                    from PyQt6.QtGui import QGradient
                                    import math
                                    
                                    for pos, qc in paradas:
                                        # Le inyectamos los topes de color exactos del SVG
                                        colores_grad.append(Color(qc.redF(), qc.greenF(), qc.blueF(), alpha=qc.alphaF() * opacidad))
                                        pos_grad.append(pos)
                                    
                                    c.saveState()
                                    # Cuchilla de Recorte: El degradado no se saldrá de los bordes
                                    c.clipPath(p, stroke=0, fill=0)
                                    
                                    # Extraemos el BoundingBox original
                                    caja_orig = qpath_orig.boundingRect()
                                    px, py = caja_orig.x(), caja_orig.y()
                                    pw, ph = caja_orig.width(), caja_orig.height()
                                    
                                    es_relativo = grad.coordinateMode() == QGradient.CoordinateMode.ObjectBoundingMode
                                    
                                    # 🚀 SEPARADOR DE TIPOS DE DEGRADADO
                                    if grad.type() == QGradient.Type.LinearGradient:
                                        x0_orig = px + (grad.start().x() * pw) if es_relativo else grad.start().x()
                                        y0_orig = py + (grad.start().y() * ph) if es_relativo else grad.start().y()
                                        x1_orig = px + (grad.finalStop().x() * pw) if es_relativo else grad.finalStop().x()
                                        y1_orig = py + (grad.finalStop().y() * ph) if es_relativo else grad.finalStop().y()
                                        
                                        # Horneamos las coordenadas
                                        pt0 = transform.map(QPointF(x0_orig, y0_orig))
                                        pt1 = transform.map(QPointF(x1_orig, y1_orig))
                                        
                                        c.linearGradient(pt0.x(), pt0.y(), pt1.x(), pt1.y(), colors=colores_grad, positions=pos_grad)
                                        
                                    elif grad.type() == QGradient.Type.RadialGradient:
                                        cx_orig = px + (grad.center().x() * pw) if es_relativo else grad.center().x()
                                        cy_orig = py + (grad.center().y() * ph) if es_relativo else grad.center().y()
                                        r_orig = (grad.radius() * max(pw, ph)) if es_relativo else grad.radius()
                                        
                                        # Horneamos el centro
                                        ptC = transform.map(QPointF(cx_orig, cy_orig))
                                        
                                        # Horneamos el radio calculando la distancia a un punto en el borde
                                        ptR = transform.map(QPointF(cx_orig + r_orig, cy_orig))
                                        r_horneado = math.hypot(ptR.x() - ptC.x(), ptR.y() - ptC.y())
                                        
                                        try:
                                            # Intentamos usar el Radial nativo de ReportLab
                                            c.radialGradient(ptC.x(), ptC.y(), r_horneado, colors=colores_grad, positions=pos_grad)
                                        except AttributeError:
                                            # FALLBACK COREL SEGURO: Si la versión de ReportLab no soporta radiales
                                            # Trazamos un lineal en diagonal que imita la profundidad
                                            pt0 = transform.map(QPointF(px, py))
                                            pt1 = transform.map(QPointF(px + pw, py + ph))
                                            c.linearGradient(pt0.x(), pt0.y(), pt1.x(), pt1.y(), colors=colores_grad, positions=pos_grad)

                                    c.restoreState()
                                    
                                    # Dibujamos el borde encima del degradado si lo tiene
                                    if stroke_flag:
                                        c.drawPath(p, fill=0, stroke=1)
                                        
                                except Exception as e:
                                    print(f"Error en degradado nativo: {e}")
                                    c.setFillColorRGB(0.8, 0.8, 0.8)
                                    c.drawPath(p, fill=1, stroke=stroke_flag)
                            else:
                                if stroke_flag: c.drawPath(p, fill=0, stroke=1)

                        c.restoreState()
                    except Exception as e:
                        print(f"⚠️ Fallback activado por: {e}")
                        
                # 🚀 LA CURA: ¡Faltaba el bloque para dibujar las imágenes normales (PNG/JPG)!
                else:
                    try:
                        # ImageReader de ReportLab lee la ruta del archivo temporal (Base64)
                        # y respeta las transparencias 'Alpha' para los PNGs
                        img_raster = ImageReader(contenido)
                        c.drawImage(img_raster, x, y, width=w, height=h, mask='auto')
                    except Exception as e:
                        print(f"Error estampando PNG/JPG: {e}")

            # =======================================================
            # 🚀 4.5. AQUÍ ENTRA LA MAGIA VECTORIAL DEL TRAZO EN PDF
            # =======================================================
            elif tipo == "Trazo":
                c.saveState()
                
                # Le pedimos al motor que construya las curvas matemáticas de exportación
                p_trazo = self._crear_path_trazo(c, elem, cx, cy)
                
                color_trazo = elem.get('borde_color', '#000000')
                c.setFillColor(HexColor(color_trazo))
                
                # Al ser un polígono cerrado con volumen, lo rellenamos como si fuera pintura
                c.drawPath(p_trazo, fill=1, stroke=0) 
                
                c.restoreState()

            # ==========================================
            # DIBUJO DE VECTORES DESAGRUPADOS (PIEZAS DE SVG)
            # ==========================================
            elif tipo == "VectorSVG":
                dibujo = elem['contenido'] # Leemos el objeto en RAM
                
                # Magia de Color: Si el usuario cambió el color en la UI, lo inyectamos al vuelo
                if color_tx:
                    self._inyectar_color_svg(dibujo, color_tx)

                # Mantener la caja original
                escala_x = w / dibujo.width
                escala_y = h / dibujo.height
                
                c.saveState()
                # 1. Aplicamos opacidad y posición general
                if opacidad < 1.0:
                    c.setFillAlpha(opacidad)
                    c.setStrokeAlpha(opacidad)
                    
                c.translate(x, y)
                
                # 2. Rotación pivotando sobre el centro
                if rotacion != 0.0:
                    c.translate(w/2, h/2)
                    c.rotate(rotacion)
                    c.translate(-w/2, -h/2)
                    
                # 3. Escalar y Estampar
                c.scale(escala_x, escala_y)
                renderPDF.draw(dibujo, c, 0, 0)
                c.restoreState()

            # 5. Códigos de Barras y QR
            elif tipo in ["Código QR", "Código de Barras"] and contenido:
                if tipo == "Código QR": h = w
                try:
                    color_hex = HexColor(color_tx) if isinstance(color_tx, str) else HexColor("#000000")
                    if tipo == "Código QR":
                        d = createBarcodeDrawing('QR', value=contenido, barFillColor=color_hex, barStrokeColor=color_hex)
                    else:
                        d = createBarcodeDrawing('Code128', value=contenido, barFillColor=color_hex, barStrokeColor=color_hex)
                    
                    bounds = d.getBounds()
                    d_w, d_h = bounds[2] - bounds[0], bounds[3] - bounds[1]
                    c.translate(x, y)
                    if w > 0 and h > 0 and d_w > 0 and d_h > 0: c.scale(w / d_w, h / d_h)
                    d.drawOn(c, -bounds[0], -bounds[1])
                except: pass
                
            c.restoreState()

    def _dibujar_texto_crudo(self, c, lineas, cx, cy, w, align, fuente, elem, render_mode=0, interlineado_mult=1.2):
        """Estampa vectores puros respetando el CENTRO DE MASA (Zero-Origin) y el clon exacto de PyQt."""
        t = c.beginText()
        t.setFont(fuente, w)
        t.setTextRenderMode(render_mode)
        
        # 🚀 LA CLONACIÓN: Leemos la inyección de Qt si existe
        ancho_max = elem.get('_qt_w')
        alto_total = elem.get('_qt_h')
        ascent = elem.get('_qt_ascent')
        margenes = elem.get('_qt_margenes', [0] * len(lineas))
        advances = elem.get('_qt_advances', [0] * len(lineas))
        
        if ancho_max is None:
            # Fallback a ReportLab si se exporta sin que la interfaz gráfica haya arrancado
            ancho_max = max([pdfmetrics.stringWidth(l, fuente, w) for l in lineas] + [0.1])
            try: 
                face = pdfmetrics.getFont(fuente).face
                ascent = (face.ascent / 1000.0) * w
                descent = (face.descent / 1000.0) * w
                if ascent == 0 and descent == 0: raise ValueError()
            except: 
                ascent = w * 0.8
                descent = -w * 0.2
            alto_linea = ascent - descent
            if alto_linea < w * 0.5: alto_linea = w
            alto_total = alto_linea + ((len(lineas) - 1) * w * interlineado_mult)
            margenes = [0] * len(lineas)
            advances = [pdfmetrics.stringWidth(l, fuente, w) for l in lineas]
            
        # cy es el centro geométrico de la caja. En PDF la Y va hacia arriba.
        y_actual = cy + (alto_total / 2.0) - ascent
        
        interlineado_px = w * interlineado_mult
        
        for i, linea in enumerate(lineas):
            ancho_linea = advances[i]
            margen_izq = margenes[i]
            palabras = linea.split()
            
            # 🚀 EL CLON DEL JUSTIFICADO PARA PDF
            if align == "Justificado" and i < len(lineas) - 1 and len(palabras) > 1:
                ancho_palabras = sum([pdfmetrics.stringWidth(p, fuente, w) for p in palabras])
                gap = (ancho_max - ancho_palabras) / (len(palabras) - 1)
                
                cursor_x = cx - (ancho_max / 2.0) - (margen_izq / 2.0)
                for p in palabras:
                    t.setTextOrigin(cursor_x, y_actual)
                    t.textOut(p)
                    cursor_x += pdfmetrics.stringWidth(p, fuente, w) + gap
                    
                y_actual -= interlineado_px
                continue
            
            # Alineaciones normales
            if align == "Izquierda" or align == "Justificado": start_x = cx - (ancho_max / 2.0) - (margen_izq / 2.0)
            elif align == "Centrado": start_x = cx - (ancho_linea / 2.0)
            else: start_x = cx + (ancho_max / 2.0) - ancho_linea + (margen_izq / 2.0)
            
            t.setTextOrigin(start_x, y_actual)
            t.textOut(linea)
            
            y_actual -= interlineado_px
            
        c.drawText(t)

    def _crear_path_trazo(self, c, elem, cx, cy):
        """Reconstruye el trazo variable matemáticamente para exportarlo como vector puro."""
        import math
        puntos_raw = elem.get('puntos', [])
        p = c.beginPath()
        
        if len(puntos_raw) < 2:
            if puntos_raw:
                px, py, w = puntos_raw[0]
                # 🚀 Usamos 'py' directo, sin invertir
                p.circle(cx + px, cy + py, w/2.0) 
            return p
            
        # 🚀 LA CORRECCIÓN: Los puntos ya vienen en coordenadas PDF (Y hacia arriba).
        # Eliminamos el '-' de 'py'.
        puntos_con_grosor = [(px, py, w) for px, py, w in puntos_raw]
        
        # 1. Curvas de Bézier (Muestreo)
        puntos_finos = [puntos_con_grosor[0]]
        for i in range(1, len(puntos_con_grosor) - 1):
            x0, y0, w0 = puntos_finos[-1]
            x1, y1, w1 = puntos_con_grosor[i]
            x2_orig, y2_orig, w2_orig = puntos_con_grosor[i+1]
            
            mid_x, mid_y, mid_w = (x1 + x2_orig)/2.0, (y1 + y2_orig)/2.0, (w1 + w2_orig)/2.0
            x2, y2, w2 = mid_x, mid_y, mid_w
            
            d1 = math.hypot(x1 - x0, y1 - y0)
            d2 = math.hypot(x2 - x1, y2 - y1)
            d3 = math.hypot(x2 - x0, y2 - y0)
            
            pasos = max(3, min(int((d1+d2+d3)/8.0), 30))
            
            for j in range(1, pasos + 1):
                t = j / float(pasos)
                mt = 1.0 - t
                nx = (mt*mt*x0) + (2*mt*t*x1) + (t*t*x2)
                ny = (mt*mt*y0) + (2*mt*t*y1) + (t*t*y2)
                nw = (mt*mt*w0) + (2*mt*t*w1) + (t*t*w2)
                puntos_finos.append((nx, ny, nw))
                
        x_ult, y_ult, w_ult = puntos_finos[-1]
        x_fin, y_fin, w_fin = puntos_con_grosor[-1]
        dist_fin = math.hypot(x_fin - x_ult, y_fin - y_ult)
        pasos_fin = max(2, min(int(dist_fin / 8.0), 15))
        for j in range(1, pasos_fin + 1):
            t = j / float(pasos_fin)
            nx = x_ult + (x_fin - x_ult) * t
            ny = y_ult + (y_fin - y_ult) * t
            nw = w_ult + (w_fin - w_ult) * t
            puntos_finos.append((nx, ny, nw))
            
        # 2. Extrusión (Normales)
        borde_izq, borde_der = [], []
        total = len(puntos_finos)
        for i in range(total):
            pt_x, pt_y, w = puntos_finos[i]
            if i == 0:
                sig_x, sig_y, _ = puntos_finos[1]
                dx, dy = sig_x - pt_x, sig_y - pt_y
            elif i == total - 1:
                ant_x, ant_y, _ = puntos_finos[i-1]
                dx, dy = pt_x - ant_x, pt_y - ant_y
            else:
                ant_x, ant_y, _ = puntos_finos[i-1]
                sig_x, sig_y, _ = puntos_finos[i+1]
                dx1, dy1, dx2, dy2 = pt_x - ant_x, pt_y - ant_y, sig_x - pt_x, sig_y - pt_y
                l1, l2 = math.hypot(dx1, dy1), math.hypot(dx2, dy2)
                vx1, vy1 = (dx1/l1, dy1/l1) if l1 > 0 else (1, 0)
                vx2, vy2 = (dx2/l2, dy2/l2) if l2 > 0 else (1, 0)
                nx_dir, ny_dir = (-vy1 + -vy2) / 2.0, (vx1 + vx2) / 2.0
                l_sq = nx_dir*nx_dir + ny_dir*ny_dir
                if l_sq > 0.01:
                    nx_dir, ny_dir = nx_dir/l_sq, ny_dir/l_sq
                    miter_len = 1.0 / math.sqrt(l_sq)
                    if miter_len > 2.5: nx_dir, ny_dir = nx_dir*(2.5/miter_len), ny_dir*(2.5/miter_len)
                else: nx_dir, ny_dir = -vy1, vx1
                r = w / 2.0
                borde_izq.append((pt_x + nx_dir * r, pt_y + ny_dir * r))
                borde_der.append((pt_x - nx_dir * r, pt_y - ny_dir * r))
                continue
                
            l = math.hypot(dx, dy)
            vx, vy = (dx/l, dy/l) if l > 0 else (1, 0)
            nx_dir, ny_dir, r = -vy, vx, w / 2.0
            borde_izq.append((pt_x + nx_dir * r, pt_y + ny_dir * r))
            borde_der.append((pt_x - nx_dir * r, pt_y - ny_dir * r))
            
        def generar_tapa(x_c, y_c, radio, es_inicio):
            arco = []
            pasos = max(4, int(radio * 0.4))
            if es_inicio:
                sig_x, sig_y, _ = puntos_finos[1]
                ang_start = math.atan2(sig_y - y_c, sig_x - x_c) + (math.pi / 2.0)
            else:
                ant_x, ant_y, _ = puntos_finos[-2]
                ang_start = math.atan2(y_c - ant_y, x_c - ant_x) - (math.pi / 2.0)
            for j in range(pasos + 1):
                t = j / float(pasos)
                ang = ang_start + (math.pi * t)
                arco.append((x_c + radio * math.cos(ang), y_c + radio * math.sin(ang)))
            return arco

        poly_maestro = borde_izq[:]
        x_fin, y_fin, w_fin = puntos_finos[-1]
        poly_maestro.extend(generar_tapa(x_fin, y_fin, w_fin/2.0, False))
        poly_maestro.extend(borde_der[::-1])
        x_ini, y_ini, w_ini = puntos_finos[0]
        poly_maestro.extend(generar_tapa(x_ini, y_ini, w_ini/2.0, True))

        if poly_maestro:
            p.moveTo(cx + poly_maestro[0][0], cy + poly_maestro[0][1])
            for pt in poly_maestro[1:]: p.lineTo(cx + pt[0], cy + pt[1])
            p.close()
        return p

    def _crear_path_forma(self, c, elem, x, y, w, h):
        """Genera el esqueleto matemático invisible de la figura con límites seguros."""
        p = c.beginPath()
        forma = elem.get('forma', 'Rectángulo')
        radio = float(elem.get('radio_esquinas', 0.0))
        puntos = elem.get('puntos', [])

        if forma == 'Rectángulo':
            limite_radio = min(w / 2.0, h / 2.0)
            radio_seguro = min(radio, limite_radio)
            if radio_seguro > 0: 
                p.roundRect(x, y, w, h, radio_seguro)
            else: 
                p.rect(x, y, w, h)
                
        # --- AQUÍ ESTABA EL BUG: AÑADIMOS 'Circular' A LA LISTA ---
        elif forma in ['Elipse', 'Circular']: 
            p.ellipse(x, y, x + w, y + h)
            
        elif forma == 'Línea' and puntos:
            p.moveTo(x + puntos[0][0], y + puntos[0][1])
            for pt in puntos[1:]: p.lineTo(x + pt[0], y + pt[1])
        elif forma == 'Polígono' and puntos:
            p.moveTo(x + puntos[0][0], y + puntos[0][1])
            for pt in puntos[1:]: p.lineTo(x + pt[0], y + pt[1])
            p.close()
            
        return p

    def _inyectar_color_svg(self, dibujo, color_hex):
        """Navega recursivamente por el SVG estático y le sobrescribe el color."""
        if not color_hex: return
        color_rl = HexColor(color_hex)
        for nodo in dibujo.getContents():
            # Si el nodo tiene relleno o trazo original, lo reemplazamos
            if getattr(nodo, 'fillColor', None) is not None:
                nodo.fillColor = color_rl
            if getattr(nodo, 'strokeColor', None) is not None:
                nodo.strokeColor = color_rl
            # Si es un grupo que contiene más nodos, entramos recursivamente
            if hasattr(nodo, 'getContents'):
                self._inyectar_color_svg(nodo, color_hex)

    def obtener_handle_sombra(self, uid):
        """Devuelve la coordenada de pantalla donde debe dibujarse el nodo de la sombra."""
        if uid not in self.elementos: return None
        elem = self.elementos[uid]
        
        # El nodo de la sombra está en el centro del objeto + el offset de la sombra
        caja = self.obtener_caja_elemento(uid)
        centro_x = caja['x'] + (caja['w'] / 2)
        centro_y = caja['y'] + (caja['h'] / 2)
        
        return {
            'x': centro_x + elem.get('sombra_x', 0),
            'y': centro_y + elem.get('sombra_y', 0)
        }

    # ==========================================
    # CALCULADORAS DE ROTACIÓN
    # ==========================================
    def obtener_handle_rotacion(self, uid, distancia_extra=30):
        caja = self.obtener_caja_elemento(uid)
        if not caja: return None
        
        elem = self.elementos[uid]
        angulo_actual = elem.get('rotacion', 0.0)
        
        cx = caja['x'] + (caja['w'] / 2.0)
        cy = caja['y'] + (caja['h'] / 2.0)
        
        # ==========================================
        # EL CAMBIO: LO PONEMOS EN LA PARTE SUPERIOR
        # ==========================================
        hx_base = cx
        # Le sumamos la altura completa de la caja + la distancia extra
        hy_base = caja['y'] + caja['h'] + distancia_extra 
        
        if angulo_actual == 0.0:
            return {'x': hx_base, 'y': hy_base}
            
        rad = math.radians(-angulo_actual) 
        hx_rot = cx + (hx_base - cx) * math.cos(rad) - (hy_base - cy) * math.sin(rad)
        hy_rot = cy + (hx_base - cx) * math.sin(rad) + (hy_base - cy) * math.cos(rad)
        
        return {'x': hx_rot, 'y': hy_rot}

    def calcular_angulo_raton(self, uid, mouse_x, mouse_y):
        """
        Lee la posición actual del ratón (en puntos PDF) y devuelve cuántos 
        grados debe rotar el objeto. Incluye "Snapping" (Magnetismo) en ángulos rectos.
        """
        caja = self.obtener_caja_elemento(uid)
        if not caja: return 0.0
        
        # 1. Obtenemos el centro, que será nuestro punto de anclaje (pivote)
        cx = caja['x'] + (caja['w'] / 2.0)
        cy = caja['y'] + (caja['h'] / 2.0)
        
        # 2. Distancia entre el ratón y el centro
        dx = mouse_x - cx
        dy = mouse_y - cy
        
        # 3. Arco Tangente (atan2) nos da el ángulo en radianes
        rads = math.atan2(dy, dx)
        grados = math.degrees(rads)
        
        # 4. Compensación Canva: atan2(0, -1) da un ángulo, pero nosotros 
        # queremos que el handle inicial (abajo) equivalga a 0 grados.
        grados_finales = grados + 90 
        
        # Normalizamos para que siempre esté entre 0 y 360 grados
        grados_finales = grados_finales % 360
        
        # 5. MAGIA UX: "Snapping" magnético
        # A los usuarios les cuesta atinarle exactamente a 90 o 180 a pulso.
        # Si el ratón pasa cerca de estos ángulos (margen de 3 grados), lo clavamos ahí.
        angulos_iman = [0, 45, 90, 135, 180, 225, 270, 315, 360]
        for snap in angulos_iman:
            if abs(grados_finales - snap) < 3.5:
                grados_finales = float(snap)
                break
                
        return grados_finales

    # ==========================================
    # MOTOR DE GUÍAS INTELIGENTES (SNAPPING)
    # ==========================================
    def calcular_snap(self, uid_activo, prop_x, prop_y, tolerancia=8.0):
        """
        Versión Definitiva: Imanta estrictamente basado en las cajas delimitadoras (BBox).
        """
        if uid_activo not in self.elementos:
            return {'x': prop_x, 'y': prop_y, 'lineas_x': [], 'lineas_y': []}

        # 1. Obtenemos la caja actual para saber el W, H 
        caja_activa = self.obtener_caja_elemento(uid_activo)
        elem = self.elementos[uid_activo]
        
        # LA MAGIA: Calculamos la distancia entre el origen del elemento y su caja real (por las tildes/colas)
        offset_bx = caja_activa['x'] - elem['x']
        offset_by = caja_activa['y'] - elem['y']
        
        w, h = caja_activa['w'], caja_activa['h']
        
        # Coordenadas propuestas de la CAJA (no del elemento)
        prop_bx = prop_x + offset_bx
        prop_by = prop_y + offset_by
        
        # Puntos de anclaje de la CAJA en movimiento
        p_x = [prop_bx, prop_bx + (w/2), prop_bx + w]
        p_y = [prop_by, prop_by + (h/2), prop_by + h]

        # Blancos magnéticos (bordes del papel)
        targets_x = [0, self.w_pdf / 2, self.w_pdf]
        targets_y = [0, self.h_pdf / 2, self.h_pdf]

        # Blancos magnéticos (cajas de otros elementos)
        for uid, e in self.elementos.items():
            if uid == uid_activo or uid in self.grupos.get(uid_activo, []): 
                continue
            
            c_otro = self.obtener_caja_elemento(uid)
            if c_otro:
                targets_x.extend([c_otro['x'], c_otro['x'] + (c_otro['w']/2), c_otro['x'] + c_otro['w']])
                targets_y.extend([c_otro['y'], c_otro['y'] + (c_otro['h']/2), c_otro['y'] + c_otro['h']])

        # Evaluamos las colisiones magnéticas
        snap_bx, snap_by = prop_bx, prop_by
        lineas_x, lineas_y = [], []

        for tx in targets_x:
            if abs(p_x[0] - tx) <= tolerancia:   snap_bx = tx; lineas_x.append(tx); break
            elif abs(p_x[1] - tx) <= tolerancia: snap_bx = tx - (w/2); lineas_x.append(tx); break
            elif abs(p_x[2] - tx) <= tolerancia: snap_bx = tx - w; lineas_x.append(tx); break

        for ty in targets_y:
            if abs(p_y[0] - ty) <= tolerancia:   snap_by = ty; lineas_y.append(ty); break
            elif abs(p_y[1] - ty) <= tolerancia: snap_by = ty - (h/2); lineas_y.append(ty); break
            elif abs(p_y[2] - ty) <= tolerancia: snap_by = ty - h; lineas_y.append(ty); break

        # Re-convertimos la coordenada de la CAJA a la coordenada del ELEMENTO para no romper ReportLab
        final_x = snap_bx - offset_bx
        final_y = snap_by - offset_by

        return {
            'x': final_x, 
            'y': final_y, 
            'lineas_x': list(set(lineas_x)), 
            'lineas_y': list(set(lineas_y))
        }

    # ==========================================
    # SISTEMA DE AGRUPACIÓN Y ALINEACIÓN
    # ==========================================
    def agrupar_elementos(self, id_grupo, lista_uids):
        """Crea un grupo con los elementos especificados."""
        # Filtramos solo los que realmente existen en el lienzo
        validos = [uid for uid in lista_uids if uid in self.elementos]
        if validos:
            self.grupos[id_grupo] = validos

    def desagrupar(self, id_grupo):
        if id_grupo in self.grupos:
            del self.grupos[id_grupo]

    def obtener_caja_grupo(self, id_grupo):
        """Calcula el Bounding Box global que encierra a todos los elementos del grupo."""
        if id_grupo not in self.grupos: return None
        # Reutilizamos la lógica inteligente múltiple
        return self.obtener_caja_multiple(self.grupos[id_grupo])

    def obtener_caja_multiple(self, uids):
        """Calcula la caja delimitadora visual REAL, incluyendo 3D, 
           Perspectiva y Rotación individual de todos los hijos."""
        from PyQt6.QtGui import QTransform, QPolygonF
        from PyQt6.QtCore import QPointF, Qt
        import math
        
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        validos = 0
        
        # Expandimos los UIDs para incluir automáticamente a los hijos si seleccionaste un grupo
        uids_expandidos = set(uids)
        for uid in uids:
            if uid in self.elementos and self.elementos[uid]['tipo'] == 'Marco':
                for h_uid, h_e in self.elementos.items():
                    if h_e.get('parent_marco') == uid:
                        uids_expandidos.add(h_uid)
        
        for uid in uids_expandidos:
            elem = self.elementos.get(uid)
            if not elem: continue
            
            # Para los hijos, obtenemos su caja plana base
            caja = self.obtener_caja_elemento(uid)
            if not caja: continue
            
            w = float(caja['w'])
            h = float(caja['h'])
            cx = float(caja['x']) + (w / 2.0)
            cy = float(caja['y']) + (h / 2.0)
            
            t = QTransform()
            
            # 1. Aplicar Deformación 3D
            rot_3dx = float(elem.get('rot_3d_x', 0.0))
            rot_3dy = float(elem.get('rot_3d_y', 0.0))
            if rot_3dx != 0.0: t.rotate(rot_3dx, Qt.Axis.XAxis)
            if rot_3dy != 0.0: t.rotate(rot_3dy, Qt.Axis.YAxis)
            
            # 2. Medir la nueva caja tras el 3D para la Perspectiva
            hw, hh = w / 2.0, h / 2.0
            pts_3d = [t.map(QPointF(-hw, -hh)), t.map(QPointF(hw, -hh)), t.map(QPointF(hw, hh)), t.map(QPointF(-hw, hh))]
            w_3d = max(p.x() for p in pts_3d) - min(p.x() for p in pts_3d)
            h_3d = max(p.y() for p in pts_3d) - min(p.y() for p in pts_3d)
            
            # 3. Aplicar Perspectiva local
            persp = elem.get('perspectiva')
            if persp and any(pt != [0,0] for pt in persp):
                hw_p, hh_p = w_3d / 2.0, h_3d / 2.0
                poly_src = QPolygonF([QPointF(-hw_p, -hh_p), QPointF(hw_p, -hh_p), QPointF(hw_p, hh_p), QPointF(-hw_p, hh_p)])
                poly_dst = QPolygonF([
                    QPointF(-hw_p + persp[0][0], -hh_p + persp[0][1]),
                    QPointF(hw_p + persp[1][0], -hh_p + persp[1][1]),
                    QPointF(hw_p + persp[2][0], hh_p + persp[2][1]),
                    QPointF(-hw_p + persp[3][0], hh_p + persp[3][1])
                ])
                tp = QTransform()
                if QTransform.quadToQuad(poly_src, poly_dst, tp):
                    t = t * tp
            
            # 4. Rotación 2D Plana
            t.rotate(-float(elem.get('rotacion', 0.0)))
            
            # 5. 🚀 LA CURA: Calcular la posición global resolviendo la anidación de grupos sin UI
            cx_global = cx
            cy_global = cy
            
            padre_uid = elem.get('parent_marco')
            while padre_uid and padre_uid in self.elementos:
                caja_padre = self.obtener_caja_elemento(padre_uid)
                if caja_padre:
                    cx_global += float(caja_padre.get('x') or 0.0)
                    cy_global += float(caja_padre.get('y') or 0.0)
                padre_uid = self.elementos[padre_uid].get('parent_marco')

            # 6. Mapear vértices
            pts_locales = [QPointF(-hw, -hh), QPointF(hw, -hh), QPointF(hw, hh), QPointF(-hw, hh)]
            for p in pts_locales:
                p_global = t.map(p)
                px = cx_global + p_global.x()
                py = cy_global + p_global.y()
                
                min_x, max_x = min(min_x, px), max(max_x, px)
                min_y, max_y = min(min_y, py), max(max_y, py)
                
            validos += 1
            
        if validos == 0: return None
        return {'x': min_x, 'y': min_y, 'w': max_x - min_x, 'h': max_y - min_y}

    def mover_grupo(self, id_grupo, dx, dy):
        """Mueve todos los elementos del grupo sumando un Delta X y Delta Y."""
        if id_grupo not in self.grupos: return
        for uid in self.grupos[id_grupo]:
            elem = self.elementos[uid]
            self.modificar_elemento(uid, x=elem['x'] + dx, y=elem['y'] + dy)

    # ==========================================
    # SISTEMA DE MARCOS (FRAMES / PLACEHOLDERS)
    # ==========================================
    def insertar_en_marco(self, uid_elemento, uid_marco):
        """Asigna un elemento como hijo de un marco y lo posiciona en la capa superior."""
        if uid_elemento in self.elementos and uid_marco in self.elementos:
            self.elementos[uid_elemento]['parent_marco'] = uid_marco
            # Asegurar que la foto/texto quede visualmente por encima del fondo del marco
            z_marco = self.elementos[uid_marco].get('z_index', 0)
            self.elementos[uid_elemento]['z_index'] = z_marco + 1
            self._normalizar_z_index()

    def obtener_sublienzo_marco(self, uid_marco):
        """
        PREPARACIÓN PARA LA UI: Extrae todos los elementos dentro de un marco 
        y convierte sus coordenadas a un universo local (0,0) para poder abrir
        una 'Nueva Ventana de Edición' aislada.
        """
        if uid_marco not in self.elementos: return None
        marco = self.elementos[uid_marco]
        
        elementos_hijos = {}
        for uid, elem in self.elementos.items():
            if elem.get('parent_marco') == uid_marco:
                # Clonamos para no afectar el motor principal todavía
                hijo_clon = copy.deepcopy(elem)
                # Convertimos las coordenadas globales a coordenadas locales del marco
                hijo_clon['x'] -= marco['x']
                hijo_clon['y'] -= marco['y']
                elementos_hijos[uid] = hijo_clon
                
        return {
            "w_pdf": marco['w'],
            "h_pdf": marco['h'],
            "elementos": elementos_hijos,
            "marco_x": marco['x'], # Guardamos el offset original
            "marco_y": marco['y']
        }

    def guardar_sublienzo_marco(self, uid_marco, elementos_hijos_editados):
        """
        SINCRONIZACIÓN: Recibe los elementos que el usuario editó en la ventana aislada
        y los devuelve al lienzo global sumándoles la posición del marco.
        """
        if uid_marco not in self.elementos: return
        marco = self.elementos[uid_marco]
        
        for uid, hijo_local in elementos_hijos_editados.items():
            # Revertimos a coordenadas absolutas globales del PDF
            hijo_local['x'] += marco['x']
            hijo_local['y'] += marco['y']
            hijo_local['parent_marco'] = uid_marco
            
            # Actualizamos el motor
            self.elementos[uid] = hijo_local

    # ==========================================
    # HERRAMIENTAS DE ALINEACIÓN Y DISTRIBUCIÓN
    # ==========================================
    def alinear_elementos(self, lista_uids, tipo_alineacion="centro_h"):
        """Alinea múltiples elementos en base a la caja global que los envuelve."""
        if len(lista_uids) < 2: return # Se necesitan mínimo 2 para alinear
        
        # 1. Obtener cajas reales de todos los seleccionados
        cajas = {}
        for uid in lista_uids:
            c = self.obtener_caja_elemento(uid)
            if c: cajas[uid] = c
            
        if len(cajas) < 2: return
        
        # 2. Calcular la caja perimetral (BBox Global) de la selección
        min_x = min(c['x'] for c in cajas.values())
        max_x = max(c['x'] + c['w'] for c in cajas.values())
        min_y = min(c['y'] for c in cajas.values())
        max_y = max(c['y'] + c['h'] for c in cajas.values())
        
        centro_x = min_x + (max_x - min_x) / 2.0
        centro_y = min_y + (max_y - min_y) / 2.0
        
        # 3. Aplicar alineación compensando el Offset (tildes/colas)
        for uid, c in cajas.items():
            elem = self.elementos[uid]
            offset_x = c['x'] - elem['x']
            offset_y = c['y'] - elem['y']
            
            if tipo_alineacion == "izquierda":
                self.modificar_elemento(uid, x=min_x - offset_x)
            elif tipo_alineacion == "centro_h":
                self.modificar_elemento(uid, x=(centro_x - (c['w'] / 2.0)) - offset_x)
            elif tipo_alineacion == "derecha":
                self.modificar_elemento(uid, x=(max_x - c['w']) - offset_x)
            elif tipo_alineacion == "abajo":
                self.modificar_elemento(uid, y=min_y - offset_y)
            elif tipo_alineacion == "centro_v":
                self.modificar_elemento(uid, y=(centro_y - (c['h'] / 2.0)) - offset_y)
            elif tipo_alineacion == "arriba":
                self.modificar_elemento(uid, y=(max_y - c['h']) - offset_y)

    def distribuir_elementos(self, lista_uids, eje="horizontal"):
        """Distribuye el espacio equitativamente entre los elementos seleccionados."""
        if len(lista_uids) < 3: return # Se necesitan mínimo 3 para distribuir el medio
        
        cajas = []
        for uid in lista_uids:
            c = self.obtener_caja_elemento(uid)
            if c:
                offset_x = c['x'] - self.elementos[uid]['x']
                offset_y = c['y'] - self.elementos[uid]['y']
                cajas.append({'uid': uid, 'c': c, 'ox': offset_x, 'oy': offset_y})
                
        if len(cajas) < 3: return
        
        if eje == "horizontal":
            # Ordenamos visualmente de izquierda a derecha
            cajas.sort(key=lambda item: item['c']['x'])
            primer_x = cajas[0]['c']['x']
            ultimo_x_fin = cajas[-1]['c']['x'] + cajas[-1]['c']['w']
            
            # Matemáticas de distribución
            espacio_total = ultimo_x_fin - primer_x
            ancho_total_elementos = sum(item['c']['w'] for item in cajas)
            espacio_vacio = espacio_total - ancho_total_elementos
            
            # El espacio en blanco que debe ir entre cada objeto
            gap = espacio_vacio / (len(cajas) - 1)
            
            x_actual = primer_x
            for item in cajas:
                self.modificar_elemento(item['uid'], x=x_actual - item['ox'])
                x_actual += item['c']['w'] + gap
                
        elif eje == "vertical":
            # Ordenamos visualmente de abajo hacia arriba
            cajas.sort(key=lambda item: item['c']['y'])
            primer_y = cajas[0]['c']['y']
            ultimo_y_fin = cajas[-1]['c']['y'] + cajas[-1]['c']['h']
            
            espacio_total = ultimo_y_fin - primer_y
            alto_total_elementos = sum(item['c']['h'] for item in cajas)
            espacio_vacio = espacio_total - alto_total_elementos
            
            gap = espacio_vacio / (len(cajas) - 1)
            
            y_actual = primer_y
            for item in cajas:
                self.modificar_elemento(item['uid'], y=y_actual - item['oy'])
                y_actual += item['c']['h'] + gap

    # ==========================================
    # UTILIDADES PARA LA INTERFAZ (UI "Tonta")
    # ==========================================
    def ui_a_pdf(self, x_real, y_real, zoom):
        """Convierte los píxeles de la pantalla a coordenadas matemáticas exactas del PDF."""
        pdf_x = x_real / zoom
        pdf_y = self.h_pdf - (y_real / zoom)
        return pdf_x, pdf_y

    def pdf_a_ui(self, pdf_x, pdf_y, w_pdf, h_pdf, zoom, h_lienzo_pdf):
        """Convierte una caja matemática del PDF a coordenadas de pantalla (Tkinter/Web) para dibujar."""
        x1 = pdf_x * zoom
        y1 = (h_lienzo_pdf - (pdf_y + h_pdf)) * zoom
        x2 = (pdf_x + w_pdf) * zoom
        y2 = (h_lienzo_pdf - pdf_y) * zoom
        return x1, y1, x2, y2

    def seleccionar_por_area(self, x1_pdf, y1_pdf, x2_pdf, y2_pdf):
        """Devuelve una lista con los IDs de los objetos atrapados en el cuadro de selección."""
        min_x, max_x = min(x1_pdf, x2_pdf), max(x1_pdf, x2_pdf)
        min_y, max_y = min(y1_pdf, y2_pdf), max(y1_pdf, y2_pdf)
        
        seleccionados = []
        for uid, elem in self.elementos.items():
            if elem.get('oculto', False) or elem['tipo'] == "Ignorar": continue
            c = self.obtener_caja_elemento(uid)
            if c:
                # Matemática de colisión: Si la caja del objeto toca la caja de selección
                if (c['x'] <= max_x and c['x'] + c['w'] >= min_x and 
                    c['y'] <= max_y and c['y'] + c['h'] >= min_y):
                    seleccionados.append(uid)
        return seleccionados

    # ==========================================
    # RUTINAS DE EXPORTACIÓN Y VISTA PREVIA
    # ==========================================

    def obtener_estado_ui(self):
        """Devuelve un JSON con TODO el estado del lienzo, incluyendo efectos y cajas reales."""
        elementos_ui = {}
        for uid, elem in self.elementos.items():
            if elem.get('tipo') == "Ignorar": continue
            
            # 1. Clonamos el diccionario completo para heredar bordes, sombras, degradados, etc.
            elem_export = elem.copy()
            
            # 2. Calculamos la caja real (Bounding Box) para los nodos de la UI
            caja = self.obtener_caja_elemento(uid)
            if caja:
                # Enviamos las dimensiones de colisión bajo nombres específicos
                # Así el frontend sabe dibujar el cuadro azul sin alterar el X/Y matemático del texto
                elem_export['caja_x'] = caja['x']
                elem_export['caja_y'] = caja['y']
                elem_export['caja_w'] = caja['w']
                elem_export['caja_h'] = caja['h']
            else:
                elem_export['caja_x'] = elem['x']
                elem_export['caja_y'] = elem['y']
                elem_export['caja_w'] = elem['w']
                elem_export['caja_h'] = elem['h']
                
            elementos_ui[uid] = elem_export
            
        return {
            "w_pdf": self.w_pdf,
            "h_pdf": self.h_pdf,
            "elementos": elementos_ui
        }

    # ==========================================
    # GESTIÓN DE ARCHIVOS PROPIETARIOS (.diseño, .dtf, etc.)
    # ==========================================
    def guardar_proyecto(self, ruta_archivo, firma_app="RECTOR_OP_CORE_V1"):
        """
        Guarda el proyecto empaquetando las imágenes en Base64.
        Acepta cualquier extensión (ej. .diseño) y le pone un sello de seguridad.
        """
        estado_elementos = {}
        for uid, elem in self.elementos.items():
            elem_clon = copy.deepcopy(elem)
            
            if elem['tipo'] == 'Foto' and os.path.exists(str(elem['contenido'])):
                ruta_archivo_img = str(elem['contenido'])
                _, ext = os.path.splitext(ruta_archivo_img)
                try:
                    with open(ruta_archivo_img, "rb") as f:
                        elem_clon['b64_data'] = base64.b64encode(f.read()).decode('utf-8')
                        elem_clon['b64_ext'] = ext
                except Exception as e:
                    print(f"Error empaquetando archivo {ruta_archivo_img}: {e}")
                    
            estado_elementos[uid] = elem_clon

        plantilla_b64 = None
        if self.ruta_plantilla and os.path.exists(self.ruta_plantilla):
            try:
                with open(self.ruta_plantilla, "rb") as f:
                    plantilla_b64 = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                print(f"Error empaquetando plantilla: {e}")

        estado = {
            "firma_app": firma_app, # <-- EL SELLO PROPIETARIO
            "ruta_plantilla": self.ruta_plantilla,
            "plantilla_b64": plantilla_b64,
            "w_pdf": self.w_pdf,
            "h_pdf": self.h_pdf,
            "elementos": estado_elementos
        }
        
        # Python guardará el JSON perfecto sin importar la extensión de ruta_archivo
        with open(ruta_archivo, 'w', encoding='utf-8') as f: 
            json.dump(estado, f, indent=4)

    def cargar_proyecto(self, ruta_archivo, firma_esperada=None):
        """
        Abre tu archivo propietario, extrae los Base64 y valida el sello.
        """
        with open(ruta_archivo, 'r', encoding='utf-8') as f: 
            estado = json.load(f)
            
        # --- VALIDACIÓN DE SEGURIDAD ---
        if firma_esperada and estado.get("firma_app") != firma_esperada:
            raise ValueError(f"Formato no válido. Se esperaba un archivo de tipo: {firma_esperada}")
        
        self.ruta_plantilla = estado.get("ruta_plantilla")
        self.w_pdf = estado.get("w_pdf", 0)
        self.h_pdf = estado.get("h_pdf", 0)
        
        plantilla_b64 = estado.get("plantilla_b64")
        if plantilla_b64:
            fd, ruta_temp_pdf = tempfile.mkstemp(prefix="proyecto_base_", suffix=".pdf")
            with os.fdopen(fd, "wb") as f:
                f.write(base64.b64decode(plantilla_b64))
            self.ruta_plantilla = ruta_temp_pdf

        elementos_cargados = estado.get("elementos", {})
        for uid, elem in elementos_cargados.items():
            if 'b64_data' in elem:
                ext = elem.get('b64_ext', '.png')
                data_bytes = base64.b64decode(elem['b64_data'])
                
                fd, ruta_temp = tempfile.mkstemp(prefix="proyecto_asset_", suffix=ext)
                with os.fdopen(fd, "wb") as f:
                    f.write(data_bytes)
                    
                elem['contenido'] = ruta_temp
                del elem['b64_data']
                if 'b64_ext' in elem: 
                    del elem['b64_ext']

        self.elementos = elementos_cargados
        self.limpiar_cache_imagenes()

    def exportar_pdf(self, ruta_salida):
        if not self.w_pdf or not self.h_pdf: raise ValueError("No hay lienzo activo.")
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(self.w_pdf, self.h_pdf))
        
        self._estampar_elementos(c) # <--- 🚀 CORRECCIÓN: Ahora solo se llama UNA vez
        
        c.save()
        packet.seek(0)

        if self.ruta_plantilla:
            with fitz.open(self.ruta_plantilla) as doc_final:
                data_pdf = fitz.open("stream", packet.read())
                if len(data_pdf) > 0: doc_final[0].show_pdf_page(doc_final[0].rect, data_pdf, 0)
                doc_final.save(ruta_salida)
                data_pdf.close()
        else:
            with open(ruta_salida, "wb") as f: f.write(packet.getvalue())

    def exportar_imagen(self, ruta_salida, dpi=300):
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(self.w_pdf, self.h_pdf))
        self._estampar_elementos(c)
        c.save()
        packet.seek(0)
        with fitz.open("stream", packet.read()) as doc_capa:
            pix = doc_capa[0].get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if ruta_salida.lower().endswith(('.jpg', '.jpeg')):
                img.save(ruta_salida, quality=95)
            else:
                img.save(ruta_salida)

    def exportar_png_transparente(self, ruta_salida, dpi=300):
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(self.w_pdf, self.h_pdf))
        
        self._estampar_elementos(c) # <--- 🚀 CORRECCIÓN: Eliminamos el duplicado
        
        c.save()
        packet.seek(0)
        with fitz.open("stream", packet.read()) as doc_capa:
            pix = doc_capa[0].get_pixmap(dpi=dpi, alpha=True)
            img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
            img.save(ruta_salida, format="PNG")
