# xml2altimetria.py
# -*- coding: utf-8 -*-
"""
Genera el archivo altimetria.svg (perfil altimétrico de la etapa) a partir de etapaEsquema.xml

- Lee el árbol DOM con xml.etree.ElementTree
- Obtiene los datos mediante expresiones XPath
- Dibuja la altimetría a semejanza del libro de ruta de la Vuelta:
    * perfil como polilínea cerrada rellena de rojo
    * escala horizontal en km y escala vertical en metros
    * nombres de la salida y de la meta
    * nombres en vertical de los hitos con sus iconos (S, M, puertos, SP, B)
    * nombres en vertical de los puntos anónimos que tienen nombre
    * desnivel positivo de la etapa al pie

@author: Daniel Rodríguez Fernández. Universidad de Oviedo
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass


def formatoKm(valor):
    """
    Punto kilométrico al estilo del libro de ruta: coma decimal y sin ',0' (155,4 · 136)
    """
    texto = '{:.1f}'.format(valor).replace('.', ',')
    return texto[:-2] if texto.endswith(',0') else texto


def formatoMetros(valor):
    """
    Altitud o desnivel con punto de millares (1.348)
    """
    return '{:,.0f}'.format(valor).replace(',', '.')


@dataclass(frozen=True)
class PuntoPerfil(object):
    """
    Punto del perfil altimétrico de la etapa (salida, meta o hito)
    """
    nombre: str
    tipo: str
    altitud: float
    distanciaSalida: float
    tieneNombre: bool = True
    bonificado: bool = False


class LectorEtapa(object):
    """
    Lee el archivo XML de la etapa y extrae sus puntos usando expresiones XPath
    """
    ESPACIO_NOMBRES = {'uo': 'http://www.uniovi.es'}

    def __init__(self, nombreArchivoXML):
        """
        Construye el árbol DOM en memoria a partir del archivo XML
        """
        try:
            self.raiz = ET.parse(nombreArchivoXML).getroot()
        except IOError:
            raise SystemExit('No se encuentra el archivo ' + nombreArchivoXML)
        except ET.ParseError:
            raise SystemExit('Error procesando el archivo XML = ' + nombreArchivoXML)

    def numeroEtapa(self):
        """
        Número de la etapa (atributo del elemento raíz)
        """
        return self.raiz.get('numero')

    def nombreEtapa(self):
        """
        Nombre de la etapa
        """
        return self.__texto(self.raiz, 'uo:nombre')

    def longitudEtapa(self):
        """
        Longitud total de la etapa en km
        """
        return float(self.__texto(self.raiz, 'uo:longitud'))

    def desnivelEtapa(self):
        """
        Desnivel positivo acumulado de la etapa en metros
        """
        return float(self.__texto(self.raiz, 'uo:desnivel'))

    def salida(self):
        """
        Punto de salida de la etapa
        """
        altitud = float(self.__texto(self.raiz, 'uo:salida/uo:coordenadas/uo:altitud'))
        return PuntoPerfil(self.__texto(self.raiz, 'uo:lugar_salida'), 'salida', altitud, 0.0)

    def meta(self):
        """
        Punto de llegada de la etapa
        """
        altitud = float(self.__texto(self.raiz, 'uo:meta/uo:coordenadas/uo:altitud'))
        return PuntoPerfil(self.__texto(self.raiz, 'uo:lugar_meta'), 'meta',
                           altitud, self.longitudEtapa())

    def hitos(self):
        """
        Todos los hitos de la etapa (con y sin nombre): dan forma al perfil
        """
        return [self.__crearHito(hito)
                for hito in self.raiz.findall('uo:hitos/uo:hito', self.ESPACIO_NOMBRES)]

    def hitosConNombre(self):
        """
        Hitos que se rotulan: puertos, sprints y puntos anónimos que tienen nombre
        """
        return [self.__crearHito(hito)
                for hito in self.raiz.findall('uo:hitos/uo:hito[@nombre]', self.ESPACIO_NOMBRES)]

    def __crearHito(self, hito):
        """
        Convierte un elemento <hito> del árbol DOM en un PuntoPerfil
        """
        tipo = hito.get('tipo', 'punto_anonimo')
        return PuntoPerfil(nombre=hito.get('nombre', ''),
                           tipo=tipo,
                           altitud=float(self.__texto(hito, 'uo:coordenadas/uo:altitud')),
                           distanciaSalida=float(self.__texto(hito, 'uo:distancia_salida')),
                           tieneNombre=hito.get('nombre') is not None,
                           bonificado=hito.get('bonificado', 'false').strip().lower()
                           in ('true', '1'))

    def __texto(self, elemento, expresion):
        """
        Contenido textual del nodo seleccionado por la expresión XPath
        """
        texto = elemento.findtext(expresion, namespaces=self.ESPACIO_NOMBRES)
        if texto is None:
            raise SystemExit('Falta el elemento ' + expresion + ' en el archivo XML')
        return texto.strip()


class Svg(object):
    """
    Genera archivos SVG con rectángulos, líneas, polígonos, rutas y textos
    """
    FUENTE = "'Arial Narrow', 'Roboto Condensed', Arial, Helvetica, sans-serif"

    def __init__(self, ancho, alto):
        """
        Crea el elemento raíz con el espacio de nombres y el área de dibujo
        """
        self.raiz = ET.Element('svg', xmlns='http://www.w3.org/2000/svg', version='1.1',
                               width=str(ancho), height=str(alto),
                               viewBox='0 0 {} {}'.format(ancho, alto))

    def addTitulo(self, texto):
        """
        Añade el elemento <title> del documento
        """
        ET.SubElement(self.raiz, 'title').text = texto

    def addRect(self, x, y, ancho, alto, relleno, trazo='none'):
        """
        Añade un rectángulo
        """
        ET.SubElement(self.raiz, 'rect', x=self.num(x), y=self.num(y),
                      width=self.num(ancho), height=self.num(alto),
                      fill=relleno, stroke=trazo)

    def addLinea(self, x1, y1, x2, y2, color, ancho, opacidad=None):
        """
        Añade una línea recta
        """
        linea = ET.SubElement(self.raiz, 'line', x1=self.num(x1), y1=self.num(y1),
                              x2=self.num(x2), y2=self.num(y2), stroke=color)
        linea.set('stroke-width', str(ancho))
        if opacidad is not None:
            linea.set('stroke-opacity', str(opacidad))

    def addPoligono(self, puntos, relleno, trazo='none', ancho=0):
        """
        Añade un polígono cerrado a partir de una lista de pares (x, y)
        """
        poligono = ET.SubElement(self.raiz, 'polygon', points=self.__puntos(puntos),
                                 fill=relleno, stroke=trazo)
        poligono.set('stroke-width', str(ancho))
        poligono.set('stroke-linejoin', 'round')

    def addPolilinea(self, puntos, color, ancho):
        """
        Añade una línea quebrada abierta a partir de una lista de pares (x, y)
        """
        polilinea = ET.SubElement(self.raiz, 'polyline', points=self.__puntos(puntos),
                                  fill='none', stroke=color)
        polilinea.set('stroke-width', str(ancho))
        polilinea.set('stroke-linejoin', 'round')

    def addRuta(self, d, relleno, trazo='none', ancho=0):
        """
        Añade un elemento <path> (se usa para el escudo de los iconos)
        """
        ruta = ET.SubElement(self.raiz, 'path', d=d, fill=relleno, stroke=trazo)
        ruta.set('stroke-width', str(ancho))

    def addTexto(self, x, y, texto, tamano, color='#222222', anclaje='start',
                 negrita=False, rotacion=0):
        """
        Añade un texto, opcionalmente en negrita y girado sobre su punto de anclaje
        """
        elemento = ET.SubElement(self.raiz, 'text', x=self.num(x), y=self.num(y),
                                 fill=color)
        elemento.set('font-family', self.FUENTE)
        elemento.set('font-size', str(tamano))
        elemento.set('text-anchor', anclaje)
        if negrita:
            elemento.set('font-weight', 'bold')
        if rotacion:
            elemento.set('transform', 'rotate({} {} {})'.format(
                rotacion, self.num(x), self.num(y)))
        elemento.text = texto
        return elemento

    def addTramoTexto(self, elementoTexto, texto, negrita=False, x=None, dy=None):
        """
        Añade un <tspan> al texto; con x y dy empieza una línea nueva
        """
        tramo = ET.SubElement(elementoTexto, 'tspan')
        if x is not None:
            tramo.set('x', self.num(x))
        if dy is not None:
            tramo.set('dy', self.num(dy))
        tramo.set('font-weight', 'bold' if negrita else 'normal')
        tramo.text = texto

    def escribir(self, nombreArchivoSVG):
        """
        Escribe el archivo SVG con declaración, codificación e indentación
        """
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        # la indentación dentro de <text> se vería como espacios entre los <tspan>
        for texto in self.raiz.iter('text'):
            if len(texto):
                texto.text = None
                for tramo in texto:
                    tramo.tail = None
        arbol.write(nombreArchivoSVG, encoding='utf-8', xml_declaration=True)

    def __puntos(self, puntos):
        """
        Lista de pares (x, y) en el formato del atributo points
        """
        return ' '.join('{},{}'.format(self.num(x), self.num(y)) for x, y in puntos)

    @staticmethod
    def num(valor):
        """
        Número con dos decimales como máximo
        """
        return '{:.2f}'.format(valor).rstrip('0').rstrip('.')


class EstilosAltimetria(object):
    """
    Colores e iconos asociados a cada tipo de punto, como en el libro de ruta
    """
    # tipo: (letra del icono, color del escudo, color de la letra, adorno superior)
    ICONOS = {
        'salida':              ('S', '#5bc2e7', '#ffffff', 'banderin'),
        'meta':                ('M', '#e8432e', '#ffffff', 'cuadros'),
        'puerto_especial':     ('E', '#c27ab8', '#ffffff', 'montana'),
        'puerto_1a_categoria': ('1', '#c27ab8', '#ffffff', 'montana'),
        'puerto_2a_categoria': ('2', '#c27ab8', '#ffffff', 'montana'),
        'puerto_3a_categoria': ('3', '#c27ab8', '#ffffff', 'montana'),
        'sprint_intermedio':   ('SP', '#dde58a', '#222222', 'rayas'),
        'bonificacion':        ('B', '#a6bc6a', '#ffffff', 'almena'),
    }
    # orden de apilado cuando un mismo punto tiene varios iconos (de abajo arriba)
    ORDEN_ICONOS = ['salida', 'meta', 'sprint_intermedio', 'bonificacion',
                    'puerto_3a_categoria', 'puerto_2a_categoria',
                    'puerto_1a_categoria', 'puerto_especial']

    COLOR_FONDO = '#ffffff'
    RELLENO_PERFIL = '#e8432e'
    COLOR_PERFIL = '#c8331f'
    RELLENO_SUBIDA = '#b0331f'
    COLOR_REJILLA = '#000000'
    COLOR_EJES = '#222222'
    COLOR_TEXTO = '#1a1a1a'
    COLOR_GUIA = '#1a1a1a'

    def tieneIcono(self, tipo):
        """
        Indica si el tipo de punto se representa con un icono
        """
        return tipo in self.ICONOS

    def icono(self, tipo):
        """
        Datos del icono de un tipo de punto
        """
        return self.ICONOS[tipo]

    def ordenar(self, tipos):
        """
        Ordena los tipos de un punto para apilar sus iconos
        """
        return sorted(tipos, key=lambda t: self.ORDEN_ICONOS.index(t)
                      if t in self.ORDEN_ICONOS else len(self.ORDEN_ICONOS))


class EscalaPerfil(object):
    """
    Transforma distancias (km) y altitudes (m) en coordenadas del lienzo SVG
    """

    def __init__(self, x0, y0, ancho, alto, distanciaMaxima, altitudMaxima):
        """
        (x0, y0) es la esquina inferior izquierda del área del perfil
        """
        self.x0 = x0
        self.y0 = y0
        self.ancho = ancho
        self.alto = alto
        self.distanciaMaxima = distanciaMaxima
        self.altitudMaxima = altitudMaxima

    def x(self, distancia):
        """
        Coordenada horizontal de un punto kilométrico
        """
        return self.x0 + distancia * self.ancho / self.distanciaMaxima

    def y(self, altitud):
        """
        Coordenada vertical de una altitud
        """
        return self.y0 - altitud * self.alto / self.altitudMaxima

    def punto(self, puntoPerfil):
        """
        Par (x, y) de un punto del perfil
        """
        return self.x(puntoPerfil.distanciaSalida), self.y(puntoPerfil.altitud)


@dataclass
class Rotulo(object):
    """
    Hito rotulado: puede reunir varios tipos (p. ej. sprint y bonificación) en el mismo km
    """
    nombre: str
    altitud: float
    distanciaSalida: float
    tipos: list
    xRotulo: float = 0.0


class GeneradorAltimetria(object):
    """
    Construye la altimetría SVG de una etapa a partir de sus datos
    """
    ANCHO = 1450
    ALTO = 820
    MARGEN_IZQUIERDO = 175     # nombre vertical de la salida y escala de altitudes
    MARGEN_DERECHO = 95        # nombre vertical de la meta
    Y_PERFIL_SUPERIOR = 420    # altura de la altitud máxima de la escala
    Y_PERFIL_INFERIOR = 655    # eje de distancias (altitud 0)
    Y_BASE_ICONOS = 395        # parte inferior de la fila de iconos
    ALTO_ICONO = 46
    ANCHO_ICONO = 36
    SEPARACION_ICONOS = 10
    PASO_ALTITUD = 200
    TAMANO_ROTULO = 17
    INTERLINEA = 19
    SEPARACION_MINIMA = 24     # distancia mínima entre rótulos verticales
    LONGITUD_MAXIMA_LINEA = 26 # los nombres más largos se parten en dos líneas
    SEPARACION_KM = 36         # distancia mínima entre textos de la escala de km
    Y_PIE = 770

    def __init__(self, lector, estilos):
        """
        Recibe sus dependencias por inyección para poder sustituirlas
        """
        self.lector = lector
        self.estilos = estilos

    def generar(self, nombreArchivoSVG):
        """
        Genera y escribe el archivo SVG de la etapa
        """
        salida = self.lector.salida()
        meta = self.lector.meta()
        perfil = sorted([salida] + self.lector.hitos() + [meta],
                        key=lambda punto: punto.distanciaSalida)
        escala = self.__crearEscala(perfil, meta.distanciaSalida)
        rotulos = self.__agruparRotulos(self.lector.hitosConNombre())
        self.__colocarRotulos(escala, rotulos)

        svg = Svg(self.ANCHO, self.ALTO)
        svg.addTitulo('Etapa {}. {}'.format(self.lector.numeroEtapa(), self.lector.nombreEtapa()))
        svg.addRect(0, 0, self.ANCHO, self.ALTO, self.estilos.COLOR_FONDO)

        self.__addPerfil(svg, escala, perfil)
        self.__addSubidas(svg, escala, perfil)
        self.__addEscalaAltitudes(svg, escala)
        self.__addGuias(svg, escala, salida, meta, rotulos)
        self.__addEscalaDistancias(svg, escala, rotulos)
        self.__addSalidaMeta(svg, escala, salida, meta)
        self.__addRotulos(svg, rotulos)
        self.__addDesnivel(svg)

        svg.escribir(nombreArchivoSVG)

    # ------------------------------------------------------------------ cálculo

    def __crearEscala(self, perfil, distanciaMaxima):
        """
        La altitud máxima de la escala se redondea al siguiente múltiplo del paso
        """
        altitudMaxima = max(punto.altitud for punto in perfil)
        techo = max(self.PASO_ALTITUD,
                    math.ceil(altitudMaxima / self.PASO_ALTITUD) * self.PASO_ALTITUD)
        return EscalaPerfil(self.MARGEN_IZQUIERDO, self.Y_PERFIL_INFERIOR,
                            self.ANCHO - self.MARGEN_IZQUIERDO - self.MARGEN_DERECHO,
                            self.Y_PERFIL_INFERIOR - self.Y_PERFIL_SUPERIOR,
                            distanciaMaxima, techo)

    def __agruparRotulos(self, hitos):
        """
        Reúne en un solo rótulo los iconos de cada punto kilométrico: los hitos
        con atributo bonificado="true" llevan además el icono B (Tocón: SP + B)
        """
        rotulos = {}
        for hito in hitos:
            clave = round(hito.distanciaSalida, 1)
            if clave not in rotulos:
                rotulos[clave] = Rotulo(hito.nombre, hito.altitud, hito.distanciaSalida, [])
            tipos = [hito.tipo] + (['bonificacion'] if hito.bonificado else [])
            for tipo in tipos:
                if self.estilos.tieneIcono(tipo) and tipo not in rotulos[clave].tipos:
                    rotulos[clave].tipos.append(tipo)
        for rotulo in rotulos.values():
            rotulo.tipos = self.estilos.ordenar(rotulo.tipos)
        return [rotulos[clave] for clave in sorted(rotulos)]

    def __anchoRotulo(self, rotulo):
        """
        Espacio horizontal que ocupa un rótulo vertical (una o dos líneas)
        """
        return self.SEPARACION_MINIMA + self.INTERLINEA * (len(self.__lineas(rotulo)) - 1)

    def __colocarRotulos(self, escala, rotulos):
        """
        Desplaza a la derecha los rótulos que se solaparían (como Salobreña junto a la S)
        """
        mitadIcono = self.ANCHO_ICONO / 2
        bordeAnterior = escala.x0 + mitadIcono               # borde derecho del icono S
        for rotulo in rotulos:
            # espacio necesario a la izquierda de la guía: texto (1 o 2 líneas) o icono
            izquierda = self.__anchoRotulo(rotulo)
            if rotulo.tipos:
                izquierda = max(izquierda, mitadIcono + 6)
            rotulo.xRotulo = max(escala.x(rotulo.distanciaSalida), bordeAnterior + izquierda)
            bordeAnterior = rotulo.xRotulo + (mitadIcono if rotulo.tipos else 0)

    def __lineas(self, rotulo):
        """
        Parte el nombre en dos líneas si es muy largo (Alto de la Venta / de la Cebada)
        """
        nombre = rotulo.nombre
        if len(nombre) <= self.LONGITUD_MAXIMA_LINEA or ' ' not in nombre:
            return [nombre]
        mitad = len(nombre) // 2
        espacios = [i for i, c in enumerate(nombre) if c == ' ']
        corte = min(espacios, key=lambda i: abs(i - mitad))
        return [nombre[:corte], nombre[corte + 1:]]

    # ---------------------------------------------------------------- dibujo

    def __addPerfil(self, svg, escala, perfil):
        """
        Polilínea cerrada (polígono) rellena de rojo bajo el perfil
        """
        contorno = [escala.punto(punto) for punto in perfil]
        base = [(contorno[-1][0], escala.y0), (contorno[0][0], escala.y0)]
        svg.addPoligono(contorno + base, self.estilos.RELLENO_PERFIL,
                        self.estilos.COLOR_PERFIL, 1.5)

    def __addSubidas(self, svg, escala, perfil):
        """
        Sombrea en rojo oscuro la ascensión a cada puerto: desde el último punto
        más bajo antes de la cima hasta la cima, como en el libro de ruta
        """
        for i, punto in enumerate(perfil):
            if not punto.tipo.startswith('puerto'):
                continue
            inicio = i
            while inicio > 0 and perfil[inicio - 1].altitud < perfil[inicio].altitud:
                inicio -= 1
            if inicio == i:
                continue
            tramo = [escala.punto(p) for p in perfil[inicio:i + 1]]
            base = [(tramo[-1][0], escala.y0), (tramo[0][0], escala.y0)]
            svg.addPoligono(tramo + base, self.estilos.RELLENO_SUBIDA)

    def __addEscalaAltitudes(self, svg, escala):
        """
        Escala vertical en metros con líneas de referencia sobre el perfil
        """
        xFin = escala.x0 + escala.ancho
        for altitud in range(0, int(escala.altitudMaxima) + 1, self.PASO_ALTITUD):
            y = escala.y(altitud)
            svg.addLinea(escala.x0 - 6, y, xFin, y, self.estilos.COLOR_REJILLA, 0.8, 0.22)
            svg.addTexto(escala.x0 - 10, y + 4, str(altitud), 12,
                         self.estilos.COLOR_TEXTO, anclaje='end')
        svg.addLinea(escala.x0, escala.y0, escala.x0, escala.y(escala.altitudMaxima),
                     self.estilos.COLOR_EJES, 1.2)

    def __addGuias(self, svg, escala, salida, meta, rotulos):
        """
        Líneas que bajan desde cada rótulo hasta el eje; quiebran si el rótulo se desplazó
        """
        yInicio = self.Y_BASE_ICONOS + 6
        for punto in (salida, meta):
            x = escala.x(punto.distanciaSalida)
            svg.addLinea(x, yInicio, x, escala.y0, self.estilos.COLOR_GUIA, 1)
        for rotulo in rotulos:
            x = escala.x(rotulo.distanciaSalida)
            if abs(rotulo.xRotulo - x) < 0.5:
                svg.addLinea(x, yInicio, x, escala.y0, self.estilos.COLOR_GUIA, 1)
            else:
                yQuiebre = yInicio + 30
                svg.addPolilinea([(rotulo.xRotulo, yInicio), (rotulo.xRotulo, yQuiebre),
                                  (x, yQuiebre + 18), (x, escala.y0)],
                                 self.estilos.COLOR_GUIA, 1)

    def __addEscalaDistancias(self, svg, escala, rotulos):
        """
        Escala horizontal en km: salida, cada punto rotulado y meta
        """
        svg.addLinea(escala.x0, escala.y0, escala.x0 + escala.ancho, escala.y0,
                     self.estilos.COLOR_EJES, 1.5)
        kms = [0.0] + [rotulo.distanciaSalida for rotulo in rotulos] + [escala.distanciaMaxima]
        xs = [escala.x(km) for km in kms]
        yTexto = escala.y0 + 22
        for i, (km, x) in enumerate(zip(kms, xs)):
            # si dos marcas están muy juntas, sus textos se separan hacia fuera
            anclaje = 'middle'
            if i + 1 < len(xs) and xs[i + 1] - x < self.SEPARACION_KM:
                anclaje = 'end'
            elif i > 0 and x - xs[i - 1] < self.SEPARACION_KM:
                anclaje = 'start'
            xTexto = x + {'middle': 0, 'end': 2, 'start': -2}[anclaje]
            svg.addLinea(x, escala.y0, x, escala.y0 + 6, self.estilos.COLOR_EJES, 1.5)
            svg.addTexto(xTexto, yTexto, formatoKm(km), 14, self.estilos.COLOR_TEXTO,
                         anclaje=anclaje, negrita=True)
        svg.addTexto(escala.x(escala.distanciaMaxima) + 22, yTexto, 'km', 14,
                     self.estilos.COLOR_TEXTO, negrita=True)

    def __addSalidaMeta(self, svg, escala, salida, meta):
        """
        Iconos S y M y nombres verticales de salida (izquierda) y meta (derecha)
        """
        for punto, desplazamiento in ((salida, -58), (meta, 42)):
            x, y = escala.punto(punto)
            self.__addIcono(svg, x, self.Y_BASE_ICONOS, punto.tipo)
            texto = svg.addTexto(x + desplazamiento, escala.y0, '', 26,
                                 self.estilos.COLOR_TEXTO, rotacion=-90)
            svg.addTramoTexto(texto, punto.nombre.upper(), negrita=True)
            svg.addTramoTexto(texto, ' / {} m'.format(formatoMetros(punto.altitud)))
            texto.set('font-size', '26')

    def __addRotulos(self, svg, rotulos):
        """
        Iconos apilados y nombre vertical con la altitud de cada hito rotulado
        """
        for rotulo in rotulos:
            yBase = self.Y_BASE_ICONOS
            for tipo in rotulo.tipos:
                self.__addIcono(svg, rotulo.xRotulo, yBase, tipo)
                yBase -= self.ALTO_ICONO + self.SEPARACION_ICONOS
            yTexto = yBase - 4 if rotulo.tipos else yBase
            lineas = self.__lineas(rotulo)
            # la última línea queda pegada a la guía; las anteriores, a su izquierda
            xPrimera = rotulo.xRotulo - 4 - self.INTERLINEA * (len(lineas) - 1)
            texto = svg.addTexto(xPrimera, yTexto, '', self.TAMANO_ROTULO,
                                 self.estilos.COLOR_TEXTO, rotacion=-90)
            for i, linea in enumerate(lineas):
                if i == 0:
                    svg.addTramoTexto(texto, linea, negrita=True)
                else:
                    svg.addTramoTexto(texto, linea, negrita=True,
                                      x=xPrimera, dy=self.INTERLINEA)
            svg.addTramoTexto(texto, ' / {} m'.format(formatoMetros(rotulo.altitud)))

    def __addIcono(self, svg, cx, yBase, tipo):
        """
        Escudo con la letra de la categoría y su adorno superior (banderín, cuadros...)
        """
        letra, relleno, colorLetra, adorno = self.estilos.icono(tipo)
        a, h = self.ANCHO_ICONO, self.ALTO_ICONO
        izq, der, arriba = cx - a / 2, cx + a / 2, yBase - h
        radio = a / 2
        n = Svg.num
        svg.addRuta('M {} {} H {} V {} A {} {} 0 0 1 {} {} Z'.format(
            n(izq), n(arriba), n(der), n(yBase - radio), n(radio), n(radio),
            n(izq), n(yBase - radio)), relleno)
        self.__addAdorno(svg, adorno, izq, der, arriba, relleno)
        svg.addTexto(cx, yBase - h * 0.32, letra, 20 if len(letra) == 1 else 17,
                     colorLetra, anclaje='middle', negrita=True)

    def __addAdorno(self, svg, adorno, izq, der, arriba, color):
        """
        Pequeño distintivo sobre el escudo, a imitación de los iconos del libro de ruta
        """
        if adorno == 'banderin':
            svg.addPoligono([(izq, arriba - 2), (izq, arriba - 12), (der, arriba - 6),
                             (der, arriba - 2)], color)
        elif adorno == 'montana':
            svg.addPoligono([(izq, arriba - 2), (izq + 10, arriba - 9), (izq + 12, arriba - 2)],
                            color)
            svg.addPoligono([(izq + 15, arriba - 2), (der, arriba - 11), (der, arriba - 2)],
                            color)
        elif adorno == 'cuadros':
            lado = (der - izq) / 6
            for fila in range(2):
                for columna in range(6):
                    if (fila + columna) % 2 == 0:
                        svg.addRect(izq + columna * lado, arriba - 2 - lado * (fila + 1),
                                    lado, lado, color)
        elif adorno == 'rayas':
            for i in range(3):
                svg.addRect(izq + 3 * i, arriba - 4 - 3.5 * i, der - izq - 6 * i, 2, color)
        elif adorno == 'almena':
            svg.addRect(izq + 6, arriba - 6, der - izq - 12, 4, color)
            svg.addRect(izq + 11, arriba - 9, der - izq - 22, 3, color)

    def __addDesnivel(self, svg):
        """
        Desnivel positivo de la etapa al pie, en horizontal
        """
        texto = svg.addTexto(self.ANCHO / 2, self.Y_PIE, '', 26, self.estilos.COLOR_TEXTO,
                             anclaje='middle')
        svg.addTramoTexto(texto, 'Desnivel positivo: ', negrita=True)
        svg.addTramoTexto(texto, '{} m'.format(formatoMetros(self.lector.desnivelEtapa())))


class Aplicacion(object):
    """
    Punto de entrada del programa xml2altimetria.py
    """
    ARCHIVO_XML = 'etapaEsquema.xml'
    ARCHIVO_SVG = 'altimetria.svg'

    def ejecutar(self):
        """
        Lee etapaEsquema.xml y genera altimetria.svg
        """
        print(__doc__)
        generador = GeneradorAltimetria(LectorEtapa(self.ARCHIVO_XML), EstilosAltimetria())
        generador.generar(self.ARCHIVO_SVG)
        print('Creado el archivo: ', self.ARCHIVO_SVG)


if __name__ == '__main__':
    Aplicacion().ejecutar()