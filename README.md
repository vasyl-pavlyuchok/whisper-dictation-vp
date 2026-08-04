🇪🇸 **Español** | [🇬🇧 English](README.en.md)

# 🎙 Whisper Dictation VP

[![Release](https://img.shields.io/github/v/release/vasyl-pavlyuchok/whisper-dictation-vp?label=versi%C3%B3n&color=84cc16)](../../releases/latest)
[![Licencia](https://img.shields.io/badge/licencia-MIT-blue)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-Intel%20%7C%20Apple%20Silicon-black?logo=apple)](../../releases/latest)
[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011%20(beta)-0078d4?logo=windows)](../../releases/latest)

**Dicta en vez de escribir, en cualquier app.** Doble-toque una tecla, habla, toque simple — y el texto aparece donde estabas escribiendo. Gratis y de código abierto: funciona con la **API gratuita de Groq** (whisper-large-v3) — meses de uso diario sin tocar un solo límite. Sin suscripción: lo que cuesta un Wispr Flow, te lo ahorras cada mes.

🌐 **Detección automática de idioma** — habla y Whisper reconoce el idioma solo:

🇪🇸 🇬🇧 🇺🇦 🇫🇷 🇩🇪 🇮🇹 🇵🇹 🇨🇳 🇷🇺 🇸🇦 🇮🇳 🇯🇵 🇰🇷 🇹🇷 🇵🇱 🇳🇱

Diseñado por **Vasyl Pavlyuchok** & **Claude** — v3.4.0

---

## ¿Por qué existe?

Dictar en vez de escribir cambia por completo la velocidad a la que trabajas. Apps como Wispr Flow demostraron lo potente que es esta forma de interactuar; esta app nace de esa idea, pero **libre y bajo tu control**: tu API key, sin cuota mensual. Detecta el idioma automáticamente, tiene un **diccionario personal** para tu vocabulario (los nombres y términos que por pronunciación siempre salen mal) y un **Formato IA** que limpia muletillas y puntuación mientras hablas. La primera versión se construyó con Claude en una tarde; hoy es una app 100% nativa para macOS y Windows, validada con uso diario, y se comparte para que más personas tengan acceso a herramientas así sin pagar una suscripción.

---

## Descargas

Ve a la página de [**Releases**](../../releases/latest) y descarga la versión para tu sistema:

| Sistema | Archivo |
|---------|---------|
| **macOS Apple Silicon** (M1/M2/M3/M4) | `WhisperDictationVP-AppleSilicon.pkg` |
| **macOS Intel** | `WhisperDictationVP-Intel.pkg` |
| **Windows 10/11** (beta) | `WhisperDictationVP-Windows.zip` |

> **Novedad v3.0** — La app de macOS ahora es **100% nativa**: lleva Python embebido, así que ya **no necesitas tener Python instalado ni se abre ninguna ventana de Terminal**. Solo instalar y dictar.

---

## ¿Cómo funciona?

1. **Doble-toque** en **Option derecho** (⌥ derecho) para iniciar la grabación
2. Habla con tranquilidad — sin mantener ninguna tecla
3. **Toque simple** para detener
4. El texto aparece pegado donde estabas escribiendo

El icono en la barra de menús indica el estado:
- 🎙 Listo
- ⭕ Grabando
- ⏳ Transcribiendo

---

## Proveedores de transcripción

Solo necesitas **una** API key para empezar. **Recomendado: Groq** — es gratuito, muy rápido y usa el modelo Whisper large-v3, el que mejor funciona con diferencia.

| Proveedor | Modelo | Precio | Consigue tu clave en |
|-----------|--------|--------|----------------------|
| **Groq** ⭐ recomendado | whisper-large-v3 | **Gratuito** | [console.groq.com](https://console.groq.com) |
| OpenAI | whisper-1 | De pago | [platform.openai.com](https://platform.openai.com) |
| Deepgram | nova-2 | Plan gratuito | [console.deepgram.com](https://console.deepgram.com) |
| AssemblyAI | universal | Plan gratuito | [app.assemblyai.com](https://app.assemblyai.com) |

**Cómo conseguir tu clave de Groq (1 minuto):**
1. Entra en [console.groq.com](https://console.groq.com) y crea una cuenta gratuita
2. Ve a **API Keys** → **Create API Key**
3. Copia la clave (empieza por `gsk_...`)
4. Al abrir Whisper Dictation VP por primera vez, elige **Groq** y pega la clave

---

## Instalación en macOS

1. Descarga el `.pkg` de tu arquitectura desde [Releases](../../releases/latest)
2. Haz doble clic para ejecutar el instalador *(si macOS avisa de desarrollador no identificado: clic derecho → Abrir)*
3. Al finalizar, la app se abre sola y macOS te pedirá los permisos
4. En el primer arranque, la app te pedirá tu proveedor y API key

### Permisos necesarios

macOS separa en **dos permisos distintos** lo que la app necesita. **Hacen falta los dos**: con uno solo la app arranca, el icono 🎙 aparece en la barra… y la tecla no responde.

| Permiso | Para qué | Si falta |
|---------|----------|----------|
| **Monitorización de entrada** | **Leer** la tecla de dictado | La app no recibe ninguna pulsación: nada ocurre al pulsar la tecla |
| **Accesibilidad** | **Pegar** el texto transcrito | Graba y transcribe, pero el texto no se pega |

1. macOS mostrará los dos avisos automáticamente al abrir la app. Si no:
2. **Ajustes del Sistema → Privacidad y seguridad → Monitorización de entrada** → activa **Whisper Dictation VP**
3. **Ajustes del Sistema → Privacidad y seguridad → Accesibilidad** → activa **Whisper Dictation VP**
4. Sal de la app (icono 🎙 → Salir) y vuelve a abrirla

> **El fallo clásico:** tener solo Accesibilidad activada. La casilla aparece marcada, todo *parece* correcto y la tecla sigue sin hacer nada — porque quien autoriza a *leer* el teclado es Monitorización de entrada, no Accesibilidad.

> Si vienes de la v2.x: el permiso ahora es para «Whisper Dictation VP», ya no para «Terminal». Puedes desmarcar Terminal de la lista.

**Micrófono** — macOS lo pedirá automáticamente la primera vez que grabes.

---

## Instalación en Windows (beta)

1. Descarga **`WhisperDictationVP-Windows-Setup.exe`** desde [Releases](../../releases/latest) *(o el `.zip` si prefieres la versión portable)*
2. **SmartScreen mostrará un aviso azul** («Windows protegió su PC») porque la app no está firmada — los certificados de firma cuestan 200–400 €/año y esta app es gratuita y open source: pulsa **«Más información» → «Ejecutar de todas formas»**. Solo lo pide la primera vez.
3. El instalador te deja **elegir idioma** (español/inglés), te explica lo esencial (API gratuita de Groq, los 16 idiomas con detección automática) y ofrece **inicio automático con Windows**
4. En el primer arranque la app te pedirá tu API key de Groq
5. Doble-toque en **Alt izquierdo** para grabar, toque simple para detener — mientras grabas verás un **indicador flotante minimalista** (micrófono en rojo; spinner en ámbar al transcribir)

> **Consejos**: en teclados españoles el Alt derecho es AltGr — si prefieres esa tecla, elígela en el menú del icono. Si no transcribe nada, revisa **Configuración → Privacidad → Micrófono → «Permitir que las aplicaciones de escritorio accedan al micrófono»**, y consulta el log de diagnóstico en `%USERPROFILE%\whisper_dictation_vp.log` (ábrelo con el Bloc de notas).

---

## Funcionalidades

- **Doble-toque para grabar** — inicia la grabación sin mantener la tecla pulsada; toque simple para detener
- **App nativa** — Python embebido, sin dependencias externas ni ventanas de Terminal
- **✨ Formato IA** — un LLM (gratuito con Groq) elimina muletillas («eh», «em», repeticiones) y corrige puntuación y mayúsculas antes de pegar
- **📖 Diccionario personal** — añade nombres propios y tecnicismos que Whisper suele transcribir mal; se aplican tanto en la transcripción como en el formato IA
- **Historial interactivo** — haz clic en cualquier transcripción para verla completa, copiarla o editarla
- **4 proveedores de IA** — añade, cambia o elimina APIs desde el menú
- **Últimas 10 transcripciones** guardadas en el historial
- **Detección automática de idioma** — habla en el idioma que quieras y Whisper lo detecta; o fíjalo entre 16 idiomas (español, inglés, ucraniano, francés, alemán, italiano, portugués, chino, ruso, árabe, hindi, japonés, coreano, turco, polaco, neerlandés)
- **Tecla de activación configurable** — Option derecho, Option izquierdo, Control o Command
- **Detección de silencio** — no envía nada a la API si no hay voz
- **Feedback sonoro** — Tink al iniciar, Pop al transcribir, Basso si hay un error
- Se inicia automáticamente al arrancar el equipo

---

## Configuración

Toda la configuración se gestiona desde el icono de la barra de menús → **⚙️ Configuración**.

El archivo de configuración se guarda en `~/.whisper_dictation_vp.json`. Para resetear todo, elimínalo y reinicia la app.

---

## Compilar desde el código fuente

**macOS** (necesitas Python 3.11+ solo para compilar):

```bash
./build.sh
```

Genera `WhisperDictationVP-<Arquitectura>.pkg` en el Escritorio, con la app y su Python embebido vía PyInstaller. Si el llavero contiene la identidad `Whisper Dictation VP Signing`, la app se firma con ella (permiso de Accesibilidad estable entre versiones); si no, firma ad-hoc.

**Releases automáticas** — al subir un tag `v*`, GitHub Actions compila las tres versiones (macOS arm64, macOS x86_64 y Windows) y las publica en Releases.

---

## Desinstalación

**macOS:**

```bash
launchctl unload ~/Library/LaunchAgents/com.vasyl.whisper-dictation-vp.plist
rm -f ~/Library/LaunchAgents/com.vasyl.whisper-dictation-vp.plist
sudo rm -rf "/Applications/Whisper Dictation VP.app"
sudo rm -rf /usr/local/lib/whisper_dictation_vp
rm -f ~/.whisper_dictation_vp.json
```

**Windows:** elimina la carpeta descomprimida y `%USERPROFILE%\.whisper_dictation_vp.json`.

---

## Changelog

### v3.5.1 (solo Windows — en Mac puedes ignorar esta actualización)
- **Selector de micrófono en el menú** — caso real diagnosticado: Windows daba como entrada predeterminada el micrófono de una webcam que no captaba nada (RMS plano) y la app "no transcribía"; ahora eliges el micrófono correcto desde el menú de la bandeja y queda guardado
- El log registra el micrófono activo y cada cambio de dispositivo

### v3.5.0 (solo Windows — en Mac puedes ignorar esta actualización)
- **Instalador de verdad (`WhisperDictationVP-Windows-Setup.exe`)** — asistente Inno Setup con selección de idioma (ES/EN), página informativa obligatoria que explica la API gratuita de Groq, los 16 idiomas con detección automática y el aviso de SmartScreen (y por qué aparece: los certificados cuestan 200–400 €/año y esta app es gratuita), instalación por usuario sin permisos de administrador, y opción de inicio automático con Windows
- **Indicador flotante minimalista de solo iconos** — micrófono Lucide blanco sobre rojo al grabar, spinner sobre ámbar al transcribir; sin texto: universal en cualquier idioma
- **LEEME.txt bilingüe dentro del zip portable** — con la explicación de SmartScreen para leer antes de ejecutar
- **Icono propio de la app** en el exe, la barra de tareas y el instalador

### v3.4.1 (solo Windows — en Mac puedes ignorar esta actualización)
- **Indicador flotante «● Grabando… / Transcribiendo»** — píldora siempre visible abajo-centro, porque el icono de la bandeja de Windows suele quedar oculto tras la flecha
- **Sonido al parar la grabación** — feedback de tres tiempos: iniciar (agudo), parar (medio), texto pegado (ok) o error (grave)
- **Alt izquierdo como tecla por defecto** — el Alt derecho es AltGr en teclados españoles y Windows lo trata como otra tecla
- **Log de diagnóstico** en `%USERPROFILE%\whisper_dictation_vp.log` — registra micrófono detectado, RMS del audio, transcripciones y errores con detalle; el silencio del micrófono ahora suena a error y queda explicado en el log
- **Aviso claro si el micrófono está bloqueado** — con la ruta exacta del ajuste de privacidad de Windows

### v3.4.0
- **Iconos profesionales en el menú** — set Lucide monocromo (template: se adapta a modo claro/oscuro), adiós a los emojis
- **Tooltips de ayuda** — al pasar el ratón por Formato IA, Diccionario, Idioma, etc., un tooltip explica qué hace cada función
- **Submenú «Interfaz»** — elige el idioma de la app (Español/English) de una lista con marca, en vez del toggle ciego
- **Detección automática por defecto también al actualizar** — migración única: quien prefiera un idioma fijo lo cambia una vez y se respeta
- **Pantalla de instalación mejorada** — explica la API gratuita de Groq, lista los 16 idiomas + detección automática, y aclara que es un idioma por dictado

### v3.3.0
- **Interfaz bilingüe (ES/EN)** — la app detecta el idioma del sistema y muestra menús y diálogos en español o inglés; conmutador «Interfaz» en el menú para cambiarlo al vuelo *(macOS; Windows en la próxima versión)*
- **Instalador localizado** — el instalador de macOS se muestra en el idioma del sistema (recursos `.lproj`) y los avisos post-instalación son bilingües
- **Menú sin emojis** — etiquetas limpias y profesionales al estilo de las apps nativas de macOS

### v3.2.0
- **🔔 Notificaciones de actualización** — la app comprueba GitHub al arrancar (y cada 24 h); si hay versión nueva muestra una notificación y una entrada «⬆️ Nueva versión — descargar» en el menú (macOS y Windows). Desactivable con un clic desde el menú («🔔 Avisar de actualizaciones»)
- **Doble canal de escucha del hotkey** — NSEvent global monitor (API nativa de macOS) + pynput con dedupe: si un canal falla, el otro sigue funcionando (arregla el caso «permiso concedido pero la tecla no responde»)

### v3.1.2
- **Idioma automático por defecto** — Whisper detecta el idioma de cada dictado (español, inglés, ucraniano, italiano…); ya no hay que cambiarlo a mano
- **17 idiomas en el menú** — añadidos ucraniano, chino, ruso, árabe, hindi, japonés, coreano, turco, polaco y neerlandés
- **Portapapeles nativo (NSPasteboard)** — copia inmune a problemas de locale en cualquier entorno

### v3.1.1
- **Fix del permiso de Accesibilidad huérfano** — al actualizar, la firma ad-hoc cambia y macOS ignoraba el permiso ya concedido (la casilla aparecía activada pero la tecla no respondía y el aviso salía en cada arranque); el instalador ahora resetea la entrada TCC para que el permiso se pida una sola vez, limpio
- **Instancia única** — el instalador y el auto-arranque ya no pueden abrir la app dos veces (adiós diálogos duplicados)
- **Aviso de permiso una sola vez por versión** — nada de prompts repetidos en cada arranque
- **Firma estable opcional** — si existe el certificado local `Whisper Dictation VP Signing`, la app se firma con identidad constante y el permiso de Accesibilidad sobrevive a las actualizaciones
- **✨ Formato IA** — post-procesado opcional con LLM (Groq llama-3.3 gratuito u OpenAI): elimina muletillas y corrige puntuación sin cambiar el significado
- **📖 Diccionario personal** — palabras que Whisper transcribe mal (nombres, marcas, tecnicismos) se corrigen automáticamente
- **Fix crítico del hotkey** — en la app empaquetada los modificadores (Cmd, Ctrl) podían llegar como «release» sin «press» y la grabación no se podía detener; el nuevo motor consulta el estado físico real de la tecla vía Quartz y es inmune a este fallo
- **Anti-eco del pegado** — el Cmd+V sintético de la propia app ya no puede registrarse como toque del hotkey
- **Selector de tecla saneado** — sin opciones duplicadas, y con Command/Control derechos disponibles
- **Log de diagnóstico** — `~/Library/Logs/WhisperDictationVP.log` (rotativo, sin contenido de transcripciones)

### v3.0.0
- **App 100% nativa en macOS** — PyInstaller con Python embebido: ya no hace falta tener Python instalado ni queda ninguna ventana de Terminal abierta
- **Permiso de Accesibilidad propio** — la app pide el permiso con el diálogo del sistema y aparece como «Whisper Dictation VP» (antes había que dárselo a Terminal)
- **Instalador simplificado** — sin instalación de Python ni Homebrew: instalar y listo
- **Versión Windows (beta)** — icono en bandeja del sistema, mismo flujo de doble-toque
- **CI/CD** — GitHub Actions compila y publica automáticamente las versiones de macOS (Intel + Apple Silicon) y Windows

### v2.5.1
- Arreglos de transcripción para Deepgram y AssemblyAI
- Copia rápida en historial

### v2.4
- UI limpia, transparencia real (NSVisualEffectView), audio nativo y menú mejorado
- Umbral de silencio calibrado al micrófono

### v2.3.1
- Submenús de proveedor e idioma con checkmark
- Historial mejorado con edición
- Detección de silencio

### v2.1
- Detección automática de Python (3.11–3.13, Homebrew y framework)
- Protección anti-doble-instancia

### v2.0
- Rediseño completo con soporte de múltiples proveedores
- Historial de transcripciones
- Idioma y tecla de activación configurables

---

## Licencia

MIT — consulta [LICENSE](LICENSE) · Iconos: [Lucide](https://lucide.dev) (ISC)
