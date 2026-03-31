#!/usr/bin/env python3
"""
Whisper Dictation VP — Dictado por voz para macOS.
Doble-toque Option derecho para iniciar grabación. Toque simple para detener.
Diseñado por Vasyl Pavlyuchok & Claude — v2.4
"""

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

LANGUAGES = {
    "auto":  "Automático",
    "es":    "Español",
    "en":    "Inglés",
    "fr":    "Francés",
    "de":    "Alemán",
    "it":    "Italiano",
    "pt":    "Portugués",
}

HOTKEYS = {
    "alt_r":   keyboard.Key.alt_r,
    "alt":     keyboard.Key.alt,
    "ctrl":    keyboard.Key.ctrl,
    "cmd":     keyboard.Key.cmd,
}
HOTKEY_NAMES = {
    "alt_r":   "Option derecho",
    "alt":     "Option izquierdo",
    "ctrl":    "Control",
    "cmd":     "Command",
}

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


# ── Config ────────────────────────────────────────────────────────────────────

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    config.setdefault("providers", {})
    config.setdefault("active_provider", os.environ.get("WHISPER_PROVIDER", ""))
    config.setdefault("language", "es")
    config.setdefault("hotkey", "alt_r")
    config.setdefault("history", [])
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
        return DeepgramClient(api_key)
    elif provider == "assemblyai":
        import assemblyai as aai
        aai.settings.api_key = api_key
        return aai
    return None

def transcribe(provider, client, path, language):
    lang = None if language == "auto" else language
    if provider == "groq":
        with open(path, "rb") as f:
            r = client.audio.transcriptions.create(
                file=(os.path.basename(path), f, "audio/wav"),
                model="whisper-large-v3",
                language=lang,
                response_format="text",
            )
        return r.strip() if isinstance(r, str) else r.text.strip()
    elif provider == "openai":
        with open(path, "rb") as f:
            r = client.audio.transcriptions.create(
                model="whisper-1", file=f, language=lang)
        return r.text.strip()
    elif provider == "deepgram":
        from deepgram import PrerecordedOptions
        with open(path, "rb") as f:
            data = f.read()
        options = PrerecordedOptions(model="nova-2", language=lang or "es")
        response = client.listen.prerecorded.v("1").transcribe_file(
            {"buffer": data, "mimetype": "audio/wav"}, options)
        return response["results"]["channels"][0]["alternatives"][0]["transcript"].strip()
    elif provider == "assemblyai":
        import assemblyai as aai
        config = aai.TranscriptionConfig(language_code=lang or "es")
        t = aai.Transcriber()
        result = t.transcribe(path, config=config)
        return result.text.strip()
    return ""

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
        self._key_down      = False
        self._stop_tap      = False

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

        try:
            device_info = sd.query_devices(None, 'input')
            self._capture_rate = int(device_info['default_samplerate'])
        except Exception:
            self._capture_rate = SAMPLE_RATE

        self.stream = sd.InputStream(
            samplerate=self._capture_rate, channels=CHANNELS,
            dtype=DTYPE, callback=self._audio_callback, blocksize=1024,
        )
        self.stream.start()

        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

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

    def _build_menu(self):
        active_provider = self.config["active_provider"]
        active_lang     = self.config["language"]
        hotkey_name     = HOTKEY_NAMES.get(self.config["hotkey"], self.config["hotkey"])

        # ── Submenú Proveedor ─────────────────────────────────────────────────
        configured = list(self.config["providers"].keys())
        active_provider_name = PROVIDERS.get(active_provider, {}).get("name", active_provider)
        active_lang_name     = LANGUAGES.get(active_lang, active_lang)
        provider_menu = rumps.MenuItem(f"Proveedor: {active_provider_name}")
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
        lang_menu = rumps.MenuItem(f"Idioma: {active_lang_name}")
        for key, name in LANGUAGES.items():
            mark = "✓ " if key == active_lang else "    "
            lang_menu.add(rumps.MenuItem(
                f"{mark}{name}",
                callback=lambda _, k=key: self._switch_language(k)
            ))

        # ── Submenú Historial ─────────────────────────────────────────────────
        history_menu = rumps.MenuItem("Historial")
        history = self.config.get("history", [])
        if history:
            for item in history:
                short = item[:65] + "…" if len(item) > 65 else item
                history_menu.add(rumps.MenuItem(
                    short,
                    callback=lambda _, t=item: threading.Thread(
                        target=self._show_history_item, args=(t,), daemon=True
                    ).start()
                ))
            history_menu.add(None)
            history_menu.add(rumps.MenuItem(
                "Limpiar historial",
                callback=lambda _: self._clear_history()
            ))
        else:
            history_menu.add(rumps.MenuItem("(vacío)"))

        # ── Menú principal ────────────────────────────────────────────────────
        self.menu.clear()
        self.menu = [
            rumps.MenuItem("Whisper Dictation VP v2.4"),
            None,
            provider_menu,
            lang_menu,
            rumps.MenuItem(f"Tecla: {hotkey_name} (doble-toque)"),
            None,
            history_menu,
            None,
            rumps.MenuItem("⚙️ Configuración", callback=self._open_settings),
            None,
            rumps.MenuItem("Salir", callback=self._quit),
        ]

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
        subprocess.run(["pbcopy"], input=target.encode("utf-8"))
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
            "¿Qué quieres configurar?",
            "Cancelar", "Tecla de activación", "APIs"
        )
        if choice == "APIs":
            self._settings_apis()
        elif choice == "Tecla de activación":
            self._settings_hotkey()

    def _settings_apis(self):
        providers  = self.config["providers"]
        configured = [PROVIDERS[p]["name"] for p in providers if p in PROVIDERS]

        options = []
        if configured:
            options.append("Gestionar existentes")
        options.append("Añadir nueva API")
        options.append("Cancelar")

        choice = dialog_choice(
            "APIs configuradas:\n" +
            ("\n".join(f"• {n}" for n in configured) if configured else "(ninguna)") +
            "\n\n¿Qué quieres hacer?",
            *reversed(options)
        )
        if choice == "Añadir nueva API":
            self._setup_provider()
        elif choice == "Gestionar existentes":
            self._manage_providers()

    def _manage_providers(self):
        providers = [p for p in self.config["providers"] if p in PROVIDERS]
        if not providers:
            return
        names  = [PROVIDERS[p]["name"] for p in providers]
        choice = dialog_choice("Selecciona el proveedor a gestionar:", "Cancelar", *names)
        if not choice or choice == "Cancelar":
            return
        provider = next((p for p in providers if PROVIDERS[p]["name"] == choice), None)
        if not provider:
            return

        active_mark = " (activo)" if provider == self.config["active_provider"] else ""
        action = dialog_choice(
            f"Proveedor: {choice}{active_mark}\n\n¿Qué quieres hacer?",
            "Cancelar", "Eliminar", "Cambiar API key", "Usar este"
        )
        if action == "Usar este":
            self._switch_provider(provider)
        elif action == "Cambiar API key":
            self._setup_provider(edit=provider)
        elif action == "Eliminar":
            confirm = dialog_choice(f"¿Eliminar {choice}?", "Cancelar", "Eliminar")
            if confirm == "Eliminar":
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
                dialog_info("Ya tienes todos los proveedores configurados.")
                return
            names  = [PROVIDERS[p]["name"] for p in available]
            choice = dialog_choice("Selecciona el proveedor de transcripción:", "Cancelar", *names)
            if not choice or choice == "Cancelar":
                if first_run and not self.config["providers"]:
                    sys.exit(0)
                return
            provider = next((p for p in available if PROVIDERS[p]["name"] == choice), None)
            if not provider:
                return

        info    = PROVIDERS[provider]
        current = self.config["providers"].get(provider, "")
        api_key = dialog_input(
            f"API Key de {info['name']}\n({info['url']}):",
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
        names  = list(HOTKEY_NAMES.values())
        keys   = list(HOTKEY_NAMES.keys())
        choice = dialog_choice("Selecciona la tecla de activación:", "Cancelar", *names)
        if not choice or choice == "Cancelar":
            return
        self.config["hotkey"] = keys[names.index(choice)]
        save_config(self.config)
        self._dispatch(self._build_menu)

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status):
        with self.lock:
            if self.recording:
                self.audio_frames.append(indata.copy())

    def _current_hotkey(self):
        return HOTKEYS.get(self.config.get("hotkey", "alt_r"), keyboard.Key.alt_r)

    # ── Teclado ───────────────────────────────────────────────────────────────

    def _on_press(self, key):
        if key != self._current_hotkey():
            return
        if self._key_down:
            return
        self._key_down = True
        self._stop_tap = False

        with self.lock:
            if self.recording:
                self._stop_tap = True
                self.recording = False
                frames         = list(self.audio_frames)
                self._dispatch(self._set_title, ICON_PROCESSING)
                threading.Thread(target=self._process, args=(frames,), daemon=True).start()

    def _on_release(self, key):
        if key != self._current_hotkey():
            return
        self._key_down = False

        if self._stop_tap:
            self._stop_tap = False
            return

        now = time.time()
        if now - self._last_tap_time <= DOUBLE_TAP_WINDOW:
            self._last_tap_time = 0.0
            with self.lock:
                self.recording = True
                self.audio_frames.clear()
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

            # Remuestrear a 16kHz si la captura fue a otra frecuencia (evita
            # el resampling interno de macOS que degrada la calidad)
            if self._capture_rate != SAMPLE_RATE:
                flat = audio.flatten().astype(np.float32)
                n_out = int(len(flat) * SAMPLE_RATE / self._capture_rate)
                audio = np.interp(
                    np.linspace(0, len(flat) - 1, n_out),
                    np.arange(len(flat)),
                    flat
                ).astype(np.int16).reshape(-1, 1)

            duration = len(audio) / SAMPLE_RATE

            if duration < 0.3:
                play_sound("Funk")
                print(f"⚠ Grabación demasiado corta ({duration:.2f}s), ignorada")
                return

            # Detección de silencio: sin voz → no llamar a la API
            rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
            if rms < 300:
                print(f"⚠ Audio silencioso (RMS={rms:.0f}), ignorado")
                return

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = tmp.name
            with wave.open(path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio.tobytes())

            text = transcribe(self.provider, self.client, path,
                              self.config.get("language", "es"))

            if text:
                with self.config_lock:
                    history = self.config.get("history", [])
                    history.insert(0, text)
                    self.config["history"] = history[:HISTORY_MAX]
                    save_config(self.config)
                self._dispatch(self._build_menu)

                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
                subprocess.run(["osascript", "-e",
                    'tell application "System Events" to keystroke "v" using command down'],
                    check=True)
                play_sound("Pop")
                print(f"✓ [{duration:.1f}s] {text}")
            else:
                play_sound("Funk")
                print("⚠ Transcripción vacía — sin texto detectado")

        except Exception as e:
            play_sound("Basso")
            print(f"✗ Error de transcripción: {e}")
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
        self.stream.stop()
        self.stream.close()
        rumps.quit_application()


if __name__ == "__main__":
    WhisperDictationApp().run()
