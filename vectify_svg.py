import xml.etree.ElementTree as ET
import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainterPath, QColor, QBrush, QPen, QTransform, QLinearGradient, QRadialGradient

class VectifySVGParser:
    """
    🚀 LECTOR VECTORIAL NATIVO V2: Soporte para Adobe Illustrator, CSS y Degradados.
    """
    def __init__(self, ruta_svg):
        self.ruta_svg = ruta_svg
        self.geometrias = []
        self.css_styles = {}
        self.gradientes = {}

    def parsear(self):
        try:
            tree = ET.parse(self.ruta_svg)
            root = tree.getroot()
            
            # 1. Limpiamos los namespaces (Vital para buscar etiquetas sin que estorbe la URL de W3C)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]

            # 2. Extraemos las Hojas de Estilo CSS (El secreto de Illustrator)
            self._parsear_css(root)
            
            # 3. Extraemos los Degradados (Gradients)
            self._parsear_gradientes(root)
                    
            # 4. Arrancamos el motor de lectura visual
            self._procesar_nodo(root, QTransform(), "#000000", "none", 0.0)
            
        except Exception as e:
            print(f"⚠️ Error en Compilador SVG: {e}")
            
        return self.geometrias

    def _parsear_css(self, root):
        """Busca etiquetas <style> y guarda sus clases en un diccionario para usarlas luego"""
        for style_tag in root.iter('style'):
            if style_tag.text:
                # Quitamos comentarios de CSS
                css_text = re.sub(r'/\*.*?\*/', '', style_tag.text, flags=re.DOTALL)
                # Buscamos patrones: .clase { atributo: valor; }
                reglas = re.findall(r'([^{]+)\{([^}]+)\}', css_text)
                for selector, properties in reglas:
                    prop_dict = {}
                    for prop in properties.split(';'):
                        if ':' in prop:
                            key, val = prop.split(':', 1)
                            prop_dict[key.strip()] = val.strip()
                    
                    # Si varias clases comparten el mismo estilo (.cls-1, .cls-2)
                    for sel in selector.split(','):
                        sel = sel.strip()
                        if sel.startswith('.'):
                            self.css_styles[sel[1:]] = prop_dict

    def _parsear_gradientes(self, root):
        """Escanea degradados y los convierte en QBrush con coordenadas relativas"""
        for grad in root.iter():
            if grad.tag in ['linearGradient', 'radialGradient']:
                gid = grad.get('id')
                if not gid: continue
                
                stops = []
                for stop in grad.iter('stop'):
                    offset = stop.get('offset', '0')
                    if offset.endswith('%'): offset = float(offset[:-1])/100.0
                    else: offset = float(offset)
                    
                    # El color puede estar en atributo o en style
                    sc = stop.get('stop-color')
                    if not sc:
                        st = stop.get('style', '')
                        m = re.search(r'stop-color:\s*([^;]+)', st)
                        if m: sc = m.group(1).strip()
                    if not sc: sc = '#000000'
                    
                    sa = stop.get('stop-opacity', '1')
                    qcolor = QColor(sc)
                    qcolor.setAlphaF(float(sa))
                    stops.append((offset, qcolor))
                    
                # Usamos ObjectBoundingMode para que el degradado se adapte al tamaño de cualquier pieza
                if grad.tag == 'linearGradient':
                    qgrad = QLinearGradient(0, 0, 1, 0)
                else:
                    qgrad = QRadialGradient(0.5, 0.5, 0.5)
                    
                qgrad.setCoordinateMode(QLinearGradient.CoordinateMode.ObjectBoundingMode)
                for offset, color in stops:
                    qgrad.setColorAt(offset, color)
                    
                self.gradientes[gid] = QBrush(qgrad)

    def _procesar_nodo(self, nodo, transform_padre, color_padre, stroke_padre, sw_padre):
        t_local = self._parsear_transform(nodo.get('transform', ''))
        t_total = t_local * transform_padre
        
        # ========================================================
        # 🚀 LECTOR DE ATRIBUTOS MULTI-NIVEL (La Cura del Todo Negro)
        # ========================================================
        clases = nodo.get('class', '').split()
        style_inline = nodo.get('style', '')

        def get_attr(name):
            # Prioridad 1: Atributo directo (fill="red")
            val = nodo.get(name)
            if val: return val
            # Prioridad 2: Style Inline (style="fill: red;")
            m = re.search(fr'{name}:\s*([^;]+)', style_inline)
            if m: return m.group(1).strip()
            # Prioridad 3: CSS Class (class="st1")
            for c in clases:
                if c in self.css_styles and name in self.css_styles[c]:
                    return self.css_styles[c][name]
            return None

        # 1. Obtener Relleno, Borde y Grosor
        fill = get_attr('fill')
        if not fill or fill == 'inherit': fill = color_padre

        stroke = get_attr('stroke')
        if not stroke or stroke == 'inherit': stroke = stroke_padre

        sw = get_attr('stroke-width')
        try: sw = float(sw.replace('px','')) if sw else sw_padre
        except: sw = sw_padre

        # 2. Fabricar Pinceles (Detecta Degradados automáticamente)
        def create_brush(c_str):
            if not c_str or c_str.lower() in ['none', 'transparent']: 
                return QBrush(Qt.BrushStyle.NoBrush)
            if 'url(' in c_str:
                m = re.search(r'url\(\s*#([^)]+)\s*\)', c_str)
                if m and m.group(1) in self.gradientes:
                    return self.gradientes[m.group(1)]
            try: return QBrush(QColor(c_str))
            except: return QBrush(Qt.GlobalColor.black)
            
        def create_pen(c_str, width):
            if not c_str or c_str.lower() in ['none', 'transparent'] or width <= 0:
                return QPen(Qt.PenStyle.NoPen)
            try: 
                pen = QPen(QColor(c_str), width)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                return pen
            except: return QPen(Qt.GlobalColor.black, width)

        brush = create_brush(fill)
        pen = create_pen(stroke, sw)

        # 3. CONSTRUCCIÓN MATEMÁTICA
        path = QPainterPath()
        
        # 🚀 LA CURA DE LOS AGUJEROS: Leemos la regla de relleno del SVG
        fill_rule = get_attr('fill-rule')
        if fill_rule == 'evenodd': path.setFillRule(Qt.FillRule.OddEvenFill)
        else: path.setFillRule(Qt.FillRule.WindingFill)
        
        tag = nodo.tag
        tipo_forma = 'Rectángulo'

        if tag == 'path':
            path = self._parsear_path_d(nodo.get('d', ''))
            tipo_forma = 'Ruta'
        elif tag == 'rect':
            x, y, w, h = float(nodo.get('x', 0)), float(nodo.get('y', 0)), float(nodo.get('width', 0)), float(nodo.get('height', 0))
            rx = float(nodo.get('rx', 0))
            if rx > 0: path.addRoundedRect(x, y, w, h, rx, rx)
            else: path.addRect(x, y, w, h)
            tipo_forma = 'Rectángulo'
        elif tag in ['circle', 'ellipse']:
            cx, cy = float(nodo.get('cx', 0)), float(nodo.get('cy', 0))
            rx = float(nodo.get('r', nodo.get('rx', 0)))
            ry = float(nodo.get('r', nodo.get('ry', 0)))
            path.addEllipse(cx - rx, cy - ry, rx * 2, ry * 2)
            tipo_forma = 'Elipse'
        elif tag in ['polygon', 'polyline']:
            puntos_str = nodo.get('points', '').replace(',', ' ').split()
            if len(puntos_str) >= 2:
                path.moveTo(float(puntos_str[0]), float(puntos_str[1]))
                for i in range(2, len(puntos_str), 2):
                    if i + 1 < len(puntos_str):
                        path.lineTo(float(puntos_str[i]), float(puntos_str[i+1]))
                if tag == 'polygon': path.closeSubpath()
            tipo_forma = 'Ruta'
        elif tag == 'line':
            x1, y1 = float(nodo.get('x1', 0)), float(nodo.get('y1', 0))
            x2, y2 = float(nodo.get('x2', 0)), float(nodo.get('y2', 0))
            path.moveTo(x1, y1); path.lineTo(x2, y2)
            tipo_forma = 'Línea'

        # Si el objeto es visible (tiene relleno o tiene borde)
        if not path.isEmpty() and (brush.style() != Qt.BrushStyle.NoBrush or pen.style() != Qt.PenStyle.NoPen):
            path = t_total.map(path)
            self.geometrias.append({
                'path': path,
                'brush': brush,
                'pen': pen,
                'tag': tag,
                'forma': tipo_forma
            })

        # Bajar de nivel en el árbol
        for hijo in nodo:
            self._procesar_nodo(hijo, t_total, fill, stroke, sw)

    def _parsear_transform(self, t_str):
        t = QTransform()
        if not t_str: return t
        
        cmds = re.findall(r'(translate|scale|matrix|rotate)\s*\(([^)]+)\)', t_str)
        for cmd, args_str in cmds:
            args = [float(x) for x in re.findall(r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', args_str)]
            if cmd == 'translate' and len(args) >= 1:
                t.translate(args[0], args[1] if len(args) > 1 else 0.0)
            elif cmd == 'scale' and len(args) >= 1:
                t.scale(args[0], args[1] if len(args) > 1 else args[0])
            elif cmd == 'rotate' and len(args) >= 1:
                t.rotate(args[0])
            elif cmd == 'matrix' and len(args) == 6:
                t = QTransform(*args) * t
                
        return t

    def _parsear_path_d(self, d):
        path = QPainterPath()
        if not d: return path
        d = d.replace(',', ' ')
        tokens = re.findall(r'([a-zA-Z])|([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)', d)
        
        cmds = []
        for tok in tokens:
            if tok[0]: cmds.append(tok[0])
            elif tok[1]: cmds.append(float(tok[1]))
            
        if not cmds: return path
        
        i, x, y = 0, 0.0, 0.0
        cmd = ''
        
        while i < len(cmds):
            if isinstance(cmds[i], str):
                cmd = cmds[i]
                i += 1
            if i >= len(cmds): break
            
            try:
                if cmd == 'M':
                    x, y = cmds[i], cmds[i+1]; path.moveTo(x, y); i += 2; cmd = 'L'
                elif cmd == 'm':
                    x += cmds[i]; y += cmds[i+1]; path.moveTo(x, y); i += 2; cmd = 'l'
                elif cmd == 'L':
                    x, y = cmds[i], cmds[i+1]; path.lineTo(x, y); i += 2
                elif cmd == 'l':
                    x += cmds[i]; y += cmds[i+1]; path.lineTo(x, y); i += 2
                elif cmd == 'H':
                    x = cmds[i]; path.lineTo(x, y); i += 1
                elif cmd == 'h':
                    x += cmds[i]; path.lineTo(x, y); i += 1
                elif cmd == 'V':
                    y = cmds[i]; path.lineTo(x, y); i += 1
                elif cmd == 'v':
                    y += cmds[i]; path.lineTo(x, y); i += 1
                elif cmd == 'C':
                    path.cubicTo(cmds[i], cmds[i+1], cmds[i+2], cmds[i+3], cmds[i+4], cmds[i+5])
                    x, y = cmds[i+4], cmds[i+5]; i += 6
                elif cmd == 'c':
                    path.cubicTo(x+cmds[i], y+cmds[i+1], x+cmds[i+2], y+cmds[i+3], x+cmds[i+4], y+cmds[i+5])
                    x, y = x+cmds[i+4], y+cmds[i+5]; i += 6
                elif cmd in ['Z', 'z']:
                    path.closeSubpath()
                else:
                    while i < len(cmds) and not isinstance(cmds[i], str): i += 1
            except IndexError: break
            
        return path