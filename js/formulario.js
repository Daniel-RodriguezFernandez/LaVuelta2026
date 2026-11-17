"use strict";

class Formulario {
  #puntuacion;
  #dureza;
  #descripcion;
  #usuario;

  constructor() {
    this.#puntuacion = 0;

    const boton = document.querySelector("form button[type='submit']");
    boton.addEventListener("click", (evento) => {
      evento.preventDefault();
      this.analizar(evento);
    });
  }

  analizar(evento) {
    const form = evento.target.closest("form");
    this.#puntuacion = 0;

    this.#dureza = this.#obtenerRespuesta(form, "durezaEtapa");
    this.#descripcion = this.#obtenerRespuesta(form, "descripcionEtapa");
    this.#usuario = this.#obtenerRespuesta(form, "nombreParticipante");

    const soluciones = this.#cargarSoluciones(form);

    for (const [nombre, solucion] of soluciones) {
      if (this.#esCorrecta(form, nombre, solucion)) {
        this.#puntuacion++;
      }
    }

    this.calificar();
  }

  #cargarSoluciones(form) {
    const soluciones = new Map();

    for (const elemento of form.querySelectorAll("[data-solution]")) {
      const campo =
        elemento.tagName === "FIELDSET"
          ? elemento.querySelector("input[name]")
          : elemento;
      const valor = elemento.dataset.solution;

      let solucion = valor;
      if (campo.type === "checkbox") {
        solucion = valor.split(";");
      } else if (campo.type === "number") {
        solucion = Number(valor);
      }

      soluciones.set(campo.name, solucion);
    }

    return soluciones;
  }

  #esCorrecta(form, nombre, solucion) {
    if (Array.isArray(solucion)) {
      return this.#mismosElementos(
        this.#obtenerMarcadas(form, nombre),
        solucion,
      );
    }

    const respuesta = this.#obtenerRespuesta(form, nombre);

    if (typeof solucion === "number") {
      return this.#mismoNumero(respuesta, solucion);
    }

    return respuesta === solucion;
  }

  #mismoNumero(respuesta, solucion) {
    if (respuesta === "") {
      return false;
    }
    const valor = Number(respuesta);
    return Number.isFinite(valor) && valor === solucion;
  }

  #obtenerRespuesta(form, nombre) {
    const elemento =
      form.querySelector(`[name='${nombre}']:checked`) ??
      form.querySelector(
        `[name='${nombre}']:not([type='radio']):not([type='checkbox'])`,
      );
    return elemento ? elemento.value.trim() : "";
  }

  #obtenerMarcadas(form, nombre) {
    return [...form.querySelectorAll(`[name='${nombre}']:checked`)].map(
      (marcada) => marcada.value,
    );
  }

  #mismosElementos(entrada, solucion) {
    return (
      entrada.length === solucion.length &&
      entrada.every((v) => solucion.includes(v))
    );
  }

  calificar() {
    const parrafo = document.createElement("p");
    parrafo.textContent =
      `${this.#usuario} has obtenido ${this.#puntuacion} puntos, ` +
      `la dureza que has asignado a la etapa es ${this.#dureza} ` +
      `y tu descripción ${this.#descripcion}`;

    const form = document.querySelector("main form");
    form.insertAdjacentElement("afterend", parrafo);
  }
}

new Formulario();
