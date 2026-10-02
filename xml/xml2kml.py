# xml2kml.py
# -*- coding: utf-8 -*-
"""
Genera el archivo etapa.kml (planimetría de la etapa) a partir de etapaEsquema.xml

- Lee el árbol DOM con xml.etree.ElementTree
- Obtiene los datos mediante expresiones XPath
- Marca en rojo salida y meta, en verde los puertos de montaña,
  en azul los sprints intermedios y en amarillo los puntos anónimos

@version 1.0 01/Octubre/2026
@author: Daniel Rodríguez Fernández. Universidad de Oviedo
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class PuntoEtapa(object):
    """
    Punto geográfico de la etapa (salida, meta o hito)
    """
    nombre: str
    tipo: str
    longitud: float
    latitud: float
    altitud: float
    distanciaSalida: float

    def coordenadasKml(self):
        """
        Devuelve las coordenadas en el formato de KML: longitud,latitud,altitud
        """
        return '{},{},{}'.format(self.longitud, self.latitud, self.altitud)

    def descripcion(self):
        """
        Texto descriptivo del punto para el globo de información del KML
        """
        return 'Km {:.2f} - Altitud {:.0f} m'.format(self.distanciaSalida, self.altitud)


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

    def salida(self):
        """
        Punto de salida de la etapa
        """
        coordenadas = self.raiz.find('uo:salida/uo:coordenadas', self.ESPACIO_NOMBRES)
        nombre = 'Salida: ' + self.__texto(self.raiz, 'uo:lugar_salida')
        return self.__crearPunto(coordenadas, nombre, 'salida', 0.0)

    def meta(self):
        """
        Punto de llegada de la etapa
        """
        coordenadas = self.raiz.find('uo:meta/uo:coordenadas', self.ESPACIO_NOMBRES)
        nombre = 'Meta: ' + self.__texto(self.raiz, 'uo:lugar_meta')
        return self.__crearPunto(coordenadas, nombre, 'meta', self.longitudEtapa())

    def hitos(self):
        """
        Todos los hitos de la etapa en el orden del recorrido
        """
        return [self.__crearHito(hito)
                for hito in self.raiz.findall('uo:hitos/uo:hito', self.ESPACIO_NOMBRES)]

    def hitosDeTipo(self, tipo):
        """
        Hitos cuyo atributo tipo coincide con el indicado
        """
        expresion = "uo:hitos/uo:hito[@tipo='{}']".format(tipo)
        return [self.__crearHito(hito)
                for hito in self.raiz.findall(expresion, self.ESPACIO_NOMBRES)]

    def __crearHito(self, hito):
        """
        Convierte un elemento <hito> del árbol DOM en un PuntoEtapa
        """
        tipo = hito.get('tipo')
        nombre = hito.get('nombre', tipo.replace('_', ' ').capitalize())
        distancia = float(self.__texto(hito, 'uo:distancia_salida'))
        coordenadas = hito.find('uo:coordenadas', self.ESPACIO_NOMBRES)
        return self.__crearPunto(coordenadas, nombre, tipo, distancia)

    def __crearPunto(self, coordenadas, nombre, tipo, distancia):
        """
        Crea un PuntoEtapa a partir de un elemento <coordenadas>
        """
        return PuntoEtapa(nombre=nombre,
                          tipo=tipo,
                          longitud=float(self.__texto(coordenadas, 'uo:longitud')),
                          latitud=float(self.__texto(coordenadas, 'uo:latitud')),
                          altitud=float(self.__texto(coordenadas, 'uo:altitud')),
                          distanciaSalida=distancia)

    def __texto(self, elemento, expresion):
        """
        Contenido textual del nodo seleccionado por la expresión XPath
        """
        return elemento.findtext(expresion, namespaces=self.ESPACIO_NOMBRES).strip()


class Kml(object):
    """
    Genera archivos KML con estilos, puntos y líneas
    """

    def __init__(self, nombre):
        """
        Crea el elemento raíz, el espacio de nombres y el documento
        """
        self.raiz = ET.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
        self.doc = ET.SubElement(self.raiz, 'Document')
        ET.SubElement(self.doc, 'name').text = nombre

    def addEstiloPunto(self, idEstilo, color, escala):
        """
        Añade un estilo de icono reutilizable (color en formato aabbggrr)
        No se indica <Icon>: se usa el icono integrado del visor, sin descargas
        """
        estilo = ET.SubElement(self.doc, 'Style', id=idEstilo)
        icono = ET.SubElement(estilo, 'IconStyle')
        ET.SubElement(icono, 'color').text = color
        ET.SubElement(icono, 'scale').text = str(escala)

    def addEstiloLinea(self, idEstilo, color, ancho):
        """
        Añade un estilo de línea reutilizable (color en formato aabbggrr)
        """
        estilo = ET.SubElement(self.doc, 'Style', id=idEstilo)
        linea = ET.SubElement(estilo, 'LineStyle')
        ET.SubElement(linea, 'color').text = color
        ET.SubElement(linea, 'width').text = str(ancho)

    def addPlacemark(self, nombre, descripcion, coordenadas, idEstilo):
        """
        Añade un elemento <Placemark> con un punto <Point>
        Si no se indica nombre, el punto se muestra en el mapa sin etiqueta
        """
        pm = ET.SubElement(self.doc, 'Placemark')
        if nombre is not None:
            ET.SubElement(pm, 'name').text = nombre
        ET.SubElement(pm, 'description').text = descripcion
        ET.SubElement(pm, 'styleUrl').text = '#' + idEstilo
        punto = ET.SubElement(pm, 'Point')
        ET.SubElement(punto, 'coordinates').text = coordenadas
        ET.SubElement(punto, 'altitudeMode').text = 'clampToGround'

    def addLineString(self, nombre, listaCoordenadas, idEstilo):
        """
        Añade un elemento <Placemark> con una línea <LineString>
        """
        pm = ET.SubElement(self.doc, 'Placemark')
        ET.SubElement(pm, 'name').text = nombre
        ET.SubElement(pm, 'styleUrl').text = '#' + idEstilo
        ls = ET.SubElement(pm, 'LineString')
        ET.SubElement(ls, 'tessellate').text = '1'
        ET.SubElement(ls, 'coordinates').text = '\n'.join(listaCoordenadas)
        ET.SubElement(ls, 'altitudeMode').text = 'clampToGround'

    def escribir(self, nombreArchivoKML):
        """
        Escribe el archivo KML con declaración, codificación e indentación
        """
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        arbol.write(nombreArchivoKML, encoding='utf-8', xml_declaration=True)


class EstilosEtapa(object):
    """
    Asocia cada tipo de punto de la etapa con su estilo y color en el KML
    """
    # Colores KML en formato aabbggrr
    ESTILOS = {
        'salida':              ('estiloSalidaMeta', 'ff0000ff', 1.4),  # rojo
        'meta':                ('estiloSalidaMeta', 'ff0000ff', 1.4),  # rojo
        'puerto_especial':     ('estiloPuerto',     'ff00ff00', 1.2),  # verde
        'puerto_1a_categoria': ('estiloPuerto',     'ff00ff00', 1.2),  # verde
        'puerto_2a_categoria': ('estiloPuerto',     'ff00ff00', 1.2),  # verde
        'puerto_3a_categoria': ('estiloPuerto',     'ff00ff00', 1.2),  # verde
        'sprint_intermedio':   ('estiloSprint',     'ffff0000', 1.2),  # azul
        'punto_anonimo':       ('estiloAnonimo',    'ff00ffff', 0.5),  # amarillo
    }
    # Tipos de punto que se dibujan sin nombre en el mapa
    SIN_NOMBRE = {'punto_anonimo'}
    ESTILO_RUTA = ('estiloRuta', 'ff0000ff', 4)  # línea roja

    def registrar(self, kml):
        """
        Declara en el KML todos los estilos necesarios (sin duplicados)
        """
        registrados = set()
        for idEstilo, color, escala in self.ESTILOS.values():
            if idEstilo not in registrados:
                kml.addEstiloPunto(idEstilo, color, escala)
                registrados.add(idEstilo)
        idRuta, colorRuta, anchoRuta = self.ESTILO_RUTA
        kml.addEstiloLinea(idRuta, colorRuta, anchoRuta)

    def estiloDe(self, punto):
        """
        Identificador del estilo correspondiente al tipo del punto
        """
        return self.ESTILOS[punto.tipo][0]

    def muestraNombre(self, punto):
        """
        Indica si el punto debe aparecer con su nombre en el mapa
        """
        return punto.tipo not in self.SIN_NOMBRE

    def estiloRuta(self):
        """
        Identificador del estilo de la línea del recorrido
        """
        return self.ESTILO_RUTA[0]


class GeneradorPlanimetria(object):
    """
    Construye la planimetría KML de una etapa a partir de sus datos
    """

    def __init__(self, lector, estilos):
        """
        Recibe sus dependencias por inyección para poder sustituirlas
        """
        self.lector = lector
        self.estilos = estilos

    def generar(self, nombreArchivoKML):
        """
        Genera y escribe el archivo KML de la etapa
        """
        kml = Kml(self.lector.nombreEtapa())
        self.estilos.registrar(kml)

        salida = self.lector.salida()
        meta = self.lector.meta()
        hitos = self.lector.hitos()

        self.__addRuta(kml, [salida] + hitos + [meta])
        self.__addPuntos(kml, [salida, meta] + hitos)

        kml.escribir(nombreArchivoKML)

    def __addRuta(self, kml, puntos):
        """
        Añade la línea del recorrido completo de la etapa
        """
        kml.addLineString('Recorrido',
                          [punto.coordenadasKml() for punto in puntos],
                          self.estilos.estiloRuta())

    def __addPuntos(self, kml, puntos):
        """
        Añade un marcador por cada punto con el estilo según su tipo
        """
        for punto in puntos:
            nombre = punto.nombre if self.estilos.muestraNombre(punto) else None
            kml.addPlacemark(nombre, punto.descripcion(),
                             punto.coordenadasKml(), self.estilos.estiloDe(punto))


class Aplicacion(object):
    """
    Punto de entrada del programa xml2kml.py
    """
    ARCHIVO_XML = 'etapaEsquema.xml'
    ARCHIVO_KML = 'etapa.kml'

    def ejecutar(self):
        """
        Lee etapaEsquema.xml y genera etapa.kml
        """
        print(__doc__)
        generador = GeneradorPlanimetria(LectorEtapa(self.ARCHIVO_XML), EstilosEtapa())
        generador.generar(self.ARCHIVO_KML)
        print('Creado el archivo: ', self.ARCHIVO_KML)


if __name__ == '__main__':
    Aplicacion().ejecutar()
