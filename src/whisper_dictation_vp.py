#!/usr/bin/env python3
"""
Whisper Dictation VP — Dictado por voz para macOS.
Manten Option derecho para grabar. Suelta para transcribir y pegar.
Disenado por Vasyl Pavlyuchok & Claude — v2.0
"""

import os, sys, tempfile, threading, subprocess, json, wave
import rumps, numpy as np, sounddevice as sd
from pynput import keyboard
from dotenv import load_dotenv
load_dotenv()

CONFIG_FILE     = os.path.expanduser("~/.whisper_dictation_vp.json")
HISTORY_MAX     = 10
SAMPLE_RATE     = 16000
CHANNELS        = 1
DTYPE           = "int16"
ICON_IDLE       = "🎙"
ICON_RECORDING  = "⭕"
ICON_PROCESSING = "⏳"

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
    # Compatibilidad con v1.x
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

# ── Diálogos ─────────────────────────────────────────────────────────────────
# Registro global de procesos de diálogo activos para poder cerrarlos al salir
_active_dialogs: list[subprocess.Popen] = []
_dialogs_lock = threading.Lock()

def _run_dialog(args):
    """Ejecuta un osascript, lo registra y devuelve stdout."""
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
    """Cierra todos los diálogos abiertos."""
    with _dialogs_lock:
        for proc in list(_active_dialogs):
            try:
                proc.terminate()
            except Exception:
                pass
        _active_dialogs.clear()

def dialog_input(prompt, default="", cancelable=True):
    buttons = '"Cancelar", "Continuar"' if cancelable else '"Continuar"'
    return _run_dialog(["osascript", "-e",
        f'tell app "System Events"\n'
        f'  set r to display dialog "{prompt}" default answer "{default}" '
        f'with title "Whisper Dictation VP" buttons {{{buttons}}} default button "Continuar"\n'
        f'  if button returned of r is "Cancelar" then return ""\n'
        f'  return text returned of r\n'
        f'end tell'])

def dialog_choice(prompt, *buttons):
    # Filtrar el botón Cancelar de las opciones reales
    options = [b for b in buttons if b != "Cancelar"]
    has_cancel = "Cancelar" in buttons

    if len(options) <= 2 and not has_cancel:
        # Diálogo simple con botones (máx 3)
        btn_str = ", ".join(f'"{b}"' for b in buttons)
        return _run_dialog(["osascript", "-e",
            f'tell app "System Events" to return button returned of '
            f'(display dialog "{prompt}" with title "Whisper Dictation VP" '
            f'buttons {{{btn_str}}} default button "{buttons[-1]}")'])
    elif len(options) <= 2:
        # Hasta 3 botones incluyendo Cancelar
        btn_str = ", ".join(f'"{b}"' for b in buttons)
        return _run_dialog(["osascript", "-e",
            f'tell app "System Events" to return button returned of '
            f'(display dialog "{prompt}" with title "Whisper Dictation VP" '
            f'buttons {{{btn_str}}} default button "{options[-1]}")'])
    else:
        # Muchas opciones: usar choose from list
        items_str = ", ".join(f'"{o}"' for o in options)
        cancel_str = "with cancel button" if has_cancel else ""
        result = _run_dialog(["osascript", "-e",
            f'set r to choose from list {{{items_str}}} '
            f'with title "Whisper Dictation VP" with prompt "{prompt}" '
            f'OK button name "Seleccionar" cancel button name "Cancelar"\n'
            f'if r is false then return "Cancelar"\n'
            f'return item 1 of r'])
        return result if result else "Cancelar"

def dialog_info(msg):
    _run_dialog(["osascript", "-e",
        f'tell app "System Events" to display dialog "{msg}" '
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
        from deepgram import PrerecordedOptions, FileSource
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
        self.config   = load_config()
        self.lock     = threading.Lock()
        self.recording    = False
        self.audio_frames = []

        # Si no hay ningún proveedor configurado, pedir uno al arrancar
        if not self.config["providers"]:
            self._setup_provider(first_run=True)

        # Si no hay proveedor activo, usar el primero disponible
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
        threading.Thread(target=self._start_listener, daemon=True).start()

    def _build_client(self):
        provider = self.config["active_provider"]
        api_key  = self.config["providers"].get(provider, "")
        self.provider = provider
        self.client   = build_client(provider, api_key)

    def _build_menu(self):
        provider_name = PROVIDERS.get(self.provider, {}).get("name", self.provider)
        lang_name     = LANGUAGES.get(self.config["language"], self.config["language"])
        hotkey_name   = HOTKEY_NAMES.get(self.config["hotkey"], self.config["hotkey"])

        history_menu = rumps.MenuItem("Historial")
        history = self.config.get("history", [])
        if history:
            for i, item in enumerate(reversed(history)):
                short = item[:50] + "..." if len(item) > 50 else item
                history_menu.add(rumps.MenuItem(f"{i+1}. {short}",
                    callback=lambda _, t=item: self._copy_history(t)))
        else:
            history_menu.add(rumps.MenuItem("(vacío)"))

        self.menu.clear()
        self.menu = [
            rumps.MenuItem(f"Whisper Dictation VP v2.0"),
            rumps.MenuItem(f"Proveedor: {provider_name}"),
            rumps.MenuItem(f"Idioma: {lang_name}"),
            rumps.MenuItem(f"Tecla: {hotkey_name}"),
            None,
            history_menu,
            None,
            rumps.MenuItem("⚙️ Configuración", callback=self._open_settings),
            None,
            rumps.MenuItem("Salir", callback=self._quit),
        ]

    def _copy_history(self, text):
        subprocess.run(["pbcopy"], input=text.encode("utf-8"))

    # ── Configuración ─────────────────────────────────────────────────────────

    def _open_settings(self, _):
        choice = dialog_choice(
            "¿Qué quieres configurar?",
            "Cancelar", "Tecla de activación", "Idioma", "APIs"
        )
        if choice == "APIs":
            self._settings_apis()
        elif choice == "Idioma":
            self._settings_language()
        elif choice == "Tecla de activación":
            self._settings_hotkey()

    def _settings_apis(self):
        providers = self.config["providers"]
        configured = [PROVIDERS[p]["name"] for p in providers if p in PROVIDERS]
        not_configured = [PROVIDERS[p]["name"] for p in PROVIDERS if p not in providers]

        options = []
        if configured:
            options.append("Gestionar existentes")
        options.append("Añadir nueva API")
        options.append("Cancelar")

        choice = dialog_choice("APIs configuradas:\n" +
            ("\n".join(f"• {n}" for n in configured) if configured else "(ninguna)") +
            "\n\n¿Qué quieres hacer?",
            *reversed(options))

        if choice == "Añadir nueva API":
            self._setup_provider()
        elif choice == "Gestionar existentes":
            self._manage_providers()

    def _manage_providers(self):
        providers = list(self.config["providers"].keys())
        names = [PROVIDERS[p]["name"] for p in providers if p in PROVIDERS]
        choice = dialog_choice("Selecciona el proveedor a gestionar:",
            "Cancelar", *names)
        if not choice or choice == "Cancelar":
            return
        provider = next((p for p in providers if PROVIDERS.get(p, {}).get("name") == choice), None)
        if not provider:
            return

        active_mark = " (activo)" if provider == self.config["active_provider"] else ""
        action = dialog_choice(
            f"Proveedor: {choice}{active_mark}\n\n¿Qué quieres hacer?",
            "Cancelar", "Eliminar", "Cambiar API key", "Usar este"
        )
        if action == "Usar este":
            self.config["active_provider"] = provider
            save_config(self.config)
            self._build_client()
            self._build_menu()
        elif action == "Cambiar API key":
            self._setup_provider(edit=provider)
        elif action == "Eliminar":
            confirm = dialog_choice(f"¿Eliminar {choice}?", "Cancelar", "Eliminar")
            if confirm == "Eliminar":
                del self.config["providers"][provider]
                if self.config["active_provider"] == provider:
                    self.config["active_provider"] = list(self.config["providers"].keys())[0] \
                        if self.config["providers"] else ""
                save_config(self.config)
                self._build_client()
                self._build_menu()

    def _setup_provider(self, first_run=False, edit=None):
        if edit:
            provider = edit
        else:
            available = [p for p in PROVIDERS if p not in self.config["providers"]]
            if not available:
                dialog_info("Ya tienes todos los proveedores configurados.")
                return
            names = [PROVIDERS[p]["name"] for p in available]
            choice = dialog_choice(
                "Selecciona el proveedor de transcripción:",
                "Cancelar", *names
            )
            if not choice or choice == "Cancelar":
                if first_run and not self.config["providers"]:
                    sys.exit(0)
                return
            provider = next((p for p in available if PROVIDERS[p]["name"] == choice), None)
            if not provider:
                return

        info = PROVIDERS[provider]
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
        self._build_menu()

    def _settings_language(self):
        names = list(LANGUAGES.values())
        keys  = list(LANGUAGES.keys())
        choice = dialog_choice("Selecciona el idioma de transcripción:",
            "Cancelar", *names)
        if not choice or choice == "Cancelar":
            return
        lang = keys[names.index(choice)]
        self.config["language"] = lang
        save_config(self.config)
        self._build_menu()

    def _settings_hotkey(self):
        names = list(HOTKEY_NAMES.values())
        keys  = list(HOTKEY_NAMES.keys())
        choice = dialog_choice("Selecciona la tecla de activación:",
            "Cancelar", *names)
        if not choice or choice == "Cancelar":
            return
        hk = keys[names.index(choice)]
        self.config["hotkey"] = hk
        save_config(self.config)
        self._build_menu()

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status):
        with self.lock:
            if self.recording:
                self.audio_frames.append(indata.copy())

    def _start_listener(self):
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as l:
            l.join()

    def _current_hotkey(self):
        return HOTKEYS.get(self.config.get("hotkey", "alt_r"), keyboard.Key.alt_r)

    def _on_press(self, key):
        if key == self._current_hotkey():
            with self.lock:
                if not self.recording:
                    self.recording = True
                    self.audio_frames.clear()
            play_sound("Tink")
            self.title = ICON_RECORDING

    def _on_release(self, key):
        if key == self._current_hotkey():
            with self.lock:
                self.recording = False
                frames = list(self.audio_frames)
            self.title = ICON_PROCESSING
            threading.Thread(target=self._process, args=(frames,), daemon=True).start()

    def _process(self, frames):
        try:
            if not frames:
                return
            audio = np.concatenate(frames, axis=0)
            duration = len(audio) / SAMPLE_RATE
            if duration < 0.3:
                return

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = tmp.name
            try:
                with wave.open(path, "wb") as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio.tobytes())
                text = transcribe(self.provider, self.client, path,
                                  self.config.get("language", "es"))
            finally:
                os.unlink(path)

            if text:
                # Historial
                history = self.config.get("history", [])
                history.insert(0, text)
                self.config["history"] = history[:HISTORY_MAX]
                save_config(self.config)
                self._build_menu()

                # Pegar
                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
                subprocess.run(["osascript", "-e",
                    'tell application "System Events" to keystroke "v" using command down'],
                    check=True)
                play_sound("Pop")
                print(f"✓ [{duration:.1f}s] {text}")
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            self.title = ICON_IDLE

    def _quit(self, _):
        close_all_dialogs()
        self.stream.stop()
        self.stream.close()
        rumps.quit_application()

if __name__ == "__main__":
    WhisperDictationApp().run()
