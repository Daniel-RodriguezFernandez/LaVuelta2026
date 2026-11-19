"use strict";

class Buscador {
  #lupa;
  #entrada;

  constructor() {
    this.#lupa = document.querySelector("search > label > img");
    this.#entrada = document.querySelector("search > input");

    this.#lupa.addEventListener("click", this.buscar.bind(this));
    this.#entrada.addEventListener(
      "keypress",
      function (evento) {
        if (evento.key === "Enter") {
          this.buscar();
        }
      }.bind(this),
    );
  }

  buscar() {
    this.limpiar_busqueda();

    const resultados = [];
    const texto = this.#entrada.value.trim();

    if (texto === "") {
      return;
    }

    // Se escapan los caracteres especiales para buscar el texto literal
    const textoBuscar = texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

    // 1) Expresión regular global e insensible a mayúsculas/minúsculas
    const expresion = new RegExp(textoBuscar, "gi");

    // 2) Nodos de texto del cuerpo del documento
    const recorrido = document.createTreeWalker(
      document.querySelector("body"),
      NodeFilter.SHOW_TEXT,
    );

    // 3) Primer nodo a analizar
    let nodo = recorrido.nextNode();

    // 4) Se guardan los nodos que contienen el texto buscado
    while (nodo) {
      // Con el flag 'g', test() avanza lastIndex: se reinicia en cada nodo
      expresion.lastIndex = 0;
      if (expresion.test(nodo.textContent)) {
        resultados.push(nodo);
      }
      nodo = recorrido.nextNode();
    }

    // 5) Se resalta cada aparición con un elemento <mark>
    resultados.forEach((nodo) => {
      const partes = nodo.textContent.split(
        new RegExp(`(${textoBuscar})`, "gi"),
      );
      nodo.replaceWith(
        ...partes.map((parte, indice) => {
          if (indice % 2 === 0) return document.createTextNode(parte);
          const marca = document.createElement("mark");
          marca.textContent = parte;
          return marca;
        }),
      );
    });
  }

  limpiar_busqueda() {
    document.querySelectorAll("mark").forEach((marca) => {
      marca.replaceWith(document.createTextNode(marca.textContent));
    });
    document.body.normalize();
  }
}

const buscador = new Buscador();
