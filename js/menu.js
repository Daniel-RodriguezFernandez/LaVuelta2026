"use strict";

class Menu {
  #boton;
  #menu;

  constructor() {
    this.#boton = document.querySelector("header > button");
    this.#menu = document.querySelector("nav");
    this.#boton.addEventListener("click", () => this.desplegar());
  }

  desplegar() {
    const abierto = this.#menu.classList.toggle("abierto");
    this.#boton.textContent = abierto ? "x" : "☰";
    this.#boton.setAttribute("aria-expanded", abierto ? "true" : "false");
    this.#boton.setAttribute(
      "aria-label",
      abierto ? "Cerrar menú de navegación" : "Abrir menú de navegación",
    );
  }
}

const menu = new Menu();
