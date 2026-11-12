"use strict";

class Ciclista {
  #dorsal;
  #nacionalidad;
  #codigoNacionalidad;
  #nombre;
  #apellidos;
  #fechaNacimiento;

  constructor(
    dorsal,
    nacionalidad,
    codigoNacionalidad,
    nombre,
    apellidos,
    fechaNacimiento,
  ) {
    this.#dorsal = dorsal;
    this.#nacionalidad = nacionalidad;
    this.#codigoNacionalidad = codigoNacionalidad;
    this.#nombre = nombre;
    this.#apellidos = apellidos;
    this.#fechaNacimiento = fechaNacimiento;
  }

  getNombreCompleto() {
    return `${this.#nombre} - ${this.#apellidos}`;
  }

  getDorsal() {
    return this.#dorsal;
  }

  getInformacionAdicional() {
    return `${this.#fechaNacimiento}, ${this.#nacionalidad}`;
  }
}

class Equipo {
  #equipo;
  #codigoUCI;
  #pais;
  #director;
  #categoria;
  #paginaWeb;
  #alineacion;

  constructor(equipo, codigoUCI, pais) {
    this.#equipo = equipo;
    this.#codigoUCI = codigoUCI;
    this.#pais = pais;
    this.#alineacion = [];
  }

  rellenarAtributos() {
    this.#director = "Rudie Kemna";
    this.#categoria = "UCI WorldTeam";
    this.#paginaWeb = "https://www.teampicnicpostnl.com";
  }

  datosBasicos() {
    return `${this.#equipo} (${this.#codigoUCI})`;
  }

  getPais() {
    return this.#pais;
  }

  getInformacionSecundaria() {
    return (
      `<ul>` +
      `<li>Director: ${this.#director}.</li>` +
      `<li>Categoría: ${this.#categoria}.</li>` +
      `</ul>`
    );
  }

  getPaginaWeb() {
    const section = document.querySelector("section");
    const a = document.createElement("a");
    a.href = this.#paginaWeb;
    a.textContent = "Página web del equipo";
    section.appendChild(a);
  }

  async leerEquipo() {
    const fichero = "js/lavuelta.json";
    const response = await fetch(fichero);
    const data = await response.json();
    const equipos = data.equipos;
    const equipo = equipos.find(
      (equipo_1) => equipo_1.codigo_uci === this.#codigoUCI,
    );
    this.alinearCiclistas(equipo.corredores);
  }

  alinearCiclistas(corredores) {
    corredores.forEach((corredor) => {
      const ciclista = new Ciclista(
        corredor.dorsal,
        corredor.nacionalidad,
        corredor.nacionaliad_codigo,
        corredor.nombre,
        corredor.apellidos,
        corredor.fecha_nacimiento,
      );
      this.#alineacion.push(ciclista);
    });
  }

  mostrarAlineacion() {
    const section = document.querySelector("main > section:last-of-type");

    const ordenados = [...this.#alineacion].sort(
      (a, b) => a.getDorsal() - b.getDorsal(),
    );
    ordenados.forEach((ciclista) => {
      const article = document.createElement("article");

      const h4 = document.createElement("h4");
      h4.textContent = ciclista.getNombreCompleto();
      article.appendChild(h4);

      const img = document.createElement("img");
      img.src = "multimedia/icono-ciclista.png";
      img.alt = "Icono genérico de un ciclista";
      img.width = 128;
      img.height = 128;
      article.appendChild(img);

      const pDorsal = document.createElement("p");
      pDorsal.textContent = ciclista.getDorsal();
      article.appendChild(pDorsal);

      const pInfoAdicional = document.createElement("p");
      pInfoAdicional.textContent = `${ciclista.getInformacionAdicional()}`;
      article.appendChild(pInfoAdicional);

      section.appendChild(article);
    });
  }
}

const equipo = new Equipo("Team Picnic-PostNL", "TPP", "Países Bajos");
equipo.rellenarAtributos();

const section = document.createElement("section");

const h3 = document.createElement("h3");
h3.textContent = equipo.datosBasicos() + `, ${equipo.getPais()}`;
section.appendChild(h3);

section.insertAdjacentHTML("beforeend", equipo.getInformacionSecundaria());

const h2 = document.querySelector("main > h2");
h2.insertAdjacentElement("afterend", section);

equipo.getPaginaWeb();
equipo.leerEquipo().then(() => {
  equipo.mostrarAlineacion();
});
