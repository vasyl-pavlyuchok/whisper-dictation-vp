---
name: whisper-dictation-vp-release
description: Publica una nueva versión de Whisper Dictation VP de principio a fin — sincronización de versión en todos los archivos, tests del motor de toques, build del .pkg, commit, tag y release automática en GitHub. Usa esta skill siempre que haya que sacar una versión nueva, subir un fix, "hacer release", "publicar la app", bump de versión, o cuando cambios en src/ estén listos para llegar a los usuarios — aunque no se mencione la palabra release.
---

# Release de Whisper Dictation VP

Proceso completo y probado para publicar una versión. El orden importa: los tests van antes del build, y el build local antes del tag (el tag dispara la CI pública — no publiques un tag sin haber verificado el build en local).

## 1. Sincronizar la versión (5 sitios + textos)

La versión vive en varios archivos que DEBEN quedar idénticos. Olvidar uno es el error más común:

| Archivo | Qué tocar |
|---|---|
| `src/whisper_dictation_vp.py` | `APP_VERSION = "X.Y.Z"` y el docstring |
| `src/whisper_dictation_win.py` | `APP_VERSION = "X.Y.Z"` y el docstring |
| `app/whisper_dictation_vp.spec` | `APP_VERSION = "X.Y.Z"` |
| `build.sh` | `VERSION="X.Y.Z"` |
| `installer/distribution.xml` | atributo `version=` del pkg-ref |
| `installer/resources/welcome.html` | texto de versión |
| `installer/scripts/postinstall` | texto del diálogo final |

Verifica que no queda ninguna versión vieja:

```bash
grep -rn "X\.Y\.OLD" build.sh app/*.spec installer/ src/ README.md
```

Versionado: parche (X.Y.Z+1) para fixes; menor (X.Y+1.0) para funciones nuevas; mayor solo con cambios de arquitectura (p. ej. el salto a app nativa fue 2.x→3.0).

## 2. Tests y sintaxis

```bash
.buildenv/bin/python -m py_compile src/whisper_dictation_vp.py src/whisper_dictation_win.py
```

Si tocaste el motor de teclado (`_handle_key_event`, `_register_tap`, hotkeys), ejecuta los tests del motor de toques (9 escenarios que incluyen el modo de entrega defectuosa de modificadores). Si el archivo de tests no está en scratchpad, está descrito en la memoria del proyecto — recréalo antes de tocar ese código.

Si tocaste `transcribe()` o `ai_cleanup()`, haz una prueba real end-to-end: genera audio con `say`, conviértelo con `afconvert -f WAVE -d LEI16@16000 -c 1`, y pásalo por las funciones con la config real del usuario (`load_config()`). Comprueba tildes en el resultado.

## 3. Build local y verificación

```bash
./build.sh
```

Genera `~/Desktop/WhisperDictationVP-<Arch>.pkg`. Si el llavero tiene la identidad `Whisper Dictation VP Signing`, firma estable (el permiso de Accesibilidad sobrevive a updates); si no, ad-hoc y el postinstall resetea TCC.

Verifica el .pkg antes de publicar nada:

```bash
pkgutil --expand-full ~/Desktop/WhisperDictationVP-*.pkg /tmp/pkg_check
defaults read "/tmp/pkg_check/WhisperDictationVP_component.pkg/Payload/Applications/Whisper Dictation VP.app/Contents/Info.plist" CFBundleShortVersionString
"/tmp/pkg_check/WhisperDictationVP_component.pkg/Payload/Applications/Whisper Dictation VP.app/Contents/MacOS/WhisperDictationVP" &
```

La app debe seguir viva ≥10 s (el aviso «This process is not trusted» es normal en una copia de prueba). Mátala después y borra `~/.whisper_dictation_vp.lock` si quedó.

## 4. Publicar

```bash
git add -A && git commit -m "vX.Y.Z: resumen"   # con Co-Authored-By de Claude
git push origin master
git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z
```

El tag `v*` dispara `.github/workflows/release.yml`: compila macOS AppleSilicon (macos-latest), macOS Intel (macos-15-intel) y Windows (windows-latest), y publica la Release con nombres de archivo ESTABLES — no los cambies, hay enlaces `releases/latest/download/` que dependen de ellos:

- `WhisperDictationVP-AppleSilicon.pkg`
- `WhisperDictationVP-Intel.pkg`
- `WhisperDictationVP-Windows.zip`

Verifica la CI sin gh (repo público):

```bash
curl -s 'https://api.github.com/repos/vasyl-pavlyuchok/whisper-dictation-vp/actions/runs?per_page=1'
curl -s 'https://api.github.com/repos/vasyl-pavlyuchok/whisper-dictation-vp/releases/tags/vX.Y.Z'
```

Espera con un bucle `until` en background — la CI tarda 5-15 min.

## 5. Actualizar los README (bilingües) y la web

Los README son DOS y deben quedar sincronizados — publicamos en español pero el
inglés tiene que existir sí o sí para llegar a las masas:

- `README.md` — español, el principal. Entrada de changelog completa + funciones
  nuevas en la lista de funcionalidades.
- `README.en.md` — inglés. Mismas secciones y datos; el changelog inglés es un
  resumen por versión que enlaza al changelog completo del español.
- Ambos llevan el selector de idioma en la PRIMERA línea:
  `🇪🇸 **Español** | [🇬🇧 English](README.en.md)` (y el inverso en el inglés).
  Cualquier repo nuevo que se publique debe seguir este mismo patrón.

La página de la app en vasylpavlyuchok.com debe reflejar versiones/funciones
nuevas — usa la skill `publicar-vasylpavlyuchok` para eso.

## 6. Instalación local del usuario

Tú no puedes ejecutar el instalador (necesita contraseña de admin): ábrelo con `open ~/Desktop/WhisperDictationVP-Intel.pkg` y pide al usuario que lo complete. Con firma ad-hoc, macOS pedirá el permiso de Accesibilidad UNA vez tras instalar (el postinstall resetea la entrada TCC vieja — es lo esperado, no un bug).

## Diagnóstico si algo falla tras instalar

- Log de la app: `~/Library/Logs/WhisperDictationVP.log` (eventos de hotkey, permisos, transcripciones por longitud).
- Self-test del listener: `touch ~/.wdvp_selftest` y relanzar la app — postea toques sintéticos a sí misma y los registra en el log con `injected=True`.
- «La casilla de Accesibilidad está activada pero no responde» = permiso huérfano de una firma anterior: `tccutil reset Accessibility com.vasyl.whisper-dictation-vp` y reconceder.
- Tildes corruptas al pegar: casi seguro es el RECEPTOR sin locale UTF-8, no la app — comprueba el historial en `~/.whisper_dictation_vp.json`: si ahí está bien, la app es inocente.
