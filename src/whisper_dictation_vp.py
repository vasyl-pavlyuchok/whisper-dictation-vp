#!/usr/bin/env python3
"""
Whisper Dictation VP — Dictado por voz para macOS.
Doble-toque Option derecho para iniciar grabación. Toque simple para detener.
Diseñado por Vasyl Pavlyuchok & Claude — v3.5.2
"""

APP_VERSION = "3.5.2"

import os, sys, tempfile, threading, subprocess, json, wave, time, queue
import rumps, numpy as np, sounddevice as sd
from pynput import keyboard
from dotenv import load_dotenv
load_dotenv()

CONFIG_FILE       = os.path.expanduser("~/.whisper_dictation_vp.json")
HISTORY_MAX       = 10
SAMPLE_RATE       = 16000
CHANNELS          = 1
DTYPE             = "int16"
ICON_IDLE         = "🎙"
ICON_RECORDING    = "⭕"
ICON_PROCESSING   = "⏳"
DOUBLE_TAP_WINDOW = 0.4

PROVIDERS = {
    "groq":       {"name": "Groq (gratis)",  "url": "console.groq.com",       "placeholder": "gsk_..."},
    "openai":     {"name": "OpenAI",          "url": "platform.openai.com",    "placeholder": "sk-..."},
    "deepgram":   {"name": "Deepgram",        "url": "console.deepgram.com",   "placeholder": "..."},
    "assemblyai": {"name": "AssemblyAI",      "url": "app.assemblyai.com",     "placeholder": "..."},
}

# ── Internacionalización de la interfaz (ES/EN) ───────────────────────────────

def system_ui_lang():
    """Idioma preferido del sistema: 'es' o 'en' (fallback)."""
    try:
        from Foundation import NSLocale
        code = str(NSLocale.preferredLanguages()[0])[:2].lower()
        return "es" if code == "es" else "en"
    except Exception:
        return "es"

LANGUAGES_I18N = {
    "es": {
        "auto": "Automático (detecta el idioma)",
        "es": "Español", "en": "Inglés", "uk": "Ucraniano", "fr": "Francés",
        "de": "Alemán", "it": "Italiano", "pt": "Portugués", "zh": "Chino",
        "ru": "Ruso", "ar": "Árabe", "hi": "Hindi", "ja": "Japonés",
        "ko": "Coreano", "tr": "Turco", "pl": "Polaco", "nl": "Neerlandés",
    },
    "en": {
        "auto": "Automatic (detect language)",
        "es": "Spanish", "en": "English", "uk": "Ukrainian", "fr": "French",
        "de": "German", "it": "Italian", "pt": "Portuguese", "zh": "Chinese",
        "ru": "Russian", "ar": "Arabic", "hi": "Hindi", "ja": "Japanese",
        "ko": "Korean", "tr": "Turkish", "pl": "Polish", "nl": "Dutch",
    },
}
LANGUAGES = LANGUAGES_I18N["es"]  # compatibilidad; se resuelve por ui_lang

TR = {
    "es": {
        "yes": "Sí", "no": "No", "cancel": "Cancelar",
        "provider": "Proveedor", "language": "Idioma",
        "hotkey_line": "Tecla: {} (doble-toque)",
        "history": "Historial", "empty": "(vacío)",
        "clear_history": "Limpiar historial",
        "copy": "Copiar", "open_edit": "Abrir / Editar",
        "settings": "Configuración…", "quit": "Salir",
        "ai_format": "Formato IA", "ai_requires": " (requiere Groq/OpenAI)",
        "dictionary": "Diccionario", "add_word": "Añadir palabra…",
        "delete": "Eliminar",
        "updates": "Avisar de actualizaciones",
        "ui_menu": "Interfaz",
        "tip_ai": "Un modelo de IA (gratuito con Groq) limpia la transcripción antes de pegarla: elimina muletillas («eh», «em»…), corrige puntuación y mayúsculas. No cambia el significado.",
        "tip_dict": "Palabras que Whisper suele transcribir mal (nombres propios, marcas, tecnicismos). Se usan para guiar la transcripción y el Formato IA.",
        "tip_updates": "Consulta GitHub una vez al día. Si hay versión nueva, aparece un aviso y una opción de descarga en este menú. Sin datos personales.",
        "tip_ui": "Idioma de los menús y diálogos de la app (no afecta al idioma del dictado).",
        "tip_language": "Idioma del dictado. En Automático, Whisper detecta el idioma de cada grabación (un idioma por dictado).",
        "tip_hotkey": "Doble-toque para empezar a grabar; un toque para parar y pegar. Cámbiala en Configuración.",
        "tip_history": "Tus últimas 10 transcripciones. Clic para copiar o editar.",
        "new_version": "Nueva versión v{} — descargar",
        "notif_title": "Nueva versión v{} disponible",
        "notif_body": "Descárgala desde el menú 🎙 de la barra.",
        "dlg_add_word": "Añade una palabra o nombre propio que Whisper suela "
                        "transcribir mal (p. ej. «Techbooster», «Vasyl»):",
        "dlg_settings_what": "¿Qué quieres configurar?",
        "dlg_hotkey_option": "Tecla de activación",
        "dlg_select_hotkey": "Selecciona la tecla de activación:",
        "dlg_select_provider": "Selecciona el proveedor de transcripción:",
        "dlg_api_key": "API Key de {}\n({}):",
        "dlg_all_configured": "Ya tienes todos los proveedores configurados.",
        "dlg_apis_header": "APIs configuradas:",
        "dlg_none": "(ninguna)", "dlg_what_do": "¿Qué quieres hacer?",
        "dlg_manage": "Gestionar existentes", "dlg_add_api": "Añadir nueva API",
        "dlg_select_manage": "Selecciona el proveedor a gestionar:",
        "dlg_active": " (activo)", "dlg_use_this": "Usar este",
        "dlg_change_key": "Cambiar API key",
        "dlg_confirm_delete": "¿Eliminar {}?",
        "ax_help": "Whisper Dictation VP necesita el permiso de Accesibilidad "
                   "para detectar la tecla de dictado y pegar el texto.\n\n"
                   "En el aviso de macOS pulsa «Abrir Ajustes del Sistema» y "
                   "activa «Whisper Dictation VP».\n\n"
                   "Después sal de la app (icono 🎙 → Salir) y vuelve a abrirla.",
        "ax_open": "Abrir Ajustes", "ok": "OK",
        "hotkeys": {
            "alt_r": "Option derecho", "alt": "Option izquierdo",
            "alt_l": "Option izquierdo", "cmd": "Command izquierdo",
            "cmd_l": "Command izquierdo", "cmd_r": "Command derecho",
            "ctrl": "Control izquierdo", "ctrl_l": "Control izquierdo",
            "ctrl_r": "Control derecho",
        },
    },
    "en": {
        "yes": "Yes", "no": "No", "cancel": "Cancel",
        "provider": "Provider", "language": "Language",
        "hotkey_line": "Key: {} (double-tap)",
        "history": "History", "empty": "(empty)",
        "clear_history": "Clear history",
        "copy": "Copy", "open_edit": "Open / Edit",
        "settings": "Settings…", "quit": "Quit",
        "ai_format": "AI Format", "ai_requires": " (requires Groq/OpenAI)",
        "dictionary": "Dictionary", "add_word": "Add word…",
        "delete": "Delete",
        "updates": "Notify about updates",
        "ui_menu": "Interface",
        "tip_ai": "An AI model (free with Groq) cleans the transcript before pasting: removes filler words, fixes punctuation and casing. Meaning is never changed.",
        "tip_dict": "Words Whisper tends to get wrong (proper nouns, brands, technical terms). Used to guide both transcription and AI Format.",
        "tip_updates": "Checks GitHub once a day. If a new version exists, a notice and a download option appear in this menu. No personal data involved.",
        "tip_ui": "Language of the app's menus and dialogs (does not affect dictation language).",
        "tip_language": "Dictation language. On Automatic, Whisper detects the language of each recording (one language per dictation).",
        "tip_hotkey": "Double-tap to start recording; single tap to stop and paste. Change it in Settings.",
        "tip_history": "Your last 10 transcriptions. Click to copy or edit.",
        "new_version": "New version v{} — download",
        "notif_title": "New version v{} available",
        "notif_body": "Download it from the 🎙 menu bar icon.",
        "dlg_add_word": "Add a word or proper noun that Whisper tends to "
                        "get wrong (e.g. “Techbooster”, “Vasyl”):",
        "dlg_settings_what": "What do you want to configure?",
        "dlg_hotkey_option": "Activation key",
        "dlg_select_hotkey": "Choose the activation key:",
        "dlg_select_provider": "Choose the transcription provider:",
        "dlg_api_key": "{} API Key\n({}):",
        "dlg_all_configured": "All providers are already configured.",
        "dlg_apis_header": "Configured APIs:",
        "dlg_none": "(none)", "dlg_what_do": "What do you want to do?",
        "dlg_manage": "Manage existing", "dlg_add_api": "Add new API",
        "dlg_select_manage": "Choose the provider to manage:",
        "dlg_active": " (active)", "dlg_use_this": "Use this one",
        "dlg_change_key": "Change API key",
        "dlg_confirm_delete": "Delete {}?",
        "ax_help": "Whisper Dictation VP needs the Accessibility permission "
                   "to detect the dictation key and paste the text.\n\n"
                   "In the macOS prompt click “Open System Settings” and "
                   "enable “Whisper Dictation VP”.\n\n"
                   "Then quit the app (🎙 icon → Quit) and open it again.",
        "ax_open": "Open Settings", "ok": "OK",
        "hotkeys": {
            "alt_r": "Right Option", "alt": "Left Option",
            "alt_l": "Left Option", "cmd": "Left Command",
            "cmd_l": "Left Command", "cmd_r": "Right Command",
            "ctrl": "Left Control", "ctrl_l": "Left Control",
            "ctrl_r": "Right Control",
        },
    },
}

# Keycodes físicos de macOS por hotkey. Las claves legacy (cmd_l, ctrl_l,
# alt_l) se aceptan en configs antiguas y equivalen a la tecla izquierda.
HOTKEY_VKS = {
    "alt_r":  61, "alt":  58, "alt_l":  58,
    "cmd":    55, "cmd_l": 55, "cmd_r":  54,
    "ctrl":   59, "ctrl_l": 59, "ctrl_r": 62,
}
HOTKEY_NAMES = {
    "alt_r":  "Option derecho",
    "alt":    "Option izquierdo",
    "alt_l":  "Option izquierdo",
    "cmd":    "Command izquierdo",
    "cmd_l":  "Command izquierdo",
    "cmd_r":  "Command derecho",
    "ctrl":   "Control izquierdo",
    "ctrl_l": "Control izquierdo",
    "ctrl_r": "Control derecho",
}
# Opciones mostradas en el selector (sin duplicados físicos)
HOTKEY_CHOICES = ["alt_r", "alt", "cmd", "cmd_r", "ctrl", "ctrl_r"]

# Máscaras de NSEvent.modifierFlags por keycode (Command/Option/Control)
NSEVENT_FLAG_MASKS = {
    55: 1 << 20, 54: 1 << 20,   # Command
    58: 1 << 19, 61: 1 << 19,   # Option
    59: 1 << 18, 62: 1 << 18,   # Control
}
NSEVENT_MASK_FLAGS_CHANGED = 1 << 12  # NSEventTypeFlagsChanged

LOG_FILE = os.path.expanduser("~/Library/Logs/WhisperDictationVP.log")

def dbg(msg):
    """Log ligero de diagnóstico con rotación (~256 KB)."""
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 262144:
            os.replace(LOG_FILE, LOG_FILE + ".old")
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass

UPDATE_URL     = ("https://api.github.com/repos/vasyl-pavlyuchok/"
                  "whisper-dictation-vp/releases/latest")
DOWNLOAD_PAGE  = ("https://github.com/vasyl-pavlyuchok/"
                  "whisper-dictation-vp/releases/latest")

def version_tuple(v):
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except Exception:
        return (0,)

def fetch_latest_version():
    """Devuelve la última versión publicada en GitHub (o None si no hay red)."""
    import urllib.request
    req = urllib.request.Request(UPDATE_URL,
                                 headers={"User-Agent": "WhisperDictationVP"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r).get("tag_name", "").lstrip("v") or None

ICON_DIMENSIONS = (16, 16)

def icon_path(name):
    """PNG de Lucide empaquetado (o del repo en desarrollo)."""
    candidates = []
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidates.append(os.path.join(base, "icons", f"{name}.png"))
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(here, "..", "app", "icons", f"{name}.png"))
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def mi(title, callback=None, icon=None, tooltip=None):
    """MenuItem con icono template (Lucide) y tooltip opcionales."""
    path = icon_path(icon) if icon else None
    if path:
        item = rumps.MenuItem(title, callback=callback, icon=path,
                              dimensions=ICON_DIMENSIONS, template=True)
    else:
        item = rumps.MenuItem(title, callback=callback)
    if tooltip:
        try:
            item._menuitem.setToolTip_(tooltip)
        except Exception:
            pass
    return item

def key_physically_down(vk):
    """Estado físico real de la tecla vía Quartz. None si no se puede saber."""
    try:
        import Quartz
        return bool(Quartz.CGEventSourceKeyState(
            Quartz.kCGEventSourceStateHIDSystemState, vk))
    except Exception:
        return None

# ── Diálogo translúcido con NSVisualEffectView (vibrancy) ─────────────────────

try:
    import objc
    from AppKit import (
        NSObject, NSWindow, NSVisualEffectView, NSScrollView, NSTextView,
        NSTextField, NSButton, NSFont, NSColor, NSApp,
        NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
        NSWindowStyleMaskFullSizeContentView, NSBackingStoreBuffered,
        NSVisualEffectBlendingModeBehindWindow, NSVisualEffectStateActive,
        NSBezelStyleRounded,
    )
    from Foundation import NSMakeRect, NSMakeSize
    _VIBRANCY_OK = True
except ImportError:
    _VIBRANCY_OK = False


if _VIBRANCY_OK:

    class _BtnHandler(NSObject):
        """Receptor ObjC para las acciones de los botones del diálogo vibrancy."""

        def init(self):
            self = objc.super(_BtnHandler, self).init()
            if self is None:
                return None
            self._callback = None
            return self

        @objc.python_method
        def set_callback(self, fn):
            self._callback = fn

        def buttonClicked_(self, sender):
            if self._callback:
                self._callback(int(sender.tag()))


    class VibrancyTranscriptDialog:
        """Ventana modal translúcida (NSVisualEffectView) para ver/editar transcripciones."""

        W, H = 560, 350

        def __init__(self, text):
            self._text          = text
            self._result_action = None
            self._window        = None
            self._text_view     = None
            self._handler       = None
            self._scroll        = None
            self._build()

        def _build(self):
            # Ventana con barra de título transparente y contenido a tamaño completo
            style = (
                NSWindowStyleMaskTitled
                | NSWindowStyleMaskClosable
                | NSWindowStyleMaskFullSizeContentView
            )
            self._window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                NSMakeRect(0, 0, self.W, self.H),
                style,
                NSBackingStoreBuffered,
                False,
            )
            self._window.setTitle_("Whisper Dictation VP")
            self._window.center()
            self._window.setReleasedWhenClosed_(False)
            self._window.setTitlebarAppearsTransparent_(True)
            self._window.setMovableByWindowBackground_(True)
            self._window.setOpaque_(False)
            self._window.setBackgroundColor_(NSColor.clearColor())

            # Fondo vibrancy — translúcido respecto a lo que hay detrás de la ventana
            fx = NSVisualEffectView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.W, self.H)
            )
            fx.setMaterial_(12)  # NSVisualEffectMaterialWindowBackground
            fx.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            fx.setState_(NSVisualEffectStateActive)
            self._window.setContentView_(fx)

            # ScrollView + NSTextView editable
            self._scroll = NSScrollView.alloc().initWithFrame_(
                NSMakeRect(20, 55, self.W - 40, self.H - 75)
            )
            self._scroll.setBorderType_(2)  # NSBezelBorder
            self._scroll.setHasVerticalScroller_(True)
            self._scroll.setHasHorizontalScroller_(False)
            self._scroll.setDrawsBackground_(False)

            self._text_view = NSTextView.alloc().initWithFrame_(
                NSMakeRect(0, 0, self.W - 60, self.H - 90)
            )
            self._text_view.setString_(self._text)
            self._text_view.setFont_(NSFont.systemFontOfSize_(13))
            self._text_view.setEditable_(True)
            self._text_view.setRichText_(False)
            self._text_view.setDrawsBackground_(False)
            self._text_view.setTextContainerInset_(NSMakeSize(6, 8))
            self._scroll.setDocumentView_(self._text_view)
            fx.addSubview_(self._scroll)

            # Handler de botones (NSObject compatible con ObjC actions)
            self._handler = _BtnHandler.alloc().init()
            self._handler.set_callback(self._on_button)

            buttons = [
                ("Cancelar", 20,              100, 0),
                ("Copiar",   self.W - 120,    100, 1),
            ]
            for title, x, w, tag in buttons:
                btn = NSButton.alloc().initWithFrame_(NSMakeRect(x, 14, w, 32))
                btn.setTitle_(title)
                btn.setBezelStyle_(NSBezelStyleRounded)
                btn.setTag_(tag)
                btn.setTarget_(self._handler)
                btn.setAction_(b"buttonClicked:")
                if tag == 1:
                    btn.setKeyEquivalent_("\r")   # Enter → Copiar
                elif tag == 0:
                    btn.setKeyEquivalent_("\x1b")  # Escape → Cancelar
                fx.addSubview_(btn)

        def _on_button(self, tag):
            self._result_action = {0: None, 1: "Copiar"}.get(tag)
            NSApp.stopModal()
            self._window.orderOut_(None)

        def run(self):
            """Muestra el diálogo modal. Devuelve (action, edited_text)."""
            NSApp.activateIgnoringOtherApps_(True)
            self._window.makeKeyAndOrderFront_(None)
            NSApp.runModalForWindow_(self._window)
            text = str(self._text_view.string()) if self._text_view else self._text
            return self._result_action, text


# ── Permiso de Accesibilidad ──────────────────────────────────────────────────

def check_accessibility(prompt=True):
    """Comprueba el permiso de Accesibilidad. Con prompt=True, macOS muestra el
    diálogo del sistema y añade la app a la lista de Accesibilidad."""
    try:
        from ApplicationServices import (
            AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt,
        )
        return bool(AXIsProcessTrustedWithOptions(
            {kAXTrustedCheckOptionPrompt: prompt}))
    except Exception:
        return True  # Si no se puede comprobar, seguimos sin bloquear la app


def acquire_single_instance_lock():
    """Garantiza una sola instancia (el instalador y el LaunchAgent pueden
    lanzar la app casi a la vez). Devuelve el fichero de lock o None."""
    import fcntl
    lock_path = os.path.expanduser("~/.whisper_dictation_vp.lock")
    try:
        f = open(lock_path, "w")
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except OSError:
        return None


# ── Config ────────────────────────────────────────────────────────────────────

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    config.setdefault("providers", {})
    config.setdefault("active_provider", os.environ.get("WHISPER_PROVIDER", ""))
    config.setdefault("language", "auto")
    config.setdefault("hotkey", "alt_r")
    config.setdefault("history", [])
    config.setdefault("ai_format", False)
    config.setdefault("dictionary", [])
    config.setdefault("check_updates", True)
    config.setdefault("ui_lang", system_ui_lang())
    # Migración única (v3.4): el modo Automático pasa a ser el predeterminado
    # también para configs existentes — quien quiera un idioma fijo lo
    # cambia una vez y no se vuelve a tocar
    if not config.get("migr_auto_340"):
        config["language"] = "auto"
        config["migr_auto_340"] = True
        save_config(config)
    if not config["providers"] and os.environ.get("GROQ_API_KEY"):
        config["providers"]["groq"] = os.environ.get("GROQ_API_KEY")
    if not config["providers"] and os.environ.get("WHISPER_API_KEY"):
        provider = os.environ.get("WHISPER_PROVIDER", "groq")
        config["providers"][provider] = os.environ.get("WHISPER_API_KEY")
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)

# ── Diálogos osascript (configuración) ───────────────────────────────────────
_active_dialogs: list[subprocess.Popen] = []
_dialogs_lock = threading.Lock()


def _osa_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _run_dialog(args):
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with _dialogs_lock:
        _active_dialogs.append(proc)
    try:
        out, _ = proc.communicate()
        return out.decode().strip()
    finally:
        with _dialogs_lock:
            try:
                _active_dialogs.remove(proc)
            except ValueError:
                pass

def close_all_dialogs():
    with _dialogs_lock:
        for proc in list(_active_dialogs):
            try:
                proc.terminate()
            except Exception:
                pass
        _active_dialogs.clear()

def dialog_input(prompt, default="", cancelable=True):
    buttons = '"Cancelar", "Continuar"' if cancelable else '"Continuar"'
    safe_prompt  = _osa_escape(prompt)
    safe_default = _osa_escape(default)
    return _run_dialog(["osascript", "-e",
        f'tell app "System Events"\n'
        f'  set r to display dialog "{safe_prompt}" default answer "{safe_default}" '
        f'with title "Whisper Dictation VP" buttons {{{buttons}}} default button "Continuar"\n'
        f'  if button returned of r is "Cancelar" then return ""\n'
        f'  return text returned of r\n'
        f'end tell'])

def dialog_text_view_fallback(text):
    """Fallback osascript si PyObjC no está disponible."""
    safe_text = _osa_escape(text)
    result = _run_dialog(["osascript", "-e",
        f'tell app "System Events"\n'
        f'  set r to display dialog "" '
        f'default answer "{safe_text}" '
        f'with title "Whisper Dictation VP" '
        f'buttons {{"Cancelar", "Copiar"}} default button "Copiar"\n'
        f'  if button returned of r is "Cancelar" then return "CANCEL"\n'
        f'  return (button returned of r) & "|" & (text returned of r)\n'
        f'end tell'])
    if not result or result == "CANCEL":
        return None, None
    parts = result.split("|", 1)
    return parts[0], parts[1] if len(parts) > 1 else text

def dialog_choice(prompt, *buttons):
    options    = [b for b in buttons if b != "Cancelar"]
    has_cancel = "Cancelar" in buttons
    safe_prompt = _osa_escape(prompt)

    if len(options) <= 2 and not has_cancel:
        btn_str = ", ".join(f'"{b}"' for b in buttons)
        return _run_dialog(["osascript", "-e",
            f'tell app "System Events" to return button returned of '
            f'(display dialog "{safe_prompt}" with title "Whisper Dictation VP" '
            f'buttons {{{btn_str}}} default button "{buttons[-1]}")'])
    elif len(options) <= 2:
        btn_str = ", ".join(f'"{b}"' for b in buttons)
        return _run_dialog(["osascript", "-e",
            f'tell app "System Events" to return button returned of '
            f'(display dialog "{safe_prompt}" with title "Whisper Dictation VP" '
            f'buttons {{{btn_str}}} default button "{options[-1]}")'])
    else:
        items_str = ", ".join(f'"{o}"' for o in options)
        result = _run_dialog(["osascript", "-e",
            f'set r to choose from list {{{items_str}}} '
            f'with title "Whisper Dictation VP" with prompt "{safe_prompt}" '
            f'OK button name "Seleccionar" cancel button name "Cancelar"\n'
            f'if r is false then return "Cancelar"\n'
            f'return item 1 of r'])
        return result if result else "Cancelar"

def dialog_info(msg):
    safe_msg = _osa_escape(msg)
    _run_dialog(["osascript", "-e",
        f'tell app "System Events" to display dialog "{safe_msg}" '
        f'with title "Whisper Dictation VP" buttons {{"OK"}} default button "OK"'])

def play_sound(sound):
    subprocess.Popen(["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def set_clipboard(text):
    """Copia al portapapeles vía NSPasteboard (inmune a problemas de locale;
    pbcopy como fallback con entorno UTF-8 explícito)."""
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, NSPasteboardTypeString)
        return
    except Exception:
        env = dict(os.environ)
        env["LANG"] = "en_US.UTF-8"
        subprocess.run(["pbcopy"], input=text.encode("utf-8"),
                       env=env, check=True)

# ── Transcripción ─────────────────────────────────────────────────────────────

def build_client(provider, api_key):
    if provider == "groq":
        from groq import Groq
        return Groq(api_key=api_key)
    elif provider == "openai":
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    elif provider == "deepgram":
        from deepgram import DeepgramClient
        return DeepgramClient(api_key=api_key)
    elif provider == "assemblyai":
        import assemblyai as aai
        aai.settings.api_key = api_key
        return aai
    return None

def transcribe(provider, client, path, language, dictionary=None):
    lang = None if language == "auto" else language
    # Whisper acepta un "prompt" que sesga la transcripción hacia vocabulario
    # conocido — lo usamos para el diccionario personal (nombres, tecnicismos)
    vocab_hint = ", ".join(dictionary) if dictionary else None
    if provider == "groq":
        with open(path, "rb") as f:
            kwargs = {"prompt": vocab_hint} if vocab_hint else {}
            r = client.audio.transcriptions.create(
                file=(os.path.basename(path), f, "audio/wav"),
                model="whisper-large-v3",
                language=lang,
                response_format="text",
                **kwargs,
            )
        return r.strip() if isinstance(r, str) else r.text.strip()
    elif provider == "openai":
        with open(path, "rb") as f:
            kwargs = {"prompt": vocab_hint} if vocab_hint else {}
            r = client.audio.transcriptions.create(
                model="whisper-1", file=f, language=lang, **kwargs)
        return r.text.strip()
    elif provider == "deepgram":
        with open(path, "rb") as f:
            data = f.read()
        response = client.listen.v1.media.transcribe_file(
            request=data,
            model="nova-2",
            language=lang or "es",
            smart_format=True,
        )
        return response.results.channels[0].alternatives[0].transcript.strip()
    elif provider == "assemblyai":
        import assemblyai as aai
        config = aai.TranscriptionConfig(
            language_code=lang or "es",
            speech_model=aai.SpeechModel.universal,
        )
        result = aai.Transcriber().transcribe(path, config=config)
        if result.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI error: {result.error}")
        return (result.text or "").strip()
    return ""


def ai_cleanup(provider, client, text, dictionary=None):
    """Post-procesa la transcripción con un LLM: quita muletillas, corrige
    puntuación y aplica el diccionario personal. Solo Groq y OpenAI (los dos
    tienen modelos de chat). Si algo falla, se devuelve el texto original."""
    dict_hint = ""
    if dictionary:
        dict_hint = (" Si aparecen palabras que suenan parecido a estas, "
                     f"usa la grafía exacta: {', '.join(dictionary)}.")
    system = (
        "Eres un corrector de dictado por voz. Recibes una transcripción en "
        "bruto y devuelves EXACTAMENTE el mismo contenido, limpio: elimina "
        "muletillas y repeticiones accidentales (eh, em, mmm, «o sea» "
        "duplicados), corrige puntuación, tildes y mayúsculas, y mantén el "
        "idioma original. NO resumas, NO añadas nada, NO cambies el "
        "significado, NO respondas al contenido." + dict_hint +
        " Devuelve solo el texto corregido, sin comillas ni explicaciones."
    )
    if provider == "groq":
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": text}],
            temperature=0.2,
        )
        cleaned = (r.choices[0].message.content or "").strip()
    elif provider == "openai":
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": text}],
            temperature=0.2,
        )
        cleaned = (r.choices[0].message.content or "").strip()
    else:
        return text
    return cleaned if cleaned else text

# ── App ───────────────────────────────────────────────────────────────────────

class WhisperDictationApp(rumps.App):

    def __init__(self):
        super().__init__(ICON_IDLE, quit_button=None)
        self.config      = load_config()
        self.lock        = threading.Lock()
        self.config_lock = threading.Lock()

        self.recording    = False
        self.audio_frames = []

        self._last_tap_time = 0.0
        self._last_tap_end  = 0.0
        self._suppress_until = 0.0

        self._ui_queue = queue.Queue()
        self._ui_timer = rumps.Timer(self._flush_ui_queue, 0.05)
        self._ui_timer.start()

        if not self.config["providers"]:
            self._setup_provider(first_run=True)

        if not self.config["active_provider"] or \
           self.config["active_provider"] not in self.config["providers"]:
            self.config["active_provider"] = list(self.config["providers"].keys())[0]
            save_config(self.config)

        self._build_client()
        self._build_menu()

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS,
            dtype=DTYPE, callback=self._audio_callback, blocksize=1024,
        )
        self.stream.start()

        # Permiso de Accesibilidad: comprobación SILENCIOSA primero. Solo si
        # falta, pedimos con el diálogo del sistema — y únicamente una vez por
        # versión, para no ser pesados en cada arranque.
        if not check_accessibility(prompt=False):
            dbg("accesibilidad NO concedida")
            if self.config.get("ax_prompted_version") != APP_VERSION:
                with self.config_lock:
                    self.config["ax_prompted_version"] = APP_VERSION
                    save_config(self.config)
                check_accessibility(prompt=True)
                threading.Thread(target=self._ax_help_dialog, daemon=True).start()
        else:
            dbg("accesibilidad OK")

        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

        # Segundo canal de escucha: NSEvent global monitor (API nativa de
        # macOS, solo requiere Accesibilidad). El event tap de pynput puede
        # crearse "muerto" en apps empaquetadas aunque el permiso esté
        # concedido; con dos canales y dedupe, si uno falla el otro funciona.
        self._ns_monitor = None
        try:
            from AppKit import NSEvent

            def _monitor_handler(event):
                try:
                    vk = int(event.keyCode())
                    flags = int(event.modifierFlags())
                    mask = NSEVENT_FLAG_MASKS.get(vk, 0)
                    self._handle_key_event(vk, bool(flags & mask), False,
                                           source="nsevent")
                except Exception as e:
                    dbg(f"monitor nsevent error: {e}")

            self._ns_monitor = NSEvent.\
                addGlobalMonitorForEventsMatchingMask_handler_(
                    NSEVENT_MASK_FLAGS_CHANGED, _monitor_handler)
            dbg(f"monitor NSEvent: {'activo' if self._ns_monitor else 'FALLÓ'}")
        except Exception as e:
            dbg(f"monitor NSEvent no disponible: {e}")

        dbg(f"app v{APP_VERSION} iniciada — hotkey={self.config.get('hotkey')} "
            f"(vk={self._current_hotkey_vk()}) proveedor={self.provider}")

        if os.path.exists(os.path.expanduser("~/.wdvp_selftest")):
            threading.Thread(target=self._selftest, daemon=True).start()

        self._update_available = None
        threading.Thread(target=self._update_check_loop, daemon=True).start()

    # ── Actualizaciones ───────────────────────────────────────────────────────

    def _update_check_loop(self):
        """Comprueba GitHub al arrancar y luego una vez al día. Si hay versión
        nueva: notificación de macOS + entrada en el menú para descargarla."""
        time.sleep(15)  # no competir con el arranque
        while True:
            if not self.config.get("check_updates", True):
                time.sleep(86400)
                continue
            try:
                latest = fetch_latest_version()
                if latest and version_tuple(latest) > version_tuple(APP_VERSION):
                    if self._update_available != latest:
                        self._update_available = latest
                        dbg(f"actualización disponible: v{latest}")
                        self._dispatch(self._build_menu)
                        try:
                            rumps.notification(
                                "Whisper Dictation VP",
                                self._t("notif_title").format(latest),
                                self._t("notif_body"))
                        except Exception as e:
                            dbg(f"notificación falló: {e}")
                else:
                    dbg(f"sin actualizaciones (última: v{latest})")
            except Exception as e:
                dbg(f"comprobación de updates falló: {e}")
            time.sleep(86400)

    def _open_download_page(self, _):
        subprocess.Popen(["open", DOWNLOAD_PAGE])

    def _selftest(self):
        """Diagnóstico: postea toques sintéticos del hotkey y deja en el log
        si el listener los recibe (llegan con injected=True y no disparan
        acciones). Se activa creando el fichero ~/.wdvp_selftest."""
        try:
            os.unlink(os.path.expanduser("~/.wdvp_selftest"))
        except OSError:
            pass
        time.sleep(4)
        # Los eventos del self-test no deben disparar grabaciones reales:
        # el canal NSEvent no distingue eventos sintéticos, así que abrimos
        # la ventana de supresión (se loguean igualmente, que es lo que importa)
        self._suppress_until = time.time() + 6
        try:
            import Quartz
            vk = self._current_hotkey_vk()
            masks = {55: Quartz.kCGEventFlagMaskCommand,
                     54: Quartz.kCGEventFlagMaskCommand,
                     58: Quartz.kCGEventFlagMaskAlternate,
                     61: Quartz.kCGEventFlagMaskAlternate,
                     59: Quartz.kCGEventFlagMaskControl,
                     62: Quartz.kCGEventFlagMaskControl}
            dbg(f"SELFTEST: posteando 2 toques sintéticos de vk={vk}")
            for _ in range(2):
                for down in (True, False):
                    ev = Quartz.CGEventCreateKeyboardEvent(None, vk, down)
                    Quartz.CGEventSetType(ev, Quartz.kCGEventFlagsChanged)
                    Quartz.CGEventSetFlags(ev, masks.get(vk, 0) if down else 0)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
                    time.sleep(0.08)
                time.sleep(0.15)
            dbg("SELFTEST: enviados — si arriba hay eventos injected=True, "
                "el listener funciona")
        except Exception as e:
            dbg(f"SELFTEST error: {e}")

    def _ax_help_dialog(self):
        choice = dialog_choice(
            self._t("ax_help"),
            self._t("ax_open"), self._t("ok"))
        if choice == self._t("ax_open"):
            subprocess.Popen(["open",
                "x-apple.systempreferences:com.apple.preference.security"
                "?Privacy_Accessibility"])

    # ── UI dispatch ───────────────────────────────────────────────────────────

    def _dispatch(self, fn, *args):
        self._ui_queue.put((fn, args))

    def _flush_ui_queue(self, _):
        while True:
            try:
                fn, args = self._ui_queue.get_nowait()
                fn(*args)
            except queue.Empty:
                break

    def _set_title(self, icon):
        self.title = icon

    # ── Client & menu ─────────────────────────────────────────────────────────

    def _build_client(self):
        provider      = self.config["active_provider"]
        api_key       = self.config["providers"].get(provider, "")
        self.provider = provider
        self.client   = build_client(provider, api_key)

    # ── i18n helpers ──────────────────────────────────────────────────────────

    def _t(self, key):
        lang = self.config.get("ui_lang", "es")
        return TR.get(lang, TR["es"]).get(key, TR["es"].get(key, key))

    def _langs(self):
        return LANGUAGES_I18N.get(self.config.get("ui_lang", "es"),
                                  LANGUAGES_I18N["es"])

    def _set_ui_lang(self, code):
        if code == self.config.get("ui_lang"):
            return
        with self.config_lock:
            self.config["ui_lang"] = code
            save_config(self.config)
        self._build_menu()

    def _build_menu(self):
        t = self._t
        active_provider = self.config["active_provider"]
        active_lang     = self.config["language"]
        hotkey_name     = t("hotkeys").get(self.config["hotkey"],
                                           self.config["hotkey"])

        # ── Submenú Proveedor ─────────────────────────────────────────────────
        configured = list(self.config["providers"].keys())
        active_provider_name = PROVIDERS.get(active_provider, {}).get("name", active_provider)
        active_lang_name     = self._langs().get(active_lang, active_lang)
        provider_menu = mi(f"{t('provider')}: {active_provider_name}", icon="cloud")
        for p in configured:
            name = PROVIDERS.get(p, {}).get("name", p)
            mark = "✓ " if p == active_provider else "    "
            if len(configured) > 1:
                provider_menu.add(rumps.MenuItem(
                    f"{mark}{name}",
                    callback=lambda _, prov=p: self._switch_provider(prov)
                ))
            else:
                provider_menu.add(rumps.MenuItem(f"{mark}{name}"))

        # ── Submenú Idioma ────────────────────────────────────────────────────
        lang_menu = mi(f"{t('language')}: {active_lang_name}", icon="languages",
                       tooltip=t("tip_language"))
        for key, name in self._langs().items():
            mark = "✓ " if key == active_lang else "    "
            lang_menu.add(rumps.MenuItem(
                f"{mark}{name}",
                callback=lambda _, k=key: self._switch_language(k)
            ))

        # ── Submenú Historial ─────────────────────────────────────────────────
        history_menu = mi(t("history"), icon="history", tooltip=t("tip_history"))
        history = self.config.get("history", [])
        if history:
            for item in history:
                short = item[:65] + "…" if len(item) > 65 else item
                item_menu = rumps.MenuItem(short)
                item_menu.add(rumps.MenuItem(
                    t("copy"),
                    callback=lambda _, x=item: self._copy_history_item(x)
                ))
                item_menu.add(rumps.MenuItem(
                    t("open_edit"),
                    callback=lambda _, x=item: threading.Thread(
                        target=self._show_history_item, args=(x,), daemon=True
                    ).start()
                ))
                history_menu.add(item_menu)
            history_menu.add(None)
            history_menu.add(rumps.MenuItem(
                t("clear_history"),
                callback=lambda _: self._clear_history()
            ))
        else:
            history_menu.add(rumps.MenuItem(t("empty")))

        # ── Submenú Diccionario personal ──────────────────────────────────────
        dictionary = self.config.get("dictionary", [])
        dict_menu = mi(f"{t('dictionary')} ({len(dictionary)})", icon="book-open",
                       tooltip=t("tip_dict"))
        for word in dictionary:
            word_item = rumps.MenuItem(word)
            word_item.add(rumps.MenuItem(
                t("delete"),
                callback=lambda _, w=word: self._remove_dictionary_word(w)
            ))
            dict_menu.add(word_item)
        if dictionary:
            dict_menu.add(None)
        dict_menu.add(rumps.MenuItem(
            t("add_word"),
            callback=lambda _: threading.Thread(
                target=self._add_dictionary_word, daemon=True).start()
        ))

        # ── Toggles ───────────────────────────────────────────────────────────
        ai_on = self.config.get("ai_format", False)
        ai_available = active_provider in ("groq", "openai")
        ai_label = f"{t('ai_format')}: {t('yes') if ai_on else t('no')}"
        if not ai_available:
            ai_label += t("ai_requires")
        ai_item = mi(ai_label,
                     callback=self._toggle_ai_format if ai_available else None,
                     icon="sparkles", tooltip=t("tip_ai"))

        updates_on = self.config.get("check_updates", True)
        updates_item = mi(
            f"{t('updates')}: {t('yes') if updates_on else t('no')}",
            callback=self._toggle_check_updates,
            icon="bell", tooltip=t("tip_updates"))

        # Submenú Interfaz: idiomas de la UI con marca en el activo
        ui_lang_item = mi(t("ui_menu"), icon="globe", tooltip=t("tip_ui"))
        active_ui = self.config.get("ui_lang", "es")
        for code, label in (("es", "Español"), ("en", "English")):
            mark = "✓ " if code == active_ui else "    "
            ui_lang_item.add(rumps.MenuItem(
                f"{mark}{label}",
                callback=lambda _, c=code: self._set_ui_lang(c)))

        # ── Menú principal ────────────────────────────────────────────────────
        update_items = []
        if getattr(self, "_update_available", None):
            update_items = [mi(
                t("new_version").format(self._update_available),
                callback=self._open_download_page, icon="download")]

        self.menu.clear()
        self.menu = [
            rumps.MenuItem(f"Whisper Dictation VP v{APP_VERSION}"),
            *update_items,
            None,
            provider_menu,
            lang_menu,
            mi(t("hotkey_line").format(hotkey_name), icon="keyboard",
               tooltip=t("tip_hotkey")),
            None,
            ai_item,
            dict_menu,
            updates_item,
            ui_lang_item,
            None,
            history_menu,
            None,
            mi(t("settings"), callback=self._open_settings, icon="settings"),
            None,
            mi(t("quit"), callback=self._quit, icon="power"),
        ]

    # ── Formato IA y diccionario ──────────────────────────────────────────────

    def _toggle_ai_format(self, _):
        with self.config_lock:
            self.config["ai_format"] = not self.config.get("ai_format", False)
            save_config(self.config)
        self._build_menu()

    def _toggle_check_updates(self, _):
        with self.config_lock:
            self.config["check_updates"] = not self.config.get("check_updates", True)
            save_config(self.config)
        self._build_menu()

    def _add_dictionary_word(self):
        word = dialog_input(self._t("dlg_add_word")).strip()
        if not word:
            return
        with self.config_lock:
            dictionary = self.config.get("dictionary", [])
            if word not in dictionary:
                dictionary.append(word)
                self.config["dictionary"] = dictionary
                save_config(self.config)
        self._dispatch(self._build_menu)

    def _remove_dictionary_word(self, word):
        with self.config_lock:
            dictionary = self.config.get("dictionary", [])
            if word in dictionary:
                dictionary.remove(word)
                self.config["dictionary"] = dictionary
                save_config(self.config)
        self._dispatch(self._build_menu)

    # ── Cambio rápido desde el menú ───────────────────────────────────────────

    def _switch_provider(self, provider):
        if provider == self.config["active_provider"]:
            return
        self.config["active_provider"] = provider
        save_config(self.config)
        self._build_client()
        self._build_menu()

    def _switch_language(self, lang):
        if lang == self.config["language"]:
            return
        self.config["language"] = lang
        save_config(self.config)
        self._build_menu()

    # ── Historial interactivo ─────────────────────────────────────────────────

    def _copy_history_item(self, text):
        set_clipboard(text)
        play_sound("Tink")

    def _show_history_item(self, text):
        """Abre la transcripción en un diálogo translúcido (o fallback osascript)."""
        if _VIBRANCY_OK:
            result_holder = [None, text]
            done = threading.Event()

            def show_on_main():
                try:
                    dlg = VibrancyTranscriptDialog(text)
                    action, edited = dlg.run()
                    result_holder[0] = action
                    result_holder[1] = edited
                except Exception as e:
                    print(f"⚠ Vibrancy dialog error: {e}")
                finally:
                    done.set()

            self._dispatch(show_on_main)
            done.wait()
            action, edited = result_holder
        else:
            action, edited = dialog_text_view_fallback(text)

        if action is None:
            return

        target = edited if edited else text
        set_clipboard(target)
        play_sound("Tink")

        # Actualizar historial si se editó el texto
        if edited and edited != text:
            with self.config_lock:
                history = self.config.get("history", [])
                try:
                    idx = history.index(text)
                    history[idx] = edited
                    self.config["history"] = history
                    save_config(self.config)
                except ValueError:
                    pass
            self._dispatch(self._build_menu)

    def _clear_history(self):
        with self.config_lock:
            self.config["history"] = []
            save_config(self.config)
        self._dispatch(self._build_menu)

    # ── Configuración ─────────────────────────────────────────────────────────

    def _open_settings(self, _):
        threading.Thread(target=self._settings_thread, daemon=True).start()

    def _settings_thread(self):
        choice = dialog_choice(
            self._t("dlg_settings_what"),
            self._t("cancel"), self._t("dlg_hotkey_option"), "APIs"
        )
        if choice == "APIs":
            self._settings_apis()
        elif choice == self._t("dlg_hotkey_option"):
            self._settings_hotkey()

    def _settings_apis(self):
        providers  = self.config["providers"]
        configured = [PROVIDERS[p]["name"] for p in providers if p in PROVIDERS]

        t = self._t
        options = []
        if configured:
            options.append(t("dlg_manage"))
        options.append(t("dlg_add_api"))
        options.append(t("cancel"))

        choice = dialog_choice(
            t("dlg_apis_header") + "\n" +
            ("\n".join(f"• {n}" for n in configured) if configured else t("dlg_none")) +
            "\n\n" + t("dlg_what_do"),
            *reversed(options)
        )
        if choice == t("dlg_add_api"):
            self._setup_provider()
        elif choice == t("dlg_manage"):
            self._manage_providers()

    def _manage_providers(self):
        providers = [p for p in self.config["providers"] if p in PROVIDERS]
        if not providers:
            return
        t = self._t
        names  = [PROVIDERS[p]["name"] for p in providers]
        choice = dialog_choice(t("dlg_select_manage"), t("cancel"), *names)
        if not choice or choice == t("cancel"):
            return
        provider = next((p for p in providers if PROVIDERS[p]["name"] == choice), None)
        if not provider:
            return

        active_mark = t("dlg_active") if provider == self.config["active_provider"] else ""
        action = dialog_choice(
            f"{t('provider')}: {choice}{active_mark}\n\n{t('dlg_what_do')}",
            t("cancel"), t("delete"), t("dlg_change_key"), t("dlg_use_this")
        )
        if action == t("dlg_use_this"):
            self._switch_provider(provider)
        elif action == t("dlg_change_key"):
            self._setup_provider(edit=provider)
        elif action == t("delete"):
            confirm = dialog_choice(t("dlg_confirm_delete").format(choice),
                                    t("cancel"), t("delete"))
            if confirm == t("delete"):
                del self.config["providers"][provider]
                if self.config["active_provider"] == provider:
                    self.config["active_provider"] = (
                        list(self.config["providers"].keys())[0]
                        if self.config["providers"] else ""
                    )
                save_config(self.config)
                self._build_client()
                self._dispatch(self._build_menu)

    def _setup_provider(self, first_run=False, edit=None):
        if edit:
            provider = edit
        else:
            available = [p for p in PROVIDERS if p not in self.config["providers"]]
            if not available:
                dialog_info(self._t("dlg_all_configured"))
                return
            names  = [PROVIDERS[p]["name"] for p in available]
            choice = dialog_choice(self._t("dlg_select_provider"),
                                   self._t("cancel"), *names)
            if not choice or choice == self._t("cancel"):
                if first_run and not self.config["providers"]:
                    sys.exit(0)
                return
            provider = next((p for p in available if PROVIDERS[p]["name"] == choice), None)
            if not provider:
                return

        info    = PROVIDERS[provider]
        current = self.config["providers"].get(provider, "")
        api_key = dialog_input(
            self._t("dlg_api_key").format(info["name"], info["url"]),
            default=current or info["placeholder"]
        )
        if not api_key or api_key == info["placeholder"]:
            if first_run and not self.config["providers"]:
                sys.exit(0)
            return

        self.config["providers"][provider] = api_key
        if not self.config["active_provider"]:
            self.config["active_provider"] = provider
        save_config(self.config)
        self._build_client()
        self._dispatch(self._build_menu)

    def _settings_hotkey(self):
        names  = [self._t("hotkeys")[k] for k in HOTKEY_CHOICES]
        choice = dialog_choice(self._t("dlg_select_hotkey"),
                               self._t("cancel"), *names)
        if not choice or choice == self._t("cancel"):
            return
        self.config["hotkey"] = HOTKEY_CHOICES[names.index(choice)]
        save_config(self.config)
        self._dispatch(self._build_menu)

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status):
        with self.lock:
            if self.recording:
                self.audio_frames.append(indata.copy())

    def _current_hotkey_vk(self):
        return HOTKEY_VKS.get(self.config.get("hotkey", "alt_r"), 61)

    # ── Teclado ───────────────────────────────────────────────────────────────
    # Motor por toques: no confiamos en la dirección press/release que reporta
    # pynput (en apps empaquetadas los modificadores pueden llegar como release
    # sin press). En cada evento consultamos el estado FÍSICO real de la tecla
    # (Quartz) y detectamos el fin de cada toque. Un toque para la grabación;
    # dos toques seguidos la inician.

    def _on_press(self, key, injected=False):
        vk = getattr(getattr(key, "value", key), "vk", None)
        self._handle_key_event(vk, True, injected, source="pynput")

    def _on_release(self, key, injected=False):
        vk = getattr(getattr(key, "value", key), "vk", None)
        self._handle_key_event(vk, False, injected, source="pynput")

    def _handle_key_event(self, vk, reported_press, injected, source="?"):
        if vk is None or vk != self._current_hotkey_vk():
            return

        down = key_physically_down(vk)
        dbg(f"hotkey ev[{source}]: vk={vk} reported_press={reported_press} "
            f"injected={injected} phys_down={down}")

        # Ignorar eventos sintéticos (p. ej. nuestro propio Cmd+V al pegar)
        if injected:
            return
        # Ventana de gracia tras pegar, por si el evento no viene marcado
        if time.time() < self._suppress_until:
            return

        # Dirección efectiva: estado físico real; si no disponible, lo reportado
        is_down = down if down is not None else reported_press
        if is_down:
            return  # el toque aún no ha terminado

        now = time.time()
        # Dedupe: si press+release llegan ya con la tecla soltada, ambos
        # eventos se procesan con milisegundos de diferencia
        if now - self._last_tap_end < 0.05:
            return
        self._last_tap_end = now
        self._register_tap(now)

    def _register_tap(self, now):
        with self.lock:
            if self.recording:
                self.recording      = False
                frames              = list(self.audio_frames)
                self._last_tap_time = 0.0
                dbg("tap: STOP grabación")
                self._dispatch(self._set_title, ICON_PROCESSING)
                threading.Thread(target=self._process, args=(frames,),
                                 daemon=True).start()
                return

        if now - self._last_tap_time <= DOUBLE_TAP_WINDOW:
            self._last_tap_time = 0.0
            with self.lock:
                self.recording = True
                self.audio_frames.clear()
            dbg("doble tap: START grabación")
            play_sound("Tink")
            self._dispatch(self._set_title, ICON_RECORDING)
        else:
            self._last_tap_time = now

    # ── Procesado ─────────────────────────────────────────────────────────────

    def _process(self, frames):
        path = None
        try:
            if not frames:
                return

            audio    = np.concatenate(frames, axis=0)
            duration = len(audio) / SAMPLE_RATE

            if duration < 0.3:
                play_sound("Funk")
                print(f"⚠ Grabación demasiado corta ({duration:.2f}s), ignorada")
                return

            rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
            if rms < 2:
                print(f"⚠ Silencio detectado (RMS={rms:.1f}), ignorado")
                return

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = tmp.name
            with wave.open(path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio.tobytes())

            dictionary = self.config.get("dictionary", [])
            text = transcribe(self.provider, self.client, path,
                              self.config.get("language", "es"), dictionary)
            dbg(f"transcripción: {len(text)} caracteres [{duration:.1f}s audio]")

            if text and self.config.get("ai_format"):
                try:
                    text = ai_cleanup(self.provider, self.client, text, dictionary)
                    dbg("formato IA aplicado")
                except Exception as e:
                    dbg(f"formato IA falló (uso texto original): {e}")

            if text:
                with self.config_lock:
                    history = self.config.get("history", [])
                    history.insert(0, text)
                    self.config["history"] = history[:HISTORY_MAX]
                    save_config(self.config)
                self._dispatch(self._build_menu)

                set_clipboard(text)
                # Nuestro Cmd+V sintético no debe contar como toque del hotkey
                self._suppress_until = time.time() + 1.0
                subprocess.run(["osascript", "-e",
                    'tell application "System Events" to keystroke "v" using command down'],
                    check=True)
                play_sound("Pop")
            else:
                play_sound("Funk")
                dbg("transcripción vacía — sin texto detectado")

        except Exception as e:
            play_sound("Basso")
            dbg(f"error de transcripción: {e}")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)
            self._dispatch(self._set_title, ICON_IDLE)

    # ── Salir ─────────────────────────────────────────────────────────────────

    def _quit(self, _):
        close_all_dialogs()
        self._ui_timer.stop()
        try:
            self._listener.stop()
        except Exception:
            pass
        try:
            if self._ns_monitor is not None:
                from AppKit import NSEvent
                NSEvent.removeMonitor_(self._ns_monitor)
        except Exception:
            pass
        self.stream.stop()
        self.stream.close()
        rumps.quit_application()


if __name__ == "__main__":
    _instance_lock = acquire_single_instance_lock()
    if _instance_lock is None:
        dbg("instancia duplicada — saliendo")
        sys.exit(0)
    WhisperDictationApp().run()
