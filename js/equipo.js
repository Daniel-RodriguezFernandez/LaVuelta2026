"use strict";
class Equipo {
    #equipo;
    #codigoUCI;
    #pais;
    #director;
    #categoria;
    #paginaWeb;

    constructor(equipo, codigoUCI, pais) {
        this.#equipo = equipo;
        this.#codigoUCI = codigoUCI;
        this.#pais = pais;
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