"use strict";

class Carrusel {
  #busqueda;
  #actual = 0;
  #maximo = 4;
  #fotografias;
  #imagenes = [];

  constructor(busqueda) {
    this.#busqueda = busqueda;
  }

  getFotografias() {
    const flickrAPI =
      "https://api.flickr.com/services/feeds/photos_public.gne?jsoncallback=?";

    return $.getJSON(flickrAPI, {
      tags: this.#busqueda,
      tagmode: "any",
      format: "json",
    }).done((datos) => {
      // El feed devuelve las imágenes con el sufijo _m (240 px).
      // Se sustituye por _z para obtenerlas todas a 640 px en el borde más grande.
      $.each(datos.items, (_, item) => {
        item.media.m = item.media.m.replace("_m.", "_z.");
      });
      this.#fotografias = datos;
    });
  }

  procesarJSONFotografias() {
    this.#imagenes = [];

    // Se recorren los items hasta tener maximo + 1 (5) fotografías diferentes
    for (const item of this.#fotografias.items) {
      if (this.#imagenes.length > this.#maximo) break;

      const url = item.media.m;
      if (this.#imagenes.some((imagen) => imagen.url === url)) continue;

      this.#imagenes.push({
        titulo: item.title,
        url: url,
        autor: item.author,
        enlace: item.link,
      });
    }
  }

  mostrarFotografias() {
    const imagen = this.#imagenes[this.#actual];

    const articulo = $("<article>");
    articulo.append($("<h2>").text("Instantáneas de LaVuelta"));
    articulo.append(
      $("<img>").attr({
        src: imagen.url,
        alt: imagen.titulo,
      }),
    );

    $("main").append(articulo);

    setInterval(this.cambiarFotografia.bind(this), 3000);
  }

  cambiarFotografia() {
    // Se avanza a la siguiente foto y, tras la quinta, se vuelve a la primera
    if (this.#actual < this.#maximo && this.#actual < this.#imagenes.length - 1) {
      this.#actual++;
    } else {
      this.#actual = 0;
    }

    const imagen = this.#imagenes[this.#actual];
    $("main article h2 + img").attr({
      src: imagen.url,
      alt: imagen.titulo,
    });
  }
}

const carrusel = new Carrusel("lavuelta2026");
carrusel.getFotografias().done(() => {
  carrusel.procesarJSONFotografias();
  carrusel.mostrarFotografias();
});
