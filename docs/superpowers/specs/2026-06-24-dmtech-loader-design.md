# Diseño: DMTechLoader — loader animado de carga (DMTech Landing)

Fecha: 2026-06-24

## Objetivo

Mostrar, al cargar la página, una animación de marca: 4 puntos que se deslizan,
se conectan con líneas suaves y convergen formando la marca DMTECH; luego el
overlay desaparece con un fade suave. Debe sentirse tecnológico, limpio y
moderno, mantener buen rendimiento y ser responsive.

## Contexto y decisión de arquitectura

El sitio NO es un proyecto Vite/React con archivos `.jsx`. Es un `index.html`
estático con un runtime tipo React (DCLogic + React UMD self-hosteado en
`assets/`). Un loader debe verse **antes** de que React monte (su propósito es
tapar ese momento de carga), por lo tanto NO puede ser un componente React que
recién aparece tras el montaje.

**Decisión (aprobada por el usuario):** el loader es un **overlay nativo
incrustado en `index.html`** — SVG + CSS + un poco de JS vanilla. Aparece al
instante, se quita solo con fade cuando la página está lista. Encapsulado bajo
`#dmtech-loader` con clases prefijadas `dml-` y su propio `<style>`/`<script>`,
de modo que sea fácil de quitar o reutilizar (cumple "componente reutilizable"
en espíritu, sin depender de un framework).

Se descartó Lottie (no existe JSON de animación; sumaría ~250KB de librería) y
Canvas/partículas (más código, difícil calzar con el logo exacto). SVG+CSS es
suficiente y sin dependencias, coherente con el sitio (React ya self-hosteado,
sin CDN externo).

## Activos

- Marca/logo: `assets/image-9b49c9cc.png` (monograma "M/DM" geométrico, el mismo
  del header). No hay SVG del logo; la marca final del loader usa este PNG.
- Tipografía del wordmark "DMTECH": misma del header (`Hanken Grotesk`, peso 600,
  `letter-spacing` amplio), ya cargada en la página.

## Coreografía (duración total objetivo ~2.0–2.4s)

1. **Overlay** a pantalla completa, `position:fixed`, fondo `#0a0b0d` (igual al
   fondo del sitio), `z-index` muy alto (sobre el header sticky que usa z-index
   50; el loader usa 9999).
2. **Aparición de 4 puntos** (`<circle>` SVG) en posiciones dispersas, con
   `opacity` 0→1 escalonada.
3. **Deslizamiento**: los 4 puntos se mueven suavemente hacia los vértices clave
   de la marca "M" (transform/atributos `cx,cy` animados con easing
   `cubic-bezier(.16,.84,.44,1)`).
4. **Trazo de líneas**: líneas/paths SVG entre los puntos se dibujan con efecto
   de trazo (`stroke-dasharray`/`stroke-dashoffset` 100%→0) formando la silueta
   angular de la marca.
5. **Crossfade al logo real**: la marca PNG (`image-9b49c9cc.png`) aparece con
   `opacity` 0→1 encima del esqueleto de líneas; el texto **"DMTECH"** entra al
   lado con un fade/slide corto. Layout marca+texto igual al del header.
6. **Salida**: el overlay completo hace `opacity` 1→0 (con un leve `scale` o
   `translateY` opcional) y se **elimina del DOM** (`remove()`).

## Comportamiento y control

- **Frecuencia: 1 vez por sesión.** Al iniciar, si
  `sessionStorage.getItem('dmtechLoaderSeen')` existe, NO se muestra el loader
  (se remueve de inmediato). Al terminar la animación se hace
  `sessionStorage.setItem('dmtechLoaderSeen','1')`.
- **Nunca congela (failsafe):** un `setTimeout` máximo (~2.6s) elimina el overlay
  sí o sí, aunque algo falle. El contenido del sitio ya es visible por debajo
  (arquitectura visible-por-defecto existente), así que el loader solo decora la
  entrada; si fallara, nada queda oculto de forma permanente.
- **Disparo de salida:** la salida ocurre cuando termina la secuencia animada
  (timeline por CSS/JS), acotada por el failsafe. No depende de eventos de React.
- **No bloquea scroll permanentemente:** mientras el overlay está visible puede
  fijarse `overflow:hidden` en `body`; al remover el overlay se restablece.

## Accesibilidad y rendimiento

- **`prefers-reduced-motion: reduce`**: sin movimiento — se muestra directamente
  la marca + "DMTECH" estáticos con un fade corto (o se omite el loader y se
  marca como visto). Sin deslizamientos ni trazos.
- Animar solo `opacity` y `transform` (y `stroke-dashoffset`), propiedades
  baratas para el compositor; evitar layout/reflow. Usar `will-change` con
  mesura.
- SVG con `viewBox` para escalar nítido; tamaños con `clamp` para responsive.
- El bloque del loader va temprano en `<body>` para pintar cuanto antes.

## Estructura de archivos

- Modificar: `index.html`
  - Bloque `#dmtech-loader` (HTML del overlay: SVG con 4 `<circle>`, líneas/paths,
    `<img>` de la marca, `<span>` "DMTECH"), insertado al inicio de `<body>`.
  - `<style>` propio con las reglas `.dml-*` y los `@keyframes` del loader, más la
    regla `@media (prefers-reduced-motion:reduce)`.
  - `<script>` propio (IIFE) que: chequea `sessionStorage`; si ya se vio, remueve
    el overlay al instante; si no, orquesta el fin de la animación (fade-out +
    `remove()` + set `sessionStorage`) y arma el failsafe de ~2.6s.
- No se crean archivos nuevos ni se toca `assets/app.js`.

## Casos límite

- **sessionStorage no disponible** (modo privado estricto): el `try/catch` trata
  "no disponible" como "no visto" pero igual respeta el failsafe; en el peor caso
  el loader se muestra y se remueve normalmente.
- **JS desactivado:** el overlay quedaría visible (cubre el contenido). Mitigación:
  el overlay se inserta con una clase que, sin JS, igual permite ver el contenido
  — alternativa simple: el failsafe es JS, así que con JS off se acepta que no hay
  loader animado. Para no tapar el contenido sin JS, el overlay puede incluir un
  `<noscript>`-style: se define que el overlay base tenga una animación CSS de
  auto-fade-out (p. ej. `animation: dmlAutoHide` que termina en
  `opacity:0;visibility:hidden`) de modo que aun sin JS desaparezca por CSS.
- **Logo PNG lento:** el `<img>` de la marca se precarga; si no cargó al momento
  del crossfade, el wordmark y las líneas igual se muestran y el failsafe cierra.

## Verificación

- Cargar en el preview (puerto 4787): ver la secuencia puntos→líneas→logo→fade y
  que el overlay se elimina del DOM.
- Recargar en la misma sesión: el loader NO reaparece (sessionStorage).
- Limpiar sessionStorage y recargar: reaparece.
- Emular `prefers-reduced-motion`: sin movimiento, solo fade del logo.
- Resize móvil/desktop: el loader escala y queda centrado.
- Confirmar que tras el loader el contenido y el scroll funcionan normal
  (`body overflow` restablecido).

## Fuera de alcance

- Convertir el sitio a Vite/React real.
- Crear un archivo Lottie JSON.
- Cambios al contenido, formulario, o al flujo de reveal/scroll existente.
- Animar el logo "letra por letra" del wordmark (basta fade/slide del conjunto).
