import xml.etree.ElementTree as ET
import re
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainterPath, QColor, QBrush, QPen, QTransform

class VectifySVGParser:
    """
    🚀 LECTOR VECTORIAL NATIVO: Convierte etiquetas SVG en matemáticas puras de Qt.
    Soporta: paths, rectángulos, círculos, elipses, líneas, polígonos y transformaciones.
    """
    def __init__(self, ruta_svg):
        self.ruta_svg = ruta_svg
        self.geometrias = []

    def parsear(self):
        try:
            tree = ET.parse(self.ruta_svg)
            root = tree.getroot()
            
            # Limpiamos los namespaces (ej. {http://www.w3.org/2000/svg}rect -> rect)
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
                    
            # Iniciamos la recursión: color de relleno negro, sin bordes por defecto
            self._procesar_nodo(root, QTransform(), "#000000", "none", 0.0)
            
        except Exception as e:
            print(f"⚠️ Error en Compilador SVG: {e}")
            
        return self.geometrias

    def _procesar_nodo(self, nodo, transform_padre, color_padre, stroke_padre, sw_padre):
        t_local = self._parsear_transform(nodo.get('transform', ''))
        t_total = t_local * transform_padre
        style = nodo.get('style', '')
        
        fill = nodo.get('fill')
        if not fill:
            m = re.search(r'fill:\s*([^;]+)', style)
            if m: fill = m.group(1).strip()
        if not fill or fill == 'inherit': fill = color_padre

        def parse_color(c_str):
            if not c_str or c_str.lower() in ['none', 'transparent']: return Qt.GlobalColor.transparent
            try: return QColor(c_str)
            except: return Qt.GlobalColor.black

        c_fill = parse_color(fill)
        path = QPainterPath()
        path.setFillRule(Qt.FillRule.WindingFill) 
        
        tag = nodo.tag
        tipo_forma = 'Rectángulo' # Por defecto

        if tag == 'path':
            path = self._parsear_path_d(nodo.get('d', ''))
            tipo_forma = 'Ruta'
        elif tag == 'rect':
            x, y, w, h = float(nodo.get('x', 0)), float(nodo.get('y', 0)), float(nodo.get('width', 0)), float(nodo.get('height', 0))
            path.addRect(x, y, w, h)
            tipo_forma = 'Rectángulo'
        elif tag in ['circle', 'ellipse']:
            cx, cy = float(nodo.get('cx', 0)), float(nodo.get('cy', 0))
            rx = float(nodo.get('r', nodo.get('rx', 0)))
            ry = float(nodo.get('r', nodo.get('ry', 0)))
            path.addEllipse(cx - rx, cy - ry, rx * 2, ry * 2)
            tipo_forma = 'Elipse'

        if not path.isEmpty() and c_fill != Qt.GlobalColor.transparent:
            path = t_total.map(path)
            self.geometrias.append({
                'path': path,
                'brush': QBrush(c_fill),
                'pen': QPen(Qt.PenStyle.NoPen),
                'tag': tag,           # 🚀 GUARDAMOS EL ADN
                'forma': tipo_forma   # 🚀 GUARDAMOS EL ADN
            })

        for hijo in nodo:
            self._procesar_nodo(hijo, t_total, fill, stroke_padre, sw_padre)

    def _parsear_transform(self, t_str):
        """🚀 AHORA SOPORTA SCALE: Cura para los micropuntos del QR"""
        t = QTransform()
        if not t_str: return t
        
        cmds = re.findall(r'(translate|scale|matrix|rotate)\s*\(([^)]+)\)', t_str)
        for cmd, args_str in cmds:
            args = [float(x) for x in re.findall(r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', args_str)]
            if cmd == 'translate' and len(args) >= 1:
                tx = args[0]
                ty = args[1] if len(args) > 1 else 0.0
                t.translate(tx, ty)
            elif cmd == 'scale' and len(args) >= 1:
                sx = args[0]
                sy = args[1] if len(args) > 1 else sx
                t.scale(sx, sy) # 🚀 Aplicamos escala pura
            elif cmd == 'rotate' and len(args) >= 1:
                t.rotate(args[0])
            elif cmd == 'matrix' and len(args) == 6:
                a, b, c, d, e, f = args
                t = QTransform(a, b, c, d, e, f) * t
                
        return t

    def _parsear_path_d(self, d):
        """Compilador de Bézier"""
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
                    cx1, cy1 = cmds[i], cmds[i+1]; cx2, cy2 = cmds[i+2], cmds[i+3]; x, y = cmds[i+4], cmds[i+5]
                    path.cubicTo(cx1, cy1, cx2, cy2, x, y); i += 6
                elif cmd == 'c':
                    cx1, cy1 = x + cmds[i], y + cmds[i+1]; cx2, cy2 = x + cmds[i+2], y + cmds[i+3]; nx, ny = x + cmds[i+4], y + cmds[i+5]
                    path.cubicTo(cx1, cy1, cx2, cy2, nx, ny); x, y = nx, ny; i += 6
                elif cmd in ['Z', 'z']:
                    path.closeSubpath()
                else:
                    while i < len(cmds) and not isinstance(cmds[i], str): i += 1
            except IndexError: break
            
        return path