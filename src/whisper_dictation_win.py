#!/usr/bin/env python3
"""
Whisper Dictation VP — Dictado por voz para Windows (beta).
Doble-toque Alt derecho para iniciar grabación. Toque simple para detener.
Diseñado por Vasyl Pavlyuchok & Claude — v3.4.1
"""

APP_VERSION = "3.4.1"

import os, sys, tempfile, threading, json, wave, time
import numpy as np
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Controller as KeyboardController, Key
from PIL import Image, ImageDraw
import pystray
from dotenv import load_dotenv
load_dotenv()

CONFIG_FILE       = os.path.expanduser("~/.whisper_dictation_vp.json")
HISTORY_MAX       = 10
SAMPLE_RATE       = 16000
CHANNELS          = 1
DTYPE             = "int16"
DOUBLE_TAP_WINDOW = 0.4

PROVIDERS = {
    "groq":       {"name": "Groq (gratis)",  "url": "console.groq.com",       "placeholder": "gsk_..."},
    "openai":     {"name": "OpenAI",          "url": "platform.openai.com",    "placeholder": "sk-..."},
    "deepgram":   {"name": "Deepgram",        "url": "console.deepgram.com",   "placeholder": "..."},
    "assemblyai": {"name": "AssemblyAI",      "url": "app.assemblyai.com",     "placeholder": "..."},
}

LANGUAGES = {
    "auto":  "Automático (detecta el idioma)",
    "es":    "Español",
    "en":    "Inglés",
    "uk":    "Ucraniano",
    "fr":    "Francés",
    "de":    "Alemán",
    "it":    "Italiano",
    "pt":    "Portugués",
    "zh":    "Chino",
    "ru":    "Ruso",
    "ar":    "Árabe",
    "hi":    "Hindi",
    "ja":    "Japonés",
    "ko":    "Coreano",
    "tr":    "Turco",
    "pl":    "Polaco",
    "nl":    "Neerlandés",
}

HOTKEYS = {
    "alt_r":   keyboard.Key.alt_r,
    "alt_gr":  keyboard.Key.alt_gr,
    "alt":     keyboard.Key.alt_l,
    "ctrl_r":  keyboard.Key.ctrl_r,
    "ctrl_l":  keyboard.Key.ctrl_l,
}
HOTKEY_NAMES = {
    "alt_r":   "Alt derecho",
    "alt_gr":  "AltGr",
    "alt":     "Alt izquierdo",
    "ctrl_r":  "Control derecho",
    "ctrl_l":  "Control izquierdo",
}

LOG_FILE = os.path.expanduser("~/whisper_dictation_vp.log")

def dbg(msg):
    """Log de diagnóstico con rotación (~256 KB). Ábrelo con el Bloc de notas."""
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 262144:
            os.replace(LOG_FILE, LOG_FILE + ".old")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except Exception:
        pass

# ── Config (mismo formato que la versión macOS) ───────────────────────────────

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config = json.load(f)
    config.setdefault("providers", {})
    config.setdefault("active_provider", os.environ.get("WHISPER_PROVIDER", ""))
    config.setdefault("language", "auto")
    config.setdefault("hotkey", "alt")
    config.setdefault("history", [])
    config.setdefault("ai_format", False)
    config.setdefault("dictionary", [])
    config.setdefault("check_updates", True)
    if not config["providers"] and os.environ.get("GROQ_API_KEY"):
        config["providers"]["groq"] = os.environ.get("GROQ_API_KEY")
    return config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

# ── Actualizaciones ───────────────────────────────────────────────────────────

UPDATE_URL    = ("https://api.github.com/repos/vasyl-pavlyuchok/"
                 "whisper-dictation-vp/releases/latest")
DOWNLOAD_PAGE = ("https://github.com/vasyl-pavlyuchok/"
                 "whisper-dictation-vp/releases/latest")

def version_tuple(v):
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except Exception:
        return (0,)

def fetch_latest_version():
    import urllib.request
    req = urllib.request.Request(UPDATE_URL,
                                 headers={"User-Agent": "WhisperDictationVP"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r).get("tag_name", "").lstrip("v") or None

# ── Sonidos ───────────────────────────────────────────────────────────────────

def play_sound(kind):
    try:
        import winsound
        freqs = {"start": 880, "stop": 520, "ok": 1320, "error": 220}
        winsound.Beep(freqs.get(kind, 660), 120)
    except Exception:
        pass

# ── Diálogos tkinter ──────────────────────────────────────────────────────────

def _tk_root():
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root

def dialog_input(prompt, default=""):
    from tkinter import simpledialog
    root = _tk_root()
    try:
        return simpledialog.askstring("Whisper Dictation VP", prompt,
                                      initialvalue=default, parent=root) or ""
    finally:
        root.destroy()

def dialog_info(msg):
    from tkinter import messagebox
    root = _tk_root()
    try:
        messagebox.showinfo("Whisper Dictation VP", msg, parent=root)
    finally:
        root.destroy()

def dialog_choice_list(prompt, options):
    """Selector simple basado en botones tkinter. Devuelve la opción o None."""
    import tkinter as tk
    result = [None]
    root = tk.Tk()
    root.title("Whisper Dictation VP")
    root.attributes("-topmost", True)
    tk.Label(root, text=prompt, padx=20, pady=10).pack()
    def choose(opt):
        result[0] = opt
        root.destroy()
    for opt in options:
        tk.Button(root, text=opt, width=32,
                  command=lambda o=opt: choose(o)).pack(padx=20, pady=3)
    tk.Button(root, text="Cancelar", width=32, command=root.destroy)\
        .pack(padx=20, pady=(10, 15))
    root.eval("tk::PlaceWindow . center")
    root.mainloop()
    return result[0]

# ── Portapapeles y pegado ─────────────────────────────────────────────────────

def set_clipboard(text):
    import ctypes
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    data = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        raise RuntimeError("No se pudo abrir el portapapeles")
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        ptr = kernel32.GlobalLock(handle)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(CF_UNICODETEXT, handle)
    finally:
        user32.CloseClipboard()

def paste_text(text):
    set_clipboard(text)
    time.sleep(0.15)
    kb = KeyboardController()
    with kb.pressed(Key.ctrl):
        kb.press("v")
        kb.release("v")

# ── Transcripción (idéntica a la versión macOS) ───────────────────────────────

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
    """Post-procesa la transcripción con un LLM (solo Groq/OpenAI)."""
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

# ── Indicador flotante de estado ──────────────────────────────────────────────

class StatusOverlay:
    """Píldora flotante siempre visible (abajo-centro) mientras se graba o
    transcribe — el icono de la bandeja de Windows suele quedar oculto tras
    la flecha, así que hace falta feedback visual en pantalla."""

    STYLES = {
        "recording":  ("●  Grabando…",      "#c62828"),
        "processing": ("…  Transcribiendo", "#a8741a"),
    }

    def __init__(self):
        import queue as _queue
        self._queue = _queue.Queue()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            import tkinter as tk
            self._tk = tk
            self.root = tk.Tk()
            self.root.withdraw()
            self.root.overrideredirect(True)
            self.root.attributes("-topmost", True)
            try:
                self.root.attributes("-alpha", 0.93)
            except Exception:
                pass
            self.label = tk.Label(self.root, text="", fg="white",
                                  font=("Segoe UI", 11, "bold"),
                                  padx=16, pady=7)
            self.label.pack()
            self._poll()
            self.root.mainloop()
        except Exception as e:
            dbg(f"overlay no disponible: {e}")

    def _poll(self):
        try:
            while True:
                self._apply(self._queue.get_nowait())
        except Exception:
            pass
        self.root.after(120, self._poll)

    def _apply(self, state):
        style = self.STYLES.get(state)
        if not style:
            self.root.withdraw()
            return
        text, color = style
        self.label.config(text=text, bg=color)
        self.root.configure(bg=color)
        self.root.update_idletasks()
        w = self.label.winfo_reqwidth()
        h = self.label.winfo_reqheight()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{sh - h - 70}")
        self.root.deiconify()
        self.root.lift()

    def set_state(self, state):
        self._queue.put(state)

# ── Iconos de bandeja (generados con PIL) ─────────────────────────────────────

def make_icon(state):
    """idle=micrófono gris, recording=círculo rojo, processing=círculo ámbar."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if state == "recording":
        d.ellipse([8, 8, 56, 56], fill=(220, 50, 47, 255))
        d.ellipse([22, 22, 42, 42], fill=(255, 255, 255, 255))
    elif state == "processing":
        d.ellipse([8, 8, 56, 56], fill=(230, 160, 30, 255))
        d.rectangle([28, 16, 36, 36], fill=(255, 255, 255, 255))
        d.ellipse([28, 40, 36, 48], fill=(255, 255, 255, 255))
    else:
        d.rounded_rectangle([22, 8, 42, 38], radius=10, fill=(120, 120, 130, 255))
        d.arc([14, 20, 50, 48], start=0, end=180, fill=(120, 120, 130, 255), width=5)
        d.rectangle([30, 48, 34, 56], fill=(120, 120, 130, 255))
        d.rectangle([22, 56, 42, 60], fill=(120, 120, 130, 255))
    return img

# ── App ───────────────────────────────────────────────────────────────────────

class WhisperDictationWin:

    def __init__(self):
        self.config      = load_config()
        self.lock        = threading.Lock()
        self.config_lock = threading.Lock()

        self.recording    = False
        self.audio_frames = []

        self._last_tap_time = 0.0
        self._key_down      = False
        self._stop_tap      = False

        if not self.config["providers"]:
            self._first_run_setup()

        if not self.config["active_provider"] or \
           self.config["active_provider"] not in self.config["providers"]:
            if self.config["providers"]:
                self.config["active_provider"] = list(self.config["providers"].keys())[0]
                save_config(self.config)

        self._build_client()

        self.overlay = StatusOverlay()

        try:
            dev = sd.query_devices(kind="input")
            dbg(f"micrófono de entrada: {dev.get('name')} "
                f"(canales: {dev.get('max_input_channels')})")
        except Exception as e:
            dbg(f"sin dispositivo de entrada: {e}")

        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE, channels=CHANNELS,
                dtype=DTYPE, callback=self._audio_callback, blocksize=1024,
            )
            self.stream.start()
            dbg("stream de audio iniciado")
        except Exception as e:
            dbg(f"ERROR abriendo el micrófono: {e}")
            dialog_info(
                "No se pudo abrir el micrófono.\n\n"
                "Comprueba: Configuración → Privacidad y seguridad → "
                "Micrófono → activa «Permitir que las aplicaciones de "
                "escritorio accedan al micrófono».")
            raise

        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

        self.icon = pystray.Icon(
            "whisper_dictation_vp",
            make_icon("idle"),
            f"Whisper Dictation VP v{APP_VERSION}",
            menu=pystray.Menu(lambda: self._menu_items()),
        )

        self._update_available = None
        threading.Thread(target=self._update_check_loop, daemon=True).start()
        dbg(f"app v{APP_VERSION} iniciada — hotkey={self.config.get('hotkey')} "
            f"proveedor={self.config.get('active_provider')}")

    def _update_check_loop(self):
        time.sleep(15)
        while True:
            if not self.config.get("check_updates", True):
                time.sleep(86400)
                continue
            try:
                latest = fetch_latest_version()
                if latest and version_tuple(latest) > version_tuple(APP_VERSION):
                    if self._update_available != latest:
                        self._update_available = latest
                        try:
                            self.icon.notify(
                                f"Nueva versión v{latest} disponible — "
                                "descárgala desde el menú del icono.",
                                "Whisper Dictation VP")
                        except Exception:
                            pass
            except Exception:
                pass
            time.sleep(86400)

    def _open_download_page(self, icon, item):
        import webbrowser
        webbrowser.open(DOWNLOAD_PAGE)

    # ── Primer arranque ───────────────────────────────────────────────────────

    def _first_run_setup(self):
        names  = [PROVIDERS[p]["name"] for p in PROVIDERS]
        choice = dialog_choice_list(
            "Bienvenido a Whisper Dictation VP.\n\n"
            "Selecciona tu proveedor de transcripción\n"
            "(Groq es gratuito y recomendado):", names)
        if not choice:
            sys.exit(0)
        provider = next(p for p in PROVIDERS if PROVIDERS[p]["name"] == choice)
        info = PROVIDERS[provider]
        api_key = dialog_input(
            f"API Key de {info['name']}\n(consíguela en {info['url']}):",
            default=info["placeholder"])
        if not api_key or api_key == info["placeholder"]:
            sys.exit(0)
        self.config["providers"][provider] = api_key
        self.config["active_provider"] = provider
        save_config(self.config)
        dialog_info(
            "¡Listo! Doble-toque en Alt derecho para grabar,\n"
            "toque simple para detener.\n\n"
            "El texto se pega automáticamente donde estés escribiendo.")

    # ── Cliente ───────────────────────────────────────────────────────────────

    def _build_client(self):
        provider      = self.config["active_provider"]
        api_key       = self.config["providers"].get(provider, "")
        self.provider = provider
        self.client   = build_client(provider, api_key) if provider else None

    # ── Menú de bandeja (dinámico) ────────────────────────────────────────────

    def _menu_items(self):
        cfg = self.config
        active_provider = cfg["active_provider"]
        active_lang     = cfg["language"]
        hotkey_name     = HOTKEY_NAMES.get(cfg["hotkey"], cfg["hotkey"])

        provider_items = [
            pystray.MenuItem(
                PROVIDERS.get(p, {}).get("name", p),
                self._make_provider_action(p),
                checked=lambda item, p=p: p == self.config["active_provider"],
                radio=True)
            for p in cfg["providers"]
        ]
        lang_items = [
            pystray.MenuItem(
                name,
                self._make_lang_action(key),
                checked=lambda item, k=key: k == self.config["language"],
                radio=True)
            for key, name in LANGUAGES.items()
        ]
        hotkey_items = [
            pystray.MenuItem(
                name,
                self._make_hotkey_action(key),
                checked=lambda item, k=key: k == self.config["hotkey"],
                radio=True)
            for key, name in HOTKEY_NAMES.items()
        ]
        history = cfg.get("history", [])
        if history:
            history_items = [
                pystray.MenuItem(
                    (t[:60] + "…") if len(t) > 60 else t,
                    self._make_copy_action(t))
                for t in history
            ]
            history_items += [
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Limpiar historial", self._clear_history),
            ]
        else:
            history_items = [pystray.MenuItem("(vacío)", None, enabled=False)]

        dictionary = cfg.get("dictionary", [])
        dict_items = [
            pystray.MenuItem(f"Eliminar: {w}", self._make_remove_word_action(w))
            for w in dictionary
        ]
        if dict_items:
            dict_items.append(pystray.Menu.SEPARATOR)
        dict_items.append(pystray.MenuItem("Añadir palabra…", self._add_word))

        update_items = []
        if getattr(self, "_update_available", None):
            update_items = [pystray.MenuItem(
                f"⬆️ Nueva versión v{self._update_available} — descargar",
                self._open_download_page)]

        return [
            pystray.MenuItem(f"Whisper Dictation VP v{APP_VERSION}", None, enabled=False),
            *update_items,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Proveedor", pystray.Menu(*provider_items)),
            pystray.MenuItem("Idioma", pystray.Menu(*lang_items)),
            pystray.MenuItem(f"Tecla: {hotkey_name} (doble-toque)",
                             pystray.Menu(*hotkey_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Formato IA (limpia muletillas)",
                             self._toggle_ai_format,
                             checked=lambda item: self.config.get("ai_format", False)),
            pystray.MenuItem("Avisar de actualizaciones",
                             self._toggle_check_updates,
                             checked=lambda item: self.config.get("check_updates", True)),
            pystray.MenuItem(f"Diccionario ({len(dictionary)})",
                             pystray.Menu(*dict_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Historial (clic para copiar)",
                             pystray.Menu(*history_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Añadir / cambiar API key", self._settings_api),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self._quit),
        ]

    def _toggle_ai_format(self, icon, item):
        with self.config_lock:
            self.config["ai_format"] = not self.config.get("ai_format", False)
            save_config(self.config)

    def _toggle_check_updates(self, icon, item):
        with self.config_lock:
            self.config["check_updates"] = not self.config.get("check_updates", True)
            save_config(self.config)

    def _add_word(self, icon, item):
        def worker():
            word = dialog_input(
                "Añade una palabra o nombre propio que Whisper\n"
                "suela transcribir mal:").strip()
            if not word:
                return
            with self.config_lock:
                dictionary = self.config.get("dictionary", [])
                if word not in dictionary:
                    dictionary.append(word)
                    self.config["dictionary"] = dictionary
                    save_config(self.config)
        threading.Thread(target=worker, daemon=True).start()

    def _make_remove_word_action(self, word):
        def action(icon, item):
            with self.config_lock:
                dictionary = self.config.get("dictionary", [])
                if word in dictionary:
                    dictionary.remove(word)
                    self.config["dictionary"] = dictionary
                    save_config(self.config)
        return action

    def _make_provider_action(self, provider):
        def action(icon, item):
            self.config["active_provider"] = provider
            save_config(self.config)
            self._build_client()
        return action

    def _make_lang_action(self, lang):
        def action(icon, item):
            self.config["language"] = lang
            save_config(self.config)
        return action

    def _make_hotkey_action(self, key):
        def action(icon, item):
            self.config["hotkey"] = key
            save_config(self.config)
        return action

    def _make_copy_action(self, text):
        def action(icon, item):
            try:
                set_clipboard(text)
                play_sound("ok")
            except Exception:
                pass
        return action

    def _clear_history(self, icon, item):
        with self.config_lock:
            self.config["history"] = []
            save_config(self.config)

    def _settings_api(self, icon, item):
        threading.Thread(target=self._settings_api_thread, daemon=True).start()

    def _settings_api_thread(self):
        names  = [PROVIDERS[p]["name"] for p in PROVIDERS]
        choice = dialog_choice_list("Selecciona el proveedor:", names)
        if not choice:
            return
        provider = next(p for p in PROVIDERS if PROVIDERS[p]["name"] == choice)
        info     = PROVIDERS[provider]
        current  = self.config["providers"].get(provider, "")
        api_key  = dialog_input(
            f"API Key de {info['name']}\n(consíguela en {info['url']}):",
            default=current or info["placeholder"])
        if not api_key or api_key == info["placeholder"]:
            return
        with self.config_lock:
            self.config["providers"][provider] = api_key
            if not self.config["active_provider"]:
                self.config["active_provider"] = provider
            save_config(self.config)
        self._build_client()

    # ── Audio ─────────────────────────────────────────────────────────────────

    def _audio_callback(self, indata, frames, time_info, status):
        with self.lock:
            if self.recording:
                self.audio_frames.append(indata.copy())

    def _current_hotkey(self):
        return HOTKEYS.get(self.config.get("hotkey", "alt_r"), keyboard.Key.alt_r)

    # ── Teclado ───────────────────────────────────────────────────────────────

    def _on_press(self, key, injected=False):
        if injected:
            return  # eventos sintéticos (nuestro propio Ctrl+V al pegar)
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
                play_sound("stop")
                dbg(f"grabación parada — {len(frames)} bloques de audio")
                self._set_state("processing")
                threading.Thread(target=self._process, args=(frames,), daemon=True).start()

    def _on_release(self, key, injected=False):
        if injected:
            return
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
            play_sound("start")
            dbg("grabación iniciada")
            self._set_state("recording")
        else:
            self._last_tap_time = now

    def _set_state(self, state):
        try:
            self.icon.icon = make_icon(state)
        except Exception:
            pass
        try:
            self.overlay.set_state(state)
        except Exception:
            pass

    # ── Procesado ─────────────────────────────────────────────────────────────

    def _process(self, frames):
        path = None
        try:
            if not frames:
                dbg("sin audio: 0 bloques (¿el micrófono no entrega datos?)")
                play_sound("error")
                return

            audio    = np.concatenate(frames, axis=0)
            duration = len(audio) / SAMPLE_RATE

            if duration < 0.3:
                dbg(f"grabación demasiado corta ({duration:.2f}s)")
                play_sound("error")
                return

            rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
            dbg(f"audio: {duration:.1f}s, RMS={rms:.1f}")
            if rms < 2:
                dbg("SILENCIO detectado — el micrófono no capta tu voz. "
                    "Revisa el micrófono predeterminado en Windows y el "
                    "permiso de micrófono para apps de escritorio.")
                play_sound("error")
                return

            fd, path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            with wave.open(path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio.tobytes())

            dictionary = self.config.get("dictionary", [])
            text = transcribe(self.provider, self.client, path,
                              self.config.get("language", "es"), dictionary)
            dbg(f"transcripción: {len(text)} caracteres")

            if text and self.config.get("ai_format"):
                try:
                    text = ai_cleanup(self.provider, self.client, text, dictionary)
                except Exception:
                    pass

            if text:
                with self.config_lock:
                    history = self.config.get("history", [])
                    history.insert(0, text)
                    self.config["history"] = history[:HISTORY_MAX]
                    save_config(self.config)
                paste_text(text)
                play_sound("ok")
            else:
                play_sound("error")

        except Exception as e:
            play_sound("error")
            import traceback
            dbg(f"ERROR de transcripción: {e}\n{traceback.format_exc()}")
        finally:
            if path and os.path.exists(path):
                os.unlink(path)
            self._set_state("idle")

    # ── Salir ─────────────────────────────────────────────────────────────────

    def _quit(self, icon, item):
        try:
            self._listener.stop()
        except Exception:
            pass
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass
        icon.stop()

    def run(self):
        self.icon.run()


if __name__ == "__main__":
    WhisperDictationWin().run()
