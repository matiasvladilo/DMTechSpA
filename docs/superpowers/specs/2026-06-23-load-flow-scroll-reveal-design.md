# Diseño: Flujo de carga, scroll-reveal y formulario funcional (DMTech Landing)

Fecha: 2026-06-23 (form + multi-select añadidos 2026-06-24)
Enfoque de carga elegido: **A — Reveal aditivo, contenido visible por defecto**

Alcance: (1) arreglar el congelamiento de ~5s en la carga, (2) mantener la
aparición al hacer scroll, (3) dejar el formulario funcional vía Netlify Forms,
(4) "Tipo de solución" de selección múltiple.

## Problema

Al recargar la página, queda ~5 segundos mostrando solo el logo/header sobre
fondo oscuro, y luego aparece todo de golpe. No está rota: está esperando.

Causa raíz (dos capas que ocultan contenido hasta que "algo termina"):

1. **`assets/app.js` oculta todo de inmediato.** Es render-blocking en el
   `<head>` y ejecuta `hideRawTemplate()`, que inyecta
   `x-dc{display:none!important}`. Nada dentro de `<x-dc>` se ve hasta que React
   monta y reemplaza el DOM. El logo flotante "DM" no está dentro de `<x-dc>`,
   por eso es lo único visible mientras tanto.

2. **El reveal espera hasta 6 segundos.** El CSS pone
   `html.reveal-on [data-reveal]{opacity:0}` y un IntersectionObserver los
   revela. Pero React reemplaza los nodos *después* del escaneo (y el preview
   puede congelar el reloj de animación), así que el camino rápido falla y el
   contenido recién aparece por el `setTimeout(..., 6000)` de respaldo. Eso es
   el "~5 segundos" observado.

## Principio de la solución

Invertir la lógica: de **"ocultar todo → revelar cuando JS/React terminen"** a
**"mostrar todo por defecto → animar al entrar en viewport"**.

El contenido visible es el estado por defecto. La animación de scroll es un
extra puramente decorativo: si el JS falla, se atrasa o el preview congela el
reloj, igual se ve todo. La animación de aparición al hacer scroll **se
mantiene** — es el comportamiento que el usuario quiere.

## Cambios

### a) `assets/app.js` — quitar el ocultamiento ciego
Neutralizar el efecto de `hideRawTemplate()` para que el contenido del template
sea visible mientras React monta. React igual reemplaza el DOM; la diferencia es
que no hay pantalla de espera. (Sin tocar el formulario ni los bindings de
DCLogic.)

### b) CSS de reveal — visible por defecto
- Hoy: `html.reveal-on [data-reveal]{opacity:0}` (oculto por defecto).
- Cambio: `[data-reveal]` arranca **visible**. Solo los elementos que el JS marca
  explícitamente como "aún no entró en viewport" (ej. clase `.reveal-pending`)
  se atenúan para luego animar.
- Resultado: sin JS = todo visible.
- Mantener `@media (prefers-reduced-motion: reduce)` → todo visible, sin
  transición.

### c) JS de reveal — sin failsafe de 6s
- El IntersectionObserver agrega la animación al entrar al viewport.
- **Eliminar el `setTimeout(..., 6000)`**: ya no hace falta rescatar contenido,
  porque nunca queda oculto.
- Mantener el MutationObserver para nodos que React reemplaza, pero su rol ahora
  es solo "animar al aparecer", no "rescatar de la invisibilidad".
- El contenido sobre el pliegue (above-the-fold) ya es visible al instante; el
  contenido bajo el pliegue se atenúa y anima al scrollear hacia él.

## Casos límite / manejo de errores

- **JS desactivado o React no carga:** contenido 100% visible (estado por
  defecto).
- **Preview congela el reloj de animación:** contenido visible; a lo más no se
  aprecia la transición, pero nada queda oculto.
- **`prefers-reduced-motion`:** todo visible sin transición.
- **GitHub Pages (deploy estático):** React ya está self-hosteado en `assets/`,
  sin CDN externo; sirve igual.

## Verificación

- Recargar en el preview (puerto 4787) y confirmar que hero + tablas aparecen
  **al instante**, no a los 5s.
- Scrollear hacia abajo y confirmar que las tablas Confianza/Enfoque y el
  formulario animan suavemente al entrar en viewport.
- Simular "sin JS" / React lento y confirmar que el contenido sigue visible.

## Formulario funcional (Netlify Forms → correo Hostinger)

Contexto de infra: el sitio se publica en **Netlify**; el dominio se gestiona vía
Hostinger con los nameservers apuntando a Netlify. El correo de avisos llega a
una casilla de Hostinger (requiere registros MX recreados en el DNS de Netlify —
tarea de panel, fuera de este código).

Estado actual: el `submit` de DCLogic solo hace `setState({submitted:true})`. No
envía datos a ningún lado (hay un comentario "Punto de integración con backend").

Netlify detecta formularios parseando el **HTML estático al publicar**, pero este
formulario lo renderiza React en el cliente, así que Netlify no lo "ve". Patrón
estándar para forms renderizados por JS:

1. **Formulario oculto estático** en el HTML, con `name="contacto"`,
   `data-netlify="true"`, honeypot anti-spam, y un `<input>` por cada campo
   (nombre, empresa, cargo, correo, telefono, tipo, proceso, sistema, urgencia,
   mensaje). Esto es lo que Netlify registra al publicar.
2. En el `submit` de DCLogic: en vez de solo `setState`, hacer `fetch` POST a `/`
   con `Content-Type: application/x-www-form-urlencoded`, body =
   `form-name=contacto` + todos los campos codificados. Netlify captura el envío
   y lo reenvía como correo a la casilla de Hostinger (config de panel Netlify).
3. Éxito del `fetch` → mostrar la pantalla "Solicitud recibida" existente.
   Error → mostrar mensaje de error (reusar el bloque `{{ error }}` actual).
4. Mantener la validación actual (nombre + correo obligatorios) antes de enviar.

Limitación de prueba: la captura real de Netlify Forms **solo funciona una vez
publicado en Netlify**. En el preview local (puerto 4787) se puede probar la UX,
la validación y que el `fetch` se dispara, pero no la recepción final.

## "Tipo de solución" → selección múltiple

Hoy es un `<select>` de una sola opción. Cambiar a **chips/casillas** activables
(se puede elegir más de una): botones que se marcan/desmarcan, mobile-friendly,
acorde a la estética (mejor que `<select multiple>` nativo).

- El estado `form.tipo` pasa de string a **lista** (array).
- Al enviar, serializar la lista como string separado por coma para el correo y
  para el campo del formulario oculto de Netlify.
- Mismas opciones actuales (Plataforma web, Sistema interno de gestión,
  Automatización de procesos, Integración de sistemas, Dashboard / reportes,
  Aplicación a medida, Aún no lo tengo claro).
- `reset` debe volver `tipo` a lista vacía.

## Fuera de alcance

- Reescribir el resto del formulario DCLogic a HTML/JS vanilla (enfoque C,
  descartado).
- Configuración de panel de Netlify (notificaciones por correo) y registros MX
  en el DNS — tareas de infra del usuario, no de código.
- Cambios de contenido, tipografía, íconos o copy (ya resueltos previamente).
- El `git init` + push a GitHub queda como tarea aparte, posterior a este fix.
