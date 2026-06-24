# Flujo de carga, scroll-reveal y formulario funcional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar el congelamiento de ~5s al cargar, mantener la aparición al hacer scroll, dejar el formulario funcional vía Netlify Forms y convertir "Tipo de solución" en selección múltiple.

**Architecture:** Página estática con runtime DCLogic (custom element `<x-dc>` + React UMD self-hosteado, renderizado en cliente por `assets/app.js`). El contenido se hace visible por defecto; la animación de scroll es aditiva (nunca deja algo oculto). El formulario React envía por `fetch` POST a Netlify Forms, que reenvía como correo a la casilla de Hostinger. No hay base de datos ni framework de tests automatizados: la verificación es manual en el preview.

**Tech Stack:** HTML + CSS inline, DCLogic/React 18 (UMD self-hosteado en `assets/`), Netlify Forms, IntersectionObserver/MutationObserver.

---

## Notas de entorno (leer antes de empezar)

- **No hay repo git** en `/Users/matiasvladilo/Desktop/MASTER/DMTech`. Los pasos "Commit" de la plantilla estándar se reemplazan por **"Sincronizar al preview"**. El `git init` + push a GitHub es una tarea aparte, posterior a este plan.
- **El preview que ve el usuario corre desde `/tmp/dmtech_preview/`** (puerto 4787, según `.claude/launch.json`). El sandbox de preview no puede leer el Desktop por TCC. Por eso, **después de cada edición de `index.html` o `assets/app.js` hay que copiar el archivo a `/tmp/dmtech_preview/`**.
- Comando de sync (reutilizado en varias tareas):
  ```bash
  cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
  cp /Users/matiasvladilo/Desktop/MASTER/DMTech/assets/app.js /tmp/dmtech_preview/assets/app.js
  ```
- **Verificación = navegador.** Recargar `http://127.0.0.1:4787/` y observar. Donde se pueda, usar las herramientas del MCP de preview (screenshot / console logs) para confirmar.
- **No tocar** el contenido, tipografía, íconos ni copy ya resueltos.

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `assets/app.js` | Runtime DCLogic. Añadir red de seguridad que des-oculta `<x-dc>` si React no arranca. | Modificar (~línea 1482, 1562) |
| `index.html` (CSS `<style>` ~líneas 312-325) | Reveal visible-por-defecto + estilos de chips | Modificar |
| `index.html` (form ~líneas 687-699) | "Tipo de solución" como chips multi-select | Modificar |
| `index.html` (antes de `</body>`, fuera de `<x-dc>`) | Formulario oculto estático para detección de Netlify | Crear |
| `index.html` (script DCLogic ~líneas 784-835) | Estado `tipo` como lista, handlers de chips, `submit` con `fetch` a Netlify | Modificar |
| `index.html` (script reveal ~líneas 838-868) | Reveal aditivo con `reveal-pending`, sin failsafe de 6s | Modificar |

---

## Task 1: Red de seguridad para el des-ocultado (app.js)

**Por qué:** `hideRawTemplate()` inyecta `x-dc{display:none!important}` para evitar el parpadeo del template crudo (`{{ year }}` etc.) hasta que React monta (~22ms, imperceptible). Lo mantenemos, pero añadimos un timeout defensivo: si React nunca arranca, el contenido no debe quedar oculto para siempre. La cura principal del freeze está en Tasks 2-3; esto es solo seguro.

**Files:**
- Modify: `assets/app.js:1482-1486` (función `hideRawTemplate`)
- Modify: `assets/app.js:1562` (llamada a `hideRawTemplate`)

- [ ] **Step 1: Reemplazar `hideRawTemplate` para que guarde una referencia al `<style>` y agregue un timeout de des-ocultado**

Reemplazar exactamente este bloque (líneas ~1482-1486):

```js
  function hideRawTemplate() {
    const s = document.createElement("style");
    s.textContent = "x-dc{display:none!important}";
    document.head.appendChild(s);
  }
```

por:

```js
  function hideRawTemplate() {
    const s = document.createElement("style");
    s.textContent = "x-dc{display:none!important}";
    document.head.appendChild(s);
    // Red de seguridad: si React no arrancó en 2.5s, des-ocultar el template
    // para que el contenido nunca quede invisible de forma permanente.
    setTimeout(() => { try { s.remove(); } catch {} }, 2500);
  }
```

- [ ] **Step 2: Verificar que el resto del flujo no rompe**

Confirmar visualmente que la línea 1562 sigue siendo `hideRawTemplate();` (sin cambios) y que `loadReactUmd().then(init)` queda intacto. No se requiere otra edición aquí.

- [ ] **Step 3: Sincronizar al preview**

```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/assets/app.js /tmp/dmtech_preview/assets/app.js
```

- [ ] **Step 4: Verificar en navegador**

Recargar `http://127.0.0.1:4787/`. Esperado: la página sigue cargando normal (React monta y muestra contenido). En la consola no debe haber errores nuevos de `[dc]`. (El efecto del timeout solo se nota si React falla; no debe alterar el caso normal.)

---

## Task 2: Reveal visible-por-defecto (CSS)

**Por qué:** Hoy `html.reveal-on [data-reveal]{opacity:0}` oculta TODO el contenido revelable hasta que el JS lo muestre. Si el JS se atrasa (o el failsafe de 6s), queda congelado. Invertimos: el contenido es visible por defecto; solo lo que el JS marca como `reveal-pending` (porque aún no entra al viewport) se atenúa para luego animar.

**Files:**
- Modify: `index.html:316-324` (bloque de reglas `html.reveal-on [data-reveal]`)

- [ ] **Step 1: Reemplazar el bloque de reveal CSS**

Reemplazar exactamente estas líneas (316-324):

```css
html.reveal-on [data-reveal]{opacity:0;transform:translateY(26px);transition:opacity .75s cubic-bezier(.16,.84,.44,1),transform .75s cubic-bezier(.16,.84,.44,1);will-change:opacity,transform}
html.reveal-on [data-reveal].is-visible{opacity:1;transform:none}
html.reveal-on [data-reveal][data-delay="0.08s"]{transition-delay:.08s}
html.reveal-on [data-reveal][data-delay="0.09s"]{transition-delay:.09s}
html.reveal-on [data-reveal][data-delay="0.16s"]{transition-delay:.16s}
html.reveal-on [data-reveal][data-delay="0.18s"]{transition-delay:.18s}
html.reveal-on [data-reveal][data-delay="0.24s"]{transition-delay:.24s}
html.reveal-on [data-reveal][data-delay="0.27s"]{transition-delay:.27s}
@media (prefers-reduced-motion:reduce){html.reveal-on [data-reveal]{opacity:1!important;transform:none!important;transition:none!important}}
```

por:

```css
[data-reveal]{transition:opacity .75s cubic-bezier(.16,.84,.44,1),transform .75s cubic-bezier(.16,.84,.44,1);will-change:opacity,transform}
[data-reveal].reveal-pending{opacity:0;transform:translateY(26px)}
[data-reveal].reveal-pending[data-delay="0.08s"]{transition-delay:.08s}
[data-reveal].reveal-pending[data-delay="0.09s"]{transition-delay:.09s}
[data-reveal].reveal-pending[data-delay="0.16s"]{transition-delay:.16s}
[data-reveal].reveal-pending[data-delay="0.18s"]{transition-delay:.18s}
[data-reveal].reveal-pending[data-delay="0.24s"]{transition-delay:.24s}
[data-reveal].reveal-pending[data-delay="0.27s"]{transition-delay:.27s}
@media (prefers-reduced-motion:reduce){[data-reveal]{opacity:1!important;transform:none!important;transition:none!important}}
```

Clave del cambio: sin `reveal-pending`, `[data-reveal]` queda totalmente visible (opacity 1, sin transform). El JS solo añade `reveal-pending` a lo que está bajo el pliegue.

- [ ] **Step 2: Sincronizar al preview** (se hará junto con Task 3, que toca el mismo archivo).

No verificar todavía: el JS de reveal aún usa `is-visible`/`reveal-on`. Se valida al terminar Task 3.

---

## Task 3: Reveal aditivo sin failsafe (JS)

**Por qué:** El JS actual agrega `reveal-on` (que oculta todo) y revela con `is-visible`, con un `setTimeout(...,6000)` de rescate — el causante del "~5s". Lo reescribimos: marcar como `reveal-pending` solo lo que está fuera del viewport (antes del paint, vía el callback del observer), y quitarlo al entrar. Sin failsafe.

**Files:**
- Modify: `index.html:839-868` (IIFE de reveal completa)

- [ ] **Step 1: Reemplazar la IIFE de reveal**

Reemplazar todo el bloque desde `(function(){` (línea 839) hasta su cierre `})();` por:

```js
(function(){
  var io = ('IntersectionObserver' in window) ? new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){ e.target.classList.remove('reveal-pending'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }) : null;

  function arm(el){
    if(el.dataset.rbDone) return;
    el.dataset.rbDone = '1';
    if(!io) return; // sin IO: dejar visible (estado por defecto)
    var r = el.getBoundingClientRect();
    if(r.top < window.innerHeight && r.bottom > 0){
      return; // ya en viewport: visible por defecto, no atenuar
    }
    el.classList.add('reveal-pending'); // bajo el pliegue: atenuar y observar
    io.observe(el);
  }

  function scan(){
    document.querySelectorAll('[data-reveal]').forEach(arm);
  }

  function boot(){
    scan();
    new MutationObserver(scan).observe(document.body, { childList:true, subtree:true });
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
```

Notas: ya no se añade `reveal-on` al `<html>`. El contenido en viewport queda visible sin tocarlo. Lo de abajo se atenúa y aparece al scrollear. Si el JS muere, nada queda con `reveal-pending` → todo visible.

- [ ] **Step 2: Sincronizar al preview**

```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 3: Verificar el fix del freeze**

Recargar `http://127.0.0.1:4787/`. Esperado:
- El hero y el header aparecen **al instante** (no a los 5s).
- Al hacer scroll, las tablas Confianza/Enfoque y la sección Solicitud **aparecen suavemente** al entrar al viewport.
- En consola, sin errores.

Si el contenido sigue tardando, revisar que Task 2 (CSS) se aplicó y que no quedó ningún `reveal-on`/`is-visible` residual.

---

## Task 4: "Tipo de solución" como chips multi-select

**Por qué:** Hoy es un `<select>` de una sola opción. El usuario quiere elegir más de una. Usamos chips activables (mejor UX que `<select multiple>`). El estado `form.tipo` pasa de string a lista.

**Files:**
- Modify: `index.html` (CSS `<style>`, añadir estilos de chip cerca del bloque de reveal, ~línea 324)
- Modify: `index.html:687-699` (el `<label>` con el `<select value="{{ form.tipo }}">`)
- Modify: `index.html:786` (estado inicial `tipo:''` → `tipo:[]`)
- Modify: `index.html:799-833` (`renderVals`: handlers y clases de chips; `reset`)

- [ ] **Step 1: Añadir CSS de los chips**

Después de la línea 324 (cierre del media query de reveal), añadir dentro del mismo `<style>`:

```css
.dm-chips{display:flex;flex-wrap:wrap;gap:10px}
.dm-chip{cursor:pointer;font-size:13.5px;font-weight:400;color:#c4c9cf;background:rgba(255,255,255,.022);border:1px solid rgba(255,255,255,.1);border-radius:999px;padding:9px 15px;transition:border-color .2s,background .2s,color .2s}
.dm-chip:hover{border-color:rgba(255,255,255,.32)}
.dm-chip-on{color:#0a0c0f;background:linear-gradient(135deg,#f5f6f8,#c6ccd2);border-color:transparent;font-weight:600}
```

- [ ] **Step 2: Reemplazar el `<label>` del `<select>` de tipo por chips**

Reemplazar el bloque completo (líneas 687-699), desde `<label style="display:flex;flex-direction:column;gap:9px;">` que contiene el `<span>Tipo de solución</span>` y su `<select ...>...</select>`, por:

```html
          <label style="display:flex;flex-direction:column;gap:9px;grid-column:1/-1;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:#828a92;">Tipo de solución <span style="text-transform:none;letter-spacing:0;color:#6b727a;">(puedes elegir varias)</span></span>
            <div class="dm-chips">
              <button type="button" class="{{ tipoCls.c0 }}" onclick="{{ tipoHandlers.c0 }}">Plataforma web</button>
              <button type="button" class="{{ tipoCls.c1 }}" onclick="{{ tipoHandlers.c1 }}">Sistema interno de gestión</button>
              <button type="button" class="{{ tipoCls.c2 }}" onclick="{{ tipoHandlers.c2 }}">Automatización de procesos</button>
              <button type="button" class="{{ tipoCls.c3 }}" onclick="{{ tipoHandlers.c3 }}">Integración de sistemas</button>
              <button type="button" class="{{ tipoCls.c4 }}" onclick="{{ tipoHandlers.c4 }}">Dashboard / reportes</button>
              <button type="button" class="{{ tipoCls.c5 }}" onclick="{{ tipoHandlers.c5 }}">Aplicación a medida</button>
              <button type="button" class="{{ tipoCls.c6 }}" onclick="{{ tipoHandlers.c6 }}">Aún no lo tengo claro</button>
            </div>
          </label>
```

(El `grid-column:1/-1` hace que los chips ocupen el ancho completo de la grilla, ya que son más anchos que un input.)

- [ ] **Step 3: Cambiar el estado inicial de `tipo` a lista**

En la línea 786, dentro de `state = { form: {...} }`, cambiar `tipo:''` por `tipo:[]`:

```js
    form: { nombre:'', empresa:'', cargo:'', correo:'', telefono:'', tipo:[], proceso:'', sistema:'', urgencia:'', mensaje:'' },
```

- [ ] **Step 4: Generar handlers y clases de chips en `renderVals`**

En `renderVals()`, justo después de `const handlers = {};` y el `Object.keys(f).forEach(...)` existente (línea ~807), añadir:

```js
    const tipoOptions = ['Plataforma web','Sistema interno de gestión','Automatización de procesos','Integración de sistemas','Dashboard / reportes','Aplicación a medida','Aún no lo tengo claro'];
    const tipoHandlers = {};
    const tipoCls = {};
    tipoOptions.forEach((opt,i)=>{
      const active = this.state.form.tipo.indexOf(opt) !== -1;
      tipoCls['c'+i] = 'dm-chip' + (active ? ' dm-chip-on' : '');
      tipoHandlers['c'+i] = ()=> this.setState(s=>{
        const cur = s.form.tipo;
        const next = cur.indexOf(opt) !== -1 ? cur.filter(t=>t!==opt) : cur.concat([opt]);
        return { form: { ...s.form, tipo: next } };
      });
    });
```

Importante: el `handlers` autogenerado del bloque existente crea un handler `handlers.tipo` que asume `e.target.value` (de input). Como `tipo` ya no es un input, ese handler queda sin uso (los chips usan `tipoHandlers`). No es necesario eliminarlo, pero NO debe usarse en el template.

- [ ] **Step 5: Exponer `tipoHandlers` y `tipoCls` en el return de `renderVals`**

En el `return { ... }` (línea ~824), añadir las dos claves:

```js
    return {
      form: f,
      handlers,
      tipoHandlers,
      tipoCls,
      submit,
      reset,
      submitted: this.state.submitted,
      notSubmitted: !this.state.submitted,
      error: this.state.error,
      year: new Date().getFullYear()
    };
```

- [ ] **Step 6: Actualizar `reset` para vaciar la lista**

En `reset` (línea ~819), el objeto `form` debe usar `tipo:[]`:

```js
    const reset = ()=> this.setState({
      submitted: false,
      error: '',
      form: { nombre:'', empresa:'', cargo:'', correo:'', telefono:'', tipo:[], proceso:'', sistema:'', urgencia:'', mensaje:'' }
    });
```

- [ ] **Step 7: Sincronizar al preview**

```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 8: Verificar los chips**

Recargar `http://127.0.0.1:4787/` y bajar a "Solicitud". Esperado:
- Se ven 7 chips bajo "Tipo de solución".
- Al hacer clic en uno se marca (fondo claro); al hacer clic de nuevo se desmarca.
- Se pueden marcar **varios** a la vez.
- Sin errores en consola.

---

## Task 5: Formulario oculto estático para Netlify

**Por qué:** Netlify detecta formularios parseando el HTML al publicar. El form real lo renderiza React (invisible para Netlify). Un form oculto estático con todos los campos es lo que Netlify registra.

**Files:**
- Modify: `index.html` (añadir el form justo después de `<body>`, línea 8, FUERA de `<x-dc>`)

- [ ] **Step 1: Insertar el formulario oculto**

Justo después de `<body>` (línea 8), antes de `<x-dc>`, añadir:

```html
<form name="contacto" netlify netlify-honeypot="bot-field" hidden>
  <input type="text" name="nombre">
  <input type="text" name="empresa">
  <input type="text" name="cargo">
  <input type="email" name="correo">
  <input type="text" name="telefono">
  <input type="text" name="tipo">
  <textarea name="proceso"></textarea>
  <input type="text" name="sistema">
  <input type="text" name="urgencia">
  <textarea name="mensaje"></textarea>
  <input type="text" name="bot-field">
</form>
```

Nota: este form va FUERA de `<x-dc>` para que React no lo elimine al renderizar y para que quede en el HTML estático que Netlify parsea al publicar.

- [ ] **Step 2: Sincronizar al preview**

```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 3: Verificar que no afecta la vista**

Recargar `http://127.0.0.1:4787/`. Esperado: la página se ve idéntica (el form está `hidden`). Sin errores en consola. La detección real de Netlify solo ocurre al publicar; aquí solo confirmamos que no rompe nada.

---

## Task 6: Enviar el formulario a Netlify (fetch en `submit`)

**Por qué:** Hoy `submit` solo hace `setState({submitted:true})`. Debe enviar los datos a Netlify (POST url-encoded a `/` con `form-name=contacto`), serializando `tipo` (lista) como string separado por coma.

**Files:**
- Modify: `index.html:808-818` (función `submit` dentro de `renderVals`)

- [ ] **Step 1: Reemplazar la función `submit`**

Reemplazar el bloque (líneas 808-818):

```js
    const submit = (e)=>{
      e.preventDefault();
      const cur = this.state.form;
      if(!cur.nombre.trim() || !cur.correo.trim()){
        this.setState({ error: 'Por favor completa al menos tu nombre y tu correo.' });
        return;
      }
      // Punto de integración con backend / email / base de datos:
      // enviar `this.state.form` a tu endpoint aquí.
      this.setState({ submitted: true, error: '' });
    };
```

por:

```js
    const submit = (e)=>{
      e.preventDefault();
      const cur = this.state.form;
      if(!cur.nombre.trim() || !cur.correo.trim()){
        this.setState({ error: 'Por favor completa al menos tu nombre y tu correo.' });
        return;
      }
      this.setState({ error: 'Enviando…' });
      const payload = {
        'form-name': 'contacto',
        nombre: cur.nombre,
        empresa: cur.empresa,
        cargo: cur.cargo,
        correo: cur.correo,
        telefono: cur.telefono,
        tipo: cur.tipo.join(', '),
        proceso: cur.proceso,
        sistema: cur.sistema,
        urgencia: cur.urgencia,
        mensaje: cur.mensaje
      };
      const body = Object.keys(payload).map(function(k){
        return encodeURIComponent(k) + '=' + encodeURIComponent(payload[k]);
      }).join('&');
      fetch('/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body
      }).then((r)=>{
        if(!r.ok) throw new Error('bad status ' + r.status);
        this.setState({ submitted: true, error: '' });
      }).catch(()=>{
        this.setState({ error: 'No pudimos enviar tu solicitud. Inténtalo de nuevo o escríbenos a contacto@dmtech.com.' });
      });
    };
```

- [ ] **Step 2: Sincronizar al preview**

```bash
cp /Users/matiasvladilo/Desktop/MASTER/DMTech/index.html /tmp/dmtech_preview/index.html
```

- [ ] **Step 3: Verificar la UX de envío (local)**

Recargar `http://127.0.0.1:4787/`, ir a "Solicitud", llenar Nombre y Correo, marcar 1-2 chips, y enviar. Esperado **en local**:
- La validación funciona: sin nombre o correo, aparece el mensaje rojo y NO se envía.
- Con datos válidos, se dispara el `fetch`. **En el preview local el servidor (`SimpleHTTPRequestHandler`) no acepta POST**, así que el `fetch` fallará y se mostrará el mensaje de error. **Esto es esperado en local** y confirma que el camino de error funciona.
- La pantalla "Solicitud recibida" (camino de éxito) solo se podrá ver una vez publicado en Netlify, o se puede confirmar momentáneamente forzando `r.ok` en pruebas — no dejar ese cambio.

- [ ] **Step 4: Confirmar nombres de campo coinciden con el form oculto**

Revisar que cada `name` del form oculto (Task 5) tiene su clave correspondiente en `payload` (nombre, empresa, cargo, correo, telefono, tipo, proceso, sistema, urgencia, mensaje). El honeypot `bot-field` se deja vacío (no se envía en el payload, lo cual está bien).

---

## Task 7: Verificación integral

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Recarga limpia y flujo completo**

En `http://127.0.0.1:4787/` (recarga forzada con caché desactivada):
- [ ] El contenido aparece al instante, sin pantalla congelada de ~5s.
- [ ] Al hacer scroll, las secciones aparecen suavemente (Confianza, Enfoque, Diferencial, Solicitud).
- [ ] Los chips de "Tipo de solución" permiten marcar/desmarcar varias opciones.
- [ ] La validación de nombre/correo funciona.
- [ ] El envío dispara el `fetch` (en local termina en el mensaje de error, esperado).
- [ ] Consola sin errores de JS.

- [ ] **Step 2: Verificar el caso "sin JS / React lento"**

Abrir DevTools → Network → throttling o bloquear `assets/app.js` temporalmente, recargar. Esperado: el contenido del template no debe quedar oculto permanentemente (gracias a la red de seguridad de Task 1 y al reveal visible-por-defecto). Restaurar después.

- [ ] **Step 3: Resumen al usuario**

Reportar en español: freeze resuelto, scroll-reveal funcionando, chips multi-select listos, formulario cableado a Netlify (recordar que la recepción real de correos se prueba recién al publicar en Netlify, y que falta configurar en el panel de Netlify la notificación al correo Hostinger + verificar registros MX).

---

## Pendiente posterior (fuera de este plan)

- `git init` + push a `https://github.com/matiasvladilo/DMTechSpA.git`.
- Configurar en el panel de Netlify la notificación por correo de Netlify Forms hacia la casilla de Hostinger.
- Verificar registros MX del dominio en el DNS de Netlify para que el correo de Hostinger siga recibiendo.
