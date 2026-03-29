# Whisper Dictation VP

Dictado por voz para macOS usando inteligencia artificial. Mantén **Option derecho** pulsado para grabar, suelta para transcribir y pegar automáticamente en cualquier app.

Diseñado por **Vasyl Pavlyuchok** & **Claude** — v2.1

---

## ¿Cómo funciona?

1. Mantienes pulsado **Option derecho** (⌥ derecho)
2. Hablas
3. Sueltas la tecla
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

- **Panel de configuración** accesible desde el icono de la barra de menús
- **4 proveedores de IA** — añade, cambia o elimina APIs desde el menú
- **Historial** de las últimas 10 transcripciones
- **Idioma configurable** — español, inglés, francés, alemán, italiano, portugués o automático
- **Tecla de activación configurable** — Option derecho, Option izquierdo, Control o Command
- **Sonido sutil** al empezar a grabar y al terminar
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

## Licencia

MIT — consulta [LICENSE](LICENSE)
