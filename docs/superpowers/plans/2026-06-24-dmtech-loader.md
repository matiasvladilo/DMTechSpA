# DMTechLoader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un loader de carga animado (4 puntos → líneas → marca DMTECH → fade-out) como overlay nativo en `index.html`, una vez por sesión.

**Architecture:** Overlay `position:fixed` incrustado al inicio de `<body>`, autónomo: su propio `<style>` (clases `.dml-*` + `@keyframes`) y su propio `<script>` IIFE que controla sessionStorage, fin de animación y un failsafe anti-congelamiento. SVG con `viewBox` para los puntos/líneas, `<img>` del PNG de la marca + `<span>` "DMTECH" para la forma final. Sin dependencias, sin tocar `assets/app.js`.

**Tech Stack:** HTML estático, CSS (keyframes, transforms/opacity), SVG, JS vanilla (IIFE + sessionStorage). Verificación vía Claude Preview MCP (server `dmtech-static`, puerto 4787, serverId `ce345c13-1e98-4e25-ad3d-bc5d5cb75d26`).

**Spec:** `docs/superpowers/specs/2026-06-24-dmtech-loader-design.md`

---

## Notas de verificación (aplican a todas las tareas)

- No hay test runner. Cada tarea se verifica en el navegador con el preview.
- Tras CADA edición de `index.html`, sincronizar al directorio del preview:
  ```bash
  cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
  ```
  (El preview no puede leer el Desktop por TCC de macOS; hay que copiar a `/tmp/dmtech_preview/`.)
- Para recargar y poder ver el loader otra vez (es 1 vez por sesión), limpiar el flag antes de recargar:
  ```js
  // preview_eval
  sessionStorage.removeItem('dmtechLoaderSeen'); location.reload(); 'reloaded'
  ```

---

## Estructura de archivos

- **Modificar:** `index.html`
  - Insertar bloque overlay al inicio de `<body>` (después de `<body>`, junto al form oculto de Netlify; el orden no importa porque es `position:fixed`).
  - El bloque incluye: `<div id="dmtech-loader">…`, un `<style id="dml-style">` y un `<script id="dml-script">`.
- **No** se crean archivos nuevos. **No** se toca `assets/app.js`.

Referencias del codebase:
- El `<body>` está en `index.html:8`; el form oculto de Netlify ocupa `index.html:9-22`.
- Logo de la marca: `assets/image-9b49c9cc.png`.
- Fondo del sitio: `#0a0b0d`. Header sticky usa `z-index:50` → el loader usa `9999`.

---

### Task 1: Overlay base + guard de sessionStorage + failsafe

Crea el overlay oscuro a pantalla completa, el script que lo controla, el guard "1 vez por sesión" y el failsafe que lo remueve sí o sí. Sin animación de puntos todavía (placeholder visible: solo fondo). Esto valida el esqueleto y que nunca quede pegado.

**Files:**
- Modify: `index.html` (insertar tras `index.html:8`, justo después de la etiqueta `<body>` y antes del `<form name="contacto" ...>`)

- [ ] **Step 1: Insertar el bloque del overlay (HTML + style + script)**

Insertar EXACTAMENTE este bloque inmediatamente después de la línea `<body>` (es decir, antes de `<form name="contacto" ...>`):

```html
<div id="dmtech-loader" class="dml-root" role="status" aria-label="Cargando DMTECH">
  <div class="dml-stage"></div>
</div>
<style id="dml-style">
#dmtech-loader.dml-root{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:#0a0b0d;opacity:1;transition:opacity .6s ease}
#dmtech-loader.dml-hide{opacity:0;pointer-events:none}
.dml-stage{width:min(60vw,260px);aspect-ratio:1/1;position:relative}
</style>
<script id="dml-script">
(function(){
  var KEY = 'dmtechLoaderSeen';
  var el = document.getElementById('dmtech-loader');
  if(!el) return;
  function remove(){
    if(!el || !el.parentNode) return;
    el.classList.add('dml-hide');
    document.documentElement.style.overflow = '';
    document.body && (document.body.style.overflow = '');
    setTimeout(function(){ if(el && el.parentNode) el.parentNode.removeChild(el); }, 650);
  }
  var seen = false;
  try { seen = !!sessionStorage.getItem(KEY); } catch(e) {}
  if(seen){ if(el.parentNode) el.parentNode.removeChild(el); return; }
  try { sessionStorage.setItem(KEY,'1'); } catch(e) {}
  document.documentElement.style.overflow = 'hidden';
  // Failsafe: pase lo que pase, el overlay se va.
  var FAILSAFE_MS = 2600;
  var killer = setTimeout(remove, FAILSAFE_MS);
  // Punto único de salida programada (las tareas siguientes ajustan EXIT_MS).
  var EXIT_MS = 800;
  setTimeout(function(){ clearTimeout(killer); remove(); }, EXIT_MS);
})();
</script>
```

- [ ] **Step 2: Sincronizar al preview**

Run:
```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```
Expected: copia sin error.

- [ ] **Step 3: Verificar aparición y auto-remoción (preview_eval)**

Recargar limpiando el flag y, tras ~1.5s, confirmar que el overlay ya NO está en el DOM:
```js
// preview_eval #1
sessionStorage.removeItem('dmtechLoaderSeen'); location.reload(); 'reloaded'
```
```js
// preview_eval #2 (ejecutar ~1500ms después)
(function(){ return { exists: !!document.getElementById('dmtech-loader'), overflow: document.documentElement.style.overflow }; })()
```
Expected: `{ exists: false, overflow: "" }` (se removió y se restauró el overflow).

- [ ] **Step 4: Verificar guard de sesión**

```js
// preview_eval (sin limpiar el flag)
location.reload(); 'reloaded'
```
Luego:
```js
(function(){ return { exists: !!document.getElementById('dmtech-loader') }; })()
```
Expected: `{ exists: false }` inmediatamente (porque el flag ya estaba, se remueve al instante).

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat(loader): overlay base con guard de sesión y failsafe"
```

---

### Task 2: Cuatro puntos que aparecen y se deslizan + líneas que se trazan

Reemplaza el `.dml-stage` vacío por un SVG con 4 círculos y líneas. Los puntos aparecen dispersos, se deslizan a sus posiciones y las líneas se dibujan (efecto trazo) formando una figura angular tipo "M".

**Files:**
- Modify: `index.html` (dentro del bloque `#dmtech-loader`: el `.dml-stage` y el `<style id="dml-style">`)

- [ ] **Step 1: Reemplazar el contenido de `.dml-stage` por el SVG**

Reemplazar `<div class="dml-stage"></div>` por:

```html
<div class="dml-stage">
  <svg class="dml-svg" viewBox="0 0 200 200" fill="none" aria-hidden="true">
    <path class="dml-line" d="M40 150 L75 55 L125 55 L160 150" stroke="url(#dmlGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <defs>
      <linearGradient id="dmlGrad" x1="0" y1="0" x2="200" y2="200" gradientUnits="userSpaceOnUse">
        <stop offset="0.2" stop-color="#ffffff"/>
        <stop offset="0.96" stop-color="#9aa2aa"/>
      </linearGradient>
    </defs>
    <circle class="dml-dot dml-dot1" r="6" cx="40"  cy="150" fill="#fff"/>
    <circle class="dml-dot dml-dot2" r="6" cx="75"  cy="55"  fill="#fff"/>
    <circle class="dml-dot dml-dot3" r="6" cx="125" cy="55"  fill="#fff"/>
    <circle class="dml-dot dml-dot4" r="6" cx="160" cy="150" fill="#fff"/>
  </svg>
</div>
```

- [ ] **Step 2: Agregar las reglas y keyframes al `<style id="dml-style">`**

Añadir, antes de `</style>` del bloque `#dml-style`:

```css
.dml-svg{width:100%;height:100%;overflow:visible}
.dml-dot{opacity:0;transform-box:fill-box;transform-origin:center;animation:dmlDotIn .5s cubic-bezier(.16,.84,.44,1) forwards}
.dml-dot1{animation-delay:.05s}
.dml-dot2{animation-delay:.15s}
.dml-dot3{animation-delay:.25s}
.dml-dot4{animation-delay:.35s}
@keyframes dmlDotIn{from{opacity:0;transform:scale(.2) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}
.dml-line{stroke-dasharray:360;stroke-dashoffset:360;opacity:0;animation:dmlDraw .7s cubic-bezier(.16,.84,.44,1) .5s forwards}
@keyframes dmlDraw{0%{opacity:0;stroke-dashoffset:360}15%{opacity:1}100%{opacity:1;stroke-dashoffset:0}}
```

- [ ] **Step 3: Ajustar `EXIT_MS` para que dé tiempo a ver puntos+líneas**

En el `<script id="dml-script">`, cambiar:
```js
  var EXIT_MS = 800;
```
por:
```js
  var EXIT_MS = 1400;
```

- [ ] **Step 4: Sincronizar al preview**

Run:
```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 5: Verificar visualmente (preview_screenshot)**

```js
// preview_eval: relanzar el loader y congelar la captura a mitad de animación
sessionStorage.removeItem('dmtechLoaderSeen'); location.reload(); 'reloaded'
```
Tomar `preview_screenshot` ~700ms después de recargar.
Expected: se ven 4 puntos blancos y una línea angular (en proceso de trazo) sobre fondo oscuro. Ajustar coordenadas/`stroke-width` si se ve tosco.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat(loader): 4 puntos animados y trazado de líneas SVG"
```

---

### Task 3: Crossfade a la marca real (PNG) + wordmark "DMTECH"

Sobre el esqueleto de líneas, aparece el logo real y el texto "DMTECH", con el mismo layout del header.

**Files:**
- Modify: `index.html` (dentro de `.dml-stage` y `<style id="dml-style">`)

- [ ] **Step 1: Agregar la capa de marca dentro de `.dml-stage`**

Justo después del `</svg>` (todavía dentro de `.dml-stage`), agregar:

```html
<div class="dml-brand">
  <img class="dml-mark" src="assets/image-9b49c9cc.png" alt="DMTECH" decoding="async" fetchpriority="high">
  <span class="dml-word">DMTECH</span>
</div>
```

- [ ] **Step 2: Agregar estilos de la marca al `<style id="dml-style">`**

Añadir antes de `</style>`:

```css
.dml-brand{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;opacity:0;animation:dmlBrandIn .6s ease 1.15s forwards}
.dml-mark{height:38%;width:auto;filter:drop-shadow(0 2px 10px rgba(0,0,0,.5))}
.dml-word{font-family:'Hanken Grotesk',system-ui,sans-serif;font-weight:600;font-size:clamp(16px,4.5vw,22px);letter-spacing:.34em;padding-left:.34em;color:#f3f5f7;transform:translateY(6px);opacity:0;animation:dmlWordIn .5s cubic-bezier(.16,.84,.44,1) 1.35s forwards}
@keyframes dmlBrandIn{from{opacity:0}to{opacity:1}}
@keyframes dmlWordIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.dml-svg{transition:opacity .5s ease}
.dml-fade-skeleton .dml-svg{opacity:0}
```

- [ ] **Step 3: Atenuar el esqueleto SVG cuando entra la marca (script)**

En `<script id="dml-script">`, justo antes de la línea `var FAILSAFE_MS = 2600;`, agregar:
```js
  setTimeout(function(){ el.classList.add('dml-fade-skeleton'); }, 1300);
```

- [ ] **Step 4: Ajustar `EXIT_MS` para incluir la marca**

Cambiar:
```js
  var EXIT_MS = 1400;
```
por:
```js
  var EXIT_MS = 2100;
```

- [ ] **Step 5: Sincronizar al preview**

Run:
```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 6: Verificar (preview_screenshot)**

```js
sessionStorage.removeItem('dmtechLoaderSeen'); location.reload(); 'reloaded'
```
Tomar `preview_screenshot` ~1700ms después.
Expected: se ve la marca PNG centrada con "DMTECH" debajo, y las líneas SVG ya atenuadas. Confirmar layout limpio.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat(loader): crossfade a marca real + wordmark DMTECH"
```

---

### Task 4: Salida suave + reduced-motion + auto-hide sin JS + responsive

Garantiza el fade-out final (ya cableado vía `remove()`), la accesibilidad y que sin JS el overlay también desaparezca por CSS.

**Files:**
- Modify: `index.html` (`<style id="dml-style">`)

- [ ] **Step 1: Auto-hide por CSS (cubre JS desactivado)**

Añadir antes de `</style>` del `#dml-style`:

```css
@keyframes dmlAutoHide{0%,92%{opacity:1;visibility:visible}100%{opacity:0;visibility:hidden}}
#dmtech-loader.dml-root{animation:dmlAutoHide 3s ease forwards}
```

Nota: con JS activo, `remove()` quita el nodo antes (≈2.1s); el `dmlAutoHide` (3s) solo actúa como respaldo si el JS no corre.

- [ ] **Step 2: Soporte `prefers-reduced-motion`**

Añadir antes de `</style>`:

```css
@media (prefers-reduced-motion:reduce){
  .dml-dot,.dml-line,.dml-brand,.dml-word{animation:none!important;opacity:1!important;transform:none!important;stroke-dashoffset:0!important}
  #dmtech-loader.dml-root{animation:none!important}
}
```

Y en `<script id="dml-script">`, reducir el tiempo en caso de reduced-motion. Reemplazar:
```js
  var EXIT_MS = 2100;
```
por:
```js
  var reduce = false;
  try { reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch(e) {}
  var EXIT_MS = reduce ? 700 : 2100;
```

- [ ] **Step 3: Sincronizar al preview**

Run:
```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 4: Verificar fade-out y remoción**

```js
sessionStorage.removeItem('dmtechLoaderSeen'); location.reload(); 'reloaded'
```
```js
// ~2600ms después
(function(){ return { exists: !!document.getElementById('dmtech-loader'), bodyOverflow: document.documentElement.style.overflow }; })()
```
Expected: `{ exists:false, bodyOverflow:"" }`.

- [ ] **Step 5: Verificar reduced-motion (preview_resize colorScheme no aplica; usar emulación)**

Con `preview_eval` no se puede forzar la media query directamente; verificar al menos que el camino normal funciona y revisar el CSS de reduced-motion a ojo. Si el entorno de preview permite emular reduced-motion, confirmar que aparece la marca sin movimiento y se va a ~700ms.

- [ ] **Step 6: Verificar responsive (preview_resize)**

`preview_resize` preset `mobile` (375x812), recargar limpiando flag, `preview_screenshot`.
Expected: loader centrado, marca + "DMTECH" legibles, sin desbordes.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "feat(loader): salida suave, reduced-motion, auto-hide sin JS y responsive"
```

---

### Task 5: Verificación integral + versión de cache-busting

Confirmar la experiencia completa y forzar que el navegador no sirva el `index.html` viejo en producción.

**Files:**
- Modify: `index.html` (solo si se decide bump de versión del query del script, ver paso 1)

- [ ] **Step 1: (Opcional) cache-busting de app.js si cambió**

`index.html:5` referencia `assets/app.js?v=2`. El loader NO toca app.js, así que NO es necesario cambiarlo. No modificar salvo que se observe cache stale. (Sin acción por defecto.)

- [ ] **Step 2: Recorrido completo en preview (desktop)**

`preview_resize` preset `desktop`. Luego:
```js
sessionStorage.removeItem('dmtechLoaderSeen'); location.reload(); 'reloaded'
```
Observar la secuencia completa con 2-3 `preview_screenshot` a ~600ms, ~1200ms, ~1800ms.
Expected: puntos → líneas → marca+wordmark → fade. Sin parpadeos del contenido detrás.

- [ ] **Step 3: Confirmar que el contenido queda usable tras el loader**

```js
// ~2600ms tras recargar
(function(){
  var loader = document.getElementById('dmtech-loader');
  var hero = document.querySelector('#top h1');
  return { loaderGone: !loader, heroVisible: !!hero && getComputedStyle(hero).opacity === '1', overflow: document.documentElement.style.overflow };
})()
```
Expected: `{ loaderGone:true, heroVisible:true, overflow:"" }`.

- [ ] **Step 4: Confirmar 1-vez-por-sesión en navegación real**

Recargar SIN limpiar el flag:
```js
location.reload(); 'reloaded'
```
```js
(function(){ return { exists: !!document.getElementById('dmtech-loader') }; })()
```
Expected: `{ exists:false }`.

- [ ] **Step 5: Commit final (si hubo cambios) y resumen**

```bash
git add index.html
git commit -m "test(loader): verificación integral del flujo de carga"
```
(Si no hubo cambios de código en esta tarea, omitir el commit.)

---

## Self-Review (cobertura de la spec)

- Overlay nativo en index.html → Task 1. ✓
- 4 puntos + deslizamiento + líneas → Task 2. ✓
- Crossfade a marca real + "DMTECH" → Task 3. ✓
- Fade-out + remoción del DOM + restaurar overflow → Task 1 (`remove()`) + Task 4. ✓
- 1 vez por sesión (sessionStorage) → Task 1. ✓
- Failsafe anti-congelamiento (~2.6s) → Task 1. ✓
- prefers-reduced-motion → Task 4. ✓
- Auto-hide sin JS (CSS) → Task 4. ✓
- Responsive (viewBox + clamp) → Task 2/3 (SVG, clamp en wordmark) + verificación Task 4/5. ✓
- Rendimiento (solo opacity/transform/stroke-dashoffset) → respetado en Task 2/3/4. ✓
- No tocar app.js / form / reveal → respetado (solo se inserta bloque aislado). ✓

Sin placeholders. Nombres consistentes (`#dmtech-loader`, `.dml-*`, `KEY='dmtechLoaderSeen'`, `EXIT_MS`, `FAILSAFE_MS`, `remove()`) en todas las tareas.
