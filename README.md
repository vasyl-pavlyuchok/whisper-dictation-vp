# Whisper Dictation VP

Dictado por voz para macOS y Windows usando inteligencia artificial. Doble-toque **Option derecho** para iniciar la grabación, toque simple para detener — el texto aparece pegado automáticamente en cualquier app.

Diseñado por **Vasyl Pavlyuchok** & **Claude** — v3.1.1

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

**Accesibilidad (obligatorio)** — para detectar la tecla de dictado y pegar el texto:

1. macOS mostrará el aviso automáticamente al abrir la app. Si no:
2. **Ajustes del Sistema → Privacidad y seguridad → Accesibilidad**
3. Activa **Whisper Dictation VP**
4. Sal de la app (icono 🎙 → Salir) y vuelve a abrirla

> Si vienes de la v2.x: el permiso ahora es para «Whisper Dictation VP», ya no para «Terminal». Puedes desmarcar Terminal de la lista.

**Micrófono** — macOS lo pedirá automáticamente la primera vez que grabes.

---

## Instalación en Windows (beta)

1. Descarga `WhisperDictationVP-Windows.zip` desde [Releases](../../releases/latest)
2. Descomprime y ejecuta `WhisperDictationVP.exe` *(si SmartScreen avisa: Más información → Ejecutar de todas formas)*
3. El icono aparece en la bandeja del sistema; en el primer arranque te pedirá tu API key
4. Doble-toque en **Alt derecho** para grabar, toque simple para detener

---

## Funcionalidades

- **Doble-toque para grabar** — inicia la grabación sin mantener la tecla pulsada; toque simple para detener
- **App nativa** — Python embebido, sin dependencias externas ni ventanas de Terminal
- **✨ Formato IA** — un LLM (gratuito con Groq) elimina muletillas («eh», «em», repeticiones) y corrige puntuación y mayúsculas antes de pegar
- **📖 Diccionario personal** — añade nombres propios y tecnicismos que Whisper suele transcribir mal; se aplican tanto en la transcripción como en el formato IA
- **Historial interactivo** — haz clic en cualquier transcripción para verla completa, copiarla o editarla
- **4 proveedores de IA** — añade, cambia o elimina APIs desde el menú
- **Últimas 10 transcripciones** guardadas en el historial
- **Idioma configurable** — español, inglés, francés, alemán, italiano, portugués o automático
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

MIT — consulta [LICENSE](LICENSE)
