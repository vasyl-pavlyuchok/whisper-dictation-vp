#!/usr/bin/env python3
"""
Whisper Dictation VP — Dictado por voz para macOS.
Manten Option derecho para grabar. Suelta para transcribir y pegar.
Disenado por Vasyl Pavlyuchok & Claude
"""

import os, sys, tempfile, threading, subprocess, json
import rumps, numpy as np, sounddevice as sd
from pynput import keyboard
from dotenv import load_dotenv
load_dotenv()

CONFIG_FILE = os.path.expanduser("~/.whisper_dictation_vp.json")
SAMPLE_RATE     = 16000
CHANNELS        = 1
DTYPE           = "int16"
HOTKEY          = keyboard.Key.alt_r
ICON_IDLE       = "🎙"
ICON_RECORDING  = "🔴"
ICON_PROCESSING = "⏳"

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    config.setdefault("provider", os.environ.get("WHISPER_PROVIDER", "groq"))
    config.setdefault("api_key",  os.environ.get("WHISPER_API_KEY") or os.environ.get("GROQ_API_KEY", ""))
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    os.chmod(CONFIG_FILE, 0o600)

def ask_dialog(prompt, default=""):
    r = subprocess.run(["osascript", "-e",
        f'tell app "System Events" to return text returned of '
        f'(display dialog "{prompt}" default answer "{default}" '
        f'with title "Whisper Dictation VP" buttons {{"Continuar"}} default button 1)'],
        capture_output=True, text=True)
    return r.stdout.strip()

def choose_dialog(prompt, btn1, btn2):
    r = subprocess.run(["osascript", "-e",
        f'tell app "System Events" to return button returned of '
        f'(display dialog "{prompt}" with title "Whisper Dictation VP" '
        f'buttons {{"{btn1}", "{btn2}"}} default button 1)'],
        capture_output=True, text=True)
    return r.stdout.strip()

def setup_first_run():
    label = choose_dialog(
        "Selecciona el proveedor de transcripcion:\n\nGroq — rapido y gratuito (recomendado)\nOpenAI — Whisper oficial",
        "Groq (gratis)", "OpenAI"
    )
    provider = "openai" if label == "OpenAI" else "groq"
    default_key = "sk-..." if provider == "openai" else "gsk_..."
    url = "platform.openai.com" if provider == "openai" else "console.groq.com"
    api_key = ask_dialog(f"Introduce tu API Key\n({url}):", default_key)

    if not api_key or api_key in ("sk-...", "gsk_..."):
        subprocess.run(["osascript", "-e",
            'tell app "System Events" to display dialog "API Key no valida." buttons {"OK"}'])
        sys.exit(1)

    config = {"provider": provider, "api_key": api_key}
    save_config(config)
    return config

config = load_config()
if not config.get("api_key"):
    config = setup_first_run()

PROVIDER = config["provider"]
API_KEY  = config["api_key"]

if PROVIDER == "openai":
    from openai import OpenAI
    ai_client = OpenAI(api_key=API_KEY)
    def transcribe_audio(path):
        with open(path, "rb") as f:
            r = ai_client.audio.transcriptions.create(model="whisper-1", file=f, language="es")
        return r.text.strip()
else:
    from groq import Groq
    ai_client = Groq(api_key=API_KEY)
    def transcribe_audio(path):
        with open(path, "rb") as f:
            r = ai_client.audio.transcriptions.create(
                file=(os.path.basename(path), f, "audio/wav"),
                model="whisper-large-v3", language="es", response_format="text",
            )
        return r.strip() if isinstance(r, str) else r.text.strip()

class WhisperDictationApp(rumps.App):

    def __init__(self):
        super().__init__(ICON_IDLE, quit_button=None)
        self.menu = [
            rumps.MenuItem(f"Whisper Dictation VP ({PROVIDER})"),
            None,
            rumps.MenuItem("Salir", callback=self._quit),
        ]
        self.recording    = False
        self.audio_frames = []
        self.lock         = threading.Lock()
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS,
            dtype=DTYPE, callback=self._audio_callback, blocksize=1024,
        )
        self.stream.start()
        threading.Thread(target=self._start_listener, daemon=True).start()

    def _audio_callback(self, indata, frames, time_info, status):
        with self.lock:
            if self.recording:
                self.audio_frames.append(indata.copy())

    def _start_listener(self):
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as l:
            l.join()

    def _on_press(self, key):
        if key == HOTKEY:
            with self.lock:
                if not self.recording:
                    self.recording = True
                    self.audio_frames.clear()
            self.title = ICON_RECORDING

    def _on_release(self, key):
        if key == HOTKEY:
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
            import wave
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                path = tmp.name
            try:
                with wave.open(path, "wb") as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio.tobytes())
                text = transcribe_audio(path)
            finally:
                os.unlink(path)
            if text:
                subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
                subprocess.run(["osascript", "-e",
                    'tell application "System Events" to keystroke "v" using command down'], check=True)
                print(f"✓ [{duration:.1f}s] {text}")
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            self.title = ICON_IDLE

    def _quit(self, _):
        self.stream.stop()
        self.stream.close()
        rumps.quit_application()

if __name__ == "__main__":
    WhisperDictationApp().run()
