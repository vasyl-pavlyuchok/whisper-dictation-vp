# Whisper Dictation VP

Dictado por voz para macOS usando inteligencia artificial. Doble-toque **Option derecho** para iniciar la grabación, toque simple para detener — el texto aparece pegado automáticamente en cualquier app.

Diseñado por **Vasyl Pavlyuchok** & **Claude** — v2.2

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

## Requisitos

- macOS 11 Big Sur o superior
- Python 3.11 o superior *(el instalador te ayuda a instalarlo si no lo tienes)*
- Una API key de cualquiera de los proveedores soportados

### Proveedores de transcripción

| Proveedor | Modelo | Precio | Enlace |
|-----------|--------|--------|--------|
| **Groq** (recomendado) | whisper-large-v3 | Gratuito | [console.groq.com](https://console.groq.com) |
| OpenAI | whisper-1 | De pago | [platform.openai.com](https://platform.openai.com) |
| Deepgram | nova-2 | Plan gratuito | [console.deepgram.com](https://console.deepgram.com) |
| AssemblyAI | — | Plan gratuito | [app.assemblyai.com](https://app.assemblyai.com) |

Groq es gratuito y más que suficiente para uso personal.

---

## Instalación

1. Descarga `WhisperDictationVP.pkg` desde la página de [Releases](../../releases)
2. Haz doble clic para ejecutar el instalador
3. El instalador comprueba automáticamente si tienes Python instalado y lo instala si hace falta
4. Al finalizar aparecerá un aviso recordándote activar el permiso de Accesibilidad (ver abajo)
5. Al primer arranque, la app te pedirá tu proveedor y API key

---

## Permisos necesarios

### Accesibilidad — obligatorio

La app necesita que **Terminal** tenga permiso de Accesibilidad para poder escuchar la tecla de dictado y pegar el texto.

El instalador te recordará este paso, pero los pasos son:

1. Abre **Preferencias del Sistema → Seguridad y Privacidad → Privacidad → Accesibilidad**
2. Haz clic en el candado e introduce tu contraseña
3. Activa la casilla de **Terminal**

Sin este permiso la tecla de dictado no funcionará.

### Micrófono

macOS pedirá permiso de micrófono automáticamente la primera vez que grabes.

---

## Funcionalidades

- **Doble-toque para grabar** — inicia la grabación sin mantener la tecla pulsada; toque simple para detener
- **Historial interactivo** — haz clic en cualquier transcripción para verla completa, copiarla, pegarla o editarla
- **Panel de configuración** accesible desde el icono de la barra de menús
- **4 proveedores de IA** — añade, cambia o elimina APIs desde el menú
- **Últimas 10 transcripciones** guardadas en el historial
- **Idioma configurable** — español, inglés, francés, alemán, italiano, portugués o automático
- **Tecla de activación configurable** — Option derecho, Option izquierdo, Control o Command
- **Feedback sonoro** — Tink al iniciar, Pop al transcribir, Basso si hay un error
- Se inicia automáticamente al arrancar el Mac

---

## Configuración

Toda la configuración se gestiona desde el icono de la barra de menús → **⚙️ Configuración**.

El archivo de configuración se guarda en `~/.whisper_dictation_vp.json`. Para resetear todo, elimínalo y reinicia la app.

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

## Changelog

### v2.2
- **Doble-toque para grabar** — ya no hace falta mantener la tecla pulsada
- **Historial interactivo** — clic en una transcripción para ver, copiar, pegar o editar
- Thread safety: todas las actualizaciones de UI van al main thread
- Feedback sonoro en errores de transcripción y grabaciones demasiado cortas
- Protección contra key-repeat del SO
- Escape de caracteres especiales en diálogos AppleScript
- Cierre limpio del keyboard listener al salir
- Diálogos de configuración en hilos separados (no bloquean el run loop)

### v2.1
- Detección automática de Python (3.11–3.13, Homebrew y framework)
- Protección anti-doble-instancia en el launcher
- Soporte multi-proveedor con gestión desde el menú

### v2.0
- Rediseño completo con soporte de múltiples proveedores
- Historial de transcripciones
- Idioma y tecla de activación configurables

---

## Licencia

MIT — consulta [LICENSE](LICENSE)
