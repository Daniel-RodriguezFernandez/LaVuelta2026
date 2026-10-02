# xml2altimetria.py
# -*- coding: utf-8 -*-
"""
Genera el archivo altimetria.svg (perfil altimétrico de la etapa) a partir de etapaEsquema.xml

- Lee el árbol DOM con xml.etree.ElementTree
- Obtiene los datos mediante expresiones XPath
- Dibuja el perfil de la etapa (distancia desde la salida frente a altitud)
  con una rejilla de referencia y etiquetas para salida, meta, puertos de
  montaña y sprints intermedios, a semejanza del libro de ruta oficial

@author: Daniel Rodríguez Fernández. Universidad de Oviedo
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class PuntoPerfil(object):
    """
    Punto del perfil altimétrico de la etapa (salida, meta o hito)
    """
    nombre: str
    tipo: str
    altitud: float
    distanciaSalida: float

    def etiqueta(self):
        """
        Texto con la altitud y el punto kilométrico del punto
        """
        return '{:.0f} m · km {:.1f}'.format(self.altitud, self.distanciaSalida)


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
        Desnivel acumulado de la etapa en metros
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
        Todos los hitos de la etapa en el orden del recorrido
        """
        return [self.__crearHito(hito)
                for hito in self.raiz.findall('uo:hitos/uo:hito', self.ESPACIO_NOMBRES)]

    def hitosConNombre(self):
        """
        Hitos destacados (puertos y sprints): los que tienen atributo nombre
        """
        return [self.__crearHito(hito)
                for hito in self.raiz.findall('uo:hitos/uo:hito[@nombre]', self.ESPACIO_NOMBRES)]

    def __crearHito(self, hito):
        """
        Convierte un elemento <hito> del árbol DOM en un PuntoPerfil
        """
        tipo = hito.get('tipo')
        return PuntoPerfil(nombre=hito.get('nombre', tipo.replace('_', ' ').capitalize()),
                           tipo=tipo,
                           altitud=float(self.__texto(hito, 'uo:coordenadas/uo:altitud')),
                           distanciaSalida=float(self.__texto(hito, 'uo:distancia_salida')))

    def __texto(self, elemento, expresion):
        """
        Contenido textual del nodo seleccionado por la expresión XPath
        """
        return elemento.findtext(expresion, namespaces=self.ESPACIO_NOMBRES).strip()


class Svg(object):
    """
    Genera archivos SVG con rectángulos, líneas, polígonos, círculos y textos
    """

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
        ET.SubElement(self.raiz, 'rect', x=self.__num(x), y=self.__num(y),
                      width=self.__num(ancho), height=self.__num(alto),
                      fill=relleno, stroke=trazo)

    def addLinea(self, x1, y1, x2, y2, color, ancho, discontinua=None):
        """
        Añade una línea recta; si se indica, con trazo discontinuo
        """
        linea = ET.SubElement(self.raiz, 'line', x1=self.__num(x1), y1=self.__num(y1),
                              x2=self.__num(x2), y2=self.__num(y2), stroke=color)
        linea.set('stroke-width', str(ancho))
        if discontinua is not None:
            linea.set('stroke-dasharray', discontinua)

    def addPoligono(self, puntos, relleno, trazo, ancho):
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

    def addCirculo(self, cx, cy, radio, relleno, trazo='#ffffff'):
        """
        Añade un círculo
        """
        circulo = ET.SubElement(self.raiz, 'circle', cx=self.__num(cx), cy=self.__num(cy),
                                r=str(radio), fill=relleno, stroke=trazo)
        circulo.set('stroke-width', '2')

    def addTexto(self, x, y, texto, tamano, color='#222222', anclaje='start',
                 negrita=False, rotacion=0):
        """
        Añade un texto, opcionalmente en negrita y girado sobre su punto de anclaje
        """
        elemento = ET.SubElement(self.raiz, 'text', x=self.__num(x), y=self.__num(y),
                                 fill=color)
        elemento.set('font-family', 'Arial, Helvetica, sans-serif')
        elemento.set('font-size', str(tamano))
        elemento.set('text-anchor', anclaje)
        if negrita:
            elemento.set('font-weight', 'bold')
        if rotacion:
            elemento.set('transform', 'rotate({} {} {})'.format(
                rotacion, self.__num(x), self.__num(y)))
        elemento.text = texto
        return elemento

    def addTramoTexto(self, elementoTexto, texto, color=None, negrita=False):
        """
        Añade un <tspan> a continuación del contenido de un texto existente
        """
        tramo = ET.SubElement(elementoTexto, 'tspan')
        if color is not None:
            tramo.set('fill', color)
        if negrita:
            tramo.set('font-weight', 'bold')
        tramo.text = texto

    def escribir(self, nombreArchivoSVG):
        """
        Escribe el archivo SVG con declaración, codificación e indentación
        """
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        arbol.write(nombreArchivoSVG, encoding='utf-8', xml_declaration=True)

    def __puntos(self, puntos):
        """
        Lista de pares (x, y) en el formato del atributo points
        """
        return ' '.join('{},{}'.format(self.__num(x), self.__num(y)) for x, y in puntos)

    def __num(self, valor):
        """
        Número con dos decimales como máximo
        """
        return '{:.2f}'.format(valor).rstrip('0').rstrip('.')


class EstilosAltimetria(object):
    """
    Colores y textos asociados a cada tipo de punto del perfil
    """
    # tipo: (color del marcador, texto de la categoría)
    TIPOS = {
        'salida':              ('#d0021b', 'Salida'),
        'meta':                ('#d0021b', 'Meta'),
        'puerto_especial':     ('#4a0d0d', 'Cat. Especial'),
        'puerto_1a_categoria': ('#c0392b', '1ª Cat.'),
        'puerto_2a_categoria': ('#e67e22', '2ª Cat.'),
        'puerto_3a_categoria': ('#27ae60', '3ª Cat.'),
        'sprint_intermedio':   ('#1f6fd1', 'Sprint'),
        'punto_anonimo':       ('#888888', ''),
    }
    COLOR_FONDO = '#ffffff'
    COLOR_PERFIL = '#8a6d1d'
    RELLENO_PERFIL = '#f5d76e'
    COLOR_REJILLA = '#dddddd'
    COLOR_EJES = '#444444'
    COLOR_TEXTO = '#222222'
    COLOR_SECUNDARIO = '#666666'

    def colorDe(self, punto):
        """
        Color del marcador según el tipo del punto
        """
        return self.TIPOS[punto.tipo][0]

    def categoriaDe(self, punto):
        """
        Texto de la categoría del punto (puerto, sprint, salida o meta)
        """
        return self.TIPOS[punto.tipo][1]


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


class GeneradorAltimetria(object):
    """
    Construye la altimetría SVG de una etapa a partir de sus datos
    """
    ANCHO = 1200
    ALTO = 800
    MARGEN_IZQUIERDO = 80
    MARGEN_DERECHO = 50
    MARGEN_SUPERIOR = 370   # espacio para las etiquetas verticales de los hitos
    MARGEN_INFERIOR = 90
    PASO_KM = 10
    PASO_ALTITUD = 250

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

        svg = Svg(self.ANCHO, self.ALTO)
        svg.addTitulo(self.__titulo())
        svg.addRect(0, 0, self.ANCHO, self.ALTO, self.estilos.COLOR_FONDO)

        self.__addCabecera(svg)
        self.__addRejilla(svg, escala)
        self.__addPerfil(svg, escala, perfil)
        self.__addEjes(svg, escala)
        self.__addHitos(svg, escala, self.lector.hitosConNombre())
        self.__addSalidaMeta(svg, escala, salida, meta)

        svg.escribir(nombreArchivoSVG)

    def __crearEscala(self, perfil, distanciaMaxima):
        """
        Escala del perfil: la altitud máxima se redondea al siguiente múltiplo del paso
        """
        altitudMaxima = max(punto.altitud for punto in perfil)
        techo = math.ceil(altitudMaxima / self.PASO_ALTITUD) * self.PASO_ALTITUD
        return EscalaPerfil(self.MARGEN_IZQUIERDO, self.ALTO - self.MARGEN_INFERIOR,
                            self.ANCHO - self.MARGEN_IZQUIERDO - self.MARGEN_DERECHO,
                            self.ALTO - self.MARGEN_SUPERIOR - self.MARGEN_INFERIOR,
                            distanciaMaxima, techo)

    def __titulo(self):
        """
        Título de la etapa: número y nombre
        """
        return 'Etapa {}. {}'.format(self.lector.numeroEtapa(), self.lector.nombreEtapa())

    def __addCabecera(self, svg):
        """
        Título de la etapa y datos generales (longitud y desnivel)
        """
        svg.addTexto(self.MARGEN_IZQUIERDO, 40, self.__titulo(), 24,
                     self.estilos.COLOR_TEXTO, negrita=True)
        datos = 'Altimetría · {:.1f} km · Desnivel acumulado {:.0f} m'.format(
            self.lector.longitudEtapa(), self.lector.desnivelEtapa())
        svg.addTexto(self.MARGEN_IZQUIERDO, 66, datos, 15, self.estilos.COLOR_SECUNDARIO)

    def __addRejilla(self, svg, escala):
        """
        Líneas horizontales de altitud y verticales de distancia
        """
        for altitud in range(self.PASO_ALTITUD, int(escala.altitudMaxima) + 1, self.PASO_ALTITUD):
            y = escala.y(altitud)
            svg.addLinea(escala.x0, y, escala.x0 + escala.ancho, y,
                         self.estilos.COLOR_REJILLA, 1)
            svg.addTexto(escala.x0 - 10, y + 4, '{} m'.format(altitud), 12,
                         self.estilos.COLOR_SECUNDARIO, anclaje='end')
        for km in range(self.PASO_KM, int(escala.distanciaMaxima) + 1, self.PASO_KM):
            x = escala.x(km)
            svg.addLinea(x, escala.y0, x, escala.y(escala.altitudMaxima),
                         self.estilos.COLOR_REJILLA, 1)

    def __addPerfil(self, svg, escala, perfil):
        """
        Área rellena bajo el perfil y su contorno
        """
        contorno = [escala.punto(punto) for punto in perfil]
        base = [(contorno[-1][0], escala.y0), (contorno[0][0], escala.y0)]
        svg.addPoligono(contorno + base, self.estilos.RELLENO_PERFIL, 'none', 0)
        svg.addPolilinea(contorno, self.estilos.COLOR_PERFIL, 2.5)

    def __addEjes(self, svg, escala):
        """
        Ejes de distancia y altitud con las marcas kilométricas
        """
        svg.addLinea(escala.x0, escala.y0, escala.x0 + escala.ancho, escala.y0,
                     self.estilos.COLOR_EJES, 1.5)
        svg.addLinea(escala.x0, escala.y0, escala.x0, escala.y(escala.altitudMaxima),
                     self.estilos.COLOR_EJES, 1.5)
        for km in range(0, int(escala.distanciaMaxima) + 1, self.PASO_KM):
            x = escala.x(km)
            svg.addLinea(x, escala.y0, x, escala.y0 + 6, self.estilos.COLOR_EJES, 1.5)
            svg.addTexto(x, escala.y0 + 20, str(km), 12, self.estilos.COLOR_SECUNDARIO,
                         anclaje='middle')
        svg.addTexto(escala.x0 + escala.ancho, escala.y0 + 20, 'km', 12,
                     self.estilos.COLOR_SECUNDARIO, anclaje='start')

    def __addHitos(self, svg, escala, hitos):
        """
        Marcador sobre el perfil y etiqueta vertical para cada hito destacado
        """
        yEtiqueta = escala.y(escala.altitudMaxima) - 12
        for hito in hitos:
            x, y = escala.punto(hito)
            color = self.estilos.colorDe(hito)
            svg.addLinea(x, y, x, yEtiqueta, color, 1, discontinua='4 3')
            svg.addCirculo(x, y, 6, color)
            texto = svg.addTexto(x - 3, yEtiqueta, '', 13, self.estilos.COLOR_TEXTO,
                                 rotacion=-90)
            svg.addTramoTexto(texto, self.estilos.categoriaDe(hito) + '  ', color, negrita=True)
            svg.addTramoTexto(texto, hito.nombre, negrita=True)
            svg.addTexto(x + 12, yEtiqueta, hito.etiqueta(), 11,
                         self.estilos.COLOR_SECUNDARIO, rotacion=-90)

    def __addSalidaMeta(self, svg, escala, salida, meta):
        """
        Marcadores de salida y meta con su nombre bajo el eje de distancias
        """
        for punto, anclaje in ((salida, 'start'), (meta, 'end')):
            x, y = escala.punto(punto)
            color = self.estilos.colorDe(punto)
            svg.addCirculo(x, y, 7, color)
            texto = svg.addTexto(x, escala.y0 + 48, '', 15, self.estilos.COLOR_TEXTO,
                                 anclaje=anclaje)
            svg.addTramoTexto(texto, self.estilos.categoriaDe(punto).upper() + ': ',
                              color, negrita=True)
            svg.addTramoTexto(texto, punto.nombre, negrita=True)
            svg.addTexto(x, escala.y0 + 68, punto.etiqueta(), 12,
                         self.estilos.COLOR_SECUNDARIO, anclaje=anclaje)


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
