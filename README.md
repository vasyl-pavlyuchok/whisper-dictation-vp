# Whisper Dictation VP

Dictado por voz para macOS usando inteligencia artificial. Mantén **Option derecho** pulsado para grabar, suelta para transcribir y pegar automáticamente en cualquier app.

Diseñado por **Vasyl Pavlyuchok** & **Claude** — v1.3

---

## ¿Cómo funciona?

1. Mantienes pulsado **Option derecho** (⌥ derecho)
2. Hablas
3. Sueltas la tecla
4. El texto aparece pegado donde estabas escribiendo

El icono en la barra de menús indica el estado:
- 🎙 Listo
- 🔴 Grabando
- ⏳ Transcribiendo

---

## Requisitos

- macOS 11 Big Sur o superior
- Python 3.11 o superior *(el instalador te ayuda a instalarlo si no lo tienes)*
- Una API key gratuita de [Groq](https://console.groq.com) **o** de [OpenAI](https://platform.openai.com)

### Sobre la API key

La transcripción se realiza en la nube usando la API de Whisper. Necesitas una cuenta en uno de estos servicios:

| Proveedor | Modelo | Precio | Enlace |
|-----------|--------|--------|--------|
| **Groq** (recomendado) | whisper-large-v3 | Gratuito | [console.groq.com](https://console.groq.com) |
| OpenAI | whisper-1 | De pago | [platform.openai.com](https://platform.openai.com) |

Groq ofrece un generoso plan gratuito más que suficiente para uso personal.

---

## Instalación

### Opción 1 — Instalador .pkg (recomendado)

1. Descarga `WhisperDictationVP.pkg` desde la página de [Releases](../../releases)
2. Haz doble clic para ejecutar el instalador
3. El instalador comprueba automáticamente si tienes Python instalado y lo instala si hace falta
4. Al primer arranque, la app te pedirá tu API key

### Opción 2 — Desde el código fuente

Consulta la sección [Build](#build-desde-el-código-fuente) más abajo.

---

## Permisos necesarios

macOS pedirá dos permisos la primera vez:

- **Accesibilidad** — para pegar el texto automáticamente con Cmd+V
- **Micrófono** — para grabar tu voz *(se concede a Terminal, que actúa como proceso intermediario)*

---

## Configuración

La configuración se guarda en `~/.whisper_dictation_vp.json`:

```json
{
  "provider": "groq",
  "api_key": "gsk_..."
}
```

También puedes usar variables de entorno:

```bash
export WHISPER_PROVIDER=groq
export WHISPER_API_KEY=gsk_...
```

Para cambiar la API key o el proveedor, elimina `~/.whisper_dictation_vp.json` y reinicia la app.

---

## Desinstalación

```bash
launchctl unload ~/Library/LaunchAgents/com.vasyl.whisper-dictation-vp.plist
rm -f ~/Library/LaunchAgents/com.vasyl.whisper-dictation-vp.plist
sudo rm -rf "/Applications/Whisper Dictation VP.app"
sudo rm -rf /usr/local/lib/whisper_dictation_vp
rm -f ~/.whisper_dictation_vp.json
```

---

## Build desde el código fuente

### Estructura del repositorio

```
whisper-dictation-vp/
├── src/
│   └── whisper_dictation_vp.py   # Script principal de la app
├── app/
│   ├── Info.plist                 # Configuración del bundle .app
│   └── launch_whisper.scpt        # Script de arranque (AppleScript)
├── installer/
│   ├── distribution.xml           # Configuración del wizard de instalación
│   ├── scripts/
│   │   └── postinstall            # Script de post-instalación
│   └── resources/
│       ├── welcome.html           # Pantalla de bienvenida del instalador
│       └── background.png         # Imagen de fondo del instalador *
├── build.sh                       # Script de build automatizado
└── README.md
```

> `*` No incluida en el repositorio. Coloca tu propia imagen en `installer/resources/background.png` (800×600 px recomendado).

### Generar el .pkg

```bash
# Requiere macOS con Xcode Command Line Tools instalado
chmod +x build.sh
./build.sh
```

El instalador se genera en `~/Desktop/WhisperDictationVP.pkg`.

---

## Dependencias Python

Instaladas automáticamente por el instalador:

- `rumps` — icono y menú en la barra de menús
- `sounddevice` — captura de audio
- `numpy` — procesamiento de audio
- `pynput` — escucha global del teclado
- `python-dotenv` — soporte de variables de entorno
- `groq` — cliente de la API de Groq
- `openai` — cliente de la API de OpenAI

---

## Licencia

MIT — consulta [LICENSE](LICENSE)
