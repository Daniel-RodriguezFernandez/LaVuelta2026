"use strict";
class Ciudad {
  #ciudad;
  #pais;
  #gentilicio;
  #poblacion;
  #coordenadas;

  constructor(ciudad, pais, gentilicio) {
    this.#ciudad = ciudad;
    this.#pais = pais;
    this.#gentilicio = gentilicio;
  }

  rellenarAtributos() {
    this.#poblacion = 27_554;
    this.#coordenadas = { latitud: 36.733333, longitud: -3.683333 };
  }

  getCiudad() {
    return this.#ciudad;
  }

  getPais() {
    return this.#pais;
  }

  getInformacionSecundaria() {
    return (
      `<ul>` +
      `<li>Población: ${this.#poblacion} habitantes.</li>` +
      `<li>Gentilicio: ${this.#gentilicio}.</li>` +
      `</ul>`
    );
  }
  escribeCoordenadas() {
    const section = document.querySelector("section");
    const coordenadas = document.createElement("p");
    coordenadas.textContent = `Coordenadas: ${this.#coordenadas.latitud}, ${this.#coordenadas.longitud}.`;
    section.appendChild(coordenadas);
  }
}

const ciudad = new Ciudad("Almuñécar", "España", "sexitano");
ciudad.rellenarAtributos();

const section = document.createElement("section");

const h3 = document.createElement("h3");
h3.textContent = `${ciudad.getCiudad()}, ${ciudad.getPais()}`;
section.appendChild(h3);

section.insertAdjacentHTML("beforeend", ciudad.getInformacionSecundaria());

const h2 = document.querySelector("main > h2");
h2.insertAdjacentElement("afterend", section);

ciudad.escribeCoordenadas();
